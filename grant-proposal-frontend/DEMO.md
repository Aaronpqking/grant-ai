# 🎬 Grant Proposal AI - Demo Guide

Welcome to your Grant Proposal AI platform! This guide will walk you through using the application to create compelling grant proposals.

## 🚀 Getting Started

### 1. Access the Application
- Navigate to `http://localhost:3000` in your browser
- You should see the **Grant Proposal AI Dashboard**

### 2. Dashboard Overview
The dashboard shows you:
- **API Status**: Green indicator shows your Vertex AI service is online
- **Statistics**: Proposal metrics and success rates
- **Quick Actions**: Two main proposal creation options
- **Recent Proposals**: Your previously generated proposals

## ⚡ Quick Proposal Demo

### Step 1: Start Quick Proposal
1. Click **"Quick Proposal"** card or the **"New Proposal"** button
2. You'll see a 4-step wizard interface

### Step 2: Fill Organization Info
```
Organization Name: Freedom Equity Inc.
```
- Notice AI suggestions appear as you type
- Click suggestions to auto-fill

### Step 3: Project Details
```
Project Title: Digital Literacy Training for Underserved Communities
Project Description: A comprehensive program designed to provide digital literacy training to underserved communities, focusing on essential computer skills, internet safety, and digital communication tools. The program will serve 500 participants over 12 months, with measurable outcomes in employment readiness and digital confidence.
```

### Step 4: Funding Information
```
Funder Name: Gates Foundation
Amount Requested: 75000
```

### Step 5: Review & Generate
1. Review all information in the final step
2. Click **"Generate Proposal"** 
3. Watch as your AI agent creates a comprehensive proposal
4. Download the finished proposal as a text file

## 📋 Full Proposal Builder Demo

### Step 1: Access Full Builder
1. From the dashboard, click **"Full Proposal Builder"**
2. You'll see a tabbed interface with 5 sections

### Step 2: Complete Each Tab

#### Organization Tab
```
Organization Name: Freedom Equity Inc.
Mission Statement: To provide equitable access to technology and digital literacy education for underserved communities.
Organization History: Founded in 2020, Freedom Equity has served over 2,000 community members through various digital inclusion programs.
Leadership Team: Dr. Sarah Johnson (Executive Director), 15 years experience in community development...
```

#### Funder Info Tab
```
Funder Name: Ford Foundation
Funding Priorities: Social justice, digital equity, community empowerment
Requirements: Projects must demonstrate measurable community impact and sustainability
Deadline: December 31, 2024
Contact: Program Officer, Digital Futures Initiative
```

#### Project Details Tab
```
Project Title: Community Digital Empowerment Initiative
Executive Summary: A 24-month program to establish digital learning centers in 5 underserved neighborhoods...
Goals: Train 1,000 community members, establish 3 permanent learning centers, achieve 85% job placement rate...
Methodology: Community-based participatory approach with peer mentoring...
Timeline: Phase 1 (Months 1-6): Setup and recruitment, Phase 2 (Months 7-18): Training delivery...
Budget: $150,000 total - $75,000 personnel, $50,000 equipment, $25,000 operations
Evaluation: Pre/post assessments, employment tracking, community impact surveys
Sustainability: Revenue from certificate programs, local partnerships, ongoing funding applications
```

#### Documents Tab
1. Upload supporting documents (optional)
2. Add budgets, organizational charts, letters of support

#### Review Tab
1. Review all sections
2. Click **"Generate Full Proposal"**
3. Download comprehensive proposal

## 🎯 Expected Results

### Quick Proposal Output
You should receive a 2-3 page proposal including:
- Executive Summary
- Project Description
- Goals and Objectives
- Implementation Plan
- Budget Overview
- Expected Outcomes

### Full Proposal Output
You should receive a comprehensive 8-12 page proposal including:
- Cover Letter
- Organization Background
- Detailed Project Narrative
- Methodology and Timeline
- Budget Justification
- Evaluation Plan
- Sustainability Strategy
- Appendices

