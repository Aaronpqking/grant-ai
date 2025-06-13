#!/usr/bin/env python3
"""
Integrated Grant Builder with Critical Fixes Applied
Tests with all available documents and provides comprehensive quality reporting.
"""

import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import io

from refactored.models import GrantWorkflowData, OrganizationInfo, FunderInfo, LanguageAnalysis
from refactored.services import DocumentService, ExtractionService, LanguageAnalysisService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedExtractionService(ExtractionService):
    """Enhanced extraction service with integrated fixes"""
    
    def __init__(self):
        super().__init__()
        # Enhanced theme dictionaries
        self.enhanced_themes = {
            'cdfi_operations': [
                'community development financial institution', 'cdfi', 'lending', 
                'microfinance', 'community lending', 'financial inclusion',
                'community development', 'loan fund', 'capital access', 'cdi'
            ],
            'small_business': [
                'small business', 'entrepreneur', 'startup', 'business development',
                'job creation', 'business loans', 'working capital', 'micro enterprise',
                'sba', 'minority business', 'women-owned business'
            ],
            'housing': [
                'affordable housing', 'homeownership', 'housing development',
                'residential', 'housing finance', 'first-time homebuyer',
                'mortgage', 'housing trust fund', 'low-income housing'
            ],
            'racial_equity': [
                'minority-owned', 'black-owned', 'diversity', 'inclusion',
                'racial equity', 'underserved communities', 'communities of color',
                'african american', 'hispanic', 'latino', 'disadvantaged'
            ],
            'economic_development': [
                'economic development', 'economic growth', 'community investment',
                'revitalization', 'economic opportunity', 'wealth building',
                'job creation', 'economic impact', 'community economic'
            ],
            'geographic_focus': [
                'ohio', 'columbus', 'central ohio', 'midwest', 'urban', 'rural',
                'cleveland', 'cincinnati', 'toledo', 'dayton', 'akron'
            ],
            'financial_services': [
                'banking', 'credit', 'loan', 'capital', 'finance', 'investment',
                'microfinance', 'alternative lending', 'financial literacy'
            ],
            'non_profit': [
                'non-profit', 'nonprofit', '501c3', 'charitable', 'foundation',
                'community organization', 'social impact', 'mission-driven'
            ]
        }
    
    def extract_grant_amounts_enhanced(self, text: str) -> List[Tuple[float, str]]:
        """Enhanced amount extraction with K/M suffix handling"""
        amounts = []
        
        patterns = [
            # $200K or $200 thousand
            (r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:thousand|K)\b', 1000),
            # $2M or $2 million  
            (r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|M)\b', 1000000),
            # $200,000 explicit format
            (r'\$(\d{1,3}(?:,\d{3})+(?:\.\d{2})?)\b', 1),
            # $200 basic format (lowest priority)
            (r'\$(\d{1,3}(?:\.\d{2})?)\b', 1)
        ]
        
        for pattern, multiplier in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                amount = float(amount_str) * multiplier
                
                # Get context around the match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                amounts.append((amount, context))
        
        # Remove duplicates and sort by amount (descending)
        unique_amounts = []
        seen_amounts = set()
        
        for amount, context in sorted(amounts, key=lambda x: x[0], reverse=True):
            if amount not in seen_amounts:
                unique_amounts.append((amount, context))
                seen_amounts.add(amount)
        
        return unique_amounts
    
    def classify_content_sections(self, text: str) -> Dict[str, str]:
        """Enhanced field boundary detection"""
        sections = {
            'organization': '',
            'funder': '',
            'financial': '',
            'program': '',
            'unknown': ''
        }
        
        org_indicators = [
            'our mission', 'our organization', 'we are', 'we serve', 
            'founded in', 'established', 'cdfi', 'community development',
            'our impact', 'we have', 'our team', 'freedom equity'
        ]
        
        funder_indicators = [
            'foundation', 'grant program', 'funding opportunity', 
            'award', 'grants', 'we intend to award', 'application deadline',
            'eligibility', 'funding priorities', 'selection criteria',
            'keybank', 'bicentennial', 'funder'
        ]
        
        financial_indicators = [
            'budget', 'amount', 'funding', 'cost', 'expense', 
            'revenue', 'financial', '$', 'million', 'thousand'
        ]
        
        program_indicators = [
            'program', 'project', 'initiative', 'services',
            'activities', 'outcomes', 'impact', 'beneficiaries'
        ]
        
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        for paragraph in paragraphs:
            paragraph_lower = paragraph.lower()
            
            # Score each paragraph for different categories
            org_score = sum(1 for indicator in org_indicators if indicator in paragraph_lower)
            funder_score = sum(1 for indicator in funder_indicators if indicator in paragraph_lower)
            financial_score = sum(1 for indicator in financial_indicators if indicator in paragraph_lower)
            program_score = sum(1 for indicator in program_indicators if indicator in paragraph_lower)
            
            # Assign to highest scoring category
            max_score = max(org_score, funder_score, financial_score, program_score)
            
            if max_score == 0:
                sections['unknown'] += paragraph + '\n'
            elif funder_score == max_score:
                sections['funder'] += paragraph + '\n'
            elif org_score == max_score:
                sections['organization'] += paragraph + '\n'
            elif program_score == max_score:
                sections['program'] += paragraph + '\n'
            else:
                sections['financial'] += paragraph + '\n'
        
        return sections
    
    def extract_funder_priorities_enhanced(self, text: str) -> List[str]:
        """Enhanced funder priority extraction"""
        priorities = []
        
        priority_patterns = [
            r'(?:funding|grant)\s+priorities?[:\s]+([^.]+)',
            r'(?:we|the foundation)\s+(?:support|fund|focus on)[:\s]+([^.]+)', 
            r'eligible\s+(?:activities|programs|organizations)[:\s]+([^.]+)',
            r'(?:strategic|funding)\s+areas?[:\s]+([^.]+)',
            r'(?:focus|emphasis)\s+on[:\s]+([^.]+)',
            r'criteria\s+for\s+(?:selection|funding)[:\s]+([^.]+)'
        ]
        
        for pattern in priority_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                priority_text = match.group(1).strip()
                priority_text = re.sub(r'\s+', ' ', priority_text)
                if len(priority_text) > 10:
                    priorities.append(priority_text)
        
        # Look for bulleted/numbered lists
        priority_sections = re.finditer(
            r'(?:priorities|focus areas|funding areas|criteria)[:\s]*\n((?:\s*[•\-\*\d\.]\s*[^\n]+\n?)+)',
            text, re.IGNORECASE | re.MULTILINE
        )
        
        for section in priority_sections:
            list_text = section.group(1)
            items = re.findall(r'[•\-\*\d\.]\s*([^\n]+)', list_text)
            priorities.extend([item.strip() for item in items if len(item.strip()) > 5])
        
        return list(set(priorities))
    
    def extract_organization_enhanced(self, text: str) -> Optional[OrganizationInfo]:
        """Enhanced organization extraction with better field separation"""
        sections = self.classify_content_sections(text)
        org_text = sections['organization'] + sections['program']
        
        # Extract organization name
        name_patterns = [
            r'(?:organization|company|entity)(?:\s+name)?[:\s]+([^\n]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*(?:\s+Inc\.?)?)\s+is\s+a',
            r'(Freedom\s+Equity(?:\s+Inc\.?)?)',
            r'^([A-Z][A-Za-z\s&,.]+(?:Inc\.?|LLC|Foundation))',
        ]
        
        org_name = "Unknown Organization"
        for pattern in name_patterns:
            match = re.search(pattern, org_text, re.MULTILINE | re.IGNORECASE)
            if match:
                org_name = match.group(1).strip()
                break
        
        # Extract mission
        mission_patterns = [
            r'(?:mission|purpose)[:\s]+([^.]+(?:\.[^.]*){0,2})',
            r'(?:we|our organization)\s+(?:aim|seek|strive|work)\s+to\s+([^.]+)',
            r'(?:dedicated|committed)\s+to\s+([^.]+)'
        ]
        
        mission = ""
        for pattern in mission_patterns:
            match = re.search(pattern, org_text, re.IGNORECASE)
            if match:
                mission = match.group(1).strip()
                break
        
        # Extract background/history
        background_patterns = [
            r'(?:founded|established|created|started)\s+in\s+(\d{4})',
            r'(?:since|for)\s+(\d+)\s+years',
            r'(?:history|background)[:\s]+([^.]+(?:\.[^.]*){0,2})'
        ]
        
        background = ""
        for pattern in background_patterns:
            match = re.search(pattern, org_text, re.IGNORECASE)
            if match:
                background = match.group(0).strip()
                break
        
        # Extract location (only from org sections)
        location_patterns = [
            r'(?:located|based|headquarters?)\s+in\s+([^.,\n]+)',
            r'(?:serving|in)\s+(Columbus|Ohio|Central\s+Ohio)',
            r'(?:address|location)[:\s]+([^,\n]+)'
        ]
        
        location = ""
        for pattern in location_patterns:
            match = re.search(pattern, sections['organization'], re.IGNORECASE)
            if match and not any(word in match.group(1).lower() for word in ['grant', 'foundation', 'award']):
                location = match.group(1).strip()
                break
        
        return OrganizationInfo(
            name=org_name,
            mission=mission,
            background=background,
            location=location
        )
    
    def extract_funder_enhanced(self, text: str) -> Optional[FunderInfo]:
        """Enhanced funder extraction with better amount handling"""
        sections = self.classify_content_sections(text)
        funder_text = sections['funder'] + sections['financial']
        
        # Extract funder name
        funder_patterns = [
            r'(KeyBank\s+Foundation)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+Foundation)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+Grant\s+Program)',
        ]
        
        funder_name = "Unknown Funder"
        for pattern in funder_patterns:
            match = re.search(pattern, funder_text, re.IGNORECASE)
            if match:
                funder_name = match.group(1).strip()
                break
        
        # Extract grant amount using enhanced method
        amounts = self.extract_grant_amounts_enhanced(text)
        grant_amount = amounts[0][0] if amounts else 0.0
        
        # Extract priorities
        priorities = self.extract_funder_priorities_enhanced(funder_text)
        
        return FunderInfo(
            name=funder_name,
            grant_amount=grant_amount,
            funding_type="Unrestricted" if "unrestricted" in funder_text.lower() else "Restricted",
            funding_priorities=priorities
        )

