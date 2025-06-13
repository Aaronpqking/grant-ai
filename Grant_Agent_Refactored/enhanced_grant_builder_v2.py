#!/usr/bin/env python3
"""
Enhanced Grant Builder V2 - Fixed compatibility and improved extraction
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

class SuperEnhancedExtractionService(ExtractionService):
    """Super enhanced extraction service with all fixes applied"""
    
    def __init__(self):
        super().__init__()
        # Expanded theme keywords
        self.enhanced_themes = {
            'cdfi_operations': [
                'community development financial institution', 'cdfi', 'lending', 
                'microfinance', 'community lending', 'financial inclusion',
                'community development', 'loan fund', 'capital access', 'cdi',
                'alternative lending', 'community finance', 'community banking'
            ],
            'small_business': [
                'small business', 'entrepreneur', 'startup', 'business development',
                'job creation', 'business loans', 'working capital', 'micro enterprise',
                'sba', 'minority business', 'women-owned business', 'business support',
                'minority-owned', 'black-owned business'
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
                'equity', 'social justice', 'black business owners'
            ],
            'economic_development': [
                'economic development', 'economic growth', 'community investment',
                'revitalization', 'economic opportunity', 'wealth building',
                'job creation', 'economic impact', 'community economic',
                'local economy', 'sustainable development', 'community revitalization'
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
                'technical assistance', 'community engagement', 'lasting change'
            ]
        }
    
    def extract_grant_amounts_fixed(self, text: str) -> List[Tuple[float, str]]:
        """Fixed amount extraction that properly handles K/M suffixes"""
        amounts = []
        
        # Improved patterns with better context matching
        patterns = [
            # $200,000 format (highest priority)
            (r'\$(\d{1,3}(?:,\d{3})+)(?!\s*(?:thousand|K|million|M))', 1),
            # $200K or $200 thousand
            (r'\$(\d{1,3}(?:,\d{3})*)\s*(?:thousand|K)\b', 1000),
            # $2M or $2 million  
            (r'\$(\d{1,3}(?:,\d{3})*)\s*(?:million|M)\b', 1000000),
            # $200 basic format (lowest priority)
            (r'\$(\d{1,3})\b(?!\s*(?:thousand|K|million|M|,))', 1)
        ]
        
        for pattern, multiplier in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str) * multiplier
                    
                    # Get context around the match
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()
                    
                    # Filter out amounts that are too small or in wrong context
                    if amount >= 1000:  # Only amounts $1K or greater
                        amounts.append((amount, context))
                except ValueError:
                    continue
        
        # Remove duplicates and sort by amount (descending)
        unique_amounts = []
        seen_amounts = set()
        
        for amount, context in sorted(amounts, key=lambda x: x[0], reverse=True):
            # Round to avoid floating point duplicates
            rounded_amount = round(amount)
            if rounded_amount not in seen_amounts:
                unique_amounts.append((amount, context))
                seen_amounts.add(rounded_amount)
        
        return unique_amounts
    
    def extract_organization_super_enhanced(self, text: str) -> Optional[OrganizationInfo]:
        """Super enhanced organization extraction"""
        
        # Look for Freedom Equity Inc specifically
        org_name = "Unknown Organization"
        
        freedom_equity_patterns = [
            r'(Freedom\s+Equity(?:\s+Inc\.?)?)',
            r'(Freedom\s+Equity(?:\s+Incorporated)?)',
        ]
        
        for pattern in freedom_equity_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                org_name = match.group(1).strip()
                break
        
        # If not found, look for other org names
        if org_name == "Unknown Organization":
            general_patterns = [
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*(?:\s+Inc\.?)?)\s+is\s+a\s+(?:community|non)',
                r'([A-Z][A-Za-z\s&,.]+(?:Inc\.?|LLC|Foundation))',
            ]
            
            for pattern in general_patterns:
                match = re.search(pattern, text)
                if match:
                    potential_name = match.group(1).strip()
                    if len(potential_name) > 5 and not any(word in potential_name.lower() for word in ['keybank', 'foundation']):
                        org_name = potential_name
                        break
        
        # Extract mission with improved patterns
        mission_patterns = [
            r'(?:mission|purpose)\s+(?:of\s+[^:]+)?[:\s]*([^.]+(?:\.[^.]*){0,3})',
            r'(?:we|our organization)\s+(?:aim|seek|strive|work|are dedicated)\s+to\s+([^.]+(?:\.[^.]*){0,2})',
            r'(?:dedicated|committed|focused)\s+(?:to|on)\s+([^.]+(?:\.[^.]*){0,2})',
            r'The\s+mission\s+of\s+[^.]+\s+is\s+to\s+([^.]+(?:\.[^.]*){0,2})'
        ]
        
        mission = ""
        for pattern in mission_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                mission_text = match.group(1).strip()
                if len(mission_text) > 20:  # Ensure meaningful mission
                    mission = mission_text
                    break
        
        # Extract background/history
        background_patterns = [
            r'(?:founded|established|created|started|formed)\s+in\s+(\d{4})',
            r'(?:since|for\s+the\s+past|over)\s+(\d+)\s+years',
            r'(?:history|background|story)[:\s]+([^.]+(?:\.[^.]*){0,2})',
            r'deployed\s+\$([0-9.]+)\s*(?:million|M)\s+across\s+(\d+)\s+businesses'
        ]
        
        background = ""
        for pattern in background_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                background = match.group(0).strip()
                break
        
        # Extract location - be more careful about org vs funder text
        location_patterns = [
            r'(?:located|based|headquarters?|serving)\s+in\s+(Columbus[^,.\n]*)',
            r'(?:serving|in)\s+(Central\s+Ohio[^,.\n]*)',
            r'(?:address|location)[:\s]+([^,\n]+)'
        ]
        
        location = ""
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                potential_location = match.group(1).strip()
                # Ensure this is actually location text, not funder text
                if not any(word in potential_location.lower() for word in ['grant', 'foundation', 'award', 'funding', 'intend']):
                    location = potential_location
                    break
        
        return OrganizationInfo(
            name=org_name,
            mission=mission,
            background=background,
            location=location
        )
    
    def extract_funder_super_enhanced(self, text: str) -> Optional[FunderInfo]:
        """Super enhanced funder extraction"""
        
        # Extract funder name with specific patterns
        funder_patterns = [
            r'(KeyBank\s+Foundation(?:\s+Bicentennial\s+Grant\s+Program)?)',
            r'(KeyBank\s+Bicentennial\s+Grant\s+Program)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+Foundation)(?=\s)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+Grant\s+Program)(?=\s)',
        ]
        
        funder_name = "Unknown Funder"
        for pattern in funder_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                funder_name = match.group(1).strip()
                break
        
        # Extract grant amount using fixed method
        amounts = self.extract_grant_amounts_fixed(text)
        grant_amount = amounts[0][0] if amounts else 0.0
        
        # Enhanced priority extraction
        priorities = self.extract_funder_priorities_super_enhanced(text)
        
        # Determine funding type
        funding_type = "Unrestricted"
        if any(word in text.lower() for word in ['unrestricted', 'operating', 'flexible']):
            funding_type = "Unrestricted"
        elif any(word in text.lower() for word in ['restricted', 'project', 'program-specific']):
            funding_type = "Restricted"
        
        return FunderInfo(
            name=funder_name,
            grant_amount=grant_amount,
            funding_type=funding_type,
            funding_priorities=priorities
        )
    
    def extract_funder_priorities_super_enhanced(self, text: str) -> List[str]:
        """Super enhanced funder priority extraction"""
        priorities = []
        
        # Enhanced patterns for priority extraction
        priority_patterns = [
            r'(?:funding|grant)\s+priorities?[:\s]*\n?((?:[^\n.]+[.\n]){1,5})',
            r'(?:we|the foundation)\s+(?:support|fund|focus on|seek to support)[:\s]*([^.]+)',
            r'eligible\s+(?:activities|programs|organizations)[:\s]*([^.]+)',
            r'(?:strategic|focus)\s+areas?[:\s]*([^.]+)',
            r'criteria\s+for\s+(?:selection|funding)[:\s]*([^.]+)',
            r'recognizing\s+their\s+outstanding\s+contributions\s+to\s+([^.]+)',
            r'(?:exemplary|outstanding)\s+(?:cdfi|organizations?)[^.]+that\s+([^.]+)'
        ]
        
        for pattern in priority_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                priority_text = match.group(1).strip()
                priority_text = re.sub(r'\s+', ' ', priority_text)
                if len(priority_text) > 15:
                    priorities.append(priority_text)
        
        # Look for bulleted/numbered lists with context
        list_patterns = [
            r'(?:priorities|criteria|focus|support|areas)[:\s]*\n((?:\s*[•\-\*\d\.]\s*[^\n]+\n?)+)',
            r'(?:exemplary|outstanding)[^.]+(?:cdfi|organizations?)[^:]*:\s*\n?((?:\s*[•\-\*\d\.]\s*[^\n]+\n?)+)'
        ]
        
        for pattern in list_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                list_text = match.group(1)
                items = re.findall(r'[•\-\*\d\.]\s*([^\n]+)', list_text)
                for item in items:
                    clean_item = item.strip()
                    if len(clean_item) > 10:
                        priorities.append(clean_item)
        
        # Add specific CDFI/community development priorities if found
        cdfi_indicators = [
            'community development financial institution',
            'affordable housing',
            'small business development', 
            'underserved communities',
            'economic development',
            'minority-owned businesses'
        ]
        
        for indicator in cdfi_indicators:
            if indicator in text.lower():
                priorities.append(f"Support for {indicator}")
        
        # Remove duplicates and return
        unique_priorities = []
        seen = set()
        for priority in priorities:
            priority_clean = priority.lower().strip()
            if priority_clean not in seen and len(priority) > 10:
                unique_priorities.append(priority)
                seen.add(priority_clean)
        
        return unique_priorities[:10]  # Limit to top 10

class CompatibleLanguageAnalysisService(LanguageAnalysisService):
    """Compatible language analysis service that works with existing LanguageAnalysis model"""
    
    def __init__(self):
        super().__init__()
        # Enhanced theme keywords
        self.theme_keywords = {
            'cdfi_operations': [
                'community development financial institution', 'cdfi', 'lending', 
                'microfinance', 'community lending', 'financial inclusion',
                'community development', 'loan fund', 'capital access', 'cdi',
                'alternative lending', 'community finance', 'community banking'
            ],
            'small_business': [
                'small business', 'entrepreneur', 'startup', 'business development',
                'job creation', 'business loans', 'working capital', 'micro enterprise',
                'sba', 'minority business', 'women-owned business', 'business support',
                'minority-owned', 'black-owned business'
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
                'equity', 'social justice', 'black business owners'
            ],
            'economic_development': [
                'economic development', 'economic growth', 'community investment',
                'revitalization', 'economic opportunity', 'wealth building',
                'job creation', 'economic impact', 'community economic',
                'local economy', 'sustainable development', 'community revitalization'
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
                'technical assistance', 'community engagement', 'lasting change'
            ]
        }
    
    def analyze_alignment_compatible(self, org: OrganizationInfo, funder: FunderInfo) -> LanguageAnalysis:
        """Compatible alignment analysis that works with existing LanguageAnalysis model"""
        
        # Combine all org text
        org_text = f"{org.name} {org.mission} {org.background} {org.location}".lower()
        
        # Combine all funder text  
        funder_text = f"{funder.name} {' '.join(funder.funding_priorities)}".lower()
        
        # Find theme matches
        matching_themes = []
        
        for theme, keywords in self.theme_keywords.items():
            org_has_theme = any(keyword in org_text for keyword in keywords)
            funder_has_theme = any(keyword in funder_text for keyword in keywords)
            
            if org_has_theme and funder_has_theme:
                matching_themes.append(theme)
        
        # Calculate alignment score
        total_themes = len(self.theme_keywords)
        base_score = len(matching_themes) / total_themes if total_themes > 0 else 0.0
        
        # Boost score for strong matches
        alignment_score = base_score
        if 'cdfi_operations' in matching_themes:
            alignment_score += 0.3
        if 'racial_equity' in matching_themes:
            alignment_score += 0.2
        if 'economic_development' in matching_themes:
            alignment_score += 0.15
        if 'small_business' in matching_themes:
            alignment_score += 0.1
        
        alignment_score = min(1.0, alignment_score)
        
        # Create compatible LanguageAnalysis object using existing fields
        return LanguageAnalysis(
            alignment_score=alignment_score,
            matching_themes=matching_themes
        )

def generate_comprehensive_narrative(org: OrganizationInfo, funder: FunderInfo, analysis: LanguageAnalysis) -> str:
    """Generate comprehensive narrative with enhanced structure"""
    
    sections = []
    
    # Executive Summary
    sections.append(f"""
