import os
import logging
import datetime
import time
import base64
import io
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz
from google.adk.models import Gemini
import json
from typing import Optional, List, Dict, Any, Union
from ..OSOD.prompts import return_instructions_root
import jinja2
from google.adk.tools import FunctionTool, ToolContext
import numpy as np
import requests
from PIL import Image
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# --- Load environment ---
load_dotenv()

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "eleanor-for-enterprise-3307cc9e33c9.json")
SCOPES = ["https://www.googleapis.com/auth/calendar", 
          "https://www.googleapis.com/auth/calendar.events", 
          "https://www.googleapis.com/auth/calendar.readonly"]
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TIMEZONE = "America/New_York"

# Default calendar IDs for direct access
DEFAULT_CALENDAR_IDS = [
    "aaron@kingcrowe.com",
    "aaronpqking@gmail.com"
]

# --- Template Initialization ---
template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath=TEMPLATES_DIR),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)

# --- Data Ingestion Tools ---

def process_image_ocr(image_path: str, language: str = 'eng') -> dict:
    """Extract text from an image using OCR.
    
    Args:
        image_path: Path to the image file or URL
        language: OCR language (default: eng)
    
    Returns:
        dict: Extracted text and metadata
    """
    try:
        if not TESSERACT_AVAILABLE:
            return {
                "status": "error",
                "error_message": "OCR functionality requires pytesseract. Please install with: pip install pytesseract"
            }
            
        # Handle different input types (URL vs file path)
        if image_path.startswith(('http://', 'https://')):
            # Download image from URL
            response = requests.get(image_path, stream=True)
            if response.status_code != 200:
                return {
                    "status": "error",
                    "error_message": f"Failed to download image: {response.status_code}"
                }
                
            img = Image.open(io.BytesIO(response.content))
        else:
            # Load from local file
            if not os.path.exists(image_path):
                return {
                    "status": "error",
                    "error_message": f"Image file not found: {image_path}"
                }
                
            img = Image.open(image_path)
        
        # Perform OCR
        extracted_text = pytesseract.image_to_string(img, lang=language)
        
        # Get image metadata
        width, height = img.size
        format_name = img.format
        mode = img.mode
        
        # Save a unique copy in the output directory for reference
        filename = f"ocr_image_{int(time.time())}.{format_name.lower() if format_name else 'png'}"
        filepath = os.path.join(OUTPUT_DIR, filename)
        img.save(filepath)
        
        # Process the extracted text further
        text_lines = extracted_text.strip().split('\n')
        cleaned_lines = [line.strip() for line in text_lines if line.strip()]
        
        return {
            "status": "success",
            "extracted_text": extracted_text,
            "cleaned_text": '\n'.join(cleaned_lines),
            "line_count": len(cleaned_lines),
            "metadata": {
                "width": width,
                "height": height,
                "format": format_name,
                "mode": mode,
                "saved_copy": filepath
            },
            "data_type": "unstructured",
            "content": '\n'.join(cleaned_lines)
        }
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }

