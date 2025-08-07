# Enhanced Uptime Analysis System

## Overview

The elevator AI agent has been enhanced to provide comprehensive, standardized uptime analysis responses when users ask for elevator uptime information or when there's no specific tool to handle their question but installation and date range are provided.

## Key Features

### 1. Comprehensive Response Format

The system now provides a standardized, detailed analysis format that includes:

**Elevator Information Section:**
- Individual elevator operational time breakdown
- Uptime and downtime hours with percentages
- Data coverage information for each elevator
- Missing date ranges explanation

**Installation-Level Aggregation:**
- Combined metrics from all elevators
- Overall installation uptime percentage
- Total data coverage for the requested period

**Daily Breakdown Calculation:**
- Day-by-day data availability breakdown
- Shows expected vs actual hours for each day
- Provides transparency for incomplete data periods

### 2. Enhanced Query Handling

The system now handles two main scenarios:

#### Direct Uptime Queries
When users ask questions containing keywords like:
- "uptime", "downtime", "availability"
- "working", "broken", "operational"
- "service", "failure", "outage"

#### Fallback Scenarios
When users ask general questions about elevator performance but provide:
- Installation ID
- Date range
- No specific tool can handle the query

### 3. Example Response Format

```
I apologize, but I cannot directly answer your specific question. However, I can provide you with comprehensive uptime analysis for this installation and time period:

**Elevator Information:**
**Elevator 1:**
- Total operational time: 32.4 hours
- Uptime: 32.4 hours (100.0%)
- Downtime: 0.0 hours (0.0%)
- Data coverage: 16.9% of requested period, partial data from July 26 to August 02, 2025

**Elevator 2:**
- Total operational time: 10.6 hours
- Uptime: 10.6 hours (100.0%)
- Downtime: 0.0 hours (0.0%)
- Data coverage: 5.5% of requested period, partial data from July 26 to August 02, 2025

**Installation-Level Aggregation:**
Overall metrics calculated by combining data from all elevators:

- Combined uptime: 43.0 hours
- Combined total time: 43.0 hours
- Installation uptime percentage: 100.0% (calculated from available data)
- Data coverage: 22.4% of requested 192-hour period

**Daily Breakdown Calculation for date range selected:**
📅 Daily Data Availability Breakdown (8 days):
   🏢 Elevator 1:
      • 2025-07-26: No data (0h / 24.0h)
      • 2025-07-27: No data (0h / 24.0h)
      • 2025-07-28: No data (0h / 24.0h)
      • 2025-07-29: No data (0h / 24.0h)
      • 2025-07-30: No data (0h / 24.0h)
      • 2025-07-31: No data (0h / 24.0h)
      • 2025-08-01: 8.4h / 24.0h (35.0%)
      • 2025-08-02: 24.0h / 24.0h (100.0%)

   🏢 Elevator 2:
      • 2025-07-26: No data (0h / 24.0h)
      • 2025-07-27: No data (0h / 24.0h)
      • 2025-07-28: No data (0h / 24.0h)
      • 2025-07-29: No data (0h / 24.0h)
      • 2025-07-30: No data (0h / 24.0h)
      • 2025-07-31: No data (0h / 24.0h)
      • 2025-08-01: No data (0h / 24.0h)
      • 2025-08-02: 10.6h / 24.0h (44.1%)
```

## Implementation Details

### Files Modified

1. **`elevator_ai_agent/agents/orchestrator.py`**
   - Added `format_comprehensive_uptime_analysis()` method
   - Added `_get_missing_dates_summary()` helper method
   - Added `_calculate_daily_breakdown_for_machine()` helper method
   - Enhanced `process_query()` to detect uptime and fallback scenarios
   - Added logic to bypass LLM for comprehensive uptime analysis

### Key Methods

#### `format_comprehensive_uptime_analysis()`
- Generates the standardized comprehensive analysis format
- Processes tool results into human-readable format
- Calculates daily breakdowns for each elevator
- Provides data coverage explanations

#### `_calculate_daily_breakdown_for_machine()`
- Calculates day-by-day data availability for individual elevators
- Shows expected vs actual hours for each day
- Handles timezone conversion and date range calculations

### Query Classification Logic

The system uses the following logic to determine when to provide comprehensive analysis:

```python
# Check if this is an uptime-related query
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
    return comprehensive_analysis
```

## Benefits

1. **Consistent Format**: All uptime-related responses follow the same comprehensive format
2. **Transparency**: Clear indication of data coverage and missing periods
3. **Fallback Capability**: Provides valuable analysis even when the agent can't directly answer the specific question
4. **Data Quality Indicators**: Shows data coverage percentages and missing date ranges
5. **User-Friendly**: Structured, easy-to-read format with clear sections

## Testing

The system has been tested with:

1. **Direct uptime queries**: "What is the uptime for the elevators?"
2. **Fallback scenarios**: "Can you help me understand the elevator performance trends?"
3. **Non-uptime queries**: "How many elevators are in this installation?" (still uses LLM)

All tests pass successfully and provide the expected behavior.

## API Response Structure

When comprehensive uptime analysis is provided, the response includes:
- `analysis_type: "comprehensive_uptime"` indicator
- Standardized `answer` with the comprehensive format
- Complete `tool_results` with detailed metrics
- Installation and timezone information
- Time range details

This enhancement ensures users always receive detailed, useful uptime information regardless of how they phrase their questions, while maintaining the existing functionality for other types of queries.
