import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { ClipboardList, Play, Trash, ChevronDown, ChevronUp, FileText, CheckCircle2 } from 'lucide-react'

const API_BASE_URL = 'http://127.0.0.1:5000/api'

function TestCaseModule() {
  const [suites, setSuites] = useState([])
  const [activeSuite, setActiveSuite] = useState(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)

  // Input states
  const [reqTitle, setReqTitle] = useState('')
  const [requirements, setRequirements] = useState('')

  // Accordion active state for test cases
  const [expandedCaseId, setExpandedCaseId] = useState(null)

  useEffect(() => {
    fetchSuites()
  }, [])

  const fetchSuites = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_BASE_URL}/test-cases/suites`)
      setSuites(response.data)
      if (response.data.length > 0 && !activeSuite) {
        fetchSuiteDetails(response.data[0].id)
      }
    } catch (err) {
      console.error('Failed to load suites:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchSuiteDetails = async (suiteId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/test-cases/suites/${suiteId}`)
      setActiveSuite(response.data)
    } catch (err) {
      console.error('Failed to load suite details:', err)
    }
  }

  const handleGenerate = async (e) => {
    e.preventDefault()
    if (!requirements) return

    // Extract dynamic keys from localStorage
    const provider = localStorage.getItem('llm_provider') || 'gemini'
    const model = localStorage.getItem('llm_model') || 'gemini-1.5-flash'
    const apiKey = localStorage.getItem('llm_api_key')

    if (!apiKey) {
      alert('Missing LLM API Key. Please navigate to the Configuration Panel to configure your keys first.')
      return
    }

    setGenerating(true)
    try {
      const response = await axios.post(
        `${API_BASE_URL}/test-cases/generate`,
        {
          requirements: requirements,
          title: reqTitle || undefined
        },
        {
          headers: {
            'X-LLM-Provider': provider,
            'X-LLM-Model': model,
            'X-LLM-API-Key': apiKey
          }
        }
      )

      setReqTitle('')
      setRequirements('')
      await fetchSuites()
      // Set generated suite as active
      if (response.data.suite_id) {
        await fetchSuiteDetails(response.data.suite_id)
      }
    } catch (err) {
      alert(`Generation failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setGenerating(false)
    }
  }

  const handleDeleteSuite = async (suiteId) => {
    if (!confirm('Are you sure you want to permanently delete this test suite?')) return
    try {
      await axios.delete(`${API_BASE_URL}/test-cases/suites/${suiteId}`)
      setActiveSuite(null)
      await fetchSuites()
    } catch (err) {
      alert('Delete failed.')
    }
  }

  const toggleCase = (id) => {
    setExpandedCaseId(expandedCaseId === id ? null : id)
  }

  return (
    <div className="grid grid-cols-12 gap-8 animate-fadeIn">
      {/* Sidebar: Test suites list */}
      <div className="col-span-4 bg-gray-900 border border-gray-800 rounded-2xl p-6 h-fit space-y-6">
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <ClipboardList size={18} className="text-indigo-400" />
            <span>Generated Suites</span>
          </h3>
        </div>

        {/* Requirements form */}
        <form onSubmit={handleGenerate} className="space-y-4 bg-gray-950 p-4 border border-gray-800/60 rounded-xl">
          <p className="text-xs font-bold uppercase tracking-wider text-indigo-400">Generate Suite</p>
          <div className="space-y-1">
            <input
              type="text"
              placeholder="Suite title (e.g. Checkout Cart)"
              value={reqTitle}
              onChange={(e) => setReqTitle(e.target.value)}
              className="w-full bg-gray-900 border border-gray-800/80 rounded-lg px-3 py-2.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
              disabled={generating}
            />
          </div>
          <div className="space-y-1">
            <textarea
              placeholder="Paste requirements, user stories, or functional constraints here..."
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              rows={4}
              className="w-full bg-gray-900 border border-gray-800/80 rounded-lg p-3 text-xs text-gray-200 focus:outline-none focus:border-indigo-500 placeholder:text-gray-600 resize-none leading-relaxed"
              required
              disabled={generating}
            />
          </div>
          <button
            type="submit"
            disabled={generating}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold py-2.5 rounded-lg flex items-center justify-center gap-1.5 active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none"
          >
            {generating ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                <span>AI Engineering Cases...</span>
              </>
            ) : (
              <>
                <Play size={14} />
                <span>Generate Test Cases</span>
              </>
            )}
          </button>
        </form>

        {/* Suites listing */}
        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
          {suites.length === 0 ? (
            <p className="text-xs text-gray-500 text-center py-4">No test suites created yet.</p>
          ) : (
            suites.map((s) => (
              <button
                key={s.id}
                onClick={() => fetchSuiteDetails(s.id)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-center justify-between ${
                  activeSuite?.id === s.id
                    ? 'bg-indigo-600/10 border-indigo-500/20 text-indigo-300 font-semibold'
                    : 'bg-gray-950/40 border-gray-800/40 text-gray-400 hover:border-gray-800 hover:text-gray-200'
                }`}
              >
                <div className="truncate pr-4">
                  <p className="text-sm truncate">{s.title}</p>
                  <p className="text-xs text-gray-500 truncate mt-0.5">{s.test_case_count} cases</p>
                </div>
                <ChevronRightActive active={activeSuite?.id === s.id} />
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Panel: Suite details viewer */}
      <div className="col-span-8">
        {activeSuite ? (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 space-y-6">
            <div className="border-b border-gray-800 pb-5 flex items-center justify-between select-none">
              <div>
                <h3 className="font-bold text-lg text-white">{activeSuite.title}</h3>
                <p className="text-xs text-gray-500 mt-1">Created on: {new Date(activeSuite.created_at).toLocaleString()}</p>
              </div>
              <button
                onClick={() => handleDeleteSuite(activeSuite.id)}
                className="bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 p-2.5 rounded-xl transition-all active:scale-[0.96]"
                title="Delete Test Suite"
              >
                <Trash size={16} />
              </button>
            </div>

            {/* Accordion Test Cases list */}
            <div className="space-y-3">
              {activeSuite.test_cases?.map((tc) => (
                <div
                  key={tc.id}
                  className="border border-gray-800/60 rounded-xl overflow-hidden bg-gray-950/25 hover:border-gray-800 transition-colors"
                >
                  {/* Header click */}
                  <div
                    onClick={() => toggleCase(tc.id)}
                    className="p-4 flex items-center justify-between cursor-pointer select-none"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-bold text-indigo-400 bg-indigo-500/5 border border-indigo-500/10 px-2.5 py-1 rounded">
                        {tc.test_id}
                      </span>
                      <h4 className="font-bold text-sm text-gray-200">{tc.title}</h4>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className={`text-[10px] uppercase tracking-wider font-extrabold px-2.5 py-0.5 border rounded-full ${
                        tc.priority === 'High'
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          : tc.priority === 'Medium'
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                          : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                      }`}>
                        {tc.priority}
                      </span>
                      {expandedCaseId === tc.id ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />}
                    </div>
                  </div>

                  {/* Body expansion */}
                  {expandedCaseId === tc.id && (
                    <div className="p-5 border-t border-gray-800/60 bg-gray-950/50 space-y-4 animate-slideDown">
                      <div className="space-y-1">
                        <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Test Objective</p>
                        <p className="text-sm text-gray-300 leading-relaxed">{tc.description}</p>
                      </div>

                      {tc.preconditions && (
                        <div className="space-y-1">
                          <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Preconditions</p>
                          <p className="text-sm text-gray-300 leading-relaxed bg-gray-900 border border-gray-800 p-3 rounded-lg font-mono text-[11px]">{tc.preconditions}</p>
                        </div>
                      )}

                      <div className="space-y-2">
                        <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Action Steps</p>
                        <ol className="space-y-1.5 list-decimal list-inside text-sm text-gray-300">
                          {tc.steps?.map((step, idx) => (
                            <li key={idx} className="leading-relaxed pl-1">{step}</li>
                          ))}
                        </ol>
                      </div>

                      <div className="space-y-1">
                        <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Expected Outcome</p>
                        <div className="p-3.5 bg-emerald-500/5 border border-emerald-500/10 rounded-lg flex items-start gap-2.5 text-sm text-emerald-300/90 leading-relaxed">
                          <CheckCircle2 size={16} className="text-emerald-400 shrink-0 mt-0.5" />
                          <span>{tc.expected_result}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center text-gray-500 select-none">
            <ClipboardList size={48} className="mx-auto text-gray-700 mb-4" />
            <h4 className="font-bold text-gray-300 text-lg">No Active Suite Selected</h4>
            <p className="text-sm text-gray-500 max-w-sm mx-auto mt-1 leading-relaxed">Paste functional specifications or choose an established test case suite from the sidebar to inspect structural outcomes.</p>
          </div>
        )}
      </div>
    </div>
  )
}

function ChevronRightActive({ active }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={2.5}
      stroke="currentColor"
      className={`w-4 h-4 transition-transform duration-200 ${active ? 'translate-x-1' : 'opacity-40'}`}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
  )
}

export default TestCaseModule
