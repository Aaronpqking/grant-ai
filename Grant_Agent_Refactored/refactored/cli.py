"""
CLI interface for Grant Agent Refactored
Allows testing and demonstration of the refactored architecture
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

def test_architecture():
    """Test the refactored architecture components"""
    print("🧪 Testing Grant Agent Refactored Architecture")
    print("=" * 50)
    
    try:
        # Test core components
        from .test_imports import test_models, test_services, test_workflow_engine
        
        test_models()
        test_services()
        test_workflow_engine()
        
        print("\n✅ All core components working correctly!")
        
        # Test ADK integration if available
        try:
            from . import create_grant_agent
            print("\n🔌 Testing ADK Integration...")
            agent = create_grant_agent()
            print(f"✅ ADK Agent created: {agent.name}")
            print(f"✅ Workflow stages: {len(agent.workflow_engine.stages)}")
            print("✅ ADK integration fully functional!")
            
        except ImportError as e:
            print(f"\n📝 ADK Integration: {e}")
            print("   Install google-adk package for full functionality")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def extract_from_document(file_path: str):
    """Test document extraction capabilities"""
    print(f"📄 Testing document extraction: {file_path}")
    
    try:
        from .services import DocumentService, ExtractionService
        from .models import GrantWorkflowData
        
        # Read file
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return False
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Process document
        doc_service = DocumentService()
        doc_data = doc_service.process_upload(
            file_data, 
            file_path.name, 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        print(f"✅ Document processed: {doc_data.document_type.value}")
        print(f"   Content length: {len(doc_data.content)} characters")
        print(f"   Hash: {doc_data.content_hash}")
        
        # Test extraction
        workflow = GrantWorkflowData()
        workflow.add_document(doc_data)
        
        extraction_service = ExtractionService()
        result = extraction_service.extract_all(workflow)
        
        if result.success:
            print(f"✅ Extraction successful from: {', '.join(result.extracted_from)}")
            if result.organization:
                print(f"   Organization: {result.organization.name}")
                print(f"   Mission: {result.organization.mission[:100]}...")
            if result.funder:
                print(f"   Funder: {result.funder.name}")
                print(f"   Amount: ${result.funder.grant_amount:,}")
        else:
            print(f"❌ Extraction failed: {'; '.join(result.errors)}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Error processing document: {e}")
        import traceback
        traceback.print_exc()
        return False


def status_check():
    """Check the current status and capabilities"""
    print("📊 Grant Agent Refactored - Status Check")
    print("=" * 40)
    
    # Check core components
    components = {
        "models": False,
        "services": False, 
        "workflow_engine": False,
        "adk_integration": False
    }
    
    try:
        from . import models
        components["models"] = True
        print("✅ Models: Available")
    except ImportError:
        print("❌ Models: Import failed")
    
    try:
        from . import services
        components["services"] = True
        print("✅ Services: Available")
    except ImportError:
        print("❌ Services: Import failed")
    
    try:
        from . import workflow_engine
        components["workflow_engine"] = True
        print("✅ Workflow Engine: Available")
    except ImportError:
        print("❌ Workflow Engine: Import failed")
    
    try:
        from . import create_grant_agent
        components["adk_integration"] = True
        print("✅ ADK Integration: Available")
    except ImportError:
        print("📝 ADK Integration: Requires google-adk package")
    
    # Summary
    available = sum(components.values())
    total = len(components)
    print(f"\n📈 Component Status: {available}/{total} available")
    
    if available == total:
        print("🎉 All components fully functional!")
    elif available >= 3:
        print("✅ Core functionality available")
    else:
        print("⚠️  Limited functionality - check dependencies")
    
    return components


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Grant Agent Refactored CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  grant-agent test                    # Test all components
  grant-agent status                  # Check component status
  grant-agent extract document.docx  # Test document extraction
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test architecture components')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check component status')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Test document extraction')
    extract_parser.add_argument('file_path', help='Path to document file')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute commands
    if args.command == 'test':
        success = test_architecture()
        sys.exit(0 if success else 1)
        
    elif args.command == 'status':
        components = status_check()
        # Exit with error code if critical components missing
        critical_missing = not (components["models"] and components["services"])
        sys.exit(1 if critical_missing else 0)
        
    elif args.command == 'extract':
        success = extract_from_document(args.file_path)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 