## 🔧 Testing API Integration

### Health Check
1. Dashboard should show "API Online" status
2. If offline, check your Vertex AI service deployment

### Error Handling
1. Try submitting incomplete forms to see validation
2. Disconnect internet to test error messages
3. Check console for detailed error logs

## 📊 Demo Data

Use this sample data for testing:

### Sample Organization
```json
{
  "name": "Community Tech Alliance",
  "mission": "Bridging the digital divide through community-based technology education",
  "history": "Established 2018, served 5,000+ participants",
  "leadership": "Maria Rodriguez (CEO), 20 years nonprofit experience"
}
```

### Sample Project
```json
{
  "title": "Youth Digital Skills Program",
  "description": "12-week coding bootcamp for teens aged 14-18 in low-income areas",
  "goals": "Train 200 youth, 90% completion rate, 75% job placement",
  "budget": "85000"
}
```

### Sample Funder
```json
{
  "name": "Robert Wood Johnson Foundation",
  "priorities": "Health equity, community development, youth empowerment",
  "requirements": "Evidence-based approaches, community partnerships"
}
```

## 🎉 Success Indicators

Your demo is successful when you can:

✅ **Navigate** smoothly between dashboard and proposal builders  
✅ **Generate** both quick and full proposals without errors  
✅ **Download** proposals as text files  
✅ **See** API health status as "Online"  
✅ **Experience** responsive design on different screen sizes  
✅ **Observe** real-time form validation and suggestions  
✅ **Complete** the full workflow from start to download  

## 🐛 Troubleshooting

### Common Issues

**API Offline**: 
- Check Vertex AI service deployment
- Verify environment variables
- Test service with `curl https://vertex-grant-agent-46681871020.us-central1.run.app/health`

**Form Not Submitting**:
- Check browser console for errors
- Ensure all required fields are completed
- Verify network connectivity

**Styling Issues**:
- Clear browser cache
- Check Tailwind CSS is loading
- Refresh the page

### Debug Mode
Open browser developer tools (F12) to:
- Monitor network requests
- Check console errors
- Inspect API responses

## 🎯 Next Steps

After successful demo:
1. **Customize** the interface for your organization
2. **Deploy** to production (Vercel, Netlify, etc.)
3. **Integrate** with additional services
4. **Train** team members on usage
5. **Scale** for organizational needs

---

**🎉 Congratulations! You've successfully built and tested your AI-powered grant proposal platform!** 

## Quick Demo Steps

### 1. Start the Application 
```bash
cd /Users/aurictechnology/Grant/adk-docs/Grant_Agent_Vertex_Native/grant-proposal-frontend
npm run dev
```
Visit: http://localhost:3000

### 2. Dashboard Overview
- **Top Section**: API health status (shows "API Online" when connected to Vertex AI)
- **Stats Cards**: View proposal metrics (populated from localStorage)
- **Action Cards**: Two main pathways - Quick Proposal (5 min) vs Full Proposal (comprehensive)
- **Recent Proposals**: Shows your generated proposals history

### 3. Quick Proposal Demo (5 minutes)
Navigate to: http://localhost:3000/proposal/quick

**Step 1 - Organization Info:**
- Organization Name: `Freedom Equity Inc.`

**Step 2 - Project Details:**
- Project Title: `Digital Literacy for Underserved Communities`
- Project Description: `Our program will provide digital literacy training to 500 individuals in underserved communities over 18 months. We will establish learning centers in community venues and provide tablets, internet access, and comprehensive training in basic computer skills, internet safety, and essential digital tools.`

**Step 3 - Funding Details:**
- Funder Name: `Gates Foundation`
- Amount Requested: `50000`

**Step 4 - Review & Generate:**
- Review all information
- Click "Generate Proposal"
- Download the generated proposal

### 4. Full Proposal Demo (15+ minutes)
Navigate to: http://localhost:3000/proposal/full

