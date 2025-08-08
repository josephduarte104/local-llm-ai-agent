# 📊 Data Coverage Questions - Examples & Capabilities

## ✅ **NEW: Questions the Agent Can Now Answer**

The agent has been enhanced with a dedicated data coverage analysis tool. It can now directly answer detailed questions about data quality, availability, and coverage.

### **📈 Data Coverage & Quality Questions**

#### **Overall Coverage Questions**
- "What's the data coverage for this installation?"
- "How much data do we have for last week?"
- "What's the data quality like?"
- "How reliable is this data?"
- "What percentage of expected data do we have?"

#### **Machine-Specific Coverage Questions**
- "Which elevators are reporting data?"
- "What's the data coverage for elevator 2?"
- "Which machines have missing data?"
- "Are all elevators sending data?"
- "Which elevators are silent?"

#### **Data Gaps & Issues Questions**
- "Are there any data gaps?"
- "What periods have missing data?"
- "Where is data incomplete?"
- "What data issues should I know about?"
- "Why is the coverage low?"

#### **Event Count & Span Questions**
- "How many events were recorded?"
- "What's the event count for each elevator?"
- "How much data span do we have?"
- "When was the first/last event recorded?"

#### **Data Type Availability Questions**
- "What types of data are available?"
- "Do we have door operation data?"
- "Is CarModeChanged data available?"
- "What events are being collected?"

#### **Data Collection & Monitoring Questions**
- "How can we improve data collection?"
- "What sensors aren't working?"
- "Are there connectivity issues?"
- "Which elevators need attention?"
- "What's the monitoring status?"

---

## 🔧 **Technical Implementation Details**

### **New Data Coverage Tool**
```python
# File: elevator_ai_agent/tools/data_coverage_tool.py
class DataCoverageTool(BaseTool):
    def run(self, installation_id, tz, start, end, **kwargs):
        # Returns comprehensive coverage analysis including:
        # - Overall coverage percentages
        # - Machine-specific status and metrics
        # - Data quality assessment
        # - Gap analysis and recommendations
```

### **Enhanced Tool Selection**
The orchestrator now automatically detects data coverage questions using keywords:
```python
data_coverage_keywords = [
    'coverage', 'data quality', 'data availability', 'missing data', 'data gaps',
    'incomplete data', 'data completeness', 'reporting', 'silent', 'no data',
    'data span', 'event count', 'how much data', 'data reliability',
    'data issues', 'connectivity', 'sensors', 'collection', 'monitoring'
]
```

### **Rich Response Data**
The tool provides structured analysis including:

#### **Analysis Summary**
- Overall status (excellent/good/fair/poor)
- Coverage percentage with visual indicators
- Elevator counts (total/reporting/silent)
- Available data types
- Time span metrics

#### **Machine Summaries**
For each elevator:
- Reporting status
- Coverage percentage and quality rating
- Event counts and data span
- First/last event timestamps

#### **Quality Assessment**
- Data quality rating
- Identified issues and strengths
- Issue count and severity

#### **Actionable Recommendations**
- Specific improvement suggestions
- Machine-specific actions needed
- Data collection optimization tips

---

## 📋 **Example Responses**

### **Question: "What's the data coverage for this installation?"**

**Expected Response:**
```markdown
### Data Coverage Analysis for Installation 1234

**Overall Status:** 🟡 Good (87.3% coverage)

The installation has **good data coverage** for the requested period from January 1-7, 2025.

**Summary:**
- **Total Elevators:** 4
- **Reporting Elevators:** 3 (75%)
- **Silent Elevators:** 1 (Elevator 4)
- **Data Types Available:** CarModeChanged, Door events
- **Expected Hours:** 168.0 hours per elevator
- **Available Hours:** 146.6 hours per elevator

**Elevator Details:**
- **Elevator 1:** 95.2% coverage (159.9 hours) - Excellent
- **Elevator 2:** 89.1% coverage (149.7 hours) - Good  
- **Elevator 3:** 77.6% coverage (130.4 hours) - Fair
- **Elevator 4:** 0% coverage (0 hours) - No data

**Recommendations:**
- Check connectivity/sensors for silent Elevator 4
- Investigate data quality issues for Elevator 3 (low coverage)

---
**Data Coverage Summary:**
🟡 **87.3%** overall data coverage | 📊 **3/4** elevators with data | 📈 **CarModeChanged, Door** events available
```

### **Question: "Which elevators have missing data?"**

**Expected Response:**
```markdown
### Missing Data Analysis

Based on the coverage analysis, the following elevators have data issues:

**Silent Elevators (No Data):**
- **Elevator 4:** Completely silent - no events recorded
  - Status: No data for entire period
  - Action needed: Check connectivity and sensor status

**Low Coverage Elevators:**
- **Elevator 3:** 77.6% coverage 
  - Missing approximately 37.6 hours of expected data
  - Data gaps may indicate intermittent connectivity issues

**Recommendations:**
1. Priority: Investigate Elevator 4 - complete communication failure
2. Check Elevator 3 sensors and data collection systems
3. Consider maintenance window to address connectivity issues

All other elevators (1 and 2) are reporting well with >89% coverage.

---
**Data Coverage Summary:**
🟡 **87.3%** overall data coverage | 📊 **3/4** elevators with data | ⚠️ 1 of 4 elevators have no data for this period
```

---

## 🧪 **Testing the New Capabilities**

### **Test Questions to Try:**
1. "What's the data coverage percentage?"
2. "Are there any silent elevators?"
3. "How much data is missing?"
4. "What's the data quality like?"
5. "Which machines aren't reporting?"
6. "How many events were recorded yesterday?"
7. "Are there any data gaps I should know about?"
8. "What can we do to improve data collection?"

### **Expected Tool Selection:**
All these questions should now automatically route to the `data_coverage_analysis` tool instead of defaulting to uptime analysis.

---

## 🔄 **Integration with Existing Features**

- **Automatic Coverage Summary:** Still included in all responses
- **Uptime Analysis:** Now includes more detailed coverage context
- **Door Analysis:** Benefits from enhanced coverage information
- **Error Handling:** Graceful fallback if coverage analysis fails

The agent now provides a complete picture of both **operational performance** AND **data quality** for comprehensive elevator system analysis! 🎯
