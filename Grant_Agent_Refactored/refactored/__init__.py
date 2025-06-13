"""
Refactored Grant Agent Package
Clean, coordinated grant writing workflow
"""

from .models import (
    GrantWorkflowData, WorkflowResult, DocumentData, DocumentType,
    OrganizationInfo, FunderInfo, LanguageAnalysis, WorkflowStatus
)

from .services import (
    DocumentService, ExtractionService, LanguageAnalysisService
)

from .workflow_engine import (
    WorkflowEngine, WorkflowStage, ConflictResolver
)

# ADK integration is optional for testing
try:
    from .adk_integration import (
        RefactoredGrantAgent, create_grant_agent
    )
    _has_adk = True
except ImportError:
    _has_adk = False
    def create_grant_agent():
        raise ImportError("google-adk package required for full functionality")

__version__ = "2.0.0"
__all__ = [
    # Core models
    'GrantWorkflowData',
    'WorkflowResult', 
    'DocumentData',
    'DocumentType',
    'OrganizationInfo',
    'FunderInfo',
    'LanguageAnalysis',
    'WorkflowStatus',
    
    # Services
    'DocumentService',
    'ExtractionService', 
    'LanguageAnalysisService',
    
    # Workflow engine
    'WorkflowEngine',
    'WorkflowStage',
    'ConflictResolver'
]

# Add ADK components if available
if _has_adk:
    __all__.extend(['create_grant_agent', 'RefactoredGrantAgent']) 