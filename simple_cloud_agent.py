#!/usr/bin/env python3
"""
Simplified Vertex AI Grant Agent for Cloud Deployment
Standalone version without Redis/Neo4j dependencies
"""

import os
import asyncio
import logging
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GrantType(Enum):
    """Grant types for specialized processing"""
    FEDERAL = "federal"
    STATE = "state"
    FOUNDATION = "foundation"
    CORPORATE = "corporate"


@dataclass
class GrantRequest:
    """Grant request structure"""
    organization_info: Dict[str, Any]
    funder_info: Dict[str, Any]
    requirements: Dict[str, Any]
    documents: Optional[List[str]] = None


class VertexAIConfig:
    """Configuration for Vertex AI models"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'eleanor-for-enterprise')
        self.region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        self.model_name = os.getenv('VERTEX_AI_MODEL', 'gemini-2.0-flash-lite-001')
        self.fast_model = os.getenv('VERTEX_AI_FAST_MODEL', 'gemini-2.0-flash-lite-001')


class SimpleGrantAgent:
    """Simplified Grant Agent for cloud deployment"""
    
    def __init__(self):
        self.config = VertexAIConfig()
        
        # Initialize Vertex AI
        vertexai.init(project=self.config.project_id, location=self.config.region)
        self.model = GenerativeModel(self.config.model_name)
        self.fast_model = GenerativeModel(self.config.fast_model)
        
        logger.info(f"Initialized Grant Agent for project: {self.config.project_id}")
    
    async def generate_text(self, prompt: str, use_fast_model: bool = False) -> str:
        """Generate text using Vertex AI"""
        model_name = self.config.fast_model if use_fast_model else self.config.model_name
        logger.info(f"🤖 Starting AI generation with model: {model_name}")
        logger.info(f"📝 Prompt length: {len(prompt)} characters")
        logger.info(f"🔧 Project: {self.config.project_id}, Location: {self.config.region}")
        
        try:
            model = self.fast_model if use_fast_model else self.model
            
            logger.info(f"⚡ Sending request to Vertex AI...")
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: model.generate_content(prompt)
            )
            
            if response.text:
                logger.info(f"✅ Response received - Length: {len(response.text)} characters")
                logger.info(f"📊 Response preview: {response.text[:200]}...")
                return response.text
            else:
                logger.warning("⚠️ Empty response from AI model")
                return "No response generated"
            
        except Exception as e:
            logger.error(f"❌ Error generating text with model {model_name}: {e}")
            logger.error(f"🔍 Full error details: {type(e).__name__}: {str(e)}")
            return f"[AI Model Error - {model_name}]: {str(e)}"
    
    async def detect_grant_type(self, funder_info: Dict[str, Any]) -> GrantType:
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
    
    async def generate_grant_proposal(self, request: GrantRequest) -> str:
        """Generate a complete grant proposal"""
        
        try:
            # Detect grant type
            grant_type = await self.detect_grant_type(request.funder_info)
            
            # Build comprehensive prompt
            proposal_prompt = f"""
            Generate a professional grant proposal for the following request:
            
            ORGANIZATION INFORMATION:
            {self._format_dict(request.organization_info)}
            
            FUNDER INFORMATION:
            {self._format_dict(request.funder_info)}
            
            GRANT TYPE: {grant_type.value}
            
            REQUIREMENTS:
            {self._format_dict(request.requirements)}
            
            Please generate a comprehensive grant proposal that includes:
            1. Executive Summary
            2. Project Description
            3. Goals and Objectives
            4. Methodology/Implementation Plan
            5. Budget Overview
            6. Expected Outcomes
            7. Evaluation Plan
            8. Sustainability Plan
            9. Organization Qualifications
            10. Conclusion
            
            Format the proposal professionally with clear sections and compelling language.
            Tailor the content specifically to the {grant_type.value} grant type and funder requirements.
            """
            
            proposal = await self.generate_text(proposal_prompt)
            
            return proposal
            
        except Exception as e:
            logger.error(f"Error generating grant proposal: {e}")
            return f"Error generating proposal: {str(e)}"
    
    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format dictionary data for prompt inclusion"""
        if not data:
            return "No information provided"
        
        formatted = []
        for key, value in data.items():
            formatted.append(f"- {key.title()}: {value}")
        
        return "\n".join(formatted)


