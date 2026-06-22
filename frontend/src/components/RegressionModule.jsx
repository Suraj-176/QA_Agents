import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Eye, Play, Plus, RefreshCw, AlertTriangle, CheckCircle, Image as ImageIcon, Trash, ChevronRight } from 'lucide-react'

const API_BASE_URL = 'http://127.0.0.1:5000/api'
const STATIC_URL = 'http://127.0.0.1:5000/static'

function RegressionModule() {
  const [baselines, setBaselines] = useState([])
  const [loading, setLoading] = useState(false)
  const [activeBaseline, setActiveBaseline] = useState(null)

  // Form states for creating baseline
  const [newName, setNewName] = useState('')
  const [newUrl, setNewUrl] = useState('')

  // Form states for running tests
  const [targetUrl, setTargetUrl] = useState('')
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)

  // Modal visual states
  const [activeModalImg, setActiveModalImg] = useState(null)

  useEffect(() => {
    fetchBaselines()
  }, [])

  const fetchBaselines = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_BASE_URL}/regression-testing/baselines`)
      setBaselines(response.data)
      if (response.data.length > 0 && !activeBaseline) {
        setActiveBaseline(response.data[0])
        setTargetUrl(response.data[0].url)
      }
    } catch (err) {
      console.error('Failed to fetch visual baselines:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateBaseline = async (e) => {
    e.preventDefault()
    if (!newName || !newUrl) return
    setLoading(true)

    // Read transient browser headers from localStorage
    const browserHeaders = localStorage.getItem('browser_headers') || ""
    
    // Normalize Windows backslashes (\) to forward slashes (/) for HTTP header transmission safety!
    const chromeProfile = (localStorage.getItem('chrome_profile') || "").replace(/\\/g, '/')

    try {
      await axios.post(
        `${API_BASE_URL}/regression-testing/baselines`, 
        {
          name: newName,
          url: newUrl
        },
        {
          headers: {
            'X-Browser-Headers': browserHeaders,
            'X-Chrome-Profile': chromeProfile
          }
        }
      )
      setNewName('')
      setNewUrl('')
      await fetchBaselines()
    } catch (err) {
      alert(`Baseline generation failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteBaseline = async () => {
    if (!activeBaseline) return
    if (!confirm(`Are you sure you want to permanently delete baseline "${activeBaseline.name}"? This will clear all associated historical test runs and delete all image files from your local disk!`)) return
    
    setLoading(true)
    try {
      await axios.delete(`${API_BASE_URL}/regression-testing/baselines/${activeBaseline.id}`)
      setActiveBaseline(null)
      setTestResult(null)
      await fetchBaselines()
    } catch (err) {
      alert(`Delete failed: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRecaptureBaseline = async () => {
    if (!activeBaseline) return
    if (!confirm(`Are you sure you want to re-capture and overwrite baseline visual benchmarks for "${activeBaseline.name}" at URL: ${activeBaseline.url}?`)) return
    
    setLoading(true)
    const browserHeaders = localStorage.getItem('browser_headers') || ""
    const chromeProfile = (localStorage.getItem('chrome_profile') || "").replace(/\\/g, '/')

    try {
      await axios.post(
        `${API_BASE_URL}/regression-testing/baselines/${activeBaseline.id}/recapture`,
        {},
        {
          headers: {
            'X-Browser-Headers': browserHeaders,
            'X-Chrome-Profile': chromeProfile
          }
        }
      )
      alert("Baseline visual benchmarks successfully re-captured and updated on disk!")
      await fetchBaselines()
    } catch (err) {
      alert(`Recapture failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRunRegression = async (e) => {
    e.preventDefault()
    if (!activeBaseline || !targetUrl) return
    setTesting(true)
    setTestResult(null)

    const browserHeaders = localStorage.getItem('browser_headers') || ""
    const chromeProfile = (localStorage.getItem('chrome_profile') || "").replace(/\\/g, '/')

    try {
      const response = await axios.post(
        `${API_BASE_URL}/regression-testing/test`, 
        {
          baseline_id: activeBaseline.id,
          target_url: targetUrl
        },
        {
          headers: {
            'X-Browser-Headers': browserHeaders,
            'X-Chrome-Profile': chromeProfile
          }
        }
      )
      
      const runId = response.data.run_id
      pollTestStatus(runId)
    } catch (err) {
      alert(`Testing initiation failed: ${err.message}`)
      setTesting(false)
    }
  }

  const pollTestStatus = async (runId) => {
    const checkStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/regression-testing/runs/${runId}`)
        const runData = response.data
        if (runData.status === 'completed' || runData.status === 'failed') {
          setTestResult(runData)
          setTesting(false)
          clearInterval(interval)
        }
      } catch (err) {
        console.error('Polling failed:', err)
        setTesting(false)
        clearInterval(interval)
      }
    }

    const interval = setInterval(checkStatus, 2500)
  }

  return (
    <div className="grid grid-cols-12 gap-8 animate-fadeIn">
      {/* Sidebar: Baselines list */}
      <div className="col-span-4 bg-gray-900 border border-gray-800 rounded-2xl p-6 h-fit space-y-6">
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <Eye size={18} className="text-indigo-400" />
            <span>Visual Baselines</span>
          </h3>
          <button
            onClick={fetchBaselines}
            className="text-gray-500 hover:text-gray-300 transition-colors"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Create Baseline Form */}
        <form onSubmit={handleCreateBaseline} className="space-y-4 bg-gray-950 p-4 border border-gray-800/60 rounded-xl">
          <p className="text-xs font-bold uppercase tracking-wider text-indigo-400">Establish New Base</p>
          <div className="space-y-1">
            <input
              type="text"
              placeholder="e.g. Landing Page"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full bg-gray-900 border border-gray-800/80 rounded-lg px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>
          <div className="space-y-1">
            <input
              type="url"
              placeholder="https://example.com"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              className="w-full bg-gray-900 border border-gray-800/80 rounded-lg px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading || testing}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold py-2.5 rounded-lg flex items-center justify-center gap-1.5 active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none"
          >
            <Plus size={14} />
            <span>{loading ? 'Capturing Base...' : 'Capture Baseline'}</span>
          </button>
        </form>

        {/* Baselines listing */}
        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
          {baselines.length === 0 ? (
            <p className="text-xs text-gray-500 text-center py-4">No baselines established yet.</p>
          ) : (
            baselines.map((b) => (
              <button
                key={b.id}
                onClick={() => {
                  setActiveBaseline(b)
                  setTargetUrl(b.url)
                  setTestResult(null)
                }}
                className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-center justify-between ${
                  activeBaseline?.id === b.id
                    ? 'bg-indigo-600/10 border-indigo-500/20 text-indigo-300 font-semibold'
                    : 'bg-gray-950/40 border-gray-800/40 text-gray-400 hover:border-gray-800 hover:text-gray-200'
                }`}
              >
                <div className="truncate pr-4">
                  <p className="text-sm truncate">{b.name}</p>
                  <p className="text-xs text-gray-500 truncate mt-0.5">{b.url}</p>
                </div>
                <ChevronRightActive active={activeBaseline?.id === b.id} />
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Panel: Baseline inspect & run tests */}
      <div className="col-span-8 space-y-8">
        {activeBaseline ? (
          <>
            {/* Run Visual Test form */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 space-y-5">
              <div className="flex items-center justify-between border-b border-gray-800/60 pb-3 select-none">
                <h3 className="font-bold text-base text-white">🔍 Compare Base of "{activeBaseline.name}"</h3>
                <div className="flex items-center gap-3">
                  {/* Re-capture Button */}
                  <button
                    onClick={handleRecaptureBaseline}
                    disabled={loading || testing}
                    className="bg-indigo-600/10 hover:bg-indigo-600/20 border border-indigo-500/20 text-indigo-400 px-3.5 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1.5 transition-all active:scale-[0.96] disabled:opacity-50"
                    title="Re-capture Baseline Benchmarks"
                  >
                    <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
                    <span>Re-capture Base</span>
                  </button>
                  {/* Delete Button */}
                  <button
                    onClick={handleDeleteBaseline}
                    disabled={loading || testing}
                    className="bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 p-2 rounded-lg transition-all active:scale-[0.96] disabled:opacity-50"
                    title="Delete Baseline and Runs History"
                  >
                    <Trash size={14} />
                  </button>
                </div>
              </div>
              
              <form onSubmit={handleRunRegression} className="flex gap-4 pt-2">
                <input
                  type="url"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  placeholder="Enter target test url (default: baseline url)..."
                  className="flex-1 bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors"
                  required
                  disabled={testing}
                />
                <button
                  type="submit"
                  disabled={testing}
                  className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-600/50 text-white font-bold text-sm px-6 rounded-xl flex items-center gap-2 active:scale-[0.98] transition-all"
                >
                  {testing ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      <span>Comparing...</span>
                    </>
                  ) : (
                    <>
                      <Play size={16} />
                      <span>Run Comparison</span>
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Test Results list */}
            {testResult && (
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 space-y-6 animate-fadeIn">
                <div className="border-b border-gray-800 pb-4 flex items-center justify-between select-none">
                  <div>
                    <h3 className="font-bold text-lg text-white">Visual Comparison Report</h3>
                    <p className="text-xs text-gray-400 mt-1">Target URL: <span className="text-gray-300 font-semibold">{testResult.target_url}</span></p>
                  </div>
                  <div className={`px-4 py-1.5 border rounded-full text-xs font-bold flex items-center gap-1.5 ${
                    testResult.summary.includes('Visual Regressions Detected')
                      ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                      : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                  }`}>
                    {testResult.summary.includes('Visual Regressions Detected') ? <AlertTriangle size={14} /> : <CheckCircle size={14} />}
                    <span>{testResult.summary.includes('Visual Regressions Detected') ? 'Layout Regression Found' : 'Matched Baseline'}</span>
                  </div>
                </div>

                {/* Grid of Viewports */}
                <div className="grid grid-cols-3 gap-6">
                  {testResult.results?.map((res) => (
                    <div key={res.id} className="bg-gray-950 border border-gray-800/80 p-5 rounded-xl space-y-4">
                      <div className="flex items-center justify-between border-b border-gray-800 pb-3 select-none">
                        <span className="text-sm font-bold text-gray-200 capitalize">{res.viewport} Viewport</span>
                        <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ${
                          res.is_mismatch
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/10'
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/10'
                        }`}>
                          {res.is_mismatch ? `${res.similarity_score}% Match` : '100% Match'}
                        </span>
                      </div>

                      {/* View image comparison actions */}
                      <div className="grid grid-cols-3 gap-2 text-center text-xs font-semibold">
                        <button
                          onClick={() => setActiveModalImg(`${STATIC_URL}/${res.baseline_image_path}`)}
                          className="bg-gray-900 border border-gray-800 hover:border-indigo-500/30 p-2.5 rounded-lg text-gray-400 hover:text-gray-200 transition-all flex flex-col items-center gap-1"
                        >
                          <ImageIcon size={14} />
                          <span>Base</span>
                        </button>
                        <button
                          onClick={() => setActiveModalImg(`${STATIC_URL}/${res.run_image_path}`)}
                          className="bg-gray-900 border border-gray-800 hover:border-indigo-500/30 p-2.5 rounded-lg text-gray-400 hover:text-gray-200 transition-all flex flex-col items-center gap-1"
                        >
                          <ImageIcon size={14} />
                          <span>Run</span>
                        </button>
                        <button
                          onClick={() => setActiveModalImg(`${STATIC_URL}/${res.diff_image_path}`)}
                          className="bg-gray-900 border border-gray-800 hover:border-indigo-500/30 p-2.5 rounded-lg text-gray-400 hover:text-gray-200 transition-all flex flex-col items-center gap-1"
                          disabled={!res.diff_image_path}
                        >
                          <ImageIcon size={14} className="text-rose-400" />
                          <span className="text-rose-400">Diff Map</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Baseline screenshot references */}
            {!testResult && (
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 space-y-6">
                <h3 className="font-bold text-base text-white">🖼️ Established Baseline Viewports</h3>
                <div className="grid grid-cols-3 gap-6">
                  {activeBaseline.screenshots?.map((scr) => (
                    <div key={scr.id} className="bg-gray-950 border border-gray-800/80 rounded-xl overflow-hidden group">
                      <div className="p-4 border-b border-gray-800 flex items-center justify-between select-none">
                        <span className="text-xs font-bold text-gray-300 capitalize">{scr.viewport} frame</span>
                      </div>
                      <div className="relative aspect-video bg-gray-900 flex items-center justify-center cursor-zoom-in" onClick={() => setActiveModalImg(`${STATIC_URL}/${scr.image_path}`)}>
                        <img
                          src={`${STATIC_URL}/${scr.image_path}`}
                          alt={`${scr.viewport} baseline`}
                          className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-300"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center text-gray-500 select-none">
            <Eye size={48} className="mx-auto text-gray-700 mb-4" />
            <h4 className="font-bold text-gray-300 text-lg">No Active Baseline Selected</h4>
            <p className="text-sm text-gray-500 max-w-sm mx-auto mt-1 leading-relaxed">Establish or select an established visual baseline from the left-side bar list to run automated layout reviews.</p>
          </div>
        )}
      </div>

      {/* Screenshot Visual Lightbox Modal */}
      {activeModalImg && (
        <div
          onClick={() => setActiveModalImg(null)}
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex items-center justify-center p-12 animate-fadeIn cursor-zoom-out"
        >
          <div className="relative max-w-5xl max-h-[85vh] overflow-auto rounded-lg bg-gray-900 p-2 shadow-2xl border border-gray-800">
            <img
              src={activeModalImg}
              alt="Visual inspect zoom"
              className="max-w-full max-h-[80vh] object-contain rounded-md"
            />
          </div>
        </div>
      )}
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

export default RegressionModule
