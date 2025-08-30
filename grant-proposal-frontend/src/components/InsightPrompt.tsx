import React, { useMemo, useState } from 'react'

interface InsightPromptProps {
  extracted: Record<string, any>
  onSubmit: (answers: Record<string, string>) => void
}

function flatten(obj: Record<string, any>, prefix = ''): Record<string, any> {
  return Object.keys(obj).reduce((acc: Record<string, any>, key) => {
    const value = obj[key]
    const nextKey = prefix ? `${prefix}.${key}` : key
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      Object.assign(acc, flatten(value, nextKey))
    } else {
      acc[nextKey] = value
    }
    return acc
  }, {})
}

function generateQuestions(extracted: Record<string, any>): Array<{ key: string, question: string }> {
  const flat = flatten(extracted)
  const entries = Object.entries(flat)
  const questions: Array<{ key: string, question: string }> = []

  for (const [key, value] of entries) {
    if (value == null || value === '' || (Array.isArray(value) && value.length === 0)) {
      questions.push({ key, question: `Provide details for "${key}"` })
    } else if (typeof value === 'string' && value.split(' ').length < 5) {
      questions.push({ key, question: `Clarify or expand on "${key}"` })
    }
  }
  // Heuristic: cap between 3 and 7
  if (questions.length < 3) {
    const extras = entries
      .filter(([k]) => !questions.find(q => q.key === k))
      .slice(0, 3 - questions.length)
      .map(([k]) => ({ key: k, question: `Add any important context for "${k}"` }))
    questions.push(...extras)
  }
  return questions.slice(0, 7)
}

export default function InsightPrompt({ extracted, onSubmit }: InsightPromptProps) {
  const qs = useMemo(() => generateQuestions(extracted), [extracted])
  const [answers, setAnswers] = useState<Record<string, string>>({})

  function handleChange(key: string, value: string) {
    setAnswers(prev => ({ ...prev, [key]: value }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit(answers)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {qs.map(({ key, question }) => (
        <div key={key} className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">{question}</label>
          <textarea
            className="w-full text-sm border rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            rows={3}
            value={answers[key] || ''}
            onChange={(e) => handleChange(key, e.target.value)}
            placeholder="Type your answer..."
          />
          <div className="text-[11px] text-gray-500">Key: {key}</div>
        </div>
      ))}
      <div className="pt-2">
        <button
          type="submit"
          className="text-sm px-3 py-1.5 rounded bg-primary-600 text-white hover:bg-primary-700"
        >
          Continue
        </button>
      </div>
    </form>
  )
}


