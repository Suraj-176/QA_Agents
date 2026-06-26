import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Bug, Upload, RefreshCw, Send, CheckCircle, ExternalLink, Trash, Image as ImageIcon, HelpCircle } from 'lucide-react'

const API_BASE_URL = 'http://127.0.0.1:5000/api'
const STATIC_URL = 'http://127.0.0.1:5000/static'

function BugReporterModule() {
  const [reports, setReports] = useState([])
  const [activeReport, setActiveSuite] = useState(null)
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [exporting, setExporting] = useState(false)

  // Symmetrical dynamic guide states
  const [showGuide, setShowGuide] = useState(false)
  const [guideContent, setGuideContent] = useState('')

  // Upload state
  const [screenshotFile, setScreenshotFile] = useState(null)
  const [screenshotPreview, setScreenshotPreview] = useState(null)
  const [userRemarks, setUserRemarks] = useState('')

  useEffect(() => {
    fetchReports()
  }, [])

  const fetchReports = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_BASE_URL}/bug-reporter/reports`)
      setReports(response.data)
      if (response.data.length > 0 && !activeReport) {
        fetchReportDetails(response.data[0].id)
      }
    } catch (err) {
      console.error('Failed to load visual audits:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchReportDetails = async (reportId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/bug-reporter/reports/${reportId}`)
      setActiveSuite(response.data)
    } catch (err) {
      console.error('Failed to load report details:', err)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file && file.type.startsWith('image/')) {
      setScreenshotFile(file)
      setScreenshotPreview(URL.createObjectURL(file))
    } else {
      alert('Please upload a valid screenshot image file.')
    }
  }

  const handleAnalyze = async (e) => {
    e.preventDefault()
    if (!screenshotFile && !userRemarks.trim()) return

    // Extract isolated LLM credentials dynamically from localStorage matching Settings schema!
    const provider = localStorage.getItem('llm_provider') || 'gemini'
    const apiKey = localStorage.getItem(`llm_${provider}_api_key`) || ''
    const model = localStorage.getItem(`llm_${provider}_model`) || ''

    if (!apiKey || !apiKey.trim()) {
      alert('Missing LLM API Key. Please navigate to the Configuration Panel to configure your keys first.')
      return
    }

    setAnalyzing(true)
    const formData = new FormData()
    if (screenshotFile) {
      formData.append('file', screenshotFile)
    }
    formData.append('description', userRemarks)

    try {
      const response = await axios.post(
        `${API_BASE_URL}/bug-reporter/analyze`,
        formData,
        {
          headers: {
            'X-LLM-Provider': provider,
            'X-LLM-Model': model,
            'X-LLM-API-Key': apiKey
          }
        }
      )

      setScreenshotFile(null)
      setScreenshotPreview(null)
      setUserRemarks('')
      await fetchReports()
      if (response.data.bug_id) {
        await fetchReportDetails(response.data.bug_id)
      }
    } catch (err) {
      alert(`Audit failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleExportToTracker = async () => {
    if (!activeReport) return

    const target = localStorage.getItem('bug_export_target') || 'jira'
    let credentials = {}

    // Parse credentials dynamically based on active target platform
    if (target === 'jira') {
      const domain = localStorage.getItem('jira_domain')
      const email = localStorage.getItem('jira_email')
      const token = localStorage.getItem('jira_token')
      const project = localStorage.getItem('jira_project')

      if (!domain || !email || !token || !project) {
        alert('Atlassian JIRA integration credentials are incomplete. Please configure them in your Configuration Panel first.')
        return
      }
      credentials = {
        jira_domain: domain,
        jira_email: email,
        jira_token: token,
        jira_project: project
      }
    } else if (target === 'azure_devops') {
      const org = localStorage.getItem('ado_org')
      const proj = localStorage.getItem('ado_proj')
      const pat = localStorage.getItem('ado_pat')

      if (!org || !proj || !pat) {
        alert('Azure DevOps Boards credentials are incomplete. Please configure them in your Configuration Panel first.')
        return
      }
      credentials = {
        organization: org,
        project: proj,
        personal_access_token: pat
      }
    } else if (target === 'github') {
      const owner = localStorage.getItem('github_owner')
      const repo = localStorage.getItem('github_repo')
      const pat = localStorage.getItem('github_pat')

      if (!owner || !repo || !pat) {
        alert('GitHub repository credentials are incomplete. Please configure them in your Configuration Panel first.')
        return
      }
      credentials = {
        owner: owner,
        repo: repo,
        personal_access_token: pat
      }
    } else if (target === 'gitlab') {
      const projId = localStorage.getItem('gitlab_project_id')
      const pat = localStorage.getItem('gitlab_pat')

      if (!projId || !pat) {
        alert('GitLab project credentials are incomplete. Please configure them in your Configuration Panel first.')
        return
      }
      credentials = {
        project_id: projId,
        personal_access_token: pat
      }
    }

    setExporting(true)
    try {
      await axios.post(`${API_BASE_URL}/bug-reporter/export/${activeReport.id}`, {
        target: target,
        credentials: credentials
      })
      await fetchReportDetails(activeReport.id)
    } catch (err) {
      alert(`Publication failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setExporting(false)
    }
  }

  const handleDeleteReport = async (reportId) => {
    if (!confirm('Are you sure you want to permanently delete this bug audit report?')) return
    try {
      await axios.delete(`${API_BASE_URL}/bug-reporter/reports/${reportId}`)
      setActiveSuite(null)
      await fetchReports()
    } catch (err) {
      alert('Delete failed.')
    }
  }

  // Symmetrical dynamic guide handler
  const handleOpenGuide = async () => {
    setShowGuide(true)
    setGuideContent('Loading step-by-step user guide from disk...')
    try {
      const response = await axios.get(`${STATIC_URL}/guides/BugReporterGuide.md`)
      setGuideContent(response.data)
    } catch (err) {
      setGuideContent('### ❌ Failed to load guide file from static storage on server disk. Please check your folder structure.')
    }
  }

  return (
    <div className="grid grid-cols-12 gap-8 animate-fadeIn">
      {/* Sidebar: Bug reports list */}
      <div className="col-span-4 bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl p-6 h-fit space-y-6">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-gray-800 pb-4">
          <h3 className="font-bold text-slate-800 dark:text-white text-base flex items-center gap-2">
            <Bug size={18} className="text-indigo-400" />
            <span>Visual Bug Audits</span>
          </h3>
        </div>

        {/* Upload Screenshot Form */}
        <form onSubmit={handleAnalyze} className="space-y-4 bg-slate-50 dark:bg-gray-950 p-4 border border-slate-200 dark:border-gray-800/60 rounded-xl">
          <div className="flex items-center justify-between border-b border-slate-200/60 dark:border-gray-800/60 pb-2 mb-2">
            <p className="text-xs font-bold uppercase tracking-wider text-indigo-400">File New Bug Report</p>
            {/* Guide Button */}
            <button
              type="button"
              onClick={handleOpenGuide}
              className="text-slate-400 hover:text-indigo-500 transition-colors flex items-center gap-1 text-[10px] font-bold"
              title="Open non-technical step-by-step User Guide for this Agent"
            >
              <HelpCircle size={14} />
              <span>User Guide</span>
            </button>
          </div>
          
          <div className="border border-dashed border-slate-200 dark:border-gray-800 rounded-xl aspect-video relative flex flex-col items-center justify-center overflow-hidden hover:border-indigo-500/40 transition-colors bg-slate-50/50 dark:bg-gray-900/50">
            {screenshotPreview ? (
              <div className="relative w-full h-full group select-none">
                <img src={screenshotPreview} alt="Screenshot preview" className="w-full h-full object-cover" />
                <button
                  type="button"
                  onClick={() => {
                    setScreenshotFile(null)
                    setScreenshotPreview(null)
                  }}
                  className="absolute top-2 right-2 bg-red-600 hover:bg-red-500 text-white rounded-lg px-3 py-1.5 text-[10px] font-bold transition-all shadow-md opacity-0 group-hover:opacity-100"
                >
                  Clear Screen
                </button>
              </div>
            ) : (
              <label className="cursor-pointer flex flex-col items-center justify-center p-6 text-center space-y-2 h-full w-full select-none">
                <Upload className="text-slate-400 dark:text-gray-500" size={24} />
                <span className="text-xs font-semibold text-slate-600 dark:text-gray-300">Drag or Upload Screenshot</span>
                <span className="text-[10px] text-slate-400 dark:text-gray-500">Optional | Supports PNG, JPG (Max 5MB)</span>
                <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
              </label>
            )}
          </div>

          <div className="space-y-1">
            <textarea
              placeholder="Enter bug description or context (mandatory if no screenshot is uploaded)..."
              value={userRemarks}
              onChange={(e) => setUserRemarks(e.target.value)}
              rows={3}
              className="w-full bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 shadow-sm transition-all/80 rounded-lg p-3 text-xs text-slate-700 dark:text-gray-200 focus:outline-none focus:border-indigo-500 placeholder:text-gray-600 resize-none leading-relaxed"
              disabled={analyzing}
            />
          </div>
          <button
            type="submit"
            disabled={analyzing || (!screenshotFile && !userRemarks.trim())}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold py-2.5 rounded-lg flex items-center justify-center gap-1.5 active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none animate-pulse-subtle"
          >
            {analyzing ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                <span>Auditing Layout...</span>
              </>
            ) : (
              <>
                <Send size={14} />
                <span>Audit and Draft Bug</span>
              </>
            )}
          </button>
        </form>

        {/* Reports listing */}
        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
          {reports.length === 0 ? (
            <p className="text-xs text-slate-400 dark:text-gray-500 text-center py-4">No bug reports compiled yet.</p>
          ) : (
            reports.map((r) => (
              <button
                key={r.id}
                onClick={() => fetchReportDetails(r.id)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-center justify-between ${
                  activeReport?.id === r.id
                    ? 'bg-indigo-600/10 border-indigo-500/20 text-indigo-300 font-semibold'
                    : 'bg-slate-50 dark:bg-gray-950/40 border-slate-200 dark:border-gray-800/40 text-slate-500 dark:text-gray-400 hover:border-slate-200 dark:border-gray-800 hover:text-slate-700 dark:text-gray-200'
                }`}
              >
                <div className="truncate pr-4">
                  <p className="text-sm truncate">{r.title}</p>
                  <p className="text-xs text-slate-400 dark:text-gray-500 truncate mt-0.5">{r.severity} Severity</p>
                </div>
                <ChevronRightActive active={activeReport?.id === r.id} />
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Panel: Report details viewer */}
      <div className="col-span-8">
        {activeReport ? (
          <div className={`grid ${activeReport.screenshot_path ? 'grid-cols-2' : 'grid-cols-1'} gap-8 animate-fadeIn`}>
            {/* Visual Screenshot Display (Conditionally rendered only if a screenshot was uploaded) */}
            {activeReport.screenshot_path && (
              <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl overflow-hidden shadow-sm h-fit">
                <div className="p-4 border-b border-slate-200 dark:border-gray-800 flex items-center justify-between bg-slate-50/50 dark:bg-gray-900/50 select-none">
                  <span className="text-xs font-bold text-slate-600 dark:text-gray-300 flex items-center gap-1.5">
                    <ImageIcon size={14} className="text-indigo-400" />
                    <span>Audited Screenshot</span>
                  </span>
                </div>
                <div className="bg-black/20 flex items-center justify-center p-4">
                  <img
                    src={`${STATIC_URL}/${activeReport.screenshot_path}`}
                    alt="Visual audit reference"
                    className="max-h-[360px] w-full object-contain rounded-lg border border-slate-200 dark:border-gray-800"
                  />
                </div>
              </div>
            )}

            {/* AI Vision analysis details and Export */}
            <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl p-8 space-y-6 h-fit">
              <div className="border-b border-slate-200 dark:border-gray-800 pb-5 flex items-center justify-between select-none">
                <div>
                  <h3 className="font-bold text-lg text-white pr-4">{activeReport.title}</h3>
                  <div className="flex gap-2.5 mt-2">
                    <span className={`text-[10px] uppercase tracking-wider font-extrabold px-2.5 py-0.5 border rounded-full ${
                      activeReport.severity === 'Critical' || activeReport.severity === 'High'
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                    }`}>
                      {activeReport.severity}
                    </span>
                    <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 dark:text-gray-500 bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 px-2.5 py-0.5 rounded-full">
                      {activeReport.status.replace(/submitted_to_/g, '').replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteReport(activeReport.id)}
                  className="bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 p-2.5 rounded-xl transition-all active:scale-[0.96] shrink-0"
                >
                  <Trash size={16} />
                </button>
              </div>

              {/* Universal Connected Exporter section */}
              <div className="space-y-4">
                {activeReport.status !== 'draft' ? (
                  <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-xl space-y-3">
                    <p className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5 select-none">
                      <CheckCircle size={14} />
                      <span>Successfully Published Bug</span>
                    </p>
                    <p className="text-xs text-emerald-300/80 leading-relaxed">
                      This bug audit has been successfully posted as an issue ticket to your configured tracker. 
                      You can trace or modify it directly in your workspace browser.
                    </p>
                    <a
                      href={activeReport.jira_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-4 py-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all select-none w-full shadow-lg shadow-emerald-500/5"
                    >
                      <span>View Ticket {activeReport.jira_key}</span>
                      <ExternalLink size={12} />
                    </a>
                  </div>
                ) : (
                  <div className="p-4 bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800/80 rounded-xl space-y-3">
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-gray-400 select-none">Bug Tracker Exporter</p>
                    <p className="text-xs text-slate-400 dark:text-gray-500 leading-relaxed">
                      Publish this bug report directly to your active connected issue tracking board. 
                      {activeReport.screenshot_path ? " The visual screenshot attachment will automatically be uploaded if supported." : " No attachment will be sent since this is a text-only bug."}
                    </p>
                    <button
                      onClick={handleExportToTracker}
                      disabled={exporting}
                      className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-4 py-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all w-full active:scale-[0.98] shadow-lg shadow-indigo-500/5"
                    >
                      {exporting ? (
                        <>
                          <RefreshCw size={12} className="animate-spin" />
                          <span>Publishing Bug...</span>
                        </>
                      ) : (
                        <>
                          <Send size={12} />
                          <span>Publish to Connected Tracker</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>

              {/* Description visual audit output */}
              <div className="space-y-4 bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800/80 p-5 rounded-xl max-h-[250px] overflow-y-auto">
                <p className="text-xs font-bold uppercase tracking-wider text-indigo-400 border-b border-slate-200 dark:border-gray-800/60 pb-2 select-none">Layout Audit Log</p>
                <p className="text-xs text-slate-600 dark:text-gray-300 leading-relaxed font-mono whitespace-pre-line">{activeReport.description.replace(/h3\. /g, '\n\n**').replace(/\n\n\*\*/, '**')}</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl p-12 text-center text-slate-400 dark:text-gray-500 select-none">
            <Bug size={48} className="mx-auto text-gray-700 mb-4" />
            <h4 className="font-bold text-slate-600 dark:text-gray-300 text-lg">No Active Bug Selected</h4>
            <p className="text-sm text-slate-400 dark:text-gray-500 max-w-sm mx-auto mt-1 leading-relaxed">Upload a UI layout screenshot or type in a text-only bug description on the sidebar to audit and draft bug details.</p>
          </div>
        )}
      </div>

      {/* Symmetrical dynamic User Guide Lightbox Modal */}
      {showGuide && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6 animate-fadeIn">
          <div className="relative w-full max-w-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-2xl shadow-2xl p-8 max-h-[85vh] overflow-y-auto space-y-6">
            <div className="border-b border-slate-200 dark:border-gray-800 pb-4 flex items-center justify-between">
              <h3 className="font-bold text-lg text-slate-800 dark:text-white flex items-center gap-2">
                <HelpCircle className="text-indigo-500 animate-pulse" size={20} />
                <span>AI Visual Bug Reporter Agent Guide</span>
              </h3>
              <button 
                onClick={() => setShowGuide(false)}
                className="text-slate-400 dark:text-gray-500 hover:text-slate-600 dark:hover:text-gray-300 text-xs font-bold px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-gray-800 transition-colors"
              >
                Close Guide
              </button>
            </div>
            
            {/* Scrollable, non-hardcoded markdown text viewport */}
            <div className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-850 p-6 rounded-xl font-sans text-xs text-slate-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap select-text h-[400px] overflow-y-auto shadow-inner">
              {guideContent}
            </div>
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

export default BugReporterModule
