"""
Async Artifact Service for Grant Agent Vertex AI Native
Handles document uploads, processing, and storage with async operations
"""

import asyncio
import aiofiles
import aiohttp
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging
import base64
import hashlib

from google.cloud import storage
from google.cloud import aiplatform
import redis.asyncio as redis

from pydantic import BaseModel, Field
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArtifactMetadata(BaseModel):
    """Metadata for artifact storage"""
    artifact_id: str
    filename: str
    content_type: str
    size_bytes: int
    upload_timestamp: datetime
    processed_timestamp: Optional[datetime] = None
    processing_status: str = "pending"  # pending, processing, completed, failed
    extracted_text: Optional[str] = None
    content_hash: str
    storage_path: str
    user_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ProcessingResult(BaseModel):
    """Result of document processing"""
    artifact_id: str
    success: bool
    extracted_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_seconds: float


class AsyncArtifactService:
    """Async service for handling document artifacts"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.storage_client = None
        self.redis_client = None
        self.bucket_name = config.get('ARTIFACT_BUCKET_NAME', 'grant-artifacts')
        self.max_size_mb = int(config.get('ARTIFACT_MAX_SIZE_MB', 100))
        self.retention_days = int(config.get('ARTIFACT_RETENTION_DAYS', 90))
        self.temp_path = Path(config.get('DOC_TEMP_STORAGE_PATH', '/tmp/grant_docs'))
        self.temp_path.mkdir(exist_ok=True)
        
        # Initialize storage backend
        self.storage_backend = config.get('ARTIFACT_STORAGE_BACKEND', 'gcs')
        
    async def initialize(self):
        """Initialize async components"""
        try:
            # Initialize Redis for caching and queuing with graceful fallback
            try:
                redis_url = self.config.get('REDIS_URL', 'redis://localhost:6379/0')
                self.redis_client = redis.from_url(redis_url)
                await self.redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed, will operate without caching: {e}")
                self.redis_client = None
            
            # Initialize Google Cloud Storage if using GCS backend
            if self.storage_backend == 'gcs':
                self.storage_client = storage.Client()
                logger.info("Google Cloud Storage client initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize async components: {e}")
            raise
    
    async def upload_artifact(
        self, 
        file_data: bytes, 
        filename: str, 
        content_type: str,
        user_id: Optional[str] = None,
        tags: List[str] = None
    ) -> ArtifactMetadata:
        """Upload and store an artifact asynchronously"""
        
        try:
            # Generate unique artifact ID
            artifact_id = str(uuid.uuid4())
            
            # Validate file size
            size_bytes = len(file_data)
            if size_bytes > self.max_size_mb * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"File size {size_bytes} exceeds maximum {self.max_size_mb}MB"
                )
            
            # Calculate content hash
            content_hash = hashlib.sha256(file_data).hexdigest()
            
            # Check for duplicates
            existing_artifact = await self._check_duplicate(content_hash)
            if existing_artifact:
                logger.info(f"Duplicate artifact found: {existing_artifact}")
                return existing_artifact
            
            # Store file
            storage_path = await self._store_file(artifact_id, file_data, filename)
            
            # Create metadata
            metadata = ArtifactMetadata(
                artifact_id=artifact_id,
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                upload_timestamp=datetime.now(),
                content_hash=content_hash,
                storage_path=storage_path,
                user_id=user_id,
                tags=tags or []
            )
            
            # Store metadata in Redis (if available)
            await self._store_metadata(metadata)
            
            # Queue for processing (if Redis available)
            await self._queue_for_processing(artifact_id)
            
            logger.info(f"Artifact uploaded successfully: {artifact_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error uploading artifact: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    async def process_artifact(self, artifact_id: str) -> ProcessingResult:
        """Process an artifact asynchronously"""
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Get metadata
            metadata = await self._get_metadata(artifact_id)
            if not metadata:
                raise ValueError(f"Artifact not found: {artifact_id}")
            
            # Update processing status
            metadata.processing_status = "processing"
            metadata.processed_timestamp = datetime.now()
            await self._store_metadata(metadata)
            
            # Retrieve file data
            file_data = await self._retrieve_file(metadata.storage_path)
            
            # Process based on content type
            extracted_text = await self._extract_text(file_data, metadata.content_type)
            
            # Update metadata with results
            metadata.extracted_text = extracted_text
            metadata.processing_status = "completed"
            await self._store_metadata(metadata)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = ProcessingResult(
                artifact_id=artifact_id,
                success=True,
                extracted_text=extracted_text,
                metadata=asdict(metadata),
                processing_time_seconds=processing_time
            )
            
            logger.info(f"Artifact processed successfully: {artifact_id}")
            return result
            
        except Exception as e:
            # Update error status
            try:
                metadata = await self._get_metadata(artifact_id)
                if metadata:
                    metadata.processing_status = "failed"
                    await self._store_metadata(metadata)
            except:
                pass
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = ProcessingResult(
                artifact_id=artifact_id,
                success=False,
                error_message=str(e),
                processing_time_seconds=processing_time
            )
            
            logger.error(f"Error processing artifact {artifact_id}: {e}")
            return result
    
    async def get_artifact_metadata(self, artifact_id: str) -> Optional[ArtifactMetadata]:
        """Get artifact metadata"""
        return await self._get_metadata(artifact_id)
    
    async def list_artifacts(
        self, 
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[ArtifactMetadata]:
        """List artifacts with optional filtering"""
        
        try:
            # Return empty list if Redis not available
            if not self.redis_client:
                logger.info("Redis not available, cannot list artifacts")
                return []
                
            # Get all artifact keys
            pattern = "artifact:*"
            keys = await self.redis_client.keys(pattern)
            
            artifacts = []
            for key in keys[:limit]:
                try:
                    data = await self.redis_client.get(key)
                    if data:
                        artifact_data = json.loads(data)
                        metadata = ArtifactMetadata(**artifact_data)
                        
                        # Apply filters
                        if user_id and metadata.user_id != user_id:
                            continue
                        if status and metadata.processing_status != status:
                            continue
                        
                        artifacts.append(metadata)
                except Exception as e:
                    logger.warning(f"Error loading artifact {key}: {e}")
                    continue
            
            # Sort by upload timestamp (newest first)
            artifacts.sort(key=lambda x: x.upload_timestamp, reverse=True)
            
            return artifacts
            
        except Exception as e:
            logger.error(f"Error listing artifacts: {e}")
            return []
    
    async def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact and its metadata"""
        
        try:
            # Get metadata first
            metadata = await self._get_metadata(artifact_id)
            if not metadata:
                return False
            
            # Delete file from storage
            await self._delete_file(metadata.storage_path)
            
            # Delete metadata from Redis (if available)
            if self.redis_client:
                await self.redis_client.delete(f"artifact:{artifact_id}")
            
            logger.info(f"Artifact deleted: {artifact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting artifact {artifact_id}: {e}")
            return False
    
    async def cleanup_expired_artifacts(self):
        """Cleanup expired artifacts based on retention policy"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            artifacts = await self.list_artifacts()
            
            deleted_count = 0
            for artifact in artifacts:
                if artifact.upload_timestamp < cutoff_date:
                    if await self.delete_artifact(artifact.artifact_id):
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} expired artifacts")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
    
    # Private methods
    
    async def _check_duplicate(self, content_hash: str) -> Optional[ArtifactMetadata]:
        """Check for duplicate artifacts by content hash"""
        
        try:
            # Skip duplicate check if Redis not available
            if not self.redis_client:
                return None
                
            # Search for existing artifact with same hash
            pattern = "artifact:*"
            keys = await self.redis_client.keys(pattern)
            
            for key in keys:
                data = await self.redis_client.get(key)
                if data:
                    artifact_data = json.loads(data)
                    if artifact_data.get('content_hash') == content_hash:
                        return ArtifactMetadata(**artifact_data)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error checking duplicates: {e}")
            return None
    
    async def _store_file(self, artifact_id: str, file_data: bytes, filename: str) -> str:
        """Store file in configured backend"""
        
        if self.storage_backend == 'gcs':
            return await self._store_file_gcs(artifact_id, file_data, filename)
        else:
            return await self._store_file_local(artifact_id, file_data, filename)
    
    async def _store_file_gcs(self, artifact_id: str, file_data: bytes, filename: str) -> str:
        """Store file in Google Cloud Storage"""
        
        try:
            blob_name = f"artifacts/{artifact_id}/{filename}"
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            
            # Upload in a thread to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, blob.upload_from_string, file_data
            )
            
            return f"gcs://{self.bucket_name}/{blob_name}"
            
        except Exception as e:
            logger.error(f"Error storing file in GCS: {e}")
            raise
    
    async def _store_file_local(self, artifact_id: str, file_data: bytes, filename: str) -> str:
        """Store file locally"""
        
        try:
            file_path = self.temp_path / artifact_id / filename
            file_path.parent.mkdir(exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error storing file locally: {e}")
            raise
    
    async def _retrieve_file(self, storage_path: str) -> bytes:
        """Retrieve file from storage"""
        
        if storage_path.startswith('gcs://'):
            return await self._retrieve_file_gcs(storage_path)
        else:
            return await self._retrieve_file_local(storage_path)
    
    async def _retrieve_file_gcs(self, storage_path: str) -> bytes:
        """Retrieve file from Google Cloud Storage"""
        
        try:
            # Parse GCS path
            path_parts = storage_path.replace('gcs://', '').split('/', 1)
            bucket_name = path_parts[0]
            blob_name = path_parts[1]
            
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            # Download in a thread to avoid blocking
            return await asyncio.get_event_loop().run_in_executor(
                None, blob.download_as_bytes
            )
            
        except Exception as e:
            logger.error(f"Error retrieving file from GCS: {e}")
            raise
    
    async def _retrieve_file_local(self, storage_path: str) -> bytes:
        """Retrieve file from local storage"""
        
        try:
            async with aiofiles.open(storage_path, 'rb') as f:
                return await f.read()
            
        except Exception as e:
            logger.error(f"Error retrieving local file: {e}")
            raise
    
    async def _delete_file(self, storage_path: str):
        """Delete file from storage"""
        
        if storage_path.startswith('gcs://'):
            await self._delete_file_gcs(storage_path)
        else:
            await self._delete_file_local(storage_path)
    
    async def _delete_file_gcs(self, storage_path: str):
        """Delete file from Google Cloud Storage"""
        
        try:
            path_parts = storage_path.replace('gcs://', '').split('/', 1)
            bucket_name = path_parts[0]
            blob_name = path_parts[1]
            
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            await asyncio.get_event_loop().run_in_executor(None, blob.delete)
            
        except Exception as e:
            logger.warning(f"Error deleting file from GCS: {e}")
    
    async def _delete_file_local(self, storage_path: str):
        """Delete local file"""
        
        try:
            path = Path(storage_path)
            if path.exists():
                path.unlink()
                # Try to remove parent directory if empty
                try:
                    path.parent.rmdir()
                except:
                    pass
            
        except Exception as e:
            logger.warning(f"Error deleting local file: {e}")
    
    async def _store_metadata(self, metadata: ArtifactMetadata):
        """Store artifact metadata in Redis"""
        
        try:
            # Skip metadata storage if Redis not available
            if not self.redis_client:
                logger.info(f"Redis not available, skipping metadata storage for {metadata.artifact_id}")
                return
                
            key = f"artifact:{metadata.artifact_id}"
            data = json.dumps(asdict(metadata), default=str)
            await self.redis_client.set(key, data)
            
            # Set expiration based on retention policy
            expire_seconds = self.retention_days * 24 * 3600
            await self.redis_client.expire(key, expire_seconds)
            
        except Exception as e:
            logger.error(f"Error storing metadata: {e}")
            # Don't raise - allow operation to continue without Redis
    
    async def _get_metadata(self, artifact_id: str) -> Optional[ArtifactMetadata]:
        """Get artifact metadata from Redis"""
        
        try:
            # Return None if Redis not available
            if not self.redis_client:
                return None
                
            key = f"artifact:{artifact_id}"
            data = await self.redis_client.get(key)
            
            if data:
                artifact_data = json.loads(data)
                return ArtifactMetadata(**artifact_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            return None
    
    async def _queue_for_processing(self, artifact_id: str):
        """Queue artifact for processing"""
        
        try:
            # Skip queuing if Redis not available
            if not self.redis_client:
                logger.info(f"Redis not available, skipping queue for {artifact_id}")
                return
                
            await self.redis_client.lpush("processing_queue", artifact_id)
            logger.info(f"Artifact queued for processing: {artifact_id}")
            
        except Exception as e:
            logger.error(f"Error queuing artifact: {e}")
            # Don't raise - allow operation to continue without Redis
    
    async def _extract_text(self, file_data: bytes, content_type: str) -> str:
        """Extract text from document based on content type"""
        
        try:
            if content_type == 'application/pdf':
                return await self._extract_pdf_text(file_data)
            elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return await self._extract_docx_text(file_data)
            elif content_type == 'text/plain':
                return file_data.decode('utf-8', errors='ignore')
            else:
                return f"[Unsupported content type: {content_type}]"
                
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return f"[Text extraction failed: {str(e)}]"
    
    async def _extract_pdf_text(self, file_data: bytes) -> str:
        """Extract text from PDF"""
        # Implementation would use PyPDF2 or similar in executor
        return "[PDF text extraction placeholder]"
    
    async def _extract_docx_text(self, file_data: bytes) -> str:
        """Extract text from DOCX"""
        # Implementation would use python-docx in executor
        return "[DOCX text extraction placeholder]"


# Background task processor
class ArtifactProcessor:
    """Background processor for artifact queue"""
    
    def __init__(self, artifact_service: AsyncArtifactService):
        self.artifact_service = artifact_service
        self.processing = False
    
    async def start_processing(self):
        """Start background processing of queued artifacts"""
        
        if self.processing:
            return
        
        self.processing = True
        logger.info("Starting artifact processing loop")
        
        try:
            while self.processing:
                try:
                    # Get next artifact from queue
                    artifact_id = await self.artifact_service.redis_client.brpop(
                        "processing_queue", timeout=5
                    )
                    
                    if artifact_id:
                        _, aid = artifact_id
                        aid = aid.decode('utf-8')
                        
                        logger.info(f"Processing artifact: {aid}")
                        result = await self.artifact_service.process_artifact(aid)
                        
                        if result.success:
                            logger.info(f"Successfully processed: {aid}")
                        else:
                            logger.error(f"Failed to process: {aid} - {result.error_message}")
                
                except Exception as e:
                    logger.error(f"Error in processing loop: {e}")
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Fatal error in processing loop: {e}")
        finally:
            self.processing = False
    
    def stop_processing(self):
        """Stop background processing"""
        self.processing = False
        logger.info("Stopping artifact processing loop")


# Export main classes
__all__ = [
    'AsyncArtifactService',
    'ArtifactProcessor',
    'ArtifactMetadata',
    'ProcessingResult'
] 