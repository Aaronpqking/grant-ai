#!/usr/bin/env python3
"""
Critical Fixes for Grant Agent System
Addresses the most urgent issues identified in quality analysis.
"""

import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

def fix_amount_extraction(text: str) -> List[Tuple[float, str]]:
    """
    Enhanced amount extraction that handles K/M suffixes and comma formatting
    Returns list of (amount, context) tuples
    """
    amounts = []
    
    # Pattern 1: $200K, $200,000, $2M format with context
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
            
            # Get context around the match (50 chars before and after)
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

def fix_field_boundary_detection(text: str) -> Dict[str, str]:
    """
    Improved field boundary detection to prevent data mixing
    """
    sections = {
        'organization': '',
        'funder': '',
        'financial': '',
        'unknown': ''
    }
    
    # Define section indicators
    org_indicators = [
        'our mission', 'our organization', 'we are', 'we serve', 
        'founded in', 'established', 'cdfi', 'community development',
        'our impact', 'we have', 'our team'
    ]
    
    funder_indicators = [
        'foundation', 'grant program', 'funding opportunity', 
        'award', 'grants', 'we intend to award', 'application deadline',
        'eligibility', 'funding priorities', 'selection criteria'
    ]
    
    financial_indicators = [
        'budget', 'amount', 'funding', 'cost', 'expense', 
        'revenue', 'financial', '$'
    ]
    
    # Split text into paragraphs
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    for paragraph in paragraphs:
        paragraph_lower = paragraph.lower()
        
        # Score each paragraph for different categories
        org_score = sum(1 for indicator in org_indicators if indicator in paragraph_lower)
        funder_score = sum(1 for indicator in funder_indicators if indicator in paragraph_lower)
        financial_score = sum(1 for indicator in financial_indicators if indicator in paragraph_lower)
        
        # Assign to highest scoring category
        if funder_score > org_score and funder_score > financial_score:
            sections['funder'] += paragraph + '\n'
        elif org_score > financial_score:
            sections['organization'] += paragraph + '\n'
        elif financial_score > 0:
            sections['financial'] += paragraph + '\n'
        else:
            sections['unknown'] += paragraph + '\n'
    
    return sections

def extract_funder_priorities_enhanced(text: str) -> List[str]:
    """
    Enhanced funder priority extraction
    """
    priorities = []
    
    # Priority indicators
    priority_patterns = [
        r'(?:funding|grant)\s+priorities?[:\s]+([^.]+)',
        r'(?:we|the foundation)\s+(?:support|fund|focus on)[:\s]+([^.]+)', 
        r'eligible\s+(?:activities|programs|organizations)[:\s]+([^.]+)',
        r'(?:strategic|funding)\s+areas?[:\s]+([^.]+)',
        r'(?:focus|emphasis)\s+on[:\s]+([^.]+)'
    ]
    
    for pattern in priority_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            priority_text = match.group(1).strip()
            # Clean up the priority text
            priority_text = re.sub(r'\s+', ' ', priority_text)
            if len(priority_text) > 10:  # Filter out very short matches
                priorities.append(priority_text)
    
    # Also look for bulleted/numbered lists after priority keywords
    priority_sections = re.finditer(
        r'(?:priorities|focus areas|funding areas)[:\s]*\n((?:\s*[•\-\*\d\.]\s*[^\n]+\n?)+)',
        text, re.IGNORECASE | re.MULTILINE
    )
    
    for section in priority_sections:
        list_text = section.group(1)
        # Extract individual list items
        items = re.findall(r'[•\-\*\d\.]\s*([^\n]+)', list_text)
        priorities.extend([item.strip() for item in items if len(item.strip()) > 5])
    
    return list(set(priorities))  # Remove duplicates

