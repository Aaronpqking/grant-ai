#!/usr/bin/env python3
"""
Enhanced Grant Builder v3 - Multi-Template System
Supports federal, state, foundation, and corporate grant templates with automatic type detection.
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from Grant_Agent.src.template_manager import TemplateManager, GrantType
    from Grant_Agent.src.schema import GrantRequest, OrganizationInfo, FunderInfo
except ImportError:
    # Fallback imports if the above don't work
    print("Template manager not available - using fallback system")
    TemplateManager = None
    GrantType = None

from refactored.services import DocumentClassifier, OrganizationExtractor, FunderExtractor
from refactored.models import DocumentData, DocumentType, GrantWorkflowData

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultiTemplateGrantBuilder:
    """Enhanced grant builder with multi-template support"""
    
    def __init__(self):
        self.classifier = DocumentClassifier()
        self.org_extractor = OrganizationExtractor()
        self.funder_extractor = FunderExtractor()
        self.template_manager = TemplateManager() if TemplateManager else None
        
        # Directory paths
        self.input_dir = Path("../input")
        self.output_dir = Path("../output")
        self.output_dir.mkdir(exist_ok=True)
    
    def process_grant_application(self) -> Dict[str, Any]:
        """Process grant application with template selection"""
        
        try:
            logger.info("🚀 Starting Multi-Template Grant Builder v3")
            
            # Step 1: Load and classify documents
            documents = self._load_documents()
            if not documents:
                return {"error": "No documents found in input directory"}
            
            # Step 2: Extract organization and funder information
            extraction_result = self._extract_information(documents)
            
            # Step 3: Identify grant type and select template
            grant_type = self._identify_grant_type(extraction_result.get('funder'))
            
            # Step 4: Generate grant proposal using appropriate template
            if self.template_manager:
                proposal_result = self._generate_templated_proposal(extraction_result, grant_type)
            else:
                proposal_result = self._generate_fallback_proposal(extraction_result, grant_type)
            
            # Step 5: Save results
            output_files = self._save_results(proposal_result, grant_type)
            
            return {
                "status": "success",
                "grant_type": grant_type.value if grant_type else "foundation",
                "extraction": extraction_result,
                "proposal": proposal_result,
                "output_files": output_files,
                "processing_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "processing_time": datetime.now().isoformat()
            }
    
    def _load_documents(self) -> List[DocumentData]:
        """Load and classify documents from input directory"""
        
        documents = []
        
        if not self.input_dir.exists():
            logger.warning(f"Input directory {self.input_dir} does not exist")
            return documents
        
        for file_path in self.input_dir.glob("*.docx"):
            try:
                # Read document content
                content = self._read_docx_content(file_path)
                
                # Classify document
                doc_type = self.classifier.classify_document(content)
                
                # Create document data
                doc = DocumentData(
                    file_path=str(file_path),
                    content=content,
                    document_type=doc_type,
                    file_size=file_path.stat().st_size,
                    last_modified=datetime.fromtimestamp(file_path.stat().st_mtime)
                )
                
                documents.append(doc)
                logger.info(f"Loaded {file_path.name} as {doc_type.value}")
                
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        return documents
    
    def _read_docx_content(self, file_path: Path) -> str:
        """Read content from DOCX file"""
        try:
            from docx import Document
            doc = Document(file_path)
            content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text.strip())
            
            return "\n".join(content)
            
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            return ""
    
    def _extract_information(self, documents: List[DocumentData]) -> Dict[str, Any]:
        """Extract organization and funder information"""
        
        # Combine all document content
        all_content = "\n".join([doc.content for doc in documents if doc.content])
        
        # Extract organization info
        org_info = self.org_extractor.extract(all_content)
        
        # Extract funder info
        funder_info = self.funder_extractor.extract(all_content)
        
        return {
            "organization": {
                "name": org_info.name if org_info else "Unknown Organization",
                "mission": org_info.mission if org_info else "Mission needs extraction",
                "location": org_info.location if org_info else "Location unknown",
                "contact": {
                    "name": org_info.contact_info.name if org_info and org_info.contact_info else "Contact unknown",
                    "email": org_info.contact_info.email if org_info and org_info.contact_info else "Email unknown"
                }
            },
            "funder": {
                "name": funder_info.name if funder_info else "Unknown Funder",
                "grant_amount": funder_info.grant_amount if funder_info else 0,
                "funding_type": funder_info.funding_type if funder_info else "Unknown",
                "priorities": funder_info.funding_priorities if funder_info else []
            },
            "documents_processed": len(documents),
            "extraction_quality": self._assess_extraction_quality(org_info, funder_info)
        }
    
    def _identify_grant_type(self, funder_info: Dict[str, Any]) -> Optional[GrantType]:
        """Identify grant type based on funder information"""
        
        if not GrantType or not funder_info:
            return None
        
        funder_name = funder_info.get('name', '').lower()
        
        # Federal grant indicators
        federal_keywords = [
            'nsf', 'nih', 'doe', 'dod', 'nasa', 'usda', 'epa', 'neh', 'nea',
            'department of', 'national science foundation', 'national institutes',
            'federal', 'government', 'agency'
        ]
        
        # State grant indicators
        state_keywords = [
            'state', 'commonwealth', 'department of education', 'arts council',
            'health department', 'environmental agency'
        ]
        
        # Corporate grant indicators
        corporate_keywords = [
            'corporation', 'company', 'inc.', 'llc', 'bank', 'foundation',
            'keybank', 'wells fargo', 'chase', 'microsoft', 'google'
        ]
        
        # Check for federal
        for keyword in federal_keywords:
            if keyword in funder_name:
                return GrantType.FEDERAL
        
        # Check for state
        for keyword in state_keywords:
            if keyword in funder_name:
                return GrantType.STATE
        
        # Check for corporate
        for keyword in corporate_keywords:
            if keyword in funder_name and 'foundation' in funder_name:
                return GrantType.CORPORATE
        
        # Default to foundation
        return GrantType.FOUNDATION
    
    def _generate_templated_proposal(self, extraction_result: Dict[str, Any], grant_type: GrantType) -> Dict[str, Any]:
        """Generate proposal using template system"""
        
        try:
            # Create grant request object
            grant_request = self._create_grant_request(extraction_result)
            
            # Render using template manager
            result = self.template_manager.render_grant_proposal(grant_request, grant_type)
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "content": result["content"],
                    "grant_type": result["grant_type"],
                    "template_used": result["template_file"],
                    "requirements": result["requirements"],
                    "missing_sections": result.get("missing_sections", []),
                    "evaluation_criteria": result.get("evaluation_criteria", []),
                    "character_count": len(result["content"]),
                    "estimated_pages": len(result["content"]) // 2500  # Rough estimate
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "Template rendering failed"),
                    "grant_type": grant_type.value
                }
        
        except Exception as e:
            logger.error(f"Template generation error: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "grant_type": grant_type.value if grant_type else "unknown"
            }
    
    def _generate_fallback_proposal(self, extraction_result: Dict[str, Any], grant_type: Optional[GrantType]) -> Dict[str, Any]:
        """Generate proposal using fallback method when template system unavailable"""
        
        org = extraction_result.get('organization', {})
        funder = extraction_result.get('funder', {})
        
        # Basic template based on grant type
        if grant_type == GrantType.FEDERAL:
            content = self._generate_federal_fallback(org, funder)
        elif grant_type == GrantType.STATE:
            content = self._generate_state_fallback(org, funder)
        elif grant_type == GrantType.CORPORATE:
            content = self._generate_corporate_fallback(org, funder)
        else:
            content = self._generate_foundation_fallback(org, funder)
        
        return {
            "status": "success",
            "content": content,
            "grant_type": grant_type.value if grant_type else "foundation",
            "template_used": "fallback_template",
            "character_count": len(content),
            "estimated_pages": len(content) // 2500
        }
    
    def _create_grant_request(self, extraction_result: Dict[str, Any]) -> GrantRequest:
        """Create GrantRequest object from extraction results"""
        
        org_data = extraction_result.get('organization', {})
        funder_data = extraction_result.get('funder', {})
        
        # Create organization info
        org_info = OrganizationInfo(
            name=org_data.get('name', 'Unknown Organization'),
            mission=org_data.get('mission', 'Mission needs extraction'),
            contact=org_data.get('contact', {})
        )
        
        # Create funder info  
        funder_info = FunderInfo(
            name=funder_data.get('name', 'Unknown Funder'),
            funding_areas=funder_data.get('priorities', []),
            grant_amounts={'typical': str(funder_data.get('grant_amount', 0))}
        )
        
        return GrantRequest(
            organization_info=org_info,
            funder_info=funder_info,
            grant_metadata=extraction_result
        )
    
    def _assess_extraction_quality(self, org_info, funder_info) -> float:
        """Assess quality of extracted information"""
        
        score = 0.0
        max_score = 10.0
        
        # Organization scoring
        if org_info:
            if org_info.name and org_info.name != "Unknown Organization":
                score += 2.0
            if org_info.mission and len(org_info.mission) > 20:
                score += 2.0
            if org_info.contact_info and org_info.contact_info.email:
                score += 1.0
        
        # Funder scoring
        if funder_info:
            if funder_info.name and funder_info.name != "Unknown Funder":
                score += 2.0
            if funder_info.grant_amount and funder_info.grant_amount > 0:
                score += 2.0
            if funder_info.funding_priorities:
                score += 1.0
        
        return round(score / max_score * 100, 1)
    
    def _generate_federal_fallback(self, org: Dict, funder: Dict) -> str:
        """Generate federal grant fallback template"""
        return f"""
