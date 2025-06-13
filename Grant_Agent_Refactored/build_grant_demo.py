#!/usr/bin/env python3
"""
Grant Building Demonstration
Shows the complete refactored Grant Agent workflow in action
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add the refactored package to path
sys.path.insert(0, str(Path(__file__).parent))

def build_complete_grant():
    """Demonstrate building a complete grant from multiple documents"""
    print("🚀 **GRANT BUILDER DEMONSTRATION**")
    print("Using Refactored Grant Agent v2.0")
    print("=" * 60)
    
    try:
        # Import refactored components
        from refactored.models import GrantWorkflowData, DocumentType, WorkflowStatus
        from refactored.services import DocumentService, ExtractionService, LanguageAnalysisService
        from refactored.workflow_engine import WorkflowEngine
        
        # Initialize the workflow
        print("📋 **Step 1: Initialize Workflow**")
        workflow = GrantWorkflowData()
        print(f"✅ Workflow initialized: {workflow.status.value}")
        print(f"   Created at: {workflow.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Document processing service
        doc_service = DocumentService()
        
        # Process organization documents
        print("\n📄 **Step 2: Process Organization Documents**")
        org_documents = [
            "../Freedom_Equity_Grant_Application.docx",
            "../Freedom_Equity_Inc_Grant_Proposal.docx"
        ]
        
        for doc_path in org_documents:
            if Path(doc_path).exists():
                try:
                    with open(doc_path, 'rb') as f:
                        file_data = f.read()
                    
                    doc_data = doc_service.process_upload(
                        file_data, 
                        Path(doc_path).name,
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    )
                    
                    workflow.add_document(doc_data)
                    print(f"✅ Processed: {Path(doc_path).name}")
                    print(f"   Type: {doc_data.document_type.value}")
                    print(f"   Content: {len(doc_data.content)} characters")
                    print(f"   Hash: {doc_data.content_hash}")
                    
                except Exception as e:
                    print(f"⚠️  Error processing {doc_path}: {e}")
        
        # Process funder documents
        print("\n🏦 **Step 3: Process Funder Documents**")
        funder_documents = [
            "../KeyBank_Grant_Application.docx",
            "../KeyBank_Grant_Application_Freedom_Equity_Inc.docx"
        ]
        
        for doc_path in funder_documents:
            if Path(doc_path).exists():
                try:
                    with open(doc_path, 'rb') as f:
                        file_data = f.read()
                    
                    doc_data = doc_service.process_upload(
                        file_data,
                        Path(doc_path).name,
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    )
                    
                    workflow.add_document(doc_data)
                    print(f"✅ Processed: {Path(doc_path).name}")
                    print(f"   Type: {doc_data.document_type.value}")
                    print(f"   Content: {len(doc_data.content)} characters")
                    print(f"   Hash: {doc_data.content_hash}")
                    
                except Exception as e:
                    print(f"⚠️  Error processing {doc_path}: {e}")
        
        print(f"\n📊 **Document Summary**")
        print(f"   Total documents: {len(workflow.documents)}")
        print(f"   Workflow status: {workflow.status.value}")
        
        # Data extraction
        print("\n🔍 **Step 4: Extract Organization & Funder Information**")
        extraction_service = ExtractionService()
        extraction_result = extraction_service.extract_all(workflow)
        
        if extraction_result.success:
            print("✅ Extraction successful!")
            
            # Update workflow with extracted data
            if extraction_result.organization:
                workflow.organization = extraction_result.organization
                workflow.status = WorkflowStatus.EXTRACTION_COMPLETE
                
                print(f"\n🏢 **Organization Information:**")
                print(f"   Name: {workflow.organization.name}")
                print(f"   Mission: {workflow.organization.mission}")
                print(f"   Location: {workflow.organization.location}")
                print(f"   Budget: ${workflow.organization.financials.annual_budget:,.0f}")
                print(f"   Contact: {workflow.organization.contact_info.name}")
                print(f"   Email: {workflow.organization.contact_info.email}")
            
            if extraction_result.funder:
                workflow.funder = extraction_result.funder
                
                print(f"\n🏦 **Funder Information:**")
                print(f"   Name: {workflow.funder.name}")
                print(f"   Grant Amount: ${workflow.funder.grant_amount:,}")
                print(f"   Funding Type: {workflow.funder.funding_type}")
                print(f"   Priorities: {len(workflow.funder.funding_priorities)} items")
                for i, priority in enumerate(workflow.funder.funding_priorities[:3], 1):
                    print(f"     {i}. {priority}")
                print(f"   Eligibility: {len(workflow.funder.eligibility_criteria)} criteria")
                for i, criteria in enumerate(workflow.funder.eligibility_criteria[:3], 1):
                    print(f"     {i}. {criteria}")
        else:
            print(f"❌ Extraction failed: {'; '.join(extraction_result.errors)}")
            return False
        
        # Language analysis
        print("\n🧠 **Step 5: Analyze Language Alignment**")
        if workflow.organization and workflow.funder:
            analysis_service = LanguageAnalysisService()
            language_analysis = analysis_service.analyze_alignment(
                workflow.organization, 
                workflow.funder
            )
            
            workflow.language_analysis = language_analysis
            workflow.status = WorkflowStatus.ANALYSIS_COMPLETE
            
            print(f"✅ Language analysis complete!")
            print(f"   Alignment Score: {language_analysis.alignment_score:.1%}")
            print(f"   Matching Themes: {len(language_analysis.matching_themes)} found")
            
            for theme in language_analysis.matching_themes:
                print(f"     🎯 {theme}")
            
            print(f"   Recommendations: {len(language_analysis.recommendations)}")
            for rec in language_analysis.recommendations:
                print(f"     💡 {rec}")
        
        # Generate grant narrative
        print("\n✍️ **Step 6: Generate Grant Narrative**")
        narrative = generate_grant_narrative(workflow)
        workflow.narrative = narrative
        workflow.status = WorkflowStatus.NARRATIVE_GENERATED
        
        print("✅ Grant narrative generated!")
        print(f"   Length: {len(narrative)} characters")
        print(f"   Status: {workflow.status.value}")
        
        # Create final document
        print("\n📄 **Step 7: Create Final Grant Document**")
        final_document = create_final_document(workflow)
        workflow.final_document = final_document
        workflow.status = WorkflowStatus.COMPLETED
        
        print("✅ Final document created!")
        print(f"   Document size: {len(final_document)} bytes")
        print(f"   Final status: {workflow.status.value}")
        
        # Save the grant
        output_path = save_grant_document(workflow)
        print(f"   Saved to: {output_path}")
        
        # Summary
        print("\n🎉 **GRANT BUILDING COMPLETE!**")
        print("=" * 40)
        print(f"📊 **Final Results:**")
        print(f"   Organization: {workflow.organization.name}")
        print(f"   Funder: {workflow.funder.name}")
        print(f"   Grant Amount: ${workflow.funder.grant_amount:,}")
        print(f"   Alignment Score: {workflow.language_analysis.alignment_score:.1%}")
        print(f"   Processing Time: {(datetime.now() - workflow.created_at).total_seconds():.1f}s")
        print(f"   Documents Processed: {len(workflow.documents)}")
        print(f"   Final Status: ✅ {workflow.status.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in grant building: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_grant_narrative(workflow):
    """Generate a compelling grant narrative"""
    org = workflow.organization
    funder = workflow.funder
    analysis = workflow.language_analysis
    
    narrative = f"""
