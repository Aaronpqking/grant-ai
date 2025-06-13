"""
Grant Agent - Tool functions for document parsing, extraction, and narrative generation.

These tools handle the core functionality of the Grant Agent system:
1. Parsing and extracting content from various document formats
2. Matching language between organization and funder
3. Tracking required attachments
4. Generating grant narratives using templates
"""

import os
import logging
import json
import tempfile
from pathlib import Path
import asyncio
from typing import Dict, List, Any, Optional, Union
import glob
from datetime import datetime
from .schema import (
    GrantSchema, OrganizationInfo, FunderInfo, GrantNarrative, 
    GrantSection, LogicModel, EvaluationPlan, AttachmentInfo
)
from .parsers import DocxParser, PDFParser, PPTXParser, LogicModelExtractor, EvaluationPlanExtractor
from .matchers import FunderLanguageMatcher, CSRKeywordExtractor
from .trackers import AttachmentTracker
from .renderers import Jinja2Renderer, ReportAssembler
from google.adk.tools import ToolContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default directories
DEFAULT_INPUT_DIR = os.environ.get('GRANT_AGENT_INPUT_DIR', './input')
DEFAULT_OUTPUT_DIR = os.environ.get('GRANT_AGENT_OUTPUT_DIR', './output')
DEFAULT_TEMPLATES_DIR = os.environ.get('GRANT_AGENT_TEMPLATES_DIR', './templates')

# --- Context Compatibility Helper ---

def ensure_context_state(ctx: ToolContext) -> Dict[str, Any]:
    """
    Ensure that the context has a state attribute.
    
    This helper function enables compatibility between different versions
    of the ADK ToolContext, which might structure state differently.
    
    Args:
        ctx: The ToolContext object
        
    Returns:
        A dictionary that can be used to store state
    """
    # If the context has session.state (standard ADK structure)
    if hasattr(ctx, 'session') and hasattr(ctx.session, 'state'):
        return ctx.session.state
    
    # If the context already has a state attribute (our mock context)
    if hasattr(ctx, 'state'):
        return ctx.state
    
    # Create a state attribute if none exists
    ctx.state = {}
    return ctx.state

# --- Document Parsing Tools ---

async def parse_docx_content(ctx: ToolContext, file_path: str) -> Dict[str, Any]:
    """
    Parse a Word document (.docx) and extract its content
    
    Args:
        ctx: Tool context for storing state
        file_path: Path to the .docx file
        
    Returns:
        Dict containing the parsed content
    """
    # Resolve path if relative
    if not os.path.isabs(file_path):
        file_path = os.path.join(DEFAULT_INPUT_DIR, file_path)
    
    # Check file existence first
    if not os.path.exists(file_path):
        return {
            "status": "error",
            "message": f"File not found: {file_path}"
        }
    
    # Check if this is a text file (for testing)
    _, ext = os.path.splitext(file_path)
    if ext.lower() == '.txt':
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Create a simple result structure
            result = {
                "status": "success",
                "content": content,
                "paragraphs": [{"text": para.strip()} for para in content.split('\n\n') if para.strip()],
                "metadata": {"title": os.path.basename(file_path)}
            }
            
            # Extract sections from markdown-style headings
            sections = {}
            current_section = None
            section_content = []
            
            for line in content.split('\n'):
                if line.startswith('#'):
                    # Save previous section if any
                    if current_section and section_content:
                        sections[current_section] = '\n'.join(section_content)
                        section_content = []
                    
                    # Extract new section name
                    current_section = line.strip('#').strip()
                else:
                    if current_section:
                        section_content.append(line)
            
            # Save last section
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content)
            
            result["sections"] = sections
            
            # Store in session state
            ctx.session.state["docx_content"] = result
            
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to parse text file: {str(e)}"
            }
    
    # Parse the document
    result = DocxParser.parse(file_path)
    
    # Store result in session state if successful
    if result["status"] == "success":
        ctx.session.state["docx_content"] = result
    
    return result


