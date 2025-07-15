#!/usr/bin/env python3
"""
Simple script to run the RAG service with proper environment configuration
"""
import os
import sys

# Set the environment variable
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'Grant_Agent_Vertex_Native/eleanor-for-enterprise-64bd78746cab.json'

# Load the RAG service
from google_drive_rag_service import GoogleDriveRAGService
import asyncio

async def run_rag_service():
    """Run the RAG service with proper authentication"""
    try:
        # Initialize the RAG service
        rag_service = GoogleDriveRAGService()
        await rag_service.initialize()
        
        print("🎉 RAG Service initialized successfully!")
        print(f"✅ Service account: {rag_service.config.service_account_path}")
        print(f"✅ File exists: {os.path.exists(rag_service.config.service_account_path)}")
        
        # Test a simple search
        results = await rag_service.search_funder_information(
            "Ford Foundation", 
            "environmental grants"
        )
        
        print("\n📊 Search Results:")
        print(f"Funder: {results.get('funder_name', 'N/A')}")
        print(f"Query: {results.get('query', 'N/A')}")
        print(f"Timestamp: {results.get('timestamp', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_rag_service())
    sys.exit(0 if success else 1) 