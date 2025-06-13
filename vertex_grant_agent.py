"""
Vertex AI Native Grant Agent
Multi-Agent System (MAS) implementation with async artifact service
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Google Cloud imports
import vertexai
from vertexai.generative_models import GenerativeModel


# FastAPI for async web service
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Local imports
from async_artifact_service import AsyncArtifactService, ArtifactProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Configure logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Different agent roles in the MAS"""
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    WRITING = "writing"
    REVIEW = "review"
    COMPLIANCE = "compliance"


class GrantType(Enum):
    """Grant types for specialized processing"""
    FEDERAL = "federal"
    STATE = "state"
    FOUNDATION = "foundation"
    CORPORATE = "corporate"


@dataclass
class TaskContext:
    """Context for task execution"""
    task_id: str
    grant_type: GrantType
    organization_info: Dict[str, Any]
    funder_info: Dict[str, Any]
    documents: List[str]  # Artifact IDs
    requirements: Dict[str, Any]
    deadline: Optional[datetime] = None


class VertexAIConfig:
    """Configuration for Vertex AI models"""
    
    def __init__(self, config: Dict[str, str]):
        self.project_id = config.get('GOOGLE_CLOUD_PROJECT')
        self.region = config.get('GOOGLE_CLOUD_REGION', 'us-central1')
        self.model_name = config.get('VERTEX_AI_MODEL', 'gemini-1.5-pro')
        self.fast_model = config.get('VERTEX_AI_FAST_MODEL', 'gemini-1.5-flash')


class BaseAgent:
    """Base class for all agents in the MAS"""
    
    def __init__(
        self, 
        agent_id: str, 
        role: AgentRole, 
        vertex_config: VertexAIConfig
    ):
        self.agent_id = agent_id
        self.role = role
        self.vertex_config = vertex_config
        self.is_active = False
        
        # Initialize Vertex AI
        vertexai.init(project=vertex_config.project_id, location=vertex_config.region)
        self.model = GenerativeModel(vertex_config.model_name)
        self.fast_model = GenerativeModel(vertex_config.fast_model)
        
        logger.info(f"Initialized {role.value} agent: {agent_id}")
    
    async def generate_text(self, prompt: str, use_fast_model: bool = False) -> str:
        """Generate text using Vertex AI"""
        try:
            model = self.fast_model if use_fast_model else self.model
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: model.generate_content(prompt)
            )
            
            return response.text if response.text else ""
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return f"[Error: {str(e)}]"


