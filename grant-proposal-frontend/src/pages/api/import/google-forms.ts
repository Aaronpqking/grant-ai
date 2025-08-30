import type { NextApiRequest, NextApiResponse } from 'next'

// Simple proxy to fetch a public Google Sheets CSV export (Google Forms responses can be exported as CSV)
// Request: POST { url: string } where url is the public CSV export URL for the sheet

async function fetchText(url: string) {
  const resp = await fetch(url)
  if (!resp.ok) throw new Error(`Fetch failed: ${resp.status}`)
  return await resp.text()
}

function parseCsvToObjects(csvText: string) {
  const lines = csvText.split(/\r?\n/).filter(Boolean)
  if (lines.length === 0) return []
  const headers = lines[0].split(',').map(h => h.trim())
  return lines.slice(1).map(line => {
    const cols = line.split(',')
    const obj: Record<string, string> = {}
    headers.forEach((h, i) => { obj[h] = (cols[i] || '').trim() })
    return obj
  })
}

// simple rate limit per IP for import endpoint
const rl: Record<string, { t: number; c: number }> = {}
function limited(ip: string, limit = 30, windowMs = 10 * 60 * 1000) {
  const now = Date.now()
  const rec = rl[ip] || { t: now, c: 0 }
  if (now - rec.t > windowMs) { rec.t = now; rec.c = 0 }
  rec.c += 1
  rl[ip] = rec
  return rec.c <= limit
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') return res.status(405).json({ message: 'Method not allowed' })
  const ip = (req.headers['x-forwarded-for'] as string)?.split(',')[0]?.trim() || req.socket.remoteAddress || 'unknown'
  if (!limited(ip)) return res.status(429).json({ message: 'Rate limit exceeded' })
  const { url } = req.body
  if (!url || typeof url !== 'string') return res.status(400).json({ message: 'Missing url in body' })

  try {
    const csvText = await fetchText(url)
    const parsed = parseCsvToObjects(csvText)
    
    return res.status(200).json({ success: true, rows: parsed })
  } catch (e: any) {
    console.error(JSON.stringify({ action: 'import_google_forms', status: 'error', message: e?.message || 'failed' }))
    return res.status(500).json({ success: false, message: e.message || 'Import failed' })
  }
}


