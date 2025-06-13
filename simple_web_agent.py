#!/usr/bin/env python3
"""
Simple Web-Compatible Grant Agent for ADK Platform
Focused on reliability and ease of deployment.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Use the correct ADK imports
from google.adk import Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleGrantAgent:
    """Simple, reliable Grant Agent for web deployment"""
    
    def __init__(self):
        self.input_dir = Path("input")
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
    def process_grant_request(self, user_message: str = "") -> str:
        """Process grant request and return response"""
        
        try:
            # Check for enhanced components
            enhanced_available = self._check_enhanced_components()
            
            if enhanced_available:
                return self._process_with_enhanced_system(user_message)
            else:
                return self._process_with_basic_system(user_message)
                
        except Exception as e:
            logger.error(f"Grant processing error: {e}")
            return f"""🚨 **Processing Error**
            
An error occurred: {str(e)}

**Troubleshooting:**
• Check if input documents are available
• Verify system components are properly installed
• Try again with different documents
• Contact support if issues persist"""
    
    def _check_enhanced_components(self) -> bool:
        """Check if enhanced grant builder components are available"""
        try:
            from Grant_Agent_Refactored.enhanced_grant_builder_v2 import run_comprehensive_test
            return True
        except ImportError:
            return False
    
    def _process_with_enhanced_system(self, user_message: str) -> str:
        """Process using the enhanced grant builder system"""
        
        try:
            from Grant_Agent_Refactored.enhanced_grant_builder_v2 import (
                SuperEnhancedExtractionService,
                CompatibleLanguageAnalysisService,
                generate_comprehensive_narrative
            )
            from Grant_Agent_Refactored.refactored.models import GrantWorkflowData
            from Grant_Agent_Refactored.refactored.services import DocumentService
            
            # Initialize services
            doc_service = DocumentService()
            extraction_service = SuperEnhancedExtractionService()
            analysis_service = CompatibleLanguageAnalysisService()
            workflow_data = GrantWorkflowData()
            
            # Process documents from input directory
            processed_docs = []
            all_text = ""
            
            if self.input_dir.exists():
                for doc_file in self.input_dir.glob("*.docx"):
                    try:
                        with open(doc_file, 'rb') as f:
                            file_data = f.read()
                        
                        doc_data = doc_service.process_upload(
                            file_data, 
                            doc_file.name, 
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                        )
                        workflow_data.add_document(doc_data)
                        processed_docs.append(doc_file.name)
                        
                        if hasattr(doc_data, 'content') and doc_data.content:
                            all_text += doc_data.content + "\n"
                            
                    except Exception as e:
                        logger.error(f"Error processing {doc_file}: {e}")
                        continue
            
            if not processed_docs:
                return """📁 **No Documents Found**
                
Please add grant documents to the `input/` directory:
• Organization information documents
• Funder RFPs or guidelines
• Previous grant proposals
• Any relevant DOCX files

Supported formats: DOCX, PDF, PPTX"""
            
            # Extract data
            org = extraction_service.extract_organization_super_enhanced(all_text)
            funder = extraction_service.extract_funder_super_enhanced(all_text)
            
            if not org or not funder:
                return f"""⚠️ **Partial Data Extraction**
                
**Processed:** {len(processed_docs)} documents
**Organization:** {'✅ Found' if org else '❌ Not found'}
**Funder:** {'✅ Found' if funder else '❌ Not found'}

**Next Steps:**
• Ensure documents contain clear organization information
• Include funder guidelines or RFP documents
• Add more comprehensive grant documents"""
            
            # Analyze alignment
            analysis = analysis_service.analyze_alignment_compatible(org, funder)
            
            # Generate narrative
            narrative = generate_comprehensive_narrative(org, funder, analysis)
            
            # Save output
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.output_dir / f"grant_proposal_{timestamp}.txt"
            
            with open(output_file, 'w') as f:
                f.write(narrative)
            
            return f"""🎉 **Grant Proposal Generated Successfully!**

