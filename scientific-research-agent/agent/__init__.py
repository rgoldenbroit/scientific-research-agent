"""
Agent entry point for ADK CLI.
Re-exports root_agent from the agents package.

To test different agents, change the import below:
- ideation_agent: Hypothesis generation
- analysis_agent: Statistical analysis
- research_coordinator: Full orchestration with sub-agents
"""
from agents import ideation_agent, analysis_agent, research_coordinator

# ADK CLI expects 'root_agent' variable
# Change this to test different agents:
root_agent = research_coordinator  # Testing multi-agent coordination
# root_agent = ideation_agent
# root_agent = analysis_agent
