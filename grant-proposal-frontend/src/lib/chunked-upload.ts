// Chunked upload utility for large files
const CHUNK_SIZE = 5 * 1024 * 1024 // 5MB chunks
const MAX_RETRIES = 3

interface ChunkUploadProgress {
  fileName: string
  chunkIndex: number
  totalChunks: number
  uploadedBytes: number
  totalBytes: number
  percentage: number
}

interface ChunkedUploadResult {
  success: boolean
  uploadId: string
  fileName: string
  finalUrl?: string
  error?: string
}

export class ChunkedUploader {
  private onProgress?: (progress: ChunkUploadProgress) => void

  constructor(onProgress?: (progress: ChunkUploadProgress) => void) {
    this.onProgress = onProgress
  }

  async uploadFile(file: File): Promise<ChunkedUploadResult> {
    const fileName = file.name
    const totalBytes = file.size
    const totalChunks = Math.ceil(totalBytes / CHUNK_SIZE)
    
    console.log(`🔄 Starting chunked upload: ${fileName}`)
    console.log(`📊 File size: ${(totalBytes / 1024 / 1024).toFixed(2)}MB`)
    console.log(`📦 Total chunks: ${totalChunks}`)

    try {
      // Initialize chunked upload session
      const uploadId = await this.initializeUpload(fileName, totalBytes, totalChunks)
      
      // Upload chunks
      for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        const start = chunkIndex * CHUNK_SIZE
        const end = Math.min(start + CHUNK_SIZE, totalBytes)
        const chunk = file.slice(start, end)
        
        let success = false
        let retries = 0
        
        while (!success && retries < MAX_RETRIES) {
          try {
            await this.uploadChunk(uploadId, chunkIndex, chunk)
            success = true
            
            // Report progress
            const uploadedBytes = end
            const percentage = Math.round((uploadedBytes / totalBytes) * 100)
            
            this.onProgress?.({
              fileName,
              chunkIndex,
              totalChunks,
              uploadedBytes,
              totalBytes,
              percentage
            })
            
            console.log(`✅ Chunk ${chunkIndex + 1}/${totalChunks} uploaded (${percentage}%)`)
            
          } catch (error) {
            retries++
            console.warn(`⚠️ Chunk ${chunkIndex + 1} failed (attempt ${retries}/${MAX_RETRIES}):`, error)
            
            if (retries >= MAX_RETRIES) {
              throw new Error(`Failed to upload chunk ${chunkIndex + 1} after ${MAX_RETRIES} attempts`)
            }
            
            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, 1000 * retries))
          }
        }
      }
      
      // Finalize upload
      const finalUrl = await this.finalizeUpload(uploadId)
      
      return {
        success: true,
        uploadId,
        fileName,
        finalUrl
      }
      
    } catch (error) {
      console.error(`❌ Chunked upload failed for ${fileName}:`, error)
      return {
        success: false,
        uploadId: '',
        fileName,
        error: error instanceof Error ? error.message : String(error)
      }
    }
  }

  private async initializeUpload(fileName: string, totalBytes: number, totalChunks: number): Promise<string> {
    const response = await fetch('/api/upload/init', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        fileName,
        totalBytes,
        totalChunks
      })
    })

    if (!response.ok) {
      throw new Error(`Failed to initialize upload: ${response.status}`)
    }

    const result = await response.json()
    return result.uploadId
  }

  private async uploadChunk(uploadId: string, chunkIndex: number, chunk: Blob): Promise<void> {
    const formData = new FormData()
    formData.append('uploadId', uploadId)
    formData.append('chunkIndex', chunkIndex.toString())
    formData.append('chunk', chunk)

    const response = await fetch('/api/upload/chunk', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`Failed to upload chunk: ${response.status}`)
    }
  }

  private async finalizeUpload(uploadId: string): Promise<string> {
    const response = await fetch('/api/upload/finalize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ uploadId })
    })

    if (!response.ok) {
      throw new Error(`Failed to finalize upload: ${response.status}`)
    }

    const result = await response.json()
    return result.url
  }
}

// Simple helper function to check if file needs chunked upload
export function needsChunkedUpload(file: File): boolean {
  const MAX_SIMPLE_UPLOAD = 25 * 1024 * 1024 // 25MB
  return file.size > MAX_SIMPLE_UPLOAD
}

// Helper to upload multiple files with mixed approach
export async function uploadFiles(
  files: File[],
  onProgress?: (fileName: string, progress: number) => void
): Promise<{ success: boolean; results: any[]; errors: string[] }> {
  const results: any[] = []
  const errors: string[] = []
  
  for (const file of files) {
    try {
      if (needsChunkedUpload(file)) {
        console.log(`📦 Using chunked upload for large file: ${file.name}`)
        
        const chunkedUploader = new ChunkedUploader((progress) => {
          onProgress?.(file.name, progress.percentage)
        })
        
        const result = await chunkedUploader.uploadFile(file)
        
        if (result.success) {
          results.push({
            fileName: file.name,
            uploadId: result.uploadId,
            url: result.finalUrl,
            method: 'chunked'
          })
        } else {
          errors.push(`${file.name}: ${result.error}`)
        }
        
      } else {
        console.log(`📄 Using simple upload for file: ${file.name}`)
        
        // Use existing simple upload method
        const formData = new FormData()
        formData.append('files', file)
        
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        })
        
        if (response.ok) {
          const result = await response.json()
          results.push({
            fileName: file.name,
            result,
            method: 'simple'
          })
          onProgress?.(file.name, 100)
        } else {
          const errorText = await response.text()
          errors.push(`${file.name}: ${errorText}`)
        }
      }
    } catch (error) {
      errors.push(`${file.name}: ${error instanceof Error ? error.message : String(error)}`)
    }
  }
  
  return {
    success: errors.length === 0,
    results,
    errors
  }
} 