# {org.get('name', 'Organization')} - Federal Grant Proposal

## Project Summary
{org.get('mission', 'Project summary needed')}

## Intellectual Merit
This project addresses fundamental questions and utilizes innovative approaches to advance the field.

## Broader Impacts
• Advancing knowledge and understanding
• Training diverse participants
• Disseminating results broadly
• Benefiting society

## Budget Justification
Total Requested: ${funder.get('grant_amount', 0):,.0f}

## Personnel
Principal Investigator: {org.get('contact', {}).get('name', 'TBD')}

## Facilities and Equipment
[Facilities description needed]

## Timeline
[Project timeline needed]

## Evaluation Plan
[Evaluation methodology needed]

## Required Attachments
- [ ] SF-424 Form
- [ ] Budget Forms
- [ ] Biographical Sketches
- [ ] Current and Pending Support
- [ ] Facilities Description
"""
    
    def _generate_state_fallback(self, org: Dict, funder: Dict) -> str:
        """Generate state grant fallback template"""
        return f"""
# {org.get('name', 'Organization')} - State Grant Application

## Executive Summary
{org.get('mission', 'Executive summary needed')}

## Needs Assessment
[Community needs analysis needed]

## Project Description
[Detailed project description needed]

## Local Impact
This project will directly benefit local communities and support state priorities.

