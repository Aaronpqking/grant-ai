import React, { useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import type { Section } from '../lib/api'

interface SectionEditorProps {
  section: Section
  onChange: (updated: Section, isDirty: boolean) => void
  showMarkdown?: boolean
}

export default function SectionEditor({ section, onChange, showMarkdown = false }: SectionEditorProps) {
  const [content, setContent] = useState<string>(section.content || '')
  const [preview, setPreview] = useState<boolean>(showMarkdown)

  const isDirty = useMemo(() => content !== (section.content || ''), [content, section.content])

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const next = e.target.value
    setContent(next)
    onChange({ ...section, content: next }, next !== (section.content || ''))
  }

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-900">{section.title}</h3>
        <div className="flex items-center gap-3">
          {isDirty && (
            <span className="inline-flex items-center rounded-full bg-yellow-50 px-2 py-0.5 text-xs font-medium text-yellow-800 ring-1 ring-inset ring-yellow-600/20">dirty</span>
          )}
          <button
            type="button"
            onClick={() => setPreview(v => !v)}
            className="text-xs px-2 py-1 rounded border text-gray-700 hover:bg-gray-50"
          >
            {preview ? 'Edit' : 'Preview'}
          </button>
        </div>
      </div>
      {preview ? (
        <div className="prose max-w-none text-sm text-gray-800">
          {content.trim().length === 0 ? (
            <div className="text-xs text-gray-500">No content yet.</div>
          ) : (
            <ReactMarkdown>{content}</ReactMarkdown>
          )}
        </div>
      ) : (
        <textarea
          value={content}
          onChange={handleChange}
          rows={8}
          className="w-full text-sm border rounded-md p-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      )}
    </div>
  )
}