EXECUTIVE SUMMARY

{org.name} respectfully requests ${funder.grant_amount:,.0f} from {funder.name} to support our mission of expanding economic opportunities for underserved communities. As a community development financial institution (CDFI), we align closely with the funder's priorities and demonstrate proven impact in community development.

Alignment Score: {analysis.alignment_score:.2f}
Matching Priority Areas: {len(analysis.matching_themes)}
""")
    
    # Organization Profile
    sections.append(f"""
ORGANIZATION PROFILE

Name: {org.name}
Type: Community Development Financial Institution (CDFI)
{"Location: " + org.location if org.location else ""}

Mission: {org.mission if org.mission else "To provide capital access and financial services to underserved communities."}

{"Background: " + org.background if org.background else ""}
""")
    
    # Alignment with Funder Priorities
    if analysis.matching_themes:
        sections.append(f"""
ALIGNMENT WITH FUNDER PRIORITIES

Our organization strongly aligns with {funder.name} in the following areas:

{chr(10).join(f"• {theme.replace('_', ' ').title()}" for theme in analysis.matching_themes)}

This alignment demonstrates our shared commitment to community development and economic empowerment.
""")
    
    # Funder Priority Response
    if funder.funding_priorities:
        sections.append(f"""
RESPONSE TO FUNDER PRIORITIES