## Budget
Total Requested: ${funder.get('grant_amount', 0):,.0f}

## Sustainability
[Long-term sustainability plan needed]

## Community Partnerships
[Partnership descriptions needed]

## Contact Information
{org.get('contact', {}).get('name', 'Contact TBD')}
{org.get('contact', {}).get('email', 'Email TBD')}
"""
    
    def _generate_corporate_fallback(self, org: Dict, funder: Dict) -> str:
        """Generate corporate grant fallback template"""
        return f"""
# Partnership Proposal: {org.get('name', 'Organization')} & {funder.get('name', 'Corporation')}

## Executive Summary
{org.get('name', 'Organization')} seeks partnership with {funder.get('name', 'Corporation')} for ${funder.get('grant_amount', 0):,.0f} to support {org.get('mission', 'our mission')}.

## Business Case
This partnership provides measurable business value through enhanced brand reputation and community goodwill.

## ROI Analysis
Expected returns include improved brand recognition and strengthened community relationships.

## Employee Engagement
• Volunteer opportunities
• Skills-based volunteering
• Mentoring programs

## Community Impact
[Measurable community impact needed]

## Recognition Opportunities
• Corporate website and materials
• Social media promotion
• Press release opportunities

## Contact Information
{org.get('contact', {}).get('name', 'Contact TBD')}
{org.get('contact', {}).get('email', 'Email TBD')}
"""
    
    def _generate_foundation_fallback(self, org: Dict, funder: Dict) -> str:
        """Generate foundation grant fallback template"""
        return f"""
