"""Car Mode Changed analysis tool."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from .base import BaseTool
from ..services.uptime import uptime_service


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
        today_override: Optional[datetime] = None,
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
            Dictionary with uptime/downtime metrics
        """
        # The uptime service now handles date validation and returns structured data.
        # This tool's responsibility is to simply call the service and return the results.
        metrics = uptime_service.get_uptime_metrics(
            installation_id=installation_id,
            start_time=start,
            end_time=end,
            installation_tz=tz,
            machine_id=machine_id,
            today_override=today_override
        )
        
        return metrics


# Tool instance
car_mode_changed_tool = CarModeChangedTool()
