#!/usr/bin/env python3
"""
Multi-Template Grant System
Supports different grant types with appropriate templates and requirements.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from refactored.services import DocumentClassifier, OrganizationExtractor, FunderExtractor
from refactored.models import DocumentData, DocumentType, GrantWorkflowData

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GrantType(Enum):
    """Different types of grants with specific requirements"""
    FEDERAL = "federal"
    STATE = "state"
    FOUNDATION = "foundation"
    CORPORATE = "corporate"
    INTERNATIONAL = "international"


class GrantTemplateSystem:
    """System for managing different grant templates and requirements"""
    
    def __init__(self):
        self.classifier = DocumentClassifier()
        self.org_extractor = OrganizationExtractor()
        self.funder_extractor = FunderExtractor()
        
        # Template specifications
        self.template_specs = self._load_template_specifications()
        
        # Directory paths
        self.input_dir = Path("../input")
        self.output_dir = Path("../output") 
        self.output_dir.mkdir(exist_ok=True)
    
    def _load_template_specifications(self) -> Dict[GrantType, Dict[str, Any]]:
        """Load specifications for different grant types"""
        
        return {
            GrantType.FEDERAL: {
                "name": "Federal Grant Proposal",
                "page_limits": {"min": 10, "max": 15},
                "required_sections": [
                    "Project Summary", "Project Description", "Intellectual Merit",
                    "Broader Impacts", "Budget Justification", "Personnel",
                    "Facilities and Equipment", "Timeline", "Evaluation Plan"
                ],
                "compliance_requirements": [
                    "DUNS Number", "SAM Registration", "IRB Approval (if applicable)",
                    "IACUC Approval (if applicable)", "Export Control Compliance"
                ],
                "required_attachments": [
                    "SF-424 Form", "Budget Forms", "Biographical Sketches",
                    "Current and Pending Support", "Facilities Description"
                ],
                "evaluation_criteria": [
                    "Intellectual Merit", "Broader Impacts", "Technical Feasibility",
                    "Institutional Capacity", "Cost Effectiveness"
                ],
                "formatting": {
                    "font": "Times New Roman, 11pt",
                    "margins": "1 inch all sides",
                    "line_spacing": "Single",
                    "page_numbers": "Required"
                }
            },
            GrantType.STATE: {
                "name": "State Grant Application",
                "page_limits": {"min": 5, "max": 8},
                "required_sections": [
                    "Executive Summary", "Needs Assessment", "Project Description",
                    "Goals and Objectives", "Methodology", "Local Impact",
                    "Budget", "Sustainability", "Community Partnerships"
                ],
                "compliance_requirements": [
                    "State Registration", "Local Procurement Laws",
                    "Prevailing Wage Compliance", "Environmental Review (if applicable)"
                ],
                "required_attachments": [
                    "State Application Form", "Budget Worksheet",
                    "Organizational Chart", "Board Resolution"
                ],
                "evaluation_criteria": [
                    "Local Community Benefit", "State Priority Alignment",
                    "Cost Effectiveness", "Organizational Capacity", "Community Support"
                ],
                "formatting": {
                    "font": "Arial or Times New Roman, 12pt",
                    "margins": "1 inch all sides", 
                    "line_spacing": "1.5",
                    "page_numbers": "Required"
                }
            },
            GrantType.FOUNDATION: {
                "name": "Foundation Grant Proposal",
                "page_limits": {"min": 2, "max": 5},
                "required_sections": [
                    "Executive Summary", "Organization Profile", "Needs Statement",
                    "Project Description", "Goals and Outcomes", "Methodology",
                    "Evaluation Plan", "Budget", "Sustainability"
                ],
                "compliance_requirements": [
                    "501(c)(3) Status", "Board Oversight", "Financial Transparency",
                    "Outcome Reporting"
                ],
                "required_attachments": [
                    "IRS Determination Letter", "Audited Financial Statements",
                    "Board of Directors List", "Organizational Chart"
                ],
                "evaluation_criteria": [
                    "Mission Alignment", "Organizational Capacity", "Measurable Outcomes",
                    "Cost Effectiveness", "Sustainability Plan"
                ],
                "formatting": {
                    "font": "Any readable font, 11pt",
                    "margins": "1 inch all sides",
                    "line_spacing": "Single or 1.15",
                    "page_numbers": "Optional"
                }
            },
            GrantType.CORPORATE: {
                "name": "Corporate Partnership Proposal",
                "page_limits": {"min": 3, "max": 7},
                "required_sections": [
                    "Executive Summary", "Business Case", "Project Overview",
                    "Corporate Alignment", "ROI Analysis", "Employee Engagement",
                    "Community Impact", "Success Metrics", "Recognition Opportunities"
                ],
                "compliance_requirements": [
                    "Corporate Giving Policies", "CSR Alignment",
                    "Stakeholder Approval", "Publicity Rights"
                ],
                "required_attachments": [
                    "Corporate Application Form", "Budget Breakdown",
                    "Impact Measurement Plan", "Recognition Plan"
                ],
                "evaluation_criteria": [
                    "Brand Alignment", "Business Value", "Employee Engagement",
                    "Community Impact", "ROI Potential"
                ],
                "formatting": {
                    "font": "Professional, branded if specified",
                    "margins": "1 inch all sides",
                    "line_spacing": "1.15",
                    "page_numbers": "Required"
                }
            }
        }
    
    def identify_grant_type(self, funder_name: str) -> GrantType:
        """Identify grant type based on funder name"""
        
        funder_lower = funder_name.lower()
        
        # Federal agency indicators
        federal_indicators = [
            'nsf', 'nih', 'doe', 'dod', 'nasa', 'usda', 'epa', 'neh', 'nea',
            'department of', 'national science foundation', 'national institutes',
            'federal', 'government', 'agency'
        ]
        
        # State agency indicators
        state_indicators = [
            'state', 'commonwealth', 'department of education', 'arts council',
            'health department', 'environmental agency'
        ]
        
        # Corporate indicators
        corporate_indicators = [
            'corporation', 'company', 'inc.', 'llc', 'bank',
            'keybank', 'wells fargo', 'chase', 'microsoft', 'google', 'walmart'
        ]
        
        # Check for federal
        for indicator in federal_indicators:
            if indicator in funder_lower:
                return GrantType.FEDERAL
        
        # Check for state
        for indicator in state_indicators:
            if indicator in funder_lower:
                return GrantType.STATE
        
        # Check for corporate (but not foundation)
        for indicator in corporate_indicators:
            if indicator in funder_lower and 'foundation' not in funder_lower:
                return GrantType.CORPORATE
        
        # Default to foundation
        return GrantType.FOUNDATION
    
    def generate_grant_proposal(self, org_info: Dict, funder_info: Dict, grant_type: GrantType) -> Dict[str, Any]:
        """Generate grant proposal based on type"""
        
        template_spec = self.template_specs[grant_type]
        
        if grant_type == GrantType.FEDERAL:
            content = self._generate_federal_proposal(org_info, funder_info, template_spec)
        elif grant_type == GrantType.STATE:
            content = self._generate_state_proposal(org_info, funder_info, template_spec)
        elif grant_type == GrantType.CORPORATE:
            content = self._generate_corporate_proposal(org_info, funder_info, template_spec)
        else:  # FOUNDATION
            content = self._generate_foundation_proposal(org_info, funder_info, template_spec)
        
        return {
            "status": "success",
            "grant_type": grant_type.value,
            "content": content,
            "specifications": template_spec,
            "character_count": len(content),
            "estimated_pages": len(content) // 2500,
            "requirements_check": self._check_requirements(org_info, funder_info, template_spec)
        }
    
    def _generate_federal_proposal(self, org: Dict, funder: Dict, spec: Dict) -> str:
        """Generate federal grant proposal"""
        return f"""
{spec['name']}: {org.get('name', 'Organization Name')}

