# Changelog

## [Unreleased]

### Added - RAG System Implementation
- **Google Drive RAG Service**: Direct access to funder information via Google Drive API
- **RAG Research Agent**: MAS-integrated research agent for grant writing
- **Multitenant Architecture**: Support for multiple organizations with data isolation
- **Smart Caching**: 1-hour cache duration for optimal performance
- **Document Classification**: Automatic identification of ESG reports, annual reports, founder info, and grant guidelines
- **Comprehensive Testing**: Full integration test suite with 100% pass rate
- **Service Account Authentication**: Secure Google Drive API access
- **Setup and Deployment Scripts**: Automated system initialization

### Technical Details
- **Core Files**: `google_drive_rag_service.py`, `rag_research_agent.py`, `test_rag_integration.py`
- **Dependencies**: Added tiktoken, google-api-python-client, vertexai
- **Configuration**: Environment-based configuration with service account support
- **Architecture**: Direct access pattern (no ChromaDB) for minimal overhead
- **MAS Integration**: Primary orchestrator (decision making) + secondary orchestrator (intelligence)

### Documentation
- **Multitenancy Architecture**: Comprehensive guide for scaling to multiple tenants
- **Setup Instructions**: Step-by-step system initialization
- **API Reference**: Complete RAG service API documentation

## Previous Releases
- [Previous changelog entries would go here] 