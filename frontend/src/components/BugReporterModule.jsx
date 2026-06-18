import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Bug, Upload, RefreshCw, Send, AlertCircle, CheckCircle, ExternalLink, Trash, Image as ImageIcon } from 'lucide-react'

const API_BASE_URL = 'http://127.0.0.1:5000/api'
const STATIC_URL = 'http://127.0.0.1:5000/static'

function BugReporterModule() {
  const [reports, setReports] = useState([])
  const [activeReport, setActiveSuite] = useState(null)
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [exporting, setExporting] = useState(false)

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
    if (!screenshotFile) return

    // Extract LLM credentials from localStorage
    const provider = localStorage.getItem('llm_provider') || 'gemini'
    const model = localStorage.getItem('llm_model') || 'gemini-1.5-flash'
    const apiKey = localStorage.getItem('llm_api_key')

    if (!apiKey) {
      alert('Missing LLM API Key. Please navigate to the Configuration Panel to configure your keys first.')
      return
    }

    setAnalyzing(true)
    const formData = new FormData()
    formData.append('file', screenshotFile)
    formData.append('description', userRemarks)

    try {
      const response = await axios.post(
        `${API_BASE_URL}/bug-reporter/analyze`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
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

  const handleExportToJira = async () => {
    if (!activeReport) return

    // Extract Jira credentials from localStorage
    const domain = localStorage.getItem('jira_domain')
    const email = localStorage.getItem('jira_email')
    const token = localStorage.getItem('jira_token')
    const project = localStorage.getItem('jira_project')

    if (!domain || !email || !token || !project) {
      alert('JIRA integration details are missing. Please configure them in your Configuration Panel first.')
      return
    }

    setExporting(true)
    try {
      await axios.post(`${API_BASE_URL}/bug-reporter/export/${activeReport.id}`, {
        jira_domain: domain,
        jira_email: email,
        jira_token: token,
        jira_project: project
      })
      await fetchReportDetails(activeReport.id)
    } catch (err) {
      alert(`JIRA filing failed: ${err.response?.data?.detail || err.message}`)
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

  return (
    <div className="grid grid-cols-12 gap-8 animate-fadeIn">
      {/* Sidebar: Bug reports list */}
      <div className="col-span-4 bg-gray-900 border border-gray-800 rounded-2xl p-6 h-fit space-y-6">
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <Bug size={18} className="text-indigo-400" />
            <span>Visual Bug Audits</span>
          </h3>
        </div>

        {/* Upload Screenshot Form */}
        <form onSubmit={handleAnalyze} className="space-y-4 bg-gray-950 p-4 border border-gray-800/60 rounded-xl">
          <p className="text-xs font-bold uppercase tracking-wider text-indigo-400">File New Visual Bug</p>
          
          <div className="border border-dashed border-gray-800 rounded-xl aspect-video relative flex flex-col items-center justify-center overflow-hidden hover:border-indigo-500/40 transition-colors bg-gray-900/50">
            {screenshotPreview ? (
              <img src={screenshotPreview} alt="Screenshot preview" className="w-full h-full object-cover" />
            ) : (
              <label className="cursor-pointer flex flex-col items-center justify-center p-6 text-center space-y-2 h-full w-full select-none">
                <Upload className="text-gray-500" size={24} />
                <span className="text-xs font-semibold text-gray-300">Drag or Upload Screenshot</span>
                <span className="text-[10px] text-gray-500">Supports PNG, JPG (Max 5MB)</span>
                <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" required />
              </label>
            )}
          </div>

          <div className="space-y-1">
            <textarea
              placeholder="Enter optional remarks or manual context..."
              value={userRemarks}
              onChange={(e) => setUserRemarks(e.target.value)}
              rows={3}
              className="w-full bg-gray-900 border border-gray-800/80 rounded-lg p-3 text-xs text-gray-200 focus:outline-none focus:border-indigo-500 placeholder:text-gray-600 resize-none leading-relaxed"
              disabled={analyzing}
            />
          </div>
          <button
            type="submit"
            disabled={analyzing || !screenshotFile}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold py-2.5 rounded-lg flex items-center justify-center gap-1.5 active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none"
          >
            {analyzing ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                <span>Auditing Layout...</span>
              </>
            ) : (
              <>
                <Send size={14} />
                <span>Audit Screenshot</span>
              </>
            )}
          </button>
        </form>

        {/* Reports listing */}
        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
          {reports.length === 0 ? (
            <p className="text-xs text-gray-500 text-center py-4">No bug reports compiled yet.</p>
          ) : (
            reports.map((r) => (
              <button
                key={r.id}
                onClick={() => fetchReportDetails(r.id)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-center justify-between ${
                  activeReport?.id === r.id
                    ? 'bg-indigo-600/10 border-indigo-500/20 text-indigo-300 font-semibold'
                    : 'bg-gray-950/40 border-gray-800/40 text-gray-400 hover:border-gray-800 hover:text-gray-200'
                }`}
              >
                <div className="truncate pr-4">
                  <p className="text-sm truncate">{r.title}</p>
                  <p className="text-xs text-gray-500 truncate mt-0.5">{r.severity} Severity</p>
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
          <div className="grid grid-cols-2 gap-8">
            {/* Visual Screenshot Display */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-sm h-fit">
              <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-gray-900/50 select-none">
                <span className="text-xs font-bold text-gray-300 flex items-center gap-1.5">
                  <ImageIcon size={14} className="text-indigo-400" />
                  <span>Audited Screenshot</span>
                </span>
              </div>
              <div className="bg-black/20 flex items-center justify-center p-4">
                <img
                  src={`${STATIC_URL}/${activeReport.screenshot_path}`}
                  alt="Visual audit reference"
                  className="max-h-[360px] w-full object-contain rounded-lg border border-gray-800"
                />
              </div>
            </div>

            {/* AI Vision analysis details and Export */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 space-y-6 h-fit">
              <div className="border-b border-gray-800 pb-5 flex items-center justify-between select-none">
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
                    <span className="text-[10px] uppercase tracking-wider font-semibold text-gray-500 bg-gray-950 border border-gray-800 px-2.5 py-0.5 rounded-full">
                      {activeReport.status.replace('_', ' ')}
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

              {/* JIRA Publishing section */}
              <div className="space-y-4">
                {activeReport.status === 'submitted_to_jira' ? (
                  <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-xl space-y-3">
                    <p className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle size={14} />
                      <span>Successfully Posted to JIRA</span>
                    </p>
                    <p className="text-xs text-emerald-300/80 leading-relaxed">
                      This visual bug has been created as an issue ticket in Atlassian JIRA. 
                      You can trace or modify it directly in your workspace browser.
                    </p>
                    <a
                      href={activeReport.jira_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-4 py-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all select-none w-full"
                    >
                      <span>View Ticket {activeReport.jira_key}</span>
                      <ExternalLink size={12} />
                    </a>
                  </div>
                ) : (
                  <div className="p-4 bg-gray-950 border border-gray-800/80 rounded-xl space-y-3">
                    <p className="text-xs font-bold uppercase tracking-wider text-gray-400">Jira Publishing</p>
                    <p className="text-xs text-gray-500 leading-relaxed">
                      Publish this structural layout audit as a Bug Ticket in your company JIRA Cloud project. 
                      The audited layout screenshot will automatically be uploaded as an attachment.
                    </p>
                    <button
                      onClick={handleExportToJira}
                      disabled={exporting}
                      className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-4 py-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all w-full active:scale-[0.98]"
                    >
                      {exporting ? (
                        <>
                          <RefreshCw size={12} className="animate-spin" />
                          <span>Publishing Issue...</span>
                        </>
                      ) : (
                        <>
                          <Send size={12} />
                          <span>Publish to JIRA Cloud</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>

              {/* Description visual audit output */}
              <div className="space-y-4 bg-gray-950 border border-gray-800/80 p-5 rounded-xl max-h-[250px] overflow-y-auto">
                <p className="text-xs font-bold uppercase tracking-wider text-indigo-400 border-b border-gray-800/60 pb-2">Layout Audit Log</p>
                <p className="text-xs text-gray-300 leading-relaxed font-mono whitespace-pre-line">{activeReport.description.replace(/h3\. /g, '\n\n**').replace(/\n\n\*\*/, '**')}</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center text-gray-500 select-none">
            <Bug size={48} className="mx-auto text-gray-700 mb-4" />
            <h4 className="font-bold text-gray-300 text-lg">No Active Bug Selected</h4>
            <p className="text-sm text-gray-500 max-w-sm mx-auto mt-1 leading-relaxed">Upload a UI layout screenshot or choose an active bug audit from the sidebar to inspect visual details.</p>
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

export default BugReporterModule
