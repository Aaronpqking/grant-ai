#!/usr/bin/env python3
"""
RAG Research Agent for Grant Writing MAS
Integrates Google Drive RAG system with the existing Multi-Agent System
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

try:
    from google_drive_rag_service import GoogleDriveRAGService, initialize_rag_service
except ImportError:
    logging.error("google_drive_rag_service not found - make sure it's in the same directory")
    raise

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles in the MAS"""
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    WRITING = "writing"
    REVIEW = "review"
    COMPLIANCE = "compliance"


class TaskContext:
    """Context for task execution"""
    def __init__(self, task_id: str, task_type: str, data: Dict[str, Any]):
        self.task_id = task_id
        self.task_type = task_type
        self.data = data


class VertexAIConfig:
    """Configuration for Vertex AI"""
    def __init__(self, config_dict: Dict[str, Any]):
        self.project_id = config_dict.get('project_id', 'eleanor-for-enterprise')
        self.region = config_dict.get('region', 'us-central1')
        self.model_name = config_dict.get('model_name', 'gemini-1.5-pro')
        self.fast_model = config_dict.get('fast_model', 'gemini-1.5-flash')


class BaseAgent:
    """Base class for all agents"""
    def __init__(self, name: str, role: AgentRole, vertex_config: VertexAIConfig):
        self.name = name
        self.role = role
        self.vertex_config = vertex_config
        
        # Initialize Vertex AI
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        vertexai.init(project=vertex_config.project_id, location=vertex_config.region)
        self.model = GenerativeModel(vertex_config.model_name)
        self.fast_model = GenerativeModel(vertex_config.fast_model)
    
    async def generate_text(self, prompt: str, use_fast_model: bool = False) -> str:
        """Generate text using Vertex AI"""
        try:
            model = self.fast_model if use_fast_model else self.model
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return f"Error: {str(e)}"


