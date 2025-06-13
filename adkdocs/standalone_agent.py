"""
Standalone agent implementation that doesn't rely on Grant_Agent imports.

This implementation creates a simple LlmAgent directly.
"""

import os
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import ADK components
from google.adk.agents import LlmAgent
from google.adk.models import Gemini

# Create a simple agent
agent = LlmAgent(
    name="SimpleGrantAgent",
    model="gemini-1.5-flash",
    instruction="""You are a grant writing assistant. You help users write grant proposals.

You can help with:
1. Analyzing organization and funder information
2. Creating logic models and evaluation plans
3. Matching organization language with funder priorities
4. Drafting grant narratives

Ask the user what kind of grant they need help with and what documents they have available.
""",
    description="Grant writing assistant"
)

# For backwards compatibility
root_agent = agent

# Log that the agent was created
logger.info(f"Created standalone agent: {agent.name}") 