import type { NextApiRequest, NextApiResponse } from 'next'
import { google } from 'googleapis'

// Server-side Google Docs export using a service account.
// Requirements (production):
// - Set env var GOOGLE_SERVICE_ACCOUNT_KEY to the JSON key string (or set GOOGLE_APPLICATION_CREDENTIALS to file path).
// - Provide DRIVE_FOLDER_ID (optional) to put created docs into a specific folder.
// - Ensure the service account has the following scopes: Drive (drive.file) and Docs (docs).

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
  const { title, content } = req.body
  if (!title || !content) return res.status(400).json({ message: 'Missing title or content' })

  try {
    const authClient = await getAuthClient()
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

    // 3) Move document into DRIVE_FOLDER_ID if provided
    const folderId = process.env.DRIVE_FOLDER_ID
    if (folderId) {
      // Retrieve current parents and remove root assignment before adding to folder
      await drive.files.update({ fileId: documentId, addParents: folderId, removeParents: '', fields: 'id, parents' })
    }

    // 4) Make the document viewable by link (optional - ADK: consider least privilege)
    if (process.env.GOOGLE_DOCS_SHARE === 'public') {
      await drive.permissions.create({ fileId: documentId, requestBody: { role: 'reader', type: 'anyone' } })
    }

    // 5) Export as .docx (binary) for default Word download and return signed link to Drive webView
    // For larger files, consider uploading export to GCS via backend artifact service
    const exportMime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    const exportRes = await drive.files.export({ fileId: documentId, mimeType: exportMime }, { responseType: 'arraybuffer' })
    const docxBuffer = Buffer.from(exportRes.data as ArrayBuffer)

    // Optionally store exported docx in Drive (create a copy) or return as base64 payload
    // Here we attach as base64 and return a downloadable link via Drive webViewLink
    const fileMeta = await drive.files.get({ fileId: documentId, fields: 'id, webViewLink, name' })

    // Return document metadata and base64 docx for immediate download if desired
    return res.status(200).json({
      success: true,
      documentId,
      webViewLink: fileMeta.data.webViewLink,
      name: fileMeta.data.name,
      docx_base64: docxBuffer.toString('base64')
    })

  } catch (e: any) {
    console.error('Google Docs export failed', e)
    return res.status(500).json({ success: false, message: e.message || 'Export failed' })
  }
}


