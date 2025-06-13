#!/bin/bash

# Deploy with increased request size limits for large file uploads
echo "🚀 Deploying Grant Agent with 500MB upload support..."

# Set project and region
PROJECT_ID="eleanor-for-enterprise"
REGION="us-central1"
SERVICE_NAME="vertex-grant-agent"

echo "📦 Building and deploying to Cloud Run with large upload limits..."

# Deploy with increased memory, CPU, and request size limits
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 900 \
  --concurrency 10 \
  --max-instances 50 \
  --set-env-vars "ARTIFACT_MAX_SIZE_MB=500" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --set-env-vars "GOOGLE_CLOUD_REGION=$REGION" \
  --port 8080

echo "✅ Deployment complete!"
echo "🌐 Service URL: https://$SERVICE_NAME-$(gcloud config get-value project | tr ':' '-' | tr '.' '-')-uc.a.run.app"
echo ""
echo "📁 Upload Limits:"
echo "  • Per file: 500MB"
echo "  • Total request: Automatic chunking for >30MB"
echo "  • Timeout: 15 minutes"
echo "  • Memory: 4GB"
echo "  • CPU: 2 cores" 