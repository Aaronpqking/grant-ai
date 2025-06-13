#!/usr/bin/env python3
"""
Test script for the web-compatible Grant Agent
"""

import asyncio
from pathlib import Path
import sys

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

async def test_web_agent():
    """Test the web grant agent functionality"""
    
    print("🧪 Testing Web Grant Agent")
    print("=" * 40)
    
    try:
        # Import the web agent
        from web_grant_agent import agent, web_grant_agent, process_grant_documents
        from google.adk.core import Message, Conversation
        
        print("✅ Web agent imported successfully")
        print(f"📝 Agent name: {agent.name}")
        print(f"📋 Agent description: {agent.description}")
        
        # Test basic conversation
        print("\n🔧 Testing basic conversation...")
        
        # Create a test conversation
        conversation = Conversation(messages=[
            Message(role="user", content="Hello, I'd like to create a grant proposal")
        ])
        
        # Process the conversation
        response = await process_grant_documents(conversation)
        
        print(f"✅ Response generated: {len(response.content)} characters")
        print(f"📝 Response preview: {response.content[:200]}...")
        
        # Test with input files if available
        input_dir = Path("input")
        if input_dir.exists() and list(input_dir.glob("*.docx")):
            print(f"\n📂 Testing with files from {input_dir}")
            
            files = [{"name": f.name, "path": str(f)} for f in input_dir.glob("*.docx")[:3]]
            
            # Test file processing
            results = await web_grant_agent.process_grant_request(files)
            
            print(f"📊 Processing status: {results['status']}")
            if results['status'] == 'success':
                print(f"📄 Files processed: {len(results['processed_files'])}")
                print(f"🏆 Quality score: {results['quality_score']:.1f}/100")
            else:
                print(f"❌ Error: {results['message']}")
        
        else:
            print("\n📂 No input files found for testing")
            print("   Create an 'input' directory with .docx files to test file processing")
        
        print("\n🎉 Web agent test completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure Grant_Agent_Refactored directory is properly set up")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        print(f"🔍 Error type: {type(e).__name__}")

async def test_quality_features():
    """Test the enhanced quality features"""
    
    print("\n🏆 Testing Enhanced Quality Features")
    print("=" * 40)
    
    try:
        from Grant_Agent_Refactored.enhanced_grant_builder_v2 import run_comprehensive_test
        
        print("🚀 Running comprehensive quality test...")
        
        # This will test with real documents if available
        # Note: This may take a moment to complete
        await asyncio.get_event_loop().run_in_executor(None, run_comprehensive_test)
        
        print("✅ Quality test completed!")
        
    except ImportError:
        print("❌ Enhanced quality features not available")
        print("💡 Grant_Agent_Refactored components need to be properly installed")
        
    except Exception as e:
        print(f"❌ Quality test error: {e}")

if __name__ == "__main__":
    print("🎯 Grant Agent Web Testing Suite")
    print("=" * 50)
    
    # Run basic web agent test
    asyncio.run(test_web_agent())
    
    # Run quality feature test
    asyncio.run(test_quality_features())
    
    print("\n🏁 All tests completed!")
    print("\n💡 To run in ADK web environment:")
    print("   1. Ensure this directory is in your ADK project")
    print("   2. Start the ADK web server")
    print("   3. The Enhanced Grant Agent will be available")
    print("   4. Upload grant documents to test functionality") 