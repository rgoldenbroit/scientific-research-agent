"""
Multi-Agent Scientific Research Assistant
Entry point for the ADK application.

This application uses a coordinator agent that orchestrates specialized sub-agents:
- Ideation Agent: Generates research hypotheses from literature and data
- Analysis Agent: Performs statistical analysis and hypothesis testing
- Visualization Agent: Creates publication-quality charts
- Writer Agent: Drafts research documents in Google Docs
"""

from vertexai.agent_engines import AdkApp
from agents import research_coordinator

# Export the coordinator as the root agent
agent = research_coordinator

# Wrap in AdkApp for Vertex AI Agent Engine deployment
app = AdkApp(agent=agent)
