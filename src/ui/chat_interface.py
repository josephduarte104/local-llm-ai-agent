"""
ChatGPT-like interface for the Elevator Operations Agent
"""

import streamlit as st
import asyncio
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

class ChatInterface:
    """
    Streamlit-based chat interface similar to ChatGPT
    """
    
    def __init__(self, agent):
        """Initialize with elevator agent"""
        self.agent = agent
    
    async def render(self):
        """Render the chat interface"""
        # Display conversation history
        self._display_messages()
        
        # Chat input
        if prompt := st.chat_input("Ask about elevator uptime, downtime, or performance..."):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message immediately
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing elevator data..."):
                    # Process the message
                    response = await self.agent.process_message(prompt, st.session_state.messages[:-1])
                    
                    # Display response
                    if response.get("content"):
                        st.write(response["content"])
                        
                        # Add visualizations if applicable
                        await self._add_visualizations(response)
                    
                    # Show tool results if debug mode
                    if st.session_state.get("debug_mode", False):
                        self._display_debug_info(response)
            
            # Add assistant response to history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response.get("content", "Sorry, I couldn't process that request.")
            })
    
    def _display_messages(self):
        """Display conversation history"""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    async def _add_visualizations(self, response: Dict[str, Any]):
        """Add relevant visualizations based on response content"""
        tool_results = response.get("tool_results", [])
        
        for result in tool_results:
            if "uptime_minutes" in str(result) and "downtime_minutes" in str(result):
                self._create_uptime_chart(result)
            elif "downtime_intervals" in str(result):
                self._create_downtime_timeline(result)
    
    def _create_uptime_chart(self, result: Dict):
        """Create uptime/downtime visualization"""
        try:
            # Check if this is an uptime/downtime result
            if "totals" in result:
                totals = result["totals"]
                
                # Create pie chart for overall uptime/downtime
                fig = go.Figure(data=[
                    go.Pie(
                        labels=["Uptime", "Downtime"],
                        values=[totals["uptime_minutes"], totals["downtime_minutes"]],
                        hole=0.3,
                        marker_colors=["#00CC88", "#FF6B6B"]
                    )
                ])
                
                fig.update_layout(
                    title="Overall Uptime vs Downtime",
                    annotations=[{
                        "text": f"{totals['uptime_percent']}%<br>Uptime",
                        "x": 0.5, "y": 0.5,
                        "font_size": 16,
                        "showarrow": False
                    }]
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Create bar chart for machines if available
                if "machines" in result and result["machines"]:
                    machines_data = result["machines"]
                    df = pd.DataFrame(machines_data)
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        name='Uptime %',
                        x=df['machineId'],
                        y=df['uptime_percent'],
                        marker_color='#00CC88'
                    ))
                    
                    fig.add_trace(go.Bar(
                        name='Downtime %',
                        x=df['machineId'],
                        y=df['downtime_percent'],
                        marker_color='#FF6B6B'
                    ))
                    
                    fig.update_layout(
                        title="Uptime/Downtime by Machine",
                        xaxis_title="Machine ID",
                        yaxis_title="Percentage",
                        barmode='stack'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Summary table
                    st.subheader("Machine Summary")
                    display_df = df.copy()
                    display_df['uptime_hours'] = display_df['uptime_minutes'] / 60
                    display_df['downtime_hours'] = display_df['downtime_minutes'] / 60
                    
                    st.dataframe(
                        display_df[['machineId', 'uptime_percent', 'downtime_percent', 'uptime_hours', 'downtime_hours']],
                        column_config={
                            'machineId': 'Machine ID',
                            'uptime_percent': st.column_config.NumberColumn('Uptime %', format="%.2f%%"),
                            'downtime_percent': st.column_config.NumberColumn('Downtime %', format="%.2f%%"),
                            'uptime_hours': st.column_config.NumberColumn('Uptime Hours', format="%.1f"),
                            'downtime_hours': st.column_config.NumberColumn('Downtime Hours', format="%.1f")
                        }
                    )
                    
        except Exception as e:
            st.error(f"Error creating visualization: {str(e)}")
    
    def _create_downtime_timeline(self, result: Dict):
        """Create downtime timeline visualization"""
        try:
            if "downtime_intervals" in result:
                intervals = result["downtime_intervals"]
                
                if intervals:
                    # Convert to DataFrame
                    df = pd.DataFrame(intervals)
                    df['start'] = pd.to_datetime(df['start'])
                    df['end'] = pd.to_datetime(df['end'])
                    
                    # Create timeline chart
                    fig = go.Figure()
                    
                    for i, interval in enumerate(intervals):
                        fig.add_trace(go.Scatter(
                            x=[interval['start'], interval['end']],
                            y=[i, i],
                            mode='lines+markers',
                            name=f"{interval['mode']} ({interval['minutes']} min)",
                            line=dict(width=8),
                            hovertemplate=f"<b>{interval['reason']}</b><br>" +
                                        f"Duration: {interval['minutes']} minutes<br>" +
                                        f"Start: {interval['start']}<br>" +
                                        f"End: {interval['end']}<extra></extra>"
                        ))
                    
                    fig.update_layout(
                        title=f"Downtime Timeline - Machine {result.get('machineId', 'Unknown')}",
                        xaxis_title="Time",
                        yaxis_title="Downtime Events",
                        yaxis=dict(showticklabels=False),
                        height=max(300, len(intervals) * 50)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Downtime summary table
                    st.subheader("Downtime Details")
                    display_df = df.copy()
                    display_df['duration'] = display_df['minutes'].apply(lambda x: f"{x:.1f} min")
                    
                    st.dataframe(
                        display_df[['start', 'end', 'mode', 'reason', 'duration']],
                        column_config={
                            'start': st.column_config.DatetimeColumn('Start Time'),
                            'end': st.column_config.DatetimeColumn('End Time'),
                            'mode': 'Mode Code',
                            'reason': 'Description',
                            'duration': 'Duration'
                        }
                    )
                    
        except Exception as e:
            st.error(f"Error creating timeline: {str(e)}")
    
    def _display_debug_info(self, response: Dict[str, Any]):
        """Display debug information"""
        if response.get("tool_results"):
            with st.expander("🔧 Debug: Tool Results"):
                for i, result in enumerate(response["tool_results"]):
                    st.subheader(f"Tool Call {i+1}")
                    st.json(result)

# Quick actions sidebar
def render_quick_actions(agent):
    """Render quick action buttons in sidebar"""
    st.sidebar.markdown("### 🚀 Quick Actions")
    
    if st.sidebar.button("📊 Last Week Uptime"):
        quick_query = "What was the uptime and downtime for all elevators last week?"
        st.session_state.messages.append({"role": "user", "content": quick_query})
        st.rerun()
    
    if st.sidebar.button("⚠️ Current Issues"):
        quick_query = "Show me any elevators currently experiencing downtime or issues"
        st.session_state.messages.append({"role": "user", "content": quick_query})
        st.rerun()
    
    if st.sidebar.button("📈 Performance Trends"):
        quick_query = "Compare elevator performance across installations"
        st.session_state.messages.append({"role": "user", "content": quick_query})
        st.rerun()
    
    if st.sidebar.button("🔍 Detailed Analysis"):
        quick_query = "Provide a detailed analysis of elevator operations for the past month"
        st.session_state.messages.append({"role": "user", "content": quick_query})
        st.rerun()
    
    # Debug toggle
    st.sidebar.markdown("---")
    debug_mode = st.sidebar.checkbox("🐛 Debug Mode", value=False)
    st.session_state.debug_mode = debug_mode
