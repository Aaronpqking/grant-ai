"""
Refactored Grant Agent - Workflow Engine
Orchestrated stages with dependency injection and deterministic execution
"""

import logging
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type
from datetime import datetime

from .models import (
    GrantWorkflowData, WorkflowResult, WorkflowStatus, DocumentData,
    ExtractionResult, LanguageAnalysis, DataConflict, ConflictResolution,
    WorkflowError, OrganizationInfo, FunderInfo
)
from .services import (
    DocumentService, ExtractionService, LanguageAnalysisService
)

logger = logging.getLogger(__name__)


class WorkflowStage(ABC):
    """Abstract base class for workflow stages"""
    
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.logger = logging.getLogger(f"{__name__}.{stage_name}")
    
    @abstractmethod
    def can_execute(self, workflow_data: GrantWorkflowData) -> bool:
        """Check if stage can execute with current data"""
        pass
    
    @abstractmethod
    def execute(self, workflow_data: GrantWorkflowData, context: Dict[str, Any]) -> WorkflowResult:
        """Execute the stage"""
        pass
    
    def create_result(self, workflow_data: GrantWorkflowData, success: bool, 
                     next_stage: Optional[str] = None) -> WorkflowResult:
        """Helper to create workflow result"""
        return WorkflowResult(
            data=workflow_data,
            success=success,
            stage_completed=self.stage_name,
            next_stage=next_stage
        )


class DocumentProcessingStage(WorkflowStage):
    """Stage 1: Process uploaded documents"""
    
    def __init__(self, document_service: DocumentService):
        super().__init__("document_processing")
        self.document_service = document_service
    
    def can_execute(self, workflow_data: GrantWorkflowData) -> bool:
        """Can always execute - handles empty document state"""
        return True
    
    def execute(self, workflow_data: GrantWorkflowData, context: Dict[str, Any]) -> WorkflowResult:
        """Process any new documents from context"""
        try:
            # Get file uploads from context
            file_uploads = context.get('file_uploads', [])
            
            for file_data, filename, mime_type in file_uploads:
                # Process document
                doc_data = self.document_service.process_upload(file_data, filename, mime_type)
                
                # Add to workflow
                workflow_data.add_document(doc_data)
                self.logger.info(f"Processed document: {filename}")
            
            # Determine next stage
            next_stage = "data_extraction" if workflow_data.documents else None
            
            return self.create_result(workflow_data, True, next_stage)
            
        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            workflow_data.add_error(f"Document processing failed: {e}")
            return self.create_result(workflow_data, False)


