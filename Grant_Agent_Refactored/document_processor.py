"""
Document Processing Utility for Grant Agent
Extracts text from DOCX, PDF, and other document formats
"""

import io
import logging
from typing import Dict, List, Optional, Union
import base64

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logging.warning("python-docx not available. DOCX processing disabled.")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PyPDF2 not available. PDF processing disabled.")

class DocumentProcessor:
    """Processes various document formats and extracts text content"""
    
    SUPPORTED_FORMATS = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/pdf': 'pdf',
        'text/plain': 'txt',
        'application/msword': 'doc'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_text_from_base64(self, base64_data: str, mime_type: str) -> str:
        """Extract text from base64 encoded document data"""
        try:
            # Decode base64 data
            document_bytes = base64.b64decode(base64_data)
            
            # Process based on MIME type
            if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return self._extract_from_docx_bytes(document_bytes)
            elif mime_type == 'application/pdf':
                return self._extract_from_pdf_bytes(document_bytes)
            elif mime_type == 'text/plain':
                return document_bytes.decode('utf-8', errors='ignore')
            else:
                return f"[Unsupported document type: {mime_type}]"
                
        except Exception as e:
            self.logger.error(f"Error extracting text from {mime_type}: {str(e)}")
            return f"[Error processing document: {str(e)}]"
    
    def _extract_from_docx_bytes(self, document_bytes: bytes) -> str:
        """Extract text from DOCX document bytes"""
        if not DOCX_AVAILABLE:
            return "[DOCX processing not available - install python-docx]"
        
        try:
            doc_stream = io.BytesIO(document_bytes)
            doc = Document(doc_stream)
            
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            # Also extract from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_content.append(" | ".join(row_text))
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            return f"[Error extracting DOCX content: {str(e)}]"
    
    def _extract_from_pdf_bytes(self, document_bytes: bytes) -> str:
        """Extract text from PDF document bytes"""
        if not PDF_AVAILABLE:
            return "[PDF processing not available - install PyPDF2]"
        
        try:
            pdf_stream = io.BytesIO(document_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(f"[Page {page_num + 1}]\n{page_text.strip()}")
                except Exception as e:
                    text_content.append(f"[Page {page_num + 1} - Error: {str(e)}]")
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            return f"[Error extracting PDF content: {str(e)}]"
    
    def process_inline_data_parts(self, parts: List[Dict]) -> str:
        """Process parts with inline_data and return combined text"""
        extracted_texts = []
        
        for part in parts:
            if 'inline_data' in part:
                mime_type = part['inline_data'].get('mime_type', '')
                data = part['inline_data'].get('data', '')
                
                if data and mime_type:
                    text = self.extract_text_from_base64(data, mime_type)
                    extracted_texts.append(f"[Document - {mime_type}]\n{text}")
            elif 'text' in part:
                extracted_texts.append(part['text'])
        
        return "\n\n" + "="*50 + "\n\n".join(extracted_texts)

# Global instance
document_processor = DocumentProcessor() 