class RAGResearchAgent(BaseAgent):
    """Research Agent that uses RAG system for funder intelligence"""
    
    def __init__(self, vertex_config: VertexAIConfig, rag_service: GoogleDriveRAGService):
        super().__init__(
            name="RAG Research Agent",
            role=AgentRole.RESEARCH,
            vertex_config=vertex_config
        )
        self.rag_service = rag_service
        self.research_cache = {}
        self.capabilities = [
            "funder_profile_research",
            "esg_analysis",
            "funding_priorities_extraction",
            "grant_requirements_analysis",
            "competitive_analysis"
        ]
    
    async def execute_task(self, context: TaskContext) -> Dict[str, Any]:
        """Execute research task using RAG system"""
        logger.info(f"🔬 RAG Research Agent executing task: {context.task_type}")
        
        try:
            if context.task_type == "funder_research":
                return await self._conduct_funder_research(context)
            elif context.task_type == "competitive_analysis":
                return await self._conduct_competitive_analysis(context)
            elif context.task_type == "requirement_analysis":
                return await self._analyze_grant_requirements(context)
            elif context.task_type == "esg_analysis":
                return await self._conduct_esg_analysis(context)
            else:
                return await self._general_research(context)
                
        except Exception as e:
            logger.error(f"Error in RAG Research Agent: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_research": await self._fallback_research(context)
            }
    
    async def _conduct_funder_research(self, context: TaskContext) -> Dict[str, Any]:
        """Conduct comprehensive funder research using RAG"""
        funder_name = context.data.get("funder_name")
        if not funder_name:
            return {"success": False, "error": "No funder name provided"}
        
        # Check cache first
        cache_key = f"funder_research_{funder_name}"
        if cache_key in self.research_cache:
            logger.info(f"Using cached research for {funder_name}")
            return self.research_cache[cache_key]
        
        logger.info(f"🔍 Conducting comprehensive RAG research for {funder_name}")
        
        # Get comprehensive funder profile
        funder_profile = await self.rag_service.get_funder_profile(funder_name)
        
        # Extract key insights
        insights = await self._extract_research_insights(funder_profile, context)
        
        # Generate strategic recommendations
        recommendations = await self._generate_strategic_recommendations(
            funder_profile, insights, context
        )
        
        result = {
            "success": True,
            "funder_name": funder_name,
            "timestamp": datetime.now().isoformat(),
            "profile": funder_profile,
            "insights": insights,
            "recommendations": recommendations,
            "research_quality": self._assess_research_quality(funder_profile)
        }
        
        # Cache the result
        self.research_cache[cache_key] = result
        
        logger.info(f"✅ Completed comprehensive research for {funder_name}")
        return result
    
    async def _conduct_competitive_analysis(self, context: TaskContext) -> Dict[str, Any]:
        """Conduct competitive analysis using RAG"""
        funder_name = context.data.get("funder_name")
        sector = context.data.get("sector", "nonprofit")
        
        # Search for competitive information
        competitive_info = await self.rag_service.search_funder_information(
            funder_name,
            f"recent grants awarded competitive funding {sector}",
            ["annual_report", "grant_guidelines"]
        )
        
        # Analyze competitive landscape
        analysis = await self._analyze_competitive_landscape(competitive_info)
        
        return {
            "success": True,
            "funder_name": funder_name,
            "sector": sector,
            "competitive_info": competitive_info,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_grant_requirements(self, context: TaskContext) -> Dict[str, Any]:
        """Analyze grant requirements using RAG"""
        funder_name = context.data.get("funder_name")
        
        # Search for requirements information
        requirements_info = await self.rag_service.search_funder_information(
            funder_name,
            "grant requirements eligibility criteria application process",
            ["grant_guidelines"]
        )
        
        # Extract and structure requirements
        structured_requirements = await self._structure_requirements(requirements_info)
        
        return {
            "success": True,
            "funder_name": funder_name,
            "requirements_info": requirements_info,
            "structured_requirements": structured_requirements,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _conduct_esg_analysis(self, context: TaskContext) -> Dict[str, Any]:
        """Conduct ESG analysis using RAG"""
        funder_name = context.data.get("funder_name")
        
        # Search for ESG information
        esg_info = await self.rag_service.search_funder_information(
            funder_name,
            "ESG environmental social governance sustainability priorities",
            ["esg_report", "annual_report"]
        )
        
        # Analyze ESG focus areas
        esg_analysis = await self._analyze_esg_focus(esg_info)
        
        return {
            "success": True,
            "funder_name": funder_name,
            "esg_info": esg_info,
            "esg_analysis": esg_analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _extract_research_insights(self, funder_profile: Dict, context: TaskContext) -> Dict[str, Any]:
        """Extract key insights from funder profile"""
        try:
            # Use AI to extract insights from the profile
            profile_text = json.dumps(funder_profile, indent=2)
            
            insight_prompt = f"""
            Analyze the following funder profile and extract key insights for grant writing:
            
            {profile_text}
            
            Extract:
            1. Key funding priorities and focus areas
            2. Decision-making criteria and preferences
            3. Recent funding trends and patterns
            4. Application success factors
            5. Strategic alignment opportunities
            
            Provide insights in JSON format with clear, actionable information.
            """
            
            insights_text = await self.generate_text(insight_prompt)
            
            # Try to parse as JSON, fallback to manual parsing
            try:
                insights = json.loads(insights_text)
            except json.JSONDecodeError:
                insights = self._manual_insight_extraction(funder_profile)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            return self._manual_insight_extraction(funder_profile)
    
    async def _generate_strategic_recommendations(self, profile: Dict, insights: Dict, context: TaskContext) -> List[str]:
        """Generate strategic recommendations for grant application"""
        try:
            org_info = context.data.get("organization_info", {})
            
            recommendation_prompt = f"""
            Based on the funder profile and insights, generate strategic recommendations for a grant application:
            
            Funder Profile Summary: {self._summarize_profile(profile)}
            Key Insights: {json.dumps(insights, indent=2)}
            Organization Info: {json.dumps(org_info, indent=2)}
            
            Provide 5-7 specific, actionable recommendations for maximizing grant application success.
            Focus on alignment strategies, application approach, and key messaging.
            """
            
            recommendations_text = await self.generate_text(recommendation_prompt)
            
            # Parse recommendations into list
            recommendations = []
            for line in recommendations_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    # Clean up formatting
                    clean_line = line.lstrip('-•0123456789. ')
                    if clean_line:
                        recommendations.append(clean_line)
            
            return recommendations[:7]  # Limit to 7 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return [
                "Align proposal with funder's stated priorities",
                "Emphasize measurable outcomes and impact",
                "Follow application guidelines precisely",
                "Highlight organizational capacity and experience",
                "Provide clear budget justification"
            ]
    
    def _assess_research_quality(self, funder_profile: Dict) -> Dict[str, Any]:
        """Assess quality of research data"""
        quality_metrics = {
            "completeness": 0,
            "recency": 0,
            "relevance": 0,
            "overall_score": 0
        }
        
        # Calculate completeness
        required_fields = ['funding_priorities', 'esg_focus', 'leadership_info', 
                          'recent_grants', 'application_process']
        found_fields = sum(1 for field in required_fields if funder_profile.get(field))
        quality_metrics["completeness"] = found_fields / len(required_fields)
        
        # Calculate overall score
        quality_metrics["overall_score"] = (
            quality_metrics["completeness"] * 0.5 +
            quality_metrics["recency"] * 0.3 +
            quality_metrics["relevance"] * 0.2
        )
        
        return quality_metrics
    
    def _manual_insight_extraction(self, funder_profile: Dict) -> Dict[str, Any]:
        """Manual insight extraction fallback"""
        insights = {
            "funding_focus": [],
            "decision_makers": [],
            "recent_trends": [],
            "application_insights": [],
            "alignment_opportunities": []
        }
        
        # Extract from funding priorities
        if funder_profile.get('funding_priorities'):
            funding_info = funder_profile['funding_priorities'].get('information', {})
            for doc_type, data in funding_info.items():
                if data.get('found') and data.get('summary'):
                    insights['funding_focus'].append(data['summary'])
        
        return insights
    
    def _summarize_profile(self, profile: Dict) -> str:
        """Create brief summary of funder profile"""
        summary_parts = []
        
        for key, value in profile.items():
            if isinstance(value, dict) and value.get('information'):
                found_items = [k for k, v in value['information'].items() if v.get('found')]
                if found_items:
                    summary_parts.append(f"{key}: {', '.join(found_items)}")
        
        return "; ".join(summary_parts) if summary_parts else "Limited profile information available"
    
    async def _analyze_competitive_landscape(self, competitive_info: Dict) -> Dict[str, Any]:
        """Analyze competitive landscape from RAG results"""
        analysis = {
            "competitive_advantage": [],
            "funding_patterns": [],
            "success_factors": [],
            "differentiation_opportunities": []
        }
        
        # Extract competitive insights from search results
        for doc_type, data in competitive_info.get('information', {}).items():
            if data.get('found') and data.get('documents'):
                for doc in data['documents']:
                    content = doc.get('content', '')
                    if 'competitive' in content.lower() or 'awarded' in content.lower():
                        analysis['competitive_advantage'].append(content[:200])
        
        return analysis
    
    async def _structure_requirements(self, requirements_info: Dict) -> Dict[str, Any]:
        """Structure requirements information"""
        structured = {
            "eligibility_criteria": [],
            "application_process": [],
            "deadlines": [],
            "required_documents": [],
            "funding_limits": []
        }
        
        # Extract structured requirements from search results
        for doc_type, data in requirements_info.get('information', {}).items():
            if data.get('found') and data.get('documents'):
                for doc in data['documents']:
                    content = doc.get('content', '')
                    
                    # Simple keyword-based extraction
                    if 'eligible' in content.lower():
                        structured['eligibility_criteria'].append(content[:200])
                    if 'deadline' in content.lower():
                        structured['deadlines'].append(content[:200])
                    if 'required' in content.lower():
                        structured['required_documents'].append(content[:200])
        
        return structured
    
    async def _analyze_esg_focus(self, esg_info: Dict) -> Dict[str, Any]:
        """Analyze ESG focus areas"""
        analysis = {
            "environmental_priorities": [],
            "social_impact_areas": [],
            "governance_standards": [],
            "sustainability_metrics": []
        }
        
        # Extract ESG insights from search results
        for doc_type, data in esg_info.get('information', {}).items():
            if data.get('found') and data.get('documents'):
                for doc in data['documents']:
                    content = doc.get('content', '').lower()
                    
                    if 'environmental' in content or 'climate' in content:
                        analysis['environmental_priorities'].append(doc.get('content', '')[:200])
                    if 'social' in content or 'community' in content:
                        analysis['social_impact_areas'].append(doc.get('content', '')[:200])
                    if 'governance' in content or 'board' in content:
                        analysis['governance_standards'].append(doc.get('content', '')[:200])
        
        return analysis
    
    async def _general_research(self, context: TaskContext) -> Dict[str, Any]:
        """General research task handler"""
        query = context.data.get("query", "general funder information")
        funder_name = context.data.get("funder_name", "Unknown")
        
        # Perform general search
        research_results = await self.rag_service.search_funder_information(
            funder_name, query
        )
        
        return {
            "success": True,
            "task_type": "general_research",
            "query": query,
            "funder_name": funder_name,
            "results": research_results,
            "summary": self._summarize_research_results(research_results),
            "timestamp": datetime.now().isoformat()
        }
    
    def _summarize_research_results(self, research_results: Dict) -> str:
        """Summarize research results"""
        if not research_results.get('information'):
            return "No research results found"
        
        summary_parts = []
        for doc_type, data in research_results['information'].items():
            if data.get('found') and data.get('summary'):
                summary_parts.append(f"{doc_type}: {data['summary']}")
        
        return " | ".join(summary_parts)
    
    async def _fallback_research(self, context: TaskContext) -> Dict[str, Any]:
        """Fallback research method when RAG fails"""
        logger.warning("Using fallback research method")
        
        funder_name = context.data.get("funder_name", "Unknown Funder")
        
        # Generate basic research using AI
        fallback_prompt = f"""
        Provide general information about {funder_name} for grant writing purposes:
        
        Include:
        1. Likely funding priorities
        2. Application process insights
        3. Success factors
        4. Common requirements
        """
        
        try:
            fallback_info = await self.generate_text(fallback_prompt)
            return {
                "method": "AI_fallback",
                "information": fallback_info,
                "reliability": "low"
            }
        except Exception as e:
            logger.error(f"Fallback research failed: {e}")
            return {
                "method": "manual_fallback",
                "information": f"Basic research template for {funder_name}",
                "reliability": "minimal"
            }


async def initialize_rag_research_agent(vertex_config: VertexAIConfig) -> RAGResearchAgent:
    """Initialize RAG research agent with dependencies"""
    try:
        # Initialize RAG service
        rag_service = await initialize_rag_service()
        
        # Create research agent
        research_agent = RAGResearchAgent(vertex_config, rag_service)
        
        logger.info("RAG Research Agent initialized successfully")
        return research_agent
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG Research Agent: {e}")
        raise


if __name__ == "__main__":
    # Test the research agent
    async def test_research_agent():
        try:
            vertex_config = VertexAIConfig({
                'project_id': 'eleanor-for-enterprise',
                'region': 'us-central1',
                'model_name': 'gemini-1.5-pro',
                'fast_model': 'gemini-1.5-flash'
            })
            
            research_agent = await initialize_rag_research_agent(vertex_config)
            
            # Test funder research
            test_context = TaskContext(
                task_id="test_001",
                task_type="funder_research",
                data={
                    "funder_name": "Ford Foundation",
                    "organization_info": {
                        "name": "Test Organization",
                        "sector": "environmental"
                    }
                }
            )
            
            result = await research_agent.execute_task(test_context)
            print("Research Agent Test Results:")
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"Test failed: {e}")
    
    asyncio.run(test_research_agent()) 