def parse_data_source(source_path: str, source_type: str = None) -> dict:
    """Parse data from various sources into a structured format.
    
    Args:
        source_path: Path to the data source file
        source_type: Type of data (json, csv, txt) - will be auto-detected if None
    
    Returns:
        dict: Parsed structured data
    """
    try:
        if not source_type and source_path:
            # Auto-detect file type from extension
            _, ext = os.path.splitext(source_path)
            source_type = ext.lower().strip('.')
        
        if not os.path.exists(source_path):
            return {
                "status": "error",
                "error_message": f"File not found: {source_path}"
            }
            
        if source_type == "csv":
            df = pd.read_csv(source_path)
            return {
                "status": "success",
                "data_type": "tabular",
                "columns": df.columns.tolist(),
                "rows": df.to_dict(orient="records"),
                "summary": {
                    "row_count": len(df),
                    "column_count": len(df.columns)
                }
            }
        elif source_type == "json":
            with open(source_path, 'r') as f:
                data = json.load(f)
            return {
                "status": "success",
                "data_type": "structured",
                "data": data
            }
        elif source_type in ["txt", "md", "text"]:
            with open(source_path, 'r') as f:
                content = f.read()
            return {
                "status": "success",
                "data_type": "unstructured",
                "content": content
            }
        else:
            return {
                "status": "error",
                "error_message": f"Unsupported file type: {source_type}"
            }
    except Exception as e:
        logger.error(f"Error parsing data source: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }

def parse_raw_input(content: str, format_hint: str = None) -> dict:
    """Process raw input text into structured data.
    
    Args:
        content: Raw text content to parse
        format_hint: Optional hint about the content format
        
    Returns:
        dict: Structured data extracted from raw input
    """
    try:
        # Try to parse as JSON first
        if format_hint == "json" or (content.strip().startswith('{') and content.strip().endswith('}')):
            try:
                data = json.loads(content)
                return {
                    "status": "success",
                    "data_type": "structured",
                    "data": data
                }
            except json.JSONDecodeError:
                pass
                
        # Check if it might be CSV
        if format_hint == "csv" or ',' in content:
            try:
                df = pd.read_csv(io.StringIO(content))
                return {
                    "status": "success",
                    "data_type": "tabular",
                    "columns": df.columns.tolist(),
                    "rows": df.to_dict(orient="records"),
                    "summary": {
                        "row_count": len(df),
                        "column_count": len(df.columns)
                    }
                }
            except Exception:
                pass
                
        # Process as unstructured text
        return {
            "status": "success",
            "data_type": "unstructured",
            "content": content
        }
    except Exception as e:
        logger.error(f"Error parsing raw input: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }

# --- Report Template Tools ---

def get_available_templates() -> dict:
    """List available report templates."""
    try:
        templates = {}
        template_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.j2')]
        
        for filename in template_files:
            template_name = filename.split('.')[0]
            template_type = template_name.split('_')[0] if '_' in template_name else 'generic'
            
            if template_type not in templates:
                templates[template_type] = []
                
            templates[template_type].append(template_name)
            
        return {
            "status": "success", 
            "templates": templates
        }
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }

def generate_report_template(report_type: str, audience: str = "internal") -> dict:
    """Create a structured template for a specific report type.
    
    Args:
        report_type: Type of report (strategic, financial, stakeholder, meeting)
        audience: Target audience (internal, executive, investor, client, public)
        
    Returns:
        dict: Report template structure
    """
    try:
        # Define base templates for different report types and audiences
        templates = {
            "strategic": {
                "internal": {
                    "title": "Strategic Plan",
                    "subtitle": "{organization} - {timeframe}",
                    "sections": [
                        {"name": "executive_summary", "title": "Executive Summary", "content": ""},
                        {"name": "objectives", "title": "Objectives & Key Results", "content": ""},
                        {"name": "market_trends", "title": "Market Trends", "content": ""},
                        {"name": "timeline", "title": "Timeline & Milestones", "content": ""},
                        {"name": "team", "title": "Team Responsibilities", "content": ""},
                        {"name": "risks", "title": "Risks & Mitigations", "content": ""},
                        {"name": "metrics", "title": "Success Metrics", "content": ""},
                        {"name": "budget", "title": "Budget & Resources", "content": ""}
                    ],
                    "metadata": {
                        "author": "",
                        "created_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "audience": "Internal Stakeholders",
                        "timeframe": f"Q{(datetime.datetime.now().month-1)//3 + 2} {datetime.datetime.now().year}",
                        "classification": "Confidential - Internal Only"
                    }
                },
                "executive": {
                    "title": "Strategic Plan Executive Summary",
                    "subtitle": "{organization} - {timeframe}",
                    "sections": [
                        {"name": "executive_summary", "title": "Executive Summary", "content": ""},
                        {"name": "objectives", "title": "Strategic Objectives", "content": ""},
                        {"name": "impact", "title": "Business Impact", "content": ""},
                        {"name": "timeline", "title": "Key Milestones", "content": ""},
                        {"name": "metrics", "title": "Key Performance Indicators", "content": ""},
                        {"name": "investment", "title": "Investment Required", "content": ""}
                    ],
                    "metadata": {
                        "author": "",
                        "created_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "audience": "Executive Leadership",
                        "timeframe": f"Q{(datetime.datetime.now().month-1)//3 + 2} {datetime.datetime.now().year}",
                        "classification": "Confidential - Executive Only"
                    }
                },
                "investor": {
                    "title": "Strategic Growth Plan",
                    "subtitle": "{organization} - {timeframe}",
                    "sections": [
                        {"name": "opportunity", "title": "Market Opportunity", "content": ""},
                        {"name": "strategy", "title": "Strategic Approach", "content": ""},
                        {"name": "projections", "title": "Growth Projections", "content": ""},
                        {"name": "milestones", "title": "Key Milestones", "content": ""},
                        {"name": "competitive", "title": "Competitive Positioning", "content": ""},
                        {"name": "metrics", "title": "Success Metrics", "content": ""}
                    ],
                    "metadata": {
                        "author": "",
                        "created_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "audience": "Investors",
                        "timeframe": f"Q{(datetime.datetime.now().month-1)//3 + 2} {datetime.datetime.now().year}",
                        "classification": "Confidential - Investment Materials"
                    }
                },
                "client": {
                    "title": "Strategic Partnership Plan",
                    "subtitle": "{organization} - {timeframe}",
                    "sections": [
                        {"name": "overview", "title": "Partnership Overview", "content": ""},
                        {"name": "value", "title": "Value Proposition", "content": ""},
                        {"name": "implementation", "title": "Implementation Roadmap", "content": ""},
                        {"name": "success", "title": "Success Criteria", "content": ""},
                        {"name": "engagement", "title": "Engagement Model", "content": ""}
                    ],
                    "metadata": {
                        "author": "",
                        "created_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "audience": "Client Partners",
                        "timeframe": f"Q{(datetime.datetime.now().month-1)//3 + 2} {datetime.datetime.now().year}",
                        "classification": "Confidential - Partnership Materials"
                    }
                },
                "public": {
                    "title": "Strategic Direction",
                    "subtitle": "{organization} - {timeframe}",
                    "sections": [
                        {"name": "vision", "title": "Vision & Mission", "content": ""},
                        {"name": "focus", "title": "Strategic Focus Areas", "content": ""},
                        {"name": "innovation", "title": "Innovation Highlights", "content": ""},
                        {"name": "impact", "title": "Expected Impact", "content": ""}
                    ],
                    "metadata": {
                        "author": "",
                        "created_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "audience": "Public",
                        "timeframe": f"Q{(datetime.datetime.now().month-1)//3 + 2} {datetime.datetime.now().year}",
                        "classification": "Public Information"
                    }
                }
            },
            "financial": {
                "internal": {
                    "title": "Financial Report",
                    "subtitle": "For period ending {end_date}",
                    "sections": [
                        {"name": "executive_summary", "title": "Executive Summary", "content": ""},
                        {"name": "key_metrics", "title": "Key Financial Metrics", "content": "", "chart_type": "bar"},
                        {"name": "revenue", "title": "Revenue Analysis", "content": "", "chart_type": "line"},
                        {"name": "expenses", "title": "Expense Analysis", "content": "", "chart_type": "pie"},
                        {"name": "cash_flow", "title": "Cash Flow Analysis", "content": ""},
                        {"name": "outlook", "title": "Financial Outlook", "content": ""}
                    ],
                    "metadata": {
                        "author": "",
                        "created_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "audience": "Internal Finance Team",
                        "data_sources": [],
                        "classification": "Confidential - Finance Only"
                    }
                },
                "executive": {
                    "title": "Financial Performance Summary",
                    "subtitle": "For period ending {end_date}",
                    "sections": [
                        {"name": "highlights", "title": "Financial Highlights", "content": ""},
                        {"name": "performance", "title": "Performance vs. Targets", "content": "", "chart_type": "bar"},
                        {"name": "trends", "title": "Key Trends", "content": "", "chart_type": "line"},
                        {"name": "outlook", "title": "Outlook & Forecast", "content": ""}
                    ],
                    "metadata": {
                        "author": "",
                        "created_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "audience": "Executive Leadership",
                        "data_sources": [],
                        "classification": "Confidential - Executive Only"
                    }
                },
                "investor": {
                    "title": "Investor Financial Report",
                    "subtitle": "For period ending {end_date}",
                    "sections": [
                        {"name": "highlights", "title": "Financial Highlights", "content": ""},
                        {"name": "growth", "title": "Growth Metrics", "content": "", "chart_type": "line"},
                        {"name": "profitability", "title": "Profitability Analysis", "content": "", "chart_type": "bar"},
                        {"name": "runway", "title": "Runway & Burn Rate", "content": ""},
                        {"name": "funding", "title": "Funding & Investment", "content": ""},
                        {"name": "projections", "title": "Financial Projections", "content": ""}
                    ],
                    "metadata": {
                        "author": "",
                        "created_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "audience": "Investors",
                        "data_sources": [],
                        "classification": "Confidential - Investment Materials"
                    }
                }
            },
            "stakeholder": {
                "title": "Stakeholder Update",
                "subtitle": "{project_name} - {update_period}",
                "sections": [
                    {"name": "highlights", "title": "Key Highlights", "content": ""},
                    {"name": "progress", "title": "Progress Update", "content": ""},
                    {"name": "challenges", "title": "Challenges & Solutions", "content": ""},
                    {"name": "next_steps", "title": "Next Steps", "content": ""},
                    {"name": "feedback", "title": "Feedback Requested", "content": ""}
                ],
                "metadata": {
                    "author": "",
                    "created_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "distribution": "All Stakeholders"
                }
            },
            "meeting": {
                "title": "Meeting Summary",
                "subtitle": "{meeting_topic} - {meeting_date}",
                "sections": [
                    {"name": "attendees", "title": "Attendees", "content": ""},
                    {"name": "agenda", "title": "Agenda", "content": ""},
                    {"name": "discussion", "title": "Discussion", "content": ""},
                    {"name": "action_items", "title": "Action Items", "content": ""},
                    {"name": "next_meeting", "title": "Next Meeting", "content": ""}
                ],
                "metadata": {
                    "author": "",
                    "meeting_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "meeting_duration": "60 minutes"
                }
            }
        }
        
        # Return the requested template or a generic one if not found
        if report_type.lower() in templates:
            template_data = templates[report_type.lower()]
            
            # Handle audience-specific templates
            if isinstance(template_data, dict) and audience in template_data:
                selected_template = template_data[audience]
            elif isinstance(template_data, dict) and "internal" in template_data:
                # Fall back to internal template if requested audience isn't available
                selected_template = template_data["internal"]
                logger.info(f"Using internal template as fallback for {audience} audience")
            else:
                # Use the template as is if it's not audience-specific
                selected_template = template_data
                
            template_id = f"{report_type}_{audience}_{int(time.time())}"
            
            # Also create the corresponding Jinja template file if it doesn't exist
            template_file = f"{report_type}_{audience}_template.md.j2"
            template_path = os.path.join(TEMPLATES_DIR, template_file)
            
            if not os.path.exists(template_path):
                # Create a basic Jinja template based on the structure
                with open(template_path, 'w') as f:
                    f.write(f"# {{{{ title }}}}\n\n")
                    f.write("**Audience:** {{ metadata.audience }}  \n")
                    
                    if "timeframe" in selected_template.get("metadata", {}):
                        f.write("**Timeframe:** {{ metadata.timeframe }}  \n\n")
                    elif "end_date" in selected_template.get("subtitle", ""):
                        f.write("**Period:** {{ metadata.end_date }}  \n\n")
                        
                    f.write("---\n\n")
                    
                    for section in selected_template["sections"]:
                        f.write(f"## {section['title']}\n\n")
                        f.write("{{ " + section["name"] + "_content }}\n\n")
                        f.write("---\n\n")
                    
                    f.write("*Generated on {{ metadata.created_date }}*\n")
                    if "classification" in selected_template.get("metadata", {}):
                        f.write("\n*{{ metadata.classification }}*\n")
            
            return {
                "status": "success",
                "template_id": template_id,
                "template": selected_template,
                "template_file": template_file,
                "message": f"Generated {audience} template for {report_type} report"
            }
        else:
            # Create a generic template if requested type not found
            generic_template = {
                "title": f"{report_type.title()} Report",
                "subtitle": "Generated on {date}",
                "sections": [
                    {"name": "introduction", "title": "Introduction", "content": ""},
                    {"name": "main_content", "title": "Main Content", "content": ""},
                    {"name": "conclusion", "title": "Conclusion", "content": ""}
                ],
                "metadata": {
                    "author": "",
                    "created_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "audience": audience.capitalize()
                }
            }
            
            template_id = f"generic_{report_type}_{audience}_{int(time.time())}"
            
            return {
                "status": "success",
                "template_id": template_id,
                "template": generic_template,
                "message": f"Generated generic {audience} template for {report_type} report"
            }
            
    except Exception as e:
        logger.error(f"Error generating report template: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }

# --- Data Visualization Tools ---

def generate_chart(data: dict, chart_type: str, title: str) -> dict:
    """Generate a chart visualization from data.
    
    Args:
        data: Source data for visualization (dict or DataFrame-compatible structure)
        chart_type: Type of chart (bar, line, pie, scatter, radar, etc.)
        title: Chart title
        
    Returns:
        dict: Chart as embedded HTML and metadata
    """
    try:
        plt.figure(figsize=(10, 6))
        
        # Process the data based on its structure
        if isinstance(data, dict) and "rows" in data and "columns" in data:
            # Data is in a table-like format
            df = pd.DataFrame(data["rows"])
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # Data is a list of dictionaries
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and len(data) > 0:
            # Data is a dictionary with key-value pairs
            df = pd.DataFrame.from_dict(data, orient='index', columns=['value'])
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'key'}, inplace=True)
        else:
            return {
                "status": "error",
                "error_message": "Unsupported data format for chart generation"
            }
        
        # Generate the chart based on type
        if chart_type.lower() == "bar":
            if len(df.columns) >= 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
                ax = df.plot(kind='bar', x=x_col, y=y_col, title=title)
                plt.xlabel(x_col)
                plt.ylabel(y_col)
            else:
                ax = df.plot(kind='bar', title=title)
                
            plt.tight_layout()
            
        elif chart_type.lower() == "line":
            if len(df.columns) >= 2:
                x_col = df.columns[0]
                y_cols = df.columns[1:]
                ax = df.plot(kind='line', x=x_col, y=y_cols, title=title, marker='o')
                plt.xlabel(x_col)
            else:
                ax = df.plot(kind='line', title=title, marker='o')
                
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            
        elif chart_type.lower() == "pie":
            if len(df.columns) >= 2:
                labels = df[df.columns[0]]
                values = df[df.columns[1]]
                plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            else:
                plt.pie(df['value'], labels=df['key'], autopct='%1.1f%%', startangle=90)
                
            plt.axis('equal')
            plt.title(title)
            
        elif chart_type.lower() == "scatter":
            if len(df.columns) >= 3:
                x_col = df.columns[0]
                y_col = df.columns[1]
                size_col = df.columns[2]
                plt.scatter(df[x_col], df[y_col], s=df[size_col]/10, alpha=0.6)
                plt.xlabel(x_col)
                plt.ylabel(y_col)
            elif len(df.columns) >= 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
                plt.scatter(df[x_col], df[y_col], alpha=0.6)
                plt.xlabel(x_col)
                plt.ylabel(y_col)
            else:
                return {
                    "status": "error",
                    "error_message": "Scatter plot requires at least 2 data columns"
                }
                
            plt.title(title)
            plt.grid(True, linestyle='--', alpha=0.7)
            
        else:
            # Default to bar chart for unsupported types
            logger.warning(f"Unsupported chart type: {chart_type}. Defaulting to bar chart.")
            ax = df.plot(kind='bar', title=f"{title} (Bar Chart)")
            plt.tight_layout()
        
        # Save the chart to a BytesIO object
        chart_data = io.BytesIO()
        plt.savefig(chart_data, format='png')
        chart_data.seek(0)
        
        # Encode as base64 for embedding in HTML
        chart_base64 = base64.b64encode(chart_data.read()).decode()
        plt.close()
        
        # Generate a unique filename for the chart
        chart_filename = f"chart_{chart_type}_{int(time.time())}.png"
        chart_path = os.path.join(OUTPUT_DIR, chart_filename)
        
        # Save the chart to file for persistence
        try:
            with open(chart_path, 'wb') as f:
                f.write(base64.b64decode(chart_base64))
            logger.info(f"Chart saved to {chart_path}")
        except Exception as e:
            logger.warning(f"Could not save chart to file: {e}")
        
        return {
            "status": "success",
            "chart_html": f'<img src="data:image/png;base64,{chart_base64}" alt="{title}" width="100%">',
            "chart_file": chart_path,
            "chart_base64": chart_base64,
            "message": f"Generated {chart_type} chart: {title}"
        }
        
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }

