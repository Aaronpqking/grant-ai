import { NextRequest, NextResponse } from 'next/server'

const API_BASE = process.env.NEXT_PUBLIC_GRANT_API_URL || 'https://vertex-grant-agent-vqjdj6kdpq-uc.a.run.app'

export async function POST(request: NextRequest) {
  try {
    console.log('🔄 Proxying single file upload to backend...')
    
    // Get the formData from the request
    const formData = await request.formData()
    
    console.log('📦 Single file FormData received in proxy:')
    for (let [key, value] of formData.entries()) {
      console.log(`  ${key}:`, value instanceof File ? `File(${value.name}, ${value.size}b)` : value)
    }

    // Forward the request to the backend API with extended timeout for large files
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 600000) // 10 minute timeout for very large files
    
    const backendResponse = await fetch(`${API_BASE}/upload_documents`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
      // Don't set Content-Type header - let fetch set it with boundary for multipart
    })
    
    clearTimeout(timeoutId)

    console.log('📡 Backend response status:', backendResponse.status)
    
    if (!backendResponse.ok) {
      const errorText = await backendResponse.text()
      console.error('❌ Backend single file upload failed:', errorText)
      return NextResponse.json(
        { success: false, error: `Backend error: ${backendResponse.status}`, details: errorText },
        { status: backendResponse.status }
      )
    }

    const result = await backendResponse.json()
    console.log('✅ Backend single file upload successful:', result)
    
    return NextResponse.json(result)
    
  } catch (error) {
    console.error('❌ Proxy single file upload error:', error)
    return NextResponse.json(
      { success: false, error: 'Proxy server error', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    )
  }
} 