**Organization Tab:**
- Name: `Freedom Equity Inc.`
- Mission: `To promote equity and opportunity in underserved communities through education, technology access, and economic development initiatives`
- Established: `2018`
- Tax ID: `12-3456789`
- Website: `https://freedomequity.org`
- Address: `123 Community St., Chicago, IL 60601`
- Contact Person: `Jane Smith`
- Contact Email: `jsmith@freedomequity.org`
- Contact Phone: `(312) 555-0123`

**Funder Info Tab:**
- Funder Name: `Gates Foundation`
- Grant Program: `Digital Equity Initiative`
- Application Deadline: Select a future date
- Funding Range: Min `50000`, Max `100000`
- Focus Areas: `Digital literacy, educational technology, community development, underserved populations`
- Requirements: `Must serve at least 500 individuals, provide measurable outcomes, demonstrate sustainability plan`

**Project Details Tab:**
- Project Title: `Digital Literacy for Underserved Communities`
- Executive Summary: `A comprehensive digital literacy program targeting 500 individuals in underserved Chicago neighborhoods through community-based learning centers and partnerships with local organizations.`
- Statement of Need: `Many residents in underserved Chicago communities lack basic digital skills necessary for employment, education, and civic engagement. This digital divide prevents access to opportunities and perpetuates inequality.`
- Project Description: `We will establish 5 digital learning centers in community venues, providing tablets, internet access, and comprehensive training programs covering basic computer skills, internet safety, job search techniques, and essential digital tools.`
- Total Budget: `75000`
- Timeline: `18 months (January 2024 - June 2025)`

**Documents Tab:**
- Upload sample PDFs or documents (optional)
- Add notes about any special requirements

**Review & Generate Tab:**
- Review all entered information
- Click "Generate Full Proposal"
- Download the comprehensive proposal

### 5. Key Features to Highlight

**AI-Powered Suggestions:**
- Quick Proposal form shows AI suggestions while typing
- Smart field completion based on organization type

**Real-time Validation:**
- Form progression only allows next step when required fields are completed
- Visual progress indicators show completion status

**Data Persistence:**
- Proposals saved to localStorage for demo purposes
- Recent proposals appear on dashboard
- Statistics update automatically

**Professional Output:**
- Generated proposals formatted for submission
- Download as text files
- Comprehensive structure following grant writing best practices

**API Integration:**
- Connects to deployed Vertex AI service
- Health monitoring shows connection status
- Fallback error handling when API is unavailable

### 6. API Endpoint Testing

The frontend connects to: `https://vertex-grant-agent-46681871020.us-central1.run.app`

**Available endpoints:**
- `GET /health` - API health check
- `POST /quick-proposal` - Generate quick proposal
- `POST /full-proposal` - Generate comprehensive proposal
- `POST /upload-document` - Document upload support

### 7. Troubleshooting

**If API shows "Offline":**
- Check the Vertex AI service is running
- Verify the API URL in `src/lib/api.ts`
- Check browser console for CORS or network errors

**If forms don't work:**
- Ensure all required fields are filled
- Check browser console for JavaScript errors
- Verify form validation logic

**Performance:**
- Initial proposal generation may take 10-30 seconds
- Subsequent requests are typically faster
- Large document uploads may take additional time

### 8. Demo Script for Presentations

1. **Start**: "Let me show you our AI-powered grant proposal generator"
2. **Dashboard**: "This is the command center showing all your proposal activity" 
3. **Quick Demo**: "For urgent deadlines, we can generate a proposal in under 5 minutes"
4. **Full Demo**: "For comprehensive grants, we provide a detailed builder with document support"
5. **Generated Output**: "The AI creates professional, compelling proposals ready for submission"
6. **Benefits**: "This saves hours of writing time while ensuring best practices and compliance"

### 9. Sample Generated Output

The AI will generate proposals with sections like:
- Executive Summary
- Statement of Need  
- Project Description
- Goals and Objectives
- Methodology
- Budget Justification
- Evaluation Plan
- Sustainability
- Organization Qualifications

Each section will be tailored to your specific project and funder requirements. 