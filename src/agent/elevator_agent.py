"""
Main Elevator Operations Agent
Coordinates between LLM, tools, and database to answer elevator questions
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pytz

from ..config.settings import Settings
from ..database.cosmos_client import CosmosDBClient
from ..tools.uptime_calculator import compute_uptime_downtime, explain_downtime

class ElevatorAgent:
    """
    Main agent class that orchestrates elevator operations analysis
    """
    
    def __init__(self, settings: Settings):
        """Initialize the agent with configuration"""
        self.settings = settings
        self.cosmos_client = None
        self.llm_client = None
        self.system_prompt = self._create_system_prompt()
        
    def initialize(self) -> bool:
        """Initialize the agent components (synchronous version for Flask)"""
        try:
            print("🏢 Initializing Cosmos DB...")
            
            # Initialize Cosmos DB client
            from ..database.cosmos_client import CosmosDBClient
            self.cosmos_client = CosmosDBClient(
                self.settings.cosmosdb_endpoint,
                self.settings.cosmosdb_key,
                self.settings.cosmosdb_database,
                self.settings.cosmosdb_container
            )
            
            try:
                cosmos_ok = self.cosmos_client.initialize_sync()
                if not cosmos_ok:
                    print("Failed to initialize Cosmos DB client")
            except Exception as e:
                print(f"Failed to initialize Cosmos DB: {e}")
                print("⚠️  Agent will work in demo mode without database access")
            
            # Initialize LLM client
            from src.llm.client import LLMClient
            self.llm_client = LLMClient(self.settings)
            
            # Test LLM connection (skip for now to avoid hanging)
            print("✅ LLM client initialized (connection test skipped)")
            
            print("✅ Agent initialized successfully")
            return True
            
        except Exception as e:
            print(f"Failed to initialize agent: {e}")
            return False
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the LLM"""
        return """You are an AI agent that analyzes elevator event data stored in Azure Cosmos DB to compute uptime/downtime and explain incidents, returning answers in the installation's local time zone.

Your mission:
- Analyze elevator CarModeChanged events to compute uptime/downtime
- Provide timezone-aware analysis for each installation
- Explain downtime incidents with detailed reasoning
- Use memory-efficient patterns for large datasets

Key Rules:
1. UPTIME modes: ANS, ATT, CHC, CTL, DCP, DEF, DHB, DTC, DTO, EFO, EFS, EHS, EPC, EPR, EPW, IDL, INI, INS, ISC, LNS, NOR, PKS, PRK, RCY, REC, SRO, STP
2. DOWNTIME modes: COR, DBF, DLF, ESB, HAD, HBP, NAV
3. Always use installation's local timezone for time calculations
4. "Last week" means ISO week (Monday 00:00 to Sunday 23:59:59) in local timezone
5. Report both percentages (2 decimals) and minutes/hours
6. Offer downtime explanations when downtime > 0

Available tools:
- read_installations(): Get all installations with timezone info
- query_events(): Get CarModeChanged events for analysis
- get_prior_mode(): Get last mode before time window
- compute_uptime_downtime(): Calculate uptime/downtime metrics
- explain_downtime(): Get detailed downtime explanations

Always state the timezone used and exact date ranges in responses."""

    def _get_system_prompt_with_tools(self) -> str:
        """Get system prompt enhanced with tool descriptions"""
        base_prompt = self._create_system_prompt()
        tools = self._get_tool_definitions()
        
        tool_descriptions = []
        for tool in tools:
            func = tool["function"]
            tool_descriptions.append(f"- {func['name']}: {func['description']}")
        
        return f"{base_prompt}\n\nTo help users, you can call these functions:\n" + "\n".join(tool_descriptions)

    def process_message(self, user_message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Process a user message and return response (fully synchronous)
        
        Args:
            user_message: The user's question/request
            conversation_history: Previous messages in conversation
            
        Returns:
            Dict with response content and any tool results
        """
        try:
            # Create a simple system prompt without tool definitions to avoid any async calls
            system_prompt = """You are an AI agent that analyzes elevator event data stored in Azure Cosmos DB to compute uptime/downtime and explain incidents.

Your mission:
- Analyze elevator CarModeChanged events to compute uptime/downtime
- Provide timezone-aware analysis for each installation
- Explain downtime incidents with detailed reasoning

Key Rules:
1. UPTIME modes: ANS, ATT, CHC, CTL, DCP, DEF, DHB, DTC, DTO, EFO, EFS, EHS, EPC, EPR, EPW, IDL, INI, INS, ISC, LNS, NOR, PKS, PRK, RCY, REC, SRO, STP
2. DOWNTIME modes: COR, DBF, DLF, ESB, HAD, HBP, NAV
3. Always use installation's local timezone for time calculations
4. "Last week" means ISO week (Monday 00:00 to Sunday 23:59:59) in local timezone
5. Report both percentages (2 decimals) and minutes/hours

Always state the timezone used and exact date ranges in responses."""
            
            # Create a focused user prompt
            user_prompt = f"User question: {user_message}"
            
            # Query the LLM
            llm_response = self.llm_client.query(user_prompt, system_prompt)
            
            if llm_response.startswith("Error:"):
                return {
                    "content": f"❌ {llm_response}",
                    "tool_results": []
                }
            
            # Return simple response structure
            return {
                "content": llm_response,
                "tool_results": []
            }
            
        except Exception as e:
            return {
                "content": f"❌ Error processing message: {str(e)}",
                "tool_results": []
            }
    
    def _get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions for the LLM"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_installations",
                    "description": "Get all installations with their timezone information",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "query_events",
                    "description": "Query CarModeChanged events for analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "installationId": {"type": "string", "description": "Installation ID"},
                            "dataType": {"type": "string", "description": "Event type (CarModeChanged)"},
                            "startIso": {"type": "string", "description": "Start time in ISO format"},
                            "endIso": {"type": "string", "description": "End time in ISO format"},
                            "machineIds": {"type": "array", "items": {"type": "integer"}, "description": "Optional machine IDs"}
                        },
                        "required": ["installationId", "dataType", "startIso", "endIso"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_prior_mode", 
                    "description": "Get last CarModeChanged before start time",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "installationId": {"type": "string", "description": "Installation ID"},
                            "startIso": {"type": "string", "description": "Start time in ISO format"},
                            "machineIds": {"type": "array", "items": {"type": "integer"}, "description": "Optional machine IDs"}
                        },
                        "required": ["installationId", "startIso"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compute_uptime_downtime",
                    "description": "Compute uptime/downtime analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "installationId": {"type": "string", "description": "Installation ID"},
                            "timezone": {"type": "string", "description": "IANA timezone name"},
                            "startIso": {"type": "string", "description": "Start time in ISO format"},
                            "endIso": {"type": "string", "description": "End time in ISO format"},
                            "eventsJson": {"type": "string", "description": "JSON string with events and prior modes"}
                        },
                        "required": ["installationId", "timezone", "startIso", "endIso", "eventsJson"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "explain_downtime",
                    "description": "Explain downtime intervals for a specific machine",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "installationId": {"type": "string", "description": "Installation ID"},
                            "machineId": {"type": "integer", "description": "Machine ID"},
                            "timezone": {"type": "string", "description": "IANA timezone name"},
                            "startIso": {"type": "string", "description": "Start time in ISO format"},
                            "endIso": {"type": "string", "description": "End time in ISO format"},
                            "eventsJson": {"type": "string", "description": "JSON string with events and prior modes"}
                        },
                        "required": ["installationId", "machineId", "timezone", "startIso", "endIso", "eventsJson"]
                    }
                }
            }
        ]
    
    async def _execute_tool_call(self, tool_call: Dict) -> Dict[str, Any]:
        """Execute a tool call and return results"""
        function_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])
        
        if function_name == "read_installations":
            return await self._tool_read_installations()
        elif function_name == "query_events":
            return await self._tool_query_events(**arguments)
        elif function_name == "get_prior_mode":
            return await self._tool_get_prior_mode(**arguments)
        elif function_name == "compute_uptime_downtime":
            return await self._tool_compute_uptime_downtime(**arguments)
        elif function_name == "explain_downtime":
            return await self._tool_explain_downtime(**arguments)
        else:
            return {"error": f"Unknown tool: {function_name}"}
    
    async def _tool_read_installations(self) -> Dict[str, Any]:
        """Tool: Read installations"""
        try:
            installations = await self.cosmos_client.get_installations()
            return {"installations": installations}
        except Exception as e:
            return {"error": f"Failed to read installations: {str(e)}"}
    
    async def _tool_query_events(self, **kwargs) -> Dict[str, Any]:
        """Tool: Query events"""
        try:
            return await self.cosmos_client.query_events(**kwargs)
        except Exception as e:
            return {"error": f"Failed to query events: {str(e)}"}
    
    async def _tool_get_prior_mode(self, **kwargs) -> Dict[str, Any]:
        """Tool: Get prior mode"""
        try:
            return await self.cosmos_client.get_prior_mode(**kwargs)
        except Exception as e:
            return {"error": f"Failed to get prior mode: {str(e)}"}
    
    async def _tool_compute_uptime_downtime(self, **kwargs) -> Dict[str, Any]:
        """Tool: Compute uptime/downtime"""
        try:
            result = compute_uptime_downtime(**kwargs)
            return result
        except Exception as e:
            return {"error": f"Failed to compute uptime/downtime: {str(e)}"}
    
    async def _tool_explain_downtime(self, **kwargs) -> Dict[str, Any]:
        """Tool: Explain downtime"""
        try:
            result = explain_downtime(**kwargs)
            return result
        except Exception as e:
            return {"error": f"Failed to explain downtime: {str(e)}"}
    
    def _format_tool_results(self, tool_results: List[Dict]) -> str:
        """Format tool results for LLM context"""
        formatted = ""
        for result in tool_results:
            if "error" in result:
                formatted += f"❌ Tool Error: {result['error']}\n\n"
            else:
                formatted += f"Tool Result:\n{json.dumps(result, indent=2)}\n\n"
        return formatted
    
    def get_last_week_iso_range(self, timezone_name: str) -> tuple[str, str]:
        """Get ISO week range for last week in given timezone"""
        try:
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)
            
            # Get start of current week (Monday)
            days_since_monday = now.weekday()
            start_of_this_week = (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            
            # Last week
            start_of_last_week = start_of_this_week - timedelta(weeks=1)
            end_of_last_week = start_of_this_week - timedelta(microseconds=1)
            
            return start_of_last_week.isoformat(), end_of_last_week.isoformat()
            
        except Exception as e:
            print(f"Error calculating last week range: {e}")
            # Fallback to UTC
            now = datetime.now(pytz.UTC)
            days_since_monday = now.weekday()
            start_of_this_week = (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            start_of_last_week = start_of_this_week - timedelta(weeks=1)
            end_of_last_week = start_of_this_week - timedelta(microseconds=1)
            
            return start_of_last_week.isoformat(), end_of_last_week.isoformat()
    
    async def close(self):
        """Clean up resources"""
        if self.cosmos_client:
            self.cosmos_client.close()
