"""
Vertex AI Native Grant Agent
Multi-Agent System (MAS) implementation with async artifact service
"""

import asyncio
import json
import logging
import os
import re
import uuid
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

# Google Cloud imports
import vertexai
from vertexai.generative_models import GenerativeModel


# FastAPI for async web service
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
import time

# Local imports
from async_artifact_service import AsyncArtifactService, ArtifactProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Configure logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

# Firestore availability flag
FIRESTORE_AVAILABLE = bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))


# Unified logging helpers with request-id parity
def log_info(request: Request, msg: str, **kw):
    rid = getattr(request.state, "request_id", "-") if request else "-"
    logger.info(json.dumps({"request_id": rid, "msg": msg, **kw}))


def log_error(request: Request, msg: str, **kw):
    rid = getattr(request.state, "request_id", "-") if request else "-"
    logger.error(json.dumps({"request_id": rid, "msg": msg, **kw}))


# ---------------------------
# Pydantic Models (lean V1)
# ---------------------------

class Section(BaseModel):
    id: str
    key: str
    title: str
    content: str = ""
    updatedAt: Optional[str] = None


class Anchor(BaseModel):
    startOffset: int = 0
    endOffset: int = 0


class Comment(BaseModel):
    id: str
    draftId: str
    sectionId: str
    anchor: Anchor
    text: str
    author: Optional[str] = None
    resolved: bool = False
    createdAt: str


class Refinement(BaseModel):
    id: str
    draftId: str
    commentIds: List[str] = []
    changedSectionIds: List[str] = []
    before: Dict[str, str] = Field(default_factory=dict)
    after: Dict[str, str] = Field(default_factory=dict)
    createdAt: str


class Draft(BaseModel):
    id: str
    title: Optional[str] = None
    createdAt: str
    updatedAt: str
    initialInput: Dict[str, Any] = Field(default_factory=dict)
    sections: List[Section] = Field(default_factory=list)


class CreateDraftRequest(BaseModel):
    title: Optional[str] = None
    initialInput: Optional[Dict[str, Any]] = None


class AddCommentsRequest(BaseModel):
    comments: Optional[List[Comment]] = None


class RefineRequest(BaseModel):
    changedSectionIds: List[str]
    commentIds: Optional[List[str]] = None


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


# ---------------------------
# DAO Layer (Firestore or In-Memory)
# ---------------------------

class DraftDAO:
    async def create_draft(self, draft: Draft) -> Draft:
        raise NotImplementedError

    async def get_draft(self, draft_id: str) -> Optional[Draft]:
        raise NotImplementedError

    async def save_sections(self, draft_id: str, sections: List[Section]) -> None:
        raise NotImplementedError

    async def add_comments(self, draft_id: str, comments: List[Comment]) -> List[Comment]:
        raise NotImplementedError

    async def list_comments(self, draft_id: str) -> List[Comment]:
        raise NotImplementedError

    async def create_refinement(self, refinement: Refinement) -> Refinement:
        raise NotImplementedError


class InMemoryDAO(DraftDAO):
    def __init__(self):
        self._drafts: Dict[str, Draft] = {}
        self._comments: Dict[str, List[Comment]] = {}
        self._refinements: Dict[str, List[Refinement]] = {}

    async def create_draft(self, draft: Draft) -> Draft:
        self._drafts[draft.id] = draft
        self._comments[draft.id] = []
        self._refinements[draft.id] = []
        return draft

    async def get_draft(self, draft_id: str) -> Optional[Draft]:
        return self._drafts.get(draft_id)

    async def save_sections(self, draft_id: str, sections: List[Section]) -> None:
        draft = self._drafts.get(draft_id)
        if draft:
            draft.sections = sections
            draft.updatedAt = _now_iso()

    async def add_comments(self, draft_id: str, comments: List[Comment]) -> List[Comment]:
        if draft_id not in self._comments:
            self._comments[draft_id] = []
        self._comments[draft_id].extend(comments)
        return comments

    async def list_comments(self, draft_id: str) -> List[Comment]:
        return self._comments.get(draft_id, [])

    async def create_refinement(self, refinement: Refinement) -> Refinement:
        if refinement.draftId not in self._refinements:
            self._refinements[refinement.draftId] = []
        self._refinements[refinement.draftId].append(refinement)
        return refinement


