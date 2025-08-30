import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') return res.status(405).json({ message: 'Method not allowed' })
  return res.status(200).json({
    enable_quick_proposal: process.env.ENABLE_QUICK_PROPOSAL === 'true'
  })
}


