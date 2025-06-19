# Grant AI Proposal Builder Frontend

A Next.js frontend application for the Grant AI system, designed to help users create high-quality grant proposals using AI assistance.

## Features

- Interactive proposal builder
- Document upload and analysis
- AI-powered grant writing assistance
- Real-time feedback and suggestions
- Quick and comprehensive proposal options

## Tech Stack

- Next.js 15.3.3
- React 19
- Tailwind CSS
- Inter font (Google Fonts)

## Deployment to Vercel

### Option 1: Automatic Deployment via GitHub

1. Push your changes to GitHub
2. Log in to your Vercel account
3. Connect your GitHub repository
4. Select the `Grant_Agent_Vertex_Native/grant-proposal-frontend` directory as the root
5. Configure build settings:
   - Framework: Next.js
   - Root Directory: `Grant_Agent_Vertex_Native/grant-proposal-frontend`
6. Deploy

### Option 2: Using Vercel CLI

1. Install Vercel CLI: `npm install -g vercel`
2. Navigate to the frontend directory: `cd Grant_Agent_Vertex_Native/grant-proposal-frontend`
3. Run the deployment script: `./vercel-deploy.sh`

### Environment Variables

Set these environment variables in your Vercel project settings:

- `NEXT_PUBLIC_API_URL`: URL of your backend API
- `NEXT_PUBLIC_APP_ENV`: Set to `production` for production deployment

## Local Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Font Configuration

This project uses the Inter font from Google Fonts. The font is configured in:
- `src/app/layout.tsx` - Font import and variable setup
- `tailwind.config.js` - Font family configuration
- `src/app/globals.css` - CSS variables and base styles

## License

Proprietary - All rights reserved

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Sample Test Data

To quickly test the applications, you can use this sample data:

### Quick Proposal Sample Data
- **Organization Name**: Freedom Equity Inc.
- **Project Title**: Digital Literacy for Underserved Communities  
- **Funder Name**: Gates Foundation
- **Amount Requested**: 50000
- **Project Description**: Our program will provide digital literacy training to 500 individuals in underserved communities over 18 months. We will establish learning centers in community venues and provide tablets, internet access, and comprehensive training in basic computer skills, internet safety, and essential digital tools. The program includes partnerships with local libraries and community centers to ensure sustainability beyond the grant period.

### Full Proposal Sample Data
**Organization:**
- Name: Freedom Equity Inc.
- Mission: To promote equity and opportunity in underserved communities through education, technology access, and economic development initiatives
- Established: 2018
- Tax ID: 12-3456789
- Website: https://freedomequity.org
- Address: 123 Community St., Chicago, IL 60601
- Contact: Jane Smith, Executive Director
- Email: jsmith@freedomequity.org
- Phone: (312) 555-0123

**Funder:**
- Name: Gates Foundation
- Program: Digital Equity Initiative
- Focus Areas: Digital literacy, educational technology, community development, underserved populations
- Requirements: Must serve at least 500 individuals, provide measurable outcomes, demonstrate sustainability plan

**Project:**
- Title: Digital Literacy for Underserved Communities
- Budget: 75000
- Timeline: 18 months (January 2024 - June 2025)
- Summary: A comprehensive digital literacy program targeting 500 individuals in underserved Chicago neighborhoods through community-based learning centers and partnerships with local organizations.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
