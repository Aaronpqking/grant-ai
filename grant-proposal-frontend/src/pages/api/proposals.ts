import type { NextApiRequest, NextApiResponse } from 'next'

async function getFirestore() {
  const mod = await import('@google-cloud/firestore')
  const { Firestore } = mod as any
  const db = new Firestore()
  return db
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const db = await getFirestore()
    const col = db.collection('proposals')

    if (req.method === 'POST') {
      const body = req.body || {}
      const now = new Date().toISOString()
      const doc = {
        organization: body.organization || {},
        funder: body.funder || {},
        project: body.project || {},
        documents: body.documents || [],
        proposal: body.proposal || '',
        summary: body.summary || null,
        grade: body.grade || null,
        export_gcs_path: body.export_gcs_path || null,
        updated_at: now,
        created_at: body.created_at || now
      }
      const ref = body.id ? col.doc(body.id) : col.doc()
      await ref.set(doc, { merge: true })
      return res.status(200).json({ success: true, id: ref.id })
    }

    if (req.method === 'GET') {
      const { id } = req.query
      if (id && typeof id === 'string') {
        const snap = await col.doc(id).get()
        if (!snap.exists) return res.status(404).json({ success: false, message: 'Not found' })
        return res.status(200).json({ success: true, id, data: snap.data() })
      }
      const snaps = await col.limit(20).orderBy('updated_at', 'desc').get()
      const items = snaps.docs.map(d => ({ id: d.id, ...d.data() }))
      return res.status(200).json({ success: true, items })
    }

    return res.status(405).json({ message: 'Method not allowed' })
  } catch (e: any) {
    console.error(JSON.stringify({ action: 'proposals_api', status: 'error', message: e?.message || 'failed' }))
    return res.status(500).json({ success: false, message: e?.message || 'Server error' })
  }
}


