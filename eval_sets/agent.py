"""
Agent module for the eval_sets package.

This directly creates agent and root_agent variables at the module level.
"""

# Import the standalone agent
from adkdocs.standalone_agent import agent as _imported_agent
from adkdocs.standalone_agent import root_agent as _imported_root_agent

# Expose the variables directly at the module level
agent = _imported_agent
root_agent = _imported_root_agent 