class OrchestratorAgent(BaseAgent):
    """Main orchestrator agent for task delegation and coordination"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_tasks: Dict[str, TaskContext] = {}
    
    async def process_grant_request(
        self, 
        organization_info: Dict[str, Any],
        funder_info: Dict[str, Any],
        document_artifacts: List[str],
        requirements: Dict[str, Any]
    ) -> str:
        """Process a grant request by coordinating sub-agents"""
        
        try:
            # Generate task ID
            task_id = f"grant_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Detect grant type
            grant_type = await self._detect_grant_type(funder_info)
            
            # Create task context
            task_context = TaskContext(
                task_id=task_id,
                grant_type=grant_type,
                organization_info=organization_info,
                funder_info=funder_info,
                documents=document_artifacts,
                requirements=requirements
            )
            
            self.active_tasks[task_id] = task_context
            
            # Start coordinated processing
            result = await self._coordinate_grant_processing(task_context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing grant request: {e}")
            return f"Error: {str(e)}"
    
    async def _detect_grant_type(self, funder_info: Dict[str, Any]) -> GrantType:
        """Detect grant type based on funder information"""
        
        classification_prompt = f"""
        Classify the following funder as one of: federal, state, foundation, corporate
        
        Funder Information:
        Name: {funder_info.get('name', '')}
        Type: {funder_info.get('type', '')}
        Description: {funder_info.get('description', '')}
        
        Classification (respond with only one word: federal, state, foundation, or corporate):
        """
        
        classification = await self.generate_text(classification_prompt, use_fast_model=True)
        classification = classification.strip().lower()
        
        # Map to enum
        type_mapping = {
            'federal': GrantType.FEDERAL,
            'state': GrantType.STATE,
            'foundation': GrantType.FOUNDATION,
            'corporate': GrantType.CORPORATE
        }
        
        return type_mapping.get(classification, GrantType.FOUNDATION)
    
    async def _coordinate_grant_processing(self, task_context: TaskContext) -> str:
        """Coordinate the grant processing across multiple agents"""
        
        try:
            # Phase 1: Research and Analysis
            research_result = await self._delegate_research(task_context)
            
            # Phase 2: Content Generation
            writing_result = await self._delegate_writing(task_context, research_result)
            
            # Phase 3: Review and Quality Assurance
            review_result = await self._delegate_review(task_context, writing_result)
            
            # Phase 4: Compliance Check
            compliance_result = await self._delegate_compliance(task_context, review_result)
            
            # Generate final output
            final_result = await self._generate_final_output(
                task_context, research_result, writing_result, review_result, compliance_result
            )
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error in coordination: {e}")
            return f"Coordination error: {str(e)}"
    
    async def _delegate_research(self, task_context: TaskContext) -> Dict[str, Any]:
        """Delegate research task to research agent"""
        
        research_prompt = f"""
        Conduct comprehensive research for a {task_context.grant_type.value} grant proposal.
        
        Organization: {task_context.organization_info.get('name', 'Unknown')}
        Funder: {task_context.funder_info.get('name', 'Unknown')}
        
        Research areas:
        1. Funder priorities and requirements
        2. Similar successful proposals
        3. Compliance requirements
        4. Budget guidelines
        5. Evaluation criteria
        
        Provide detailed research findings in JSON format.
        """
        
        research_result = await self.generate_text(research_prompt)
        
        return {"research_findings": research_result}
    
    async def _delegate_writing(self, task_context: TaskContext, research_result: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate writing task to writing agent"""
        
        writing_prompt = f"""
        Generate a comprehensive {task_context.grant_type.value} grant proposal based on the following:
        
        Research Findings:
        {research_result.get('research_findings', '')}
        
        Organization Information:
        {json.dumps(task_context.organization_info, indent=2)}
        
        Funder Information:
        {json.dumps(task_context.funder_info, indent=2)}
        
        Generate a complete proposal with all required sections for {task_context.grant_type.value} grants.
        """
        
        proposal_content = await self.generate_text(writing_prompt)
        
        return {"proposal_content": proposal_content}
    
    async def _delegate_review(self, task_context: TaskContext, writing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate review task to review agent"""
        
        review_prompt = f"""
        Review the following {task_context.grant_type.value} grant proposal for:
        1. Completeness
        2. Clarity and coherence
        3. Alignment with funder requirements
        4. Quality score (1-10)
        5. Specific improvement recommendations
        
        Proposal Content:
        {writing_result.get('proposal_content', '')}
        
        Provide detailed review and recommendations.
        """
        
        review_result = await self.generate_text(review_prompt)
        
        return {"review_analysis": review_result}
    
    async def _delegate_compliance(self, task_context: TaskContext, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate compliance check to compliance agent"""
        
        compliance_prompt = f"""
        Perform compliance check for {task_context.grant_type.value} grant proposal.
        
        Check for:
        1. Required sections and attachments
        2. Formatting requirements
        3. Budget compliance
        4. Regulatory requirements
        5. Submission requirements
        
        Review Analysis:
        {review_result.get('review_analysis', '')}
        
        Provide compliance checklist and any issues found.
        """
        
        compliance_result = await self.generate_text(compliance_prompt)
        
        return {"compliance_check": compliance_result}
    
    async def _generate_final_output(
        self, 
        task_context: TaskContext,
        research_result: Dict[str, Any],
        writing_result: Dict[str, Any],
        review_result: Dict[str, Any],
        compliance_result: Dict[str, Any]
    ) -> str:
        """Generate final grant proposal output"""
        
        final_prompt = f"""
        Generate the FINAL, polished {task_context.grant_type.value} grant proposal incorporating all feedback:
        
        Original Proposal:
        {writing_result.get('proposal_content', '')}
        
        Review Feedback:
        {review_result.get('review_analysis', '')}
        
        Compliance Requirements:
        {compliance_result.get('compliance_check', '')}
        
        Create the final, submission-ready grant proposal.
        """
        
        final_proposal = await self.generate_text(final_prompt)
        
        return final_proposal


class VertexGrantAgentService:
    """Main service orchestrating the MAS for grant proposal generation"""
    
    def __init__(self):
        self.config = self._load_config()
        self.vertex_config = VertexAIConfig(self.config)
        self.artifact_service = None
        self.artifact_processor = None
        self.orchestrator = None
        
        # FastAPI app
        self.app = FastAPI(
            title="Vertex AI Grant Agent Service",
            description="Multi-Agent System for Grant Proposal Generation",
            version="1.0.0"
        )
        
        self._setup_routes()
        self._setup_middleware()
    
    def _load_config(self) -> Dict[str, str]:
        """Load configuration from environment"""
        return {key: os.getenv(key, default) for key, default in [
            ('GOOGLE_CLOUD_PROJECT', ''),
            ('GOOGLE_CLOUD_REGION', 'us-central1'),
            ('VERTEX_AI_MODEL', 'gemini-2.0-flash-lite-001'),
            ('VERTEX_AI_FAST_MODEL', 'gemini-2.0-flash-lite-001'),


            ('ARTIFACT_BUCKET_NAME', 'grant-artifacts'),
            ('ARTIFACT_MAX_SIZE_MB', '500'),
            ('ARTIFACT_RETENTION_DAYS', '90'),
            ('DOC_TEMP_STORAGE_PATH', '/tmp/grant_docs'),
            ('ARTIFACT_STORAGE_BACKEND', 'gcs')
        ]}
    
    async def initialize(self):
        """Initialize all services and agents"""
        try:
            

            
            # Initialize artifact service
            try:
                self.artifact_service = AsyncArtifactService(self.config)
                await self.artifact_service.initialize()
                logger.info("Artifact service initialized")
            except Exception as e:
                logger.warning(f"Artifact service initialization failed: {e}")
                self.artifact_service = None
            
            # Initialize artifact processor
            if self.artifact_service:
                self.artifact_processor = ArtifactProcessor(self.artifact_service)
            else:
                self.artifact_processor = None
            
            # Initialize orchestrator agent
            self.orchestrator = OrchestratorAgent(
                agent_id="orchestrator_001",
                role=AgentRole.ORCHESTRATOR,
                vertex_config=self.vertex_config
            )
            
            logger.info("Core services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize core services: {e}")
            # Don't raise - allow service to start with limited functionality
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            """Root endpoint"""
            return JSONResponse({
                "service": "Vertex AI Grant Agent - MAS Version",
                "version": "2.0.0-mas",
                "status": "operational",
                "architecture": "Multi-Agent System with AsyncArtifactService",
                "endpoints": {
                    "health": "/health",
                    "quick_proposal": "/quick_proposal",
                    "full_proposal": "/full_proposal", 
                    "upload_documents": "/upload_documents",
                    "get_document": "/documents/{artifact_id}",
                    "generate_grant_proposal": "/generate_grant_proposal",
                    "docs": "/docs"
                },
                "services": {
                    "vertex_ai": "active",
                    "gcs_storage": "active",
                    "direct_gcs_storage": "active",
 
                    "async_artifacts": "available" if self.artifact_service else "gcs_fallback",
                    "multi_agent_system": "active"
                }
            })
        
        @self.app.post("/upload_documents")
        async def upload_documents(files: List[UploadFile] = File(...)):
            """Upload documents for grant processing"""
            try:
                # Use AsyncArtifactService if available, otherwise fallback to direct GCS upload
                if self.artifact_service:
                    logger.info("Using AsyncArtifactService for document upload")
                    artifact_ids = []
                    
                    for file in files:
                        # Read file content
                        content = await file.read()
                        
                        # Upload to artifact service
                        metadata = await self.artifact_service.upload_artifact(
                            file_data=content,
                            filename=file.filename,
                            content_type=file.content_type
                        )
                        
                        artifact_ids.append(metadata.artifact_id)
                    
                    return JSONResponse({
                        "success": True,
                        "artifact_ids": artifact_ids,
                        "message": f"Uploaded {len(files)} documents successfully"
                    })
                else:
                    # Fallback: Direct GCS upload without Redis dependency
                    logger.info("Using direct GCS upload fallback")
                    
                    from google.cloud import storage
                    import uuid
                    import hashlib
                    
                    storage_client = storage.Client()
                    bucket_name = "grant-artifacts-fallback"  # Use a fallback bucket
                    
                    # Try to get bucket, create if doesn't exist
                    try:
                        bucket = storage_client.bucket(bucket_name)
                        if not bucket.exists():
                            bucket = storage_client.create_bucket(bucket_name)
                    except Exception:
                        # Use default project bucket or create temp storage
                        bucket_name = f"{self.vertex_config.project_id}-grant-docs"
                        bucket = storage_client.bucket(bucket_name)
                    
                    uploaded_documents = []
                    
                    for file in files:
                        # Read file content
                        content = await file.read()
                        
                        # Generate unique artifact ID
                        artifact_id = str(uuid.uuid4())
                        content_hash = hashlib.sha256(content).hexdigest()
                        
                        # Create GCS object path
                        blob_name = f"documents/{artifact_id}/{file.filename}"
                        blob = bucket.blob(blob_name)
                        
                        # Upload to GCS
                        blob.upload_from_string(
                            content,
                            content_type=file.content_type or 'application/octet-stream'
                        )
                        
                        # Create document metadata
                        doc_metadata = {
                            "artifact_id": artifact_id,
                            "filename": file.filename,
                            "content_type": file.content_type,
                            "size_bytes": len(content),
                            "content_hash": content_hash,
                            "gcs_url": f"gs://{bucket_name}/{blob_name}",
                            "public_url": blob.public_url,
                            "upload_timestamp": datetime.now().isoformat()
                        }
                        
                        uploaded_documents.append(doc_metadata)
                        logger.info(f"Uploaded {file.filename} to GCS: {blob_name}")
                    
                    return JSONResponse({
                        "success": True,
                        "documents": uploaded_documents,
                        "message": f"Uploaded {len(files)} documents to cloud storage",
                        "storage_type": "gcs_direct"
                    })
                
            except Exception as e:
                logger.error(f"Error uploading documents: {e}")
                raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
        
        @self.app.get("/documents/{artifact_id}")
        async def get_document(artifact_id: str):
            """Retrieve document metadata and content by artifact ID"""
            try:
                if self.artifact_service:
                    # Use AsyncArtifactService if available
                    metadata = await self.artifact_service.get_artifact_metadata(artifact_id)
                    if metadata:
                        return JSONResponse({
                            "success": True,
                            "metadata": metadata.dict(),
                            "storage_type": "async_service"
                        })
                else:
                    # Fallback: Try to find in GCS
                    from google.cloud import storage
                    
                    storage_client = storage.Client()
                    bucket_name = f"{self.vertex_config.project_id}-grant-docs"
                    
                    try:
                        bucket = storage_client.bucket(bucket_name)
                        blobs = list(bucket.list_blobs(prefix=f"documents/{artifact_id}/"))
                        
                        if blobs:
                            blob = blobs[0]  # Get first matching document
                            return JSONResponse({
                                "success": True,
                                "metadata": {
                                    "artifact_id": artifact_id,
                                    "filename": blob.name.split('/')[-1],
                                    "content_type": blob.content_type,
                                    "size_bytes": blob.size,
                                    "gcs_url": f"gs://{bucket_name}/{blob.name}",
                                    "public_url": blob.public_url,
                                    "created": blob.time_created.isoformat() if blob.time_created else None
                                },
                                "storage_type": "gcs_direct"
                            })
                    except Exception as e:
                        logger.error(f"Error retrieving document from GCS: {e}")
                
                raise HTTPException(status_code=404, detail="Document not found")
                
            except Exception as e:
                logger.error(f"Error retrieving document: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/generate_grant_proposal")
        async def generate_grant_proposal(request: Dict[str, Any]):
            """Generate grant proposal using MAS"""
            try:
                # Extract request parameters
                organization_info = request.get('organization_info', {})
                funder_info = request.get('funder_info', {})
                document_artifacts = request.get('document_artifacts', [])
                requirements = request.get('requirements', {})
                
                # Process through orchestrator
                result = await self.orchestrator.process_grant_request(
                    organization_info=organization_info,
                    funder_info=funder_info,
                    document_artifacts=document_artifacts,
                    requirements=requirements
                )
                
                return JSONResponse({
                    "success": True,
                    "proposal": result,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error generating proposal: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/quick_proposal")
        async def quick_proposal(data: Dict[str, Any]):
            """Quick proposal generation with minimal input"""
            logger.info(f"🚀 Quick Proposal Request Started - MAS Version")
            logger.info(f"📊 Input data: {data}")
            
            try:
                # Extract basic info
                organization_name = data.get('organization_name', 'Your Organization')
                project_title = data.get('project_title', 'Grant Project')
                funder_name = data.get('funder_name', 'Grant Funder')
                amount_requested = data.get('amount_requested', '50000')
                project_description = data.get('project_description', 'Project description')
                
                logger.info(f"📝 Processing through MAS - Org: {organization_name}, Project: {project_title}")
                
                # Create simplified request for orchestrator
                organization_info = {"name": organization_name}
                funder_info = {"name": funder_name}
                requirements = {
                    "project_title": project_title,
                    "amount_requested": amount_requested,
                    "project_description": project_description,
                    "type": "quick_proposal"
                }
                
                # Process through orchestrator (if available) or fallback to simple generation
                if self.orchestrator:
                    proposal = await self.orchestrator.process_grant_request(
                        organization_info=organization_info,
                        funder_info=funder_info,
                        document_artifacts=[],
                        requirements=requirements
                    )
                else:
                    # Fallback to simple generation
                    quick_prompt = f"""
                    Generate a concise grant proposal for:
                    
                    Organization: {organization_name}
                    Project: {project_title}
                    Funder: {funder_name}
                    Amount: ${amount_requested}
                    Description: {project_description}
                    
                    Include: summary, objectives, budget outline, and expected impact.
                    """
                    # Simple text generation fallback
                    proposal = f"Grant proposal for {organization_name} - {project_title} requesting ${amount_requested} from {funder_name}. {project_description}"
                
                logger.info(f"✅ Quick proposal generated successfully")
                
                return JSONResponse({
                    "success": True,
                    "proposal": proposal,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error in quick proposal: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/full_proposal")
        async def full_proposal(data: Dict[str, Any]):
            """Full comprehensive proposal generation using MAS"""
            logger.info(f"🚀 Full Proposal Request Started - MAS Version")
            
            try:
                # Extract comprehensive data
                organization_info = data.get('organizationData', {})
                funder_info = data.get('funderData', {})
                project_data = data.get('projectData', {})
                documents = data.get('uploadedFiles', [])
                
                logger.info(f"📊 Processing comprehensive proposal through MAS")
                
                # Build requirements for orchestrator
                requirements = {
                    "type": "full_proposal",
                    "project_data": project_data,
                    "mode": "comprehensive"
                }
                
                # Process through orchestrator
                if self.orchestrator:
                    proposal = await self.orchestrator.process_grant_request(
                        organization_info=organization_info,
                        funder_info=funder_info,
                        document_artifacts=documents,
                        requirements=requirements
                    )
                else:
                    # Fallback comprehensive generation
                    proposal = f"""
                    # Comprehensive Grant Proposal
                    
                    ## Organization: {organization_info.get('name', 'N/A')}
                    Mission: {organization_info.get('mission', 'N/A')}
                    
                    ## Project: {project_data.get('title', 'N/A')}
                    Amount Requested: ${project_data.get('amountRequested', 'N/A')}
                    Duration: {project_data.get('projectDuration', 'N/A')}
                    
                    ## Description
                    {project_data.get('projectDescription', 'N/A')}
                    
                    ## Objectives
                    {project_data.get('projectObjectives', 'N/A')}
                    
                    [This is a fallback proposal - full MAS processing unavailable]
                    """
                
                logger.info(f"✅ Full proposal generated successfully")
                
                return JSONResponse({
                    "success": True,
                    "proposal": proposal,
                    "timestamp": datetime.now().isoformat(),
                    "mode": "full_comprehensive_mas"
                })
                
            except Exception as e:
                logger.error(f"❌ Error in full proposal: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            services = {
                "direct_gcs": "active",
                "artifact_service": "active" if self.artifact_service else "unavailable",
                "orchestrator": "active" if self.orchestrator else "inactive"
            }
            
            # Service is healthy if core orchestrator is available
            status = "healthy" if self.orchestrator else "unhealthy"
            
            return JSONResponse({
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "services": services,
                "message": "Vertex AI Grant Agent is operational"
            })


# Main entry point
async def main():
    """Main entry point"""
    service = VertexGrantAgentService()
    
    try:
        await service.initialize()
        
        import uvicorn
        config = uvicorn.Config(
            app=service.app,
            host="0.0.0.0",
            port=8080,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error running service: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 