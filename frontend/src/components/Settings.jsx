import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Save, ShieldCheck, Eye, EyeOff, Code2, RefreshCw, CheckCircle, AlertCircle, ChevronDown, ChevronUp, Play, Sparkles, HelpCircle, Bug, Sliders } from 'lucide-react'

const API_BASE_URL = 'http://127.0.0.1:5000/api'

function Settings() {
  const [provider, setProvider] = useState('gemini')
  const [activeModel, setActiveModel] = useState('gemini-1.5-flash')
  const [activeKey, setActiveKey] = useState('')

  // Symmetrical state holders for individual providers
  const [keyOpenai, setKeyOpenai] = useState('')
  const [modelOpenai, setModelOpenai] = useState('gpt-4o')

  const [keyGemini, setKeyGemini] = useState('')
  const [modelGemini, setModelGemini] = useState('gemini-1.5-flash')

  const [keyGroq, setKeyGroq] = useState('')
  const [modelGroq, setModelGroq] = useState('llama-3.3-70b-versatile')

  const [keyGrok, setKeyGrok] = useState('')
  const [modelGrok, setModelGrok] = useState('grok-2-vision')

  const [keyOpenrouter, setKeyOpenrouter] = useState('')
  const [modelOpenrouter, setModelOpenrouter] = useState('google/gemini-2.5-flash:free')

  const [keyAzure, setKeyAzure] = useState('')
  const [modelAzure, setModelAzure] = useState('gpt-5.2')
  const [azureEndpoint, setAzureEndpoint] = useState('')
  const [azureApiVersion, setAzureApiVersion] = useState('2023-05-15')

  // Show/Hide credentials state
  const [showKey, setShowKey] = useState(false)
  const [showAdoPat, setShowAdoPat] = useState(false)
  const [showGithubPat, setShowGithubPat] = useState(false)
  const [showGitlabPat, setShowGitlabPat] = useState(false)

  // Custom Browser Session Headers config
  const [browserHeaders, setBrowserHeaders] = useState('')
  const [visualHeadless, setVisualHeadless] = useState(true)
  const [captureDesktop, setCaptureDesktop] = useState(true)
  const [captureLaptop, setCaptureLaptop] = useState(true)
  const [captureTablet, setCaptureTablet] = useState(true)
  const [captureMobile, setCaptureMobile] = useState(true)

  // Symmetrical Live Session Harvester states
  const [harvesting, setHarvesting] = useState(false)
  const [harvestStatus, setHarvestStatus] = useState(null)

  // Bug tracker selection
  const [bugExportTarget, setBugExportTarget] = useState('jira')

  // Jira configs
  const [jiraDomain, setJiraDomain] = useState('')
  const [jiraEmail, setJiraEmail] = useState('')
  const [jiraToken, setJiraToken] = useState('')
  const [jiraProjectKey, setJiraProjectKey] = useState('')

  // Azure DevOps configs
  const [adoOrg, setAdoOrg] = useState('')
  const [adoProj, setAdoProj] = useState('')
  const [adoPat, setAdoPat] = useState('')

  // GitHub configs
  const [githubOwner, setGithubOwner] = useState('')
  const [githubRepo, setGithubRepo] = useState('')
  const [githubPat, setGithubPat] = useState('')

  // GitLab configs
  const [gitlabProjectId, setGitlabProjectId] = useState('')
  const [gitlabPat, setGitlabPat] = useState('')

  // Prompt states
  const [promptFiles, setPromptFiles] = useState([])
  const [selectedPromptFile, setSelectedPromptFile] = useState('CombinedPrompt.txt')
  const [promptsText, setPromptsText] = useState('')
  const [promptsSaved, setPromptsSaved] = useState(false)

  // Accordion panels state
  const [llmOpen, setLlmOpen] = useState(true)
  const [browserOpen, setBrowserOpen] = useState(true)
  const [bugOpen, setBugOpen] = useState(true)
  const [promptOpen, setPromptOpen] = useState(true)

  // Save status states per card
  const [llmSaved, setLlmSaved] = useState(false)
  const [browserSaved, setBrowserSaved] = useState(false)
  const [bugSaved, setBugSaved] = useState(false)

  // Test connection states per card
  const [testingLlm, setTestingLlm] = useState(false)
  const [llmConnStatus, setLlmConnStatus] = useState(null)
  
  const [testingBug, setTestingBug] = useState(false)
  const [bugConnStatus, setBugConnStatus] = useState(null)

  useEffect(() => {
    // Load active provider selection
    const savedProvider = localStorage.getItem('llm_provider') || 'gemini'
    setProvider(savedProvider)

    // Load static browser fields
    setBrowserHeaders(localStorage.getItem('browser_headers') || '')
    setVisualHeadless(localStorage.getItem('visual_headless') !== 'false')
    setCaptureDesktop(localStorage.getItem('capture_desktop') !== 'false')
    setCaptureTablet(localStorage.getItem('capture_tablet') !== 'false')
    setCaptureMobile(localStorage.getItem('capture_mobile') !== 'false')

    // Load Bug tracker target
    setBugExportTarget(localStorage.getItem('bug_export_target') || 'jira')

    // Load individual provider Keys and Models to prevent any key-spillovers!
    setKeyOpenai(localStorage.getItem('llm_openai_api_key') || '')
    setModelOpenai(localStorage.getItem('llm_openai_model') || 'gpt-4o')

    setKeyGemini(localStorage.getItem('llm_gemini_api_key') || '')
    setModelGemini(localStorage.getItem('llm_gemini_model') || 'gemini-1.5-flash')

    setKeyGroq(localStorage.getItem('llm_groq_api_key') || '')
    setModelGroq(localStorage.getItem('llm_groq_model') || 'llama-3.3-70b-versatile')

    setKeyGrok(localStorage.getItem('llm_grok_api_key') || '')
    setModelGrok(localStorage.getItem('llm_grok_model') || 'grok-2-vision')

    setKeyOpenrouter(localStorage.getItem('llm_openrouter_api_key') || '')
    setModelOpenrouter(localStorage.getItem('llm_openrouter_model') || 'google/gemini-2.5-flash:free')

    setKeyAzure(localStorage.getItem('llm_azure_api_key') || '')
    setModelAzure(localStorage.getItem('llm_azure_model') || 'gpt-5.2')

    // Symmetrical Connection String De-compiling / Parsing on load!
    const savedConnString = localStorage.getItem('llm_azure_connection_string') || ''
    if (savedConnString) {
      const parts = savedConnString.split(';')
      let resolvedEndpoint = ''
      let resolvedVersion = '2023-05-15'
      
      parts.forEach(part => {
        if (part.includes('=')) {
          const [k, v] = part.split('=', 2)
          const kClean = k.trim().toLowerCase()
          if (kClean === 'endpoint' || kClean === 'url' || kClean === 'azure_endpoint') {
            resolvedEndpoint = v.trim()
          } else if (kClean === 'version' || kClean === 'api_version' || kClean === 'api-version') {
            resolvedVersion = v.trim()
          }
        }
      })
      setAzureEndpoint(resolvedEndpoint)
      setAzureApiVersion(resolvedVersion)
    }

    // Load Jira variables
    setJiraDomain(localStorage.getItem('jira_domain') || '')
    setJiraEmail(localStorage.getItem('jira_email') || '')
    setJiraToken(localStorage.getItem('jira_token') || '')
    setJiraProjectKey(localStorage.getItem('jira_project_key') || '')

    // Load Azure DevOps variables
    setAdoOrg(localStorage.getItem('ado_org') || '')
    setAdoProj(localStorage.getItem('ado_proj') || '')
    setAdoPat(localStorage.getItem('ado_pat') || '')

    // Load GitHub variables
    setGithubOwner(localStorage.getItem('github_owner') || '')
    setGithubRepo(localStorage.getItem('github_repo') || '')
    setGithubPat(localStorage.getItem('github_pat') || '')

    // Load GitLab variables
    setGitlabProjectId(localStorage.getItem('gitlab_project_id') || '')
    setGitlabPat(localStorage.getItem('gitlab_pat') || '')

    // Fetch list of prompts files
    const fetchPrompts = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/test-cases/prompts/list`)
        setPromptFiles(response.data.prompts || [])
      } catch (err) {
        console.error('Failed to load prompts file list:', err)
      }
    }
    fetchPrompts()
  }, [])

  // Dynamic model & key sync to bind display values of active provider
  useEffect(() => {
    if (provider === 'openai') {
      setActiveKey(keyOpenai)
      setActiveModel(modelOpenai)
    } else if (provider === 'gemini') {
      setActiveKey(keyGemini)
      setActiveModel(modelGemini)
    } else if (provider === 'groq') {
      setActiveKey(keyGroq)
      setActiveModel(modelGroq)
    } else if (provider === 'grok') {
      setActiveKey(keyGrok)
      setActiveModel(modelGrok)
    } else if (provider === 'openrouter') {
      setActiveKey(keyOpenrouter)
      setActiveModel(modelOpenrouter)
    } else if (provider === 'azure') {
      setActiveKey(keyAzure)
      setActiveModel(modelAzure)
    }
  }, [provider, keyOpenai, modelOpenai, keyGemini, modelGemini, keyGroq, modelGroq, keyGrok, modelGrok, keyOpenrouter, modelOpenrouter, keyAzure, modelAzure])

  // Load selected prompt content in real-time
  useEffect(() => {
    const fetchSelectedPrompt = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/test-cases/prompts/raw?file=${selectedPromptFile}`)
        setPromptsText(response.data.content)
      } catch (err) {
        console.error(`Failed to load ${selectedPromptFile}:`, err)
      }
    }
    fetchSelectedPrompt()
  }, [selectedPromptFile])

  // =====================================================================
  // MODULAR SAVE HANDLERS
  // =====================================================================

  const handleSaveLlm = (e) => {
    e.preventDefault()
    localStorage.setItem('llm_provider', provider)

    // Save specific provider model/key states to avoid bleeding
    if (provider === 'openai') {
      localStorage.setItem('llm_openai_api_key', activeKey)
      localStorage.setItem('llm_openai_model', activeModel)
      setKeyOpenai(activeKey)
      setModelOpenai(activeModel)
    } else if (provider === 'gemini') {
      localStorage.setItem('llm_gemini_api_key', activeKey)
      localStorage.setItem('llm_gemini_model', activeModel)
      setKeyGemini(activeKey)
      setModelGemini(activeModel)
    } else if (provider === 'groq') {
      localStorage.setItem('llm_groq_api_key', activeKey)
      localStorage.setItem('llm_groq_model', activeModel)
      setKeyGroq(activeKey)
      setModelGroq(activeModel)
    } else if (provider === 'grok') {
      localStorage.setItem('llm_grok_api_key', activeKey)
      localStorage.setItem('llm_grok_model', activeModel)
      setKeyGrok(activeKey)
      setModelGrok(activeModel)
    } else if (provider === 'openrouter') {
      localStorage.setItem('llm_openrouter_api_key', activeKey)
      localStorage.setItem('llm_openrouter_model', activeModel)
      setKeyOpenrouter(activeKey)
      setModelOpenrouter(activeModel)
    } else if (provider === 'azure') {
      localStorage.setItem('llm_azure_api_key', activeKey)
      localStorage.setItem('llm_azure_model', activeModel)
      setKeyAzure(activeKey)
      setModelAzure(activeModel)

      // Symmetrical Connection String compiler
      const compiledConnString = `Key=${activeKey};Endpoint=${azureEndpoint};Version=${azureApiVersion}`
      localStorage.setItem('llm_azure_connection_string', compiledConnString)
    }

    setLlmSaved(true)
    setTimeout(() => setLlmSaved(false), 3000)
  }

  const handleSaveBrowser = (e) => {
    e.preventDefault()
    localStorage.setItem('browser_headers', browserHeaders.trim())
    localStorage.setItem('visual_headless', visualHeadless ? 'true' : 'false')
    localStorage.setItem('capture_desktop', captureDesktop ? 'true' : 'false')
    localStorage.setItem('capture_tablet', captureTablet ? 'true' : 'false')
    localStorage.setItem('capture_mobile', captureMobile ? 'true' : 'false')

    setBrowserSaved(true)
    setTimeout(() => setBrowserSaved(false), 3000)
  }

  const handleSaveBugTracker = (e) => {
    e.preventDefault()
    localStorage.setItem('bug_export_target', bugExportTarget)

    // Save active bug tracker variables
    if (bugExportTarget === 'jira') {
      localStorage.setItem('jira_domain', jiraDomain.trim())
      localStorage.setItem('jira_email', jiraEmail.trim())
      localStorage.setItem('jira_token', jiraToken.trim())
      localStorage.setItem('jira_project_key', jiraProjectKey.trim().toUpperCase())
    } else if (bugExportTarget === 'ado') {
      localStorage.setItem('ado_org', adoOrg.trim())
      localStorage.setItem('ado_proj', adoProj.trim())
      localStorage.setItem('ado_pat', adoPat.trim())
    } else if (bugExportTarget === 'github') {
      localStorage.setItem('github_owner', githubOwner.trim())
      localStorage.setItem('github_repo', githubRepo.trim())
      localStorage.setItem('github_pat', githubPat.trim())
    } else if (bugExportTarget === 'gitlab') {
      localStorage.setItem('gitlab_project_id', gitlabProjectId.trim())
      localStorage.setItem('gitlab_pat', gitlabPat.trim())
    }

    setBugSaved(true)
    setTimeout(() => setBugSaved(false), 3000)
  }

  const handlePublishPrompt = async (e) => {
    e.preventDefault()
    setPromptsSaved(false)
    try {
      await axios.post(`${API_BASE_URL}/test-cases/prompts/raw?file=${selectedPromptFile}`, {
        content: promptsText
      })
      setPromptsSaved(true)
      setTimeout(() => setPromptsSaved(false), 3000)
    } catch (err) {
      alert(`Failed to save prompt: ${err.message}`)
    }
  }

  // =====================================================================
  // TESTING CONNECTIONS HANDLERS
  // =====================================================================

  const handleTestLlmConnection = async () => {
    setTestingLlm(true)
    setLlmConnStatus(null)
    
    // Compile Azure settings on the fly if active
    const compConnString = provider === 'azure' 
      ? `Key=${activeKey};Endpoint=${azureEndpoint};Version=${azureApiVersion}` 
      : ''

    try {
      const response = await axios.post(`${API_BASE_URL}/settings/test-connection`, {
        provider: provider,
        model: activeModel,
        api_key: activeKey,
        azure_connection_string: compConnString
      })
      setLlmConnStatus({ success: true, message: response.data.message })
    } catch (err) {
      setLlmConnStatus({ success: false, message: err.response?.data?.detail || err.message })
    } finally {
      setTestingLlm(false)
    }
  }

  const handleTestBugConnection = async () => {
    setTestingBug(true)
    setBugConnStatus(null)

    try {
      const response = await axios.post(`${API_BASE_URL}/bugs/test-connection`, {
        target: bugExportTarget,
        jira_domain: jiraDomain,
        jira_email: jiraEmail,
        jira_token: jiraToken,
        jira_project_key: jiraProjectKey,
        ado_org: adoOrg,
        ado_proj: adoProj,
        ado_pat: adoPat,
        github_owner: githubOwner,
        github_repo: githubRepo,
        github_pat: githubPat,
        gitlab_project_id: gitlabProjectId,
        gitlab_pat: gitlabPat
      })
      setBugConnStatus({ success: true, message: response.data.message })
    } catch (err) {
      setBugConnStatus({ success: false, message: err.response?.data?.detail || err.message })
    } finally {
      setTestingBug(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
      
      {/* =====================================================================
          CARD 1: BRING YOUR OWN KEY (BYOK)
          ===================================================================== */}
      <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl p-6">
        <div 
          onClick={() => setLlmOpen(!llmOpen)}
          className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-gray-800 cursor-pointer select-none group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-500 dark:text-indigo-400 rounded-xl">
              <ShieldCheck size={20} />
            </div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-800 dark:text-white text-base">Bring Your Own Key</h3>
              {/* Privacy Tooltip info button */}
              <div className="relative group/tooltip">
                <HelpCircle size={14} className="text-slate-400 hover:text-indigo-500 transition-colors cursor-help" />
                <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover/tooltip:block w-48 bg-slate-900 text-white text-[10px] p-2 rounded-lg text-center leading-normal shadow-xl border border-gray-800 z-50">
                  Your credentials are kept private and saved strictly inside your local browser sandbox.
                </div>
              </div>
            </div>
          </div>
          <div className="text-slate-400 group-hover:text-indigo-500 dark:group-hover:text-indigo-400 transition-colors">
            {llmOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </div>
        </div>

        {llmOpen && (
          <form onSubmit={handleSaveLlm} className="mt-6 space-y-6 animate-fadeIn">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">LLM Cloud Provider</label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
                >
                  <option value="gemini">Google Gemini AI</option>
                  <option value="openai">OpenAI (GPT Engine)</option>
                  <option value="azure">Azure OpenAI Service</option>
                  <option value="groq">Groq Cloud (Llama Engine)</option>
                  <option value="grok">Grok AI (X.AI Engine)</option>
                  <option value="openrouter">OpenRouter (Unified Free Models)</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Selected Model</label>
                <input
                  type="text"
                  value={activeModel}
                  onChange={(e) => {
                    setActiveModel(e.target.value)
                    if (provider === 'openai') setModelOpenai(e.target.value)
                    else if (provider === 'gemini') setModelGemini(e.target.value)
                    else if (provider === 'groq') setModelGroq(e.target.value)
                    else if (provider === 'grok') setModelGrok(e.target.value)
                    else if (provider === 'openrouter') setModelOpenrouter(e.target.value)
                    else if (provider === 'azure') setModelAzure(e.target.value)
                  }}
                  placeholder="Enter model deployment string..."
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                />
                
                {/* Free suggested models triggers */}
                {provider === 'openrouter' && (
                  <div className="text-[10px] text-slate-400 dark:text-gray-500 flex flex-wrap gap-2 pt-1 select-none">
                    <span className="font-bold uppercase tracking-wider text-[8px] mt-0.5 text-indigo-400">Free Suggested:</span>
                    <button type="button" onClick={() => setActiveModel('google/gemini-2.5-flash:free')} className="text-indigo-500 hover:underline font-medium">gemini-2.5-flash:free</button>
                    <span>|</span>
                    <button type="button" onClick={() => setActiveModel('meta-llama/llama-3.3-70b-instruct:free')} className="text-indigo-500 hover:underline font-medium">llama-3.3:free</button>
                    <span>|</span>
                    <button type="button" onClick={() => setActiveModel('deepseek/deepseek-chat:free')} className="text-indigo-500 hover:underline font-medium">deepseek:free</button>
                  </div>
                )}
                {provider === 'groq' && (
                  <div className="text-[10px] text-slate-400 dark:text-gray-500 flex flex-wrap gap-2 pt-1 select-none">
                    <span className="font-bold uppercase tracking-wider text-[8px] mt-0.5 text-indigo-400">Default suggested:</span>
                    <button type="button" onClick={() => setActiveModel('llama-3.3-70b-versatile')} className="text-indigo-500 hover:underline font-medium">llama-3.3-70b-versatile</button>
                  </div>
                )}
              </div>

              <div className="col-span-1 md:col-span-2 space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">API Bearer Key / Private Access Secret</label>
                <div className="relative">
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={activeKey}
                    onChange={(e) => {
                      setActiveKey(e.target.value)
                      if (provider === 'openai') setKeyOpenai(e.target.value)
                      else if (provider === 'gemini') setKeyGemini(e.target.value)
                      else if (provider === 'groq') setKeyGroq(e.target.value)
                      else if (provider === 'grok') setKeyGrok(e.target.value)
                      else if (provider === 'openrouter') setKeyOpenrouter(e.target.value)
                      else if (provider === 'azure') setKeyAzure(e.target.value)
                    }}
                    placeholder="Paste private API credentials secret..."
                    className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-4 pr-12 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs placeholder:text-gray-400 dark:placeholder:text-gray-600"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-gray-300 transition-colors"
                  >
                    {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {/* Symmetrical Azure OpenAI fields */}
              {provider === 'azure' && (
                <div className="col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-100 dark:border-gray-850 animate-fadeIn">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Azure Resource Endpoint URL</label>
                    <input
                      type="text"
                      value={azureEndpoint}
                      onChange={(e) => setAzureEndpoint(e.target.value)}
                      placeholder="e.g. https://my-resource.openai.azure.com/"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Azure Target API Version</label>
                    <input
                      type="text"
                      value={azureApiVersion}
                      onChange={(e) => setAzureApiVersion(e.target.value)}
                      placeholder="e.g. 2023-05-15"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Save & Test Actions for BYOK Card */}
            <div className="pt-4 border-t border-slate-100 dark:border-gray-850 flex flex-wrap gap-4 items-center justify-between select-none">
              <button
                type="button"
                onClick={handleTestLlmConnection}
                disabled={testingLlm || !activeKey}
                className="bg-indigo-500/10 hover:bg-indigo-500/20 disabled:opacity-40 disabled:cursor-not-allowed border border-indigo-500/25 text-indigo-500 dark:text-indigo-400 font-bold text-xs px-5 py-3 rounded-xl flex items-center gap-2 transition-all active:scale-[0.98]"
              >
                <RefreshCw size={14} className={testingLlm ? 'animate-spin' : ''} />
                <span>{testingLlm ? 'Verifying...' : 'Test LLM Connection'}</span>
              </button>

              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-6 py-3.5 rounded-xl flex items-center gap-2.5 active:scale-[0.98] transition-all shadow-md"
              >
                <Save size={16} />
                <span>{llmSaved ? 'LLM Credentials Saved!' : 'Save LLM Credentials'}</span>
              </button>
            </div>

            {/* Test Connection Result alert Banner */}
            {llmConnStatus && (
              <div className={`p-4 rounded-xl border flex items-start gap-3.5 animate-fadeIn text-xs leading-relaxed ${
                llmConnStatus.success 
                  ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-600 dark:text-emerald-400' 
                  : 'bg-rose-500/10 border-rose-500/25 text-rose-600 dark:text-rose-400'
              }`}>
                {llmConnStatus.success ? <CheckCircle size={16} className="shrink-0 mt-0.5" /> : <AlertCircle size={16} className="shrink-0 mt-0.5" />}
                <span>{llmConnStatus.message}</span>
              </div>
            )}
          </form>
        )}
      </div>

      {/* =====================================================================
          CARD 2: BROWSER & VISUAL TESTING SETTINGS (OTHER OPTIONS)
          ===================================================================== */}
      <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl p-6">
        <div 
          onClick={() => setBrowserOpen(!browserOpen)}
          className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-gray-800 cursor-pointer select-none group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-500 dark:text-indigo-400 rounded-xl">
              <Sliders size={20} />
            </div>
            <h3 className="font-bold text-slate-800 dark:text-white text-base">Browser & Visual Testing Settings</h3>
          </div>
          <div className="text-slate-400 group-hover:text-indigo-500 dark:group-hover:text-indigo-400 transition-colors">
            {browserOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </div>
        </div>

        {browserOpen && (
          <form onSubmit={handleSaveBrowser} className="mt-6 space-y-6 animate-fadeIn">
            <div className="space-y-6">
              
              {/* Custom Browser Session Headers */}
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Custom Browser Session Headers (JSON Optional)</label>
                <input
                  type="text"
                  value={browserHeaders}
                  onChange={(e) => setBrowserHeaders(e.target.value)}
                  placeholder='e.g. {"Authorization": "Bearer token123", "Cookie": "session=abc"}'
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs placeholder:text-gray-400 dark:placeholder:text-gray-600"
                />
                <p className="text-[10px] text-slate-400 dark:text-gray-500 leading-normal">
                  * Inject raw session authorization headers or cookies to automatically bypass login screens and capture password-protected user dashboards.
                </p>
              </div>

              {/* LIVE MANUAL SESSION HARVESTER */}
              <div className="space-y-4 pt-4 border-t border-slate-100 dark:border-gray-850">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300 flex items-center gap-2">
                      <Sparkles className="text-indigo-500 animate-pulse" size={16} />
                      <span>🔐 Live Manual Session Harvester (Ultimate Login Rescue!)</span>
                    </label>
                    <p className="text-[10px] text-slate-400 dark:text-gray-500 leading-normal">
                      * If credentials or cookie injections get blocked by strict IIS/MFA firewalls, click this button to open a physical Chrome window. Manually log in once, and close the window—the platform will automatically harvest and save your session files natively to disk forever!
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={async () => {
                      const savedUrl = localStorage.getItem('harvester_login_url') || ''
                      const url = prompt("Enter your application login entry point URL:", savedUrl)
                      if (!url || !url.trim()) return
                      
                      const cleanUrl = url.trim()
                      localStorage.setItem('harvester_login_url', cleanUrl)
                      
                      setHarvesting(true)
                      setHarvestStatus(null)
                      try {
                        const response = await axios.post(`${API_BASE_URL}/regression-testing/session/harvest`, { login_url: cleanUrl })
                        setHarvestStatus({ success: true, message: response.data.message })
                      } catch (err) {
                        setHarvestStatus({ success: false, message: err.response?.data?.detail || err.message })
                      } finally {
                        setHarvesting(false)
                      }
                    }}
                    disabled={harvesting}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs px-5 py-3 rounded-xl flex items-center gap-2 transition-all active:scale-[0.96] shrink-0 shadow-md"
                  >
                    {harvesting ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                    <span>{harvesting ? 'Harvesting Session...' : 'Capture Live Session'}</span>
                  </button>
                </div>

                {harvesting && (
                  <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4 flex items-start gap-3.5 animate-pulse text-xs text-indigo-400 leading-relaxed">
                    <RefreshCw size={16} className="animate-spin shrink-0 mt-0.5 text-indigo-400" />
                    <div>
                      <h4 className="font-bold">🔐 LIVE BROWSER WINDOW OPENED ON YOUR DESKTOP!</h4>
                      <p className="opacity-90 mt-0.5">Please locate the newly opened Chrome browser window on your taskbar, log in completely (override warning popups), and **CLOSE the browser window** when ready to capture your session cookies natively!</p>
                    </div>
                  </div>
                )}

                {harvestStatus && (
                  <div className={`p-4 rounded-xl border flex items-start gap-3.5 animate-fadeIn text-xs leading-relaxed ${
                    harvestStatus.success 
                      ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-600 dark:text-emerald-400' 
                      : 'bg-rose-500/10 border-rose-500/25 text-rose-600 dark:text-rose-400'
                  }`}>
                    {harvestStatus.success ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                    <span>{harvestStatus.message}</span>
                  </div>
                )}
              </div>

              {/* DYNAMIC VISUAL HEADLESS & VIEWPORT SELECTORS */}
              <div className="flex flex-wrap items-center justify-between gap-6 pt-4 border-t border-slate-100 dark:border-gray-850 select-none">
                {/* LEFT: SINGLE HEADLESS TOGGLE CHECKBOX */}
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="headless_checkbox"
                    checked={visualHeadless}
                    onChange={(e) => setVisualHeadless(e.target.checked)}
                    className="w-4 h-4 rounded text-indigo-600 border-slate-300 dark:border-gray-800 focus:ring-indigo-500 accent-indigo-600 cursor-pointer"
                  />
                  <label htmlFor="headless_checkbox" className="text-sm font-semibold text-slate-700 dark:text-gray-300 cursor-pointer flex items-center gap-1.5 hover:text-indigo-500 transition-colors">
                    <span>Run Visual Testing Headless</span>
                    <div className="relative group/tooltip">
                      <HelpCircle size={14} className="text-slate-400 hover:text-indigo-500 transition-colors cursor-help" />
                      <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover/tooltip:block w-64 bg-slate-900 text-white text-[10px] p-2.5 rounded-lg text-center leading-normal shadow-xl border border-gray-800 z-50 font-normal">
                        Enable to run visual sweeps silently in the background (Fast). Disable (uncheck) if you are using manual live browser sessions or local Chrome profiles to bypass SSO login walls.
                      </div>
                    </div>
                  </label>
                </div>

                {/* RIGHT: ACTIVE CAPTURE VIEWPORTS CHECKBOXES */}
                <div className="flex items-center gap-4 border-l border-slate-100 dark:border-gray-800 pl-4">
                  <span className="text-xs font-semibold text-slate-500 dark:text-gray-400 select-none">Viewports:</span>
                  
                  <label className="flex items-center gap-2 cursor-pointer group/v select-none">
                    <input
                      type="checkbox"
                      checked={captureDesktop}
                      onChange={(e) => setCaptureDesktop(e.target.checked)}
                      className="w-4 h-4 rounded text-indigo-600 border-slate-300 dark:border-gray-800 focus:ring-indigo-500 accent-indigo-600 cursor-pointer"
                    />
                    <span className="text-xs font-semibold text-slate-700 dark:text-gray-300 group-hover/v:text-indigo-500 transition-colors">Desktop</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer group/v select-none">
                    <input
                      type="checkbox"
                      checked={captureLaptop}
                      onChange={(e) => setCaptureLaptop(e.target.checked)}
                      className="w-4 h-4 rounded text-indigo-600 border-slate-300 dark:border-gray-800 focus:ring-indigo-500 accent-indigo-600 cursor-pointer"
                    />
                    <span className="text-xs font-semibold text-slate-700 dark:text-gray-300 group-hover/v:text-indigo-500 transition-colors">Laptop</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer group/v select-none">
                    <input
                      type="checkbox"
                      checked={captureTablet}
                      onChange={(e) => setCaptureTablet(e.target.checked)}
                      className="w-4 h-4 rounded text-indigo-600 border-slate-300 dark:border-gray-800 focus:ring-indigo-500 accent-indigo-600 cursor-pointer"
                    />
                    <span className="text-xs font-semibold text-slate-700 dark:text-gray-300 group-hover/v:text-indigo-500 transition-colors">Tablet</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer group/v select-none">
                    <input
                      type="checkbox"
                      checked={captureMobile}
                      onChange={(e) => setCaptureMobile(e.target.checked)}
                      className="w-4 h-4 rounded text-indigo-600 border-slate-300 dark:border-gray-800 focus:ring-indigo-500 accent-indigo-600 cursor-pointer"
                    />
                    <span className="text-xs font-semibold text-slate-700 dark:text-gray-300 group-hover/v:text-indigo-500 transition-colors">Mobile</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Save button for Browser Settings Card */}
            <div className="pt-4 border-t border-slate-100 dark:border-gray-850 flex justify-end select-none">
              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-6 py-3.5 rounded-xl flex items-center gap-2.5 active:scale-[0.98] transition-all shadow-md"
              >
                <Save size={16} />
                <span>{browserSaved ? 'Browser Settings Saved!' : 'Save Browser Settings'}</span>
              </button>
            </div>
          </form>
        )}
      </div>

      {/* =====================================================================
          CARD 3: BUG TRACKER INTEGRATIONS
          ===================================================================== */}
      <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl p-6">
        <div 
          onClick={() => setBugOpen(!bugOpen)}
          className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-gray-800 cursor-pointer select-none group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-500 dark:text-indigo-400 rounded-xl">
              <Bug size={20} />
            </div>
            <h3 className="font-bold text-slate-800 dark:text-white text-base">Enterprise Bug Tracker Integrations</h3>
          </div>
          <div className="text-slate-400 group-hover:text-indigo-500 dark:group-hover:text-indigo-400 transition-colors">
            {bugOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </div>
        </div>

        {bugOpen && (
          <form onSubmit={handleSaveBugTracker} className="mt-6 space-y-6 animate-fadeIn">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              <div className="col-span-1 md:col-span-2 space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Select Target Tracker</label>
                <select
                  value={bugExportTarget}
                  onChange={(e) => setBugExportTarget(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
                >
                  <option value="jira">Atlassian JIRA Cloud (v2 Markdown REST API)</option>
                  <option value="ado">Microsoft Azure DevOps Boards</option>
                  <option value="github">GitHub Issues Tracker</option>
                  <option value="gitlab">GitLab Issues Portal</option>
                </select>
              </div>

              {/* JIRA CONFIGURATION DETAILS */}
              {bugExportTarget === 'jira' && (
                <div className="col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-100 dark:border-gray-850 animate-fadeIn">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Jira Host Domain URL</label>
                    <input
                      type="text"
                      value={jiraDomain}
                      onChange={(e) => setJiraDomain(e.target.value)}
                      placeholder="e.g. https://my-org.atlassian.net"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Jira Account Email Address</label>
                    <input
                      type="email"
                      value={jiraEmail}
                      onChange={(e) => setJiraEmail(e.target.value)}
                      placeholder="e.g. admin@org.com"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Jira Project Access Key</label>
                    <input
                      type="text"
                      value={jiraProjectKey}
                      onChange={(e) => setJiraProjectKey(e.target.value)}
                      placeholder="e.g. PROJ"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs uppercase"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Jira API Token</label>
                    <input
                      type="password"
                      value={jiraToken}
                      onChange={(e) => setJiraToken(e.target.value)}
                      placeholder="Enter Jira Api Token..."
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                    />
                  </div>
                </div>
              )}

              {/* AZURE DEVOPS CONFIGURATION DETAILS */}
              {bugExportTarget === 'ado' && (
                <div className="col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-100 dark:border-gray-850 animate-fadeIn">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Azure DevOps Organization Name</label>
                    <input
                      type="text"
                      value={adoOrg}
                      onChange={(e) => setAdoOrg(e.target.value)}
                      placeholder="e.g. MyOrg"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Target Project Name</label>
                    <input
                      type="text"
                      value={adoProj}
                      onChange={(e) => setAdoProj(e.target.value)}
                      placeholder="e.g. TestProject"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-2 col-span-1 md:col-span-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Personal Access Token (PAT)</label>
                    <div className="relative">
                      <input
                        type={showAdoPat ? 'text' : 'password'}
                        value={adoPat}
                        onChange={(e) => setAdoPat(e.target.value)}
                        placeholder="Enter Azure DevOps PAT..."
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-4 pr-12 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                      />
                      <button
                        type="button"
                        onClick={() => setShowAdoPat(!showAdoPat)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-gray-300 transition-colors"
                      >
                        {showAdoPat ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* GITHUB INTEGRATION CONFIG DETAILS */}
              {bugExportTarget === 'github' && (
                <div className="col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-100 dark:border-gray-850 animate-fadeIn">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Repository Owner Profile (Organization / Username)</label>
                    <input
                      type="text"
                      value={githubOwner}
                      onChange={(e) => setGithubOwner(e.target.value)}
                      placeholder="e.g. MyAccount"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Target Repository Name</label>
                    <input
                      type="text"
                      value={githubRepo}
                      onChange={(e) => setGithubRepo(e.target.value)}
                      placeholder="e.g. MyRepoName"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-2 col-span-1 md:col-span-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">GitHub Personal Access Token (PAT)</label>
                    <div className="relative">
                      <input
                        type={showGithubPat ? 'text' : 'password'}
                        value={githubPat}
                        onChange={(e) => setGithubPat(e.target.value)}
                        placeholder="Enter GitHub PAT..."
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-4 pr-12 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                      />
                      <button
                        type="button"
                        onClick={() => setShowGithubPat(!showGithubPat)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-gray-300 transition-colors"
                      >
                        {showGithubPat ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* GITLAB CONFIGURATION INTEGRATION DETAILS */}
              {bugExportTarget === 'gitlab' && (
                <div className="col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-100 dark:border-gray-850 animate-fadeIn">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">GitLab Project ID / Target ID</label>
                    <input
                      type="text"
                      value={gitlabProjectId}
                      onChange={(e) => setGitlabProjectId(e.target.value)}
                      placeholder="e.g. 12345678"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">GitLab Personal Access Token</label>
                    <div className="relative">
                      <input
                        type={showGitlabPat ? 'text' : 'password'}
                        value={gitlabPat}
                        onChange={(e) => setGitlabPat(e.target.value)}
                        placeholder="Enter GitLab PAT..."
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-4 pr-12 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs"
                      />
                      <button
                        type="button"
                        onClick={() => setShowGitlabPat(!showGitlabPat)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-gray-300 transition-colors"
                      >
                        {showGitlabPat ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Test Connection and Save Actions row for Bug integration Card */}
            <div className="pt-4 border-t border-slate-100 dark:border-gray-850 flex flex-wrap gap-4 items-center justify-between select-none">
              <button
                type="button"
                onClick={handleTestBugConnection}
                disabled={testingBug}
                className="bg-indigo-500/10 hover:bg-indigo-500/20 disabled:opacity-40 border border-indigo-500/25 text-indigo-500 dark:text-indigo-400 font-bold text-xs px-5 py-3 rounded-xl flex items-center gap-2 transition-all active:scale-[0.98]"
              >
                <RefreshCw size={14} className={testingBug ? 'animate-spin' : ''} />
                <span>{testingBug ? 'Verifying...' : 'Test Tracker Connection'}</span>
              </button>

              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-6 py-3.5 rounded-xl flex items-center gap-2.5 active:scale-[0.98] transition-all shadow-md"
              >
                <Save size={16} />
                <span>{bugSaved ? 'Tracker Credentials Saved!' : 'Save Bug Tracker Credentials'}</span>
              </button>
            </div>

            {/* Test Connection Result Alert banner */}
            {bugConnStatus && (
              <div className={`p-4 rounded-xl border flex items-start gap-3.5 animate-fadeIn text-xs leading-relaxed ${
                bugConnStatus.success 
                  ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-600 dark:text-emerald-400' 
                  : 'bg-rose-500/10 border-rose-500/25 text-rose-600 dark:text-rose-400'
              }`}>
                {bugConnStatus.success ? <CheckCircle size={16} className="shrink-0 mt-0.5" /> : <AlertCircle size={16} className="shrink-0 mt-0.5" />}
                <span>{bugConnStatus.message}</span>
              </div>
            )}
          </form>
        )}
      </div>

      {/* =====================================================================
          CARD 4: PROMPT MANAGEMENT SETTINGS
          ===================================================================== */}
      <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm transition-all rounded-2xl p-6">
        <div 
          onClick={() => setPromptOpen(!promptOpen)}
          className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-gray-800 cursor-pointer select-none group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-500 dark:text-indigo-400 rounded-xl">
              <Code2 size={20} />
            </div>
            <h3 className="font-bold text-slate-800 dark:text-white text-base">Prompts System Configuration Files</h3>
          </div>
          <div className="text-slate-400 group-hover:text-indigo-500 dark:group-hover:text-indigo-400 transition-colors">
            {promptOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </div>
        </div>

        {promptOpen && (
          <form onSubmit={handlePublishPrompt} className="mt-6 space-y-4 animate-fadeIn">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-slate-100 dark:border-gray-800 pb-4">
              <div className="space-y-1.5 flex-1 max-w-md">
                <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Select Prompt Target File</label>
                <select
                  value={selectedPromptFile}
                  onChange={(e) => setSelectedPromptFile(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-2.5 text-xs text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer font-mono"
                >
                  {promptFiles.map((file) => (
                    <option key={file} value={file}>
                      {file}
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-5 py-2.5 rounded-xl flex items-center gap-2 active:scale-[0.98] transition-all shadow-md shrink-0 h-[40px] mt-auto"
              >
                <Save size={14} />
                <span>{promptsSaved ? 'Prompt Saved Successfully!' : 'Save Edited Prompt'}</span>
              </button>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">System Prompt Template Editor</label>
              <textarea
                value={promptsText}
                onChange={(e) => setPromptsText(e.target.value)}
                className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-4 text-xs text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono leading-relaxed h-[420px]"
              />
            </div>
          </form>
        )}
      </div>

    </div>
  )
}

export default Settings