class EnhancedLanguageAnalysisService(LanguageAnalysisService):
    """Enhanced language analysis with expanded themes"""
    
    def __init__(self):
        super().__init__()
        # Enhanced theme keywords
        self.theme_keywords = {
            'cdfi_operations': [
                'community development financial institution', 'cdfi', 'lending', 
                'microfinance', 'community lending', 'financial inclusion',
                'community development', 'loan fund', 'capital access', 'cdi',
                'alternative lending', 'community finance'
            ],
            'small_business': [
                'small business', 'entrepreneur', 'startup', 'business development',
                'job creation', 'business loans', 'working capital', 'micro enterprise',
                'sba', 'minority business', 'women-owned business', 'business support'
            ],
            'housing': [
                'affordable housing', 'homeownership', 'housing development',
                'residential', 'housing finance', 'first-time homebuyer',
                'mortgage', 'housing trust fund', 'low-income housing'
            ],
            'racial_equity': [
                'minority-owned', 'black-owned', 'diversity', 'inclusion',
                'racial equity', 'underserved communities', 'communities of color',
                'african american', 'hispanic', 'latino', 'disadvantaged',
                'equity', 'social justice'
            ],
            'economic_development': [
                'economic development', 'economic growth', 'community investment',
                'revitalization', 'economic opportunity', 'wealth building',
                'job creation', 'economic impact', 'community economic',
                'local economy', 'sustainable development'
            ],
            'geographic_focus': [
                'ohio', 'columbus', 'central ohio', 'midwest', 'urban', 'rural',
                'cleveland', 'cincinnati', 'toledo', 'dayton', 'akron',
                'local', 'community', 'neighborhood'
            ],
            'financial_services': [
                'banking', 'credit', 'loan', 'capital', 'finance', 'investment',
                'microfinance', 'alternative lending', 'financial literacy',
                'financial education', 'credit building'
            ],
            'community_impact': [
                'community impact', 'social impact', 'community benefit',
                'measurable outcomes', 'sustainability', 'capacity building',
                'technical assistance', 'community engagement'
            ]
        }
    
    def analyze_alignment_enhanced(self, org: OrganizationInfo, funder: FunderInfo) -> LanguageAnalysis:
        """Enhanced alignment analysis with better theme detection"""
        
        # Combine all org text
        org_text = f"{org.name} {org.mission} {org.background} {org.location}".lower()
        
        # Combine all funder text  
        funder_text = f"{funder.name} {' '.join(funder.funding_priorities)}".lower()
        
        # Find theme matches
        matching_themes = []
        org_themes = {}
        funder_themes = {}
        
        for theme, keywords in self.theme_keywords.items():
            org_has_theme = any(keyword in org_text for keyword in keywords)
            funder_has_theme = any(keyword in funder_text for keyword in keywords)
            
            if org_has_theme:
                org_themes[theme] = [kw for kw in keywords if kw in org_text]
            if funder_has_theme:
                funder_themes[theme] = [kw for kw in keywords if kw in funder_text]
            
            if org_has_theme and funder_has_theme:
                matching_themes.append(theme)
        
        # Calculate alignment score
        total_themes = len(self.theme_keywords)
        alignment_score = len(matching_themes) / total_themes if total_themes > 0 else 0.0
        
        # Boost score for strong matches
        if 'cdfi_operations' in matching_themes:
            alignment_score += 0.2
        if 'racial_equity' in matching_themes:
            alignment_score += 0.1
        if 'economic_development' in matching_themes:
            alignment_score += 0.1
        
        alignment_score = min(1.0, alignment_score)
        
        return LanguageAnalysis(
            alignment_score=alignment_score,
            matching_themes=matching_themes,
            org_themes=org_themes,
            funder_themes=funder_themes
        )

