"""
Refactored Grant Agent - Main Entry Point
Replaces the existing agent.py with clean architecture
"""

import logging
from .adk_integration import create_grant_agent

# Configure logging for the refactored system
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create the agent instance
logger.info("Initializing Refactored Grant Agent v2.0")
agent = create_grant_agent()
logger.info("Refactored Grant Agent ready")

# Export the agent for ADK framework
__all__ = ['agent'] 