"""Base tool interface for elevator operations analysis."""

from typing import Protocol, Any
from datetime import datetime


class Tool(Protocol):
    """Protocol defining the interface for all analysis tools."""
    
    name: str
    description: str
    
    def run(
        self, 
        installation_id: str, 
        tz: str, 
        start: datetime, 
        end: datetime, 
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        Run the tool analysis.
        
        Args:
            installation_id: The installation to analyze
            tz: IANA timezone string for the installation
            start: Start datetime (timezone-aware)
            end: End datetime (timezone-aware)
            **kwargs: Additional tool-specific parameters
            
        Returns:
            Structured data dictionary with analysis results
        """
        ...


class BaseTool:
    """Base implementation for analysis tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def run(
        self, 
        installation_id: str, 
        tz: str, 
        start: datetime, 
        end: datetime, 
        **kwargs: Any
    ) -> dict[str, Any]:
        """Default implementation raises NotImplementedError."""
        raise NotImplementedError(f"Tool {self.name} must implement run method")
