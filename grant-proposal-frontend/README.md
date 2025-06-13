# 🚀 Grant Proposal AI - Frontend

A modern, AI-powered grant proposal generation platform built with Next.js, React, and Tailwind CSS. This application connects to your deployed Vertex AI Grant Agent service to create compelling grant proposals in minutes.

## ✨ Features

### 🏠 Dashboard
- **Real-time API Health Monitoring** - Live status of your Vertex AI backend
- **Proposal Analytics** - Track success rates, total funding, and proposal metrics
- **Recent Proposals** - Quick access to your latest generated proposals
- **Quick Actions** - Fast navigation to proposal creation tools

### ⚡ Quick Proposal Generator  
- **4-Step Wizard** - Guided form with progress tracking
- **AI-Powered Suggestions** - Smart recommendations for organization names, project titles, and descriptions
- **Real-time Validation** - Input validation and error handling
- **Instant Generation** - Create proposals in under 5 minutes
- **Download & Export** - Save proposals as text files

### 📋 Full Proposal Builder
- **Comprehensive Sections** - Organization info, funder details, project specifications
- **Document Upload** - Support for PDFs, Word docs, and text files
- **Tabbed Interface** - Organized workflow with progress tracking
- **Advanced Features** - Timeline management, budget planning, evaluation metrics
- **Rich Text Editing** - Detailed forms for complex proposals

### 🔧 Technical Features
- **Responsive Design** - Works perfectly on desktop, tablet, and mobile
- **Modern UI/UX** - Clean, professional interface with smooth animations
- **Error Handling** - Graceful error management and user feedback
- **Local Storage** - Automatic saving of proposals and form data
- **Real-time Updates** - Live status indicators and progress tracking

## 🛠️ Technology Stack

- **Frontend Framework**: Next.js 14 with App Router
- **UI Library**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom components
- **Icons**: Lucide React
- **API Integration**: Fetch API with custom client
- **State Management**: React Hooks (useState, useEffect)
- **File Handling**: Browser File API
- **Backend Integration**: Vertex AI Grant Agent Service

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Access to deployed Vertex AI Grant Agent service

### Installation

1. **Clone and Install**
   ```bash
   cd grant-proposal-frontend
   npm install
   ```

2. **Configure Environment**
   ```bash
   echo "NEXT_PUBLIC_GRANT_API_URL=https://vertex-grant-agent-46681871020.us-central1.run.app" > .env.local
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

4. **Open Application**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
grant-proposal-frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx           # Dashboard homepage
│   │   ├── proposal/
│   │   │   ├── quick/page.tsx # Quick proposal generator
│   │   │   └── full/page.tsx  # Full proposal builder
│   │   └── layout.tsx         # Root layout
│   ├── components/            # React components
│   │   ├── dashboard.tsx      # Main dashboard component
│   │   ├── quick-proposal-form.tsx    # Quick proposal wizard
│   │   └── full-proposal-builder.tsx  # Full proposal interface
│   └── lib/
│       └── api.ts            # API client for backend integration
├── public/                   # Static assets
├── .env.local               # Environment variables (create this)
└── package.json             # Dependencies and scripts
```

## 🔌 API Integration

The application connects to your deployed Vertex AI service with the following endpoints:

- **Health Check**: `GET /health` - Service status monitoring
- **Quick Proposal**: `POST /quick_proposal` - Fast proposal generation
- **Full Proposal**: `POST /generate_grant_proposal` - Comprehensive proposals
- **Document Upload**: `POST /upload_documents` - File processing (future feature)

### API Client Usage

```typescript
import { grantAPI } from '@/lib/api'

// Generate quick proposal
const response = await grantAPI.generateQuickProposal({
  organization_name: "Your Organization",
  project_title: "Your Project",
  funder_name: "Target Funder",
  amount_requested: "50000",
  project_description: "Project details..."
})

// Check service health
const health = await grantAPI.checkHealth()
```

## 🎨 Key Components

### Dashboard Component
- Real-time API health monitoring
- Proposal statistics and analytics
- Quick action cards for navigation
- Recent proposals list with status indicators

### Quick Proposal Form
- Multi-step wizard with progress tracking
- AI-powered suggestions and auto-completion
- Form validation and error handling
- Success state with download functionality

### Full Proposal Builder
- Tabbed interface for complex proposals
- Document upload and management
- Comprehensive form sections
- Review and generation workflow

## 🔧 Customization

### Styling
The application uses Tailwind CSS for styling. Customize the design by:

1. **Colors**: Modify color schemes in `tailwind.config.js`
2. **Components**: Update component styles in individual files
3. **Layout**: Adjust spacing and layout in page components

### API Configuration
Update the API integration by modifying `src/lib/api.ts`:

```typescript
const API_BASE = process.env.NEXT_PUBLIC_GRANT_API_URL || 'your-api-url'
```

### Features
Add new features by:
1. Creating new components in `src/components/`
2. Adding new pages in `src/app/`
3. Extending the API client in `src/lib/api.ts`

## 🚀 Deployment

### Vercel (Recommended)
```bash
npm install -g vercel
vercel --prod
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Manual Build
```bash
npm run build
npm start
```

## 🧪 Development

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Create production build
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Adding New Features
1. Create component in `src/components/`
2. Add routing in `src/app/`
3. Update API client if needed
4. Test with development server

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Check the [Issues](../../issues) section
- Review the API documentation
- Ensure your Vertex AI service is running
- Verify environment variables are set correctly

## 🎯 Roadmap

- [ ] Real-time collaboration features  
- [ ] Advanced document intelligence
- [ ] Template library and customization
- [ ] Analytics dashboard
- [ ] Mobile app version
- [ ] Integration with grant databases

---

**Built with ❤️ using Next.js, React, and Vertex AI** 