async def parse_pdf_questions(ctx: ToolContext, file_path: str = None, artifact_filename: str = None, artifact_version: int = None) -> Dict[str, Any]:
    """
    Parse a PDF document and extract questions/sections, supporting artifact-centric flow.
    
    Args:
        ctx: Tool context
        file_path: Path to the PDF file (legacy fallback)
        artifact_filename: Artifact filename (preferred)
        artifact_version: Artifact version (optional)
    
    Returns:
        Dict containing extracted questions and content
    """
    import tempfile
    import os
    from .parsers import PDFParser
    
    # Prefer artifact-centric processing
    if artifact_filename:
        artifact_part = ctx.load_artifact(filename=artifact_filename, version=artifact_version)
        if artifact_part and artifact_part.inline_data:
            # Write artifact bytes to a temp file for legacy parser compatibility
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(artifact_part.inline_data.data)
                tmp_path = tmp.name
            try:
                result = PDFParser.parse(tmp_path)
            finally:
                os.remove(tmp_path)
            # Store artifact metadata in state
            ctx.session.state['pdf_content'] = result
            ctx.session.state['pdf_content_artifact'] = {
                'artifact_filename': artifact_filename,
                'artifact_version': artifact_version
            }
            return result
        else:
            return {"status": "error", "message": "Artifact not found or invalid."}
    # Fallback to file path
    if file_path:
        if not os.path.isabs(file_path):
            file_path = os.path.join(DEFAULT_INPUT_DIR, file_path)
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found: {file_path}"}
        result = PDFParser.parse(file_path)
        ctx.session.state['pdf_content'] = result
        return result
    return {"status": "error", "message": "No valid input provided."}


async def parse_pptx_content(ctx: ToolContext, file_path: str) -> Dict[str, Any]:
    """
    Parse a PowerPoint presentation (.pptx) and extract its content
    
    Args:
        ctx: Tool context
        file_path: Path to the .pptx file
        
    Returns:
        Dict containing the parsed content
    """
    # Resolve path if relative
    if not os.path.isabs(file_path):
        file_path = os.path.join(DEFAULT_INPUT_DIR, file_path)
    
    # Parse the document
    result = PPTXParser.parse(file_path)
    
    # Store result in session state if successful
    if result["status"] == "success":
        ctx.session.state["pptx_content"] = result
    
    return result


async def extract_logic_model_json(ctx: ToolContext, file_path: str) -> Dict[str, Any]:
    """
    Extract a logic model from a document and convert to JSON
    
    Args:
        ctx: Tool context
        file_path: Path to the document containing a logic model
        
    Returns:
        Dict containing the extracted logic model
    """
    # Resolve path if relative
    if not os.path.isabs(file_path):
        file_path = os.path.join(DEFAULT_INPUT_DIR, file_path)
    
    # Determine file type by extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    logic_model = None
    if ext == '.docx':
        logic_model = LogicModelExtractor.extract_from_docx(file_path)
    elif ext == '.pdf':
        logic_model = LogicModelExtractor.extract_from_pdf(file_path)
    else:
        return {
            "status": "error",
            "message": f"Unsupported file type: {ext}. Must be .docx or .pdf"
        }
    
    if logic_model is None:
        return {
            "status": "error",
            "message": f"No logic model found in {file_path}"
        }
    
    # Convert to dict for JSON serialization
    logic_model_dict = logic_model.model_dump()
    
    # Store in session state
    ctx.session.state["logic_model"] = logic_model_dict
    
    return {
        "status": "success",
        "logic_model": logic_model_dict
    }


async def extract_evaluation_plan(ctx: ToolContext, file_path: str) -> Dict[str, Any]:
    """
    Extract an evaluation plan from a document
    
    Args:
        ctx: Tool context
        file_path: Path to the document containing an evaluation plan
        
    Returns:
        Dict containing the extracted evaluation plan
    """
    # Resolve path if relative
    if not os.path.isabs(file_path):
        file_path = os.path.join(DEFAULT_INPUT_DIR, file_path)
    
    # Determine file type by extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    eval_plan = None
    if ext == '.docx':
        eval_plan = EvaluationPlanExtractor.extract_from_docx(file_path)
    else:
        return {
            "status": "error",
            "message": f"Unsupported file type: {ext}. Must be .docx"
        }
    
    if eval_plan is None:
        return {
            "status": "error",
            "message": f"No evaluation plan found in {file_path}"
        }
    
    # Convert to dict for JSON serialization
    eval_plan_dict = eval_plan.model_dump()
    
    # Store in session state
    ctx.session.state["evaluation_plan"] = eval_plan_dict
    
    return {
        "status": "success",
        "evaluation_plan": eval_plan_dict
    }