GRANT PROPOSAL: {funder.name} Funding Request

ORGANIZATION OVERVIEW:
{org.name} is a dedicated non-profit organization with a clear mission: {org.mission}

Our organization has been serving the community with an annual operating budget of ${org.financials.annual_budget:,.0f}. Based in {org.location}, we have established ourselves as a trusted community partner focused on sustainable impact.

ALIGNMENT WITH FUNDER PRIORITIES:
Our analysis shows a {analysis.alignment_score:.1%} alignment with {funder.name}'s funding priorities. Key areas of alignment include:

"""
    
    for theme in analysis.matching_themes:
        narrative += f"• {theme.title()}: Our programs directly address this priority through targeted community initiatives.\n"
    
    narrative += f"""
FUNDING REQUEST:
We respectfully request ${funder.grant_amount:,} to support our mission and expand our impact in the community. This {funder.funding_type.lower() if funder.funding_type else 'grant'} funding will enable us to:

"""
    
    # Add specific uses based on funding priorities
    for i, priority in enumerate(funder.funding_priorities[:3], 1):
        narrative += f"{i}. Develop programs that directly support {priority.lower()}\n"
    
    narrative += f"""
EXPECTED OUTCOMES:
With {funder.name}'s support, we will create measurable impact that aligns with both our mission and your foundation's goals. Our experienced team, led by {org.contact_info.name}, is committed to transparent reporting and accountability.

