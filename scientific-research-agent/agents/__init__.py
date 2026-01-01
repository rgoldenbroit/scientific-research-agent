"""
Agents package for the Multi-Agent Scientific Research Assistant.
Contains the coordinator and all specialized sub-agents.
"""

from .coordinator import research_coordinator
from .ideation import ideation_agent
from .analysis import analysis_agent
from .visualization import visualization_agent
from .writer import writer_agent

__all__ = [
    "research_coordinator",
    "ideation_agent",
    "analysis_agent",
    "visualization_agent",
    "writer_agent",
]