class DataExtractionStage(WorkflowStage):
    """Stage 2: Extract structured data from documents"""
    
    def __init__(self, extraction_service: ExtractionService):
        super().__init__("data_extraction")
        self.extraction_service = extraction_service
    
    def can_execute(self, workflow_data: GrantWorkflowData) -> bool:
        """Requires documents to be present"""
        return bool(workflow_data.documents)
    
    def execute(self, workflow_data: GrantWorkflowData, context: Dict[str, Any]) -> WorkflowResult:
        """Extract organization and funder information"""
        try:
            # Extract data from all documents
            extraction_result = self.extraction_service.extract_all(workflow_data)
            
            if not extraction_result.success:
                workflow_data.add_error("Extraction failed: " + "; ".join(extraction_result.errors))
                return self.create_result(workflow_data, False)
            
            # Handle conflicts if data already exists
            conflicts = []
            
            # Check organization conflicts
            if extraction_result.organization:
                if workflow_data.organization:
                    conflicts.extend(self._detect_organization_conflicts(
                        workflow_data.organization, extraction_result.organization
                    ))
                else:
                    workflow_data.organization = extraction_result.organization
                    workflow_data.status = WorkflowStatus.EXTRACTION_COMPLETE
            
            # Check funder conflicts
            if extraction_result.funder:
                if workflow_data.funder:
                    conflicts.extend(self._detect_funder_conflicts(
                        workflow_data.funder, extraction_result.funder
                    ))
                else:
                    workflow_data.funder = extraction_result.funder
                    workflow_data.status = WorkflowStatus.EXTRACTION_COMPLETE
            
            # Create result
            result = self.create_result(workflow_data, True, "language_analysis")
            result.conflicts = conflicts
            
            self.logger.info(f"Extraction complete. Conflicts: {len(conflicts)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Data extraction failed: {e}")
            workflow_data.add_error(f"Data extraction failed: {e}")
            return self.create_result(workflow_data, False)
    
    def _detect_organization_conflicts(self, existing: OrganizationInfo, 
                                     new: OrganizationInfo) -> List[DataConflict]:
        """Detect conflicts in organization info"""
        conflicts = []
        
        # Check name conflict
        if existing.name != new.name and both_non_empty(existing.name, new.name):
            conflicts.append(DataConflict(
                field_name="organization.name",
                existing_value=existing.name,
                new_value=new.name,
                resolution_strategy=ConflictResolution.USER_CHOICE
            ))
        
        # Check mission conflict
        if existing.mission != new.mission and both_non_empty(existing.mission, new.mission):
            conflicts.append(DataConflict(
                field_name="organization.mission",
                existing_value=existing.mission,
                new_value=new.mission,
                resolution_strategy=ConflictResolution.MERGE
            ))
        
        return conflicts
    
    def _detect_funder_conflicts(self, existing: FunderInfo, 
                               new: FunderInfo) -> List[DataConflict]:
        """Detect conflicts in funder info"""
        conflicts = []
        
        # Check name conflict
        if existing.name != new.name and both_non_empty(existing.name, new.name):
            conflicts.append(DataConflict(
                field_name="funder.name",
                existing_value=existing.name,
                new_value=new.name,
                resolution_strategy=ConflictResolution.USER_CHOICE
            ))
        
        # Check amount conflict
        if existing.grant_amount != new.grant_amount and both_non_zero(existing.grant_amount, new.grant_amount):
            conflicts.append(DataConflict(
                field_name="funder.grant_amount",
                existing_value=existing.grant_amount,
                new_value=new.grant_amount,
                resolution_strategy=ConflictResolution.USER_CHOICE
            ))
        
        return conflicts


class LanguageAnalysisStage(WorkflowStage):
    """Stage 3: Analyze language alignment"""
    
    def __init__(self, analysis_service: LanguageAnalysisService):
        super().__init__("language_analysis")
        self.analysis_service = analysis_service
    
    def can_execute(self, workflow_data: GrantWorkflowData) -> bool:
        """Requires both organization and funder info"""
        return (workflow_data.organization and 
                workflow_data.organization.is_complete() and
                workflow_data.funder and 
                workflow_data.funder.is_complete())
    
    def execute(self, workflow_data: GrantWorkflowData, context: Dict[str, Any]) -> WorkflowResult:
        """Analyze language alignment between org and funder"""
        try:
            # Perform analysis
            analysis = self.analysis_service.analyze_alignment(
                workflow_data.organization, 
                workflow_data.funder
            )
            
            workflow_data.language_analysis = analysis
            workflow_data.status = WorkflowStatus.ANALYSIS_COMPLETE
            
            self.logger.info(f"Language analysis complete. Score: {analysis.alignment_score:.2f}")
            return self.create_result(workflow_data, True, "narrative_generation")
            
        except Exception as e:
            self.logger.error(f"Language analysis failed: {e}")
            workflow_data.add_error(f"Language analysis failed: {e}")
            return self.create_result(workflow_data, False)


