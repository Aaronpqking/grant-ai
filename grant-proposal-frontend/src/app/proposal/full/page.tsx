import { FullProposalBuilder } from '@/components/full-proposal-builder'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

export default function FullProposalPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Navigation */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Link 
          href="/"
          className="inline-flex items-center text-gray-600 hover:text-gray-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Link>
      </div>
      
      {/* Builder */}
      <FullProposalBuilder />
    </div>
  )
} 