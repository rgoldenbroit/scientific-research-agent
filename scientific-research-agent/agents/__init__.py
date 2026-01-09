"""
Agents package for the Multi-Agent Scientific Research Assistant.
Contains the coordinator and all specialized sub-agents.
"""

from .coordinator import research_coordinator
from .ideation import ideation_agent
from .analysis import analysis_agent
from .visualization import visualization_agent
from .writer import writer_agent
from .guidance import guidance_agent
from .email import email_agent

__all__ = [
    "research_coordinator",
    "ideation_agent",
    "analysis_agent",
    "visualization_agent",
    "writer_agent",
    "guidance_agent",
    "email_agent",
]
