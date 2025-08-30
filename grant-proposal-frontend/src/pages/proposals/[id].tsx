import React, { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/router'
import SectionEditor from '../../components/SectionEditor'
import CommentPanel from '../../components/CommentPanel'
import StepBar from '../../components/StepBar'
import { getDraft as apiGetDraft, addComment as apiAddComment, refine as apiRefine, Draft, Section, Comment } from '../../lib/api'

export default function ProposalDetailPage() {
  const router = useRouter()
  const { id } = router.query as { id?: string }

  const [draft, setDraft] = useState<Draft | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null)
  const [dirtyMap, setDirtyMap] = useState<Record<string, boolean>>({})

  useEffect(() => {
    if (!id) return
    let mounted = true
    setLoading(true)
    apiGetDraft(id)
      .then((d) => {
        if (!mounted) return
        setDraft(d)
        setSelectedSectionId(d.sections?.[0]?.id || null)
      })
      .catch((e: any) => setError(e?.message || 'Failed to load draft'))
      .finally(() => setLoading(false))
    return () => { mounted = false }
  }, [id])

  const commentsForSelected = useMemo<Comment[]>(() => {
    if (!draft || !selectedSectionId) return []
    return draft.comments?.[selectedSectionId] || []
  }, [draft, selectedSectionId])

  function handleSectionChange(updated: Section, isDirty: boolean) {
    if (!draft) return
    setDraft({
      ...draft,
      sections: draft.sections.map((s) => (s.id === updated.id ? updated : s))
    })
    setDirtyMap(prev => ({ ...prev, [updated.id]: isDirty }))
  }

  function showApiError(e: unknown) {
    const err = e as { message?: string }
    alert(`Request failed. ${err?.message ?? ''}`.trim())
  }

  async function handleAddComment(text: string) {
    if (!draft || !selectedSectionId) return
    const newComment = await apiAddComment(draft.id, { sectionId: selectedSectionId, text })
    setDraft(prev => {
      if (!prev) return prev
      const map = { ...(prev.comments || {}) }
      const arr = map[selectedSectionId] ? [...map[selectedSectionId]] : []
      arr.unshift(newComment)
      map[selectedSectionId] = arr
      return { ...prev, comments: map }
    })
  }

  async function handleRefine() {
    if (!draft) return
    const dirtyIds = Object.entries(dirtyMap).filter(([_, v]) => v).map(([k]) => k)
    if (dirtyIds.length === 0) return
    try {
      setLoading(true)
      const updatedMap = await apiRefine(draft.id, dirtyIds)
      setDraft(prev => prev ? { ...prev, sections: prev.sections.map(s => (updatedMap[s.id] ? { ...s, content: updatedMap[s.id] } : s)) } : prev)
      setDirtyMap(prev => {
        const copy = { ...prev }
        for (const id of dirtyIds) delete copy[id]
        return copy
      })
    } catch (e: any) {
      setError(e?.message || 'Refine failed')
      showApiError(e)
    } finally {
      setLoading(false)
    }
  }

  function handleFinalize() {
    // Placeholder V1: transition locally to final
    if (!draft) return
    setDraft({ ...draft, status: 'final' })
  }

  if (loading && !draft) {
    return <div className="p-6 text-sm">Loading...</div>
  }
  if (error && !draft) {
    return <div className="p-6 text-sm text-red-600">{error}</div>
  }
  if (!draft) return null

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <StepBar current={'Draft'} />
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Proposal Draft</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefine}
            className="text-sm px-3 py-1.5 rounded bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Refining...' : 'Refine Changed Sections'}
          </button>
          <button
            onClick={handleFinalize}
            className="text-sm px-3 py-1.5 rounded border hover:bg-gray-50"
          >
            Finalize
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 space-y-3">
          {draft.sections.map((s) => (
            <div key={s.id} onClick={() => setSelectedSectionId(s.id)} className={"cursor-pointer"}>
              <SectionEditor section={s} onChange={handleSectionChange} />
            </div>
          ))}
        </div>
        <div className="col-span-1">
          <CommentPanel
            sectionId={selectedSectionId}
            comments={commentsForSelected}
            onAddComment={handleAddComment}
          />
        </div>
      </div>
    </div>
  )
}