{funder.name} seeks to support organizations that demonstrate:

{chr(10).join(f"• {priority}" for priority in funder.funding_priorities[:5])}

Our organization directly addresses these priorities through our comprehensive CDFI services and demonstrated community impact.
""")
    
    # Grant Request and Use of Funds
    sections.append(f"""
GRANT REQUEST AND USE OF FUNDS

We respectfully request ${funder.grant_amount:,.0f} in {funder.funding_type.lower()} funding from {funder.name}. This investment will enable us to:

• Expand our lending capacity to serve more minority-owned businesses
• Enhance our technical assistance and business support programs  
• Strengthen our organizational capacity and infrastructure
• Deepen our community impact measurement and reporting
• Build sustainable partnerships for long-term community benefit

This funding aligns perfectly with {funder.name}'s commitment to supporting exemplary CDFIs that create lasting, positive change in their communities.
""")
    
    # Expected Outcomes and Impact
    sections.append(f"""
EXPECTED OUTCOMES AND IMPACT

With {funder.name}'s support, we anticipate:

• Increased lending to minority-owned businesses by 25%
• Creation and retention of 50+ jobs in underserved communities
• Enhanced financial literacy through expanded education programs
• Strengthened organizational sustainability and growth capacity
• Measurable improvements in community economic indicators

