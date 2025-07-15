#!/usr/bin/env python3
"""
Setup script for Google Drive RAG System
Configures all necessary components for the RAG-enhanced grant writing system
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RAGSystemSetup:
    """Setup and configuration for RAG system"""
    
    def __init__(self):
        self.config = {}
        self.setup_complete = False
    
    def setup_environment_variables(self):
        """Setup required environment variables"""
        logger.info("🔧 Setting up environment variables")
        
        env_vars = {
            'GOOGLE_CLOUD_PROJECT': 'eleanor-for-enterprise',
            'GOOGLE_CLOUD_REGION': 'us-central1',
            'GDRIVE_FOLDER_ID': 'root',
            'MAX_FILE_SIZE': '50000000',
            'LOG_LEVEL': 'INFO'
        }
        
        # Create .env file if it doesn't exist
        env_file = Path('.env')
        if not env_file.exists():
            with open(env_file, 'w') as f:
                f.write("# RAG System Configuration\n")
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            logger.info("✅ Created .env file with default configuration")
        else:
            logger.info("✅ .env file already exists")
        
        return True
    
    def setup_google_drive_auth(self):
        """Setup Google Drive authentication"""
        logger.info("🔑 Setting up Google Drive authentication")
        
        service_account_path = Path('service_account.json')
        if not service_account_path.exists():
            logger.warning("⚠️  Service account file not found")
            logger.info("📝 Please follow these steps to setup Google Drive authentication:")
            logger.info("   1. Go to Google Cloud Console")
            logger.info("   2. Create a service account")
            logger.info("   3. Download the service account key as 'service_account.json'")
            logger.info("   4. Place it in the project root directory")
            return False
        else:
            logger.info("✅ Service account file found")
            return True
    
    def setup_cache_directory(self):
        """Setup cache directory for direct Google Drive access"""
        logger.info("🗃️  Setting up cache directory")
        
        cache_path = Path('cache')
        if not cache_path.exists():
            cache_path.mkdir(parents=True, exist_ok=True)
            logger.info("✅ Created cache directory")
        else:
            logger.info("✅ Cache directory already exists")
        
        return True
    
    def install_dependencies(self):
        """Check and install required dependencies"""
        logger.info("📦 Checking dependencies")
        
        required_packages = [
            'fastapi',
            'uvicorn',
            'python-dotenv',
            'google-cloud-aiplatform',
            'google-api-python-client',
            'tiktoken',
            'vertexai'
        ]
        
        try:
            import subprocess
            import sys
            
            for package in required_packages:
                try:
                    __import__(package.replace('-', '_'))
                    logger.info(f"✅ {package} is installed")
                except ImportError:
                    logger.warning(f"⚠️  {package} is not installed")
                    logger.info(f"Installing {package}...")
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                    logger.info(f"✅ {package} installed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False
    
    def create_sample_config(self):
        """Create sample configuration files"""
        logger.info("📋 Creating sample configuration files")
        
        # Create sample service account info
        sample_service_account = {
            "type": "service_account",
            "project_id": "your-project-id",
            "private_key_id": "your-private-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
            "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
            "client_id": "your-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
        }
        
        sample_file = Path('service_account.json.example')
        if not sample_file.exists():
            with open(sample_file, 'w') as f:
                json.dump(sample_service_account, f, indent=2)
            logger.info("✅ Created service_account.json.example")
        
        # Create deployment script
        deployment_script = """#!/bin/bash
# RAG System Deployment Script

echo "🚀 Starting RAG System Deployment"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running integration tests..."
python test_rag_integration.py

# Start the enhanced service
echo "🌐 Starting enhanced grant agent service..."
python vertex_grant_agent_enhanced.py

echo "✅ RAG System deployment complete!"
"""
        
        deploy_file = Path('deploy_rag_system.sh')
        if not deploy_file.exists():
            with open(deploy_file, 'w') as f:
                f.write(deployment_script)
            os.chmod(deploy_file, 0o755)
            logger.info("✅ Created deployment script")
        
        return True
    
    def validate_setup(self):
        """Validate that all components are properly configured"""
        logger.info("🔍 Validating RAG system setup")
        
        checks = [
            ("Environment variables", self._check_env_vars),
            ("Google Drive auth", self._check_google_auth),
            ("Cache directory", self._check_cache_dir),
            ("Dependencies", self._check_dependencies)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                if result:
                    logger.info(f"✅ {check_name}: PASSED")
                else:
                    logger.error(f"❌ {check_name}: FAILED")
                    all_passed = False
            except Exception as e:
                logger.error(f"💥 {check_name}: ERROR - {e}")
                all_passed = False
        
        return all_passed
    
    def _check_env_vars(self):
        """Check if environment variables are set"""
        required_vars = ['GOOGLE_CLOUD_PROJECT', 'GOOGLE_CLOUD_REGION']
        
        from dotenv import load_dotenv
        load_dotenv()
        
        for var in required_vars:
            if not os.getenv(var):
                return False
        return True
    
    def _check_google_auth(self):
        """Check Google authentication"""
        return Path('service_account.json').exists()
    
    def _check_cache_dir(self):
        """Check cache directory setup"""
        return Path('cache').exists()
    
    def _check_dependencies(self):
        """Check if all dependencies are installed"""
        try:
            import fastapi
            import vertexai
            import tiktoken
            return True
        except ImportError:
            return False
    
    def run_setup(self):
        """Run complete setup process"""
        logger.info("🚀 Starting RAG System Setup")
        
        setup_steps = [
            ("Environment variables", self.setup_environment_variables),
            ("Google Drive authentication", self.setup_google_drive_auth),
            ("Cache directory", self.setup_cache_directory),
            ("Dependencies", self.install_dependencies),
            ("Sample configuration", self.create_sample_config),
            ("Validation", self.validate_setup)
        ]
        
        all_successful = True
        
        for step_name, step_func in setup_steps:
            logger.info(f"🔄 Running: {step_name}")
            
            try:
                result = step_func()
                if result:
                    logger.info(f"✅ {step_name}: SUCCESS")
                else:
                    logger.error(f"❌ {step_name}: FAILED")
                    all_successful = False
            except Exception as e:
                logger.error(f"💥 {step_name}: ERROR - {e}")
                all_successful = False
        
        if all_successful:
            logger.info("🎉 RAG System setup completed successfully!")
            logger.info("📝 Next steps:")
            logger.info("   1. Configure your Google Drive service account")
            logger.info("   2. Update the GDRIVE_FOLDER_ID in .env file")
            logger.info("   3. Run: python test_rag_integration.py")
            logger.info("   4. Start the service: python vertex_grant_agent_enhanced.py")
        else:
            logger.error("⚠️  RAG System setup completed with errors")
            logger.info("🔧 Please review the errors above and fix them")
        
        return all_successful


def main():
    """Main setup function"""
    setup = RAGSystemSetup()
    setup.run_setup()


if __name__ == "__main__":
    main() 