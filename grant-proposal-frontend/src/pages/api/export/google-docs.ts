import type { NextApiRequest, NextApiResponse } from 'next'

// Server-side Google Docs export using a service account.
// Requirements (production):
// - Set env var GOOGLE_SERVICE_ACCOUNT_KEY to the JSON key string (or set GOOGLE_APPLICATION_CREDENTIALS to file path).
// - Provide DRIVE_FOLDER_ID (optional) to put created docs into a specific folder.
// - Ensure the service account has the following scopes: Drive (drive.file) and Docs (docs).

// simple in-memory rate limiter (per process)
const rateMap: Record<string, { tokens: number; ts: number }> = {}
function allow(ip: string, limit = 10, windowMs = 10 * 60 * 1000) {
  const now = Date.now()
  const slot = rateMap[ip] || { tokens: limit, ts: now }
  const refill = Math.floor((now - slot.ts) / windowMs)
  if (refill > 0) {
    slot.tokens = Math.min(limit, slot.tokens + refill * limit)
    slot.ts = now
  }
  if (slot.tokens <= 0) return false
  slot.tokens -= 1
  rateMap[ip] = slot
  return true
}

async function getAuthClient() {
  const keyJson = process.env.GOOGLE_SERVICE_ACCOUNT_KEY
  const keyPath = process.env.GOOGLE_APPLICATION_CREDENTIALS
  let credentials: any = undefined

  if (keyJson) {
    try {
      credentials = JSON.parse(keyJson)
    } catch (e) {
      throw new Error('Invalid JSON in GOOGLE_SERVICE_ACCOUNT_KEY')
    }
  }

  // dynamic import to avoid client bundling
  const { google } = await import('googleapis')
  const auth = new google.auth.GoogleAuth({
    credentials,
    keyFile: keyPath,
    scopes: [
      'https://www.googleapis.com/auth/documents',
      'https://www.googleapis.com/auth/drive.file',
      'https://www.googleapis.com/auth/drive'
    ]
  })

  return auth.getClient()
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') return res.status(405).json({ message: 'Method not allowed' })
  const ip = (req.headers['x-forwarded-for'] as string)?.split(',')[0]?.trim() || req.socket.remoteAddress || 'unknown'
  if (!allow(ip)) return res.status(429).json({ message: 'Rate limit exceeded' })
  const { title, content } = req.body
  if (!title || !content) return res.status(400).json({ message: 'Missing title or content' })

  try {
    const authClient = await getAuthClient()
    const { google } = await import('googleapis')
    const docs = google.docs({ version: 'v1', auth: authClient })
    const drive = google.drive({ version: 'v3', auth: authClient })

    // 1) Create document
    const createRes = await docs.documents.create({ requestBody: { title } })
    const documentId = createRes.data.documentId
    if (!documentId) throw new Error('Failed to create Google Doc')

    // 2) Insert content (append at start)
    const requests: any[] = []
    // Replace newlines with simple text inserts; complex formatting can be handled later
    requests.push({ insertText: { location: { index: 1 }, text: content } })

    await docs.documents.batchUpdate({ documentId, requestBody: { requests } })

    // 3) Move document into DRIVE_FOLDER_ID if provided (keeps private by default)
    const folderId = process.env.DRIVE_FOLDER_ID
    if (folderId) {
      await drive.files.update({ fileId: documentId, addParents: folderId, fields: 'id, parents' })
    }

    // 4) Sharing: default private; do not make public

    // 5) Export as .docx and upload to GCS for persistent storage
    const exportMime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    const exportRes = await drive.files.export({ fileId: documentId, mimeType: exportMime }, { responseType: 'arraybuffer' })
    const docxBuffer = Buffer.from(exportRes.data as ArrayBuffer)

    // Upload to GCS (no auto-create; must exist)
    const { Storage } = require('@google-cloud/storage')
    const storage = new Storage({ apiEndpoint: process.env.GCS_API_ENDPOINT || undefined })
    const bucketName = process.env.EXPORT_DOCS_BUCKET
    if (!bucketName) {
      console.error(JSON.stringify({ action: 'export_docs', stage: 'config_error', msg: 'EXPORT_DOCS_BUCKET missing' }))
      return res.status(500).json({ success: false, message: 'EXPORT_DOCS_BUCKET not configured' })
    }
    const bucket = storage.bucket(bucketName)
    const [exists] = await bucket.exists()
    if (!exists) {
      console.error(JSON.stringify({ action: 'export_docs', stage: 'bucket_missing', bucket: bucketName }))
      return res.status(500).json({ success: false, message: `Bucket ${bucketName} does not exist` })
    }

    const filename = `${(title || 'document').replace(/\s+/g, '_')}_${Date.now()}.docx`
    const file = bucket.file(filename)
    await file.save(docxBuffer, { resumable: false, metadata: { contentType: exportMime } })

    // Make the file private (default) and generate signed URL
    const [signedUrl] = await file.getSignedUrl({ action: 'read', expires: Date.now() + 1000 * 60 * 60 })

    const fileMeta = await drive.files.get({ fileId: documentId, fields: 'id, webViewLink, name' })

    
    return res.status(200).json({
      success: true,
      documentId,
      webViewLink: fileMeta.data.webViewLink,
      name: fileMeta.data.name,
      gcs_url: `gs://${bucketName}/${filename}`,
      download_url: signedUrl
    })

  } catch (e: any) {
    console.error(JSON.stringify({ action: 'export_docs', status: 'error', message: e?.message || 'failed' }))
    return res.status(500).json({ success: false, message: e.message || 'Export failed' })
  }
}