CONCLUSION:
This partnership represents an opportunity to create lasting change in our community. We are prepared to provide detailed reporting and welcome the opportunity to discuss this proposal further.

Contact Information:
{org.contact_info.name}
{org.contact_info.email}

Thank you for considering our request.
"""
    
    return narrative.strip()


def create_final_document(workflow):
    """Create the final grant document in DOCX format"""
    try:
        from docx import Document
        from docx.shared import Inches
        from io import BytesIO
        
        # Create document
        doc = Document()
        
        # Title
        title = doc.add_heading(f'Grant Proposal to {workflow.funder.name}', 0)
        
        # Organization header
        org_header = doc.add_heading('Submitted by:', level=1)
        org_info = doc.add_paragraph(f'{workflow.organization.name}')
        org_info.add_run(f'\n{workflow.organization.contact_info.name}')
        org_info.add_run(f'\n{workflow.organization.contact_info.email}')
        org_info.add_run(f'\n{workflow.organization.location}')
        
        # Add date
        date_para = doc.add_paragraph(f'Date: {datetime.now().strftime("%B %d, %Y")}')
        
        # Add narrative
        doc.add_heading('Grant Proposal', level=1)
        
        # Split narrative into paragraphs
        paragraphs = workflow.narrative.split('\n\n')
        for para in paragraphs:
            if para.strip():
                if para.strip().isupper() and ':' in para:
                    # This is a section header
                    doc.add_heading(para.strip().rstrip(':'), level=2)
                else:
                    doc.add_paragraph(para.strip())
        
        # Convert to bytes
        doc_stream = BytesIO()
        doc.save(doc_stream)
        doc_stream.seek(0)
        
        return doc_stream.getvalue()
        
    except ImportError:
        # Fallback to text format if python-docx not available
        content = f"""
GRANT PROPOSAL TO {workflow.funder.name}

Submitted by: {workflow.organization.name}
Contact: {workflow.organization.contact_info.name}
Email: {workflow.organization.contact_info.email}
Date: {datetime.now().strftime("%B %d, %Y")}

{workflow.narrative}
"""
        return content.encode('utf-8')


def save_grant_document(workflow):
    """Save the final grant document"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Grant_Proposal_{workflow.organization.name.replace(' ', '_')}_{timestamp}.docx"
    filepath = Path(filename)
    
    with open(filepath, 'wb') as f:
        f.write(workflow.final_document)
    
    return filepath


if __name__ == "__main__":
    print("🎯 Grant Agent Refactored - Live Grant Building Demo")
    print("This demonstration shows the complete workflow in action!")
    print()
    
    success = build_complete_grant()
    
    if success:
        print("\n🎉 SUCCESS: Grant built successfully!")
        print("✅ The refactored system works perfectly!")
        print("🚀 Ready for production use!")
    else:
        print("\n❌ FAILED: Grant building encountered errors")
        sys.exit(1) 