async def match_language_to_keywords(ctx: ToolContext, base_text: str, funder_doc: str) -> Dict[str, Any]:
    """
    Match language from an organization to funder keywords and priorities
    
    Args:
        ctx: Tool context
        base_text: Organization text (mission, boilerplate, etc.)
        funder_doc: Funder text (guidelines, CSR report, etc.)
        
    Returns:
        Dict with matches, keywords, and recommendations
    """
    # Match language
    result = FunderLanguageMatcher.match_language_to_keywords(base_text, funder_doc)
    
    # Store result in session state if successful
    if result["status"] == "success":
        ctx.session.state["language_matching"] = result
    
    return result


async def extract_csr_priorities(ctx: ToolContext, file_path: str) -> Dict[str, Any]:
    """
    Extract priorities and keywords from a CSR report
    
    Args:
        ctx: Tool context
        file_path: Path to the CSR report
        
    Returns:
        Dict with extracted priorities and keywords
    """
    # Resolve path if relative
    if not os.path.isabs(file_path):
        file_path = os.path.join(DEFAULT_INPUT_DIR, file_path)
    
    # Parse the document first to get text content
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    text_content = ""
    if ext == '.pdf':
        pdf_result = PDFParser.parse(file_path)
        if pdf_result["status"] == "success" and "pages" in pdf_result:
            text_content = "\n\n".join([page["text"] for page in pdf_result["pages"]])
    elif ext == '.docx':
        docx_result = DocxParser.parse(file_path)
        if docx_result["status"] == "success" and "paragraphs" in docx_result:
            text_content = "\n\n".join([para["text"] for para in docx_result["paragraphs"]])
    else:
        return {
            "status": "error",
            "message": f"Unsupported file type: {ext}. Must be .pdf or .docx"
        }
    
    if not text_content:
        return {
            "status": "error",
            "message": f"Could not extract text content from {file_path}"
        }
    
    # Extract priorities
    result = CSRKeywordExtractor.extract_csr_priorities(text_content)
    
    # Store result in session state if successful
    if result["status"] == "success":
        ctx.session.state["csr_priorities"] = result
    
    return result


async def identify_missing_attachments(ctx: ToolContext, provided_files: List[str]) -> Dict[str, Any]:
    """
    Identify which required attachments are missing or present
    
    Args:
        ctx: Tool context
        provided_files: List of file paths provided by the user
        
    Returns:
        Dict with attachment info and status
    """
    # Get attachment requirements from state, or use default requirements
    requirements = ctx.session.state.get("attachment_requirements", [
        "board_roster", "budget", "tax_exemption", "logic_model", "evaluation_plan"
    ])
    
    # Resolve paths if relative
    resolved_files = []
    for file_path in provided_files:
        if not os.path.isabs(file_path):
            resolved_files.append(os.path.join(DEFAULT_INPUT_DIR, file_path))
        else:
            resolved_files.append(file_path)
    
    # Identify missing attachments
    attachments = AttachmentTracker.identify_missing_attachments(
        requirements=requirements,
        provided_files=resolved_files
    )
    
    # Convert to dicts for JSON serialization
    attachment_dicts = [attachment.model_dump() for attachment in attachments]
    
    # Generate request templates for missing attachments
    missing_attachments = [a for a in attachments if a.status == "missing"]
    request_templates = AttachmentTracker.generate_attachment_requests(missing_attachments)
    
    # Store in session state
    ctx.session.state["attachments"] = attachment_dicts
    ctx.session.state["attachment_requests"] = request_templates
    
    return {
        "status": "success",
        "attachments": attachment_dicts,
        "missing_attachments": [a.model_dump() for a in missing_attachments],
        "attachment_requests": request_templates
    }


async def generate_attachment_template(ctx: ToolContext, attachment_type: str) -> Dict[str, Any]:
    """
    Generate a template for a missing attachment
    
    Args:
        ctx: Tool context
        attachment_type: Type of attachment to generate a template for
        
    Returns:
        Dict with template content
    """
    template_content = AttachmentTracker.generate_template_placeholder(attachment_type)
    
    # Generate a filename for the template
    filename = f"{attachment_type}_template.md"
    output_path = os.path.join(DEFAULT_OUTPUT_DIR, filename)
    
    # Ensure output directory exists
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    
    # Save the template
    with open(output_path, 'w') as f:
        f.write(template_content)
    
    return {
        "status": "success",
        "attachment_type": attachment_type,
        "template_content": template_content,
        "output_path": output_path
    }