class FirestoreDAO(DraftDAO):
    def __init__(self):
        from google.cloud import firestore  # type: ignore
        self._db = firestore.Client()

    def _draft_doc(self, draft_id: str):
        return self._db.collection('drafts').document(draft_id)

    async def create_draft(self, draft: Draft) -> Draft:
        self._draft_doc(draft.id).set(json.loads(draft.json()))
        return draft

    async def get_draft(self, draft_id: str) -> Optional[Draft]:
        snap = self._draft_doc(draft_id).get()
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        try:
            data['sections'] = [Section(**s) if isinstance(s, dict) else s for s in data.get('sections', [])]
            return Draft(**data)
        except Exception:
            return None

    async def save_sections(self, draft_id: str, sections: List[Section]) -> None:
        self._draft_doc(draft_id).update({
            'sections': [json.loads(s.json()) for s in sections],
            'updatedAt': _now_iso(),
        })

    async def add_comments(self, draft_id: str, comments: List[Comment]) -> List[Comment]:
        col = self._draft_doc(draft_id).collection('comments')
        batch = self._db.batch()
        for c in comments:
            batch.set(col.document(c.id), json.loads(c.json()))
        batch.commit()
        return comments

    async def list_comments(self, draft_id: str) -> List[Comment]:
        col = self._draft_doc(draft_id).collection('comments')
        docs = list(col.stream())
        out: List[Comment] = []
        for d in docs:
            data = d.to_dict() or {}
            try:
                if isinstance(data.get('anchor'), dict):
                    data['anchor'] = Anchor(**data['anchor'])
                out.append(Comment(**data))
            except Exception:
                continue
        return out

    async def create_refinement(self, refinement: Refinement) -> Refinement:
        col = self._draft_doc(refinement.draftId).collection('refinements')
        col.document(refinement.id).set(json.loads(refinement.json()))
        return refinement


# ---------------------------
# Content helpers
# ---------------------------

def _canonical_sections(initial: Dict[str, Any]) -> List[Section]:
    keys = [
        ("exec_summary", "Executive Summary"),
        ("need", "Statement of Need"),
        ("description", "Project Description"),
        ("goals", "Goals & Objectives"),
        ("methodology", "Methodology"),
        ("timeline", "Timeline"),
        ("budget", "Budget"),
        ("evaluation", "Evaluation Plan"),
        ("sustainability", "Sustainability"),
        ("outcomes", "Expected Outcomes"),
    ]
    content_hints = []
    if initial:
        org = initial.get('org') or initial.get('organization') or {}
        funder = initial.get('funder') or {}
        project = initial.get('project') or {}
        hint = f"Organization: {org.get('name','')}. Funder: {funder.get('name','')}. Project: {project.get('title','')}."
        content_hints.append(hint)
    now = _now_iso()
    return [Section(id=_new_id('sec'), key=k, title=title, content="\n\n".join(content_hints).strip(), updatedAt=now) for k, title in keys]


async def _safe_model_json_call(generator: Any, prompt: str, schema_note: str) -> Dict[str, Any]:
    """Ask model for JSON and robustly parse it."""
    try:
        def _call():
            return generator.generate_content(prompt)
        resp = await asyncio.get_event_loop().run_in_executor(None, _call)
        text = getattr(resp, 'text', '') or ''
    except Exception as e:
        logger.warning("model call failed: %s", e)
        text = ''

    # Try direct json
    for candidate in [text]:
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Extract JSON block
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            # naïve repairs
            repaired = m.group(0)
            repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
            try:
                return json.loads(repaired)
            except Exception:
                pass

    # Retry once with a stricter instruction
    try:
        def _retry():
            return generator.generate_content(prompt + "\nReturn ONLY valid JSON, no commentary.")
        resp2 = await asyncio.get_event_loop().run_in_executor(None, _retry)
        text2 = getattr(resp2, 'text', '') or ''
        return json.loads(text2)
    except Exception:
        pass

    logger.info("invalid JSON from model after retry, returning empty schema: %s", schema_note)
    return {}


