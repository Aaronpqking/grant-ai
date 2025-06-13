#!/usr/bin/env python3
"""
Test script to verify Vertex AI configuration is working with ADK
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

def test_vertex_config():
    """Test if environment is properly configured for Vertex AI"""
    
    print("🧪 Testing Vertex AI Configuration...")
    print("=" * 50)
    
    # Check required environment variables
    project = os.environ.get('GOOGLE_CLOUD_PROJECT')
    location = os.environ.get('GOOGLE_CLOUD_LOCATION')
    api_key = os.environ.get('GOOGLE_API_KEY')
    
    print(f"GOOGLE_CLOUD_PROJECT: {project}")
    print(f"GOOGLE_CLOUD_LOCATION: {location}")
    print(f"GOOGLE_API_KEY: {'Set' if api_key else 'Not set'}")
    
    if not project or not location:
        print("❌ Missing required Vertex AI configuration!")
        return False
    
    # Test if we can import ADK
    try:
        from google.adk import Agent
        from google.adk.tools import FunctionTool
        print("✅ ADK imports successful")
    except ImportError as e:
        print(f"❌ ADK import failed: {e}")
        return False
    
    # Test if we can create an agent
    try:
        def dummy_tool():
            return "test"
        
        agent = Agent(
            model="gemini-1.5-flash",
            name="test_agent",
            instruction="Test agent",
            description="Testing Vertex AI backend",
            tools=[FunctionTool(func=dummy_tool)]
        )
        print("✅ Agent creation successful")
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False
    
    # Test Google LLM backend detection
    try:
        from google.adk.models.google_llm import GoogleLLM
        llm = GoogleLLM(model="gemini-1.5-flash")
        
        # Check which backend it would use
        backend = "vertex" if project and location else "ml_dev"
        print(f"✅ Expected backend: {backend}")
        
        if backend == "vertex":
            print("🎯 Configuration should use Vertex AI backend!")
        else:
            print("⚠️  Configuration will use API key backend")
            
    except Exception as e:
        print(f"❌ LLM backend test failed: {e}")
        return False
    
    return True

def test_agent_import():
    """Test if our agent imports correctly"""
    
    print("\n🧪 Testing Agent Import...")
    print("=" * 50)
    
    try:
        from agent import agent
        print(f"✅ Agent imported: {agent.name}")
        print(f"✅ Tools available: {len(agent.tools)}")
        return True
    except Exception as e:
        print(f"❌ Agent import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load environment from clean config
    if os.path.exists('.env.clean'):
        print("Loading clean .env configuration...")
        with open('.env.clean', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    success1 = test_vertex_config()
    success2 = test_agent_import()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Ready to test with ADK web.")
    else:
        print("\n❌ Some tests failed. Check configuration.") 