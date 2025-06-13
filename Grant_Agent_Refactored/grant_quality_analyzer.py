#!/usr/bin/env python3
"""
Grant Quality Analyzer - Identifies issues and verifies language/narrative alignment
"""

import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

from refactored.models import GrantWorkflowData, OrganizationInfo, FunderInfo, LanguageAnalysis
from refactored.services import DocumentService, ExtractionService, LanguageAnalysisService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class QualityIssue:
    category: str
    severity: str  # 'critical', 'major', 'minor'
    description: str
    suggested_fix: str
    affected_field: str = ""

@dataclass
class AlignmentVerification:
    alignment_score: float
    keyword_matches: List[str]
    theme_overlap: List[str]
    missing_connections: List[str]
    narrative_consistency: float
    recommendations: List[str]

class GrantQualityAnalyzer:
    """Analyze grant output quality and verify alignment"""
    
    def __init__(self):
        self.issues: List[QualityIssue] = []
        self.verification_results: Dict[str, Any] = {}
    
    def analyze_workflow_data(self, workflow_data: GrantWorkflowData) -> Dict[str, Any]:
        """Comprehensive analysis of workflow data quality"""
        
        print("🔍 Analyzing Grant Building Quality...")
        print("=" * 50)
        
        # Reset issues
        self.issues = []
        
        # 1. Analyze extraction quality
        self._analyze_extraction_quality(workflow_data)
        
        # 2. Analyze language alignment
        self._analyze_language_alignment(workflow_data)
        
        # 3. Analyze narrative quality
        self._analyze_narrative_quality(workflow_data)
        
        # 4. Check data consistency
        self._check_data_consistency(workflow_data)
        
        # 5. Generate improvement recommendations
        recommendations = self._generate_recommendations()
        
        # 6. Create verification report
        verification = self._verify_alignment(workflow_data)
        
        return {
            "issues": self.issues,
            "recommendations": recommendations,
            "verification": verification,
            "quality_score": self._calculate_quality_score()
        }
    
    def _analyze_extraction_quality(self, workflow_data: GrantWorkflowData):
        """Analyze quality of extracted data"""
        
        org = workflow_data.organization
        funder = workflow_data.funder
        
        if not org:
            self.issues.append(QualityIssue(
                category="extraction",
                severity="critical",
                description="No organization information extracted",
                suggested_fix="Review organization document patterns and extraction logic",
                affected_field="organization"
            ))
            return
        
        if not funder:
            self.issues.append(QualityIssue(
                category="extraction", 
                severity="critical",
                description="No funder information extracted",
                suggested_fix="Review funder document patterns and extraction logic",
                affected_field="funder"
            ))
            return
        
        # Check organization completeness
        if not org.name:
            self.issues.append(QualityIssue(
                category="extraction",
                severity="major",
                description="Organization name missing",
                suggested_fix="Improve organization name extraction patterns",
                affected_field="organization.name"
            ))
        
        if not org.mission:
            self.issues.append(QualityIssue(
                category="extraction",
                severity="major", 
                description="Organization mission missing",
                suggested_fix="Improve mission statement extraction patterns",
                affected_field="organization.mission"
            ))
        
        # Check if location field contains funder text (data mixing issue)
        if org.location and any(word in org.location.lower() for word in ['grant', 'funder', 'foundation', 'award']):
            self.issues.append(QualityIssue(
                category="extraction",
                severity="major",
                description="Organization location field contains funder information",
                suggested_fix="Fix field assignment logic in extraction patterns",
                affected_field="organization.location"
            ))
        
        # Check funder amount extraction
        if funder.grant_amount < 1000:  # Likely incorrect if less than $1,000
            self.issues.append(QualityIssue(
                category="extraction",
                severity="critical",
                description=f"Grant amount seems too low: ${funder.grant_amount}",
                suggested_fix="Review amount extraction patterns for $200K vs $200 distinction",
                affected_field="funder.grant_amount"
            ))
        
        # Check funder priorities
        if not funder.funding_priorities:
            self.issues.append(QualityIssue(
                category="extraction",
                severity="major",
                description="No funder priorities extracted",
                suggested_fix="Improve funding priorities extraction from funder documents",
                affected_field="funder.funding_priorities"
            ))
    
    def _analyze_language_alignment(self, workflow_data: GrantWorkflowData):
        """Analyze language alignment quality"""
        
        analysis = workflow_data.language_analysis
        
        if not analysis:
            self.issues.append(QualityIssue(
                category="alignment",
                severity="major",
                description="No language analysis performed",
                suggested_fix="Ensure language analysis service is called",
                affected_field="language_analysis"
            ))
            return
        
        # Check for zero alignment
        if analysis.alignment_score == 0.0:
            self.issues.append(QualityIssue(
                category="alignment",
                severity="major",
                description="Language alignment score is 0.0 - indicates poor keyword matching",
                suggested_fix="Improve keyword extraction and theme matching algorithms",
                affected_field="language_analysis.alignment_score"
            ))
        
        # Check for missing themes
        if not analysis.matching_themes:
            self.issues.append(QualityIssue(
                category="alignment",
                severity="major",
                description="No matching themes found between org and funder",
                suggested_fix="Expand theme keyword dictionaries and improve text preprocessing",
                affected_field="language_analysis.matching_themes"
            ))
    
    def _analyze_narrative_quality(self, workflow_data: GrantWorkflowData):
        """Analyze narrative quality"""
        
        narrative = workflow_data.narrative
        
        if not narrative:
            self.issues.append(QualityIssue(
                category="narrative",
                severity="critical",
                description="No narrative generated",
                suggested_fix="Ensure narrative generation service is working",
                affected_field="narrative"
            ))
            return
        
        # Check narrative length
        if len(narrative) < 1000:
            self.issues.append(QualityIssue(
                category="narrative",
                severity="minor",
                description="Narrative is quite short",
                suggested_fix="Expand narrative templates with more detailed sections",
                affected_field="narrative"
            ))
        
        # Check for placeholder text
        placeholders = ['[INSERT', 'TODO', 'TBD', 'PLACEHOLDER']
        for placeholder in placeholders:
            if placeholder in narrative.upper():
                self.issues.append(QualityIssue(
                    category="narrative",
                    severity="major",
                    description=f"Narrative contains placeholder text: {placeholder}",
                    suggested_fix="Replace all placeholders with actual content",
                    affected_field="narrative"
                ))
    
    def _check_data_consistency(self, workflow_data: GrantWorkflowData):
        """Check for data consistency issues"""
        
        org = workflow_data.organization
        funder = workflow_data.funder
        narrative = workflow_data.narrative
        
        if not org or not funder or not narrative:
            return
        
        # Check if org name appears in narrative
        if org.name not in narrative:
            self.issues.append(QualityIssue(
                category="consistency",
                severity="minor",
                description="Organization name not found in narrative",
                suggested_fix="Ensure organization name is prominently featured in narrative",
                affected_field="narrative"
            ))
        
        # Check if funder name appears in narrative
        if funder.name not in narrative:
            self.issues.append(QualityIssue(
                category="consistency",
                severity="minor", 
                description="Funder name not found in narrative",
                suggested_fix="Ensure funder name is mentioned in grant request section",
                affected_field="narrative"
            ))
    
    def _verify_alignment(self, workflow_data: GrantWorkflowData) -> AlignmentVerification:
        """Verify language and narrative alignment independently"""
        
        org = workflow_data.organization
        funder = workflow_data.funder
        narrative = workflow_data.narrative or ""
        
        if not org or not funder:
            return AlignmentVerification(0.0, [], [], [], 0.0, ["Missing organization or funder data"])
        
        # Extract keywords from organization text
        org_text = f"{org.name} {org.mission} {org.background}".lower()
        org_keywords = set(re.findall(r'\b[a-z]{4,}\b', org_text))
        
        # Extract keywords from funder priorities
        funder_text = " ".join(funder.funding_priorities).lower() if funder.funding_priorities else ""
        funder_keywords = set(re.findall(r'\b[a-z]{4,}\b', funder_text))
        
        # Find keyword matches
        keyword_matches = list(org_keywords.intersection(funder_keywords))
        
        # Define thematic areas
        themes = {
            'housing': ['housing', 'residential', 'homeownership', 'affordable'],
            'business': ['business', 'entrepreneur', 'enterprise', 'economic'],
            'community': ['community', 'local', 'neighborhood', 'development'],
            'financial': ['financial', 'lending', 'capital', 'credit'],
            'equity': ['equity', 'inclusion', 'diversity', 'racial']
        }
        
        # Find theme overlaps
        theme_overlap = []
        for theme, keywords in themes.items():
            org_has_theme = any(kw in org_text for kw in keywords)
            funder_has_theme = any(kw in funder_text for kw in keywords) 
            if org_has_theme and funder_has_theme:
                theme_overlap.append(theme)
        
        # Calculate alignment score
        alignment_score = len(theme_overlap) / len(themes) if themes else 0.0
        
        # Check narrative consistency
        narrative_lower = narrative.lower()
        narrative_mentions_org = len(re.findall(org.name.lower(), narrative_lower))
        narrative_mentions_funder = len(re.findall(funder.name.lower(), narrative_lower))
        narrative_consistency = min(1.0, (narrative_mentions_org + narrative_mentions_funder) / 10)
        
        # Find missing connections
        missing_connections = []
        if alignment_score < 0.3:
            missing_connections.append("Low thematic alignment between organization and funder")
        if not keyword_matches:
            missing_connections.append("No keyword overlap found")
        if narrative_consistency < 0.5:
            missing_connections.append("Limited mention of key entities in narrative")
        
        # Generate recommendations
        recommendations = []
        if alignment_score < 0.5:
            recommendations.append("Strengthen connection between organization mission and funder priorities")
        if len(keyword_matches) < 3:
            recommendations.append("Use more specific keywords that align with funder language")
        if narrative_consistency < 0.7:
            recommendations.append("Increase references to organization and funder in narrative")
        
        return AlignmentVerification(
            alignment_score=alignment_score,
            keyword_matches=keyword_matches[:10],  # Limit for readability
            theme_overlap=theme_overlap,
            missing_connections=missing_connections,
            narrative_consistency=narrative_consistency,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self) -> List[str]:
        """Generate prioritized recommendations"""
        
        recommendations = []
        
        # Group issues by category
        critical_issues = [i for i in self.issues if i.severity == 'critical']
        major_issues = [i for i in self.issues if i.severity == 'major']
        
        if critical_issues:
            recommendations.append("🚨 CRITICAL: Address data extraction failures first")
            for issue in critical_issues[:3]:  # Top 3 critical
                recommendations.append(f"   • {issue.description}")
        
        if major_issues:
            recommendations.append("⚠️ MAJOR: Improve data quality and alignment")
            for issue in major_issues[:3]:  # Top 3 major
                recommendations.append(f"   • {issue.description}")
        
        # Add general recommendations
        recommendations.extend([
            "💡 ENHANCEMENT: Expand keyword dictionaries for better theme matching",
            "💡 ENHANCEMENT: Add validation rules for extracted amounts",
            "💡 ENHANCEMENT: Implement cross-field consistency checks"
        ])
        
        return recommendations
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score (0-100)"""
        
        if not self.issues:
            return 100.0
        
        # Weight by severity
        penalty = 0
        for issue in self.issues:
            if issue.severity == 'critical':
                penalty += 30
            elif issue.severity == 'major':
                penalty += 15
            elif issue.severity == 'minor':
                penalty += 5
        
        return max(0.0, 100.0 - penalty)
    
    def generate_verification_report(self, workflow_data: GrantWorkflowData, output_path: str = None):
        """Generate detailed verification report"""
        
        analysis_results = self.analyze_workflow_data(workflow_data)
        
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"../output/grant_quality_report_{timestamp}.txt"
        
        with open(output_path, 'w') as f:
            f.write("GRANT QUALITY ANALYSIS AND VERIFICATION REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Quality Score
            score = analysis_results['quality_score']
            f.write(f"OVERALL QUALITY SCORE: {score:.1f}/100\n")
            f.write("=" * 40 + "\n\n")
            
            # Issues Summary
            issues = analysis_results['issues']
            f.write(f"ISSUES IDENTIFIED: {len(issues)}\n")
            f.write("-" * 30 + "\n")
            
            for category in ['critical', 'major', 'minor']:
                cat_issues = [i for i in issues if i.severity == category]
                f.write(f"{category.upper()}: {len(cat_issues)}\n")
                for issue in cat_issues:
                    f.write(f"  • {issue.description}\n")
                    f.write(f"    Fix: {issue.suggested_fix}\n")
                f.write("\n")
            
            # Alignment Verification
            verification = analysis_results['verification']
            f.write("LANGUAGE/NARRATIVE ALIGNMENT VERIFICATION\n")
            f.write("=" * 45 + "\n")
            f.write(f"Alignment Score: {verification.alignment_score:.2f}\n")
            f.write(f"Narrative Consistency: {verification.narrative_consistency:.2f}\n")
            f.write(f"Keyword Matches: {', '.join(verification.keyword_matches[:5])}\n")
            f.write(f"Theme Overlap: {', '.join(verification.theme_overlap)}\n\n")
            
            if verification.missing_connections:
                f.write("Missing Connections:\n")
                for missing in verification.missing_connections:
                    f.write(f"  • {missing}\n")
                f.write("\n")
            
            # Recommendations
            recommendations = analysis_results['recommendations']
            f.write("IMPROVEMENT RECOMMENDATIONS\n")
            f.write("=" * 30 + "\n")
            for rec in recommendations:
                f.write(f"{rec}\n")
            f.write("\n")
            
            # Verification Recommendations
            f.write("ALIGNMENT RECOMMENDATIONS\n")
            f.write("=" * 25 + "\n")
            for rec in verification.recommendations:
                f.write(f"• {rec}\n")
        
        print(f"📄 Quality report saved to: {output_path}")
        return output_path


def main():
    """Run quality analysis on the latest grant building output"""
    
    # Load the latest workflow data by recreating it
    from refactored.services import DocumentService, ExtractionService, LanguageAnalysisService
    
    doc_service = DocumentService()
    extraction_service = ExtractionService()
    analysis_service = LanguageAnalysisService()
    
    # Recreate workflow data
    workflow_data = GrantWorkflowData()
    input_dir = Path('../input')
    
    # Process the same documents
    documents_to_process = [
        ('doc_6.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        ('doc_2.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        ('doc_3.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
    ]
    
    for filename, mime_type in documents_to_process:
        file_path = input_dir / filename
        if file_path.exists():
            with open(file_path, 'rb') as f:
                file_data = f.read()
            doc_data = doc_service.process_upload(file_data, filename, mime_type)
            workflow_data.add_document(doc_data)
    
    # Extract data
    extraction_result = extraction_service.extract_all(workflow_data)
    if extraction_result.organization:
        workflow_data.organization = extraction_result.organization
    if extraction_result.funder:
        workflow_data.funder = extraction_result.funder
    
    # Analyze language
    if workflow_data.organization and workflow_data.funder:
        analysis_result = analysis_service.analyze_alignment(
            workflow_data.organization, workflow_data.funder
        )
        workflow_data.language_analysis = analysis_result
    
    # Load narrative from file if exists
    narrative_files = list(Path('../output').glob('grant_narrative_input_*.txt'))
    if narrative_files:
        latest_narrative = max(narrative_files, key=lambda x: x.stat().st_mtime)
        with open(latest_narrative, 'r') as f:
            workflow_data.narrative = f.read()
    
    # Run quality analysis
    analyzer = GrantQualityAnalyzer()
    report_path = analyzer.generate_verification_report(workflow_data)
    
    print(f"\n🎯 Quality analysis complete! Check the report at: {report_path}")


if __name__ == "__main__":
    main() 