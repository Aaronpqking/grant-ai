#!/bin/bash

# Vercel deployment script for Grant AI frontend

echo "📦 Preparing for Vercel deployment..."

# Install Vercel CLI if not already installed
if ! command -v vercel &> /dev/null; then
    echo "🔧 Installing Vercel CLI..."
    npm install -g vercel
fi

# Build the project
echo "🏗️ Building project..."
npm run build

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel --prod

echo "✅ Deployment complete!" 