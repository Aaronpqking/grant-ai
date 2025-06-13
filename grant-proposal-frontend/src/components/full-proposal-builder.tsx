'use client'

import React, { useState, useRef } from 'react'
import { Upload, FileText, X, Plus, Sparkles, CheckCircle, AlertCircle, Download } from 'lucide-react'
import { grantAPI, FullProposalRequest } from '@/lib/api'

interface ProposalSection {
  id: string
  title: string
  content: string
  required: boolean
}

interface UploadedDocument {
  name: string
  size: number
  type: string
  content?: string
}

export function FullProposalBuilder() {
  const [organizationInfo, setOrganizationInfo] = useState({
    name: '',
    mission: '',
    history: '',
    leadership: '',
    financials: ''
  })
  
  const [funderInfo, setFunderInfo] = useState({
    name: '',
    priorities: '',
    requirements: '',
    deadline: '',
    contact: ''
  })
  
  const [projectDetails, setProjectDetails] = useState({
    title: '',
    summary: '',
    goals: '',
    methodology: '',
    timeline: '',
    budget: '',
    evaluation: '',
    sustainability: ''
  })
  
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedProposal, setGeneratedProposal] = useState('')
  const [error, setError] = useState('')
  const [currentTab, setCurrentTab] = useState('organization')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const tabs = [
    { id: 'organization', label: 'Organization', icon: '🏢' },
    { id: 'funder', label: 'Funder Info', icon: '💰' },
    { id: 'project', label: 'Project Details', icon: '📋' },
    { id: 'documents', label: 'Documents', icon: '📁' },
    { id: 'review', label: 'Review & Generate', icon: '✨' }
  ]

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files) return

    Array.from(files).forEach(file => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const newDoc: UploadedDocument = {
          name: file.name,
          size: file.size,
          type: file.type,
          content: e.target?.result as string
        }
        setUploadedDocs(prev => [...prev, newDoc])
      }
      reader.readAsText(file)
    })
  }

  const removeDocument = (index: number) => {
    setUploadedDocs(prev => prev.filter((_, i) => i !== index))
  }

  const generateProposal = async () => {
    try {
      setIsGenerating(true)
      setError('')
      
      const requestData: FullProposalRequest = {
        organization_info: organizationInfo,
        funder_info: funderInfo,
        requirements: projectDetails,
        documents: uploadedDocs.map(doc => doc.content).filter(Boolean) as string[]
      }
      
      const response = await grantAPI.generateFullProposal(requestData)
      
      if (response.success) {
        setGeneratedProposal(response.proposal)
        
        // Save to localStorage
        const savedProposals = JSON.parse(localStorage.getItem('grantProposals') || '[]')
        savedProposals.push({
          type: 'full',
          organization: organizationInfo.name,
          title: projectDetails.title,
          funder: funderInfo.name,
          proposal: response.proposal,
          timestamp: new Date().toISOString(),
          status: 'completed',
          id: Date.now()
        })
        localStorage.setItem('grantProposals', JSON.stringify(savedProposals))
      } else {
        setError('Failed to generate proposal. Please try again.')
      }
    } catch (err) {
      console.error('Full proposal generation error:', err)
      setError('Error connecting to AI service. Please check your connection and try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const downloadProposal = () => {
    const blob = new Blob([generatedProposal], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${projectDetails.title || 'full-grant-proposal'}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (generatedProposal) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-white rounded-xl shadow-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 bg-green-50">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-green-600" />
              <h2 className="text-xl font-semibold text-gray-900">Full Proposal Generated Successfully!</h2>
            </div>
          </div>
          
          <div className="p-6">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Project: {projectDetails.title}</h3>
              <p className="text-gray-600">Organization: {organizationInfo.name}</p>
              <p className="text-gray-600">Funder: {funderInfo.name}</p>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-6 mb-6 max-h-96 overflow-y-auto">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Generated Full Proposal
              </h4>
              <div className="prose max-w-none">
                <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800 leading-relaxed">
                  {generatedProposal}
                </pre>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <button
                onClick={() => {
                  setGeneratedProposal('')
                  setCurrentTab('organization')
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Create Another Proposal
              </button>
              
              <button
                onClick={downloadProposal}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Download Proposal</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-xl shadow-lg border border-gray-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <FileText className="w-6 h-6 mr-3 text-green-600" />
            Full Proposal Builder
          </h2>
          <p className="text-gray-600 mt-1">Create comprehensive grant proposals with detailed sections</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setCurrentTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  currentTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Organization Tab */}
          {currentTab === 'organization' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Organization Information</h3>
              
              <div className="grid grid-cols-1 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Organization Name *
                  </label>
                  <input
                    type="text"
                    value={organizationInfo.name}
                    onChange={(e) => setOrganizationInfo(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your organization name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mission Statement
                  </label>
                  <textarea
                    value={organizationInfo.mission}
                    onChange={(e) => setOrganizationInfo(prev => ({ ...prev, mission: e.target.value }))}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Describe your organization's mission and values"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Organization History
                  </label>
                  <textarea
                    value={organizationInfo.history}
                    onChange={(e) => setOrganizationInfo(prev => ({ ...prev, history: e.target.value }))}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Brief history and major achievements"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Leadership Team
                  </label>
                  <textarea
                    value={organizationInfo.leadership}
                    onChange={(e) => setOrganizationInfo(prev => ({ ...prev, leadership: e.target.value }))}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Key leadership team members and their qualifications"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Funder Tab */}
          {currentTab === 'funder' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Funder Information</h3>
              
              <div className="grid grid-cols-1 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Funder Name *
                  </label>
                  <input
                    type="text"
                    value={funderInfo.name}
                    onChange={(e) => setFunderInfo(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter the funder or foundation name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Funding Priorities
                  </label>
                  <textarea
                    value={funderInfo.priorities}
                    onChange={(e) => setFunderInfo(prev => ({ ...prev, priorities: e.target.value }))}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="What are the funder's key priorities and focus areas?"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Specific Requirements
                  </label>
                  <textarea
                    value={funderInfo.requirements}
                    onChange={(e) => setFunderInfo(prev => ({ ...prev, requirements: e.target.value }))}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Any specific requirements or criteria mentioned in the RFP"
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Application Deadline
                    </label>
                    <input
                      type="date"
                      value={funderInfo.deadline}
                      onChange={(e) => setFunderInfo(prev => ({ ...prev, deadline: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Contact Information
                    </label>
                    <input
                      type="text"
                      value={funderInfo.contact}
                      onChange={(e) => setFunderInfo(prev => ({ ...prev, contact: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Program officer or contact person"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Project Tab */}
          {currentTab === 'project' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Project Details</h3>
              
              <div className="grid grid-cols-1 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Project Title *
                  </label>
                  <input
                    type="text"
                    value={projectDetails.title}
                    onChange={(e) => setProjectDetails(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your project title"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Executive Summary
                  </label>
                  <textarea
                    value={projectDetails.summary}
                    onChange={(e) => setProjectDetails(prev => ({ ...prev, summary: e.target.value }))}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Brief overview of the project and its significance"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Goals and Objectives
                  </label>
                  <textarea
                    value={projectDetails.goals}
                    onChange={(e) => setProjectDetails(prev => ({ ...prev, goals: e.target.value }))}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Specific, measurable goals and objectives"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Methodology & Approach
                  </label>
                  <textarea
                    value={projectDetails.methodology}
                    onChange={(e) => setProjectDetails(prev => ({ ...prev, methodology: e.target.value }))}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="How will you implement this project?"
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Timeline
                    </label>
                    <textarea
                      value={projectDetails.timeline}
                      onChange={(e) => setProjectDetails(prev => ({ ...prev, timeline: e.target.value }))}
                      rows={3}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Key milestones and timeline"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Budget Overview
                    </label>
                    <textarea
                      value={projectDetails.budget}
                      onChange={(e) => setProjectDetails(prev => ({ ...prev, budget: e.target.value }))}
                      rows={3}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Budget breakdown and justification"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Evaluation & Metrics
                  </label>
                  <textarea
                    value={projectDetails.evaluation}
                    onChange={(e) => setProjectDetails(prev => ({ ...prev, evaluation: e.target.value }))}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="How will you measure success?"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sustainability Plan
                  </label>
                  <textarea
                    value={projectDetails.sustainability}
                    onChange={(e) => setProjectDetails(prev => ({ ...prev, sustainability: e.target.value }))}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="How will the project continue beyond the grant period?"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Documents Tab */}
          {currentTab === 'documents' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Supporting Documents</h3>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
                <div className="text-center">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">Upload Documents</h4>
                  <p className="text-gray-600 mb-4">
                    Upload supporting documents like budgets, organizational charts, letters of support, etc.
                  </p>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 mx-auto"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Choose Files</span>
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </div>
              </div>
              
              {uploadedDocs.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium text-gray-900">Uploaded Documents</h4>
                  {uploadedDocs.map((doc, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-5 h-5 text-gray-600" />
                        <div>
                          <p className="font-medium text-gray-900">{doc.name}</p>
                          <p className="text-sm text-gray-600">{(doc.size / 1024).toFixed(1)} KB</p>
                        </div>
                      </div>
                      <button
                        onClick={() => removeDocument(index)}
                        className="text-red-600 hover:text-red-800 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Review Tab */}
          {currentTab === 'review' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Review & Generate</h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Organization</h4>
                    <p className="text-gray-700">{organizationInfo.name || 'Not specified'}</p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Funder</h4>
                    <p className="text-gray-700">{funderInfo.name || 'Not specified'}</p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Project</h4>
                    <p className="text-gray-700">{projectDetails.title || 'Not specified'}</p>
                  </div>
                </div>
                
                <div className="space-y-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Documents</h4>
                    <p className="text-gray-700">{uploadedDocs.length} files uploaded</p>
                  </div>
                  
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-2">Ready to Generate</h4>
                    <p className="text-blue-700">All sections have been completed. Click generate to create your comprehensive proposal.</p>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-center pt-6">
                <button
                  onClick={generateProposal}
                  disabled={isGenerating || !organizationInfo.name || !funderInfo.name || !projectDetails.title}
                  className={`px-8 py-3 rounded-lg flex items-center space-x-3 text-lg font-medium transition-colors ${
                    isGenerating || !organizationInfo.name || !funderInfo.name || !projectDetails.title
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  {isGenerating ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  ) : (
                    <Sparkles className="w-5 h-5" />
                  )}
                  <span>{isGenerating ? 'Generating Full Proposal...' : 'Generate Full Proposal'}</span>
                </button>
              </div>
            </div>
          )}

          {/* Tab Navigation */}
          <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
            <button
              onClick={() => {
                const currentIndex = tabs.findIndex(tab => tab.id === currentTab)
                if (currentIndex > 0) {
                  setCurrentTab(tabs[currentIndex - 1].id)
                }
              }}
              disabled={currentTab === tabs[0].id}
              className={`px-6 py-2 rounded-lg transition-colors ${
                currentTab === tabs[0].id
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Previous
            </button>
            
            <div className="text-sm text-gray-500">
              {tabs.findIndex(tab => tab.id === currentTab) + 1} of {tabs.length}
            </div>
            
            <button
              onClick={() => {
                const currentIndex = tabs.findIndex(tab => tab.id === currentTab)
                if (currentIndex < tabs.length - 1) {
                  setCurrentTab(tabs[currentIndex + 1].id)
                }
              }}
              disabled={currentTab === tabs[tabs.length - 1].id}
              className={`px-6 py-2 rounded-lg transition-colors ${
                currentTab === tabs[tabs.length - 1].id
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}