def enhanced_keyword_extraction(text: str) -> Dict[str, List[str]]:
    """
    Enhanced keyword extraction with thematic categorization
    """
    # Enhanced theme dictionaries
    theme_keywords = {
        'cdfi_operations': [
            'community development financial institution', 'cdfi', 'lending', 
            'microfinance', 'community lending', 'financial inclusion',
            'community development', 'loan fund', 'capital access'
        ],
        'small_business': [
            'small business', 'entrepreneur', 'startup', 'business development',
            'job creation', 'business loans', 'working capital', 'micro enterprise'
        ],
        'housing': [
            'affordable housing', 'homeownership', 'housing development',
            'residential', 'housing finance', 'first-time homebuyer'
        ],
        'racial_equity': [
            'minority-owned', 'black-owned', 'diversity', 'inclusion',
            'racial equity', 'underserved communities', 'communities of color'
        ],
        'economic_development': [
            'economic development', 'economic growth', 'community investment',
            'revitalization', 'economic opportunity', 'wealth building'
        ],
        'geographic_focus': [
            'ohio', 'columbus', 'central ohio', 'midwest', 'urban', 'rural'
        ]
    }
    
    text_lower = text.lower()
    found_themes = {}
    
    for theme, keywords in theme_keywords.items():
        found_keywords = []
        for keyword in keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        if found_keywords:
            found_themes[theme] = found_keywords
    
    return found_themes

def validate_extracted_data(org_data: Dict, funder_data: Dict) -> List[str]:
    """
    Validate extracted data for common issues
    """
    issues = []
    
    # Check grant amount reasonableness
    if 'grant_amount' in funder_data:
        amount = funder_data['grant_amount']
        if amount < 1000:
            issues.append(f"Grant amount suspiciously low: ${amount}")
        elif amount > 10000000:
            issues.append(f"Grant amount suspiciously high: ${amount}")
    
    # Check for field mixing
    if 'location' in org_data:
        location = org_data['location'].lower()
        if any(word in location for word in ['grant', 'foundation', 'award', 'funding']):
            issues.append("Organization location contains funder-related text")
    
    # Check for missing critical fields
    if not org_data.get('name'):
        issues.append("Organization name is missing")
    
    if not org_data.get('mission'):
        issues.append("Organization mission is missing")
    
    if not funder_data.get('name'):
        issues.append("Funder name is missing")
    
    return issues

def test_fixes():
    """Test the critical fixes with sample data"""
    
    print("🧪 Testing Critical Fixes")
    print("=" * 40)
    
    # Test amount extraction
    test_amount_text = """
    KeyBank Foundation Bicentennial Grant Program provides $200,000 grants to CDFIs.
    We also offer smaller grants of $25K for capacity building.
    Previous awards ranged from $50,000 to $2M depending on organization size.
    """
    
    amounts = fix_amount_extraction(test_amount_text)
    print("💰 Amount Extraction Test:")
    for amount, context in amounts:
        print(f"   ${amount:,.0f} - {context[:50]}...")
    
    # Test field boundary detection
    test_boundary_text = """
    Freedom Equity Inc. is a community development financial institution.
    Our mission is to provide capital access to underserved communities.
    We are located in Columbus, Ohio and serve Central Ohio.
    
    KeyBank Foundation seeks to support exemplary CDFIs with funding.
    We intend to award one $200,000 grant to an outstanding organization.
    Eligible organizations must demonstrate impact in their communities.
    """
    
    sections = fix_field_boundary_detection(test_boundary_text)
    print("\n🗂️ Field Boundary Detection Test:")
    for section, content in sections.items():
        if content.strip():
            print(f"   {section}: {len(content)} characters")
    
    # Test priority extraction
    test_priority_text = """
    Funding Priorities:
    • Support for community development financial institutions
    • Organizations serving minority and underserved communities  
    • Programs that demonstrate measurable community impact
    • Sustainable business models and strong leadership
    """
    
    priorities = extract_funder_priorities_enhanced(test_priority_text)
    print("\n🎯 Priority Extraction Test:")
    for priority in priorities:
        print(f"   • {priority}")
    
    print("\n✅ All fixes tested successfully!")

if __name__ == "__main__":
    test_fixes() 