async def extract_text(content: bytes, filename: str) -> str:
    name = (filename or '').lower()
    try:
        if name.endswith('.docx'):
            try:
                from docx import Document  # type: ignore
                doc = Document(BytesIO(content))
                return "\n".join([p.text for p in doc.paragraphs])
            except Exception:
                pass
        if name.endswith('.pdf'):
            try:
                from pdfminer.high_level import extract_text as pdf_extract  # type: ignore
                return pdf_extract(BytesIO(content))
            except Exception:
                pass
        if name.endswith('.csv'):
            try:
                import csv
                text_lines: List[str] = []
                for row in csv.reader(BytesIO(content).read().decode(errors='ignore').splitlines()):
                    text_lines.append(", ".join(row))
                return "\n".join(text_lines)
            except Exception:
                pass
        # default .txt/.md or unknown
        return content.decode(errors='ignore')
    except Exception:
        return content.decode(errors='ignore')


async def extract_fields(text: str, generator: Any) -> Dict[str, Any]:
    """Map raw text to structured fields; model optional."""
    prompt = (
        "You are an information extraction system. Extract grant proposal fields as strict JSON with keys: "
        "org, funder, project, objectives, budget, timeline, impact. Use strings or arrays of strings."
        f"\nText:\n{text[:6000]}\nReturn only JSON."
    )
    if generator:
        data = await _safe_model_json_call(generator, prompt, schema_note='extract_fields')
        if data:
            return data
    # fallback heuristics
    budget_match = re.search(r"\$?[0-9][0-9,\.]+", text)
    return {
        "org": {},
        "funder": {},
        "project": {"title": None, "summary": text[:400] + ("..." if len(text) > 400 else "")},
        "objectives": [],
        "budget": {"amount": budget_match.group(0) if budget_match else None},
        "timeline": {},
        "impact": None,
    }