async def render_grant_template(ctx: ToolContext, template_name: str = "standard_grant.j2") -> Dict[str, Any]:
    """
    Render a grant template using data in the session state
    
    Args:
        ctx: Tool context
        template_name: Name of the template file
        
    Returns:
        Dict with rendered content
    """
    # Initialize renderer
    renderer = Jinja2Renderer(templates_dir=os.path.join(os.path.dirname(__file__), 'templates'))
    
    # Check if template exists
    available_templates = renderer.get_available_templates()
    if template_name not in available_templates:
        return {
            "status": "error",
            "message": f"Template '{template_name}' not found. Available templates: {available_templates}"
        }
    
    # Prepare context from session state
    context = {}
    
    # Get organization info
    if "organization_info" in ctx.session.state:
        context["organization"] = ctx.session.state["organization_info"]
    else:
        # Create some minimal placeholder data
        context["organization"] = {
            "name": "Your Organization",
            "mission": "Your mission statement."
        }
    
    # Get funder info
    if "funder_info" in ctx.session.state:
        context["funder"] = ctx.session.state["funder_info"]
    else:
        # Create some minimal placeholder data
        context["funder"] = {
            "name": "Example Foundation"
        }
    
    # Get grant info
    if "grant_info" in ctx.session.state:
        context["grant"] = ctx.session.state["grant_info"]
    else:
        # Create some minimal placeholder data
        context["grant"] = {
            "title": "Grant Proposal"
        }
    
    # Add logic model if available
    if "logic_model" in ctx.session.state:
        if "grant" not in context:
            context["grant"] = {}
        context["grant"]["logic_model"] = ctx.session.state["logic_model"]
    
    # Add evaluation plan if available
    if "evaluation_plan" in ctx.session.state:
        if "grant" not in context:
            context["grant"] = {}
        context["grant"]["evaluation_plan"] = ctx.session.state["evaluation_plan"]
    
    # Add language matching if available
    if "language_matching" in ctx.session.state:
        context["funder_matching"] = ctx.session.state["language_matching"]
    
    # Add missing elements if any
    missing_elements = []
    if "logic_model" not in ctx.session.state:
        missing_elements.append("Logic Model")
    if "evaluation_plan" not in ctx.session.state:
        missing_elements.append("Evaluation Plan")
    
    if missing_elements:
        if "grant" not in context:
            context["grant"] = {}
        context["grant"]["missing_elements"] = missing_elements
    
    # Render the template
    result = renderer.render_grant_template(template_name, context)
    
    # Store result in session state if successful
    if result["status"] == "success":
        ctx.session.state["rendered_narrative"] = result
    
    return result


