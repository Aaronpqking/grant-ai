"""
eval_sets package
"""

# Import the standalone agent from adkdocs
from adkdocs.standalone_agent import agent as _imported_agent
from adkdocs.standalone_agent import root_agent as _imported_root_agent

# Make these directly available at the module level
agent = _imported_agent
root_agent = _imported_root_agent

# No __all__ needed - variables are directly in the module namespace 