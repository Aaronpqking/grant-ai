#!/usr/bin/env python3
"""
Test script to demonstrate different grant type detection and template generation
"""

from multi_template_grant_system import GrantTemplateSystem, GrantType


def test_grant_type_detection():
    """Test the grant type detection with different funder examples"""
    
    system = GrantTemplateSystem()
    
    test_funders = [
        # Federal Agencies
        ("National Science Foundation", GrantType.FEDERAL),
        ("Department of Energy", GrantType.FEDERAL),
        ("National Institutes of Health", GrantType.FEDERAL),
        ("NASA Headquarters", GrantType.FEDERAL),
        
        # State Agencies
        ("California Arts Council", GrantType.STATE),
        ("Ohio Department of Education", GrantType.STATE),
        ("State Environmental Agency", GrantType.STATE),
        ("Commonwealth Development Fund", GrantType.STATE),
        
        # Corporate Funders
        ("Microsoft Corporation", GrantType.CORPORATE),
        ("Walmart Inc.", GrantType.CORPORATE),
        ("Google LLC", GrantType.CORPORATE),
        ("KeyBank Corporation", GrantType.CORPORATE),
        
        # Foundation Funders
        ("Gates Foundation", GrantType.FOUNDATION),
        ("Ford Foundation", GrantType.FOUNDATION),
        ("KeyBank Foundation", GrantType.FOUNDATION),
        ("Robert Wood Johnson Foundation", GrantType.FOUNDATION),
    ]
    
    print("🧪 Grant Type Detection Test")
    print("=" * 60)
    
    correct_detections = 0
    
    for funder_name, expected_type in test_funders:
        detected_type = system.identify_grant_type(funder_name)
        is_correct = detected_type == expected_type
        
        status = "✅" if is_correct else "❌"
        print(f"{status} {funder_name:<35} → {detected_type.value:<10} (expected: {expected_type.value})")
        
        if is_correct:
            correct_detections += 1
    
    accuracy = (correct_detections / len(test_funders)) * 100
    print(f"\n📊 Detection Accuracy: {correct_detections}/{len(test_funders)} ({accuracy:.1f}%)")
    
    return accuracy


def test_template_generation():
    """Test template generation for different grant types"""
    
    system = GrantTemplateSystem()
    
    # Sample organization data
    org_info = {
        "name": "Sample Community Organization",
        "mission": "To provide educational and economic opportunities for underserved communities through innovative programs and partnerships.",
        "location": "City, State",
        "contact": {
            "name": "Jane Director",
            "email": "director@sampleorg.org"
        }
    }
    
    # Test different funder types
    test_cases = [
        {
            "funder": {
                "name": "National Science Foundation",
                "grant_amount": 500000,
                "funding_type": "Research Grant"
            },
            "expected_type": GrantType.FEDERAL
        },
        {
            "funder": {
                "name": "California Arts Council", 
                "grant_amount": 25000,
                "funding_type": "Program Support"
            },
            "expected_type": GrantType.STATE
        },
        {
            "funder": {
                "name": "Microsoft Corporation",
                "grant_amount": 100000,
                "funding_type": "Corporate Partnership"
            },
            "expected_type": GrantType.CORPORATE
        },
        {
            "funder": {
                "name": "Ford Foundation",
                "grant_amount": 75000,
                "funding_type": "General Operating"
            },
            "expected_type": GrantType.FOUNDATION
        }
    ]
    
    print("\n🧪 Template Generation Test")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        funder = test_case["funder"]
        expected_type = test_case["expected_type"]
        
        # Detect grant type
        detected_type = system.identify_grant_type(funder["name"])
        
        # Generate proposal
        result = system.generate_grant_proposal(org_info, funder, detected_type)
        
        print(f"\n📋 Test {i}: {funder['name']}")
        print(f"   Type: {detected_type.value}")
        print(f"   Amount: ${funder['grant_amount']:,.0f}")
        print(f"   Content Length: {result['character_count']} characters")
        print(f"   Estimated Pages: {result['estimated_pages']}")
        print(f"   Status: {result['status']}")
        
        # Check key sections for each type
        content = result["content"]
        
        if detected_type == GrantType.FEDERAL:
            has_sections = all(section in content for section in [
                "Intellectual Merit", "Broader Impacts", "BUDGET JUSTIFICATION"
            ])
        elif detected_type == GrantType.STATE:
            has_sections = all(section in content for section in [
                "NEEDS ASSESSMENT", "LOCAL IMPACT", "COMMUNITY PARTNERSHIPS"
            ])
        elif detected_type == GrantType.CORPORATE:
            has_sections = all(section in content for section in [
                "BUSINESS CASE", "ROI ANALYSIS", "EMPLOYEE ENGAGEMENT"
            ])
        else:  # FOUNDATION
            has_sections = all(section in content for section in [
                "ORGANIZATION PROFILE", "NEEDS STATEMENT", "SUSTAINABILITY"
            ])
        
        section_check = "✅" if has_sections else "❌"
        print(f"   Required Sections: {section_check}")


def demonstrate_template_differences():
    """Demonstrate the key differences between templates"""
    
    system = GrantTemplateSystem()
    specs = system.get_template_specifications()
    
    print("\n📊 Template Specifications Comparison")
    print("=" * 80)
    
    print(f"{'Grant Type':<12} {'Pages':<8} {'Sections':<10} {'Key Focus':<20} {'Formatting'}")
    print("-" * 80)
    
    template_focus = {
        "federal": "Research Impact",
        "state": "Local Community",
        "foundation": "Mission Alignment", 
        "corporate": "Business Value"
    }
    
    for grant_type, spec in specs.items():
        pages = f"{spec['page_limits']['min']}-{spec['page_limits']['max']}"
        sections = len(spec['required_sections'])
        focus = template_focus.get(grant_type, "General")
        font = spec['formatting']['font'][:15] + "..." if len(spec['formatting']['font']) > 15 else spec['formatting']['font']
        
        print(f"{grant_type.title():<12} {pages:<8} {sections:<10} {focus:<20} {font}")
    
    print("\n🎯 Key Template Differences:")
    print("• Federal: Emphasizes intellectual merit, broader impacts, and research methodology")
    print("• State: Focuses on local community benefit, state priority alignment, and partnerships")  
    print("• Corporate: Highlights business value, ROI, employee engagement, and brand alignment")
    print("• Foundation: Emphasizes mission alignment, organizational capacity, and sustainability")


if __name__ == "__main__":
    print("🚀 Multi-Template Grant System Demonstration")
    print("=" * 70)
    
    # Test 1: Grant type detection
    accuracy = test_grant_type_detection()
    
    # Test 2: Template generation
    test_template_generation()
    
    # Test 3: Template differences
    demonstrate_template_differences()
    
    print(f"\n✅ Demonstration Complete - Detection Accuracy: {accuracy:.1f}%") 