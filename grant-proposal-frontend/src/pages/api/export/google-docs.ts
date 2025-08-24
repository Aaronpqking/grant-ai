import type { NextApiRequest, NextApiResponse } from 'next'

// NOTE: This endpoint is a stub. To enable Google Docs export you must:
// 1. Create a Google Cloud service account with Drive and Docs scopes.
// 2. Store credentials in a secure place and load them here.
// 3. Use googleapis to create a doc and return its URL.

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') return res.status(405).json({ message: 'Method not allowed' })
  const { title, content } = req.body

  // Placeholder implementation: echo back a fake URL
  return res.status(200).json({ url: `https://docs.google.com/document/d/FAKE_DOC_ID/edit?usp=sharing`, message: 'Stub - configure Google service account to enable export' })
}