PROJECT SUMMARY
{org.get('mission', 'Project summary describing the proposed research and its significance.')}

PROJECT DESCRIPTION

Intellectual Merit:
This project addresses fundamental questions in our field and employs innovative approaches to advance scientific knowledge. The proposed research builds upon established theoretical frameworks while introducing novel methodologies that have the potential to significantly impact our understanding.

Broader Impacts:
• Advancing knowledge and understanding within the field
• Training and mentoring opportunities for diverse participants
• Dissemination of results through publications and presentations
• Potential for societal benefit through practical applications
• Enhancement of research infrastructure and capacity

BUDGET JUSTIFICATION
Total Budget Requested: ${funder.get('grant_amount', 0):,.0f}

Personnel:
Principal Investigator: {org.get('contact', {}).get('name', 'PI Name Required')}
[Additional personnel details needed]

Equipment and Supplies:
[Equipment description and justification needed]

Travel:
[Travel justification for conferences and collaboration]

FACILITIES AND EQUIPMENT
[Description of institutional facilities and equipment available for the project]

PROJECT TIMELINE
Year 1: [Project initiation and methodology development]
Year 2: [Data collection and analysis phase]
Year 3: [Results compilation and dissemination]

EVALUATION PLAN
[Detailed evaluation methodology including metrics and assessment criteria]

