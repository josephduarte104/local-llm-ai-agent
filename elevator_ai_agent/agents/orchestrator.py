"""Orchestrator for routing user queries to appropriate tools and generating responses."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from ..services.cosmos import get_cosmos_service
from ..services.llm import llm_service
from ..services.timezone import timezone_service
from ..tools.car_mode_changed import car_mode_changed_tool
from ..tools.basic_tools import door_tool, passenger_report_tool, hall_call_accepted_tool

logger = logging.getLogger(__name__)


import json

class QueryOrchestrator:
    """Orchestrates user queries by routing to tools and generating LLM responses."""

    def __init__(self):
        """Initialize orchestrator with available tools."""
        self.tools = {
            'uptime_analysis': car_mode_changed_tool,
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

    def process_query(
        self,
        message: str,
        installation_id: str,
        start_iso: Optional[str] = None,
        end_iso: Optional[str] = None,
        today_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query by calling tools and generating an LLM response.
        """
        try:
            # 1. Get installation info
            try:
                cosmos_service = get_cosmos_service()
                installations = cosmos_service.get_installations()
            except Exception as e:
                logger.warning(f"Could not fetch installations: {e}. Using fallback.")
                installations = []

            demo_installations = [
                {"installationId": "demo-installation-1", "timezone": "America/New_York"},
                {"installationId": "demo-installation-2", "timezone": "America/Chicago"},
                {"installationId": "demo-installation-3", "timezone": "America/Los_Angeles"}
            ]
            installations.extend(demo_installations)
            
            installation_info = next((inst for inst in installations if inst['installationId'] == installation_id), None)

            if not installation_info:
                return {'answer': f"Installation {installation_id} not found.", 'error': True}

            installation_tz = installation_info['timezone']

            # Handle demo mode
            if installation_id.startswith('demo-'):
                # (Keeping demo mode logic for now)
                demo_response = (
                    f"🔧 **Demo Mode Response for {installation_id}**\n\n"
                    f"You asked: \"{message}\"\n\n"
                    "This is a demonstration of the Elevator Operations Analyst. "
                    "In a real environment, I would now be querying the database "
                    "and using an AI model to generate a detailed analysis."
                )
                return {'answer': demo_response, 'metadata': {'demo_mode': True}}

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

            # 3. Run tools to get structured data
            # For this refactoring, we'll assume the primary tool is always uptime_analysis.
            # A more advanced implementation would use the LLM to select the tool.
            tool_name = 'uptime_analysis'
            tool = self.tools[tool_name]
            
            tool_results = tool.run(
                installation_id=installation_id,
                tz=installation_tz,
                start=start_time,
                end=end_time,
                today_override=today_override_dt
            )

            # Preserve the original tool_results to be returned later
            original_tool_results = tool_results.copy()
            
            # 4. Generate response using the LLM
            system_prompt = self._get_system_prompt(installation_tz)
            
            # Create a cleaned version of the tool results for the LLM prompt
            prompt_tool_results = json.loads(json.dumps(tool_results, default=str)) # Deep copy
            if 'machine_metrics' in prompt_tool_results and isinstance(prompt_tool_results['machine_metrics'], list):
                for metric in prompt_tool_results['machine_metrics']:
                    metric.pop('intervals', None)
                    metric.pop('daily_availability', None)

            tool_context = json.dumps(prompt_tool_results, indent=2, default=str)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please analyze the following data for installation {installation_id} from {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')} and answer this question: '{message}'\n\n```json\n{tool_context}\n```"},
            ]

            llm_response = llm_service.chat_completion(messages)
            
            if not llm_response:
                return {'answer': "Sorry, I couldn't generate a response. Please check that the LM Studio server is running.", 'error': True}

            return {
                'answer': llm_response,
                'tool_results': original_tool_results, # Return the original, detailed results
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
"""


# Global instance
query_orchestrator = QueryOrchestrator()
