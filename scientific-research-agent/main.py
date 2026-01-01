"""
Multi-Agent Scientific Research Assistant
Entry point for the ADK application.

TEMPORARY: Testing ideation_agent directly to verify sub-agent works.
"""

from vertexai.agent_engines import AdkApp
from agents import ideation_agent

# TEMPORARY: Test ideation_agent directly (bypassing coordinator)
agent = ideation_agent

# Wrap in AdkApp for Vertex AI Agent Engine deployment
app = AdkApp(agent=agent)
