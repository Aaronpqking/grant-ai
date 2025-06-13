"""
Refactored Grant Agent - Core Data Models
Single source of truth for all workflow data
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import hashlib


class DocumentType(Enum):
    ORGANIZATION = "organization"
    FUNDER = "funder"
    SUPPORTING_EVIDENCE = "supporting_evidence"
    FINANCIAL_DETAIL = "financial_detail"
    PARTNERSHIP_INFO = "partnership_info"
    UNKNOWN = "unknown"


class WorkflowStatus(Enum):
    INITIALIZED = "initialized"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    EXTRACTION_COMPLETE = "extraction_complete"
    ANALYSIS_COMPLETE = "analysis_complete"
    NARRATIVE_GENERATED = "narrative_generated"
    DOCUMENT_CREATED = "document_created"
    COMPLETED = "completed"
    ERROR = "error"


class ConflictResolution(Enum):
    REPLACE = "replace"
    MERGE = "merge"
    USER_CHOICE = "user_choice"
    PRESERVE = "preserve"


@dataclass
class ContactInfo:
    name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""


@dataclass
class FinancialInfo:
    annual_budget: float = 0.0
    funding_sources: List[str] = field(default_factory=list)
    revenue_streams: List[str] = field(default_factory=list)


@dataclass
class DocumentData:
    content: str
    filename: str
    mime_type: str
    uploaded_at: datetime
    content_hash: str
    document_type: DocumentType = DocumentType.UNKNOWN
    
    @classmethod
    def create(cls, content: str, filename: str, mime_type: str, file_data: bytes = None):
        """Factory method to create DocumentData with hash"""
        if file_data:
            content_hash = hashlib.sha256(file_data).hexdigest()[:8]
        else:
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
            
        return cls(
            content=content,
            filename=filename,
            mime_type=mime_type,
            uploaded_at=datetime.now(),
            content_hash=content_hash
        )


@dataclass
class OrganizationInfo:
    name: str = ""
    mission: str = ""
    background: str = ""
    contact_info: ContactInfo = field(default_factory=ContactInfo)
    financials: FinancialInfo = field(default_factory=FinancialInfo)
    leadership: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    target_population: str = ""
    location: str = ""
    
    def is_complete(self) -> bool:
        """Check if organization info has minimum required data"""
        return bool(self.name and self.mission and self.background)


@dataclass
class FunderInfo:
    name: str = ""
    grant_amount: int = 0
    eligibility_criteria: List[str] = field(default_factory=list)
    funding_priorities: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    funding_type: str = ""
    deadline: Optional[datetime] = None
    
    def is_complete(self) -> bool:
        """Check if funder info has minimum required data"""
        return bool(self.name and self.grant_amount and self.funding_priorities)


@dataclass
class LanguageAnalysis:
    alignment_score: float = 0.0
    matching_themes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_areas: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class DataConflict:
    field_name: str
    existing_value: Any
    new_value: Any
    resolution_strategy: ConflictResolution
    user_choice: Optional[str] = None


@dataclass
class WorkflowSnapshot:
    id: str
    data: 'GrantWorkflowData'
    created_at: datetime
    reason: str


@dataclass
class GrantWorkflowData:
    """Complete workflow data model - single source of truth"""
    documents: Dict[str, DocumentData] = field(default_factory=dict)
    organization: Optional[OrganizationInfo] = None
    funder: Optional[FunderInfo] = None
    language_analysis: Optional[LanguageAnalysis] = None
    narrative: Optional[str] = None
    final_document: Optional[bytes] = None
    status: WorkflowStatus = WorkflowStatus.INITIALIZED
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    
    def add_document(self, doc_data: DocumentData) -> None:
        """Add document with automatic deduplication"""
        self.documents[doc_data.content_hash] = doc_data
        self.last_modified = datetime.now()
        if self.status == WorkflowStatus.INITIALIZED:
            self.status = WorkflowStatus.DOCUMENTS_UPLOADED
    
    def get_documents_by_type(self, doc_type: DocumentType) -> List[DocumentData]:
        """Get all documents of specific type"""
        return [doc for doc in self.documents.values() if doc.document_type == doc_type]
    
    def is_stage_ready(self, stage_name: str) -> bool:
        """Check if stage has required inputs"""
        requirements = {
            "extraction": lambda: bool(self.documents),
            "analysis": lambda: bool(self.organization and self.funder),
            "generation": lambda: bool(self.organization and self.funder),
            "finalization": lambda: bool(self.narrative)
        }
        return requirements.get(stage_name, lambda: False)()
    
    def add_error(self, error_message: str) -> None:
        """Add error to workflow"""
        self.errors.append(f"{datetime.now().isoformat()}: {error_message}")
        self.status = WorkflowStatus.ERROR


@dataclass
class VersionedWorkflowData:
    """Track workflow changes over time"""
    current: GrantWorkflowData
    versions: List[WorkflowSnapshot] = field(default_factory=list)
    
    def create_snapshot(self, reason: str) -> str:
        """Create snapshot before major changes"""
        import copy
        import time
        
        snapshot_id = f"v{len(self.versions) + 1}_{int(time.time())}"
        snapshot = WorkflowSnapshot(
            id=snapshot_id,
            data=copy.deepcopy(self.current),
            created_at=datetime.now(),
            reason=reason
        )
        self.versions.append(snapshot)
        return snapshot_id
    
    def rollback_to_snapshot(self, snapshot_id: str) -> bool:
        """Allow users to undo changes"""
        import copy
        
        for snapshot in self.versions:
            if snapshot.id == snapshot_id:
                self.current = copy.deepcopy(snapshot.data)
                return True
        return False


@dataclass
class ExtractionResult:
    """Result of extraction process"""
    organization: Optional[OrganizationInfo] = None
    funder: Optional[FunderInfo] = None
    success: bool = False
    errors: List[str] = field(default_factory=list)
    extracted_from: List[str] = field(default_factory=list)


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    data: GrantWorkflowData
    success: bool
    stage_completed: str
    next_stage: Optional[str] = None
    conflicts: List[DataConflict] = field(default_factory=list)
    state_changes: Dict[str, Any] = field(default_factory=dict)
    artifact_changes: Dict[str, Any] = field(default_factory=dict)
    
    def has_conflicts(self) -> bool:
        """Check if there are unresolved conflicts"""
        return bool(self.conflicts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for session state"""
        return {
            "workflow_data": self.data,
            "success": self.success,
            "stage_completed": self.stage_completed,
            "next_stage": self.next_stage,
            "has_conflicts": self.has_conflicts()
        }


@dataclass
class ReprocessPlan:
    """Plan for incremental reprocessing"""
    steps: List[tuple] = field(default_factory=list)  # (step_name, conflict_resolution)
    
    def add_step(self, step_name: str, conflict_resolution: ConflictResolution = ConflictResolution.REPLACE):
        """Add processing step"""
        self.steps.append((step_name, conflict_resolution))
    
    def has_extraction_changes(self) -> bool:
        """Check if extraction will change"""
        extraction_steps = ["extract_organization_info", "extract_funder_info", "merge_organization_info", "merge_funder_info"]
        return any(step[0] in extraction_steps for step in self.steps)


# Exception classes
class ExtractionError(Exception):
    """Raised when extraction fails"""
    pass


class WorkflowError(Exception):
    """Raised when workflow execution fails"""
    pass


class ConflictResolutionError(Exception):
    """Raised when conflict resolution fails"""
    pass 