DISSEMINATION PLAN
Results will be disseminated through peer-reviewed publications, conference presentations, and public outreach activities.

COMPLIANCE REQUIREMENTS:
{self._format_compliance_requirements(spec['compliance_requirements'])}

REQUIRED ATTACHMENTS:
{self._format_required_attachments(spec['required_attachments'])}
"""
    
    def _generate_state_proposal(self, org: Dict, funder: Dict, spec: Dict) -> str:
        """Generate state grant proposal"""
        return f"""
{spec['name']}: {org.get('name', 'Organization Name')}

EXECUTIVE SUMMARY
{org.get('name', 'Organization')} requests ${funder.get('grant_amount', 0):,.0f} from {funder.get('name', 'State Agency')} to support {org.get('mission', 'community development initiatives')}.

NEEDS ASSESSMENT
Our community faces significant challenges that this project will address:
• [Specific community need 1]
• [Specific community need 2] 
• [Specific community need 3]

PROJECT DESCRIPTION
[Detailed description of proposed activities and how they address identified needs]

GOALS AND OBJECTIVES
Short-term Goals (6-12 months):
• [Specific, measurable short-term goal]
• [Additional short-term objective]

Long-term Goals (1-3 years):
• [Sustainable impact objective]
• [Community capacity building goal]

LOCAL IMPACT
This project will directly benefit local communities by:
• Creating measurable improvements in [specific area]
• Supporting state priorities in [relevant priority area]
• Engaging [number] community members
• Building lasting partnerships with local organizations

METHODOLOGY
[Detailed description of project implementation approach]

BUDGET BREAKDOWN
Total Request: ${funder.get('grant_amount', 0):,.0f}
Personnel: [percentage]%
Program Costs: [percentage]%
Administrative: [percentage]%

SUSTAINABILITY PLAN
[Description of how project benefits will continue beyond grant period]

COMMUNITY PARTNERSHIPS
• [Local partner organization 1]
• [Local partner organization 2]
• [Government agency partnership]

EVALUATION METRICS
[Specific, measurable outcomes and evaluation methods]

CONTACT INFORMATION
{org.get('contact', {}).get('name', 'Project Director')}
{org.get('contact', {}).get('email', 'Contact Email')}

COMPLIANCE:
{self._format_compliance_requirements(spec['compliance_requirements'])}
"""
    
    def _generate_corporate_proposal(self, org: Dict, funder: Dict, spec: Dict) -> str:
        """Generate corporate partnership proposal"""
        return f"""
{spec['name']}: {org.get('name', 'Organization')} & {funder.get('name', 'Corporation')}

EXECUTIVE SUMMARY
{org.get('name', 'Organization')} seeks to partner with {funder.get('name', 'Corporation')} for ${funder.get('grant_amount', 0):,.0f} to support {org.get('mission', 'our community impact mission')}.

BUSINESS CASE
This strategic partnership offers {funder.get('name', 'Corporation')} significant value:
• Enhanced brand reputation through community engagement
• Measurable social impact aligned with corporate values
• Employee engagement and retention opportunities
• Positive media coverage and PR value
• Demonstration of corporate social responsibility leadership

