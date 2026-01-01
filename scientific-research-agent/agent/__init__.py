"""
Agent entry point for ADK CLI.
Re-exports root_agent from the agents package.
"""
from agents import ideation_agent

# ADK CLI expects 'root_agent' variable
root_agent = ideation_agent