# Grant Proposal to {funder.get('name', 'Foundation')}

## Executive Summary
{org.get('name', 'Organization')} respectfully requests ${funder.get('grant_amount', 0):,.0f} from {funder.get('name', 'Foundation')} to support {org.get('mission', 'our mission')}.

## Organization Profile
**Name:** {org.get('name', 'Organization')}
**Mission:** {org.get('mission', 'Mission statement needed')}

## Project Description
[Detailed project description needed]

## Expected Outcomes
[Expected outcomes needed]

## Evaluation Plan
[Evaluation methodology needed]

## Budget
Total Request: ${funder.get('grant_amount', 0):,.0f}
Funding Type: {funder.get('funding_type', 'Unknown')}

## Sustainability
[Long-term sustainability plan needed]

## Contact Information
{org.get('contact', {}).get('name', 'Contact TBD')}
{org.get('contact', {}).get('email', 'Email TBD')}
"""
    
    def _save_results(self, proposal_result: Dict[str, Any], grant_type: Optional[GrantType]) -> Dict[str, str]:
        """Save proposal results to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        grant_type_str = grant_type.value if grant_type else "foundation"
        
        # Save text version
        text_filename = f"grant_proposal_{grant_type_str}_{timestamp}.txt"
        text_path = self.output_dir / text_filename
        
        try:
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(proposal_result.get('content', ''))
            
            logger.info(f"Saved proposal to {text_filename}")
            
            return {
                "text_file": str(text_path),
                "grant_type": grant_type_str,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return {"error": str(e)}
    
    def get_template_info(self) -> Dict[str, Any]:
        """Get information about available templates"""
        
        if not self.template_manager:
            return {
                "status": "unavailable",
                "message": "Template manager not available - using fallback templates"
            }
        
        return {
            "status": "available",
            "templates": self.template_manager.list_available_templates()
        }


def run_comprehensive_test():
    """Run comprehensive test of the multi-template grant builder"""
    
    print("🧪 Testing Multi-Template Grant Builder v3")
    print("=" * 50)
    
    builder = MultiTemplateGrantBuilder()
    
    # Show template information
    template_info = builder.get_template_info()
    print(f"📋 Template System: {template_info['status']}")
    
    if template_info['status'] == 'available':
        templates = template_info['templates']
        print(f"📝 Available Templates: {len(templates)}")
        for grant_type, info in templates.items():
            print(f"   • {grant_type.title()}: {info['template_file']}")
            print(f"     - Pages: {info['specifications']['page_limits']['min']}-{info['specifications']['page_limits']['max']}")
            print(f"     - Sections: {len(info['structure']['required_sections'])} required")
    
    print("\n🚀 Processing Grant Application...")
    
    # Process the grant application
    result = builder.process_grant_application()
    
    if result.get('status') == 'success':
        print(f"✅ Success! Grant Type: {result['grant_type']}")
        print(f"📄 Template Used: {result['proposal'].get('template_used', 'fallback')}")
        print(f"📊 Extraction Quality: {result['extraction'].get('extraction_quality', 0)}%")
        print(f"📝 Content Length: {result['proposal'].get('character_count', 0)} characters")
        print(f"📄 Estimated Pages: {result['proposal'].get('estimated_pages', 0)}")
        
        # Show missing sections if any
        missing = result['proposal'].get('missing_sections', [])
        if missing:
            print(f"⚠️  Missing Sections: {len(missing)}")
            for section in missing[:3]:  # Show first 3
                print(f"   • {section}")
        
        # Show output files
        output_files = result.get('output_files', {})
        if output_files:
            print(f"💾 Output File: {output_files.get('text_file', 'Not saved')}")
    
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    return result


if __name__ == "__main__":
    result = run_comprehensive_test() 