import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Code2, Settings, Plus, Play, Download, FolderOpen, Save, RefreshCw, FileCode, CheckCircle, AlertCircle, Loader } from 'lucide-react'

const API_BASE_URL = 'http://127.0.0.1:5000/api'
const STATIC_URL = 'http://127.0.0.1:5000/static'

function AutomationModule() {
  const [activeSubTab, setActiveSubTab] = useState('bootstrap') // 'bootstrap' or 'extend'
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressMsg, setProgressMessage] = useState('')

  // Sub-Tab 1: Bootstrap Form states
  const [bootTool, setBootTool] = useState('Playwright')
  const [bootLang, setBootLang] = useState('TypeScript')
  const [bootPattern, setBootPattern] = useState('BDD (Cucumber / Gherkin)')
  const [bootFolder, setBootFolder] = useState('C:\\QAAgents\\my_new_framework')
  const [bootResult, setBootResult] = useState(null)

  // Sub-Tab 2: Extend Form states
  const [extendFolder, setExtendFolder] = useState('C:\\QAAgents\\my_new_framework')
  const [instruction, setInstruction] = useState('')
  const [genResult, setGenResult] = useState(null)
  const [selectedFileIdx, setSelectedExtFileIndex] = useState(0) // Added for multi-file extensions!
  const [writeResult, setWriteResult] = useState(null)

  // Get transient headers loaded dynamically matching Settings schema
  const getHeaders = () => {
    const provider = localStorage.getItem('llm_provider') || 'gemini'
    const model = localStorage.getItem(`llm_${provider}_model`) || ''
    const apiKey = localStorage.getItem(`llm_${provider}_api_key`) || ''
    
    return {
      'X-LLM-Provider': provider,
      'X-LLM-Model': model,
      'X-LLM-API-Key': apiKey
    }
  }

  // Launches native host folder selector on click and returns path
  const handleBrowseFolder = async (setPath) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/automation/browse-folder`)
      if (response.data.folder_path) {
        setPath(response.data.folder_path)
      }
    } catch (err) {
      console.error('Folder browsing failed:', err)
    }
  }

  // Smart Step-by-Step Progress Simulator for long LLM generations
  const startProgressSimulator = () => {
    setProgress(0)
    setProgressMessage('Initializing dynamic SDET model context...')
    
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 98) {
          clearInterval(interval)
          return 98
        }
        
        const nextVal = prev + Math.floor(Math.random() * 8) + 1
        const clampedVal = nextVal > 98 ? 98 : nextVal
        
        // Update semantic progress messages based on percentage ranges
        if (clampedVal < 15) {
          setProgressMessage('Initializing dynamic SDET model context...')
        } else if (clampedVal >= 15 && clampedVal < 40) {
          setProgressMessage('Formulating strict zero-laziness prompt boundaries...')
        } else if (clampedVal >= 40 && clampedVal < 75) {
          setProgressMessage('Calling Google Gemini AI for multi-file code generation (takes ~20 seconds)...')
        } else if (clampedVal >= 75 && clampedVal < 90) {
          setProgressMessage('Assembling folder trees and packaging files into ZIP archive...')
        } else {
          setProgressMessage('Polishing script structures and purging scratch spaces...')
        }
        
        return clampedVal
      })
    }, 800)
    
    return interval
  }

  const handleBootstrap = async (e) => {
    e.preventDefault()
    setLoading(true)
    setBootResult(null)
    const intervalId = startProgressSimulator()

    try {
      const response = await axios.post(
        `${API_BASE_URL}/automation/bootstrap`,
        {
          tool: bootTool,
          language: bootLang,
          pattern: bootPattern,
          output_folder: bootFolder || null // Send null if empty to trigger server scratch ZIP
        },
        {
          headers: getHeaders()
        }
      )
      
      clearInterval(intervalId)
      setProgress(100)
      setProgressMessage('Framework successfully created! Done.')
      setBootResult(response.data)
    } catch (err) {
      clearInterval(intervalId)
      alert(`Bootstrapping failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateFile = async (e) => {
    e.preventDefault()
    if (!extendFolder || !instruction) return
    setLoading(true)
    setGenResult(null)
    setWriteResult(null)
    const intervalId = startProgressSimulator()

    try {
      const response = await axios.post(
        `${API_BASE_URL}/automation/generate`,
        {
          folder_path: extendFolder,
          instruction: instruction
        },
        {
          headers: getHeaders()
        }
      )
      clearInterval(intervalId)
      setProgress(100)
      setProgressMessage('File code compiled successfully!')
      setSelectedExtFileIndex(0) // Reset to first file index cleanly on fresh generations!
      setGenResult(response.data)
    } catch (err) {
      clearInterval(intervalId)
      alert(`Generation failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleWriteFile = async () => {
    if (!genResult || !extendFolder) return
    const activeFile = genResult.files[selectedFileIdx]
    if (!activeFile) return
    
    setLoading(true)
    setWriteResult(null)

    try {
      const response = await axios.post(`${API_BASE_URL}/automation/write`, {
        folder_path: extendFolder,
        relative_path: activeFile.path,
        code: activeFile.content
      })
      setWriteResult(response.data)
    } catch (err) {
      alert(`Writing file failed: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8 animate-fadeIn select-none text-slate-800 dark:text-white">
      {/* Sub-Tab Selector Header */}
      <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 rounded-2xl p-2 flex gap-2 w-fit shadow-sm transition-all">
        <button
          onClick={() => {
            setActiveSubTab('bootstrap')
            setWriteResult(null)
          }}
          className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all ${
            activeSubTab === 'bootstrap'
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/10'
              : 'text-slate-500 hover:text-slate-700 dark:text-slate-500 dark:text-gray-400 dark:hover:text-slate-700 dark:text-gray-200'
          }`}
        >
          🚀 Bootstrap New Framework
        </button>
        <button
          onClick={() => {
            setActiveSubTab('extend')
            setBootResult(null)
          }}
          className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all ${
            activeSubTab === 'extend'
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/10'
              : 'text-slate-500 hover:text-slate-700 dark:text-slate-500 dark:text-gray-400 dark:hover:text-slate-700 dark:text-gray-200'
          }`}
        >
          🔧 Extend Existing Framework
        </button>
      </div>

      {/* Main Mode 1: Bootstrap Framework */}
      {activeSubTab === 'bootstrap' && (
        <div className="grid grid-cols-12 gap-8">
          {/* Form left */}
          <div className="col-span-5 bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-2xl p-6 h-fit space-y-6 shadow-sm transition-all">
            <div className="border-b border-slate-200 dark:border-gray-800 pb-3">
              <h3 className="font-bold text-slate-800 dark:text-white text-base">🏗️ Configure Scaffolder</h3>
              <p className="text-[10px] text-slate-500 dark:text-gray-450 mt-1 leading-normal">
                Choose your environment. Provide a local directory path to scaffold on disk, or leave it blank to download as a structured ZIP!
              </p>
            </div>

            <form onSubmit={handleBootstrap} className="space-y-5">
              {/* Tool selector */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Automation Tool</label>
                <select
                  value={bootTool}
                  onChange={(e) => setBootTool(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3 text-xs text-slate-850 dark:text-gray-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
                  disabled={loading}
                >
                  <option value="Playwright" className="bg-white dark:bg-slate-50 dark:bg-gray-950">Playwright (Modern, Fast)</option>
                  <option value="Selenium" className="bg-white dark:bg-slate-50 dark:bg-gray-950">Selenium WebDriver (Classic, Enterprise)</option>
                  <option value="Cypress" className="bg-white dark:bg-slate-50 dark:bg-gray-950">Cypress (Modern, Frontend)</option>
                </select>
              </div>

              {/* Language selector */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Target Language</label>
                <select
                  value={bootLang}
                  onChange={(e) => setBootLang(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3 text-xs text-slate-850 dark:text-gray-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
                  disabled={loading}
                >
                  <option value="TypeScript" className="bg-white dark:bg-gray-950">TypeScript (Recommended)</option>
                  <option value="JavaScript" className="bg-white dark:bg-gray-950">JavaScript</option>
                  <option value="Python" className="bg-white dark:bg-gray-950">Python</option>
                  <option value="Java" className="bg-white dark:bg-gray-950">Java</option>
                </select>
              </div>

              {/* Pattern selector */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Architecture Pattern</label>
                <select
                  value={bootPattern}
                  onChange={(e) => setBootPattern(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3 text-xs text-slate-850 dark:text-gray-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
                  disabled={loading}
                >
                  <option value="BDD (Cucumber / Gherkin)" className="bg-white dark:bg-gray-950">BDD (Cucumber / Gherkin Syntax)</option>
                  <option value="Data-Driven (CSV/JSON Inputs)" className="bg-white dark:bg-gray-950">Data-Driven (Dynamic CSV/JSON Data Loops)</option>
                  <option value="API-First Hybrid Testing" className="bg-white dark:bg-gray-950">API-First Hybrid Testing (Bypasses UI via API Seeding)</option>
                  <option value="Keyword-Driven Testing" className="bg-white dark:bg-gray-950">Keyword-Driven Testing (Semantic Action Keywords)</option>
                </select>
              </div>

              {/* DUAL-MODE Optional Folder path input with Graphical Browse Folder Button */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Local Scaffold Directory (Optional)</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={bootFolder}
                    onChange={(e) => setBootFolder(e.target.value)}
                    placeholder="Optional. Leave blank for pure ZIP downloads!"
                    className="flex-1 bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3 text-xs text-slate-850 dark:text-gray-200 placeholder-slate-400 dark:placeholder-gray-500 font-mono focus:outline-none focus:border-indigo-500"
                    disabled={loading}
                  />
                  <button
                    type="button"
                    onClick={() => handleBrowseFolder(setBootFolder)}
                    className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 hover:border-slate-300 dark:hover:border-gray-700 text-slate-500 dark:text-gray-400 hover:text-slate-700 dark:hover:text-gray-200 px-3.5 rounded-xl transition-all active:scale-[0.95]"
                    disabled={loading}
                    title="Select a directory graphically using Windows Folder Explorer Dialog"
                  >
                    <FolderOpen size={16} />
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs py-3 rounded-xl flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-50"
              >
                {loading ? <Loader size={14} className="animate-spin" /> : <Plus size={14} />}
                <span>{loading ? 'Bootstrapping Framework...' : 'Generate & Scaffold Framework'}</span>
              </button>
            </form>
          </div>

          {/* Results / Progress meter right */}
          <div className="col-span-7 space-y-6">
            {loading ? (
              /* Gorgeous step-by-step loading meter card */
              <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 rounded-2xl p-10 flex flex-col justify-center items-center h-full min-h-[400px] animate-fadeIn space-y-6 shadow-sm transition-all">
                <div className="relative w-24 h-24 flex items-center justify-center">
                  <div className="absolute inset-0 border-4 border-indigo-500/10 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-t-indigo-500 rounded-full animate-spin"></div>
                  <span className="font-extrabold text-slate-850 dark:text-slate-800 dark:text-white text-lg font-mono">{progress}%</span>
                </div>
                
                <div className="text-center space-y-2 max-w-sm">
                  <h4 className="font-bold text-indigo-600 dark:text-indigo-400 text-sm uppercase tracking-wider animate-pulse">Executing SDET Agent</h4>
                  <p className="text-xs text-slate-600 dark:text-slate-600 dark:text-gray-300 font-medium leading-relaxed font-mono h-12 flex items-center justify-center">{progressMsg}</p>
                </div>

                {/* Simulated visual progress bar */}
                <div className="w-full bg-slate-100 dark:bg-slate-50 dark:bg-gray-950 h-2.5 rounded-full overflow-hidden border border-slate-200 dark:border-slate-200 dark:border-gray-850 max-w-md">
                  <div 
                    className="bg-indigo-500 h-full rounded-full transition-all duration-300 shadow-lg shadow-indigo-500/50"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>
            ) : bootResult ? (
              <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 rounded-2xl p-8 space-y-6 animate-fadeIn shadow-sm transition-all">
                <div className="border-b border-slate-200 dark:border-slate-200 dark:border-gray-800 pb-4 flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-slate-800 dark:text-slate-800 dark:text-white text-lg flex items-center gap-2">
                      <CheckCircle className="text-emerald-500" size={20} />
                      <span>Framework Scaffolded Successfully!</span>
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-gray-450 mt-1 font-semibold">
                      Pattern Selected: <span className="text-indigo-600 dark:text-indigo-400 font-bold font-mono">{bootPattern}</span>
                    </p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-500 dark:text-gray-400 mt-1">Directory: <code className="bg-slate-50 dark:bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-slate-200 dark:border-gray-850 px-1.5 py-0.5 rounded font-bold text-indigo-600 dark:text-indigo-400 font-mono text-[10px]">{bootResult.output_folder}</code></p>
                  </div>
                  
                  {/* Download ZIP link */}
                  <a
                    href={`${STATIC_URL}/${bootResult.zip_url}`}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-5 py-3 rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-emerald-500/20 active:scale-[0.96]"
                    title="Download complete framework as .zip archive"
                  >
                    <Download size={14} />
                    <span>Download Framework ZIP</span>
                  </a>
                </div>

                {/* Scaffolder Info banner */}
                <div className="p-4 bg-indigo-500/5 border border-indigo-500/10 text-indigo-600 dark:text-indigo-300 rounded-xl flex items-start gap-3">
                  <CheckCircle className="text-indigo-500 dark:text-indigo-400 mt-0.5 shrink-0" size={16} />
                  <div>
                    <h4 className="font-bold text-xs leading-none">Scaffolding Completed Successfully! ✅</h4>
                    <p className="text-[11px] mt-1.5 text-slate-500 dark:text-slate-500 dark:text-gray-400 leading-relaxed">
                      All files for <span className="text-slate-800 dark:text-white font-bold">{bootTool} + {bootLang} ({bootPattern})</span> have been compiled in memory. Click the **Download Framework ZIP** button above to save and explore your complete corporate testing repository!
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-500 dark:text-gray-400">Scaffolded Files ({bootResult.files_count})</p>
                  <div className="bg-slate-50 dark:bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-slate-200 dark:border-gray-850 p-4 rounded-xl max-h-[220px] overflow-y-auto space-y-2 font-mono text-[11px] text-slate-600 dark:text-slate-500 dark:text-gray-400 shadow-inner">
                    {bootResult.files.map((file, idx) => (
                      <div key={idx} className="flex items-center gap-2 hover:text-slate-800 dark:hover:text-white transition-colors">
                        <FileCode size={12} className="text-indigo-500 dark:text-indigo-400 shrink-0" />
                        <span>{file}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 rounded-2xl p-12 text-center text-slate-400 dark:text-slate-400 dark:text-gray-500 h-full flex flex-col justify-center items-center min-h-[400px] shadow-sm transition-all">
                <Code2 size={48} className="text-slate-300 dark:text-gray-800 mb-4" />
                <h4 className="font-bold text-slate-700 dark:text-slate-600 dark:text-gray-300 text-base">No Bootstrapped Framework Yet</h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 dark:text-gray-500 max-w-sm mx-auto mt-1 leading-relaxed">Configure your target tool, language, and directory path on the left form panel, then click generate to bootstrap a production-ready repository.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Mode 2: Extend Framework */}
      {activeSubTab === 'extend' && (
        <div className="grid grid-cols-12 gap-8">
          {/* Instructions left */}
          <div className="col-span-5 bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl p-6 h-fit space-y-6">
            <h3 className="font-bold text-slate-800 dark:text-white text-base border-b border-slate-200 dark:border-gray-800 pb-3">🔧 Extend Local Repo</h3>
            
            <form onSubmit={handleGenerateFile} className="space-y-5">
              {/* Folder path input with Graphical Browse Folder Button */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Existing Framework Path</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={extendFolder}
                    onChange={(e) => setExtendFolder(e.target.value)}
                    placeholder="e.g. C:\QAAgents\my_new_framework"
                    className="flex-1 bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3 text-xs text-slate-700 dark:text-gray-200 font-mono focus:outline-none focus:border-indigo-500"
                    required
                    disabled={loading}
                  />
                  <button
                    type="button"
                    onClick={() => handleBrowseFolder(setExtendFolder)}
                    className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 hover:border-gray-700 text-slate-500 dark:text-gray-400 hover:text-slate-700 dark:text-gray-200 px-3.5 rounded-xl transition-all active:scale-[0.95]"
                    disabled={loading}
                    title="Select a directory graphically using Windows Folder Explorer Dialog"
                  >
                    <FolderOpen size={16} />
                  </button>
                </div>
              </div>

              {/* Instruction Prompt input */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Generation Instructions</label>
                <textarea
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  placeholder='e.g. "Create a ChatPage Page Object Model with locators for messageInput ("#msg-box") and sendBtn (".submit-button"). Include a sendMessage(msg) helper function."'
                  rows={6}
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3 text-xs text-slate-700 dark:text-gray-200 focus:outline-none focus:border-indigo-500 leading-relaxed resize-y"
                  required
                  disabled={loading}
                />
                <p className="text-[10px] text-slate-400 dark:text-gray-500 leading-normal">
                  * Playwright scans your local config files to auto-detect import structures, async patterns, and BasePage classes before generation!
                </p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs py-3 rounded-xl flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-50"
              >
                {loading ? <Loader size={14} className="animate-spin" /> : <Play size={14} />}
                <span>{loading ? 'Analyzing & Compiling...' : 'Generate New File Code'}</span>
              </button>
            </form>
          </div>

          {/* Code Preview right */}
          <div className="col-span-7 space-y-6">
            {loading ? (
              /* Gorgeous step-by-step loading meter card for extender */
              <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl p-10 flex flex-col justify-center items-center h-full min-h-[400px] animate-fadeIn space-y-6">
                <div className="relative w-24 h-24 flex items-center justify-center">
                  <div className="absolute inset-0 border-4 border-indigo-500/10 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-t-indigo-500 rounded-full animate-spin"></div>
                  <span className="font-extrabold text-slate-800 dark:text-white text-lg font-mono">{progress}%</span>
                </div>
                
                <div className="text-center space-y-2 max-w-sm">
                  <h4 className="font-bold text-slate-800 dark:text-white text-sm uppercase tracking-wider animate-pulse text-indigo-400">Analyzing Repo Context</h4>
                  <p className="text-xs text-slate-600 dark:text-gray-300 font-medium leading-relaxed font-mono h-12 flex items-center justify-center">{progressMsg}</p>
                </div>

                {/* Simulated visual progress bar */}
                <div className="w-full bg-slate-50 dark:bg-gray-950 h-2.5 rounded-full overflow-hidden border border-slate-200 dark:border-gray-850 max-w-md">
                  <div 
                    className="bg-indigo-500 h-full rounded-full transition-all duration-300 shadow-lg shadow-indigo-500/50"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>
            ) : genResult ? (
              <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl p-8 space-y-6 animate-fadeIn">
                
                {/* Multi-File dropdown selector shown if files count > 1 */}
                {genResult.files && genResult.files.length > 1 && (
                  <div className="space-y-2 border-b border-slate-200 dark:border-gray-850 pb-4 animate-fadeIn">
                    <label className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">📁 Select File to Preview</label>
                    <select
                      value={selectedFileIdx}
                      onChange={(e) => {
                        setSelectedExtFileIndex(parseInt(e.target.value, 10))
                        setWriteResult(null) // Reset saved confirm banner on file switch
                      }}
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-850 text-indigo-400 rounded-xl px-4 py-3 text-xs font-bold font-mono focus:outline-none focus:border-indigo-500 cursor-pointer"
                    >
                      {genResult.files.map((file, idx) => (
                        <option key={idx} value={idx}>
                          {idx + 1}. {file.path}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="border-b border-slate-200 dark:border-gray-800 pb-4 flex flex-wrap gap-4 items-center justify-between">
                  <div className="flex-1 min-w-[250px]">
                    <h3 className="font-bold text-slate-800 dark:text-white text-base flex items-center gap-2">
                      <FileCode className="text-indigo-400 animate-pulse" size={18} />
                      <span>Generated File Code Preview</span>
                    </h3>
                    
                    {/* Path editor */}
                    <div className="flex items-center gap-1.5 mt-2">
                      <span className="text-[10px] font-bold text-slate-400 dark:text-gray-500 uppercase shrink-0">Path:</span>
                      <input
                        type="text"
                        value={genResult.files && genResult.files[selectedFileIdx] ? genResult.files[selectedFileIdx].path : ''}
                        onChange={(e) => {
                          const updatedFiles = [...genResult.files]
                          updatedFiles[selectedFileIdx].path = e.target.value
                          setGenResult({ ...genResult, files: updatedFiles })
                        }}
                        className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-850 px-2.5 py-1 text-[11px] font-bold font-mono text-indigo-400 rounded-lg focus:outline-none focus:border-indigo-500 flex-1"
                        required
                        title="Edit output destination file path if needed"
                      />
                    </div>
                  </div>

                  {/* Save button */}
                  <button
                    onClick={handleWriteFile}
                    disabled={loading}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-5 py-2.5 rounded-xl flex items-center gap-1.5 transition-all shadow-lg shadow-emerald-500/20 active:scale-[0.96]"
                    title="Write the generated file directly to your framework on disk"
                  >
                    <Save size={14} />
                    <span>Save to Disk</span>
                  </button>
                </div>

                {/* Save confirmation banners */}
                {writeResult && (
                  <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-xl flex items-start gap-3 animate-fadeIn">
                    <CheckCircle className="text-emerald-400 mt-0.5 shrink-0" size={16} />
                    <div>
                      <h4 className="font-bold text-xs leading-none">File Saved Successfully! ✅</h4>
                      <p className="text-[11px] mt-1.5 text-slate-500 dark:text-gray-400 leading-relaxed">
                        Surgically added <code className="bg-slate-50 dark:bg-gray-950 px-1 rounded font-bold font-mono text-indigo-400">{writeResult.relative_path}</code> directly to your framework at <code className="bg-slate-50 dark:bg-gray-950 px-1 rounded font-mono">{extendFolder}</code>.
                      </p>
                    </div>
                  </div>
                )}

                {/* Code viewport block */}
                <div className="space-y-2">
                  <textarea
                    value={genResult.files && genResult.files[selectedFileIdx] ? genResult.files[selectedFileIdx].content : ''}
                    onChange={(e) => {
                      const updatedFiles = [...genResult.files]
                      updatedFiles[selectedFileIdx].content = e.target.value
                      setGenResult({ ...genResult, files: updatedFiles })
                    }}
                    rows={16}
                    className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-850 p-5 rounded-xl font-mono text-[11px] text-slate-600 dark:text-gray-300 focus:outline-none focus:border-indigo-500 leading-relaxed resize-y shadow-inner transition-all"
                    required
                  />
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl p-12 text-center text-slate-400 dark:text-gray-500 h-full flex flex-col justify-center items-center min-h-[400px]">
                <FileCode size={48} className="text-gray-800 mb-4" />
                <h4 className="font-bold text-slate-600 dark:text-gray-300 text-base">No Code Generated Yet</h4>
                <p className="text-xs text-slate-400 dark:text-gray-500 max-w-sm mx-auto mt-1 leading-relaxed font-medium">Input your existing local framework path and file description instructions on the left panel, then hit generate to inspect. Your generated scripts will appear here.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default AutomationModule
