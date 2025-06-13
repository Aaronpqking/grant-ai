'use client'

import React, { useState } from 'react'
import { Building2, Users, FileText, Upload, Download, CheckCircle, AlertCircle, Loader, Eye, Trash2 } from 'lucide-react'
import { grantAPI } from '@/lib/api'
import { DocumentUploadSection } from './document-upload-section'

interface OrganizationData {
  name: string
  mission: string
  established: string
  tax_id: string
  address: string
  website: string
  contact_person: string
  contact_email: string
  contact_phone: string
}

interface FunderData {
  name: string
  program: string
  deadline: string
  amount_min: string
  amount_max: string
  focus_areas: string
  requirements: string
}

interface ProjectData {
  title: string
  summary: string
  statement_of_need: string
  project_description: string
  goals_objectives: string
  methodology: string
  timeline: string
  budget_total: string
  budget_breakdown: string
  evaluation_plan: string
  sustainability: string
  expected_outcomes: string
}

interface DocumentData {
  files: File[]
  uploadedFiles: { name: string; url: string; status: 'uploaded' | 'failed' }[]
  additional_notes: string
}

interface FullProposalData {
  organization: OrganizationData
  funder: FunderData
  project: ProjectData
  documents: DocumentData
}

export function FullProposalBuilder() {
  const [activeTab, setActiveTab] = useState(0)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState('')
  const [generatedProposal, setGeneratedProposal] = useState('')
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({})
  const [isUploading, setIsUploading] = useState(false)
  
  const [formData, setFormData] = useState<FullProposalData>({
    organization: {
      name: '',
      mission: '',
      established: '',
      tax_id: '',
      address: '',
      website: '',
      contact_person: '',
      contact_email: '',
      contact_phone: ''
    },
    funder: {
      name: '',
      program: '',
      deadline: '',
      amount_min: '',
      amount_max: '',
      focus_areas: '',
      requirements: ''
    },
    project: {
      title: '',
      summary: '',
      statement_of_need: '',
      project_description: '',
      goals_objectives: '',
      methodology: '',
      timeline: '',
      budget_total: '',
      budget_breakdown: '',
      evaluation_plan: '',
      sustainability: '',
      expected_outcomes: ''
    },
    documents: {
      files: [],
      uploadedFiles: [],
      additional_notes: ''
    }
  })

  const tabs = [
    { id: 'organization', label: 'Organization', icon: Building2 },
    { id: 'funder', label: 'Funder Info', icon: Users },
    { id: 'project', label: 'Project Details', icon: FileText },
    { id: 'documents', label: 'Documents', icon: Upload },
    { id: 'review', label: 'Review & Generate', icon: Eye }
  ]

  const updateOrganization = (field: keyof OrganizationData, value: string) => {
    setFormData(prev => ({
      ...prev,
      organization: { ...prev.organization, [field]: value }
    }))
  }

  const updateFunder = (field: keyof FunderData, value: string) => {
    setFormData(prev => ({
      ...prev,
      funder: { ...prev.funder, [field]: value }
    }))
  }

  const updateProject = (field: keyof ProjectData, value: string) => {
    setFormData(prev => ({
      ...prev,
      project: { ...prev.project, [field]: value }
    }))
  }

  const handleFileUpload = async (files: FileList | null) => {
    if (files) {
      const newFiles = Array.from(files)
      setIsUploading(true)
      setError('')
      
      try {
        // Add files to local state first for immediate UI feedback
        setFormData(prev => ({
          ...prev,
          documents: {
            ...prev.documents,
            files: [...prev.documents.files, ...newFiles]
          }
        }))

        // Initialize progress tracking
        const progressMap: { [key: string]: number } = {}
        newFiles.forEach(file => {
          progressMap[file.name] = 0
        })
        setUploadProgress(progressMap)

        // Simulate upload progress (in real implementation, you'd get this from the upload)
        for (const file of newFiles) {
          for (let progress = 0; progress <= 100; progress += 10) {
            setUploadProgress(prev => ({
              ...prev,
              [file.name]: progress
            }))
            await new Promise(resolve => setTimeout(resolve, 100))
          }
        }

        // Upload files to backend
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
            documents: {
              ...prev.documents,
              uploadedFiles: [...prev.documents.uploadedFiles, ...uploadedFileData]
            }
          }))
        } else {
          throw new Error(uploadResponse.message || 'Upload failed')
        }
      } catch (err) {
        console.error('File upload error:', err)
        setError('Failed to upload files. Please try again.')
        
        // Mark files as failed
        const failedFiles = newFiles.map(file => ({
          name: file.name,
          url: '#',
          status: 'failed' as const
        }))

        setFormData(prev => ({
          ...prev,
          documents: {
            ...prev.documents,
            uploadedFiles: [...prev.documents.uploadedFiles, ...failedFiles]
          }
        }))
      } finally {
        setIsUploading(false)
        setUploadProgress({})
      }
    }
  }

  const removeFile = (index: number) => {
    setFormData(prev => ({
      ...prev,
      documents: {
        ...prev.documents,
        files: prev.documents.files.filter((_, i) => i !== index)
      }
    }))
  }

  const generateFullProposal = async () => {
    try {
      setIsGenerating(true)
      setError('')
      
      // Prepare data for API
      const requestData = {
        organization_name: formData.organization.name,
        project_title: formData.project.title,
        project_description: formData.project.project_description,
        funder_name: formData.funder.name,
        amount_requested: formData.project.budget_total,
        detailed_info: {
          organization: formData.organization,
          funder: formData.funder,
          project: formData.project
        }
      }
      
      const response = await grantAPI.generateFullProposal(requestData)
      
      if (response.success) {
        setGeneratedProposal(response.proposal)
        
        // Save to localStorage
        const savedProposals = JSON.parse(localStorage.getItem('grantProposals') || '[]')
        savedProposals.push({
          ...requestData,
          proposal: response.proposal,
          timestamp: new Date().toISOString(),
          status: 'completed',
          type: 'full',
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
    a.download = `${formData.project.title || 'full-grant-proposal'}.txt`
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
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{formData.project.title}</h3>
              <p className="text-gray-600">Organization: {formData.organization.name}</p>
              <p className="text-gray-600">Funder: {formData.funder.name}</p>
              <p className="text-gray-600">Budget: ${formData.project.budget_total}</p>
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
                  setActiveTab(0)
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
                <span>Download Full Proposal</span>
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
          <h2 className="text-2xl font-bold text-gray-900">Full Proposal Builder</h2>
          <p className="text-gray-600 mt-1">Create a comprehensive grant proposal with detailed information</p>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="flex space-x-6 overflow-x-auto">
            {tabs.map((tab, index) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(index)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                    activeTab === index
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Organization Tab */}
          {activeTab === 0 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Organization Information</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Organization Name *</label>
                  <input
                    type="text"
                    value={formData.organization.name}
                    onChange={(e) => updateOrganization('name', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter organization name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Year Established</label>
                  <input
                    type="text"
                    value={formData.organization.established}
                    onChange={(e) => updateOrganization('established', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g. 2010"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Mission Statement</label>
                  <textarea
                    value={formData.organization.mission}
                    onChange={(e) => updateOrganization('mission', e.target.value)}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Describe your organization's mission and purpose"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tax ID (EIN)</label>
                  <input
                    type="text"
                    value={formData.organization.tax_id}
                    onChange={(e) => updateOrganization('tax_id', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="XX-XXXXXXX"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Website</label>
                  <input
                    type="url"
                    value={formData.organization.website}
                    onChange={(e) => updateOrganization('website', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="https://..."
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
                  <textarea
                    value={formData.organization.address}
                    onChange={(e) => updateOrganization('address', e.target.value)}
                    rows={2}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Complete mailing address"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Contact Person</label>
                  <input
                    type="text"
                    value={formData.organization.contact_person}
                    onChange={(e) => updateOrganization('contact_person', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Full name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Contact Email</label>
                  <input
                    type="email"
                    value={formData.organization.contact_email}
                    onChange={(e) => updateOrganization('contact_email', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="email@organization.org"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Contact Phone</label>
                  <input
                    type="tel"
                    value={formData.organization.contact_phone}
                    onChange={(e) => updateOrganization('contact_phone', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="(555) 123-4567"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Funder Tab */}
          {activeTab === 1 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Funder Information</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Funder Name *</label>
                  <input
                    type="text"
                    value={formData.funder.name}
                    onChange={(e) => updateFunder('name', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Foundation or funding organization name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Grant Program</label>
                  <input
                    type="text"
                    value={formData.funder.program}
                    onChange={(e) => updateFunder('program', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Specific program or initiative name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Application Deadline</label>
                  <input
                    type="date"
                    value={formData.funder.deadline}
                    onChange={(e) => updateFunder('deadline', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Funding Range</label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={formData.funder.amount_min}
                      onChange={(e) => updateFunder('amount_min', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Min amount"
                    />
                    <span className="px-2 py-3 text-gray-500">to</span>
                    <input
                      type="text"
                      value={formData.funder.amount_max}
                      onChange={(e) => updateFunder('amount_max', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Max amount"
                    />
                  </div>
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Focus Areas</label>
                  <textarea
                    value={formData.funder.focus_areas}
                    onChange={(e) => updateFunder('focus_areas', e.target.value)}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Describe the funder's priority areas and interests"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Special Requirements</label>
                  <textarea
                    value={formData.funder.requirements}
                    onChange={(e) => updateFunder('requirements', e.target.value)}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Any specific requirements, restrictions, or preferences"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Project Tab */}
          {activeTab === 2 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Project Details</h3>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Project Title *</label>
                  <input
                    type="text"
                    value={formData.project.title}
                    onChange={(e) => updateProject('title', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter compelling project title"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Executive Summary</label>
                  <textarea
                    value={formData.project.summary}
                    onChange={(e) => updateProject('summary', e.target.value)}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Brief overview of the project (2-3 paragraphs)"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Statement of Need</label>
                  <textarea
                    value={formData.project.statement_of_need}
                    onChange={(e) => updateProject('statement_of_need', e.target.value)}
                    rows={5}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Describe the problem or need your project addresses"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Project Description</label>
                  <textarea
                    value={formData.project.project_description}
                    onChange={(e) => updateProject('project_description', e.target.value)}
                    rows={5}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Detailed description of project activities and approach"
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Total Budget *</label>
                    <input
                      type="text"
                      value={formData.project.budget_total}
                      onChange={(e) => updateProject('budget_total', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Total project budget (USD)"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Timeline</label>
                    <input
                      type="text"
                      value={formData.project.timeline}
                      onChange={(e) => updateProject('timeline', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="e.g. 18 months, Jan 2024 - Jun 2025"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Documents Tab */}
          {activeTab === 3 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Supporting Documents</h3>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h4 className="text-lg font-medium text-gray-900 mb-2">Upload Supporting Documents</h4>
                <p className="text-gray-600 mb-4">
                  Add documents like organizational charts, letters of support, financial statements, etc.
                </p>
                <label htmlFor="file-upload" className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors cursor-pointer inline-block">
                  Choose Files
                </label>
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  className="hidden"
                  onChange={(e) => handleFileUpload(e.target.files)}
                  accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
                />
              </div>
              
              {formData.documents.files.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-900">Uploaded Files:</h4>
                  {formData.documents.files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-5 h-5 text-gray-500" />
                        <span className="text-sm text-gray-900">{file.name}</span>
                        <span className="text-xs text-gray-500">
                          ({(file.size / 1024 / 1024).toFixed(2)} MB)
                        </span>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="text-red-600 hover:text-red-800 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Additional Notes</label>
                <textarea
                  value={formData.documents.additional_notes}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    documents: { ...prev.documents, additional_notes: e.target.value }
                  }))}
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Any additional information or special instructions"
                />
              </div>
            </div>
          )}

          {/* Funder Tab */}
          {activeTab === 1 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Funder Information</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Funder Name *</label>
                  <input
                    type="text"
                    value={formData.funder.name}
                    onChange={(e) => updateFunder('name', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Foundation or funding organization name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Grant Program</label>
                  <input
                    type="text"
                    value={formData.funder.program}
                    onChange={(e) => updateFunder('program', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Specific program or initiative name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Application Deadline</label>
                  <input
                    type="date"
                    value={formData.funder.deadline}
                    onChange={(e) => updateFunder('deadline', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Funding Range</label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={formData.funder.amount_min}
                      onChange={(e) => updateFunder('amount_min', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Min amount"
                    />
                    <span className="px-2 py-3 text-gray-500">to</span>
                    <input
                      type="text"
                      value={formData.funder.amount_max}
                      onChange={(e) => updateFunder('amount_max', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Max amount"
                    />
                  </div>
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Focus Areas</label>
                  <textarea
                    value={formData.funder.focus_areas}
                    onChange={(e) => updateFunder('focus_areas', e.target.value)}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Describe the funder's priority areas and interests"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Special Requirements</label>
                  <textarea
                    value={formData.funder.requirements}
                    onChange={(e) => updateFunder('requirements', e.target.value)}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Any specific requirements, restrictions, or preferences"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Project Tab */}
          {activeTab === 2 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Project Details</h3>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Project Title *</label>
                  <input
                    type="text"
                    value={formData.project.title}
                    onChange={(e) => updateProject('title', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter compelling project title"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Executive Summary</label>
                  <textarea
                    value={formData.project.summary}
                    onChange={(e) => updateProject('summary', e.target.value)}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Brief overview of the project (2-3 paragraphs)"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Statement of Need</label>
                  <textarea
                    value={formData.project.statement_of_need}
                    onChange={(e) => updateProject('statement_of_need', e.target.value)}
                    rows={5}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Describe the problem or need your project addresses"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Project Description</label>
                  <textarea
                    value={formData.project.project_description}
                    onChange={(e) => updateProject('project_description', e.target.value)}
                    rows={5}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Detailed description of project activities and approach"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Goals & Objectives</label>
                  <textarea
                    value={formData.project.goals_objectives}
                    onChange={(e) => updateProject('goals_objectives', e.target.value)}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Specific, measurable goals and objectives"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Methodology</label>
                  <textarea
                    value={formData.project.methodology}
                    onChange={(e) => updateProject('methodology', e.target.value)}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="How you will implement the project"
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Total Budget *</label>
                    <input
                      type="text"
                      value={formData.project.budget_total}
                      onChange={(e) => updateProject('budget_total', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Total project budget (USD)"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Timeline</label>
                    <input
                      type="text"
                      value={formData.project.timeline}
                      onChange={(e) => updateProject('timeline', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="e.g. 18 months, Jan 2024 - Jun 2025"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Budget Breakdown</label>
                  <textarea
                    value={formData.project.budget_breakdown}
                    onChange={(e) => updateProject('budget_breakdown', e.target.value)}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Detailed budget categories and amounts"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Evaluation Plan</label>
                  <textarea
                    value={formData.project.evaluation_plan}
                    onChange={(e) => updateProject('evaluation_plan', e.target.value)}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="How you will measure success and impact"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Sustainability Plan</label>
                  <textarea
                    value={formData.project.sustainability}
                    onChange={(e) => updateProject('sustainability', e.target.value)}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="How the project will continue beyond the grant period"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Expected Outcomes</label>
                  <textarea
                    value={formData.project.expected_outcomes}
                    onChange={(e) => updateProject('expected_outcomes', e.target.value)}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Anticipated results and impact"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Documents Tab */}
          {activeTab === 3 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Supporting Documents</h3>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h4 className="text-lg font-medium text-gray-900 mb-2">Upload Supporting Documents</h4>
                <p className="text-gray-600 mb-4">
                  Add documents like organizational charts, letters of support, financial statements, etc.
                </p>
                <label htmlFor="file-upload" className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors cursor-pointer inline-block">
                  Choose Files
                </label>
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  className="hidden"
                  onChange={(e) => handleFileUpload(e.target.files)}
                  accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
                />
              </div>
              
              {formData.documents.files.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-900">Uploaded Files:</h4>
                  {formData.documents.files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-5 h-5 text-gray-500" />
                        <span className="text-sm text-gray-900">{file.name}</span>
                        <span className="text-xs text-gray-500">
                          ({(file.size / 1024 / 1024).toFixed(2)} MB)
                        </span>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="text-red-600 hover:text-red-800 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Additional Notes</label>
                <textarea
                  value={formData.documents.additional_notes}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    documents: { ...prev.documents, additional_notes: e.target.value }
                  }))}
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Any additional information or special instructions"
                />
              </div>
            </div>
          )}

          {/* Review Tab */}
          {activeTab === 4 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Review & Generate</h3>
              
              <div className="bg-gray-50 rounded-lg p-6 space-y-6">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Organization</h4>
                  <p className="text-gray-700">{formData.organization.name || 'Not specified'}</p>
                  <p className="text-sm text-gray-600">{formData.organization.mission}</p>
                </div>
                
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Project</h4>
                  <p className="text-gray-700 font-medium">{formData.project.title || 'Not specified'}</p>
                  <p className="text-sm text-gray-600">{formData.project.summary}</p>
                </div>
                
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Funding</h4>
                  <p className="text-gray-700">Funder: {formData.funder.name || 'Not specified'}</p>
                  <p className="text-gray-700">Budget: ${formData.project.budget_total || '0'}</p>
                  <p className="text-gray-700">Timeline: {formData.project.timeline || 'Not specified'}</p>
                </div>
                
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Documents</h4>
                  <p className="text-gray-700">{formData.documents.files.length} files uploaded</p>
                </div>
              </div>
              
              <div className="flex justify-center pt-6">
                <button
                  onClick={generateFullProposal}
                  disabled={isGenerating || !formData.organization.name || !formData.project.title}
                  className={`px-8 py-3 rounded-lg flex items-center space-x-2 transition-colors ${
                    isGenerating || !formData.organization.name || !formData.project.title
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {isGenerating ? (
                    <Loader className="w-5 h-5 animate-spin" />
                  ) : (
                    <FileText className="w-5 h-5" />
                  )}
                  <span>
                    {isGenerating ? 'Generating Full Proposal...' : 'Generate Full Proposal'}
                  </span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        {activeTab < 4 && (
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-between">
            <button
              onClick={() => setActiveTab(Math.max(0, activeTab - 1))}
              disabled={activeTab === 0}
              className={`px-6 py-2 rounded-lg transition-colors ${
                activeTab === 0
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-200'
              }`}
            >
              Previous
            </button>
            
            <button
              onClick={() => setActiveTab(Math.min(4, activeTab + 1))}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
} 