async def generate_grant_docx(ctx: ToolContext, output_filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a Word document from the rendered grant narrative
    
    Args:
        ctx: Tool context
        output_filename: Name for the output file (optional)
        
    Returns:
        Dict with output file path
    """
    # Check if a narrative has been rendered
    if "rendered_narrative" not in ctx.session.state:
        return {
            "status": "error",
            "message": "No rendered narrative found in session state. Please call render_grant_template first."
        }
    
    # Get rendered narrative
    narrative = ctx.session.state["rendered_narrative"]
    
    # Generate output filename if not provided
    if output_filename is None:
        if "grant_info" in ctx.session.state and "title" in ctx.session.state["grant_info"]:
            title = ctx.session.state["grant_info"]["title"]
            output_filename = f"{title.replace(' ', '_')}.docx"
        else:
            output_filename = f"grant_proposal_{datetime.now().strftime('%Y%m%d')}.docx"
    
    # Ensure .docx extension
    if not output_filename.endswith('.docx'):
        output_filename += '.docx'
    
    # Prepare output path
    output_path = os.path.join(DEFAULT_OUTPUT_DIR, output_filename)
    
    # Ensure output directory exists
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    
    # Prepare context for document assembly
    grant_data = {}
    if "organization_info" in ctx.session.state:
        grant_data["organization"] = ctx.session.state["organization_info"]
    if "funder_info" in ctx.session.state:
        grant_data["funder"] = ctx.session.state["funder_info"]
    if "grant_info" in ctx.session.state:
        grant_data.update(ctx.session.state["grant_info"])
    
    # Add missing elements if any
    if "grant" in ctx.session.state and "missing_elements" in ctx.session.state["grant"]:
        grant_data["missing_elements"] = ctx.session.state["grant"]["missing_elements"]
    
    # Create the document
    assembler = ReportAssembler()
    output_path = assembler.create_docx_from_narrative(narrative, output_path, grant_data)
    
    if output_path:
        return {
            "status": "success",
            "output_path": output_path,
            "output_filename": os.path.basename(output_path)
        }
    else:
        return {
            "status": "error",
            "message": "Failed to create DOCX file"
        }


async def extract_org_info_from_docx(ctx: ToolContext, file_path: str) -> Dict[str, Any]:
    """
    Extract organization information from a document
    
    Args:
        ctx: Tool context
        file_path: Path to the document containing organization info
        
    Returns:
        Dict with extracted organization info
    """
    # Resolve path if relative
    if not os.path.isabs(file_path):
        file_path = os.path.join(DEFAULT_INPUT_DIR, file_path)
    
    # Check file existence first
    if not os.path.exists(file_path):
        return {
            "status": "error",
            "message": f"File not found: {file_path}"
        }
    
    # Check if this is a text file (for testing)
    _, ext = os.path.splitext(file_path)
    if ext.lower() == '.txt':
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract organization info from text content
            org_info = {}
            
            # Look for organization name
            for line in content.split('\n'):
                if line.startswith('Organization:'):
                    org_info["name"] = line.split(':', 1)[1].strip()
                    break
            
            # Look for mission statement
            for line in content.split('\n'):
                if line.startswith('Mission:'):
                    org_info["mission"] = line.split(':', 1)[1].strip()
                    break
            
            # Look for vision statement
            for line in content.split('\n'):
                if line.startswith('Vision:'):
                    org_info["vision"] = line.split(':', 1)[1].strip()
                    break
            
            # Look for year founded
            for line in content.split('\n'):
                if line.startswith('Year Founded:'):
                    try:
                        org_info["year_founded"] = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                    break
            
            # Look for programs
            programs = []
            in_programs_section = False
            for line in content.split('\n'):
                if line.startswith('Programs:'):
                    in_programs_section = True
                    continue
                if in_programs_section and line.strip().startswith('-'):
                    programs.append(line.strip()[1:].strip())
                elif in_programs_section and line.strip() == '':
                    in_programs_section = False
            
            if programs:
                org_info["programs"] = programs
            
            # Store in session state
            ctx.session.state["organization_info"] = org_info
            
            return {
                "status": "success",
                "organization_info": org_info
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to extract organization info from text file: {str(e)}"
            }
    
    # Parse the document
    try:
        result = DocxParser.parse(file_path)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
    if result["status"] != "success":
        return result
    
    # Extract organization info from document
    org_info = {}
    
    # Extract organization name from metadata
    if "metadata" in result and "title" in result["metadata"]:
        org_info["name"] = result["metadata"]["title"]
    
    # Look for mission statement in sections or paragraphs
    mission = None
    vision = None
    programs = []
    
    # Check sections first
    for section_name, content in result.get("sections", {}).items():
        section_name_lower = section_name.lower()
        if "mission" in section_name_lower:
            mission = content.strip()
        elif "vision" in section_name_lower:
            vision = content.strip()
        elif "program" in section_name_lower or "service" in section_name_lower:
            # Extract program list from bulleted items
            for line in content.split('\n'):
                if line.strip().startswith('•') or line.strip().startswith('-'):
                    programs.append(line.strip()[1:].strip())
    
    # If no mission found in sections, check paragraphs
    if not mission:
        for para in result.get("paragraphs", []):
            if "mission" in para["text"].lower() and len(para["text"]) < 300:  # Likely a mission statement
                mission = para["text"].strip()
                if "Mission:" in mission or "Mission Statement:" in mission:
                    # Extract the mission part after the label
                    mission = mission.split(":", 1)[1].strip()
                break
    
    # If no vision found in sections, check paragraphs
    if not vision:
        for para in result.get("paragraphs", []):
            if "vision" in para["text"].lower() and len(para["text"]) < 300:  # Likely a vision statement
                vision = para["text"].strip()
                if "Vision:" in vision or "Vision Statement:" in vision:
                    # Extract the vision part after the label
                    vision = vision.split(":", 1)[1].strip()
                break
    
    # If no name found in metadata, try to extract from content
    if "name" not in org_info:
        # Look for organization name patterns in first few paragraphs
        for para in result.get("paragraphs", [])[:5]:
            # Check for patterns like "About [Org Name]" or "[Org Name] is a..."
            text = para["text"]
            if text.startswith("About ") or " is a " in text:
                if text.startswith("About "):
                    org_name = text[6:].split(".")[0].strip()
                    org_info["name"] = org_name
                    break
                elif " is a " in text:
                    org_name = text.split(" is a ")[0].strip()
                    if len(org_name) < 50:  # Reasonable length for an org name
                        org_info["name"] = org_name
                        break
    
    # Add extracted info
    if mission:
        org_info["mission"] = mission
    if vision:
        org_info["vision"] = vision
    if programs:
        org_info["programs"] = programs
    
    # Extract other info if available
    # Look for year founded pattern
    for para in result.get("paragraphs", []):
        text = para["text"].lower()
        if "founded in" in text or "established in" in text:
            # Try to extract year
            for word in text.split():
                if word.isdigit() and len(word) == 4 and 1900 <= int(word) <= datetime.now().year:
                    org_info["year_founded"] = int(word)
                    break
        
        # Look for tax status
        if "501(c)(3)" in para["text"] or "501c3" in para["text"]:
            org_info["tax_status"] = "501(c)(3)"
    
    # Store in session state
    ctx.session.state["organization_info"] = org_info
    
    return {
        "status": "success",
        "organization_info": org_info
    }


async def extract_funder_info_from_pdf(ctx: ToolContext, file_path: str) -> Dict[str, Any]:
    """
    Extract funder information from a PDF document
    
    Args:
        ctx: Tool context
        file_path: Path to the PDF document
        
    Returns:
        Dict with extracted funder info
    """
    # Resolve path if relative
    if not os.path.isabs(file_path):
        file_path = os.path.join(DEFAULT_INPUT_DIR, file_path)
    
    # Check file existence first
    if not os.path.exists(file_path):
        return {
            "status": "error",
            "message": f"File not found: {file_path}"
        }
    
    # Check if this is a text file (for testing)
    _, ext = os.path.splitext(file_path)
    if ext.lower() == '.txt':
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract funder info from text content
            funder_info = {}
            full_text = content
            
            # Look for funder name in the first few lines
            lines = content.split('\n')
            for i in range(min(5, len(lines))):
                line = lines[i].strip()
                if "Foundation" in line or "Fund" in line or "Trust" in line:
                    funder_info["name"] = line
                    break
            
            # If no name found in first few lines, look for specific format
            if "name" not in funder_info:
                for line in content.split('\n'):
                    if line.startswith('The ') and len(line) < 50:
                        funder_info["name"] = line.strip()
                        break
            
            # Extract focus areas
            focus_areas = []
            in_focus_areas = False
            for line in content.split('\n'):
                if line.startswith('Grant Focus Areas:'):
                    in_focus_areas = True
                    continue
                elif in_focus_areas and line.strip().startswith('-'):
                    focus_areas.append(line.strip()[1:].strip())
                elif in_focus_areas and not line.strip():
                    in_focus_areas = False
            
            if focus_areas:
                funder_info["focus_areas"] = focus_areas
            
            # Extract grant ranges
            for line in content.split('\n'):
                if 'Grant Amounts:' in line:
                    amount_str = line.split(':', 1)[1].strip()
                    funder_info["grant_ranges"] = amount_str
                    break
            
            # Extract attachment requirements
            requirements = []
            in_requirements = False
            for line in content.split('\n'):
                if line.startswith('Required Attachments:'):
                    in_requirements = True
                    continue
                elif in_requirements and line.strip().startswith('-'):
                    requirements.append(line.strip()[1:].strip())
                elif in_requirements and not line.strip():
                    in_requirements = False
            
            if requirements:
                funder_info["attachment_requirements"] = requirements
                # Store in session state for later use
                ctx.session.state["attachment_requirements"] = requirements
            
            # Store in session state
            ctx.session.state["funder_info"] = funder_info
            
            return {
                "status": "success",
                "funder_info": funder_info
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to extract funder info from text file: {str(e)}"
            }
    
    # Parse the document
    try:
        result = PDFParser.parse(file_path)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
    if result["status"] != "success":
        return result
    
    # Extract funder info from document
    funder_info = {}
    
    # Extract funder name from metadata
    if "metadata" in result and "Title" in result["metadata"]:
        funder_info["name"] = result["metadata"]["Title"]
    
    # Extract text content
    full_text = "\n\n".join([page["text"] for page in result.get("pages", [])])
    
    # If no name found in metadata, try to extract from content
    if "name" not in funder_info:
        # Look for common funder name patterns in first page
        first_page = result.get("pages", [{}])[0]
        first_page_text = first_page.get("text", "")
        
        # Common patterns: "X Foundation Grant Guidelines" or "About X Foundation"
        for line in first_page_text.split("\n")[:10]:  # Check first 10 lines
            if "Foundation" in line or "Fund" in line or "Trust" in line:
                # Extract potential name
                potential_name = line.strip()
                # If the line is too long, probably not just a name
                if len(potential_name) < 50:
                    funder_info["name"] = potential_name
                    break
    
    # Extract focus areas using keyword matching
    focus_areas = []
    keywords = FunderLanguageMatcher.extract_keywords(full_text, top_n=30)
    focus_areas_keywords = [
        "education", "health", "environment", "arts", "community", "youth", "elderly", 
        "children", "housing", "homelessness", "food", "hunger", "justice", "equity",
        "diversity", "inclusion", "climate", "sustainability", "technology", "innovation",
        "entrepreneurship", "workforce", "development", "economic", "social", "mental",
        "research", "advocacy", "policy", "human rights", "STEM", "STEAM"
    ]
    
    for keyword in keywords:
        if keyword.lower() in focus_areas_keywords:
            focus_areas.append(keyword)
    
    if focus_areas:
        funder_info["focus_areas"] = focus_areas
    
    # Extract grant ranges if available
    for page in result.get("pages", []):
        text = page.get("text", "")
        if "$" in text and ("grant" in text.lower() or "award" in text.lower()):
            # Look for dollar amounts
            import re
            money_pattern = r'\$\s?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{2})?'
            grant_range_pattern = r'(?:grants|awards) (?:range|between) (?:\$\s?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{2})?)[^\n.]*(?:\$\s?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{2})?)'
            grant_avg_pattern = r'(?:average|typical) (?:grant|award) (?:is|of) (?:\$\s?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{2})?)'
            
            # Look for grant ranges
            grant_ranges = re.findall(grant_range_pattern, text.lower())
            grant_avgs = re.findall(grant_avg_pattern, text.lower())
            
            if grant_ranges or grant_avgs:
                grant_info = {}
                if grant_ranges:
                    grant_info["ranges"] = grant_ranges
                if grant_avgs:
                    grant_info["average"] = grant_avgs
                funder_info["grant_ranges"] = grant_info
                break
    
    # Extract requirements directly from PDF content
    attachment_requirements = AttachmentTracker.extract_requirements_from_text(full_text)
    if attachment_requirements:
        funder_info["attachment_requirements"] = attachment_requirements
        # Store in session state for later use
        ctx.session.state["attachment_requirements"] = attachment_requirements
    
    # Store in session state
    ctx.session.state["funder_info"] = funder_info
    
    return {
        "status": "success",
        "funder_info": funder_info
    }


async def get_available_templates(ctx: ToolContext) -> Dict[str, Any]:
    """
    Get a list of available grant templates
    
    Args:
        ctx: Tool context
        
    Returns:
        Dict with a list of available templates
    """
    # Initialize renderer
    renderer = Jinja2Renderer(templates_dir=os.path.join(os.path.dirname(__file__), 'templates'))
    
    # Get available templates
    templates = renderer.get_available_templates()
    
    return {
        "status": "success",
        "templates": templates
    }


async def create_grant_metadata(ctx: ToolContext, title: str, amount_requested: float = None) -> Dict[str, Any]:
    """
    Create or update grant metadata
    
    Args:
        ctx: Tool context
        title: Grant title
        amount_requested: Amount requested (optional)
        
    Returns:
        Dict with updated grant info
    """
    # Get existing grant info or create new
    grant_info = ctx.session.state.get("grant_info", {})
    
    # Update with new values
    grant_info["title"] = title
    if amount_requested is not None:
        grant_info["amount_requested"] = amount_requested
    
    # Add missing elements if needed
    missing_elements = []
    if "logic_model" not in ctx.session.state:
        missing_elements.append("Logic Model")
    if "evaluation_plan" not in ctx.session.state:
        missing_elements.append("Evaluation Plan")
    if missing_elements:
        grant_info["missing_elements"] = missing_elements
    
    # Store in session state
    ctx.session.state["grant_info"] = grant_info
    
    return {
        "status": "success",
        "grant_info": grant_info
    } 