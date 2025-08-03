"""Car Mode Changed analysis tool."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from tools.base import BaseTool
from services.uptime import uptime_service


class CarModeChangedTool(BaseTool):
    """Tool for analyzing CarModeChanged events and uptime/downtime metrics."""
    
    def __init__(self):
        super().__init__(
            name="car_mode_changed",
            description="Analyze elevator uptime/downtime from CarModeChanged events"
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
        Analyze uptime and downtime metrics from CarModeChanged events.
        
        Args:
            installation_id: Installation to analyze
            tz: Installation timezone
            start: Start datetime (timezone-aware)
            end: End datetime (timezone-aware)
            machine_id: Optional specific machine to analyze
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with uptime/downtime metrics and analysis
        """
        # First validate the date range and get recommendations
        from services.timezone import timezone_service
        date_validation = timezone_service.validate_date_range(start, end, tz)
        
        # If date validation fails completely, return early with error
        if not date_validation.get('is_valid', True):
            return {
                'error': 'Invalid date range',
                'warnings': date_validation.get('warnings', []),
                'recommendations': date_validation.get('recommendations', []),
                'date_validation': date_validation,
                'interpretation': [
                    "❌ Cannot analyze data for the requested time range.",
                    *date_validation.get('warnings', []),
                    *date_validation.get('recommendations', [])
                ]
            }
        
        # Adjust end time if it was in the future
        actual_end = date_validation.get('adjusted_end_time', end)
        
        # Get the uptime metrics with proper parameters only
        metrics = uptime_service.get_uptime_metrics(
            installation_id=installation_id,
            start_time=start,
            end_time=actual_end,
            installation_tz=tz,
            machine_id=machine_id
        )
        
        # Add date validation results to metrics for enhanced interpretation
        if 'interpretation' not in metrics:
            metrics['interpretation'] = []
        
        # Insert date validation warnings/recommendations at the beginning
        if date_validation.get('warnings'):
            metrics['interpretation'] = list(date_validation['warnings']) + list(metrics['interpretation'])
        if date_validation.get('recommendations'):
            metrics['interpretation'] = list(metrics['interpretation']) + list(date_validation['recommendations'])
        
        # Enhance interpretation with elevator/car context
        enhanced_interpretation: List[str] = []
        
        # Add context about what we're analyzing
        machine_count = len(metrics['machine_metrics'])
        if machine_count == 0:
            enhanced_interpretation.append("No elevator data found for the specified time range.")
        elif machine_count == 1:
            enhanced_interpretation.append(f"Analysis for 1 elevator (Car/Machine ID: {metrics['machine_metrics'][0]['machine_id']})")
        else:
            machine_ids = [str(m['machine_id']) for m in metrics['machine_metrics']]
            enhanced_interpretation.append(f"Analysis for {machine_count} elevators (Car/Machine IDs: {', '.join(machine_ids)})")
        
        # Use the built-in interpretation from uptime service and enhance it
        if 'interpretation' in metrics:
            for item in metrics['interpretation']:
                # Enhance machine references to be more descriptive
                if 'Machine' in item and 'has the lowest uptime' in item:
                    enhanced_item = item.replace('Machine', 'Elevator (Car)')
                    enhanced_interpretation.append(enhanced_item)
                else:
                    enhanced_interpretation.append(item)
        
        # Add summary of each elevator's performance
        if metrics['machine_metrics']:
            enhanced_interpretation.append("\n📊 Individual Elevator Performance:")
            for machine in metrics['machine_metrics']:
                status_emoji = "🟢" if machine['uptime_percentage'] >= 95 else "🟡" if machine['uptime_percentage'] >= 80 else "🔴"
                enhanced_interpretation.append(
                    f"{status_emoji} Elevator {machine['machine_id']}: {machine['uptime_percentage']:.1f}% uptime "
                    f"({machine['uptime_human']} up, {machine['downtime_human']} down)"
                )
        
        # Override the interpretation with enhanced version
        metrics['interpretation'] = enhanced_interpretation
        return metrics


# Tool instance
car_mode_changed_tool = CarModeChangedTool()
