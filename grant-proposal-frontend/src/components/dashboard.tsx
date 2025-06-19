'use client'

import React, { useState, useEffect } from 'react'
import { } from 'lucide-react'
import Link from 'next/link'
import { grantAPI } from '@/lib/api'

interface DashboardStats {
  totalProposals: number
  inProgress: number
  completed: number
  successRate: number
  totalFunding: string
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalProposals: 0,
    inProgress: 0,
    completed: 0,
    successRate: 0,
    totalFunding: '$0'
  })
  const [isHealthy, setIsHealthy] = useState(false)
  const [recentProposals, setRecentProposals] = useState<any[]>([])

  useEffect(() => {
    checkAPIHealth()
    loadDashboardData()
  }, [])

  const checkAPIHealth = async () => {
    try {
      await grantAPI.checkHealth()
      setIsHealthy(true)
    } catch (error) {
      console.error('API health check failed:', error)
      setIsHealthy(false)
    }
  }

  const loadDashboardData = () => {
    // Load from localStorage for demo purposes
    const savedProposals = localStorage.getItem('grantProposals')
    if (savedProposals) {
      const proposals = JSON.parse(savedProposals)
      setRecentProposals(proposals.slice(0, 3))
      
      // Calculate stats
      const completed = proposals.filter((p: any) => p.status === 'completed').length
      const inProgress = proposals.filter((p: any) => p.status === 'in_progress').length
      
      setStats({
        totalProposals: proposals.length,
        inProgress,
        completed,
        successRate: proposals.length > 0 ? Math.round((completed / proposals.length) * 100) : 0,
        totalFunding: `$${(proposals.length * 50000).toLocaleString()}`
      })
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Grant Proposal AI</h1>
              <p className="text-gray-600">Powered by Vertex AI</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                isHealthy ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                <div className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span>{isHealthy ? 'API Online' : 'API Offline'}</span>
              </div>
              <Link 
                href="/proposal/quick"
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-all duration-200 flex items-center space-x-2"
              >
                <PlusCircle className="w-5 h-5" />
                <span>New Proposal</span>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Proposals</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalProposals}</p>
              </div>
              <div className="bg-blue-100 p-3 rounded-lg">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">In Progress</p>
                <p className="text-3xl font-bold text-gray-900">{stats.inProgress}</p>
              </div>
              <div className="bg-yellow-100 p-3 rounded-lg">
                <Clock className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-3xl font-bold text-gray-900">{stats.successRate}%</p>
              </div>
              <div className="bg-green-100 p-3 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Funding</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalFunding}</p>
              </div>
              <div className="bg-purple-100 p-3 rounded-lg">
                <DollarSign className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <Link href="/proposal/quick" className="group">
            <div className="bg-white rounded-xl shadow-sm p-8 border border-gray-100 hover:shadow-lg transition-all duration-300 group-hover:border-blue-200">
              <div className="flex items-center space-x-4 mb-4">
                <div className="bg-blue-100 p-4 rounded-lg group-hover:bg-blue-200 transition-colors">
                  <Target className="w-8 h-8 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">Quick Proposal</h3>
                  <p className="text-gray-600">Generate a proposal in under 5 minutes</p>
                </div>
              </div>
              <p className="text-gray-700">Perfect for time-sensitive applications. Just provide basic information and let our AI create a compelling proposal.</p>
              <div className="mt-4 text-blue-600 font-medium group-hover:text-blue-700">Start Quick Proposal →</div>
            </div>
          </Link>

          <Link href="/proposal/full" className="group">
            <div className="bg-white rounded-xl shadow-sm p-8 border border-gray-100 hover:shadow-lg transition-all duration-300 group-hover:border-green-200">
              <div className="flex items-center space-x-4 mb-4">
                <div className="bg-green-100 p-4 rounded-lg group-hover:bg-green-200 transition-colors">
                  <FileText className="w-8 h-8 text-green-600" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">Full Proposal Builder</h3>
                  <p className="text-gray-600">Comprehensive proposal with all sections</p>
                </div>
              </div>
              <p className="text-gray-700">For complex grants requiring detailed documentation. Upload documents, collaborate with team members, and create winning proposals.</p>
              <div className="mt-4 text-green-600 font-medium group-hover:text-green-700">Build Full Proposal →</div>
            </div>
          </Link>
        </div>

        {/* Recent Proposals */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Recent Proposals</h2>
          </div>
          <div className="p-6">
            {recentProposals.length > 0 ? (
              <div className="space-y-4">
                {recentProposals.map((proposal, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="flex items-center space-x-4">
                      <div className={`w-3 h-3 rounded-full ${
                        proposal.status === 'completed' ? 'bg-green-500' : 'bg-yellow-500'
                      }`}></div>
                      <div>
                        <h3 className="font-medium text-gray-900">{proposal.title || 'Untitled Proposal'}</h3>
                        <p className="text-sm text-gray-600">{proposal.organization || 'Unknown Organization'}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">{proposal.amount || '$50,000'}</p>
                      <p className="text-xs text-gray-500">{new Date(proposal.timestamp || Date.now()).toLocaleDateString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No proposals yet</h3>
                <p className="text-gray-600 mb-4">Create your first grant proposal to get started</p>
                <Link 
                  href="/proposal/quick"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <PlusCircle className="w-4 h-4 mr-2" />
                  Create Proposal
                </Link>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
} 