def generate_basic_narrative_enhanced(org: OrganizationInfo, funder: FunderInfo, analysis: LanguageAnalysis) -> str:
    """Enhanced narrative generation with theme integration"""
    
    narrative_sections = []
    
    # Organization Overview
    narrative_sections.append(f"""
ORGANIZATION OVERVIEW

{org.name} is a community development financial institution dedicated to creating economic opportunities in underserved communities. {"" if not org.mission else f"Our mission: {org.mission}"}

{"" if not org.background else f"Background: {org.background}"}

{"" if not org.location else f"Location: {org.location}"}

""")
    
    # Funding Opportunity
    narrative_sections.append(f"""
FUNDING OPPORTUNITY

We are requesting support from {funder.name} for ${funder.grant_amount:,.0f} in {funder.funding_type.lower()} funding.

""")
    
    # Alignment Analysis
    if analysis.matching_themes:
        narrative_sections.append(f"""
ALIGNMENT WITH FUNDER PRIORITIES

Our organization aligns with {funder.name} priorities in the following areas:
{chr(10).join(f"• {theme.replace('_', ' ').title()}" for theme in analysis.matching_themes)}

Alignment Score: {analysis.alignment_score:.2f}
""")
    
    # Funder Priorities
    if funder.funding_priorities:
        narrative_sections.append(f"""
FUNDER PRIORITY ALIGNMENT

{funder.name} priorities that align with our work:
{chr(10).join(f"• {priority}" for priority in funder.funding_priorities[:5])}
""")
    
    # Request Section
    narrative_sections.append(f"""
GRANT REQUEST

We respectfully request ${funder.grant_amount:,.0f} from {funder.name} to support our continued work in community development and economic empowerment. This funding will enable us to:

• Expand our lending capacity to serve more minority-owned businesses
• Strengthen our technical assistance programs
• Enhance our community impact measurement systems
• Build organizational capacity for sustainable growth

This investment aligns with {funder.name}'s commitment to supporting exemplary CDFIs that demonstrate measurable community impact and sustainable business models.

""")
    
    return "\n".join(narrative_sections)

