"""
Multi-Agent Scientific Research Assistant
Entry point for the ADK application.

Uses research_coordinator with sub_agents for LLM-driven delegation.
"""

from vertexai.agent_engines import AdkApp
from agents import research_coordinator

# Use coordinator for multi-agent orchestration
root_agent = research_coordinator

# Wrap in AdkApp for Vertex AI Agent Engine deployment
app = AdkApp(agent=root_agent)
