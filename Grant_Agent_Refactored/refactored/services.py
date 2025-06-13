"""
Refactored Grant Agent - Service Layer
Unified document handling and extraction services
"""

import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import (
    DocumentData, DocumentType, OrganizationInfo, FunderInfo, 
    ContactInfo, FinancialInfo, ExtractionResult, 
    ExtractionError, GrantWorkflowData
)

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Classify documents based on content analysis"""
    
    ORG_PATTERNS = [
        r'organization.*name',
        r'mission.*statement',
        r'annual.*budget',
        r'background.*summary',
        r'executive.*director',
        r'board.*directors'
    ]
    
    FUNDER_PATTERNS = [
        r'grant.*program',
        r'funding.*priorities',
        r'eligibility.*criteria',
        r'request.*limit',
        r'foundation',
        r'bicentennial.*grant'
    ]
    
    def classify_document(self, content: str) -> DocumentType:
        """Classify document based on content patterns"""
        content_lower = content.lower()
        
        org_score = sum(1 for pattern in self.ORG_PATTERNS if re.search(pattern, content_lower))
        funder_score = sum(1 for pattern in self.FUNDER_PATTERNS if re.search(pattern, content_lower))
        
        if org_score > funder_score and org_score >= 2:
            return DocumentType.ORGANIZATION
        elif funder_score > org_score and funder_score >= 2:
            return DocumentType.FUNDER
        elif 'financial' in content_lower or 'budget' in content_lower:
            return DocumentType.FINANCIAL_DETAIL
        elif 'partnership' in content_lower or 'collaboration' in content_lower:
            return DocumentType.PARTNERSHIP_INFO
        else:
            return DocumentType.UNKNOWN


class TextExtractor:
    """Extract text from different document types"""
    
    def extract_from_docx(self, file_data: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            from .extractors import extract_text_from_docx
            return extract_text_from_docx(file_data)
        except Exception as e:
            logger.error(f"Error extracting DOCX: {e}")
            return ""
    
    def extract_from_pdf(self, file_data: bytes) -> str:
        """Extract text from PDF file"""
        try:
            from .extractors import extract_text_from_pdf
            return extract_text_from_pdf(file_data)
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            return ""
    
    def extract_text(self, file_data: bytes, mime_type: str) -> str:
        """Extract text based on MIME type"""
        if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return self.extract_from_docx(file_data)
        elif mime_type == 'application/pdf':
            return self.extract_from_pdf(file_data)
        else:
            # Try to decode as plain text
            try:
                return file_data.decode('utf-8')
            except:
                return f"[Binary content - {mime_type}]"


class DocumentService:
    """Unified document handling service"""
    
    def __init__(self, artifact_service=None):
        self.artifact_service = artifact_service
        self.text_extractor = TextExtractor()
        self.classifier = DocumentClassifier()
        
    def process_upload(self, file_data: bytes, filename: str, mime_type: str) -> DocumentData:
        """Single method handles all document processing"""
        # Extract text content
        content = self.text_extractor.extract_text(file_data, mime_type)
        
        # Create document data with hash
        doc_data = DocumentData.create(content, filename, mime_type, file_data)
        
        # Classify document type
        doc_data.document_type = self.classifier.classify_document(content)
        
        # Store in artifact service if available
        if self.artifact_service:
            try:
                artifact_id = f"document_{doc_data.content_hash}"
                self.artifact_service.store(artifact_id, file_data, mime_type)
                logger.info(f"Stored document {artifact_id} in artifact service")
            except Exception as e:
                logger.warning(f"Failed to store in artifact service: {e}")
        
        logger.info(f"Processed document: {filename} -> {doc_data.document_type.value}")
        return doc_data


class OrganizationExtractor:
    """Extract organization information from text"""
    
    def extract(self, content: str) -> OrganizationInfo:
        """Extract organization info from document content"""
        try:
            org_info = OrganizationInfo()
            
            # Extract organization name
            name_match = re.search(r'organization.*name[:\s]+([^\n]+)', content, re.IGNORECASE)
            if name_match:
                org_info.name = name_match.group(1).strip()
            
            # Extract mission statement
            mission_patterns = [
                r'mission.*statement[:\s]+([^\n]+)',
                r'mission[:\s]+([^\n]+)',
                r'the.*mission.*is[:\s]+([^\n]+)'
            ]
            for pattern in mission_patterns:
                mission_match = re.search(pattern, content, re.IGNORECASE)
                if mission_match:
                    org_info.mission = mission_match.group(1).strip()
                    break
            
            # Extract background/description
            background_patterns = [
                r'background.*summary[:\s]+([^\n\r]+(?:\n[^\n\r]+)*?)(?:\n\s*\n|\Z)',
                r'organization.*background[:\s]+([^\n\r]+(?:\n[^\n\r]+)*?)(?:\n\s*\n|\Z)',
                r'description[:\s]+([^\n\r]+(?:\n[^\n\r]+)*?)(?:\n\s*\n|\Z)'
            ]
            for pattern in background_patterns:
                background_match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if background_match:
                    org_info.background = background_match.group(1).strip()
                    break
            
            # Extract contact information
            org_info.contact_info = self.extract_contact_info(content)
            
            # Extract financial information
            org_info.financials = self.extract_financial_info(content)
            
            # Extract location
            location_patterns = [
                r'city[:\s]+([^\n]+)',
                r'headquarters[:\s]+([^\n]+)',
                r'located.*in[:\s]+([^\n]+)'
            ]
            for pattern in location_patterns:
                location_match = re.search(pattern, content, re.IGNORECASE)
                if location_match:
                    org_info.location = location_match.group(1).strip()
                    break
            
            logger.info(f"Extracted organization: {org_info.name}")
            return org_info
            
        except Exception as e:
            logger.error(f"Error extracting organization info: {e}")
            raise ExtractionError(f"Failed to extract organization info: {e}")
    
    def extract_contact_info(self, content: str) -> ContactInfo:
        """Extract contact information"""
        contact = ContactInfo()
        
        # Extract name and title
        name_patterns = [
            r'(?:first.*name|name)[:\s]+([^\n]+)',
            r'executive.*director[:\s]+([^\n]+)',
            r'president[:\s]+([^\n]+)'
        ]
        for pattern in name_patterns:
            name_match = re.search(pattern, content, re.IGNORECASE)
            if name_match:
                contact.name = name_match.group(1).strip()
                break
        
        # Extract email
        email_match = re.search(r'email[:\s]+([^\s\n]+@[^\s\n]+)', content, re.IGNORECASE)
        if email_match:
            contact.email = email_match.group(1).strip()
        
        # Extract phone
        phone_match = re.search(r'phone[:\s]+([0-9\-\(\)\s]+)', content, re.IGNORECASE)
        if phone_match:
            contact.phone = phone_match.group(1).strip()
        
        return contact
    
    def extract_financial_info(self, content: str) -> FinancialInfo:
        """Extract financial information"""
        financial = FinancialInfo()
        
        # Extract annual budget
        budget_patterns = [
            r'annual.*budget[:\s]+\$([0-9,\.]+)',
            r'budget[:\s]+\$([0-9,\.]+)',
            r'operating.*budget[:\s]+\$([0-9,\.]+)'
        ]
        for pattern in budget_patterns:
            budget_match = re.search(pattern, content, re.IGNORECASE)
            if budget_match:
                budget_str = budget_match.group(1).replace(',', '')
                try:
                    financial.annual_budget = float(budget_str)
                except ValueError:
                    pass
                break
        
        return financial


class FunderExtractor:
    """Extract funder information from text"""
    
    def extract(self, content: str) -> FunderInfo:
        """Extract funder info from document content"""
        try:
            funder_info = FunderInfo()
            
            # Extract funder name
            name_patterns = [
                r'keybank.*foundation',
                r'keybank.*bicentennial',
                r'keybank',
                r'foundation[:\s]+([^\n]+)'
            ]
            for pattern in name_patterns:
                name_match = re.search(pattern, content, re.IGNORECASE)
                if name_match:
                    if 'keybank' in pattern.lower():
                        funder_info.name = "KeyBank Foundation"
                    else:
                        funder_info.name = name_match.group(1).strip()
                    break
            
            # Extract grant amount
            amount_patterns = [
                r'request.*limit[:\s]+\$([0-9,]+)',
                r'grant.*amount[:\s]+\$([0-9,]+)',
                r'\$([0-9,]+).*grant'
            ]
            for pattern in amount_patterns:
                amount_match = re.search(pattern, content, re.IGNORECASE)
                if amount_match:
                    amount_str = amount_match.group(1).replace(',', '')
                    try:
                        funder_info.grant_amount = int(amount_str)
                    except ValueError:
                        pass
                    break
            
            # Extract funding type
            type_patterns = [
                r'funding.*type[:\s]+([^\n]+)',
                r'grants.*will.*provide[:\s]+([^\n]+)',
                r'unrestricted.*funding'
            ]
            for pattern in type_patterns:
                type_match = re.search(pattern, content, re.IGNORECASE)
                if type_match:
                    if 'unrestricted' in pattern.lower():
                        funder_info.funding_type = "Unrestricted"
                    else:
                        funder_info.funding_type = type_match.group(1).strip()
                    break
            
            # Extract funding priorities
            priorities = self.extract_list_items(content, 'funding priorities', 'priorities')
            funder_info.funding_priorities = priorities
            
            # Extract eligibility criteria
            criteria = self.extract_list_items(content, 'eligibility', 'criteria')
            funder_info.eligibility_criteria = criteria
            
            logger.info(f"Extracted funder: {funder_info.name}, Amount: ${funder_info.grant_amount}")
            return funder_info
            
        except Exception as e:
            logger.error(f"Error extracting funder info: {e}")
            raise ExtractionError(f"Failed to extract funder info: {e}")
    
    def extract_list_items(self, content: str, section_name: str, item_type: str) -> List[str]:
        """Extract list items from a section"""
        items = []
        
        # Find section
        section_pattern = rf'{section_name}[^\n]*(?:\n|$)(.*?)(?:\n\s*\n|\Z)'
        section_match = re.search(section_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if section_match:
            section_content = section_match.group(1)
            
            # Extract bullet points
            bullet_patterns = [
                r'[•\-\*]\s*([^\n]+)',
                r'\n\s*([^•\-\*\n][^\n]*(?:housing|business|development|entrepreneur)[^\n]*)',
                r':\s*([^:\n]+(?:housing|business|development|entrepreneur)[^\n]*)'
            ]
            
            for pattern in bullet_patterns:
                matches = re.findall(pattern, section_content, re.IGNORECASE)
                for match in matches:
                    cleaned = match.strip()
                    if len(cleaned) > 10 and cleaned not in items:  # Avoid duplicates and short matches
                        items.append(cleaned)
        
        return items


class ExtractionService:
    """Centralized extraction service"""
    
    def __init__(self):
        self.org_extractor = OrganizationExtractor()
        self.funder_extractor = FunderExtractor()
        self.classifier = DocumentClassifier()
    
    def extract_all(self, workflow_data: GrantWorkflowData) -> ExtractionResult:
        """Extract from workflow data, not files"""
        result = ExtractionResult()
        result.success = True
        
        try:
            for doc_hash, doc_data in workflow_data.documents.items():
                result.extracted_from.append(doc_data.filename)
                
                if doc_data.document_type == DocumentType.ORGANIZATION:
                    if not result.organization:
                        result.organization = self.org_extractor.extract(doc_data.content)
                        logger.info(f"Extracted organization info from {doc_data.filename}")
                    
                elif doc_data.document_type == DocumentType.FUNDER:
                    if not result.funder:
                        result.funder = self.funder_extractor.extract(doc_data.content)
                        logger.info(f"Extracted funder info from {doc_data.filename}")
                
                # Also try to extract from unknown documents
                elif doc_data.document_type == DocumentType.UNKNOWN:
                    # Try both extractors and see which one succeeds better
                    try:
                        temp_org = self.org_extractor.extract(doc_data.content)
                        if temp_org.is_complete() and not result.organization:
                            result.organization = temp_org
                            doc_data.document_type = DocumentType.ORGANIZATION
                            logger.info(f"Reclassified {doc_data.filename} as organization document")
                    except:
                        pass
                    
                    try:
                        temp_funder = self.funder_extractor.extract(doc_data.content)
                        if temp_funder.is_complete() and not result.funder:
                            result.funder = temp_funder
                            doc_data.document_type = DocumentType.FUNDER
                            logger.info(f"Reclassified {doc_data.filename} as funder document")
                    except:
                        pass
            
            # Check if we got meaningful extractions
            if not result.organization and not result.funder:
                result.success = False
                result.errors.append("No organization or funder information found in documents")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in extraction service: {e}")
            result.success = False
            result.errors.append(f"Extraction failed: {e}")
            return result


class LanguageAnalysisService:
    """Analyze language alignment between organization and funder"""
    
    def analyze_alignment(self, org_info: OrganizationInfo, funder_info: FunderInfo) -> 'LanguageAnalysis':
        """Analyze language alignment"""
        from .models import LanguageAnalysis
        
        analysis = LanguageAnalysis()
        
        try:
            # Simple keyword matching for now
            org_text = f"{org_info.mission} {org_info.background}".lower()
            funder_priorities = " ".join(funder_info.funding_priorities).lower()
            
            # Find matching themes
            common_themes = []
            theme_keywords = {
                'affordable housing': ['housing', 'affordable', 'residential'],
                'small business': ['business', 'entrepreneur', 'enterprise', 'economic'],
                'community development': ['community', 'development', 'local'],
                'financial inclusion': ['financial', 'capital', 'lending', 'credit'],
                'racial equity': ['equity', 'racial', 'diversity', 'inclusion']
            }
            
            for theme, keywords in theme_keywords.items():
                org_matches = sum(1 for kw in keywords if kw in org_text)
                funder_matches = sum(1 for kw in keywords if kw in funder_priorities)
                
                if org_matches > 0 and funder_matches > 0:
                    common_themes.append(theme)
            
            analysis.matching_themes = common_themes
            analysis.alignment_score = len(common_themes) / len(theme_keywords) if theme_keywords else 0.0
            
            # Generate recommendations
            if analysis.alignment_score > 0.6:
                analysis.recommendations.append("Strong alignment between organization mission and funder priorities")
            elif analysis.alignment_score > 0.3:
                analysis.recommendations.append("Moderate alignment - consider emphasizing shared themes")
            else:
                analysis.recommendations.append("Limited alignment - focus on connecting mission to funder priorities")
            
            logger.info(f"Language analysis complete. Alignment score: {analysis.alignment_score:.2f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in language analysis: {e}")
            analysis.recommendations.append(f"Analysis error: {e}")
            return analysis 