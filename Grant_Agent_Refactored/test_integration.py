#!/usr/bin/env python3
"""
Integration Test for Grant Agent Refactored
Tests the complete workflow end-to-end
"""

import sys
import os
from pathlib import Path

# Add the refactored package to path
sys.path.insert(0, str(Path(__file__).parent))

def test_basic_components():
    """Test that all basic components can be imported and work"""
    print("🧪 Testing Basic Components")
    print("-" * 30)
    
    try:
        from refactored.models import (
            GrantWorkflowData, DocumentData, DocumentType, 
            OrganizationInfo, FunderInfo, WorkflowStatus
        )
        
        # Test workflow data
        workflow = GrantWorkflowData()
        assert workflow.status == WorkflowStatus.INITIALIZED
        print("✅ GrantWorkflowData: Working")
        
        # Test document creation
        doc = DocumentData.create("test content", "test.txt", "text/plain")
        assert doc.content == "test content"
        assert len(doc.content_hash) == 8
        print("✅ DocumentData: Working")
        
        # Test adding document to workflow
        workflow.add_document(doc)
        assert doc.content_hash in workflow.documents
        assert workflow.status == WorkflowStatus.DOCUMENTS_UPLOADED
        print("✅ Document Addition: Working")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic Components Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_processing():
    """Test document processing and classification"""
    print("\n🧪 Testing Document Processing")
    print("-" * 30)
    
    try:
        from refactored.services import DocumentService, DocumentClassifier
        
        # Test classifier
        classifier = DocumentClassifier()
        
        org_text = """
        Organization Name: Freedom Equity Inc
        Mission Statement: Provide affordable housing solutions
        Annual Budget: $500,000
        Executive Director: John Smith
        """
        
        funder_text = """
        KeyBank Foundation Bicentennial Grant Program
        Request Limit: $25,000
        Funding Priorities: Housing development, Small business support
        Eligibility Criteria: Non-profit organizations
        """
        
        org_type = classifier.classify_document(org_text)
        funder_type = classifier.classify_document(funder_text)
        
        print(f"✅ Organization Classification: {org_type.value}")
        print(f"✅ Funder Classification: {funder_type.value}")
        
        # Test document service
        doc_service = DocumentService()
        org_doc = doc_service.process_upload(
            org_text.encode(), "org_info.txt", "text/plain"
        )
        funder_doc = doc_service.process_upload(
            funder_text.encode(), "funder_info.txt", "text/plain"
        )
        
        print(f"✅ Processed Org Doc: {org_doc.document_type.value}")
        print(f"✅ Processed Funder Doc: {funder_doc.document_type.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document Processing Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_extraction():
    """Test data extraction from documents"""
    print("\n🧪 Testing Data Extraction")
    print("-" * 30)
    
    try:
        from refactored.services import ExtractionService
        from refactored.models import GrantWorkflowData, DocumentData, DocumentType
        
        # Create sample documents
        org_content = """
        Organization Name: Freedom Equity Inc
        Mission Statement: Provide affordable housing and business development services to underserved communities
        Background Summary: Freedom Equity Inc has been serving the Cleveland community for over 10 years, focusing on creating pathways to homeownership and small business development.
        Annual Budget: $750,000
        City: Cleveland, Ohio
        First Name: John
        Email: john@freedomequity.org
        Phone: 216-555-0123
        """
        
        funder_content = """
        KeyBank Foundation Bicentennial Grant Program
        Request Limit: $25,000
        Funding Priorities:
        • Affordable housing development
        • Small business and entrepreneurship support
        • Economic development initiatives
        • Financial inclusion programs
        
        Eligibility Criteria:
        • 501(c)(3) non-profit organizations
        • Located in KeyBank footprint
        • Demonstrated community impact
        """
        
        # Create workflow with documents
        workflow = GrantWorkflowData()
        
        org_doc = DocumentData.create(org_content, "org.txt", "text/plain")
        org_doc.document_type = DocumentType.ORGANIZATION
        workflow.add_document(org_doc)
        
        funder_doc = DocumentData.create(funder_content, "funder.txt", "text/plain")
        funder_doc.document_type = DocumentType.FUNDER
        workflow.add_document(funder_doc)
        
        # Test extraction
        extraction_service = ExtractionService()
        result = extraction_service.extract_all(workflow)
        
        if result.success:
            print("✅ Extraction Successful")
            if result.organization:
                print(f"   Organization: {result.organization.name}")
                print(f"   Mission: {result.organization.mission[:50]}...")
                print(f"   Budget: ${result.organization.financials.annual_budget:,.0f}")
                print(f"   Contact: {result.organization.contact_info.email}")
            
            if result.funder:
                print(f"   Funder: {result.funder.name}")
                print(f"   Amount: ${result.funder.grant_amount:,}")
                print(f"   Priorities: {len(result.funder.funding_priorities)} items")
                print(f"   Criteria: {len(result.funder.eligibility_criteria)} items")
        else:
            print(f"❌ Extraction Failed: {'; '.join(result.errors)}")
            
        return result.success
        
    except Exception as e:
        print(f"❌ Extraction Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_engine():
    """Test the workflow engine"""
    print("\n🧪 Testing Workflow Engine")
    print("-" * 30)
    
    try:
        from refactored.workflow_engine import WorkflowEngine
        from refactored.models import GrantWorkflowData
        
        # Create engine and register stages
        engine = WorkflowEngine()
        
        # The stages should auto-register when ADK integration is available
        # For now, just test basic engine functionality
        workflow = GrantWorkflowData()
        
        print(f"✅ WorkflowEngine Created: {len(engine.stages)} stages")
        print(f"✅ Workflow Ready: {workflow.status.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow Engine Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_language_analysis():
    """Test language analysis service"""
    print("\n🧪 Testing Language Analysis")
    print("-" * 30)
    
    try:
        from refactored.services import LanguageAnalysisService
        from refactored.models import OrganizationInfo, FunderInfo
        
        # Create test data
        org_info = OrganizationInfo(
            name="Freedom Equity Inc",
            mission="Provide affordable housing and small business development",
            background="Focus on community development and economic empowerment"
        )
        
        funder_info = FunderInfo(
            name="KeyBank Foundation",
            grant_amount=25000,
            funding_priorities=[
                "Affordable housing development",
                "Small business support",
                "Economic development"
            ]
        )
        
        # Test analysis
        analysis_service = LanguageAnalysisService()
        analysis = analysis_service.analyze_alignment(org_info, funder_info)
        
        print(f"✅ Language Analysis Complete")
        print(f"   Alignment Score: {analysis.alignment_score:.2f}")
        print(f"   Matching Themes: {len(analysis.matching_themes)} found")
        print(f"   Recommendations: {len(analysis.recommendations)} generated")
        
        for theme in analysis.matching_themes:
            print(f"   📝 Theme: {theme}")
        
        return True
        
    except Exception as e:
        print(f"❌ Language Analysis Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Grant Agent Refactored - Integration Tests")
    print("=" * 50)
    
    tests = [
        test_basic_components,
        test_document_processing,
        test_extraction,
        test_workflow_engine,
        test_language_analysis
    ]
    
    results = []
    for test in tests:
        try:
            success = test()
            results.append(success)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n📊 Test Results Summary")
    print("-" * 25)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test.__name__}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✅ Grant Agent Refactored is working correctly")
        return True
    else:
        print("⚠️ Some tests failed - check the logs above")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1) 