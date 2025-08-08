"""Orchestrator for routing user queries to appropriate tools and generating responses."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from ..services.cosmos import get_cosmos_service
from ..services.llm import llm_service
from ..services.timezone import timezone_service
from ..services.data_coverage import data_coverage_service
from ..tools.car_mode_changed import car_mode_changed_tool
from ..tools.door_cycles import door_cycles_tool
from ..tools.data_coverage_tool import data_coverage_tool
from ..tools.basic_tools import door_tool, passenger_report_tool, hall_call_accepted_tool

logger = logging.getLogger(__name__)


import json

class QueryOrchestrator:
    """Orchestrates user queries by routing to tools and generating LLM responses."""

    def __init__(self):
        """Initialize orchestrator with available tools."""
        self.tools = {
            'uptime_analysis': car_mode_changed_tool,
            'door_cycle_analysis': door_cycles_tool,
            'data_coverage_analysis': data_coverage_tool,
            # The following tools are stubs and would need to be implemented
            # 'door_analysis': door_tool,
            # 'passenger_analysis': passenger_report_tool,
            # 'hall_call_analysis': hall_call_accepted_tool,
        }

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
        # (This method can be kept as is for now, but could be improved with LLM)
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(installation_tz)
        now = datetime.now(tz)
        
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

    def _select_appropriate_tool(self, message_lower: str) -> str:
        """Select the most appropriate tool based on the user's question."""
        
        # Data coverage and quality questions
        data_coverage_keywords = [
            'coverage', 'data quality', 'data availability', 'missing data', 'data gaps',
            'incomplete data', 'data completeness', 'reporting', 'silent', 'no data',
            'data span', 'event count', 'how much data', 'data reliability',
            'data issues', 'connectivity', 'sensors', 'collection', 'monitoring'
        ]
        
        # Door operation questions  
        door_keywords = ['door', 'cycle', 'open', 'close', 'deck', 'side']
        
        # Check for data coverage questions first (highest priority for new capability)
        if any(keyword in message_lower for keyword in data_coverage_keywords):
            return 'data_coverage_analysis'
        
        # Check for door-related questions
        elif any(keyword in message_lower for keyword in door_keywords):
            return 'door_cycle_analysis'
        
        # Default to uptime analysis for operational questions
        else:
            return 'uptime_analysis'

    def process_query(
        self,
        message: str,
        installation_id: str,
        start_iso: Optional[str] = None,
        end_iso: Optional[str] = None,
        today_override: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.debug(f"Orchestrator received query: message='{message}', installation_id='{installation_id}', start_iso='{start_iso}', end_iso='{end_iso}', today_override='{today_override}'")

        try:
            # 1. Get installation info
            cosmos_service = get_cosmos_service()
            installations = cosmos_service.get_installations()
            
            # Add the provided installation_id to the list for validation
            if not any(inst['installationId'] == installation_id for inst in installations):
                # In a real application, you might want to fetch the timezone
                # for the given installation_id here if it's not in the list.
                # For this case, we'll add it with a default timezone if not found.
                installations.append({
                    "installationId": installation_id,
                    "timezone": "UTC" # Default timezone
                })

            installation_info = next((inst for inst in installations if inst['installationId'] == installation_id), None)

            if not installation_info:
                # This should ideally not be reached if the above logic is sound
                return {'answer': f"Installation {installation_id} not found.", 'error': True}

            installation_tz = installation_info.get('timezone', 'UTC') # Default to UTC if timezone is missing

            # 2. Determine time range
            if start_iso and end_iso:
                start_time = timezone_service.parse_iso_with_timezone(start_iso, installation_tz)
                if 'T' not in end_iso:
                    end_time = timezone_service.parse_iso_with_timezone(f"{end_iso}T23:59:59", installation_tz)
                else:
                    end_time = timezone_service.parse_iso_with_timezone(end_iso, installation_tz)
                if not start_time or not end_time:
                    return {'answer': "Invalid date format. Please use ISO format (YYYY-MM-DD).", 'error': True}
            else:
                start_time, end_time = self.parse_time_range(message, installation_tz)

            today_override_dt = None
            if today_override:
                today_override_dt = timezone_service.parse_iso_with_timezone(
                    today_override, installation_tz
                )

            # 3. Analyze data coverage for the requested period
            data_coverage_report = data_coverage_service.analyze_coverage(
                installation_id=installation_id,
                start_time=start_time,
                end_time=end_time,
                installation_tz=installation_tz
            )
            
            logger.debug(f"Data coverage: {data_coverage_report.overall_coverage_percentage:.1f}% coverage, "
                        f"{data_coverage_report.machines_with_data}/{data_coverage_report.machines_total} elevators with data")

            # 4. Run tools to get structured data
            # Enhanced tool selection based on question content
            tool_name = self._select_appropriate_tool(message.lower())
            
            logger.info(f"Selected tool: {tool_name} for query: {message}")
            
            tool = self.tools[tool_name]
            
            tool_results = tool.run(
                installation_id=installation_id,
                tz=installation_tz,
                start=start_time,
                end=end_time,
                today_override=today_override_dt
            )

            logger.debug(f"Tool '{tool_name}' returned data: {json.dumps(tool_results, default=str, indent=2)}")

            # Pre-LLM check: If no elevators had data, return a direct response with coverage info
            if tool_results.get('installation_summary', {}).get('elevators_with_data') == 0:
                logger.info(f"No data found for installation {installation_id}. Bypassing LLM.")
                
                # Generate comprehensive no-data response with coverage details
                coverage_details = self._format_coverage_summary(data_coverage_report)
                
                answer = (
                    f"I could not find any operational data for installation "
                    f"`{installation_id}` in the specified date range "
                    f"({start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}).\n\n"
                    f"**Data Coverage Summary:**\n{coverage_details}\n\n"
                    "This could mean:\n"
                    "- The elevators were not reporting data during this period.\n"
                    "- The installation ID or date range might be incorrect.\n\n"
                    "Please verify the details and try again."
                )
                return {
                    'answer': answer,
                    'tool_results': tool_results,
                    'data_coverage': data_coverage_report.to_dict(),
                    'installation_id': installation_id,
                    'installation_tz': installation_tz,
                    'time_range': {
                        'start': start_time.isoformat(),
                        'end': end_time.isoformat()
                    }
                }

            # Preserve the original tool_results to be returned later
            original_tool_results = tool_results.copy()
            
            # 5. Generate response using the LLM with data coverage context
            system_prompt = self._get_system_prompt(installation_tz)
            
            # Create a cleaned version of the tool results for the LLM prompt
            prompt_tool_results = json.loads(json.dumps(tool_results, default=str)) # Deep copy
            if 'machine_metrics' in prompt_tool_results and isinstance(prompt_tool_results['machine_metrics'], list):
                for metric in prompt_tool_results['machine_metrics']:
                    metric.pop('intervals', None)
                    metric.pop('daily_availability', None)

            # Add data coverage information to the LLM context
            coverage_summary = self._format_coverage_summary(data_coverage_report)
            tool_context = json.dumps(prompt_tool_results, indent=2, default=str)
            logger.debug(f"Context passed to LLM:\n{tool_context}")

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please analyze the following data for installation {installation_id} from {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')} and answer this question: '{message}'\n\n**IMPORTANT:** Always include the data coverage summary at the end of your response.\n\n**Data Coverage Summary:**\n{coverage_summary}\n\n**Analysis Data:**\n```json\n{tool_context}\n```"},
            ]

            llm_response = llm_service.chat_completion(messages)
            
            if not llm_response:
                return {'answer': "Sorry, I couldn't generate a response. Please check that the LM Studio server is running.", 'error': True}

            logger.debug(f"LLM generated response:\n{llm_response}")

            # Ensure coverage information is included in the final response
            final_answer = self._ensure_coverage_in_response(llm_response, coverage_summary)

            return {
                'answer': final_answer,
                'tool_results': original_tool_results, # Return the original, detailed results
                'data_coverage': data_coverage_report.to_dict(),
                'installation_id': installation_id,
                'installation_tz': installation_tz,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {'answer': f"An error occurred processing your request: {str(e)}", 'error': True}

    def _get_system_prompt(self, timezone: str) -> str:
        """Generates the system prompt for the LLM."""
        return f"""
You are an expert Elevator Operations Analyst. Your role is to analyze elevator operational data and provide clear, concise, and helpful answers to users.

**Instructions:**
1.  You will be given a user's question and a JSON object containing structured data retrieved from the database.
2.  Analyze the provided JSON data to answer the user's question.
3.  Format your response using Markdown for readability (e.g., headings, bold text, lists).
4.  Be helpful and proactive. If the data reveals interesting patterns or issues, mention them.
5.  If the data contains warnings (e.g., in the `date_validation` field), incorporate them into your analysis to explain limitations or guide the user. For example, if data for a future date was requested, explain that you can only analyze historical data up to the present.
6.  When presenting numerical data like uptime percentages, round to one decimal place.
7.  When mentioning time, use hours or days as appropriate (e.g., convert minutes to hours).
8.  Do not just repeat the JSON data. Synthesize it into a human-readable analysis.
9.  The current timezone for the installation is {timezone}. All timestamps in your response should be assumed to be in this timezone.
10. Do not include the raw JSON data in your final response. Your response should be a direct answer to the user's question, based on your analysis of the data.
11. **ALWAYS include the provided data coverage summary at the end of your response.** This helps users understand the completeness and reliability of the analysis.

**Data Coverage Questions:**
When users ask about data coverage, quality, availability, or related topics, you can now provide detailed answers including:
- Overall coverage percentages and data quality assessments
- Machine-specific reporting status and coverage details
- Data gaps, missing periods, and reliability issues
- Event counts and data span information
- Recommendations for improving data collection
- Silent or non-reporting elevators identification
- Data type availability (CarModeChanged, Door events, etc.)
- Coverage trends and daily breakdowns

**Example of a good response:**

> ### Uptime Analysis for Installation 1234
>
> For the period from July 1, 2024, to July 7, 2024, the overall uptime for the 3 elevators at this installation was **98.5%**.
>
> **Elevator Performance:**
> *   **Elevator 1:** 99.2% uptime (166.7 hours)
> *   **Elevator 2:** 97.5% uptime (163.8 hours)
> *   **Elevator 3:** 98.8% uptime (166.0 hours)
>
> All elevators are performing well, with uptime percentages above the 95% industry standard.
>
> ---
> **Data Coverage Summary:**
> ✅ **95.2%** overall data coverage | 📊 **3/3** elevators with data | 📈 **CarModeChanged** events available
"""

    def _format_coverage_summary(self, coverage_report) -> str:
        """Format data coverage information for display."""
        coverage_pct = coverage_report.overall_coverage_percentage
        machines_info = f"{coverage_report.machines_with_data}/{coverage_report.machines_total}"
        
        # Choose appropriate emoji based on coverage percentage
        if coverage_pct >= 90:
            coverage_emoji = "✅"
        elif coverage_pct >= 70:
            coverage_emoji = "⚠️"
        else:
            coverage_emoji = "❌"
        
        summary_parts = [
            f"{coverage_emoji} **{coverage_pct:.1f}%** overall data coverage",
            f"📊 **{machines_info}** elevators with data"
        ]
        
        # Add data types available
        if coverage_report.data_types_available:
            data_types_str = ", ".join(coverage_report.data_types_available)
            summary_parts.append(f"📈 **{data_types_str}** events available")
        
        # Add warnings if any
        if coverage_report.coverage_warnings:
            for warning in coverage_report.coverage_warnings[:2]:  # Show first 2 warnings
                summary_parts.append(warning)
        
        return " | ".join(summary_parts)
    
    def _ensure_coverage_in_response(self, llm_response: str, coverage_summary: str) -> str:
        """Ensure that data coverage information is included in the response."""
        # Check if the LLM already included coverage information
        if "data coverage" in llm_response.lower() or "coverage summary" in llm_response.lower():
            return llm_response
        
        # If not, append it
        separator = "\n\n---\n**Data Coverage Summary:**\n"
        return llm_response + separator + coverage_summary


# Global instance
query_orchestrator = QueryOrchestrator()
