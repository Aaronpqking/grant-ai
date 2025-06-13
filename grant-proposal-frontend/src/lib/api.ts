// API client for connecting to the deployed Vertex AI Grant Agent
const API_BASE = process.env.NEXT_PUBLIC_GRANT_API_URL || 'https://vertex-grant-agent-vqjdj6kdpq-uc.a.run.app'

// Debug logging
console.log('Environment variable NEXT_PUBLIC_GRANT_API_URL:', process.env.NEXT_PUBLIC_GRANT_API_URL)
console.log('API_BASE resolved to:', API_BASE)

export interface QuickProposalRequest {
  organization_name: string
  project_title: string
  funder_name: string
  amount_requested: string
  project_description: string
}

export interface FullProposalRequest {
  organization_info: Record<string, any>
  funder_info: Record<string, any>
  requirements: Record<string, any>
  documents?: string[]
}

export interface ProposalResponse {
  success: boolean
  proposal: string
  timestamp: string
  grant_type?: string
}

export class GrantAPI {
  private static instance: GrantAPI
  
  public static getInstance(): GrantAPI {
    if (!GrantAPI.instance) {
      GrantAPI.instance = new GrantAPI()
    }
    return GrantAPI.instance
  }

  async checkHealth(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE}/health`)
      return await response.json()
    } catch (error) {
      console.error('Health check failed:', error)
      throw error
    }
  }

  async generateQuickProposal(data: QuickProposalRequest): Promise<ProposalResponse> {
    try {
      const response = await fetch(`${API_BASE}/quick_proposal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Quick proposal generation failed:', error)
      throw error
    }
  }

  async generateFullProposal(data: any): Promise<ProposalResponse> {
    try {
      const response = await fetch(`${API_BASE}/full_proposal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Full proposal generation failed:', error)
      throw error
    }
  }

  async uploadDocumentsChunked(files: File[]): Promise<any> {
    try {
      console.log('🚀 Starting chunked upload for large files...')
      const results = []
      
      for (const file of files) {
        console.log(`📤 Uploading file: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`)
        
        // Upload each file individually to avoid size limits
        const formData = new FormData()
        formData.append('files', file)
        
        const response = await fetch('/api/upload-single', {
          method: 'POST',
          body: formData
        })
        
        if (!response.ok) {
          const errorText = await response.text()
          console.error(`❌ Upload failed for ${file.name}:`, errorText)
          throw new Error(`Upload failed for ${file.name}: ${response.status}`)
        }
        
        const result = await response.json()
        console.log(`✅ ${file.name} uploaded successfully`)
        results.push(result)
      }
      
      // Combine all results
      const allArtifactIds = results.flatMap(r => r.artifact_ids || [])
      
      return {
        success: true,
        artifact_ids: allArtifactIds,
        message: `Uploaded ${files.length} large documents successfully (chunked)`,
        upload_method: 'chunked'
      }
      
    } catch (error) {
      console.error('❌ Chunked upload failed:', error)
      throw error
    }
  }

  async uploadDocuments(files: File[]): Promise<any> {
    try {
      console.log('🚀 Starting document upload...')
      console.log('📁 Files to upload:', files.length)
      console.log('📋 Files details:', files.map(f => ({ name: f.name, size: f.size, type: f.type })))
      console.log('🌐 Upload URL (via proxy):', '/api/upload')
      
      // Validate files array
      if (!files || files.length === 0) {
        throw new Error('No files provided for upload')
      }
      
      // Validate file sizes (Enterprise limits)
      const MAX_FILE_SIZE = 500 * 1024 * 1024 // 500MB per file
      const MAX_TOTAL_SIZE = 500 * 1024 * 1024 // 500MB total for enterprise uploads
      const CLOUD_RUN_LIMIT = 30 * 1024 * 1024 // 30MB - use chunked upload above this
      
      for (const file of files) {
        if (file.size > MAX_FILE_SIZE) {
          throw new Error(`File "${file.name}" is ${(file.size / 1024 / 1024).toFixed(2)}MB. Maximum file size is 500MB.`)
        }
      }
      
      const totalSize = files.reduce((sum, file) => sum + file.size, 0)
      if (totalSize > MAX_TOTAL_SIZE) {
        throw new Error(`Total upload size is ${(totalSize / 1024 / 1024).toFixed(2)}MB. Maximum total size is 500MB. Please upload fewer files at once.`)
      }
      
      // Check if we need chunked upload due to Cloud Run limits
      if (totalSize > CLOUD_RUN_LIMIT) {
        console.log(`🔄 Total size ${(totalSize / 1024 / 1024).toFixed(2)}MB exceeds Cloud Run limit. Using chunked upload...`)
        return await this.uploadDocumentsChunked(files)
      }
      
      const formData = new FormData()
      files.forEach((file, index) => {
        console.log(`📎 Appending file ${index + 1}: ${file.name} (${file.size} bytes)`)
        formData.append('files', file)
      })
      
      // Log FormData contents (for debugging)
      console.log('📦 FormData entries:')
      for (let [key, value] of formData.entries()) {
        console.log(`  ${key}:`, value instanceof File ? `File(${value.name}, ${value.size}b)` : value)
      }

      console.log('🌐 Sending request via proxy...')
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })

      console.log('📡 Response status:', response.status)
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ Upload failed with response:', errorText)
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`)
      }

      const result = await response.json()
      console.log('✅ Upload successful:', result)
      return result
    } catch (error) {
      console.error('❌ Document upload failed:', error)
      throw error
    }
  }

  // Stream response for real-time proposal generation
  async *streamProposal(data: QuickProposalRequest): AsyncGenerator<string, void, unknown> {
    try {
      const response = await fetch(`${API_BASE}/quick_proposal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is not readable')
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        yield chunk
      }
    } catch (error) {
      console.error('Streaming failed:', error)
      throw error
    }
  }
}

export const grantAPI = GrantAPI.getInstance() 