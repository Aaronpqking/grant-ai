import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') return res.status(405).json({ message: 'Method not allowed' })

  try {
    const { title, sections } = req.body || {}
    if (!sections || typeof sections !== 'object') {
      return res.status(400).json({ success: false, message: 'Missing sections' })
    }

    const { Document, Packer, Paragraph, HeadingLevel, TextRun } = await import('docx')

    const doc = new Document({
      sections: [
        {
          children: [
            new Paragraph({
              text: title || 'Grant Proposal',
              heading: HeadingLevel.TITLE,
            }),
            ...Object.entries(sections).flatMap(([name, content]: any) => [
              new Paragraph({ text: '' }),
              new Paragraph({ text: name, heading: HeadingLevel.HEADING_1 }),
              new Paragraph({ children: [new TextRun({ text: (content || '').toString() })] }),
            ]),
          ],
        },
      ],
    })

    const buffer = await Packer.toBuffer(doc)
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    res.setHeader('Content-Disposition', `attachment; filename="${(title || 'grant-proposal').replace(/\s+/g, '_')}.docx"`)
    return res.status(200).send(buffer)
  } catch (e: any) {
    console.error(JSON.stringify({ action: 'export_docx', status: 'error', message: e?.message || 'failed' }))
    return res.status(500).json({ success: false, message: e?.message || 'Export failed' })
  }
}