def test_with_all_documents():
    """Test the integrated system with all available documents"""
    
    print("🚀 Integrated Grant Builder - Testing with All Documents")
    print("=" * 70)
    
    # Initialize enhanced services
    doc_service = DocumentService()
    extraction_service = EnhancedExtractionService()
    analysis_service = EnhancedLanguageAnalysisService()
    
    # Initialize workflow
    workflow_data = GrantWorkflowData()
    input_dir = Path('../input')
    
    # Get all document files
    doc_files = []
    for ext in ['*.docx', '*.pdf', '*.pptx']:
        doc_files.extend(input_dir.glob(ext))
    
    print(f"📂 Found {len(doc_files)} documents to process")
    
    # Process each document
    processed_count = 0
    successful_docs = []
    failed_docs = []
    
    for doc_file in doc_files[:10]:  # Limit to first 10 for testing
        try:
            print(f"   📄 Processing {doc_file.name}...")
            
            # Determine MIME type
            if doc_file.suffix == '.docx':
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif doc_file.suffix == '.pdf':
                mime_type = 'application/pdf'
            elif doc_file.suffix == '.pptx':
                mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            else:
                continue
            
            # Read and process
            with open(doc_file, 'rb') as f:
                file_data = f.read()
            
            doc_data = doc_service.process_upload(file_data, doc_file.name, mime_type)
            workflow_data.add_document(doc_data)
            
            successful_docs.append(doc_file.name)
            processed_count += 1
            
        except Exception as e:
            print(f"      ❌ Error processing {doc_file.name}: {str(e)}")
            failed_docs.append((doc_file.name, str(e)))
    
    print(f"\n✅ Successfully processed {processed_count} documents")
    print(f"❌ Failed to process {len(failed_docs)} documents")
    
    # Extract organization and funder information
    print("\n🔍 Extracting Enhanced Data...")
    
    try:
        extraction_result = extraction_service.extract_all(workflow_data)
        
        if extraction_result.organization:
            workflow_data.organization = extraction_result.organization
            print(f"   🏢 Organization: {workflow_data.organization.name}")
        
        if extraction_result.funder:
            workflow_data.funder = extraction_result.funder
            print(f"   💰 Funder: {workflow_data.funder.name}")
            print(f"   💵 Amount: ${workflow_data.funder.grant_amount:,.0f}")
    
    except Exception as e:
        print(f"   ❌ Extraction error: {str(e)}")
        return None
    
    # Perform enhanced language analysis
    print("\n🔤 Performing Enhanced Language Analysis...")
    
    if workflow_data.organization and workflow_data.funder:
        try:
            analysis_result = analysis_service.analyze_alignment_enhanced(
                workflow_data.organization, workflow_data.funder
            )
            workflow_data.language_analysis = analysis_result
            
            print(f"   📊 Alignment score: {analysis_result.alignment_score:.2f}")
            print(f"   🎯 Matching themes: {len(analysis_result.matching_themes)}")
            
            if analysis_result.matching_themes:
                print(f"   📋 Themes: {', '.join(analysis_result.matching_themes)}")
        
        except Exception as e:
            print(f"   ❌ Analysis error: {str(e)}")
    
    # Generate enhanced narrative
    print("\n📝 Generating Enhanced Narrative...")
    
    if workflow_data.organization and workflow_data.funder and workflow_data.language_analysis:
        try:
            narrative = generate_basic_narrative_enhanced(
                workflow_data.organization,
                workflow_data.funder, 
                workflow_data.language_analysis
            )
            workflow_data.narrative = narrative
            
            print(f"   ✅ Narrative generated: {len(narrative):,} characters")
            
            # Save enhanced narrative
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"../output/enhanced_grant_narrative_{timestamp}.txt"
            with open(output_path, 'w') as f:
                f.write(narrative)
            
            print(f"   💾 Saved to: {output_path}")
        
        except Exception as e:
            print(f"   ❌ Narrative generation error: {str(e)}")
    
    return workflow_data, successful_docs, failed_docs