class NarrativeGenerationStage(WorkflowStage):
    """Stage 4: Generate grant narrative"""
    
    def __init__(self, llm_service):
        super().__init__("narrative_generation")
        self.llm_service = llm_service
    
    def can_execute(self, workflow_data: GrantWorkflowData) -> bool:
        """Requires analysis to be complete"""
        return (workflow_data.language_analysis is not None and
                workflow_data.organization and workflow_data.funder)
    
    def execute(self, workflow_data: GrantWorkflowData, context: Dict[str, Any]) -> WorkflowResult:
        """Generate narrative using LLM"""
        try:
            # Build prompt
            prompt = self._build_narrative_prompt(workflow_data)
            
            # Generate narrative
            narrative = self.llm_service.generate_text(prompt)
            
            workflow_data.narrative = narrative
            workflow_data.status = WorkflowStatus.NARRATIVE_GENERATED
            
            self.logger.info("Narrative generation complete")
            return self.create_result(workflow_data, True, "document_creation")
            
        except Exception as e:
            self.logger.error(f"Narrative generation failed: {e}")
            workflow_data.add_error(f"Narrative generation failed: {e}")
            return self.create_result(workflow_data, False)
    
    def _build_narrative_prompt(self, workflow_data: GrantWorkflowData) -> str:
        """Build comprehensive prompt for narrative generation"""
        org = workflow_data.organization
        funder = workflow_data.funder
        analysis = workflow_data.language_analysis
        
        prompt = f"""
Generate a compelling grant proposal narrative based on the following information:

ORGANIZATION INFORMATION:
Name: {org.name}
Mission: {org.mission}
Background: {org.background}
Location: {org.location}

FUNDER INFORMATION:
Name: {funder.name}
Grant Amount: ${funder.grant_amount:,}
Funding Type: {funder.funding_type}
Funding Priorities: {', '.join(funder.funding_priorities)}

LANGUAGE ANALYSIS:
Alignment Score: {analysis.alignment_score:.2f}
Matching Themes: {', '.join(analysis.matching_themes)}
Recommendations: {'; '.join(analysis.recommendations)}

Please create a professional grant proposal narrative that:
1. Clearly articulates the organization's mission and impact
2. Demonstrates strong alignment with funder priorities
3. Emphasizes the matching themes identified
4. Follows grant writing best practices
5. Is approximately 500-800 words

Focus on outcomes, community impact, and how the funding will advance both the organization's mission and the funder's priorities.
"""
        return prompt


class DocumentCreationStage(WorkflowStage):
    """Stage 5: Create final grant document"""
    
    def __init__(self, document_generator):
        super().__init__("document_creation")
        self.document_generator = document_generator
    
    def can_execute(self, workflow_data: GrantWorkflowData) -> bool:
        """Requires narrative to be generated"""
        return bool(workflow_data.narrative)
    
    def execute(self, workflow_data: GrantWorkflowData, context: Dict[str, Any]) -> WorkflowResult:
        """Create final DOCX document"""
        try:
            # Generate document
            doc_bytes = self.document_generator.create_grant_document(
                workflow_data.organization,
                workflow_data.funder,
                workflow_data.narrative
            )
            
            workflow_data.final_document = doc_bytes
            workflow_data.status = WorkflowStatus.COMPLETED
            
            self.logger.info("Document creation complete")
            return self.create_result(workflow_data, True, None)
            
        except Exception as e:
            self.logger.error(f"Document creation failed: {e}")
            workflow_data.add_error(f"Document creation failed: {e}")
            return self.create_result(workflow_data, False)


class WorkflowEngine:
    """Main workflow orchestration engine"""
    
    def __init__(self):
        self.stages: Dict[str, WorkflowStage] = {}
        self.stage_order = []
        self.logger = logging.getLogger(__name__)
    
    def register_stage(self, stage: WorkflowStage) -> None:
        """Register a workflow stage"""
        self.stages[stage.stage_name] = stage
        self.stage_order.append(stage.stage_name)
        self.logger.info(f"Registered stage: {stage.stage_name}")
    
    def execute_workflow(self, workflow_data: GrantWorkflowData, 
                        context: Dict[str, Any]) -> WorkflowResult:
        """Execute complete workflow or resume from current state"""
        try:
            # Determine starting stage
            start_stage = self._determine_start_stage(workflow_data, context)
            
            current_data = workflow_data
            current_stage = start_stage
            
            while current_stage:
                self.logger.info(f"Executing stage: {current_stage}")
                
                stage = self.stages.get(current_stage)
                if not stage:
                    raise WorkflowError(f"Unknown stage: {current_stage}")
                
                # Check if stage can execute
                if not stage.can_execute(current_data):
                    self.logger.warning(f"Stage {current_stage} cannot execute with current data")
                    break
                
                # Execute stage
                result = stage.execute(current_data, context)
                current_data = result.data
                
                # Handle conflicts
                if result.has_conflicts():
                    self.logger.info(f"Stage {current_stage} has conflicts - requires user resolution")
                    return result
                
                # Check for failure
                if not result.success:
                    self.logger.error(f"Stage {current_stage} failed")
                    return result
                
                # Move to next stage
                current_stage = result.next_stage
                
                # Update context for next stage
                context['previous_stage'] = stage.stage_name
            
            # Create final result
            final_result = WorkflowResult(
                data=current_data,
                success=True,
                stage_completed="workflow_complete",
                next_stage=None
            )
            
            self.logger.info("Workflow execution complete")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            workflow_data.add_error(f"Workflow execution failed: {e}")
            return WorkflowResult(
                data=workflow_data,
                success=False,
                stage_completed="error",
                next_stage=None
            )
    
    def _determine_start_stage(self, workflow_data: GrantWorkflowData, 
                             context: Dict[str, Any]) -> str:
        """Determine where to start workflow based on current state"""
        # If context has file uploads, start with document processing
        if context.get('file_uploads'):
            return "document_processing"
        
        # Otherwise, determine based on current data state
        if not workflow_data.documents:
            return "document_processing"
        elif not workflow_data.organization or not workflow_data.funder:
            return "data_extraction"
        elif not workflow_data.language_analysis:
            return "language_analysis"
        elif not workflow_data.narrative:
            return "narrative_generation"
        elif not workflow_data.final_document:
            return "document_creation"
        else:
            # Workflow already complete
            return None
    
    def get_workflow_status(self, workflow_data: GrantWorkflowData) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "status": workflow_data.status.value,
            "documents_count": len(workflow_data.documents),
            "has_organization": workflow_data.organization is not None,
            "has_funder": workflow_data.funder is not None,
            "has_analysis": workflow_data.language_analysis is not None,
            "has_narrative": workflow_data.narrative is not None,
            "has_final_document": workflow_data.final_document is not None,
            "errors": len(workflow_data.errors),
            "last_modified": workflow_data.last_modified.isoformat()
        }


