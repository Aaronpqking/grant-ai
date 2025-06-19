# Deploying to Vercel

This document outlines how to deploy the Grant Proposal Frontend to Vercel directly from GitHub.

## Prerequisites

1. A GitHub account with this repository pushed to it
2. A Vercel account (can sign up with GitHub)

## Deployment Steps

### 1. Connect to Vercel

1. Go to [Vercel](https://vercel.com/) and sign in with your GitHub account
2. Click "Add New..." and select "Project"
3. Import your GitHub repository
4. Find and select the repository containing this frontend

### 2. Configure Project

1. Vercel will automatically detect that this is a Next.js project
2. Configure the following settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: `Grant_Agent_Vertex_Native/grant-proposal-frontend` (adjust if your structure differs)
   - **Build Command**: `next build` (default)
   - **Output Directory**: `.next` (default)
   - **Install Command**: `npm install` (default)

### 3. Environment Variables

If your application requires environment variables, add them in the Vercel project settings:

1. Go to the "Environment Variables" section
2. Add any required variables such as:
   - `NEXT_PUBLIC_API_URL`: URL of your backend API
   - Any other configuration variables needed

### 4. Deploy

1. Click "Deploy"
2. Vercel will build and deploy your application
3. Once complete, you'll receive a URL for your deployed application

### 5. Custom Domain (Optional)

1. In your project dashboard, go to "Settings" > "Domains"
2. Add your custom domain and follow the verification steps

## Continuous Deployment

Vercel automatically sets up continuous deployment from your GitHub repository:

- **Production Branch**: Pushes to your main branch will trigger a production deployment
- **Preview Deployments**: Pull requests will create preview deployments

## Troubleshooting

If you encounter build issues:

1. Check the build logs in Vercel
2. Ensure all dependencies are correctly listed in package.json
3. Verify that your Next.js configuration is correct
4. Check that environment variables are properly set

For more help, refer to [Vercel Documentation](https://vercel.com/docs) 