def main():
    """Run integrated testing and quality analysis"""
    
    # Test with all documents
    result = test_with_all_documents()
    
    if result:
        workflow_data, successful_docs, failed_docs = result
        
        # Run quality analysis
        print("\n🔍 Running Quality Analysis...")
        from grant_quality_analyzer import GrantQualityAnalyzer
        
        analyzer = GrantQualityAnalyzer()
        report_path = analyzer.generate_verification_report(workflow_data)
        
        # Generate summary report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_path = f"../output/integration_summary_{timestamp}.txt"
        
        with open(summary_path, 'w') as f:
            f.write("INTEGRATED GRANT BUILDER - COMPREHENSIVE TEST REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("DOCUMENT PROCESSING SUMMARY\n")
            f.write("-" * 30 + "\n")
            f.write(f"Successfully Processed: {len(successful_docs)}\n")
            for doc in successful_docs:
                f.write(f"  ✅ {doc}\n")
            
            f.write(f"\nFailed to Process: {len(failed_docs)}\n")
            for doc, error in failed_docs:
                f.write(f"  ❌ {doc}: {error}\n")
            
            if workflow_data.organization:
                f.write(f"\nORGANIZATION EXTRACTED\n")
                f.write(f"Name: {workflow_data.organization.name}\n")
                f.write(f"Mission: {workflow_data.organization.mission[:200]}...\n")
                f.write(f"Location: {workflow_data.organization.location}\n")
            
            if workflow_data.funder:
                f.write(f"\nFUNDER EXTRACTED\n") 
                f.write(f"Name: {workflow_data.funder.name}\n")
                f.write(f"Amount: ${workflow_data.funder.grant_amount:,.0f}\n")
                f.write(f"Priorities: {len(workflow_data.funder.funding_priorities)}\n")
            
            if workflow_data.language_analysis:
                f.write(f"\nLANGUAGE ANALYSIS\n")
                f.write(f"Alignment Score: {workflow_data.language_analysis.alignment_score:.2f}\n")
                f.write(f"Matching Themes: {', '.join(workflow_data.language_analysis.matching_themes)}\n")
        
        print(f"\n📄 Integration summary saved to: {summary_path}")
        print(f"📄 Quality report saved to: {report_path}")
        
        print("\n🎯 Integration Testing Complete!")

if __name__ == "__main__":
    main() 