class ConflictResolver:
    """Handle data conflicts during workflow execution"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def resolve_conflicts(self, workflow_data: GrantWorkflowData, 
                         conflicts: List[DataConflict]) -> GrantWorkflowData:
        """Resolve list of conflicts based on their resolution strategies"""
        for conflict in conflicts:
            self._resolve_single_conflict(workflow_data, conflict)
        
        return workflow_data
    
    def _resolve_single_conflict(self, workflow_data: GrantWorkflowData, 
                               conflict: DataConflict) -> None:
        """Resolve a single conflict"""
        if conflict.resolution_strategy == ConflictResolution.REPLACE:
            self._apply_value(workflow_data, conflict.field_name, conflict.new_value)
        
        elif conflict.resolution_strategy == ConflictResolution.MERGE:
            merged_value = self._merge_values(conflict.existing_value, conflict.new_value)
            self._apply_value(workflow_data, conflict.field_name, merged_value)
        
        elif conflict.resolution_strategy == ConflictResolution.USER_CHOICE:
            # Use user's choice if provided, otherwise keep existing
            value = conflict.user_choice if conflict.user_choice else conflict.existing_value
            self._apply_value(workflow_data, conflict.field_name, value)
        
        elif conflict.resolution_strategy == ConflictResolution.PRESERVE:
            # Keep existing value - no action needed
            pass
    
    def _apply_value(self, workflow_data: GrantWorkflowData, field_path: str, value: Any) -> None:
        """Apply value to nested field path"""
        parts = field_path.split('.')
        obj = workflow_data
        
        # Navigate to parent object
        for part in parts[:-1]:
            obj = getattr(obj, part)
        
        # Set final value
        setattr(obj, parts[-1], value)
    
    def _merge_values(self, existing: Any, new: Any) -> Any:
        """Merge two values intelligently"""
        if isinstance(existing, str) and isinstance(new, str):
            # For strings, combine if different
            if existing.lower() != new.lower():
                return f"{existing}. {new}"
            return existing
        
        elif isinstance(existing, list) and isinstance(new, list):
            # For lists, merge uniquely
            combined = existing.copy()
            for item in new:
                if item not in combined:
                    combined.append(item)
            return combined
        
        else:
            # For other types, prefer new value
            return new


# Utility functions
def both_non_empty(val1: str, val2: str) -> bool:
    """Check if both values are non-empty strings"""
    return bool(val1 and val1.strip() and val2 and val2.strip())


def both_non_zero(val1: float, val2: float) -> bool:
    """Check if both values are non-zero numbers"""
    return bool(val1 and val2 and val1 != 0 and val2 != 0) 