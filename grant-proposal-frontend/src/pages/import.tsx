import React, { useMemo, useState } from 'react'
import StepBar from '../components/StepBar'
import InsightPrompt from '../components/InsightPrompt'
import { importDoc as apiImportDoc, createDraft as apiCreateDraft, Section } from '../lib/api'

type Step = 'Upload' | 'Review' | 'Insight' | 'Draft'

export default function ImportPage() {
  const [step, setStep] = useState<Step>('Upload')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [extracted, setExtracted] = useState<Record<string, any>>({})
  const [suggestedSections, setSuggestedSections] = useState<Section[]>([])
  const [prefill, setPrefill] = useState(true)

  const previewEntries = useMemo(() => Object.entries(extracted || {}), [extracted])

  function showApiError(e: unknown) {
    const err = e as { message?: string }
    alert(`Request failed. ${err?.message ?? ''}`.trim())
  }

  async function handleUpload() {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const res = await apiImportDoc(file)
      setExtracted(res.extracted || {})
      setSuggestedSections(res.suggestedSections || [])
      setStep('Review')
    } catch (e: any) {
      setError(e?.message || 'Upload failed')
      showApiError(e)
    } finally {
      setLoading(false)
    }
  }

  function mergeDotted(base: Record<string, any>, updates: Record<string, string>) {
    const copy = JSON.parse(JSON.stringify(base || {}))
    for (const [dottedKey, value] of Object.entries(updates)) {
      const parts = dottedKey.split('.')
      let cursor: any = copy
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i]
        const isLast = i === parts.length - 1
        if (isLast) {
          cursor[part] = value
        } else {
          cursor[part] = cursor[part] ?? {}
          cursor = cursor[part]
        }
      }
    }
    return copy
  }

  async function handleInsightSubmit(answers: Record<string, string>) {
    const merged = mergeDotted(extracted, answers)
    setExtracted(merged)
    if (prefill) {
      try {
        setLoading(true)
        const draft = await apiCreateDraft(merged)
        // route to /proposals/[id]
        window.location.href = `/proposals/${draft.id}`
      } catch (e: any) {
        setError(e?.message || 'Failed to create draft')
        showApiError(e)
      } finally {
        setLoading(false)
      }
    } else {
      setStep('Draft')
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <StepBar current={step} onStepChange={setStep} />
      <div className="space-y-4">
        {error && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 border border-red-200">{error}</div>
        )}
        {step === 'Upload' && (
          <div className="border rounded-lg p-6 bg-white shadow-sm">
            <h2 className="text-base font-semibold mb-2">Upload document</h2>
            <p className="text-sm text-gray-600 mb-4">Upload .pdf, .docx, .txt, or .md</p>
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="text-sm"
            />
            <div className="mt-4 flex items-center gap-3">
              <button
                className="text-sm px-4 py-2 rounded bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50"
                onClick={handleUpload}
                disabled={!file || loading}
              >
                {loading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        )}

        {step === 'Review' && (
          <div className="border rounded-lg p-6 bg-white shadow-sm space-y-4">
            <h2 className="text-base font-semibold">Preview extracted</h2>
            <div className="grid grid-cols-1 gap-3">
              {previewEntries.length === 0 && (
                <div className="text-sm text-gray-500">No extracted fields found.</div>
              )}
              {previewEntries.map(([k, v]) => (
                <div key={k} className="flex justify-between text-sm">
                  <span className="text-gray-600">{k}</span>
                  <span className="text-gray-900 max-w-[65%] truncate" title={typeof v === 'string' ? v : JSON.stringify(v)}>
                    {typeof v === 'string' ? v : JSON.stringify(v)}
                  </span>
                </div>
              ))}
            </div>
            {suggestedSections.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mt-4 mb-2">Suggested sections</h3>
                <div className="space-y-3">
                  {suggestedSections.map((s) => (
                    <div key={s.id} className="border rounded p-3">
                      <div className="text-xs font-medium text-gray-700 mb-1">{s.title}</div>
                      <pre className="whitespace-pre-wrap text-sm text-gray-800">{s.content}</pre>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="flex items-center gap-3 pt-2">
              <label className="inline-flex items-center gap-2 text-sm">
                <input type="checkbox" checked={prefill} onChange={(e) => setPrefill(e.target.checked)} />
                Prefill draft with insights
              </label>
              <button
                className="ml-auto text-sm px-4 py-2 rounded bg-primary-600 text-white hover:bg-primary-700"
                onClick={() => setStep('Insight')}
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {step === 'Insight' && (
          <div className="border rounded-lg p-6 bg-white shadow-sm">
            <h2 className="text-base font-semibold mb-4">Insight prompts</h2>
            <InsightPrompt extracted={extracted} onSubmit={handleInsightSubmit} />
          </div>
        )}
      </div>
    </div>
  )
}


