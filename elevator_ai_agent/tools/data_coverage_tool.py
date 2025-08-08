"""Data Coverage Analysis tool for answering data quality and availability questions."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from .base import BaseTool
from ..services.data_coverage import data_coverage_service


class DataCoverageTool(BaseTool):
    """Tool for analyzing data coverage, quality, and availability."""
    
    def __init__(self):
        super().__init__(
            name="data_coverage_analysis",
            description="Analyze data coverage, quality, availability, gaps, and completeness for elevator systems"
        )
    
    def run(
        self, 
        installation_id: str, 
        tz: str, 
        start: datetime, 
        end: datetime, 
        machine_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Analyze data coverage and quality for the specified time period.
        
        Args:
            installation_id: Installation to analyze
            tz: Installation timezone
            start: Start datetime (timezone-aware)
            end: End datetime (timezone-aware)
            machine_id: Optional specific machine filter
            **kwargs: Additional tool-specific parameters
            
        Returns:
            Dictionary with comprehensive data coverage analysis
        """
        # Get comprehensive data coverage report
        coverage_report = data_coverage_service.analyze_coverage(
            installation_id=installation_id,
            start_time=start,
            end_time=end,
            installation_tz=tz,
            machine_id=machine_id
        )
        
        # Convert to dictionary and add additional analysis
        coverage_data = coverage_report.to_dict()
        
        # Add analysis-friendly summaries
        coverage_data['analysis_summary'] = self._generate_analysis_summary(coverage_report)
        coverage_data['machine_summaries'] = self._generate_machine_summaries(coverage_report)
        coverage_data['quality_assessment'] = self._assess_data_quality(coverage_report)
        coverage_data['recommendations'] = self._generate_recommendations(coverage_report)
        
        return coverage_data
    
    def _generate_analysis_summary(self, report) -> Dict[str, Any]:
        """Generate high-level analysis summary."""
        coverage_pct = report.overall_coverage_percentage
        
        # Determine overall health status
        if coverage_pct >= 95:
            status = "excellent"
            status_emoji = "🟢"
        elif coverage_pct >= 85:
            status = "good" 
            status_emoji = "🟡"
        elif coverage_pct >= 70:
            status = "fair"
            status_emoji = "🟠"
        else:
            status = "poor"
            status_emoji = "🔴"
        
        return {
            "overall_status": status,
            "status_emoji": status_emoji,
            "coverage_percentage": coverage_pct,
            "total_elevators": report.machines_total,
            "reporting_elevators": report.machines_with_data,
            "silent_elevators": report.machines_without_data,
            "data_types_available": report.data_types_available,
            "period_days": (report.end_time - report.start_time).days + 1,
            "total_expected_hours": report.total_expected_minutes / 60.0,
            "total_available_hours": report.total_available_minutes / 60.0
        }
    
    def _generate_machine_summaries(self, report) -> List[Dict[str, Any]]:
        """Generate machine-specific summaries."""
        summaries = []
        
        for machine in report.machine_coverage:
            machine_id = machine['machine_id']
            
            if machine['has_data']:
                # Calculate time span of data
                first_event = machine.get('first_event')
                last_event = machine.get('last_event')
                
                if first_event and last_event:
                    from ..services.timezone import timezone_service
                    first_dt = timezone_service.epoch_to_local_datetime(first_event, report.timezone)
                    last_dt = timezone_service.epoch_to_local_datetime(last_event, report.timezone)
                    data_span_hours = (last_dt - first_dt).total_seconds() / 3600.0
                else:
                    data_span_hours = 0
                
                summary = {
                    "machine_id": machine_id,
                    "status": "reporting",
                    "coverage_percentage": machine['coverage_percentage'],
                    "event_count": machine['event_count'],
                    "coverage_hours": machine['coverage_minutes'] / 60.0,
                    "data_span_hours": data_span_hours,
                    "first_event_time": first_dt.isoformat() if first_event else None,
                    "last_event_time": last_dt.isoformat() if last_event else None,
                    "quality_rating": self._rate_machine_quality(machine['coverage_percentage'])
                }
            else:
                summary = {
                    "machine_id": machine_id,
                    "status": "silent", 
                    "coverage_percentage": 0.0,
                    "event_count": 0,
                    "coverage_hours": 0.0,
                    "data_span_hours": 0.0,
                    "first_event_time": None,
                    "last_event_time": None,
                    "quality_rating": "no_data"
                }
            
            summaries.append(summary)
        
        # Sort by machine ID for consistent ordering
        return sorted(summaries, key=lambda x: int(x['machine_id']))
    
    def _rate_machine_quality(self, coverage_pct: float) -> str:
        """Rate the data quality for a single machine."""
        if coverage_pct >= 95:
            return "excellent"
        elif coverage_pct >= 85:
            return "good"
        elif coverage_pct >= 70:
            return "fair"
        elif coverage_pct >= 50:
            return "poor"
        else:
            return "very_poor"
    
    def _assess_data_quality(self, report) -> Dict[str, Any]:
        """Assess overall data quality and identify issues."""
        issues = []
        strengths = []
        
        # Coverage assessment
        coverage_pct = report.overall_coverage_percentage
        if coverage_pct < 70:
            issues.append(f"Low overall coverage ({coverage_pct:.1f}%) - analysis may be incomplete")
        elif coverage_pct >= 95:
            strengths.append(f"Excellent overall coverage ({coverage_pct:.1f}%)")
        
        # Machine availability assessment
        if report.machines_without_data > 0:
            issues.append(f"{report.machines_without_data} of {report.machines_total} elevators not reporting")
        else:
            strengths.append("All elevators are reporting data")
        
        # Data type availability
        available_types = len(report.data_types_available)
        if available_types == 0:
            issues.append("No event data available for analysis")
        elif 'CarModeChanged' not in report.data_types_available:
            issues.append("Missing operational data (CarModeChanged events)")
        else:
            strengths.append("Operational data (CarModeChanged) available")
        
        if 'Door' in report.data_types_available:
            strengths.append("Door operation data available")
        
        # Data gaps assessment
        gap_count = len(report.data_gaps)
        if gap_count > 5:
            issues.append(f"Multiple data gaps detected ({gap_count} issues)")
        elif gap_count > 0:
            issues.append(f"Some data gaps detected ({gap_count} issues)")
        
        return {
            "overall_quality": "good" if len(issues) <= 1 else "needs_attention" if len(issues) <= 3 else "poor",
            "issues": issues,
            "strengths": strengths,
            "issue_count": len(issues),
            "strength_count": len(strengths)
        }
    
    def _generate_recommendations(self, report) -> List[str]:
        """Generate actionable recommendations based on coverage analysis."""
        recommendations = []
        
        # Coverage improvement recommendations
        if report.overall_coverage_percentage < 85:
            recommendations.append("Consider investigating data collection systems for improved coverage")
        
        # Silent machine recommendations
        if report.machines_without_data > 0:
            silent_machines = [m['machine_id'] for m in report.machine_coverage if not m['has_data']]
            recommendations.append(f"Check connectivity/sensors for silent elevators: {', '.join(silent_machines)}")
        
        # Low coverage machine recommendations
        low_coverage_machines = [
            m['machine_id'] for m in report.machine_coverage 
            if m['has_data'] and m['coverage_percentage'] < 50
        ]
        if low_coverage_machines:
            recommendations.append(f"Investigate data quality issues for elevators with low coverage: {', '.join(low_coverage_machines)}")
        
        # Data type recommendations
        if 'Door' not in report.data_types_available:
            recommendations.append("Enable door event collection for comprehensive operational analysis")
        
        # Time range recommendations
        period_days = (report.end_time - report.start_time).days + 1
        if period_days > 30 and report.overall_coverage_percentage < 80:
            recommendations.append("Consider shorter analysis periods for better data quality with current coverage levels")
        
        if not recommendations:
            recommendations.append("Data coverage looks good - no immediate actions needed")
        
        return recommendations


# Tool instance
data_coverage_tool = DataCoverageTool()