async def refine_sections_helper(dao: Any, draft_id: str, changed_section_ids: List[str], comment_ids: Optional[List[str]], generator: Any):
    draft = await dao.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    comments = await dao.list_comments(draft_id)
    if comment_ids:
        comments = [c for c in comments if c.id in comment_ids]
    unresolved = [c for c in comments if not c.resolved and c.sectionId in changed_section_ids]

    id_to_section = {s.id: s for s in draft.sections}
    updated: List[Section] = []
    before: Dict[str, str] = {}
    after: Dict[str, str] = {}

    for sid in changed_section_ids:
        section = id_to_section.get(sid)
        if not section:
            continue
        section_comments = [c for c in unresolved if c.sectionId == sid]
        instructions = "\n".join([f"- {c.text} (range {c.anchor.startOffset}-{c.anchor.endOffset})" for c in section_comments])
        prompt = (
            "Refine the following proposal section. Apply only the requested changes. "
            "Keep structure and tone consistent. Return only the updated section text.\n"
            f"Initial Context (org/funder/project): {json.dumps(draft.initialInput)[:1500]}\n"
            f"Section Title: {section.title}\n"
            f"Current Content:\n{section.content}\n"
            f"Instructions:\n{instructions or 'Minor improvements for clarity.'}"
        )
        new_text = section.content
        try:
            def _call():
                return generator.generate_content(prompt)
            resp = await asyncio.get_event_loop().run_in_executor(None, _call)
            cand = getattr(resp, 'text', '') or ''
            if cand.strip():
                new_text = cand.strip()
        except Exception as e:
            logger.warning("refine call failed: %s", e)
        before[sid] = section.content
        section.content = new_text
        section.updatedAt = _now_iso()
        after[sid] = new_text
        updated.append(section)

    if updated:
        # persist
        await dao.save_sections(draft_id, list(id_to_section.values()))
        refinement = Refinement(
            id=_new_id('ref'),
            draftId=draft_id,
            commentIds=[c.id for c in unresolved],
            changedSectionIds=[s.id for s in updated],
            before=before,
            after=after,
            createdAt=_now_iso(),
        )
        await dao.create_refinement(refinement)
    else:
        refinement = Refinement(
            id=_new_id('ref'), draftId=draft_id, commentIds=[], changedSectionIds=[], before={}, after={}, createdAt=_now_iso()
        )

    return updated, refinement


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
        requirements: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> str:
        """Process a grant request by coordinating sub-agents"""
        
        try:
            # Generate or use provided task ID
            task_id = task_id or f"grant_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
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
            t0 = datetime.now()
            # Phase 1: Research and Analysis
            research_result = await self._delegate_research(task_context)
            t1 = datetime.now()
            
            # Phase 2: Content Generation
            writing_result = await self._delegate_writing(task_context, research_result)
            t2 = datetime.now()
            
            # Phase 3: Review and Quality Assurance
            review_result = await self._delegate_review(task_context, writing_result)
            t3 = datetime.now()
            
            # Phase 4: Compliance Check
            compliance_result = await self._delegate_compliance(task_context, review_result)
            t4 = datetime.now()
            
            # Generate final output
            final_result = await self._generate_final_output(
                task_context, research_result, writing_result, review_result, compliance_result
            )
            t5 = datetime.now()
            
            logger.info(json.dumps({
                "latency_ms": {
                    "research": (t1 - t0).total_seconds() * 1000,
                    "writing": (t2 - t1).total_seconds() * 1000,
                    "review": (t3 - t2).total_seconds() * 1000,
                    "compliance": (t4 - t3).total_seconds() * 1000,
                    "finalize": (t5 - t4).total_seconds() * 1000,
                    "total": (t5 - t0).total_seconds() * 1000
                }
            }))
            
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
        
        # Funder-language alignment step: derive tone/lexicon from funder information and align organization content
        funder_lang_prompt = f"""
        Analyze the funder's language and phrasing preferences from this info and return a concise style guide:
        {json.dumps(task_context.funder_info, indent=2)}
        
        Return as JSON with keys: tone (string), preferred_terms (string[]), avoid_terms (string[]), reading_level (string), style_notes (string[]).
        """
        funder_lang = await self.generate_text(funder_lang_prompt, use_fast_model=True)

        writing_prompt = f"""
        Generate a comprehensive {task_context.grant_type.value} grant proposal. Strictly align language with this style guide:
        {funder_lang}

        Use organization and funder context below. Ensure sections: Executive Summary, Statement of Need, Project Description, Goals & Objectives, Methodology, Timeline, Budget, Evaluation Plan, Sustainability, Expected Outcomes.

        Research Findings:
        {research_result.get('research_findings', '')}
        
        Organization Information:
        {json.dumps(task_context.organization_info, indent=2)}
        
        Funder Information:
        {json.dumps(task_context.funder_info, indent=2)}
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
        # DAO (Firestore if credentials present; else in-memory)
        try:
            self.dao = FirestoreDAO() if FIRESTORE_AVAILABLE else InMemoryDAO()
            logger.info("DAO initialized: %s", 'Firestore' if FIRESTORE_AVAILABLE else 'InMemory')
        except Exception as e:
            logger.warning("DAO init failed, falling back to InMemory: %s", e)
            self.dao = InMemoryDAO()
        
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
        allow_origins = os.getenv('CORS_ALLOW_ORIGINS', '*')
        origins = [o.strip() for o in allow_origins.split(',')] if allow_origins else ['*']
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        class RequestIDMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                rid = request.headers.get('x-request-id') or uuid.uuid4().hex
                request.state.request_id = rid
                t0 = time.time()
                response = await call_next(request)
                response.headers['X-Request-ID'] = rid
                t1 = time.time()
                try:
                    logger.info(json.dumps({"request_id": rid, "path": str(request.url.path), "latency_ms": round((t1 - t0) * 1000, 2)}))
                except Exception:
                    pass
                return response
        
        self.app.add_middleware(RequestIDMiddleware)
    
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
        
        
        @self.app.post("/proposals")
        async def create_proposal(req: Dict[str, Any], request: Request):
            try:
                # Validate/Create initial input
                initial = req.get('initialInput') or {}
                title = req.get('title') or initial.get('project', {}).get('title') or 'Draft Proposal'
                draft_id = _new_id('draft')
                sections = _canonical_sections(initial)
                draft = Draft(
                    id=draft_id,
                    title=title,
                    createdAt=_now_iso(),
                    updatedAt=_now_iso(),
                    initialInput=initial,
                    sections=sections,
                )
                await self.dao.create_draft(draft)
                log_info(request, "create_proposal", draft_id=draft_id)
                resp = JSONResponse({"success": True, "draft": json.loads(draft.json())})
                return resp
            except Exception as e:
                logger.error(json.dumps({"request_id": request_id, "error": str(e)}))
                raise HTTPException(status_code=500, detail="Failed to create proposal")

        @self.app.get("/proposals/{draft_id}")
        async def get_proposal(draft_id: str, request: Request):
            try:
                draft = await self.dao.get_draft(draft_id)
                if not draft:
                    raise HTTPException(status_code=404, detail="Draft not found")
                log_info(request, "get_proposal", draft_id=draft_id)
                resp = JSONResponse({"success": True, "draft": json.loads(draft.json())})
                return resp
            except HTTPException:
                raise
            except Exception as e:
                logger.error(json.dumps({"request_id": request_id, "error": str(e)}))
                raise HTTPException(status_code=500, detail="Failed to fetch draft")

        @self.app.post("/proposals/{draft_id}/comments")
        async def add_comments(draft_id: str, req: Dict[str, Any], request: Request):
            try:
                draft = await self.dao.get_draft(draft_id)
                if not draft:
                    raise HTTPException(status_code=404, detail="Draft not found")

                body = req or {}
                comments_input: List[Dict[str, Any]]
                if isinstance(body.get('comments'), list):
                    comments_input = body['comments']
                else:
                    comments_input = [body]

                prepared: List[Comment] = []
                now = _now_iso()
                for c in comments_input:
                    cid = c.get('id') or _new_id('c')
                    anchor_obj = c.get('anchor') or {
                        "startOffset": c.get('startOffset', 0),
                        "endOffset": c.get('endOffset', 0)
                    }
                    prepared.append(Comment(
                        id=cid,
                        draftId=draft_id,
                        sectionId=c.get('sectionId'),
                        anchor=Anchor(**anchor_obj),
                        text=c.get('text', ''),
                        author=c.get('author'),
                        resolved=bool(c.get('resolved', False)),
                        createdAt=now,
                    ))
                saved = await self.dao.add_comments(draft_id, prepared)
                log_info(request, "add_comments", draft_id=draft_id, count=len(saved))
                resp = JSONResponse({"success": True, "added": [s.dict() for s in saved]})
                return resp
            except HTTPException:
                raise
            except Exception as e:
                logger.error(json.dumps({"request_id": request_id, "error": str(e)}))
                raise HTTPException(status_code=500, detail="Failed to add comments")

        @self.app.get("/proposals/{draft_id}/comments")
        async def list_comments(draft_id: str, request: Request):
            try:
                draft = await self.dao.get_draft(draft_id)
                if not draft:
                    raise HTTPException(status_code=404, detail="Draft not found")
                comments = await self.dao.list_comments(draft_id)
                unresolved = [c for c in comments if not c.resolved]
                log_info(request, "list_comments", draft_id=draft_id, count=len(unresolved))
                resp = JSONResponse({"comments": [c.dict() for c in unresolved]})
                return resp
            except HTTPException:
                raise
            except Exception as e:
                logger.error(json.dumps({"request_id": request_id, "error": str(e)}))
                raise HTTPException(status_code=500, detail="Failed to list comments")

        @self.app.post("/proposals/{draft_id}/refine")
        async def refine(draft_id: str, req: Dict[str, Any], request: Request):
            try:
                changed_ids = req.get('changedSectionIds') or []
                comment_ids = req.get('commentIds')
                updated_sections, refinement_record = await refine_sections_helper(
                    dao=self.dao,
                    draft_id=draft_id,
                    changed_section_ids=changed_ids,
                    comment_ids=comment_ids,
                    generator=self.orchestrator.fast_model,
                )
                log_info(request, "refine", draft_id=draft_id, updated=[s.id for s in updated_sections])
                updated_map = {s.id: s.content for s in updated_sections}
                resp = JSONResponse({"success": True, "updatedSections": updated_map, "refinementId": refinement_record.id})
                return resp
            except HTTPException:
                raise
            except Exception as e:
                logger.error(json.dumps({"request_id": request_id, "error": str(e)}))
                raise HTTPException(status_code=500, detail="Failed to refine sections")

        @self.app.post("/import/document")
        async def import_document(file: UploadFile = File(...), request: Request):
            try:
                content_bytes = await file.read()
                text = await extract_text(content_bytes, filename=file.filename or "uploaded")
                fields = await extract_fields(text, generator=self.orchestrator.fast_model)
                # Optional insight prompt (3–7 questions) to guide user before prefill
                insight_questions: List[str] = []
                try:
                    if self.orchestrator and self.orchestrator.fast_model:
                        q_prompt = (
                            "Given the extracted fields for a grant draft, generate 3 to 7 short, specific questions "
                            "to clarify gaps. Return JSON array of strings only.\n"
                            f"Fields: {json.dumps(fields)[:1200]}"
                        )
                        data = await _safe_model_json_call(self.orchestrator.fast_model, q_prompt, schema_note='insight_questions')
                        if isinstance(data, list):
                            insight_questions = [str(x) for x in data][:7]
                        elif isinstance(data, dict) and isinstance(data.get('questions'), list):
                            insight_questions = [str(x) for x in data['questions']][:7]
                except Exception:
                    insight_questions = []
                proposed_sections = _canonical_sections({"project": fields.get("project", {}), "org": fields.get("org", {}), "funder": fields.get("funder", {})})
                log_info(request, "import_document", filename=file.filename, text_length=len(text))
                resp = JSONResponse({
                    "success": True,
                    "extracted": fields,
                    "suggestedSections": [s.dict() for s in proposed_sections],
                    "insightQuestions": insight_questions
                })
                return resp
            except Exception as e:
                logger.error(json.dumps({"request_id": request_id, "error": str(e)}))
                raise HTTPException(status_code=500, detail="Failed to import document")
        
        @self.app.post("/upload_documents")
        async def upload_documents(files: List[UploadFile] = File(...), request: Request):
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
                    
                    resp = JSONResponse({
                        "success": True,
                        "artifact_ids": artifact_ids,
                        "message": f"Uploaded {len(files)} documents successfully"
                    })
                    return resp
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
                            "upload_timestamp": datetime.now().isoformat()
                        }
                        
                        uploaded_documents.append(doc_metadata)
                        logger.info(f"Uploaded {file.filename} to GCS: {blob_name}")
                    
                    resp = JSONResponse({
                        "success": True,
                        "documents": uploaded_documents,
                        "message": f"Uploaded {len(files)} documents to cloud storage",
                        "storage_type": "gcs_direct"
                    })
                    return resp
                
            except Exception as e:
                logger.error(f"Error uploading documents: {e}")
                raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
        
        @self.app.get("/documents/{artifact_id}")
        async def get_document(artifact_id: str, request: Request):
            """Retrieve document metadata and content by artifact ID"""
            try:
                if self.artifact_service:
                    # Use AsyncArtifactService if available
                    metadata = await self.artifact_service.get_artifact_metadata(artifact_id)
                    if metadata:
                        md = metadata.dict()
                        md.pop('public_url', None)
                        return JSONResponse({
                            "success": True,
                            "metadata": md,
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
                            resp = JSONResponse({
                                "success": True,
                                "metadata": {
                                    "artifact_id": artifact_id,
                                    "filename": blob.name.split('/')[-1],
                                    "content_type": blob.content_type,
                                    "size_bytes": blob.size,
                                    "gcs_url": f"gs://{bucket_name}/{blob.name}",
                                    "created": blob.time_created.isoformat() if blob.time_created else None
                                },
                                "storage_type": "gcs_direct"
                            })
                            return resp
                    except Exception as e:
                        logger.error(f"Error retrieving document from GCS: {e}")
                
                raise HTTPException(status_code=404, detail="Document not found")
                
            except Exception as e:
                logger.error(f"Error retrieving document: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/generate_grant_proposal")
        async def generate_grant_proposal(request: Dict[str, Any], req: Request = None):
            """Generate grant proposal using MAS"""
            try:
                # Extract request parameters
                organization_info = request.get('organization_info', {})
                funder_info = request.get('funder_info', {})
                document_artifacts = request.get('document_artifacts', [])
                requirements = request.get('requirements', {})
                
                # Process through orchestrator
                task_id = f"grant_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
                result = await self.orchestrator.process_grant_request(
                    organization_info=organization_info,
                    funder_info=funder_info,
                    document_artifacts=document_artifacts,
                    requirements=requirements,
                    task_id=task_id
                )
                
                # Persist proposal metadata to Firestore if available
                try:
                    from google.cloud import firestore
                    db = firestore.Client()
                    doc_ref = db.collection('proposals').document(task_id)
                    # attempt to include GCS export reference if available from artifact service
                    export_ref = None
                    try:
                        if hasattr(self.artifact_service, 'last_export_gcs_path'):
                            export_ref = getattr(self.artifact_service, 'last_export_gcs_path')
                    except Exception:
                        export_ref = None

                    doc_ref.set({
                        'task_id': task_id,
                        'organization': organization_info,
                        'funder': funder_info,
                        'documents': document_artifacts,
                        'requirements': requirements,
                        'proposal': result,
                        'export_gcs_path': export_ref,
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.info('Saved proposal to Firestore: proposals/%s', task_id)
                except Exception as e:
                    logger.warning('Failed to save proposal to Firestore: %s', e)

                resp = JSONResponse({
                    "success": True,
                    "proposal": result,
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat()
                })
                return resp
                
            except Exception as e:
                logger.error(f"Error generating proposal: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/quick_proposal")
        async def quick_proposal(data: Dict[str, Any]):
            """Quick proposal generation with minimal input"""
            logger.info(f"🚀 Quick Proposal Request Started - MAS Version")
            logger.info(f"📊 Input data: {data}")
            
            try:
                # Feature flag: quick proposal can be disabled in production
                if os.getenv('ENABLE_QUICK_PROPOSAL', 'true').lower() != 'true':
                    raise HTTPException(status_code=403, detail='Quick proposal feature is disabled')

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
                
                resp = JSONResponse({
                    "success": True,
                    "proposal": proposal,
                    "timestamp": datetime.now().isoformat()
                })
                return resp
                
            except Exception as e:
                logger.error(f"❌ Error in quick proposal: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/full_proposal")
        async def full_proposal(data: Dict[str, Any]):
            """Full comprehensive proposal generation using MAS"""
            logger.info(f"🚀 Full Proposal Request Started - MAS Version")
            
            try:
                # Extract comprehensive data
                # accept both shapes: legacy and current client
                organization_info = data.get('organizationData') or data.get('organization') or {}
                funder_info = data.get('funderData') or data.get('funder') or {}
                project_data = data.get('projectData') or data.get('project') or {}
                documents = data.get('uploadedFiles') or data.get('documents') or []
                
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
                
                resp = JSONResponse({
                    "success": True,
                    "proposal": proposal,
                    "timestamp": datetime.now().isoformat(),
                    "summary": project_data.get('summary') or None,
                    "grade": None,
                    "mode": "full_comprehensive_mas"
                })
                return resp
                
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