"""
Test script for refactored architecture without ADK dependencies
"""

def test_models():
    """Test that models import and work correctly"""
    print("Testing models...")
    from .models import (
        GrantWorkflowData, DocumentData, DocumentType, 
        OrganizationInfo, FunderInfo, WorkflowStatus
    )
    
    # Test basic model creation
    workflow = GrantWorkflowData()
    print(f"✅ GrantWorkflowData created with status: {workflow.status.value}")
    
    # Test document creation
    doc = DocumentData.create("test content", "test.txt", "text/plain")
    print(f"✅ DocumentData created with hash: {doc.content_hash}")
    
    # Test organization and funder
    org = OrganizationInfo()
    funder = FunderInfo()
    print(f"✅ OrganizationInfo complete: {org.is_complete()}")
    print(f"✅ FunderInfo complete: {funder.is_complete()}")

def test_services():
    """Test service layer"""
    print("\nTesting services...")
    from .services import DocumentClassifier, ExtractionService
    
    classifier = DocumentClassifier()
    print("✅ DocumentClassifier created")
    
    # Test classification
    org_content = "Organization Name: Test Org\nMission Statement: Test mission"
    doc_type = classifier.classify_document(org_content)
    print(f"✅ Document classified as: {doc_type.value}")
    
    extraction_service = ExtractionService()
    print("✅ ExtractionService created")

def test_workflow_engine():
    """Test workflow engine"""
    print("\nTesting workflow engine...")
    from .workflow_engine import WorkflowEngine, WorkflowStage
    
    engine = WorkflowEngine()
    print(f"✅ WorkflowEngine created with {len(engine.stages)} stages")

if __name__ == "__main__":
    print("🧪 Testing Refactored Grant Agent Architecture (without ADK)")
    print("=" * 60)
    
    try:
        test_models()
        test_services() 
        test_workflow_engine()
        print("\n🎉 All core components working correctly!")
        print("📝 Note: ADK integration requires google-adk package")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc() 