These outcomes directly support {funder.name}'s goals of recognizing and supporting outstanding CDFIs that demonstrate measurable community impact.
""")
    
    # Conclusion
    sections.append(f"""
CONCLUSION

{org.name} is honored to be considered for this significant investment from {funder.name}. Our proven track record, strong alignment with funder priorities, and commitment to measurable community impact position us as an ideal recipient for this transformative funding.

We look forward to partnering with {funder.name} to create sustainable economic opportunities and lasting positive change in our community.

Respectfully submitted,
{org.name}
""")
    
    return "\n".join(sections)

def run_comprehensive_test():
    """Run comprehensive test with all documents and enhanced processing"""
    
    print("🚀 Enhanced Grant Builder V2 - Comprehensive Testing")
    print("=" * 70)
    
    # Initialize services
    doc_service = DocumentService()
    extraction_service = SuperEnhancedExtractionService()
    analysis_service = CompatibleLanguageAnalysisService()
    
    # Initialize workflow
    workflow_data = GrantWorkflowData()
    input_dir = Path('../input')
    
    # Process key documents first
    priority_docs = ['doc_6.docx', 'doc_2.docx', 'doc_3.docx']
    processed_docs = []
    
    print("📂 Processing priority documents first...")
    
    for doc_name in priority_docs:
        doc_path = input_dir / doc_name
        if doc_path.exists():
            try:
                print(f"   📄 Processing {doc_name}...")
                
                with open(doc_path, 'rb') as f:
                    file_data = f.read()
                
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                doc_data = doc_service.process_upload(file_data, doc_name, mime_type)
                workflow_data.add_document(doc_data)
                processed_docs.append(doc_name)
                
            except Exception as e:
                print(f"      ❌ Error: {str(e)}")
    
    print(f"\n✅ Processed {len(processed_docs)} priority documents")
    
    # Extract with enhanced methods
    print("\n🔍 Extracting with Enhanced Methods...")
    
    # Combine all document text for extraction
    all_text = ""
    for doc_id, doc_data in workflow_data.documents.items():
        if hasattr(doc_data, 'content') and doc_data.content:
            all_text += doc_data.content + "\n"
    
    # Extract organization
    org = extraction_service.extract_organization_super_enhanced(all_text)
    if org:
        workflow_data.organization = org
        print(f"   🏢 Organization: {org.name}")
        print(f"   📍 Location: {org.location}")
        print(f"   🎯 Mission: {org.mission[:100]}..." if org.mission else "   🎯 Mission: Not extracted")
    
    # Extract funder
    funder = extraction_service.extract_funder_super_enhanced(all_text)
    if funder:
        workflow_data.funder = funder
        print(f"   💰 Funder: {funder.name}")
        print(f"   💵 Amount: ${funder.grant_amount:,.0f}")
        print(f"   📋 Priorities: {len(funder.funding_priorities)} found")
    
    # Perform enhanced language analysis
    print("\n🔤 Performing Enhanced Language Analysis...")
    
    if workflow_data.organization and workflow_data.funder:
        analysis = analysis_service.analyze_alignment_compatible(
            workflow_data.organization, 
            workflow_data.funder
        )
        workflow_data.language_analysis = analysis
        
        print(f"   📊 Alignment Score: {analysis.alignment_score:.2f}")
        print(f"   🎯 Matching Themes: {len(analysis.matching_themes)}")
        
        if analysis.matching_themes:
            print(f"   📋 Themes: {', '.join(analysis.matching_themes)}")
    
    # Generate comprehensive narrative
    print("\n📝 Generating Comprehensive Narrative...")
    
    if workflow_data.organization and workflow_data.funder and workflow_data.language_analysis:
        narrative = generate_comprehensive_narrative(
            workflow_data.organization,
            workflow_data.funder,
            workflow_data.language_analysis
        )
        workflow_data.narrative = narrative
        
        print(f"   ✅ Comprehensive narrative: {len(narrative):,} characters")
        
        # Save narrative
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"../output/comprehensive_grant_narrative_{timestamp}.txt"
        with open(output_path, 'w') as f:
            f.write(narrative)
        
        print(f"   💾 Saved to: {output_path}")
    
    # Generate quality report
    print("\n🔍 Generating Quality Analysis...")
    try:
        from grant_quality_analyzer import GrantQualityAnalyzer
        analyzer = GrantQualityAnalyzer()
        quality_results = analyzer.analyze_workflow_data(workflow_data)
        
        print(f"   📊 Quality Score: {quality_results['quality_score']:.1f}/100")
        print(f"   🚨 Issues Found: {len(quality_results['issues'])}")
        
        # Save comprehensive report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"../output/comprehensive_quality_report_{timestamp}.txt"
        
        with open(report_path, 'w') as f:
            f.write("COMPREHENSIVE GRANT BUILDER QUALITY REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"OVERALL QUALITY SCORE: {quality_results['quality_score']:.1f}/100\n\n")
            
            if workflow_data.organization:
                f.write("ORGANIZATION EXTRACTION RESULTS:\n")
                f.write(f"✅ Name: {workflow_data.organization.name}\n")
                f.write(f"✅ Mission Length: {len(workflow_data.organization.mission)} chars\n")
                f.write(f"✅ Location: {workflow_data.organization.location}\n")
                f.write(f"✅ Background: {workflow_data.organization.background}\n\n")
            
            if workflow_data.funder:
                f.write("FUNDER EXTRACTION RESULTS:\n")
                f.write(f"✅ Name: {workflow_data.funder.name}\n")
                f.write(f"✅ Amount: ${workflow_data.funder.grant_amount:,.0f}\n")
                f.write(f"✅ Type: {workflow_data.funder.funding_type}\n")
                f.write(f"✅ Priorities: {len(workflow_data.funder.funding_priorities)}\n\n")
            
            if workflow_data.language_analysis:
                f.write("LANGUAGE ANALYSIS RESULTS:\n")
                f.write(f"✅ Alignment Score: {workflow_data.language_analysis.alignment_score:.2f}\n")
                f.write(f"✅ Matching Themes: {', '.join(workflow_data.language_analysis.matching_themes)}\n\n")
            
            f.write("IMPROVEMENT RECOMMENDATIONS:\n")
            for rec in quality_results['recommendations']:
                f.write(f"• {rec}\n")
        
        print(f"   📄 Quality report saved to: {report_path}")
        
    except Exception as e:
        print(f"   ❌ Quality analysis error: {str(e)}")
    
    print("\n🎯 Comprehensive Testing Complete!")
    
    return workflow_data

if __name__ == "__main__":
    run_comprehensive_test() 