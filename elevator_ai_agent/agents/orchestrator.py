"""Orchestrator for routing user queries to appropriate tools and generating responses."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from services.cosmos import get_cosmos_service
from services.llm import llm_service
from services.timezone import timezone_service
from tools.car_mode_changed import car_mode_changed_tool
from tools.basic_tools import door_tool, passenger_report_tool, hall_call_accepted_tool

logger = logging.getLogger(__name__)


class QueryOrchestrator:
    """Orchestrates user queries by routing to tools and generating LLM responses."""
    
    def __init__(self):
        """Initialize orchestrator with available tools."""
        self.tools = {
            'uptime': car_mode_changed_tool,
            'downtime': car_mode_changed_tool,
            'car_mode': car_mode_changed_tool,
            'door': door_tool,
            'passenger': passenger_report_tool,
            'hall_call': hall_call_accepted_tool,
        }
    
    def get_elevator_count(self, installation_id: str) -> Dict[str, Any]:
        """
        Get the count of elevators for an installation.
        
        Args:
            installation_id: Installation to analyze
            
        Returns:
            Dictionary with elevator count information
        """
        try:
            cosmos_service = get_cosmos_service()
            machine_ids = cosmos_service.get_all_machine_ids(installation_id)
            
            return {
                'installation_id': installation_id,
                'elevator_count': len(machine_ids),
                'elevator_ids': machine_ids,
                'interpretation': [
                    f"Installation {installation_id} has {len(machine_ids)} elevator(s)",
                    f"Elevator IDs found: {', '.join(map(str, machine_ids))}" if machine_ids else "No elevators found in the data"
                ]
            }
        except Exception as e:
            logger.error(f"Error getting elevator count: {e}")
            return {
                'installation_id': installation_id,
                'elevator_count': 0,
                'elevator_ids': [],
                'error': str(e),
                'interpretation': [f"Error retrieving elevator count: {str(e)}"]
            }
    
    def classify_intent(self, message: str) -> List[str]:
        """
        Classify user intent to determine which tools to use.
        
        Args:
            message: User's question/request
            
        Returns:
            List of tool names to use
        """
        selected_tools: List[str] = []
        message_lower = message.lower()
        
        # Debug logging
        logger.info(f"Classifying intent for message: '{message}' (lowercase: '{message_lower}')")
        
        # Elevator count questions - use simpler elevator count analysis
        if any(keyword in message_lower for keyword in [
            'how many elevator', 'number of elevator', 'count of elevator',
            'elevators are there', 'total elevator', 'how many cars',
            'number of cars', 'count elevator', 'many elevator'
        ]):
            selected_tools.append('elevator_count')
            logger.info(f"Matched elevator count pattern, using elevator_count tool")
        
        # Uptime/downtime analysis
        elif any(keyword in message_lower for keyword in [
            'uptime', 'downtime', 'availability', 'working', 'broken', 
            'operational', 'service', 'failure', 'outage'
        ]):
            selected_tools.append('uptime')
        
        # Door analysis
        elif any(keyword in message_lower for keyword in [
            'door', 'open', 'close', 'closing', 'opening'
        ]):
            selected_tools.append('door')
        
        # Passenger analysis
        elif any(keyword in message_lower for keyword in [
            'passenger', 'people', 'usage', 'traffic', 'load'
        ]):
            selected_tools.append('passenger')
        
        # Hall call analysis
        elif any(keyword in message_lower for keyword in [
            'hall call', 'call', 'button', 'request'
        ]):
            selected_tools.append('hall_call')
        
        # Default to uptime if no specific intent detected
        else:
            selected_tools.append('uptime')
            logger.info(f"No specific pattern matched, defaulting to uptime tool")
        
        logger.info(f"Selected tools for query: {selected_tools}")
        return selected_tools
    
    def parse_time_range(
        self, 
        message: str, 
        installation_tz: str
    ) -> Tuple[datetime, datetime]:
        """
        Parse time range from user message or use default.
        
        Args:
            message: User's message
            installation_tz: Installation timezone
            
        Returns:
            Tuple of (start_time, end_time) as timezone-aware datetimes
        """
        # Try to extract specific dates
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(installation_tz)
        now = datetime.now(tz)
        
        # Look for "last week", "last 7 days", etc.
        if 'last week' in message.lower():
            end_time = now.replace(hour=23, minute=59, second=59, microsecond=0)
            start_time = end_time - timedelta(days=7)
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif 'last 24 hours' in message.lower() or 'yesterday' in message.lower():
            end_time = now
            start_time = end_time - timedelta(days=1)
        elif 'last 30 days' in message.lower() or 'last month' in message.lower():
            end_time = now.replace(hour=23, minute=59, second=59, microsecond=0)
            start_time = end_time - timedelta(days=30)
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Default to last 7 days
            end_time = now.replace(hour=23, minute=59, second=59, microsecond=0)
            start_time = end_time - timedelta(days=7)
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return start_time, end_time
    
    def validate_date_range_and_give_feedback(
        self,
        start_time: datetime,
        end_time: datetime,
        installation_tz: str
    ) -> Tuple[bool, str]:
        """
        Validate date range and return user-friendly feedback for future dates.
        
        Args:
            start_time: Start datetime
            end_time: End datetime
            installation_tz: Installation timezone
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        from services.timezone import timezone_service
        
        validation = timezone_service.validate_date_range(start_time, end_time, installation_tz)
        
        if not validation.get('is_valid', True):
            warnings = validation.get('warnings', [])
            recommendations = validation.get('recommendations', [])
            
            error_msg = "❌ **Cannot analyze data for the requested time range**\n\n"
            
            if warnings:
                error_msg += "**Issues Found:**\n"
                for warning in warnings:
                    error_msg += f"• {warning}\n"
                error_msg += "\n"
            
            if recommendations:
                error_msg += "**Recommendations:**\n"
                for rec in recommendations:
                    error_msg += f"• {rec}\n"
                error_msg += "\n"
            
            error_msg += "💡 **Please adjust your date range to analyze historical data only.**"
            
            return False, error_msg
        
        return True, ""
            
    
    def format_comprehensive_uptime_analysis(
        self,
        tool_results: Dict[str, Any],
        installation_id: str,
        start_time: datetime,
        end_time: datetime,
        installation_tz: str
    ) -> str:
        """
        Generate a comprehensive uptime analysis in the standardized format.
        
        Args:
            tool_results: Results from running tools
            installation_id: Installation ID
            start_time: Start time
            end_time: End time
            installation_tz: Installation timezone
            
        Returns:
            Formatted comprehensive analysis string
        """
        if 'uptime' not in tool_results or 'error' in tool_results['uptime']:
            return "I apologize, but I cannot provide the uptime analysis due to data retrieval issues. Please verify the installation ID and try again."
        
        uptime_data = tool_results['uptime']
        machine_metrics = uptime_data.get('machine_metrics', [])
        summary = uptime_data.get('installation_summary', {})
        
        # Calculate total duration in hours for the request
        total_duration_hours = (end_time - start_time).total_seconds() / 3600.0
        
        # Build comprehensive response
        response_parts: List[str] = []
        
        # Header with apology and explanation
        response_parts.append("I apologize, but I cannot directly answer your specific question. However, I can provide you with comprehensive uptime analysis for this installation and time period:")
        response_parts.append("")
        
        # Elevator Information Section
        response_parts.append("**Elevator Information:**")
        
        for machine in machine_metrics:
            machine_id = machine.get('machine_id', 'Unknown')
            total_minutes = machine.get('total_minutes', 0)
            total_hours = total_minutes / 60.0
            uptime_minutes = machine.get('uptime_minutes', 0)
            uptime_hours = uptime_minutes / 60.0
            downtime_minutes = machine.get('downtime_minutes', 0) 
            downtime_hours = downtime_minutes / 60.0
            uptime_pct = machine.get('uptime_percentage', 0)
            downtime_pct = machine.get('downtime_percentage', 0)
            data_coverage_pct = machine.get('data_coverage_percentage', 0)
            has_data = machine.get('has_data', False)
            
            response_parts.append(f"**Elevator {machine_id}:**")
            
            if has_data and total_hours > 0:
                response_parts.append(f"- Total operational time: {total_hours:.1f} hours")
                response_parts.append(f"- Uptime: {uptime_hours:.1f} hours ({uptime_pct:.1f}%)")
                response_parts.append(f"- Downtime: {downtime_hours:.1f} hours ({downtime_pct:.1f}%)")
                
                # Data coverage explanation
                if data_coverage_pct < 100:
                    missing_dates = self._get_missing_dates_summary(machine.get('intervals', []), start_time, end_time, installation_tz)
                    response_parts.append(f"- Data coverage: {data_coverage_pct:.1f}% of requested period{missing_dates}")
                else:
                    response_parts.append(f"- Data coverage: Complete ({data_coverage_pct:.1f}%)")
            else:
                response_parts.append(f"- Total operational time: 0 hours (no data available)")
                response_parts.append(f"- Uptime: 0 hours (0%)")
                response_parts.append(f"- Downtime: 0 hours (0%)")
                response_parts.append(f"- Data coverage: No data for the requested period")
            
            response_parts.append("")
        
        # Installation-Level Aggregation Section
        response_parts.append("**Installation-Level Aggregation:**")
        response_parts.append("Overall metrics calculated by combining data from all elevators:")
        response_parts.append("")
        
        total_uptime_hours = summary.get('uptime_minutes', 0) / 60.0
        total_downtime_hours = summary.get('downtime_minutes', 0) / 60.0
        combined_total_hours = total_uptime_hours + total_downtime_hours
        installation_uptime_pct = summary.get('uptime_percentage', 0)
        data_coverage_pct = summary.get('data_coverage_percentage', 0)
        
        response_parts.append(f"- Combined uptime: {total_uptime_hours:.1f} hours")
        response_parts.append(f"- Combined total time: {combined_total_hours:.1f} hours")
        response_parts.append(f"- Installation uptime percentage: {installation_uptime_pct:.1f}% (calculated from available data)")
        response_parts.append(f"- Data coverage: {data_coverage_pct:.1f}% of requested {total_duration_hours:.0f}-hour period")
        response_parts.append("")
        
        # Daily Breakdown Section
        response_parts.append("**Daily Breakdown Calculation for date range selected:**")
        
        # Calculate days in range
        total_days = (end_time.date() - start_time.date()).days + 1
        response_parts.append(f"📅 Daily Data Availability Breakdown ({total_days} days):")
        
        # Generate daily breakdown for each elevator
        for machine in machine_metrics:
            machine_id = machine.get('machine_id', 'Unknown')
            intervals = machine.get('intervals', [])
            
            response_parts.append(f"   🏢 Elevator {machine_id}:")
            
            # Calculate daily data for this elevator
            daily_data = self._calculate_daily_breakdown_for_machine(
                intervals, start_time, end_time, installation_tz
            )
            
            for day_info in daily_data:
                date_str = day_info['date']
                expected_hours = day_info['expected_hours']
                actual_hours = day_info['actual_hours']
                availability_pct = day_info['availability_percentage']
                has_data = day_info['has_data']
                
                if has_data and actual_hours > 0:
                    response_parts.append(f"      • {date_str}: {actual_hours:.1f}h / {expected_hours:.1f}h ({availability_pct:.1f}%)")
                else:
                    response_parts.append(f"      • {date_str}: No data (0h / {expected_hours:.1f}h)")
            
            response_parts.append("")
        
        return "\n".join(response_parts)
    
    def _get_missing_dates_summary(self, intervals: List[Dict[str, Any]], start_time: datetime, end_time: datetime, installation_tz: str) -> str:
        """Generate a summary of missing date ranges."""
        if not intervals:
            return f", missing {start_time.strftime('%B %d')}-{end_time.strftime('%d, %Y')}"
        
        # For now, provide a simple summary
        # This could be enhanced to show specific missing date ranges
        return f", partial data from {start_time.strftime('%B %d')} to {end_time.strftime('%B %d, %Y')}"
    
    def _calculate_daily_breakdown_for_machine(
        self, 
        intervals: List[Dict[str, Any]], 
        start_time: datetime, 
        end_time: datetime,
        installation_tz: str
    ) -> List[Dict[str, Any]]:
        """Calculate daily breakdown for a specific machine."""
        from datetime import timedelta
        from services.timezone import timezone_service
        
        daily_data: List[Dict[str, Any]] = []
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            # Define day boundaries
            day_start_dt = timezone_service.parse_iso_with_timezone(
                f"{current_date}T00:00:00", installation_tz
            )
            day_end_dt = timezone_service.parse_iso_with_timezone(
                f"{current_date}T23:59:59", installation_tz
            )
            
            if not day_start_dt or not day_end_dt:
                current_date += timedelta(days=1)
                continue
            
            # Ensure we don't go beyond the requested range
            day_start_dt = max(day_start_dt, start_time)
            day_end_dt = min(day_end_dt, end_time)
            
            # Calculate expected hours for this day
            expected_minutes = (day_end_dt - day_start_dt).total_seconds() / 60.0
            expected_hours = expected_minutes / 60.0
            
            # Calculate actual data hours for this day
            actual_minutes = 0.0
            has_data = False
            
            for interval in intervals:
                interval_start = timezone_service.parse_iso_with_timezone(interval['start'], installation_tz)
                interval_end = timezone_service.parse_iso_with_timezone(interval['end'], installation_tz)
                
                if not interval_start or not interval_end:
                    continue
                
                # Check if interval overlaps with this day
                overlap_start = max(interval_start, day_start_dt)
                overlap_end = min(interval_end, day_end_dt)
                
                if overlap_start < overlap_end:
                    # There's an overlap
                    overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60.0
                    actual_minutes += overlap_minutes
                    has_data = True
            
            actual_hours = actual_minutes / 60.0
            availability_percentage = (actual_hours / expected_hours * 100) if expected_hours > 0 else 0.0
            
            daily_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'expected_hours': expected_hours,
                'actual_hours': actual_hours,
                'availability_percentage': availability_percentage,
                'has_data': has_data
            })
            
            current_date += timedelta(days=1)
        
        return daily_data

    def process_query(
        self, 
        message: str, 
        installation_id: str,
        start_iso: Optional[str] = None,
        end_iso: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the tool chain and LLM.
        
        Args:
            message: User's question
            installation_id: Selected installation ID
            start_iso: Optional start time in ISO format
            end_iso: Optional end time in ISO format
            
        Returns:
            Dictionary with answer and metadata
        """
        try:
            # Get installation info
            try:
                cosmos_service = get_cosmos_service()
                installations = cosmos_service.get_installations()
            except Exception as e:
                logger.warning(f"Could not fetch installations from Cosmos DB: {e}. Using fallback data.")
                installations = []
            
            # Always add demo installations for testing purposes
            demo_installations = [
                {"installationId": "demo-installation-1", "timezone": "America/New_York"},
                {"installationId": "demo-installation-2", "timezone": "America/Chicago"},
                {"installationId": "demo-installation-3", "timezone": "America/Los_Angeles"}
            ]
            installations.extend(demo_installations)
            
            installation_info = next(
                (inst for inst in installations if inst['installationId'] == installation_id),
                None
            )
            
            if not installation_info:
                return {
                    'answer': f"Installation {installation_id} not found.",
                    'error': True
                }
            
            installation_tz = installation_info['timezone']
            
            # If we're in fallback mode (demo installations), provide a demo response
            if installation_id.startswith('demo-'):
                demo_response = (
                    f"🔧 **Demo Mode Response for {installation_id}**\n\n"
                    f"You asked: \"{message}\"\n\n"
                    "This is a demonstration of the Elevator Operations Analyst. "
                    "In normal operation, I would:\n"
                    "• Query real elevator data from Azure Cosmos DB\n"
                    "• Analyze uptime/downtime patterns\n"
                    "• Provide detailed operational metrics\n"
                    "• Generate insights about elevator performance\n\n"
                    "To get real data analysis, please configure your Azure Cosmos DB connection "
                    "and ensure your LM Studio server is running."
                )
                
                return {
                    'answer': demo_response,
                    'metadata': {
                        'demo_mode': True,
                        'installation_id': installation_id,
                        'timezone': installation_tz
                    }
                }
            
            # Parse time range
            if start_iso and end_iso:
                start_time = timezone_service.parse_iso_with_timezone(start_iso, installation_tz)
                
                # For end dates, if only date is provided (no time), assume end of day
                if 'T' not in end_iso:
                    # Just date provided, make it end of day
                    end_time = timezone_service.parse_iso_with_timezone(f"{end_iso}T23:59:59", installation_tz)
                else:
                    end_time = timezone_service.parse_iso_with_timezone(end_iso, installation_tz)
                    
                if not start_time or not end_time:
                    return {
                        'answer': "Invalid date format. Please use ISO format (YYYY-MM-DD).",
                        'error': True
                    }
                
                # Validate the parsed dates for future date issues
                is_valid, error_message = self.validate_date_range_and_give_feedback(
                    start_time, end_time, installation_tz
                )
                
                if not is_valid:
                    return {
                        'answer': error_message,
                        'error': True,
                        'metadata': {
                            'installation_id': installation_id,
                            'timezone': installation_tz,
                            'validation_error': True
                        }
                    }
            else:
                start_time, end_time = self.parse_time_range(message, installation_tz)
                
                # Also validate default time ranges for future dates
                is_valid, error_message = self.validate_date_range_and_give_feedback(
                    start_time, end_time, installation_tz
                )
                
                if not is_valid:
                    return {
                        'answer': error_message,
                        'error': True,
                        'metadata': {
                            'installation_id': installation_id,
                            'timezone': installation_tz,
                            'validation_error': True
                        }
                    }
            
            # Classify intent and select tools
            tool_names = self.classify_intent(message)
            
            # Run tools and collect data
            tool_results: Dict[str, Any] = {}
            for tool_name in tool_names:
                try:
                    if tool_name == 'elevator_count':
                        # Handle elevator count directly
                        result = self.get_elevator_count(installation_id)
                        tool_results[tool_name] = result
                    elif tool_name in self.tools:
                        tool = self.tools[tool_name]
                        result = tool.run(
                            installation_id=installation_id,
                            tz=installation_tz,
                            start=start_time,
                            end=end_time
                        )
                        tool_results[tool_name] = result
                except Exception as e:
                    logger.error(f"Error running tool {tool_name}: {e}")
                    tool_results[tool_name] = {'error': str(e)}
            
            # Check if this is an uptime-related query that should get comprehensive analysis
            is_uptime_query = any(keyword in message.lower() for keyword in [
                'uptime', 'downtime', 'availability', 'working', 'broken', 
                'operational', 'service', 'failure', 'outage'
            ])
            
            # Check if no specific tool can handle the query but we have installation and date range
            is_fallback_query = (
                installation_id and start_time and end_time and 
                not any(keyword in message.lower() for keyword in [
                    'door', 'passenger', 'hall call', 'how many elevator'
                ])
            )
            
            # Provide comprehensive uptime analysis for uptime queries or fallback scenarios
            if (is_uptime_query or is_fallback_query) and 'uptime' in tool_results:
                comprehensive_analysis = self.format_comprehensive_uptime_analysis(
                    tool_results, installation_id, start_time, end_time, installation_tz
                )
                
                return {
                    'answer': comprehensive_analysis,
                    'tool_results': tool_results,
                    'installation_id': installation_id,
                    'installation_tz': installation_tz,
                    'time_range': {
                        'start': start_time.isoformat(),
                        'end': end_time.isoformat()
                    },
                    'analysis_type': 'comprehensive_uptime'
                }
            
            # For non-uptime queries, use the LLM response
            # Generate LLM response
            system_prompt = llm_service.get_system_prompt(installation_tz)
            
            # Format tool results for LLM context
            tool_context = self._format_tool_context(tool_results, installation_id, start_time, end_time)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {message}\n\nInstallation: {installation_id}\nTime range: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')} ({installation_tz})"},
                {"role": "user", "content": f"Tool Results:\n{tool_context}"}
            ]
            
            llm_response = llm_service.chat_completion(messages)
            
            if not llm_response:
                return {
                    'answer': "Sorry, I couldn't generate a response. Please check that the LM Studio server is running.",
                    'error': True
                }
            
            return {
                'answer': llm_response,
                'tool_results': tool_results,
                'installation_id': installation_id,
                'installation_tz': installation_tz,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'answer': f"An error occurred processing your request: {str(e)}",
                'error': True
            }
    
    def _format_tool_context(
        self, 
        tool_results: Dict[str, Any], 
        installation_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> str:
        """Format tool results for LLM context."""
        context_parts: List[str] = []
        
        for tool_name, result in tool_results.items():
            if 'error' in result:
                context_parts.append(f"{tool_name}: Error - {result['error']}")
            else:
                if tool_name == 'elevator_count':
                    # Format elevator count results
                    elevator_count = result.get('elevator_count', 0)
                    elevator_ids = result.get('elevator_ids', [])
                    
                    context_parts.append(f"""
Elevator Count Analysis for Installation {installation_id}:
- Total Elevators: {elevator_count}
- Elevator IDs: {', '.join(map(str, elevator_ids)) if elevator_ids else 'None found'}
""")
                    
                    interpretation = result.get('interpretation', [])
                    if interpretation:
                        context_parts.append("Analysis Summary:")
                        for line in interpretation:
                            if line.strip():
                                context_parts.append(f"  {line}")
                                
                elif tool_name == 'uptime':
                    # Format uptime results with clear separation
                    summary = result.get('installation_summary', {})
                    machine_metrics = result.get('machine_metrics', [])
                    
                    # Installation-level summary
                    context_parts.append(f"""
Uptime Analysis for Installation {installation_id}:
- Time Period: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}
- Total Elevators Found: {len(machine_metrics)}
- Overall Installation Uptime: {summary.get('uptime_percentage', 0):.1f}%
- Overall Installation Downtime: {summary.get('downtime_percentage', 0):.1f}%
""")
                    
                    # Individual elevator details
                    if machine_metrics:
                        context_parts.append("Individual Elevator Performance:")
                        for machine in machine_metrics:
                            machine_id = machine.get('machine_id', 'Unknown')
                            uptime_pct = machine.get('uptime_percentage', 0)
                            uptime_human = machine.get('uptime_human', 'N/A')
                            downtime_human = machine.get('downtime_human', 'N/A')
                            has_data = machine.get('has_data', False)
                            
                            if has_data:
                                context_parts.append(f"  • Elevator {machine_id}: {uptime_pct:.1f}% uptime ({uptime_human} operational, {downtime_human} downtime)")
                            else:
                                context_parts.append(f"  • Elevator {machine_id}: No data available for this time period")
                    
                    # Enhanced interpretation
                    interpretation = result.get('interpretation', [])
                    if interpretation:
                        context_parts.append("\nDetailed Analysis:")
                        for line in interpretation:
                            if line.strip():  # Only add non-empty lines
                                context_parts.append(f"  {line}")
                                
                else:
                    # Format other tool results
                    context_parts.append(f"{tool_name}: {result.get('event_count', 0)} events found")
        
        return "\n".join(context_parts)


# Global instance
query_orchestrator = QueryOrchestrator()
