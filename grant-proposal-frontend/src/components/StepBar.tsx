import React from 'react'

type Step = 'Upload' | 'Review' | 'Insight' | 'Draft'

interface StepBarProps {
  current: Step
  onStepChange?: (step: Step) => void
}

const steps: Step[] = ['Upload', 'Review', 'Insight', 'Draft']

export default function StepBar({ current, onStepChange }: StepBarProps) {
  return (
    <nav aria-label="Progress" className="mb-4">
      <ol role="list" className="flex items-center">
        {steps.map((step, idx) => {
          const isActive = step === current
          return (
            <li key={step} className="relative flex-1 flex items-center">
              <button
                type="button"
                onClick={() => onStepChange && onStepChange(step)}
                className={`flex items-center text-xs ${isActive ? 'text-primary-700' : 'text-gray-500'}`}
              >
                <span className={`flex h-6 w-6 items-center justify-center rounded-full border ${isActive ? 'border-primary-600 bg-primary-50' : 'border-gray-300'}`}>
                  {idx + 1}
                </span>
                <span className="ml-2">{step}</span>
              </button>
              {idx < steps.length - 1 && (
                <div className="mx-3 h-px flex-1 bg-gray-200" />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}


