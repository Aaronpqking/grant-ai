import React, { useState } from 'react'
import type { Comment } from '../lib/api'

interface CommentPanelProps {
  sectionId: string | null
  comments: Comment[]
  onAddComment: (text: string) => Promise<void> | void
}

export default function CommentPanel({ sectionId, comments, onAddComment }: CommentPanelProps) {
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!text.trim()) return
    try {
      setSubmitting(true)
      await onAddComment(text.trim())
      setText('')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <aside className="border rounded-lg p-4 bg-white shadow-sm h-full">
      <div className="mb-3 flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-900">Comments</h4>
        <span className="text-xs text-gray-500">{sectionId ? `Section ${sectionId}` : 'No section selected'}</span>
      </div>
      <div className="space-y-3 mb-4 max-h-64 overflow-auto">
        {comments.length === 0 && (
          <div className="text-xs text-gray-500">No comments yet.</div>
        )}
        {comments.map((c) => (
          <div key={c.id} className="border rounded-md p-2">
            <div className="text-xs text-gray-500 flex justify-between">
              <span>{c.author || 'Anonymous'}</span>
              <span>{new Date(c.createdAt).toLocaleString()}</span>
            </div>
            <p className="text-sm text-gray-800 whitespace-pre-wrap mt-1">{c.text}</p>
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="space-y-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          className="w-full text-sm border rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          disabled={!sectionId || submitting}
        />
        <button
          type="submit"
          disabled={!sectionId || submitting || !text.trim()}
          className="text-sm px-3 py-1.5 rounded bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50"
        >
          {submitting ? 'Adding...' : 'Add Comment'}
        </button>
      </form>
    </aside>
  )
}