## 📊 **Processing Summary**
- **Documents Processed:** {len(processed_docs)}
- **Organization:** {org.name}
- **Funder:** {funder.name} 
- **Grant Amount:** ${funder.grant_amount:,.0f}
- **Alignment Score:** {analysis.alignment_score:.2f}/1.00

## 🎯 **Quality Metrics**
- **Themes Matched:** {len(analysis.matching_themes)}/8
- **Matching Themes:** {', '.join(analysis.matching_themes)}
- **Narrative Length:** {len(narrative):,} characters

## 📄 **Output**
- **File:** {output_file.name}
- **Location:** output/ directory
- **Status:** Ready for review and submission

## 🚀 **Next Steps**
1. Review the generated proposal in `{output_file}`
2. Customize sections as needed for your specific program
3. Add budget details and supporting documents
4. Submit to {funder.name}

Your professional grant proposal is ready! 🎯"""
            
        except Exception as e:
            logger.error(f"Enhanced processing error: {e}")
            return f"Enhanced processing failed: {str(e)}"
    
    def _process_with_basic_system(self, user_message: str) -> str:
        """Process using basic system when enhanced components unavailable"""
        
        return """🔧 **Basic Grant Agent Mode**
        
The enhanced grant builder components are not available, but I can still help!

**What I can do in basic mode:**
• Provide grant writing guidance and best practices
• Help structure your grant proposal
• Review and suggest improvements to your narrative
• Answer questions about grant requirements

**To enable enhanced features:**
1. Ensure Grant_Agent_Refactored directory is properly set up
2. Install required dependencies
3. Test the enhanced grant builder system

**For now, please:**
• Share your grant writing questions
• Upload documents for manual review
• Ask for specific guidance on proposal sections

How can I help with your grant proposal today?"""

# Create the simple grant agent
simple_grant_agent = SimpleGrantAgent()

class GrantWriterAgent(Agent):
    """ADK Agent for Grant Writing with enhanced capabilities when available"""
    
    def __init__(self):
        # Use only the required parameter: name (must be valid identifier)
        super().__init__(name="grant_writer_agent")
        self.grant_processor = simple_grant_agent
        self.logger = logging.getLogger(__name__)
        
        # Setup callbacks
        self._setup_callbacks()
        
    def _setup_callbacks(self):
        """Setup agent callbacks for processing"""
        
        @self.before_model_callback
        def process_files(ctx):
            """Process any uploaded files"""
            try:
                if hasattr(ctx, 'files') and ctx.files:
                    self.logger.info(f"Processing {len(ctx.files)} uploaded files")
                    # Handle file uploads here when ADK supports it
                
                return ctx
            except Exception as e:
                self.logger.error(f"File processing error: {e}")
                return ctx
        
        @self.after_model_callback  
        def enhance_response(ctx):
            """Enhance response with grant processing"""
            try:
                # Get user message
                user_message = str(ctx.user_message) if hasattr(ctx, 'user_message') else ""
                
                # Process grant request
                enhanced_response = self.grant_processor.process_grant_request(user_message)
                
                # Combine with any existing response
                if hasattr(ctx, 'response') and ctx.response:
                    ctx.response = f"{ctx.response}\n\n{enhanced_response}"
                else:
                    ctx.response = enhanced_response
                
                return ctx
                
            except Exception as e:
                self.logger.error(f"Response enhancement error: {e}")
                return ctx

# Create the agent
agent = GrantWriterAgent()

# Add a function to handle user interactions
def handle_user_message(message: str) -> str:
    """Handle user messages and process grant requests"""
    return simple_grant_agent.process_grant_request(message)

# Export for ADK web server
__all__ = ["agent", "simple_grant_agent", "handle_user_message"]

# Test function
def test_simple_agent():
    """Test the simple agent functionality"""
    print("🧪 Testing Simple Grant Agent")
    print("=" * 40)
    
    try:
        print(f"✅ Agent created: {agent.name}")
        
        # Test processing
        result = simple_grant_agent.process_grant_request("Test message")
        print(f"✅ Processing test completed")
        print(f"📝 Response length: {len(result)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    test_simple_agent() 