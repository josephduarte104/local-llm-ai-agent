"""Basic tool stubs for other elevator event types."""

from datetime import datetime
from typing import Dict, Any
from .base import BaseTool
from ..services.cosmos import get_cosmos_service
from ..services.timezone import timezone_service


class BasicEventTool(BaseTool):
    """Base tool for basic event analysis."""
    
    def __init__(self, data_type: str, description: str):
        super().__init__(
            name=data_type.lower(),
            description=description
        )
        self.data_type = data_type
    
    def run(
        self, 
        installation_id: str, 
        tz: str, 
        start: datetime, 
        end: datetime, 
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Basic event counting and summary."""
        start_epoch = timezone_service.local_datetime_to_epoch(start)
        end_epoch = timezone_service.local_datetime_to_epoch(end)
        
        cosmos_service = get_cosmos_service()
        events = list(cosmos_service.query_events(
            installation_id=installation_id,
            data_type=self.data_type,
            start_ts=start_epoch,
            end_ts=end_epoch
        ))
        
        return {
            'data_type': self.data_type,
            'installation_id': installation_id,
            'time_range': {
                'start': start.isoformat(),
                'end': end.isoformat(),
                'timezone': tz
            },
            'event_count': len(events),
            'events': events[:100]  # Limit to first 100 events
        }


# Create tool instances for each data type
door_tool = BasicEventTool("Door", "Analyze door operation events")
passenger_report_tool = BasicEventTool("PassengerReport", "Analyze passenger activity")
hall_call_accepted_tool = BasicEventTool("HallCallAccepted", "Analyze hall call acceptance")
car_call_accepted_tool = BasicEventTool("CarCallAccepted", "Analyze car call acceptance")