ROI ANALYSIS
Expected Returns on Investment:
• Brand Recognition: Estimated media value of $[calculated amount]
• Employee Engagement: [number] employees participating in volunteer opportunities
• Community Impact: [number] community members served
• Social Media Reach: Estimated [number] impressions across platforms

CORPORATE ALIGNMENT
This initiative aligns with {funder.get('name', 'Corporation')}'s values by:
• Supporting [relevant corporate value/mission area]
• Demonstrating commitment to [specific CSR focus area]
• Creating measurable community impact
• Engaging employees in meaningful service

PROJECT OVERVIEW
[Detailed description of proposed activities and community impact]

EMPLOYEE ENGAGEMENT OPPORTUNITIES
• Volunteer days and team building activities
• Skills-based volunteering using employee expertise
• Board service and leadership development
• Mentoring programs connecting employees with community members

COMMUNITY IMPACT METRICS
• [Specific number] community members served
• [Percentage]% improvement in [relevant metric]
• [Number] partnerships established
• [Measurable outcome] achieved

SUCCESS METRICS AND KPIs
• Community Impact: [specific metrics]
• Employee Participation: [participation goals]
• Brand Exposure: [media coverage goals]
• ROI Measurement: [financial and social return metrics]

RECOGNITION OPPORTUNITIES
• Corporate website feature and case study
• Social media content and campaigns
• Press releases and media coverage
• Award nominations and recognition events
• Annual report inclusion

INVESTMENT DETAILS
Total Partnership Investment: ${funder.get('grant_amount', 0):,.0f}
Project Duration: [timeframe]
Expected Media Value: $[estimated amount]
Employee Volunteer Hours: [estimated hours]

NEXT STEPS
We welcome the opportunity to discuss this partnership proposal and customize our collaboration to meet {funder.get('name', 'Corporation')}'s specific goals and requirements.

CONTACT INFORMATION
{org.get('contact', {}).get('name', 'Partnership Director')}
{org.get('contact', {}).get('email', 'Contact Email')}
"""
    
    def _generate_foundation_proposal(self, org: Dict, funder: Dict, spec: Dict) -> str:
        """Generate foundation grant proposal"""
        return f"""
{spec['name']}: Request to {funder.get('name', 'Foundation')}

EXECUTIVE SUMMARY
{org.get('name', 'Organization')} respectfully requests ${funder.get('grant_amount', 0):,.0f} from {funder.get('name', 'Foundation')} to support {org.get('mission', 'our mission-driven work')}.

ORGANIZATION PROFILE
Name: {org.get('name', 'Organization Name')}
Mission: {org.get('mission', 'Organization mission statement')}
Location: {org.get('location', 'Organization location')}

{org.get('name', 'Organization')} has been serving our community with dedication and measurable impact. Our work directly aligns with {funder.get('name', 'Foundation')}'s commitment to creating positive change.

NEEDS STATEMENT
Our community faces significant challenges that require innovative solutions:
• [Specific community need or problem]
• [Supporting data and evidence]
• [Why immediate action is necessary]

PROJECT DESCRIPTION
With {funder.get('name', 'Foundation')}'s support, we will:
• [Specific project activity 1]
• [Specific project activity 2]
• [Specific project activity 3]

This project will create measurable impact by addressing the identified needs through evidence-based approaches.

GOALS AND EXPECTED OUTCOMES
Short-term Outcomes (6-12 months):
• [Specific, measurable outcome]
• [Additional short-term result]

Long-term Impact (1-3 years):
• [Sustainable change objective]
• [Community capacity building result]

METHODOLOGY
Our approach combines proven strategies with innovative elements:
• [Implementation strategy 1]
• [Implementation strategy 2]
• [Quality assurance and monitoring approach]

EVALUATION PLAN
We will measure success through:
• [Specific metric and measurement method]
• [Additional evaluation criterion]
• [Reporting schedule and methods]

BUDGET SUMMARY
Total Request: ${funder.get('grant_amount', 0):,.0f}
{funder.get('funding_type', 'Funding')} to support:
• Program implementation: [percentage]%
• Personnel: [percentage]%
• Administrative costs: [percentage]%

SUSTAINABILITY
This investment will create lasting impact through:
• [Sustainability strategy 1]
• [Capacity building approach]
• [Long-term funding plan]

