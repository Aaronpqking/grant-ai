#!/bin/bash

# Vertex AI Grant Agent - Google Cloud Deployment Script
# This script builds and deploys the agent to Google Cloud Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="eleanor-for-enterprise"
REGION="us-central1"
SERVICE_NAME="vertex-grant-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${BLUE}🚀 Starting Vertex AI Grant Agent deployment to Google Cloud${NC}"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW}📋 Setting up Google Cloud project: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable redis.googleapis.com

# Redis removed for simplified deployment - using direct GCS storage

# Build and deploy using Cloud Build
echo -e "${YELLOW}🏗️  Building and deploying with Cloud Build...${NC}"
gcloud builds submit --config cloudbuild.yaml

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${BLUE}📡 Service URL: ${SERVICE_URL}${NC}"
echo -e "${BLUE}🏥 Health Check: ${SERVICE_URL}/health${NC}"
echo -e "${BLUE}📚 API Docs: ${SERVICE_URL}/docs${NC}"

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
sleep 10
if curl -f "${SERVICE_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed. Check the logs:${NC}"
    echo -e "${YELLOW}gcloud logs read --service=${SERVICE_NAME} --limit=50${NC}"
fi

echo -e "${GREEN}🎉 Vertex AI Grant Agent is now running on Google Cloud!${NC}"
echo -e "${BLUE}To view logs: gcloud logs read --service=${SERVICE_NAME}${NC}"
echo -e "${BLUE}To update: gcloud builds submit --config cloudbuild.yaml${NC}" 