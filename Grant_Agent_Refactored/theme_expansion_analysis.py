#!/usr/bin/env python3
"""
Theme Expansion Analysis Tool
Analyzes theme coverage and provides expansion recommendations
"""

import re
from typing import Dict, List, Tuple
from pathlib import Path
from datetime import datetime

def analyze_theme_expansion():
    """Analyze theme expansion opportunities and coverage"""
    
    print("🎨 Theme Expansion Analysis")
    print("=" * 50)
    
    # Read the recent narrative for analysis
    output_dir = Path("../output")
    narrative_files = list(output_dir.glob("comprehensive_grant_narrative_*.txt"))
    
    if not narrative_files:
        print("❌ No narrative files found for analysis")
        return
    
    # Get the most recent narrative
    latest_narrative = max(narrative_files, key=lambda x: x.stat().st_mtime)
    
    with open(latest_narrative, 'r') as f:
        narrative_content = f.read()
    
    # Enhanced theme analysis
    expanded_themes = {
        'cdfi_operations': {
            'keywords': [
                'community development financial institution', 'cdfi', 'lending', 
                'microfinance', 'community lending', 'financial inclusion',
                'community development', 'loan fund', 'capital access', 'cdi',
                'alternative lending', 'community finance', 'community banking',
                'predevelopment lending', 'acquisition lending', 'rehabilitation lending'
            ],
            'coverage': 0,
            'examples': [],
            'expansion_opportunities': [
                'predevelopment lending', 'acquisition lending', 'rehabilitation lending',
                'permanent financing', 'gap financing', 'construction lending'
            ]
        },
        'small_business': {
            'keywords': [
                'small business', 'entrepreneur', 'startup', 'business development',
                'job creation', 'business loans', 'working capital', 'micro enterprise',
                'sba', 'minority business', 'women-owned business', 'business support',
                'minority-owned', 'black-owned business', 'business incubation'
            ],
            'coverage': 0,
            'examples': [],
            'expansion_opportunities': [
                'business incubation', 'mentorship programs', 'business accelerator',
                'franchise opportunities', 'e-commerce development', 'digital transformation'
            ]
        },
        'housing': {
            'keywords': [
                'affordable housing', 'homeownership', 'housing development',
                'residential', 'housing finance', 'first-time homebuyer',
                'mortgage', 'housing trust fund', 'low-income housing',
                'multifamily', 'single-family', 'rental housing'
            ],
            'coverage': 0,
            'examples': [],
            'expansion_opportunities': [
                'multifamily housing', 'single-family development', 'rental housing',
                'housing preservation', 'transit-oriented development', 'green building'
            ]
        },
        'racial_equity': {
            'keywords': [
                'minority-owned', 'black-owned', 'diversity', 'inclusion',
                'racial equity', 'underserved communities', 'communities of color',
                'african american', 'hispanic', 'latino', 'disadvantaged',
                'equity', 'social justice', 'black business owners',
                'systemic barriers', 'historical exclusion'
            ],
            'coverage': 0,
            'examples': [],
            'expansion_opportunities': [
                'systemic barriers', 'historical exclusion', 'wealth gap',
                'generational wealth', 'discrimination', 'cultural competency'
            ]
        },
        'economic_development': {
            'keywords': [
                'economic development', 'economic growth', 'community investment',
                'revitalization', 'economic opportunity', 'wealth building',
                'job creation', 'economic impact', 'community economic',
                'local economy', 'sustainable development', 'community revitalization',
                'neighborhood stabilization', 'commercial development'
            ],
            'coverage': 0,
            'examples': [],
            'expansion_opportunities': [
                'neighborhood stabilization', 'commercial development', 'mixed-use development',
                'transit-oriented development', 'brownfield redevelopment', 'placemaking'
            ]
        },
        'geographic_focus': {
            'keywords': [
                'ohio', 'columbus', 'central ohio', 'midwest', 'urban', 'rural',
                'cleveland', 'cincinnati', 'toledo', 'dayton', 'akron',
                'local', 'community', 'neighborhood', 'keybank markets',
                'regional', 'statewide'
            ],
            'coverage': 0,
            'examples': [],
            'expansion_opportunities': [
                'keybank markets', 'regional focus', 'statewide impact',
                'multi-state operations', 'metropolitan areas', 'suburban communities'
            ]
        },
        'financial_services': {
            'keywords': [
                'banking', 'credit', 'loan', 'capital', 'finance', 'investment',
                'microfinance', 'alternative lending', 'financial literacy',
                'financial education', 'credit building', 'debt counseling',
                'financial planning', 'asset building'
            ],
            'coverage': 0,
            'examples': [],
            'expansion_opportunities': [
                'debt counseling', 'financial planning', 'asset building',
                'retirement planning', 'insurance services', 'investment education'
            ]
        },
        'community_impact': {
            'keywords': [
                'community impact', 'social impact', 'community benefit',
                'measurable outcomes', 'sustainability', 'capacity building',
                'technical assistance', 'community engagement', 'lasting change',
                'community partnership', 'stakeholder engagement', 'collective impact'
            ],
            'coverage': 0,
            'examples': [],
            'expansion_opportunities': [
                'community partnership', 'stakeholder engagement', 'collective impact',
                'social return on investment', 'community resilience', 'civic engagement'
            ]
        }
    }
    
    # Analyze current coverage
    narrative_lower = narrative_content.lower()
    
    total_matches = 0
    total_possible = 0
    
    for theme_name, theme_data in expanded_themes.items():
        matches = 0
        examples = []
        
        for keyword in theme_data['keywords']:
            if keyword.lower() in narrative_lower:
                matches += 1
                # Extract context around the keyword
                pattern = re.compile(f'.{{0,50}}{re.escape(keyword.lower())}.{{0,50}}', re.IGNORECASE)
                context_matches = pattern.findall(narrative_lower)
                if context_matches:
                    examples.extend(context_matches[:2])  # Limit to 2 examples per keyword
        
        coverage_percent = (matches / len(theme_data['keywords'])) * 100
        theme_data['coverage'] = coverage_percent
        theme_data['examples'] = examples[:3]  # Limit to 3 examples per theme
        
        total_matches += matches
        total_possible += len(theme_data['keywords'])
        
        print(f"\n📋 {theme_name.upper().replace('_', ' ')}")
        print(f"   Coverage: {coverage_percent:.1f}% ({matches}/{len(theme_data['keywords'])} keywords)")
        
        if examples:
            print(f"   Examples found:")
            for example in examples[:2]:
                clean_example = ' '.join(example.split())
                print(f"   • \"{clean_example[:80]}...\"")
        
        if theme_data['expansion_opportunities']:
            print(f"   🚀 Expansion opportunities: {', '.join(theme_data['expansion_opportunities'][:3])}")
    
    # Overall analysis
    overall_coverage = (total_matches / total_possible) * 100
    print(f"\n📊 OVERALL THEME COVERAGE")
    print(f"   Total Coverage: {overall_coverage:.1f}% ({total_matches}/{total_possible} keywords)")
    
    # Recommendations for theme expansion
    print(f"\n🎯 THEME EXPANSION RECOMMENDATIONS")
    
    # Identify themes with low coverage
    low_coverage_themes = [(name, data) for name, data in expanded_themes.items() if data['coverage'] < 50]
    
    if low_coverage_themes:
        print(f"\n⚠️  Low Coverage Themes (< 50%):")
        for theme_name, theme_data in low_coverage_themes:
            print(f"   • {theme_name.replace('_', ' ').title()}: {theme_data['coverage']:.1f}%")
            print(f"     Suggested additions: {', '.join(theme_data['expansion_opportunities'][:3])}")
    
    # High-impact expansion opportunities
    print(f"\n🚀 HIGH-IMPACT EXPANSION OPPORTUNITIES")
    
    high_impact_additions = {
        'Partnership & Collaboration': [
            'strategic partnerships', 'community partnerships', 'public-private partnerships',
            'collaborative funding', 'consortium approach', 'collective impact'
        ],
        'Innovation & Technology': [
            'fintech solutions', 'digital banking', 'online lending platform',
            'data analytics', 'artificial intelligence', 'blockchain technology'
        ],
        'Sustainability & Environment': [
            'green financing', 'sustainable development', 'environmental justice',
            'climate resilience', 'renewable energy', 'energy efficiency'
        ],
        'Education & Workforce': [
            'workforce development', 'job training', 'financial literacy',
            'entrepreneurship education', 'skill development', 'career pathways'
        ],
        'Health & Wellness': [
            'community health', 'healthcare access', 'wellness programs',
            'mental health services', 'food security', 'healthy communities'
        ]
    }
    
    for category, keywords in high_impact_additions.items():
        print(f"\n   📈 {category}:")
        print(f"      Keywords: {', '.join(keywords[:4])}")
    
    # Generate expansion report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f"../output/theme_expansion_report_{timestamp}.txt"
    
    with open(report_path, 'w') as f:
        f.write("THEME EXPANSION ANALYSIS REPORT\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"OVERALL COVERAGE: {overall_coverage:.1f}% ({total_matches}/{total_possible} keywords)\n\n")
        
        f.write("THEME-BY-THEME ANALYSIS:\n")
        f.write("-" * 30 + "\n")
        
        for theme_name, theme_data in expanded_themes.items():
            f.write(f"\n{theme_name.upper().replace('_', ' ')}:\n")
            f.write(f"  Coverage: {theme_data['coverage']:.1f}%\n")
            f.write(f"  Current Keywords: {len(theme_data['keywords'])}\n")
            f.write(f"  Expansion Opportunities: {len(theme_data['expansion_opportunities'])}\n")
            f.write(f"  Priority Additions: {', '.join(theme_data['expansion_opportunities'][:3])}\n")
        
        f.write("\n\nHIGH-IMPACT EXPANSION CATEGORIES:\n")
        f.write("-" * 40 + "\n")
        
        for category, keywords in high_impact_additions.items():
            f.write(f"\n{category}:\n")
            f.write(f"  Suggested Keywords: {', '.join(keywords)}\n")
        
        f.write("\n\nRECOMMENDATIONS:\n")
        f.write("-" * 20 + "\n")
        f.write("1. Focus on low-coverage themes for immediate impact\n")
        f.write("2. Add high-impact expansion categories for broader reach\n")
        f.write("3. Implement weighted scoring for theme importance\n")
        f.write("4. Create industry-specific keyword sets\n")
        f.write("5. Develop dynamic theme learning from successful grants\n")
    
    print(f"\n📄 Detailed expansion report saved to: {report_path}")
    
    return expanded_themes

if __name__ == "__main__":
    analyze_theme_expansion() 