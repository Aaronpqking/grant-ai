'use client'

import React from 'react'
import { Upload, FileText, CheckCircle, AlertCircle, Trash2 } from 'lucide-react'

interface DocumentUploadSectionProps {
  files: File[]
  uploadedFiles: { name: string; url: string; status: 'uploaded' | 'failed' }[]
  uploadProgress: { [key: string]: number }
  isUploading: boolean
  additionalNotes: string
  onFileUpload: (files: FileList | null) => void
  onRemoveFile: (index: number) => void
  onRemoveUploadedFile: (index: number) => void
  onNotesChange: (notes: string) => void
}

export function DocumentUploadSection({
  files,
  uploadedFiles,
  uploadProgress,
  isUploading,
  additionalNotes,
  onFileUpload,
  onRemoveFile,
  onRemoveUploadedFile,
  onNotesChange
}: DocumentUploadSectionProps) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Supporting Documents</h3>
      
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h4 className="text-lg font-medium text-gray-900 mb-2">Upload Supporting Documents</h4>
        <p className="text-gray-600 mb-4">
          Add documents like organizational charts, letters of support, financial statements, etc.
        </p>
        <label htmlFor="file-upload" className={`px-6 py-2 rounded-lg transition-colors cursor-pointer inline-block ${
          isUploading 
            ? 'bg-gray-400 text-white cursor-not-allowed' 
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}>
          {isUploading ? 'Uploading...' : 'Choose Files'}
        </label>
        <input
          id="file-upload"
          type="file"
          multiple
          className="hidden"
          onChange={(e) => onFileUpload(e.target.files)}
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.xlsx,.xls,.ppt,.pptx,.csv"
          disabled={isUploading}
        />
        <p className="text-xs text-gray-500 mt-2">
          Supported formats: PDF, Word, Excel, PowerPoint, Text, Images<br/>
          <strong>Max: 500MB per file, 500MB total per upload</strong><br/>
          <span className="text-blue-600">Large files automatically use optimized upload</span>
        </p>
      </div>

      {/* Upload Progress */}
      {Object.keys(uploadProgress).length > 0 && (
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900">Uploading Files:</h4>
          {Object.entries(uploadProgress).map(([filename, progress]) => (
            <div key={filename} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-700">{filename}</span>
                <span className="text-gray-500">{progress}%</span>
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
      
      {/* Successfully Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-900">Successfully Uploaded:</h4>
          {uploadedFiles.map((file, index) => (
            <div key={index} className={`flex items-center justify-between p-3 rounded-lg ${
              file.status === 'uploaded' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-center space-x-3">
                {file.status === 'uploaded' ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-600" />
                )}
                <span className={`text-sm font-medium ${
                  file.status === 'uploaded' ? 'text-green-900' : 'text-red-900'
                }`}>
                  {file.name}
                </span>
                {file.status === 'uploaded' && (
                  <span className="text-xs text-green-600">✓ Ready for analysis</span>
                )}
                {file.status === 'failed' && (
                  <span className="text-xs text-red-600">✗ Upload failed</span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                {file.status === 'uploaded' && file.url !== '#' && (
                  <a 
                    href={file.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    View
                  </a>
                )}
                <button
                  onClick={() => onRemoveUploadedFile(index)}
                  className="text-red-600 hover:text-red-800 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Local Files (not yet uploaded) */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-900">Pending Upload:</h4>
          {files.map((file, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <FileText className="w-5 h-5 text-yellow-600" />
                <span className="text-sm text-yellow-900">{file.name}</span>
                <span className="text-xs text-yellow-600">
                  ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </span>
                <span className="text-xs text-yellow-600">⏳ Pending</span>
              </div>
              <button
                onClick={() => onRemoveFile(index)}
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
          value={additionalNotes}
          onChange={(e) => onNotesChange(e.target.value)}
          rows={4}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Any additional information or special instructions for document analysis"
        />
      </div>

      {/* Document Upload Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h5 className="font-medium text-blue-900 mb-2">Document Analysis</h5>
        <p className="text-sm text-blue-800">
          Uploaded documents will be analyzed by AI to enhance your proposal with:
        </p>
        <ul className="text-sm text-blue-800 mt-2 list-disc list-inside space-y-1">
          <li>Organizational strength assessment</li>
          <li>Financial capacity verification</li>
          <li>Past performance indicators</li>
          <li>Compliance and credential validation</li>
          <li>Supporting evidence integration</li>
        </ul>
      </div>
    </div>
  )
} 