# --- Report Rendering and Export Tools ---

def render_report(template_name: str, content: dict) -> dict:
    """Render a report using a specified template and content.
    
    Args:
        template_name: Name of the template to use
        content: Content to populate the template
        
    Returns:
        dict: Rendered report content
    """
    try:
        if not template_env:
            return {
                "status": "error",
                "error_message": "Template environment not initialized"
            }
            
        # Add .j2 extension if not present
        if not template_name.endswith('.j2'):
            template_name = f"{template_name}.j2"
            
        # Check if template exists
        template_path = os.path.join(TEMPLATES_DIR, template_name)
        if not os.path.exists(template_path):
            return {
                "status": "error",
                "error_message": f"Template not found: {template_name}"
            }
            
        # Load the template
        template = template_env.get_template(template_name)
        
        # Render the template with the provided content
        rendered_content = template.render(**content)
        
        return {
            "status": "success",
            "rendered_content": rendered_content,
            "message": f"Report rendered successfully using template: {template_name}"
        }
    except Exception as e:
        logger.error(f"Error rendering report: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }

def export_report(report_content: dict, format: str = "pdf") -> dict:
    """Export a report to the specified format.
    
    Args:
        report_content: Report content (can be rendered or unrendered)
        format: Output format (pdf, docx, md, html)
        
    Returns:
        dict: Export status and file path
    """
    try:
        # Validate input
        if not isinstance(report_content, dict):
            return {
                "status": "error",
                "error_message": "Report content must be a dictionary"
            }
            
        # Generate a unique filename
        timestamp = int(time.time())
        title = report_content.get("title", "report")
        sanitized_title = "".join(c if c.isalnum() else "_" for c in title)
        filename_base = f"{sanitized_title}_{timestamp}"
        
        # Handle markdown export (simplest case)
        if format.lower() == "md" or format.lower() == "markdown":
            # Generate markdown content
            md_content = ""
            
            # Add title and subtitle
            md_content += f"# {report_content.get('title', 'Untitled Report')}\n\n"
            if "subtitle" in report_content:
                md_content += f"*{report_content['subtitle']}*\n\n"
                
            # Add metadata
            if "metadata" in report_content:
                md_content += "## Metadata\n\n"
                for key, value in report_content["metadata"].items():
                    md_content += f"**{key.replace('_', ' ').title()}**: {value}\n"
                md_content += "\n---\n\n"
                
            # Add sections
            for section in report_content.get("sections", []):
                md_content += f"## {section.get('title', 'Untitled Section')}\n\n"
                md_content += f"{section.get('content', '')}\n\n"
                
                # Add chart if present
                if "chart_html" in section:
                    md_content += f"[Chart: {section.get('title', 'Untitled Chart')}]\n\n"
                    
            # Save the file
            filename = f"{filename_base}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, 'w') as f:
                f.write(md_content)
                
            return {
                "status": "success",
                "format": "markdown",
                "filename": filename,
                "filepath": filepath,
                "message": f"Report exported as Markdown: {filename}"
            }
            
        elif format.lower() == "html":
            # Generate HTML
            html_content = f"<!DOCTYPE html>\n<html>\n<head>\n"
            html_content += f"<title>{report_content.get('title', 'Untitled Report')}</title>\n"
            html_content += "<style>\n"
            html_content += "body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }\n"
            html_content += "h1 { color: #333366; }\n"
            html_content += "h2 { color: #666699; margin-top: 30px; }\n"
            html_content += ".subtitle { font-style: italic; color: #666; margin-bottom: 30px; }\n"
            html_content += ".metadata { background-color: #f8f8f8; padding: 15px; margin: 20px 0; border-radius: 5px; }\n"
            html_content += ".metadata-item { margin: 5px 0; }\n"
            html_content += ".section { margin-bottom: 30px; }\n"
            html_content += "</style>\n"
            html_content += "</head>\n<body>\n"
            
            # Title and subtitle
            html_content += f"<h1>{report_content.get('title', 'Untitled Report')}</h1>\n"
            if "subtitle" in report_content:
                html_content += f"<div class='subtitle'>{report_content['subtitle']}</div>\n"
                
            # Metadata
            if "metadata" in report_content:
                html_content += "<div class='metadata'>\n"
                for key, value in report_content["metadata"].items():
                    html_content += f"<div class='metadata-item'><strong>{key.replace('_', ' ').title()}</strong>: {value}</div>\n"
                html_content += "</div>\n"
                
            # Sections
            for section in report_content.get("sections", []):
                html_content += f"<div class='section'>\n"
                html_content += f"<h2>{section.get('title', 'Untitled Section')}</h2>\n"
                html_content += f"<div>{section.get('content', '')}</div>\n"
                
                # Add chart if present
                if "chart_html" in section:
                    html_content += f"<div>{section['chart_html']}</div>\n"
                    
                html_content += "</div>\n"
                
            html_content += "</body>\n</html>"
            
            # Save the file
            filename = f"{filename_base}.html"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, 'w') as f:
                f.write(html_content)
                
            return {
                "status": "success",
                "format": "html",
                "filename": filename,
                "filepath": filepath,
                "message": f"Report exported as HTML: {filename}"
            }
            
        elif format.lower() == "pdf" or format.lower() == "docx":
            # In a production implementation, use libraries like WeasyPrint (PDF) or python-docx (DOCX)
            # For this implementation, we'll simulate the export
            
            filename = f"{filename_base}.{format.lower()}"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            # Create a placeholder file
            with open(filepath, 'w') as f:
                f.write(f"This is a simulated {format.upper()} file for {report_content.get('title', 'Untitled Report')}")
                
            return {
                "status": "success",
                "format": format.lower(),
                "filename": filename,
                "filepath": filepath,
                "message": f"Report exported as {format.upper()}: {filename} (simulation)"
            }
            
        else:
            return {
                "status": "error",
                "error_message": f"Unsupported export format: {format}"
            }
            
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }

