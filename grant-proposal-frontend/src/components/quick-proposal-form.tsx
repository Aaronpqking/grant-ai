'use client'

import React, { useState } from 'react'
import { ArrowRight, Loader, Sparkles, CheckCircle, AlertCircle, FileText, Download } from 'lucide-react'
import { grantAPI, QuickProposalRequest } from '@/lib/api'

interface FormData {
  organization_name: string
  project_title: string
  funder_name: string
  amount_requested: string
  project_description: string
  documents?: File[]
  uploadedFiles?: { name: string; url: string; status: 'uploaded' | 'failed' }[]
}

export function QuickProposalForm() {
  const [formData, setFormData] = useState<FormData>({
    organization_name: '',
    project_title: '',
    funder_name: '',
    amount_requested: '',
    project_description: '',
    documents: [],
    uploadedFiles: []
  })
  
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedProposal, setGeneratedProposal] = useState('')
  const [error, setError] = useState('')
  const [currentStep, setCurrentStep] = useState(0)
  const [suggestions, setSuggestions] = useState<Record<string, string[]>>({})
  const [uploadStatus, setUploadStatus] = useState<'none' | 'uploading' | 'success' | 'failed'>('none')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({})

  const steps = [
    { title: 'Organization Info', fields: ['organization_name'] },
    { title: 'Project Details', fields: ['project_title', 'project_description'] },
    { title: 'Funding Details', fields: ['funder_name', 'amount_requested'] },
    { title: 'Review & Generate', fields: [] }
  ]

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError('')
    
    // Generate AI suggestions based on field
    generateSuggestions(field, value)
  }

  const generateSuggestions = async (field: keyof FormData, value: string) => {
    if (value.length < 3) return
    
    // Mock AI suggestions - in a real app, these would come from your AI service
    const mockSuggestions: Record<string, string[]> = {
      organization_name: [
        'Freedom Equity Inc.',
        'Community Development Foundation',
        'Educational Innovation Alliance'
      ],
      project_title: [
        'Digital Literacy for Underserved Communities',
        'Sustainable Agriculture Training Program',
        'Youth Leadership Development Initiative'
      ],
      funder_name: [
        'Gates Foundation',
        'Ford Foundation',
        'Robert Wood Johnson Foundation'
      ],
      project_description: [
        'Focus on measurable community impact',
        'Emphasize sustainability and long-term benefits',
        'Include specific target demographics'
      ]
    }
    
    if (mockSuggestions[field]) {
      setSuggestions(prev => ({
        ...prev,
        [field]: mockSuggestions[field]
      }))
    }
  }

  const applySuggestion = (field: keyof FormData, suggestion: string) => {
    setFormData(prev => ({ ...prev, [field]: suggestion }))
    setSuggestions(prev => ({ ...prev, [field]: [] }))
  }

  // Immediate upload on file selection
  const handleFileUpload = async (files: FileList | null) => {
    if (files) {
      const newFiles = Array.from(files)
      setIsUploading(true)
      setError('')
      
      console.log('🚀 Starting immediate upload of', newFiles.length, 'files')
      
      try {
        // Add files to local state first for immediate UI feedback
        setFormData(prev => ({
          ...prev,
          documents: [...(prev.documents || []), ...newFiles]
        }))

        // Initialize progress tracking - start upload immediately
        const progressMap: { [key: string]: number } = {}
        newFiles.forEach(file => {
          progressMap[file.name] = 0
        })
        setUploadProgress(progressMap)

        // Start upload immediately - handles both regular and chunked uploads
        console.log('📤 Uploading files to backend...')
        
        // Update progress for each file during upload
        const totalSize = newFiles.reduce((sum, file) => sum + file.size, 0)
        if (totalSize > 30 * 1024 * 1024) {
          console.log('🔄 Using chunked upload for large files...')
          // Show individual file progress for chunked uploads
          for (const file of newFiles) {
            setUploadProgress(prev => ({
              ...prev,
              [file.name]: 25 // Show partial progress
            }))
          }
        }
        
        const uploadResponse = await grantAPI.uploadDocuments(newFiles)
        
        if (uploadResponse.success) {
          // Add uploaded files to the uploaded files list
          const uploadedFileData = newFiles.map(file => ({
            name: file.name,
            url: uploadResponse.file_urls?.[file.name] || '#',
            status: 'uploaded' as const
          }))

          setFormData(prev => ({
            ...prev,
            uploadedFiles: [...(prev.uploadedFiles || []), ...uploadedFileData]
          }))
          
          setUploadStatus('success')
          const method = uploadResponse.upload_method || 'standard'
          console.log(`✅ Documents uploaded successfully (${method}):`, uploadedFileData)
          
          // Clear progress after successful upload
          setUploadProgress({})
        } else {
          throw new Error(uploadResponse.message || 'Upload failed')
        }
      } catch (err) {
        console.error('File upload error:', err)
        setError('Failed to upload files. Please try again.')
        setUploadStatus('failed')
        
        // Mark files as failed
        const failedFiles = newFiles.map(file => ({
          name: file.name,
          url: '#',
          status: 'failed' as const
        }))

        setFormData(prev => ({
          ...prev,
          uploadedFiles: [...(prev.uploadedFiles || []), ...failedFiles]
        }))
      } finally {
        setIsUploading(false)
        setUploadProgress({})
      }
    }
  }

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      generateProposal()
    }
  }

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const isStepComplete = (stepIndex: number) => {
    const step = steps[stepIndex]
    return step.fields.every(field => {
      const value = formData[field as keyof FormData];
      return value !== undefined && value !== null && value.toString().trim() !== '';
    })
  }

  const generateProposal = async () => {
    try {
      setIsGenerating(true)
      setError('')
      
      // Use already uploaded files (no upload during generation!)
      const uploadedFileInfo = formData.uploadedFiles?.filter(file => file.status === 'uploaded') || []
      
      console.log('📋 Generating proposal with uploaded documents:', uploadedFileInfo)
      
      // Generate proposal with form data
      const proposalData = {
        ...formData,
        uploaded_documents: uploadedFileInfo
      }
      
      const response = await grantAPI.generateQuickProposal(proposalData)
      
      if (response.success) {
        setGeneratedProposal(response.proposal)
        
        // Save to localStorage for demo
        const savedProposals = JSON.parse(localStorage.getItem('grantProposals') || '[]')
        savedProposals.push({
          ...formData,
          proposal: response.proposal,
          timestamp: new Date().toISOString(),
          status: 'completed',
          id: Date.now(),
          hasDocuments: formData.documents && formData.documents.length > 0
        })
        localStorage.setItem('grantProposals', JSON.stringify(savedProposals))
      } else {
        setError('Failed to generate proposal. Please try again.')
      }
    } catch (err) {
      console.error('Proposal generation error:', err)
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
    a.download = `${formData.project_title || 'grant-proposal'}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (generatedProposal) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-xl shadow-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 bg-green-50">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-green-600" />
              <h2 className="text-xl font-semibold text-gray-900">Proposal Generated Successfully!</h2>
            </div>
          </div>
          
          <div className="p-6">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Project: {formData.project_title}</h3>
              <p className="text-gray-600">Organization: {formData.organization_name}</p>
              <p className="text-gray-600">Requested Amount: ${formData.amount_requested}</p>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Generated Proposal
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
                  setCurrentStep(0)
                  setFormData({
                    organization_name: '',
                    project_title: '',
                    funder_name: '',
                    amount_requested: '',
                    project_description: '',
                    documents: [],
                    uploadedFiles: []
                  })
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
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-xl shadow-lg border border-gray-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Sparkles className="w-6 h-6 mr-3 text-blue-600" />
            Quick Proposal Generator
          </h2>
          <p className="text-gray-600 mt-1">Generate a compelling grant proposal in minutes</p>
        </div>

        {/* Progress Indicator */}
        <div className="px-6 py-4 bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  index < currentStep 
                    ? 'bg-green-500 text-white' 
                    : index === currentStep 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-200 text-gray-600'
                }`}>
                  {index < currentStep ? '✓' : index + 1}
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-12 h-1 mx-2 ${
                    index < currentStep ? 'bg-green-500' : 'bg-gray-200'
                  }`}></div>
                )}
              </div>
            ))}
          </div>
          <div className="text-sm text-gray-600">
            Step {currentStep + 1} of {steps.length}: {steps[currentStep].title}
          </div>
        </div>

        {/* Form Content */}
        <div className="p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Step 0: Organization Info */}
          {currentStep === 0 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organization Name *
                </label>
                <input
                  type="text"
                  value={formData.organization_name}
                  onChange={(e) => handleInputChange('organization_name', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your organization name"
                />
                {suggestions.organization_name?.length > 0 && (
                  <div className="mt-2 space-y-1">
                    <p className="text-xs text-gray-500">AI Suggestions:</p>
                    {suggestions.organization_name.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => applySuggestion('organization_name', suggestion)}
                        className="block w-full text-left px-3 py-2 text-sm bg-blue-50 hover:bg-blue-100 rounded-md transition-colors"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 1: Project Details */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Title *
                </label>
                <input
                  type="text"
                  value={formData.project_title}
                  onChange={(e) => handleInputChange('project_title', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your project title"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Description *
                </label>
                <textarea
                  value={formData.project_description}
                  onChange={(e) => handleInputChange('project_description', e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Provide a detailed description of your project goals, target audience, and expected impact"
                />
              </div>
            </div>
          )}

          {/* Step 2: Funding Details */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Funder Name *
                </label>
                <input
                  type="text"
                  value={formData.funder_name}
                  onChange={(e) => handleInputChange('funder_name', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter the funder or foundation name"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Amount Requested *
                </label>
                <input
                  type="text"
                  value={formData.amount_requested}
                  onChange={(e) => handleInputChange('amount_requested', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="50000"
                />
                <p className="text-sm text-gray-500 mt-1">Enter amount in USD</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Supporting Documents (Optional)</label>
                <input
                  type="file"
                  multiple
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onChange={(e) => handleFileUpload(e.target.files)}
                  accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.ppt,.pptx,.xls,.xlsx,.csv"
                  disabled={isUploading}
                />
                <p className="text-sm text-gray-500 mt-1">
                  Upload key documents like letters of support, presentations, or organizational info
                  <br/><strong>Max: 500MB per file, 500MB total per upload</strong>
                  <br/><span className="text-blue-600">Large files automatically use optimized upload</span>
                </p>
                
                {/* Show upload progress */}
                {isUploading && (
                  <div className="mt-2 space-y-2">
                    <p className="text-sm text-blue-600">Uploading files...</p>
                    {Object.entries(uploadProgress).map(([fileName, progress]) => (
                      <div key={fileName} className="space-y-1">
                        <div className="flex justify-between text-xs text-gray-600">
                          <span>📎 {fileName}</span>
                          <span>{progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                            style={{ width: `${progress}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Show uploaded files */}
                {formData.uploadedFiles && formData.uploadedFiles.length > 0 && (
                  <div className="mt-2 space-y-1">
                    <p className="text-sm font-medium text-gray-700">Uploaded Documents:</p>
                    {formData.uploadedFiles.map((file, index) => (
                      <div key={index} className={`text-sm flex items-center ${
                        file.status === 'uploaded' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        <span>{file.status === 'uploaded' ? '✅' : '❌'} {file.name}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Show local files being processed */}
                {formData.documents && formData.documents.length > 0 && !isUploading && (
                  <div className="mt-2 space-y-1">
                    <p className="text-sm font-medium text-gray-700">Processing:</p>
                    {formData.documents.map((file, index) => (
                      <div key={index} className="text-sm text-gray-600 flex items-center">
                        <span>📎 {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 3: Review */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Review Your Information</h3>
              
              <div className="bg-gray-50 rounded-lg p-6 space-y-4">
                <div>
                  <span className="font-medium text-gray-700">Organization:</span>
                  <span className="ml-2 text-gray-900">{formData.organization_name}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Project:</span>
                  <span className="ml-2 text-gray-900">{formData.project_title}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Funder:</span>
                  <span className="ml-2 text-gray-900">{formData.funder_name}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Amount:</span>
                  <span className="ml-2 text-gray-900">${formData.amount_requested}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Description:</span>
                  <p className="ml-2 text-gray-900 mt-1">{formData.project_description}</p>
                </div>
                {formData.uploadedFiles && formData.uploadedFiles.length > 0 && (
                  <div>
                    <span className="font-medium text-gray-700">Documents:</span>
                    <div className="ml-2 mt-1">
                      {formData.uploadedFiles.map((file, index) => (
                        <div key={index} className={`text-sm flex items-center ${
                          file.status === 'uploaded' ? 'text-green-700' : 'text-red-700'
                        }`}>
                          <span>{file.status === 'uploaded' ? '✅' : '❌'} {file.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
            <button
              onClick={prevStep}
              disabled={currentStep === 0}
              className={`px-6 py-2 rounded-lg transition-colors ${
                currentStep === 0
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Previous
            </button>
            
            <button
              onClick={nextStep}
              disabled={!isStepComplete(currentStep) || isGenerating}
              className={`px-6 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                !isStepComplete(currentStep) || isGenerating
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isGenerating ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : currentStep === steps.length - 1 ? (
                <Sparkles className="w-4 h-4" />
              ) : (
                <ArrowRight className="w-4 h-4" />
              )}
              <span>
                {isGenerating 
                  ? 'Generating...' 
                  : currentStep === steps.length - 1 
                    ? 'Generate Proposal' 
                    : 'Next'
                }
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
} 