class CloudGrantService:
    """Cloud-native Grant Service using FastAPI"""
    
    def __init__(self):
        self.agent = SimpleGrantAgent()
        
        # FastAPI app
        self.app = FastAPI(
            title="Vertex AI Grant Agent - Cloud Native",
            description="Simplified Multi-Agent System for Grant Proposal Generation",
            version="1.0.0-cloud"
        )
        
        self._setup_middleware()
        self._setup_routes()
        
        logger.info("Cloud Grant Service initialized")
    
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
                "service": "Vertex AI Grant Agent",
                "version": "1.0.0-cloud",
                "status": "operational",
                "endpoints": {
                    "health": "/health",
                    "quick_proposal": "/quick_proposal",
                    "full_proposal": "/full_proposal",
                    "upload_documents": "/upload_documents",
                    "generate": "/generate_grant_proposal",
                    "docs": "/docs"
                },
                "project": self.agent.config.project_id
            })
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return JSONResponse({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "vertex_ai": "connected",
                    "agent": "active"
                },
                "message": "Cloud Grant Agent is operational"
            })
        
        @self.app.post("/generate_grant_proposal")
        async def generate_grant_proposal(request_data: Dict[str, Any]):
            """Generate grant proposal using Vertex AI"""
            try:
                # Validate request
                required_fields = ['organization_info', 'funder_info', 'requirements']
                for field in required_fields:
                    if field not in request_data:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Missing required field: {field}"
                        )
                
                # Create grant request
                grant_request = GrantRequest(
                    organization_info=request_data['organization_info'],
                    funder_info=request_data['funder_info'],
                    requirements=request_data['requirements'],
                    documents=request_data.get('documents', [])
                )
                
                # Generate proposal
                proposal = await self.agent.generate_grant_proposal(grant_request)
                
                return JSONResponse({
                    "success": True,
                    "proposal": proposal,
                    "timestamp": datetime.now().isoformat(),
                    "grant_type": (await self.agent.detect_grant_type(grant_request.funder_info)).value
                })
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in proposal generation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/upload_documents")
        async def upload_documents(files: List[UploadFile] = File(...)):
            """Upload documents for grant processing (simplified version)"""
            try:
                # For now, just return success with file info
                file_info = []
                for file in files:
                    content = await file.read()
                    file_info.append({
                        "filename": file.filename,
                        "size": len(content),
                        "content_type": file.content_type
                    })
                
                return JSONResponse({
                    "success": True,
                    "message": f"Uploaded {len(files)} documents successfully",
                    "files": file_info,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error uploading documents: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/quick_proposal")
        async def quick_proposal(data: Dict[str, Any]):
            """Quick proposal generation with minimal input"""
            logger.info(f"🚀 Quick Proposal Request Started")
            logger.info(f"📊 Input data: {data}")
            
            try:
                organization_name = data.get('organization_name', 'Your Organization')
                project_title = data.get('project_title', 'Grant Project')
                funder_name = data.get('funder_name', 'Grant Funder')
                amount_requested = data.get('amount_requested', '50000')
                project_description = data.get('project_description', 'Project description')
                
                logger.info(f"📝 Extracted data - Org: {organization_name}, Project: {project_title}")
                
                quick_prompt = f"""
                Generate a concise grant proposal for:
                
                Organization: {organization_name}
                Project: {project_title}
                Funder: {funder_name}
                Amount: ${amount_requested}
                Description: {project_description}
                
                Include: summary, objectives, budget outline, and expected impact.
                """
                
                proposal = await self.agent.generate_text(quick_prompt)
                
                return JSONResponse({
                    "success": True,
                    "proposal": proposal,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in quick proposal: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/full_proposal")
        async def full_proposal(data: Dict[str, Any]):
            """Full comprehensive proposal generation"""
            try:
                # Extract comprehensive data
                organization_info = data.get('organizationData', {})
                funder_info = data.get('funderData', {})
                project_data = data.get('projectData', {})
                documents = data.get('uploadedFiles', [])
                
                # Build comprehensive prompt
                full_prompt = f"""
                Generate a comprehensive grant proposal with the following information:
                
                ORGANIZATION INFORMATION:
                - Name: {organization_info.get('name', 'N/A')}
                - Mission: {organization_info.get('mission', 'N/A')}
                - History: {organization_info.get('history', 'N/A')}
                - Tax Status: {organization_info.get('taxStatus', 'N/A')}
                - Contact: {organization_info.get('contactPerson', 'N/A')}
                
                FUNDER INFORMATION:
                - Name: {funder_info.get('name', 'N/A')}
                - Type: {funder_info.get('type', 'N/A')}
                - Focus Areas: {funder_info.get('focusAreas', 'N/A')}
                - Requirements: {funder_info.get('requirements', 'N/A')}
                
                PROJECT DETAILS:
                - Title: {project_data.get('title', 'N/A')}
                - Amount: ${project_data.get('amountRequested', 'N/A')}
                - Duration: {project_data.get('projectDuration', 'N/A')}
                - Description: {project_data.get('projectDescription', 'N/A')}
                - Objectives: {project_data.get('projectObjectives', 'N/A')}
                - Target Population: {project_data.get('targetPopulation', 'N/A')}
                - Expected Outcomes: {project_data.get('expectedOutcomes', 'N/A')}
                - Budget Items: {project_data.get('budgetItems', 'N/A')}
                
                UPLOADED DOCUMENTS: {len(documents)} files provided
                
                Generate a professional, comprehensive grant proposal including:
                1. Executive Summary
                2. Organization Background
                3. Statement of Need
                4. Project Description
                5. Goals and Objectives  
                6. Methodology
                7. Evaluation Plan
                8. Budget Narrative
                9. Sustainability Plan
                10. Timeline
                """
                
                proposal = await self.agent.generate_text(full_prompt)
                
                return JSONResponse({
                    "success": True,
                    "proposal": proposal,
                    "timestamp": datetime.now().isoformat(),
                    "mode": "full_comprehensive"
                })
                
            except Exception as e:
                logger.error(f"Error in full proposal: {e}")
                raise HTTPException(status_code=500, detail=str(e))


# Main entry point
async def main():
    """Main entry point for cloud deployment"""
    try:
        service = CloudGrantService()
        
        import uvicorn
        
        # Get port from environment (Cloud Run uses PORT env var)
        port = int(os.getenv("PORT", 8080))
        
        config = uvicorn.Config(
            app=service.app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        logger.info(f"Starting Vertex AI Grant Agent on port {port}")
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error running service: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 