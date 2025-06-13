"""
adkdocs - Grant Agent Application

This package exports the grant agent for the ADK web server.
"""

# Import the standalone agent - much simpler and avoids circular imports
from adkdocs.standalone_agent import agent, root_agent

# Make these available at the module level
__all__ = ["agent", "root_agent"] 