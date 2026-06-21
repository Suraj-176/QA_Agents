import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Eye, ClipboardList, Bug, CheckCircle2, ChevronRight, Activity } from 'lucide-react'

const API_BASE_URL = 'http://127.0.0.1:5000/api'

function Dashboard({ setActiveTab }) {
  const [stats, setStats] = useState({
    baselines: 0,
    testSuites: 0,
    bugReports: 0,
    regressionTestsRun: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardStats = async () => {
      try {
        const [baselinesRes, suitesRes, bugsRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/regression-testing/baselines`),
          axios.get(`${API_BASE_URL}/test-cases/suites`),
          axios.get(`${API_BASE_URL}/bug-reporter/reports`)
        ])
        
        setStats({
          baselines: baselinesRes.data.length,
          testSuites: suitesRes.data.length,
          bugReports: bugsRes.data.length,
          regressionTestsRun: baselinesRes.data.reduce((acc, b) => acc + (b.runs ? b.runs.length : 1), 0)
        })
      } catch (err) {
        console.error('Failed to load dashboard metrics:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchDashboardStats()
  }, [])

  return (
    <div className="space-y-10 animate-fadeIn">
      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 p-6 rounded-2xl flex items-center justify-between shadow-sm transition-all">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-gray-500">Established Baselines</p>
            <h3 className="text-3xl font-extrabold text-slate-800 dark:text-white tracking-tight">{loading ? '...' : stats.baselines}</h3>
          </div>
          <div className="w-12 h-10 bg-indigo-600/10 border border-indigo-500/10 text-indigo-500 dark:text-indigo-400 rounded-xl flex items-center justify-center">
            <Eye size={20} />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 p-6 rounded-2xl flex items-center justify-between shadow-sm transition-all">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-gray-500">Visual Runs Logged</p>
            <h3 className="text-3xl font-extrabold text-slate-850 dark:text-white tracking-tight">{loading ? '...' : stats.regressionTestsRun}</h3>
          </div>
          <div className="w-12 h-10 bg-emerald-600/10 border border-emerald-500/10 text-emerald-500 dark:text-emerald-400 rounded-xl flex items-center justify-center">
            <CheckCircle2 size={20} />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 p-6 rounded-2xl flex items-center justify-between shadow-sm transition-all">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-gray-500">Test Suites Created</p>
            <h3 className="text-3xl font-extrabold text-slate-850 dark:text-white tracking-tight">{loading ? '...' : stats.testSuites}</h3>
          </div>
          <div className="w-12 h-10 bg-violet-600/10 border border-violet-500/10 text-violet-500 dark:text-violet-400 rounded-xl flex items-center justify-center">
            <ClipboardList size={20} />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 p-6 rounded-2xl flex items-center justify-between shadow-sm transition-all">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-gray-500">Discovered Bugs</p>
            <h3 className="text-3xl font-extrabold text-slate-850 dark:text-white tracking-tight">{loading ? '...' : stats.bugReports}</h3>
          </div>
          <div className="w-12 h-10 bg-amber-600/10 border border-amber-500/10 text-amber-500 dark:text-amber-400 rounded-xl flex items-center justify-center">
            <Bug size={20} />
          </div>
        </div>
      </div>

      {/* Quick Launch & Active Status sections */}
      <div className="grid grid-cols-3 gap-8">
        {/* Core Quick launcher panel */}
        <div className="col-span-2 bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-2xl p-8 space-y-6 transition-all">
          <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2.5">
            <Activity size={18} className="text-indigo-500 dark:text-indigo-400 animate-pulse" />
            <span>⚡ Core Agent Quick Launch</span>
          </h3>
          
          <div className="grid grid-cols-3 gap-4">
            <button
              onClick={() => setActiveTab('regression')}
              className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800/80 hover:border-indigo-500/30 dark:hover:border-indigo-500/30 p-6 rounded-2xl text-left space-y-4 transition-all duration-200 group active:scale-[0.98]"
            >
              <div className="w-10 h-10 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-xl flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-all">
                <Eye size={18} />
              </div>
              <div>
                <h4 className="font-bold text-sm text-slate-800 dark:text-gray-100 flex items-center gap-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                  <span>Smart Visuals</span>
                  <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 transition-all" />
                </h4>
                <p className="text-xs text-slate-500 dark:text-gray-400 mt-1 leading-relaxed">Establish base frames and analyze responsive browser alignments.</p>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('testcases')}
              className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800/80 hover:border-violet-500/30 dark:hover:border-violet-500/30 p-6 rounded-2xl text-left space-y-4 transition-all duration-200 group active:scale-[0.98]"
            >
              <div className="w-10 h-10 bg-violet-500/10 text-violet-600 dark:text-violet-400 rounded-xl flex items-center justify-center group-hover:bg-violet-600 group-hover:text-white transition-all">
                <ClipboardList size={18} />
              </div>
              <div>
                <h4 className="font-bold text-sm text-slate-800 dark:text-gray-100 flex items-center gap-1 group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
                  <span>Requirements parser</span>
                  <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 transition-all" />
                </h4>
                <p className="text-xs text-slate-500 dark:text-gray-400 mt-1 leading-relaxed">Pipes raw user stories or markdown requirements to write structured test cases.</p>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('bugreporter')}
              className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800/80 hover:border-amber-500/30 dark:hover:border-amber-500/30 p-6 rounded-2xl text-left space-y-4 transition-all duration-200 group active:scale-[0.98]"
            >
              <div className="w-10 h-10 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-xl flex items-center justify-center group-hover:bg-amber-600 group-hover:text-white transition-all">
                <Bug size={18} />
              </div>
              <div>
                <h4 className="font-bold text-sm text-slate-800 dark:text-gray-100 flex items-center gap-1 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">
                  <span>Bug Auditor</span>
                  <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 transition-all" />
                </h4>
                <p className="text-xs text-slate-500 dark:text-gray-400 mt-1 leading-relaxed">Direct screenshot upload and LLM Vision alignment audit.</p>
              </div>
            </button>
          </div>
        </div>

        {/* Environmental Platform Health Panel */}
        <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-2xl p-8 space-y-6 transition-all">
          <h3 className="text-lg font-bold text-slate-800 dark:text-white">⚙️ System Topology</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-gray-800/60 pb-3">
              <span className="text-sm text-slate-500 dark:text-gray-400">REST API Server</span>
              <span className="text-sm font-semibold text-slate-700 dark:text-gray-200">FastAPI (Python)</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-gray-800/60 pb-3">
              <span className="text-sm text-slate-500 dark:text-gray-400">Database Engine</span>
              <span className="text-sm font-semibold text-slate-700 dark:text-gray-200">SQLite 3 (Zero Setup)</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-gray-800/60 pb-3">
              <span className="text-sm text-slate-500 dark:text-gray-400">Browser Driver</span>
              <span className="text-sm font-semibold text-slate-700 dark:text-gray-200">Playwright (Headless)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-500 dark:text-gray-400">Visual Engine</span>
              <span className="text-sm font-semibold text-slate-700 dark:text-gray-200">OpenCV Grayscale Diff</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
