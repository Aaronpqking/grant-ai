"""
Agent module for the adkdocs package.

This directly imports and re-exports the Grant_Agent agent for the ADK web server.
"""

# Use a relative import path to avoid module not found errors
import sys
import os
# Add parent directory to Python path 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the agent
from Grant_Agent.agent import agent, root_agent

# ADK looks for agent or root_agent
__all__ = ["agent", "root_agent"] 