CONCLUSION
{org.get('name', 'Organization')} is honored to submit this proposal to {funder.get('name', 'Foundation')}. We are committed to transparent reporting, measurable outcomes, and creating the positive change that aligns with your foundation's vision.

We welcome the opportunity to discuss this proposal further and answer any questions.

CONTACT INFORMATION
{org.get('contact', {}).get('name', 'Executive Director')}
{org.get('contact', {}).get('email', 'Contact Email')}

Thank you for your consideration.
"""
    
    def _format_compliance_requirements(self, requirements: List[str]) -> str:
        """Format compliance requirements list"""
        return "\n".join([f"• {req}" for req in requirements])
    
    def _format_required_attachments(self, attachments: List[str]) -> str:
        """Format required attachments list"""
        return "\n".join([f"- [ ] {att}" for att in attachments])
    
    def _check_requirements(self, org_info: Dict, funder_info: Dict, spec: Dict) -> Dict[str, Any]:
        """Check if proposal meets requirements"""
        
        issues = []
        
        # Check organization information completeness
        if not org_info.get('name') or org_info.get('name') == 'Unknown Organization':
            issues.append("Organization name needs to be provided")
        
        if not org_info.get('mission') or len(org_info.get('mission', '')) < 20:
            issues.append("Organization mission statement needs development")
        
        if not org_info.get('contact', {}).get('email'):
            issues.append("Contact email address required")
        
        # Check funder information
        if not funder_info.get('grant_amount') or funder_info.get('grant_amount') == 0:
            issues.append("Grant amount needs to be specified")
        
        return {
            "compliance_check": "incomplete" if issues else "complete",
            "issues_found": issues,
            "required_sections": spec['required_sections'],
            "page_limits": spec['page_limits'],
            "formatting_requirements": spec['formatting']
        }
    
    def process_grant_application_cli(self) -> Dict[str, Any]:
        """Process grant application with template selection (CLI version)"""
        
        try:
            logger.info("🚀 Starting Multi-Template Grant System")
            
            # Load documents
            documents = self._load_documents()
            if not documents:
                return {"error": "No documents found in input directory"}
            
            # Extract information
            extraction_result = self._extract_information(documents)
            
            # Identify grant type
            funder_name = extraction_result['funder']['name']
            grant_type = self.identify_grant_type(funder_name)
            
            logger.info(f"📋 Identified Grant Type: {grant_type.value}")
            
            # Generate proposal
            proposal_result = self.generate_grant_proposal(
                extraction_result['organization'],
                extraction_result['funder'],
                grant_type
            )
            
            # Save results
            output_files = self._save_results(proposal_result, grant_type)
            
            return {
                "status": "success",
                "grant_type": grant_type.value,
                "extraction": extraction_result,
                "proposal": proposal_result,
                "output_files": output_files,
                "template_specifications": self.template_specs[grant_type],
                "processing_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _load_documents(self) -> List[DocumentData]:
        """Load documents from input directory"""
        
        documents = []
        
        if not self.input_dir.exists():
            logger.warning(f"Input directory {self.input_dir} does not exist")
            return documents
        
        for file_path in self.input_dir.glob("*.docx"):
            try:
                content = self._read_docx_content(file_path)
                doc_type = self.classifier.classify_document(content)
                
                # Create DocumentData using correct parameters
                doc = DocumentData(
                    content=content,
                    filename=file_path.name,
                    mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    uploaded_at=datetime.fromtimestamp(file_path.stat().st_mtime),
                    content_hash=str(hash(content))[:8],
                    document_type=doc_type
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
        
        all_content = "\n".join([doc.content for doc in documents if doc.content])
        
        org_info = self.org_extractor.extract(all_content)
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
            "documents_processed": len(documents)
        }
    
    def _save_results(self, proposal_result: Dict[str, Any], grant_type: GrantType) -> Dict[str, str]:
        """Save proposal results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"grant_proposal_{grant_type.value}_{timestamp}.txt"
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(proposal_result.get('content', ''))
            
            logger.info(f"Saved proposal to {filename}")
            
            return {
                "text_file": str(filepath),
                "grant_type": grant_type.value,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return {"error": str(e)}
    
    def get_template_specifications(self) -> Dict[str, Any]:
        """Get all template specifications"""
        return {
            grant_type.value: {
                "name": spec["name"],
                "page_limits": spec["page_limits"],
                "required_sections": spec["required_sections"],
                "evaluation_criteria": spec["evaluation_criteria"],
                "formatting": spec["formatting"]
            }
            for grant_type, spec in self.template_specs.items()
        }

    def extract_organization_info(self, text: str) -> dict:
        """Extract organization information from document text"""
        org_info = {
            'name': '',
            'type': '',
            'focus_areas': [],
            'location': '',
            'size': ''
        }
        
        # Simple text analysis for organization details
        text_lower = text.lower()
        
        # Extract organization name (look for common patterns)
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if any(keyword in line.lower() for keyword in ['organization', 'company', 'foundation', 'inc', 'llc', 'corp']):
                org_info['name'] = line.strip()
                break
        
        # Determine organization type
        if any(word in text_lower for word in ['nonprofit', 'non-profit', 'charity', 'foundation']):
            org_info['type'] = 'nonprofit'
        elif any(word in text_lower for word in ['corporation', 'company', 'inc', 'llc']):
            org_info['type'] = 'for-profit'
        elif any(word in text_lower for word in ['university', 'college', 'school', 'academic']):
            org_info['type'] = 'academic'
        
        return org_info

    def _generate_recommendations(self, grant_type: GrantType, analysis_details: str) -> str:
        """Generates recommendations based on grant type and analysis."""
        recommendations = [
            "Ensure all sections are complete and address the funder's specific criteria.",
            "Double-check budget calculations and justifications.",
            "Proofread carefully for any grammatical errors or typos."
        ]
        if grant_type == GrantType.FEDERAL:
            recommendations.append("Emphasize broader impacts and intellectual merit clearly.")
        elif grant_type == GrantType.STATE:
            recommendations.append("Highlight community benefits and local partnerships.")
        elif grant_type == GrantType.FOUNDATION:
            recommendations.append("Clearly align your project with the foundation's mission.")
        elif grant_type == GrantType.CORPORATE:
            recommendations.append("Focus on business value, ROI, and corporate alignment.")
        
        if len(analysis_details) < 1000: 
            recommendations.append("Consider expanding on the project details and impact.")

        return "\n".join([f"- {rec}" for rec in recommendations])

    def process_grant_application(self, text_content: str) -> str:
        """Process grant application with document content for ADK agent"""
        try:
            logger.info("🚀 Starting Multi-Template Grant System (ADK Agent Request)")
            
            if not text_content or text_content == "No documents provided. Please upload grant documents for analysis.":
                return "⚠️ No document content provided. Please upload documents for analysis."

            org_info_dict = self.org_extractor.extract(text_content)
            org_info = {
                "name": org_info_dict.name if org_info_dict else "Unknown Organization",
                "mission": org_info_dict.mission if org_info_dict else "Mission needs extraction",
                "location": org_info_dict.location if org_info_dict else "Location unknown",
                "contact": {
                    "name": org_info_dict.contact_info.name if org_info_dict and org_info_dict.contact_info else "Contact unknown",
                    "email": org_info_dict.contact_info.email if org_info_dict and org_info_dict.contact_info else "Email unknown"
                }
            }

            funder_info_dict = self.funder_extractor.extract(text_content)
            funder_info = {
                "name": funder_info_dict.name if funder_info_dict else "Unknown Funder",
                "grant_amount": funder_info_dict.grant_amount if funder_info_dict else 0,
                "funding_type": funder_info_dict.funding_type if funder_info_dict else "Unknown",
                "priorities": funder_info_dict.funding_priorities if funder_info_dict else []
            }

            if not funder_info['name'] or funder_info['name'] == "Unknown Funder":
                detected_type = self.identify_grant_type(text_content)
                logger.warning(f"Funder name not definitively extracted. Detected type based on full text: {detected_type.value}")
            else:
                detected_type = self.identify_grant_type(funder_info['name'])
                logger.info(f"Funder name: {funder_info['name']}. Detected type: {detected_type.value}")

            template_spec = self.template_specs.get(detected_type)
            if not template_spec:
                logger.error(f"No template specification found for grant type: {detected_type}")
                return f"❌ Error: Could not find template for grant type '{detected_type.value}'."

            proposal_content = ""
            if detected_type == GrantType.FEDERAL:
                proposal_content = self._generate_federal_proposal(org_info, funder_info, template_spec)
            elif detected_type == GrantType.STATE:
                proposal_content = self._generate_state_proposal(org_info, funder_info, template_spec)
            elif detected_type == GrantType.CORPORATE:
                proposal_content = self._generate_corporate_proposal(org_info, funder_info, template_spec)
            elif detected_type == GrantType.FOUNDATION:
                proposal_content = self._generate_foundation_proposal(org_info, funder_info, template_spec)
            else:
                logger.warning(f"No specific proposal generator for type {detected_type}, defaulting to foundation style.")
                proposal_content = self._generate_foundation_proposal(org_info, funder_info, self.template_specs[GrantType.FOUNDATION])

            requirements_check_result = self._check_requirements(org_info, funder_info, template_spec)
            recommendations = self._generate_recommendations(detected_type, proposal_content)

            output = f"""
📊 **Grant Analysis Results**

🏢 **Organization Extracted:**
- Name: {org_info.get('name', 'Not detected')}
- Mission: {org_info.get('mission', 'Not detected')}

💰 **Funder Extracted:**
- Name: {funder_info.get('name', 'Not detected')}
- Grant Amount: ${funder_info.get('grant_amount', 0):,.0f}

🎯 **Detected Grant Type:** {detected_type.value.title()}

📋 **Template Applied:** {template_spec['name']}
- Focus: {template_spec.get('evaluation_criteria', ['N/A'])[0] if template_spec.get('evaluation_criteria') else 'N/A'} 
               (Typical Focus: {', '.join(template_spec['required_sections'][:2])}...)

📝 **Generated Proposal Snippet (Partial):**
{proposal_content[:1000]}... 
(Full content generated but truncated for brevity)

✅ **Requirements Check:**
- Status: {requirements_check_result['compliance_check']}
"""
            if requirements_check_result['issues_found']:
                output += "\n- Issues:\n"
                for issue in requirements_check_result['issues_found'][:3]:
                    output += f"  • {issue}\n"
            output += f"""\n💡 **Recommendations:**
{recommendations}
            """
            return output

        except Exception as e:
            logger.error(f"Error processing grant application via ADK: {str(e)}", exc_info=True)
            return f"❌ Error processing grant application: {str(e)}"


def run_template_system_test():
    """Test the multi-template grant system"""
    
    print("🧪 Testing Multi-Template Grant System")
    print("=" * 50)
    
    system = GrantTemplateSystem()
    
    # Show available templates
    templates = system.get_template_specifications()
    print(f"📝 Available Grant Templates: {len(templates)}")
    
    for grant_type, spec in templates.items():
        print(f"\n📋 {spec['name']} ({grant_type})")
        print(f"   Pages: {spec['page_limits']['min']}-{spec['page_limits']['max']}")
        print(f"   Sections: {len(spec['required_sections'])} required")
        print(f"   Criteria: {len(spec['evaluation_criteria'])} evaluation points")
    
    print(f"\n🚀 Processing Grant Application...")
    
    # Process application
    result = system.process_grant_application_cli()
    
    if result.get('status') == 'success':
        print(f"✅ Success! Grant Type: {result['grant_type']}")
        print(f"📊 Extraction: {result['extraction']['documents_processed']} documents processed")
        print(f"📄 Content: {result['proposal']['character_count']} characters")
        print(f"📋 Pages: ~{result['proposal']['estimated_pages']} estimated")
        
        # Show requirements check
        req_check = result['proposal']['requirements_check']
        print(f"🔍 Compliance: {req_check['compliance_check']}")
        
        if req_check['issues_found']:
            print(f"⚠️  Issues Found: {len(req_check['issues_found'])}")
            for issue in req_check['issues_found'][:3]:
                print(f"   • {issue}")
        
        print(f"💾 Output: {result['output_files'].get('text_file', 'Not saved')}")
        
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    return result


if __name__ == "__main__":
    result = run_template_system_test() 