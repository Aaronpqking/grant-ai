#!/usr/bin/env python3
"""
Google Drive RAG Service for Grant Writing System
Provides direct access to funder information through Google Drive documents
"""

import os
import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Environment variables
from dotenv import load_dotenv

# Google Drive API
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Text processing
import tiktoken

# Vertex AI for text generation
import vertexai
from vertexai.generative_models import GenerativeModel

# Load environment variables from Grant_Agent_Vertex_Native/.env
load_dotenv('Grant_Agent_Vertex_Native/.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """Metadata for documents in the RAG system"""
    file_id: str
    name: str
    document_type: str  # 'esg_report', 'annual_report', 'founder_info', 'grant_guidelines'
    funder_name: str
    last_modified: datetime
    size: int
    mime_type: str
    drive_link: str


@dataclass
class GoogleDriveConfig:
    """Configuration for Google Drive RAG service"""
    service_account_path: str = None
    scopes: List[str] = None
    folder_id: str = None
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    
    def __post_init__(self):
        # Load service account path from environment variables
        # First try GOOGLE_APPLICATION_CREDENTIALS, then try the service account file
        self.service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or \
                                   'Grant_Agent_Vertex_Native/eleanor-for-enterprise-64bd78746cab.json'
        
        # Load folder ID from environment variables
        self.folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        
        if self.scopes is None:
            self.scopes = [
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/drive.file'
            ]


class DocumentClassifier:
    """Classifies documents based on content and filename"""
    
    def __init__(self):
        self.document_patterns = {
            'esg_report': {
                'filename_keywords': ['esg', 'sustainability', 'environmental', 'social', 'governance'],
                'content_keywords': ['environmental impact', 'sustainability report', 'carbon footprint', 'social responsibility']
            },
            'annual_report': {
                'filename_keywords': ['annual', 'yearly', 'report', 'financial'],
                'content_keywords': ['annual report', 'financial statements', 'year in review', 'shareholders']
            },
            'founder_info': {
                'filename_keywords': ['founder', 'ceo', 'leadership', 'biography', 'profile'],
                'content_keywords': ['founder', 'chief executive', 'leadership team', 'company history']
            },
            'grant_guidelines': {
                'filename_keywords': ['grant', 'funding', 'application', 'guidelines', 'criteria'],
                'content_keywords': ['grant application', 'funding criteria', 'eligibility', 'application process']
            }
        }
    
    def classify_document(self, filename: str, content: str) -> Tuple[str, str]:
        """Classify document type and extract funder name"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Score each document type
        scores = {}
        for doc_type, patterns in self.document_patterns.items():
            score = 0
            
            # Check filename keywords
            for keyword in patterns['filename_keywords']:
                if keyword in filename_lower:
                    score += 2
            
            # Check content keywords
            for keyword in patterns['content_keywords']:
                if keyword in content_lower:
                    score += 1
            
            scores[doc_type] = score
        
        # Get the highest scoring type
        best_type = max(scores, key=scores.get) if max(scores.values()) > 0 else 'unknown'
        
        # Extract funder name from filename
        funder_name = self._extract_funder_name(filename)
        
        return best_type, funder_name
    
    def _extract_funder_name(self, filename: str) -> str:
        """Extract funder name from filename"""
        # Simple extraction - can be enhanced
        name_parts = filename.replace('.', ' ').replace('_', ' ').split()
        
        # Look for common organization indicators
        org_indicators = ['foundation', 'fund', 'trust', 'corporation', 'inc', 'org', 'institute']
        
        for i, part in enumerate(name_parts):
            if part.lower() in org_indicators:
                if i > 0:
                    return ' '.join(name_parts[:i+1])
        
        # Fallback: use first few words
        return ' '.join(name_parts[:3]) if len(name_parts) >= 3 else filename


class DirectGoogleDriveService:
    """Direct Google Drive access with smart caching"""
    
    def __init__(self, drive_service):
        self.drive_service = drive_service
        self.cache = {}  # Simple in-memory cache
        
        # Initialize Vertex AI for text analysis
        vertexai.init(
            project=os.getenv('GOOGLE_CLOUD_PROJECT', 'eleanor-for-enterprise'),
            location=os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        )
        self.model = GenerativeModel('gemini-1.5-flash')
    
    async def search_documents(self, query: str, funder_name: str = None, 
                             document_type: str = None, n_results: int = 5) -> List[Dict]:
        """Search Google Drive directly with smart caching"""
        
        # Build cache key
        cache_key = f"{query}:{funder_name}:{document_type}"
        
        # Check cache first (1 hour TTL)
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 3600:  # 1 hour
                logger.info(f"Using cached search results for: {query}")
                return cached_result
        
        logger.info(f"Searching Google Drive for: {query}")
        
        # Build Google Drive search query
        search_query = f"fullText contains '{query}'"
        
        # Add funder name filter if specified
        if funder_name:
            search_query += f" and name contains '{funder_name}'"
        
        # Add document type filter if specified
        if document_type:
            doc_type_keywords = {
                'esg_report': 'ESG OR sustainability OR environmental',
                'annual_report': 'annual report OR yearly report',
                'founder_info': 'founder OR CEO OR leadership',
                'grant_guidelines': 'grant OR funding OR application'
            }
            if document_type in doc_type_keywords:
                search_query += f" and name contains '{doc_type_keywords[document_type]}'"
        
        try:
            # Search Google Drive
            results = self.drive_service.files().list(
                q=search_query,
                fields='files(id,name,mimeType,modifiedTime,webViewLink,size)',
                orderBy='relevance desc',
                pageSize=min(n_results * 2, 50)  # Get more results to filter
            ).execute()
            
            files = results.get('files', [])
            
            # Process and extract relevant sections
            relevant_results = []
            for file_info in files[:n_results]:
                try:
                    # Get file content
                    content = await self._get_file_content(file_info['id'], file_info['mimeType'])
                    if not content:
                        continue
                    
                    # Extract relevant sections
                    relevant_sections = await self._extract_relevant_sections(content, query)
                    
                    for section in relevant_sections:
                        relevant_results.append({
                            "content": section,
                            "metadata": {
                                "file_id": file_info['id'],
                                "name": file_info['name'],
                                "document_type": self._classify_document_type(file_info['name']),
                                "funder_name": funder_name or self._extract_funder_name(file_info['name']),
                                "last_modified": file_info['modifiedTime'],
                                "drive_link": file_info['webViewLink']
                            },
                            "relevance_score": self._calculate_relevance(section, query)
                        })
                        
                except Exception as e:
                    logger.warning(f"Error processing file {file_info['name']}: {e}")
                    continue
            
            # Sort by relevance and limit results
            relevant_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            final_results = relevant_results[:n_results]
            
            # Cache results
            self.cache[cache_key] = (final_results, datetime.now())
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error searching Google Drive: {e}")
            return []
    
    async def _get_file_content(self, file_id: str, mime_type: str) -> str:
        """Get file content from Google Drive"""
        try:
            if mime_type == 'application/vnd.google-apps.document':
                # Google Docs
                content = self.drive_service.files().export(
                    fileId=file_id, mimeType='text/plain'
                ).execute()
                return content.decode('utf-8')
            elif mime_type == 'text/plain':
                # Plain text
                content = self.drive_service.files().get_media(fileId=file_id).execute()
                return content.decode('utf-8')
            elif mime_type == 'application/pdf':
                # PDF files - would need PDF processing
                logger.warning(f"PDF processing not implemented for file {file_id}")
                return ""
            else:
                logger.warning(f"Unsupported file type: {mime_type}")
                return ""
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            return ""
    
    async def _extract_relevant_sections(self, content: str, query: str) -> List[str]:
        """Extract relevant sections from document content"""
        try:
            # Use AI to extract relevant sections
            prompt = f"""
            From the following document content, extract the most relevant sections that answer or relate to this query: "{query}"
            
            Return only the relevant text sections, each on a separate line. Maximum 3 sections, each under 500 characters.
            
            Document content:
            {content[:3000]}
            """
            
            response = await self.model.generate_content_async(prompt)
            sections = response.text.strip().split('\n')
            
            # Filter and clean sections
            relevant_sections = []
            for section in sections:
                section = section.strip()
                if section and len(section) > 50:  # Minimum length
                    relevant_sections.append(section)
            
            return relevant_sections[:3]  # Maximum 3 sections
            
        except Exception as e:
            logger.error(f"Error extracting relevant sections: {e}")
            # Fallback: keyword-based extraction
            return self._keyword_extract_sections(content, query)
    
    def _keyword_extract_sections(self, content: str, query: str) -> List[str]:
        """Fallback keyword-based section extraction"""
        query_words = query.lower().split()
        sentences = content.split('.')
        
        relevant_sections = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50:  # Minimum length
                sentence_lower = sentence.lower()
                if any(word in sentence_lower for word in query_words):
                    relevant_sections.append(sentence)
                    if len(relevant_sections) >= 3:
                        break
        
        return relevant_sections
    
    def _classify_document_type(self, filename: str) -> str:
        """Classify document type from filename"""
        filename_lower = filename.lower()
        
        if any(keyword in filename_lower for keyword in ['esg', 'sustainability', 'environmental']):
            return 'esg_report'
        elif any(keyword in filename_lower for keyword in ['annual', 'yearly', 'report']):
            return 'annual_report'  
        elif any(keyword in filename_lower for keyword in ['founder', 'ceo', 'leadership']):
            return 'founder_info'
        elif any(keyword in filename_lower for keyword in ['grant', 'funding', 'application']):
            return 'grant_guidelines'
        else:
            return 'unknown'
    
    def _extract_funder_name(self, filename: str) -> str:
        """Extract funder name from filename"""
        # Simple extraction - can be enhanced
        name_parts = filename.replace('.', ' ').split()
        for part in name_parts:
            if part.lower() in ['foundation', 'fund', 'trust', 'corporation', 'inc']:
                return ' '.join(name_parts[:name_parts.index(part) + 1])
        return "Unknown Funder"
    
    def _calculate_relevance(self, content: str, query: str) -> float:
        """Calculate relevance score between content and query"""
        content_lower = content.lower()
        query_words = query.lower().split()
        
        score = 0
        for word in query_words:
            if word in content_lower:
                score += 1
        
        return score / len(query_words) if query_words else 0


class GoogleDriveRAGService:
    """Main RAG service for Google Drive document processing"""
    
    def __init__(self):
        self.config = GoogleDriveConfig()
        self.classifier = DocumentClassifier()
        self.drive_service = None
        self.direct_service = None
        
        # Text processing
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    async def initialize(self):
        """Initialize Google Drive service"""
        try:
            if os.path.exists(self.config.service_account_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.config.service_account_path,
                    scopes=self.config.scopes
                )
                self.drive_service = build('drive', 'v3', credentials=credentials)
                
                # Initialize direct service with the Google Drive API
                self.direct_service = DirectGoogleDriveService(self.drive_service)
                
                logger.info("Google Drive service initialized successfully")
            else:
                logger.error(f"Service account file not found: {self.config.service_account_path}")
                raise FileNotFoundError("Google Drive service account not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            raise
    
    async def scan_and_process_documents(self, folder_id: str = None):
        """Scan and process documents from Google Drive"""
        try:
            # Get all files in the specified folder or root
            query = f"parents in '{folder_id}'" if folder_id else "mimeType != 'application/vnd.google-apps.folder'"
            
            results = self.drive_service.files().list(
                q=query,
                fields='files(id,name,mimeType,modifiedTime,size,webViewLink)',
                pageSize=100
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} files to process")
            
            # Process each file
            for file_info in files:
                await self._process_file(file_info)
                
        except Exception as e:
            logger.error(f"Error scanning documents: {e}")
            raise
    
    async def _process_file(self, file_info: Dict):
        """Process a single file from Google Drive"""
        # Check if file is too large
        file_size = int(file_info.get('size', 0))
        if file_size > self.config.max_file_size:
            logger.warning(f"Skipping large file: {file_info['name']} ({file_size} bytes)")
            return
        
        # Only process text-based files
        mime_type = file_info.get('mimeType', '')
        if not self._is_text_file(mime_type):
            logger.debug(f"Skipping non-text file: {file_info['name']}")
            return
        
        try:
            # Download file content
            content = await self._download_file_content(file_info['id'], mime_type)
            if not content:
                return
            
            # Classify document
            doc_type, funder_name = self.classifier.classify_document(
                file_info['name'], content
            )
            
            logger.info(f"Processed {file_info['name']} - {doc_type} from {funder_name}")
            
        except Exception as e:
            logger.error(f"Error processing file {file_info['name']}: {e}")
            raise
    
    def _is_text_file(self, mime_type: str) -> bool:
        """Check if file is text-based"""
        text_types = [
            'text/plain',
            'application/vnd.google-apps.document',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        return mime_type in text_types
    
    async def _download_file_content(self, file_id: str, mime_type: str) -> str:
        """Download file content from Google Drive"""
        try:
            if mime_type == 'application/vnd.google-apps.document':
                # Google Docs
                content = self.drive_service.files().export(
                    fileId=file_id, mimeType='text/plain'
                ).execute()
                return content.decode('utf-8')
            elif mime_type == 'text/plain':
                # Plain text
                content = self.drive_service.files().get_media(fileId=file_id).execute()
                return content.decode('utf-8')
            else:
                logger.warning(f"Unsupported file type for download: {mime_type}")
                return ""
        except Exception as e:
            logger.error(f"Error downloading file content: {e}")
            return ""
    
    async def search_funder_information(self, funder_name: str, query: str, 
                                      document_types: List[str] = None) -> Dict[str, Any]:
        """Search for funder information using direct Google Drive access"""
        if not document_types:
            document_types = ['esg_report', 'annual_report', 'founder_info', 'grant_guidelines']
        
        results = {
            'funder_name': funder_name,
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'information': {}
        }
        
        for doc_type in document_types:
            search_results = await self.direct_service.search_documents(
                query=query,
                funder_name=funder_name,
                document_type=doc_type,
                n_results=3
            )
            
            if search_results:
                results['information'][doc_type] = {
                    'found': True,
                    'documents': search_results,
                    'summary': self._summarize_search_results(search_results)
                }
            else:
                results['information'][doc_type] = {
                    'found': False,
                    'documents': [],
                    'summary': f"No {doc_type.replace('_', ' ')} found for {funder_name}"
                }
        
        return results
    
    def _summarize_search_results(self, search_results: List[Dict]) -> str:
        """Create summary of search results"""
        if not search_results:
            return "No relevant information found."
        
        # Extract key information from top results
        top_content = []
        for result in search_results[:2]:  # Top 2 results
            content = result['content'][:300]  # First 300 chars
            top_content.append(content)
        
        return " ".join(top_content)
    
    async def get_funder_profile(self, funder_name: str) -> Dict[str, Any]:
        """Get comprehensive funder profile"""
        profile = {
            'funder_name': funder_name,
            'timestamp': datetime.now().isoformat(),
            'funding_priorities': await self.search_funder_information(
                funder_name, 'funding priorities grant criteria', ['grant_guidelines']
            ),
            'esg_focus': await self.search_funder_information(
                funder_name, 'ESG environmental social governance sustainability', ['esg_report']
            ),
            'leadership_info': await self.search_funder_information(
                funder_name, 'leadership team founder CEO board', ['founder_info']
            ),
            'recent_grants': await self.search_funder_information(
                funder_name, 'recent grants funded projects awards', ['annual_report']
            ),
            'application_process': await self.search_funder_information(
                funder_name, 'application process requirements deadline', ['grant_guidelines']
            )
        }
        
        return profile


async def initialize_rag_service() -> GoogleDriveRAGService:
    """Initialize and return RAG service"""
    rag_service = GoogleDriveRAGService()
    await rag_service.initialize()
    return rag_service


if __name__ == "__main__":
    # Test the RAG service
    async def test_rag_service():
        try:
            rag_service = await initialize_rag_service()
            
            # Test funder search
            results = await rag_service.search_funder_information(
                "Ford Foundation", 
                "environmental sustainability grants"
            )
            
            print("RAG Service Test Results:")
            print(json.dumps(results, indent=2))
            
        except Exception as e:
            print(f"Test failed: {e}")
    
    asyncio.run(test_rag_service()) 