# --- Schedule and Workflow Tools ---

def schedule_report(report_template: str, schedule: dict, data_source: str = None) -> dict:
    """Schedule a report for recurring generation.
    
    Args:
        report_template: Template to use for the report
        schedule: Schedule configuration (frequency, next_run, etc.)
        data_source: Optional data source path or URL
        
    Returns:
        dict: Scheduled report information
    """
    try:
        # Generate a unique ID for the scheduled report
        schedule_id = f"sched_{int(time.time())}"
        
        # Basic validation
        if "frequency" not in schedule:
            return {
                "status": "error",
                "error_message": "Schedule must include a frequency (daily, weekly, monthly)"
            }
            
        # Normalize the schedule object
        normalized_schedule = {
            "report_template": report_template,
            "frequency": schedule.get("frequency", "weekly"),
            "next_run": schedule.get("next_run", (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()),
            "data_source": data_source,
            "last_run": None,
            "status": "active"
        }
        
        # In a production implementation, this would be stored in a database
        # For this implementation, we'll save to a JSON file
        schedule_file = os.path.join(OUTPUT_DIR, "scheduled_reports.json")
        
        try:
            if os.path.exists(schedule_file):
                with open(schedule_file, 'r') as f:
                    schedules = json.load(f)
            else:
                schedules = {}
                
            schedules[schedule_id] = normalized_schedule
            
            with open(schedule_file, 'w') as f:
                json.dump(schedules, f, indent=2)
                
            return {
                "status": "success",
                "schedule_id": schedule_id,
                "schedule": normalized_schedule,
                "message": f"Report scheduled with frequency: {normalized_schedule['frequency']}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Error saving schedule: {str(e)}"
            }
    except Exception as e:
        logger.error(f"Error scheduling report: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }

# --- Utility Functions ---
def get_service_account_info() -> dict:
    """Load and return service account information."""
    if SERVICE_ACCOUNT_FILE and os.path.exists(SERVICE_ACCOUNT_FILE):
        try:
            with open(SERVICE_ACCOUNT_FILE, 'r') as f:
                service_account_info = json.loads(f.read())
            return service_account_info
        except Exception as e:
            logger.error(f"Failed to load service account info: {str(e)}")
    return {}

# --- Initialize VertexAI and RAG ---
vertex_ai_available = False
ask_vertex_retrieval = None

try:
    from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
    from vertexai.preview import rag
    import vertexai
    
    vertex_ai_available = True
    logger.info("VertexAI RAG is available")
    
    # Initialize VertexAI with project and location
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "eleanor-for-enterprise")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    try:
        vertexai.init(project=project_id, location=location)
        logger.info(f"VertexAI initialized with project: {project_id}, location: {location}")
        
        # Initialize RAG corpus if available
        rag_corpus = os.environ.get("RAG_CORPUS")
        if rag_corpus:
            logger.info(f"Using RAG corpus: {rag_corpus}")
            ask_vertex_retrieval = VertexAiRagRetrieval(
                name='retrieve_rag_documentation',
                description='Use this tool to retrieve documentation and reference materials for the question from the RAG corpus',
                rag_resources=[rag.RagResource(rag_corpus=rag_corpus)],
                similarity_top_k=6,
                vector_distance_threshold=0.45,
            )
            logger.info(f"RAG corpus initialized with: {rag_corpus}")
        else:
            logger.warning("RAG_CORPUS environment variable not set. RAG functionality will be limited.")
    except Exception as e:
        logger.error(f"Failed to initialize VertexAI: {str(e)}")
except ImportError:
    logger.warning("VertexAI RAG is not available - some functionality will be limited")

def categorize_task(task: str, deadline: Optional[str] = "") -> dict:
    """Categorize a task using Covey's quadrant method."""
    try:
        urgency_keywords = ["urgent", "asap", "immediately"]
        importance_keywords = ["important", "priority", "critical"]
        urgency = sum(1 for k in urgency_keywords if k in task.lower())
        importance = sum(1 for k in importance_keywords if k in task.lower())
        
        if urgency and importance:
            quadrant = "urgent_important"
        elif importance:
            quadrant = "not_urgent_important"
        elif urgency:
            quadrant = "urgent_not_important"
        else:
            quadrant = "not_urgent_not_important"
            
        return {"status": "success", "quadrant": quadrant, "task": task, "deadline": deadline or ""}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

# --- Tool Definition for Google ADK ---

process_image_ocr_tool = FunctionTool(
    name="processImageOcr",
    description="Extract text from images using OCR (supports local files and URLs)",
    function=process_image_ocr
)

parse_data_source_tool = FunctionTool(
    name="parseDataSource",
    description="Parse data from a file into a structured format for reporting (CSV, JSON, text)",
    function=parse_data_source
)

parse_raw_input_tool = FunctionTool(
    name="parseRawInput",
    description="Process raw input text into structured data for reporting",
    function=parse_raw_input
)

get_templates_tool = FunctionTool(
    name="getAvailableTemplates",
    description="List all available report templates",
    function=get_available_templates
)

generate_report_template_tool = FunctionTool(
    name="generateReportTemplate",
    description="Create a template for a specific report type with audience targeting",
    function=generate_report_template
)

generate_chart_tool = FunctionTool(
    name="generateChart",
    description="Create a data visualization chart (bar, line, pie, scatter)",
    function=generate_chart
)

render_report_tool = FunctionTool(
    name="renderReport",
    description="Render a report using a template and content",
    function=render_report
)

export_report_tool = FunctionTool(
    name="exportReport",
    description="Export a report to a specified format (pdf, docx, md, html)",
    function=export_report
)

schedule_report_tool = FunctionTool(
    name="scheduleReport",
    description="Schedule a report for recurring generation",
    function=schedule_report
)

# --- Agent Initialization ---

# Creating the report agent with specialized sub-agents

# Execution agent for data processing and chart generation
execution_agent = Agent(
    name="execution_agent",
    model=LiteLlm(model="openai/gpt-4o", api_key=OPENAI_API_KEY),
    instruction="Data processing specialist for report generation. Extract structured data from various inputs and create visualizations.",
    description="Processes raw inputs into structured data and creates charts/visualizations.",
    tools=[
        parse_data_source_tool,
        parse_raw_input_tool,
        process_image_ocr_tool,
        generate_chart_tool
    ]
)

# Template renderer agent for report formatting
template_agent = Agent(
    name="template_agent",
    model=LiteLlm(model="openai/gpt-4o", api_key=OPENAI_API_KEY),
    instruction="Expert in creating and rendering report templates based on audience and content requirements.",
    description="Creates and applies templates for different report types and audiences.",
    tools=[
        get_templates_tool,
        generate_report_template_tool,
        render_report_tool
    ]
)

# Report export agent for document generation
export_agent = Agent(
    name="export_agent",
    model=LiteLlm(model="openai/gpt-4o", api_key=OPENAI_API_KEY),
    instruction="Specialist in report formatting and exporting to various document formats.",
    description="Exports reports to PDF, DOCX, HTML, and Markdown formats.",
    tools=[
        export_report_tool,
        schedule_report_tool
    ]
)

# Main reporting agent that coordinates the sub-agents
report_agent = Agent(
    name="reporting_agent",
    model=LiteLlm(model="openai/gpt-4o", api_key=OPENAI_API_KEY),
    instruction="""Generate and visualize structured reports from various data sources using templates, prompts, and agent-based synthesis logic.

Key capabilities:
1. Create professional reports including Strategic Plans, Financial Reports, Stakeholder Reports, Meeting Summaries, and Project Briefs
2. Process multiple input formats including structured JSON, CSV, raw notes, and images (OCR)
3. Target reports for specific audiences (internal, executive, investor, client, public)
4. Include data visualizations, charts, and metrics
5. Export to multiple formats (Markdown, PDF, HTML, DOCX)
6. Support for scheduled reporting and workflow integration

When handling requests:
- Understand the report type, audience, and required content
- Extract data from provided inputs or request necessary information
- Select appropriate templates and customize based on the target audience
- Generate professional, well-structured reports with proper formatting
- Include relevant visualizations to enhance understanding""",
    description="Comprehensive reporting system for creating professional documents from various data sources.",
    sub_agents=[execution_agent, template_agent, export_agent],
    tools=[]
)

# Initialize sub-agents list
sub_agents = [report_agent]

# Add RAG agent if VertexAI is available
if vertex_ai_available and ask_vertex_retrieval is not None:
    rag_agent = Agent(
        model=LiteLlm(model="openai/gpt-4o", api_key=OPENAI_API_KEY),
        name='ask_rag_agent',
        instruction=return_instructions_root(),
        tools=[ask_vertex_retrieval],
    )
    sub_agents.append(rag_agent)

# Root agent for orchestration
root_agent = Agent(
    name="eleanor_root_agent",
    model=LiteLlm(model="gemini/gemini-2.0-flash", api_key=GOOGLE_API_KEY),
    description="Orchestrator for multi-agent routing only.",
    instruction="Route requests to the appropriate sub-agent or answer directly.",
    tools=[],
    sub_agents=sub_agents,
)
