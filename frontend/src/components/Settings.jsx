import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Save, ShieldCheck, Eye, EyeOff, Code2, RefreshCw, CheckCircle, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'

const API_BASE_URL = 'http://127.0.0.1:5000/api'

function Settings() {
  const [provider, setProvider] = useState('gemini')
  const [showKey, setShowKey] = useState(false)

  // ISOLATED PROVIDER STATES (Zero Key-Bleeding Sandbox!)
  const [geminiKey, setGeminiKey] = useState('')
  const [geminiModel, setGeminiModel] = useState('gemini-1.5-flash')

  const [openaiKey, setOpenaiKey] = useState('')
  const [openaiModel, setOpenaiModel] = useState('gpt-4o-mini')

  const [azureKey, setAzureKey] = useState('')
  const [azureModel, setAzureModel] = useState('gpt-4o-mini')
  const [azureEndpoint, setAzureEndpoint] = useState('')
  const [azureApiVersion, setAzureApiVersion] = useState('2023-05-15')

  const [groqKey, setGroqKey] = useState('')
  const [groqModel, setGroqModel] = useState('llama-3.3-70b-versatile')

  const [grokKey, setGrokKey] = useState('')
  const [grokModel, setGrokModel] = useState('grok-2-1212')

  const [openrouterKey, setOpenrouterKey] = useState('')
  const [openrouterModel, setOpenrouterModel] = useState('google/gemini-2.5-flash:free')

  const [anthropicKey, setAnthropicKey] = useState('')
  const [anthropicModel, setAnthropicModel] = useState('claude-3-5-sonnet-20241022')

  // Browser headers for authenticated page captures
  const [browserHeaders, setBrowserHeaders] = useState('')

  // Chrome Profile Path for Persistent session login bypasses
  const [chromeProfile, setChromeProfile] = useState('')

  // Bug tracker selection
  const [bugExportTarget, setBugExportTarget] = useState('jira')

  // Jira configs
  const [jiraDomain, setJiraDomain] = useState('')
  const [jiraEmail, setJiraEmail] = useState('')
  const [jiraToken, setJiraToken] = useState('')
  const [showJiraToken, setShowJiraToken] = useState(false)
  const [jiraProject, setJiraProject] = useState('')

  // Azure DevOps configs
  const [adoOrg, setAdoOrg] = useState('')
  const [adoProj, setAdoProject] = useState('')
  const [adoPat, setAdoPat] = useState('')
  const [showAdoPat, setShowAdoPat] = useState(false)

  // GitHub configs
  const [githubOwner, setGithubOwner] = useState('')
  const [githubRepo, setGithubRepo] = useState('')
  const [githubPat, setGithubPat] = useState('')
  const [showGithubPat, setShowGithubPat] = useState(false)

  // GitLab configs
  const [gitlabProjectId, setGitlabProjectId] = useState('')
  const [gitlabPat, setGitlabPat] = useState('')
  const [showGitlabPat, setShowGitlabPat] = useState(false)

  const [saved, setSaved] = useState(false)

  // Test connection states
  const [testingConn, setTestingConn] = useState(false)
  const [connStatus, setConnStatus] = useState(null)
  const [llmConnStatus, setLlmConnStatus] = useState(null) // Isolated state for LLM connection verification!

  // Accordion Toggle States (Open/Collapse)
  const [llmOpen, setLlmOpen] = useState(true)
  const [bugOpen, setBugOpen] = useState(true)
  const [promptOpen, setPromptOpen] = useState(true)

  // Multi-file Prompt configuration editor states
  const [selectedPromptFile, setSelectedPromptFile] = useState('CombinedPrompt.txt')
  const [promptsText, setPromptsText] = useState('')
  const [promptsSaved, setPromptsSaved] = useState(false)

  // Get active Key based on current provider
  const getActiveApiKey = () => {
    if (provider === 'gemini') return geminiKey
    if (provider === 'openai') return openaiKey
    if (provider === 'azure') return azureKey
    if (provider === 'groq') return groqKey
    if (provider === 'grok') return grokKey
    if (provider === 'openrouter') return openrouterKey
    if (provider === 'anthropic') return anthropicKey
    return ''
  }

  const setActiveApiKey = (val) => {
    if (provider === 'gemini') setGeminiKey(val)
    else if (provider === 'openai') setOpenaiKey(val)
    else if (provider === 'azure') setAzureKey(val)
    else if (provider === 'groq') setGroqKey(val)
    else if (provider === 'grok') setGrokKey(val)
    else if (provider === 'openrouter') setOpenrouterKey(val)
    else if (provider === 'anthropic') setAnthropicKey(val)
  }

  // Get active Model based on current provider
  const getActiveModel = () => {
    if (provider === 'gemini') return geminiModel
    if (provider === 'openai') return openaiModel
    if (provider === 'azure') return azureModel
    if (provider === 'groq') return groqModel
    if (provider === 'grok') return grokModel
    if (provider === 'openrouter') return openrouterModel
    if (provider === 'anthropic') return anthropicModel
    return ''
  }

  const setActiveModel = (val) => {
    if (provider === 'gemini') setGeminiModel(val)
    else if (provider === 'openai') setOpenaiModel(val)
    else if (provider === 'azure') setAzureModel(val)
    else if (provider === 'groq') setGroqModel(val)
    else if (provider === 'grok') setGrokModel(val)
    else if (provider === 'openrouter') setOpenrouterModel(val)
    else if (provider === 'anthropic') setAnthropicModel(val)
  }

  // Load existing configs from localStorage on mount
  useEffect(() => {
    const savedProvider = localStorage.getItem('llm_provider') || 'gemini'
    setProvider(savedProvider)
    setBrowserHeaders(localStorage.getItem('browser_headers') || '')
    setChromeProfile(localStorage.getItem('chrome_profile') || '')
    
    setBugExportTarget(localStorage.getItem('bug_export_target') || 'jira')

    setJiraDomain(localStorage.getItem('jira_domain') || '')
    setJiraEmail(localStorage.getItem('jira_email') || '')
    setJiraToken(localStorage.getItem('jira_token') || '')
    setJiraProject(localStorage.getItem('jira_project') || '')

    setAdoOrg(localStorage.getItem('ado_org') || '')
    setAdoProject(localStorage.getItem('ado_proj') || '')
    setAdoPat(localStorage.getItem('ado_pat') || '')

    setGithubOwner(localStorage.getItem('github_owner') || '')
    setGithubRepo(localStorage.getItem('github_repo') || '')
    setGithubPat(localStorage.getItem('github_pat') || '')

    setGitlabProjectId(localStorage.getItem('gitlab_project_id') || '')
    setGitlabPat(localStorage.getItem('gitlab_pat') || '')

    // Load individual provider Keys and Models to prevent any key-spillovers!
    setGeminiKey(localStorage.getItem('llm_gemini_api_key') || '')
    setGeminiModel(localStorage.getItem('llm_gemini_model') || 'gemini-1.5-flash')

    setOpenaiKey(localStorage.getItem('llm_openai_api_key') || '')
    setOpenaiModel(localStorage.getItem('llm_openai_model') || 'gpt-4o-mini')

    setAzureEndpoint(localStorage.getItem('azure_endpoint') || '')
    setAzureApiVersion(localStorage.getItem('azure_api_version') || '2023-05-15')

    setGroqKey(localStorage.getItem('llm_groq_api_key') || '')
    setGroqModel(localStorage.getItem('llm_groq_model') || 'llama-3.3-70b-versatile')

    setGrokKey(localStorage.getItem('llm_grok_api_key') || '')
    setGrokModel(localStorage.getItem('llm_grok_model') || 'grok-2-1212')

    setOpenrouterKey(localStorage.getItem('llm_openrouter_api_key') || '')
    setOpenrouterModel(localStorage.getItem('llm_openrouter_model') || 'google/gemini-2.5-flash:free')

    setAnthropicKey(localStorage.getItem('llm_anthropic_api_key') || '')
    setAnthropicModel(localStorage.getItem('llm_anthropic_model') || 'claude-3-5-sonnet-20241022')

    // Parse legacy compiled connection string for Azure fallback if present
    const savedLegacyKey = localStorage.getItem('llm_api_key') || ''
    if (savedProvider === 'azure' && savedLegacyKey.includes(';')) {
      const parts = savedLegacyKey.split(';')
      let resolvedKey = ''
      let resolvedEndpoint = ''
      let resolvedVersion = '2023-05-15'
      
      parts.forEach(part => {
        if (part.includes('=')) {
          const [k, v] = part.split('=', 2)
          const kClean = k.trim().toLowerCase()
          const vClean = v.trim()
          if (kClean === 'key' || kClean === 'apikey') resolvedKey = vClean
          else if (kClean === 'endpoint' || kClean === 'url') resolvedEndpoint = vClean
          else if (kClean === 'version' || kClean === 'apiversion') resolvedVersion = vClean
        }
      })
      setAzureKey(resolvedKey)
      setAzureEndpoint(resolvedEndpoint)
      setAzureApiVersion(resolvedVersion)
    } else if (savedProvider === 'azure') {
      setAzureKey(localStorage.getItem('llm_azure_api_key') || savedLegacyKey || '')
    }
  }, [])

  // Fetch the selected prompt configuration dynamically when the file selection changes
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

  // Auto update model options based on selected provider
  const handleProviderChange = (p) => {
    setProvider(p)
  }

  const handleTestLLMConnection = async () => {
    const activeKey = getActiveApiKey()
    const activeModel = getActiveModel()

    if (!activeKey) {
      alert("Please enter your API Key first.")
      return
    }
    setTestingConn(true)
    setLlmConnStatus(null)
    setConnStatus(null) // Cross-reset: Cleanly clears any lingering Bug Tracker test messages!
    
    // Auto-compile credentials for the connection test API if in Azure mode!
    let testApiKey = activeKey.trim()
    if (provider === 'azure') {
      testApiKey = `key=${activeKey.trim()};endpoint=${azureEndpoint.trim()};version=${azureApiVersion.trim()}`
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/settings/test-connection`, {
        provider: provider,
        model: activeModel,
        api_key: testApiKey
      })
      setLlmConnStatus({ success: true, message: response.data.message })
    } catch (err) {
      setLlmConnStatus({ 
        success: false, 
        message: err.response?.data?.detail || `Connection test failed: ${err.message}` 
      })
    } finally {
      setTestingConn(false)
    }
  }

  const handleSave = (e) => {
    e.preventDefault()
    
    // Validate browser headers JSON format only if they explicitly wrote a JSON block (starts with '{')
    const headersTrimmed = browserHeaders.trim()
    if (headersTrimmed && headersTrimmed.startsWith('{')) {
      try {
        JSON.parse(headersTrimmed)
      } catch (err) {
        alert("Invalid JSON format for Browser Session Headers! Please check your syntax (ensure double quotes are used for keys and values).")
        return
      }
    }

    // 1. Save independent provider keys/models
    localStorage.setItem('llm_gemini_api_key', geminiKey.trim())
    localStorage.setItem('llm_gemini_model', geminiModel.trim())

    localStorage.setItem('llm_openai_api_key', openaiKey.trim())
    localStorage.setItem('llm_openai_model', openaiModel.trim())

    localStorage.setItem('llm_azure_api_key', azureKey.trim())
    localStorage.setItem('llm_azure_model', azureModel.trim())
    localStorage.setItem('azure_endpoint', azureEndpoint.trim())
    localStorage.setItem('azure_api_version', azureApiVersion.trim())

    localStorage.setItem('llm_groq_api_key', groqKey.trim())
    localStorage.setItem('llm_groq_model', groqModel.trim())

    // Update default groq model in memory
    localStorage.setItem('llm_groq_model', groqModel.trim())

    localStorage.setItem('llm_grok_api_key', grokKey.trim())
    localStorage.setItem('llm_grok_model', grokModel.trim())

    localStorage.setItem('llm_openrouter_api_key', openrouterKey.trim())
    localStorage.setItem('llm_openrouter_model', openrouterModel.trim())

    localStorage.setItem('llm_anthropic_api_key', anthropicKey.trim())
    localStorage.setItem('llm_anthropic_model', anthropicModel.trim())

    // 2. Save currently active compiled credentials for backward compatibility
    let activeKey = getActiveApiKey()
    let activeModel = getActiveModel()
    
    if (provider === 'azure') {
      activeKey = `key=${azureKey.trim()};endpoint=${azureEndpoint.trim()};version=${azureApiVersion.trim()}`
    }

    localStorage.setItem('llm_provider', provider)
    localStorage.setItem('llm_model', activeModel)
    localStorage.setItem('llm_api_key', activeKey)

    localStorage.setItem('browser_headers', browserHeaders.trim())
    localStorage.setItem('chrome_profile', chromeProfile.trim())
    
    localStorage.setItem('bug_export_target', bugExportTarget)

    localStorage.setItem('jira_domain', jiraDomain)
    localStorage.setItem('jira_email', jiraEmail)
    localStorage.setItem('jira_token', jiraToken)
    localStorage.setItem('jira_project', jiraProject)

    localStorage.setItem('ado_org', adoOrg)
    localStorage.setItem('ado_proj', adoProj)
    localStorage.setItem('ado_pat', adoPat)

    localStorage.setItem('github_owner', githubOwner)
    localStorage.setItem('github_repo', githubRepo)
    localStorage.setItem('github_pat', githubPat)

    localStorage.setItem('gitlab_project_id', gitlabProjectId)
    localStorage.setItem('gitlab_pat', gitlabPat)

    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleTestConnection = async () => {
    setTestingConn(true)
    setConnStatus(null)
    setLlmConnStatus(null) // Cross-reset: Cleanly clears any lingering LLM connection test messages!
    
    let credentials = {}
    if (bugExportTarget === 'jira') {
      credentials = {
        jira_domain: jiraDomain,
        jira_email: jiraEmail,
        jira_token: jiraToken,
        jira_project: jiraProject
      }
    } else if (bugExportTarget === 'azure_devops') {
      credentials = {
        organization: adoOrg,
        project: adoProj,
        personal_access_token: adoPat
      }
    } else if (bugExportTarget === 'github') {
      credentials = {
        owner: githubOwner,
        repo: githubRepo,
        personal_access_token: githubPat
      }
    } else if (bugExportTarget === 'gitlab') {
      credentials = {
        project_id: gitlabProjectId,
        personal_access_token: gitlabPat
      }
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/bug-reporter/test-connection`, {
        target: bugExportTarget,
        credentials: credentials
      })
      setConnStatus({ status: 'success', message: response.data.message })
    } catch (err) {
      setConnStatus({ status: 'error', message: err.response?.data?.detail || err.message })
    } finally {
      setTestingConn(false)
    }
  }

  const handleSavePrompts = async (e) => {
    e.preventDefault()
    try {
      await axios.post(`${API_BASE_URL}/test-cases/prompts/raw?file=${selectedPromptFile}`, {
        content: promptsText
      })
      setPromptsSaved(true)
      setTimeout(() => setPromptsSaved(false), 3000)
    } catch (err) {
      alert(`Failed to save prompt ${selectedPromptFile} on disk: ${err.message}`)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
      {/* Privacy Notice Banner */}
      <div className="bg-indigo-600/10 border border-indigo-500/20 p-5 rounded-2xl flex items-start gap-4 shadow-sm select-none">
        <ShieldCheck className="text-indigo-500 dark:text-indigo-400 shrink-0 mt-0.5" size={24} />
        <div>
          <h3 className="font-bold text-indigo-900 dark:text-indigo-200 text-base">"Bring Your Own Key" (BYOK) Architecture</h3>
          <p className="text-sm text-indigo-700/80 dark:text-indigo-300/80 leading-relaxed mt-1">
            Your credentials are kept 100% private. All API keys and platform passwords are saved in your local browser storage. 
            They are never committed to any remote database. They are only sent in transient request headers to your local host server.
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-8">
        {/* Card 1: LLM API configurations (Collapsible Accordion!) */}
        <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-2xl p-8 space-y-6 transition-all shadow-sm">
          <div 
            onClick={() => setLlmOpen(!llmOpen)}
            className="flex items-center justify-between border-b border-slate-100 dark:border-gray-800 pb-4 cursor-pointer select-none group"
            title="Click to Collapse or Expand LLM credentials configuration"
          >
            <h2 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
              <span>🧠 Large Language Model (LLM) Settings</span>
            </h2>
            <div className="text-slate-400 group-hover:text-indigo-500 dark:group-hover:text-indigo-400 transition-colors">
              {llmOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </div>
          </div>
          
          {llmOpen && (
            <div className="space-y-6 animate-fadeIn">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">LLM Provider</label>
                  <select
                    value={provider}
                    onChange={(e) => handleProviderChange(e.target.value)}
                    onClick={(e) => e.stopPropagation()} // Prevent accordion from collapsing on dropdown clicks!
                    className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
                  >
                    <option value="gemini">Google Gemini AI</option>
                    <option value="openai">OpenAI (GPT)</option>
                    <option value="azure">Azure OpenAI</option>
                    <option value="groq">Groq (LPU Llama-3)</option>
                    <option value="grok">xAI Grok</option>
                    <option value="openrouter">OpenRouter (Multi-LLM)</option>
                    <option value="anthropic">Anthropic Claude</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Selected Model</label>
                  <input
                    type="text"
                    value={getActiveModel()}
                    onChange={(e) => setActiveModel(e.target.value)}
                    placeholder={provider === 'gemini' ? 'e.g. gemini-1.5-flash' : provider === 'openai' ? 'e.g. gpt-4o' : provider === 'azure' ? 'e.g. gpt-4o-mini' : 'e.g. claude-3-5-sonnet'}
                    className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors"
                    required
                  />
                  <div className="flex gap-2.5 mt-2 text-[10px] text-slate-400 dark:text-gray-500 select-none flex-wrap">
                    <span>Suggested:</span>
                    {provider === 'gemini' && (
                      <>
                        <button type="button" onClick={() => setGeminiModel('gemini-1.5-flash')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">gemini-1.5-flash</button>
                        <span>|</span>
                        <button type="button" onClick={() => setGeminiModel('gemini-1.5-pro')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">gemini-1.5-pro</button>
                        <span>|</span>
                        <button type="button" onClick={() => setGeminiModel('gemini-2.5-flash')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">gemini-2.5-flash</button>
                      </>
                    )}
                    {provider === 'openai' && (
                      <>
                        <button type="button" onClick={() => setOpenaiModel('gpt-4o-mini')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">gpt-4o-mini</button>
                        <span>|</span>
                        <button type="button" onClick={() => setOpenaiModel('gpt-4o')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">gpt-4o</button>
                      </>
                    )}
                    {provider === 'azure' && (
                      <>
                        <button type="button" onClick={() => setAzureModel('gpt-4o-mini')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">gpt-4o-mini (deployment)</button>
                        <span>|</span>
                        <button type="button" onClick={() => setAzureModel('gpt-4o')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">gpt-4o (deployment)</button>
                      </>
                    )}
                    {provider === 'anthropic' && (
                      <>
                        <button type="button" onClick={() => setAnthropicModel('claude-3-5-sonnet-20241022')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">claude-3-5-sonnet</button>
                        <span>|</span>
                        <button type="button" onClick={() => setAnthropicModel('claude-3-opus-20240229')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">claude-3-opus</button>
                      </>
                    )}
                    {provider === 'groq' && (
                      <>
                        <button type="button" onClick={() => setGroqModel('llama-3.3-70b-versatile')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">llama-3.3-70b-versatile</button>
                        <span>|</span>
                        <button type="button" onClick={() => setGroqModel('llama-3.3-70b-specdec')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">llama-3.3-70b-specdec</button>
                        <span>|</span>
                        <button type="button" onClick={() => setGroqModel('llama-3.2-11b-vision-preview')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">llama-3.2-11b-vision</button>
                      </>
                    )}
                    {provider === 'grok' && (
                      <>
                        <button type="button" onClick={() => setGrokModel('grok-2-1212')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">grok-2-1212</button>
                        <span>|</span>
                        <button type="button" onClick={() => setGrokModel('grok-2-vision-1212')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">grok-2-vision</button>
                      </>
                    )}
                    {provider === 'openrouter' && (
                      <>
                        <button type="button" onClick={() => setOpenrouterModel('google/gemini-2.5-flash:free')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">gemini-2.5-flash:free</button>
                        <span>|</span>
                        <button type="button" onClick={() => setOpenrouterModel('meta-llama/llama-3.3-70b-instruct:free')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">llama-3.3:free</button>
                        <span>|</span>
                        <button type="button" onClick={() => setOpenrouterModel('deepseek/deepseek-chat:free')} className="text-indigo-500 dark:text-indigo-400 hover:underline font-medium">deepseek:free</button>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="space-y-2 relative">
                <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">API Key</label>
                <div className="relative">
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={getActiveApiKey()}
                    onChange={(e) => setActiveApiKey(e.target.value)}
                    placeholder={provider === 'azure' ? 'Enter Azure OpenAI Key...' : `Enter your ${provider.toUpperCase()} API credentials...`}
                    className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-4 pr-12 py-3.5 text-sm text-slate-850 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-gray-400 dark:placeholder:text-gray-600"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 dark:text-gray-500 hover:text-slate-600 dark:hover:text-gray-300"
                  >
                    {showKey ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {/* DYNAMIC AZURE OPENAI DEDICATED INPUT FIELDS */}
              {provider === 'azure' && (
                <div className="grid grid-cols-2 gap-6 animate-fadeIn">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Azure Endpoint URL</label>
                    <input
                      type="text"
                      value={azureEndpoint}
                      onChange={(e) => setAzureEndpoint(e.target.value)}
                      placeholder="https://my-company-resource.openai.azure.com/"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-xs text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono placeholder:text-gray-400 dark:placeholder:text-gray-600"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Azure API Version</label>
                    <input
                      type="text"
                      value={azureApiVersion}
                      onChange={(e) => setAzureApiVersion(e.target.value)}
                      placeholder="e.g. 2023-05-15"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-xs text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                      required
                    />
                  </div>
                </div>
              )}

              {/* Test LLM Connection Action Row */}
              <div className="pt-4 border-t border-slate-100 dark:border-gray-850 flex flex-wrap gap-4 items-center justify-between select-none">
                <button
                  type="button"
                  onClick={handleTestLLMConnection}
                  disabled={testingConn || !getActiveApiKey()}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs px-5 py-3 rounded-xl flex items-center gap-2 transition-all active:scale-[0.96]"
                >
                  {testingConn ? <RefreshCw size={14} className="animate-spin" /> : <ShieldCheck size={14} />}
                  <span>{testingConn ? 'Testing LLM Credentials...' : 'Test LLM Connection'}</span>
                </button>

                {llmConnStatus && (
                  <div className={`flex-1 p-3.5 border rounded-xl flex items-center gap-2.5 animate-fadeIn text-xs leading-relaxed max-w-xl ${
                    llmConnStatus.success 
                      ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-600 dark:text-emerald-400' 
                      : 'bg-rose-500/10 border-rose-500/25 text-rose-600 dark:text-rose-400'
                  }`}>
                    {llmConnStatus.success ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                    <span>{llmConnStatus.message}</span>
                  </div>
                )}
              </div>

              {/* Browser Headers Configuration for Login Support */}
              <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-gray-850">
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

              {/* Chrome Profile Path Configuration for Persistent session login bypasses */}
              <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-gray-850">
                <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Persistent Browser Profile Path (Edge / Chrome Optional)</label>
                <input
                  type="text"
                  value={chromeProfile}
                  onChange={(e) => setChromeProfile(e.target.value)}
                  placeholder="e.g. C:\Users\suraj.yadav\AppData\Local\Microsoft\Edge\User Data"
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors font-mono text-xs placeholder:text-gray-400 dark:placeholder:text-gray-600"
                />
                <p className="text-[10px] text-slate-400 dark:text-gray-500 leading-normal">
                  * Bypasses strict Microsoft/Okta SSO login walls entirely by launching Playwright using your active, authenticated manual Microsoft Edge or Google Chrome session profile directory.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Card 2: Dynamic Issue Tracker settings (Collapsible Accordion!) */}
        <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-2xl p-8 space-y-6 transition-all shadow-sm">
          <div 
            onClick={() => setBugOpen(!bugOpen)}
            className="flex items-center justify-between border-b border-slate-100 dark:border-gray-800 pb-4 cursor-pointer select-none group"
            title="Click to Collapse or Expand Bug Tracker integration settings"
          >
            <div className="flex flex-col md:flex-row md:items-center gap-4">
              <h2 className="text-lg font-bold text-slate-800 dark:text-white">💼 Bug Tracker Integration Settings</h2>
              
              {bugOpen && (
                <div className="flex items-center gap-3" onClick={(e) => e.stopPropagation()}>
                  <span className="text-xs font-bold text-slate-400 dark:text-gray-500">Platform:</span>
                  <select
                    value={bugExportTarget}
                    onChange={(e) => {
                      setBugExportTarget(e.target.value)
                      setConnStatus(null) // reset conn verification on target shift
                    }}
                    className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-lg px-3 py-1.5 text-xs font-bold text-indigo-500 dark:text-indigo-400 focus:outline-none focus:border-indigo-500 cursor-pointer"
                  >
                    <option value="jira">Atlassian JIRA Cloud</option>
                    <option value="azure_devops">Azure DevOps Boards</option>
                    <option value="github">GitHub Issues</option>
                    <option value="gitlab">GitLab Issues</option>
                  </select>
                </div>
              )}
            </div>
            
            <div className="text-slate-400 group-hover:text-indigo-500 dark:group-hover:text-indigo-400 transition-colors">
              {bugOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </div>
          </div>
          
          {bugOpen && (
            <div className="space-y-6 animate-fadeIn">
              {/* 1. Jira Fields */}
              {bugExportTarget === 'jira' && (
                <div className="space-y-6 animate-fadeIn">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Jira Domain Workspace</label>
                      <div className="flex items-center">
                        <input
                          type="text"
                          value={jiraDomain}
                          onChange={(e) => setJiraDomain(e.target.value)}
                          placeholder="my-company"
                          className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-l-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors"
                        />
                        <span className="bg-slate-200 border-t border-b border-r border-slate-200 dark:bg-gray-800 dark:border-gray-850 rounded-r-xl px-4 py-3.5 text-sm font-semibold text-slate-500 dark:text-gray-400 select-none shrink-0">
                          .atlassian.net
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Project Key</label>
                      <input
                        type="text"
                        value={jiraProject}
                        onChange={(e) => setJiraProject(e.target.value)}
                        placeholder="e.g. PROJ"
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500 uppercase"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Account Email</label>
                      <input
                        type="email"
                        value={jiraEmail}
                        onChange={(e) => setJiraEmail(e.target.value)}
                        placeholder="your-atlassian-email@company.com"
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <div className="space-y-2 relative">
                      <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">JIRA API Token</label>
                      <div className="relative">
                        <input
                          type={showJiraToken ? 'text' : 'password'}
                          value={jiraToken}
                          onChange={(e) => setJiraToken(e.target.value)}
                          placeholder="Enter JIRA API Token..."
                          className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-4 pr-12 py-3.5 text-sm text-slate-850 dark:text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                        <button
                          type="button"
                          onClick={() => setShowJiraToken(!showJiraToken)}
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 dark:text-gray-500"
                        >
                          {showJiraToken ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 2. Azure DevOps Fields */}
              {bugExportTarget === 'azure_devops' && (
                <div className="space-y-6 animate-fadeIn">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Organization Name</label>
                      <input
                        type="text"
                        value={adoOrg}
                        onChange={(e) => setAdoOrg(e.target.value)}
                        placeholder="e.g. my-organization"
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Project Name</label>
                      <input
                        type="text"
                        value={adoProj}
                        onChange={(e) => setAdoProject(e.target.value)}
                        placeholder="e.g. MyProject"
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>

                  <div className="space-y-2 relative">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Personal Access Token (PAT)</label>
                    <div className="relative">
                      <input
                        type={showAdoPat ? 'text' : 'password'}
                        value={adoPat}
                        onChange={(e) => setAdoPat(e.target.value)}
                        placeholder="Enter Azure DevOps PAT..."
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-4 pr-12 py-3.5 text-sm text-slate-850 dark:text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                      <button
                        type="button"
                        onClick={() => setShowAdoPat(!showAdoPat)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 dark:text-gray-500"
                      >
                        {showAdoPat ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* 3. GitHub Fields */}
              {bugExportTarget === 'github' && (
                <div className="space-y-6 animate-fadeIn">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Repository Owner</label>
                      <input
                        type="text"
                        value={githubOwner}
                        onChange={(e) => setGithubOwner(e.target.value)}
                        placeholder="e.g. octocat"
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">Repository Name</label>
                      <input
                        type="text"
                        value={githubRepo}
                        onChange={(e) => setGithubRepo(e.target.value)}
                        placeholder="e.g. Hello-World"
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>

                  <div className="space-y-2 relative">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">GitHub Personal Access Token (PAT)</label>
                    <div className="relative">
                      <input
                        type={showGithubPat ? 'text' : 'password'}
                        value={githubPat}
                        onChange={(e) => setGithubPat(e.target.value)}
                        placeholder="Enter GitHub PAT (with 'repo' scope)..."
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-4 pr-12 py-3.5 text-sm text-slate-850 dark:text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                      <button
                        type="button"
                        onClick={() => setShowGithubPat(!showGithubPat)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 dark:text-gray-500"
                      >
                        {showGithubPat ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* 4. GitLab Fields */}
              {bugExportTarget === 'gitlab' && (
                <div className="space-y-6 animate-fadeIn">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">GitLab Project ID or URL-encoded Path</label>
                    <input
                      type="text"
                      value={gitlabProjectId}
                      onChange={(e) => setGitlabProjectId(e.target.value)}
                      placeholder="e.g. 123456 or owner/my-project"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div className="space-y-2 relative">
                    <label className="text-sm font-semibold text-slate-700 dark:text-gray-300">GitLab Personal Access Token (PAT)</label>
                    <div className="relative">
                      <input
                        type={showGitlabPat ? 'text' : 'password'}
                        value={gitlabPat}
                        onChange={(e) => setGitlabPat(e.target.value)}
                        placeholder="Enter GitLab PAT (with 'api' scope)..."
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-4 pr-12 py-3.5 text-sm text-slate-850 dark:text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                      <button
                        type="button"
                        onClick={() => setShowGitlabPat(!showGitlabPat)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 dark:text-gray-500"
                      >
                        {showGitlabPat ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Connection status display banners */}
              {connStatus && (
                <div className={`p-4 rounded-xl border flex items-start gap-3.5 animate-fadeIn select-none ${
                  connStatus.status === 'success'
                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                    : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
                }`}>
                  {connStatus.status === 'success' ? <CheckCircle size={18} className="shrink-0 mt-0.5 text-emerald-400" /> : <AlertCircle size={18} className="shrink-0 mt-0.5 text-rose-400" />}
                  <div>
                    <h4 className="font-bold text-sm leading-none">{connStatus.status === 'success' ? 'Connection Verified Successfully! ✅' : 'Connection Failed! ❌'}</h4>
                    <p className="text-xs mt-1 leading-relaxed opacity-90">{connStatus.message}</p>
                  </div>
                </div>
              )}

              {/* Card footer: Test Connection button */}
              <div className="flex justify-end pt-2 select-none">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testingConn}
                  className="bg-slate-100 hover:bg-slate-200 dark:bg-gray-800 dark:hover:bg-gray-750 text-slate-700 dark:text-gray-200 font-bold text-xs px-6 py-3 rounded-xl flex items-center gap-2 active:scale-[0.98] transition-all"
                >
                  {testingConn ? <RefreshCw size={14} className="animate-spin" /> : <ShieldCheck size={14} />}
                  <span>{testingConn ? 'Verifying Link...' : 'Verify Tracker Connection'}</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Action Button for LocalStorage */}
        <div className="flex items-center justify-end border-b border-slate-200 dark:border-gray-850 pb-8 select-none">
          <button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm px-8 py-3.5 rounded-xl shadow-lg shadow-indigo-500/10 flex items-center gap-2.5 active:scale-[0.98] transition-all duration-200"
          >
            <Save size={16} />
            <span>{saved ? 'Settings Saved Successfully!' : 'Save System Credentials'}</span>
          </button>
        </div>
      </form>

      {/* Card 3: GORGEOUS LIVE SYSTEM PROMPT CONFIGURATION EDITOR (Collapsible Accordion!) */}
      <form onSubmit={handleSavePrompts} className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-2xl p-8 space-y-6 transition-all shadow-sm animate-fadeIn">
        <div 
          onClick={() => setPromptOpen(!promptOpen)}
          className="flex items-center justify-between border-b border-slate-100 dark:border-gray-800 pb-4 cursor-pointer select-none group"
          title="Click to Collapse or Expand Prompts Config console"
        >
          <div className="flex flex-col md:flex-row md:items-center gap-4">
            <h2 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
              <Code2 size={20} className="text-indigo-500 dark:text-indigo-400" />
              <span>📜 Live System Prompt Engineering Console</span>
            </h2>
            
            {/* Dropdown to choose which prompt file to view & edit */}
            {promptOpen && (
              <div className="flex items-center gap-3" onClick={(e) => e.stopPropagation()}>
                <span className="text-xs font-bold text-slate-400 dark:text-gray-500 select-none">Editing File:</span>
                <select
                  value={selectedPromptFile}
                  onChange={(e) => setSelectedPromptFile(e.target.value)}
                  className="bg-slate-100 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-lg px-3 py-1.5 text-xs font-bold text-indigo-500 dark:text-indigo-400 focus:outline-none focus:border-indigo-500 cursor-pointer transition-colors"
                >
                  <option value="CombinedPrompt.txt">CombinedPrompt.txt (TestCase Generator)</option>
                  <option value="UIPrompt.txt">UIPrompt.txt (UI Tests)</option>
                  <option value="FunctionalPrompt.txt">FunctionalPrompt.txt (Functional Tests)</option>
                  <option value="BugReportPrompt.txt">BugReportPrompt.txt (Visual Bug Analyzer)</option>
                  <option value="PlaywrightBootstrap.txt">PlaywrightBootstrap.txt (Playwright Scaffolder)</option>
                  <option value="SeleniumBootstrap.txt">SeleniumBootstrap.txt (Selenium Scaffolder)</option>
                  <option value="CypressBootstrap.txt">CypressBootstrap.txt (Cypress Scaffolder)</option>
                  <option value="AutomationFileGen.txt">AutomationFileGen.txt (SDET File Generator)</option>
                </select>
              </div>
            )}
          </div>
          <div className="text-slate-400 group-hover:text-indigo-500 dark:group-hover:text-indigo-400 transition-colors">
            {promptOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </div>
        </div>

        {promptOpen && (
          <div className="space-y-6 animate-fadeIn">
            <p className="text-sm text-slate-500 dark:text-gray-400 leading-relaxed">
              Inspect, adjust, and re-engineer the system prompts used by your AI agents in real-time. 
              Modify the boundaries, instructions, or strict JSON structures of <code className="bg-slate-100 dark:bg-gray-950 px-1.5 py-0.5 rounded font-bold text-indigo-500 dark:text-indigo-400">{selectedPromptFile}</code>. 
              Clicking="Publish Prompt Edits" writes the changes directly back to its physical file inside **`backend/app/prompts/`** dynamically.
            </p>

            <div className="space-y-1">
              <textarea
                value={promptsText}
                onChange={(e) => setPromptsText(e.target.value)}
                rows={15}
                className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 p-4 rounded-xl font-mono text-xs text-slate-700 dark:text-gray-300 focus:outline-none focus:border-indigo-500 leading-relaxed resize-y shadow-inner transition-all"
                required
                placeholder="Loading prompts configuration..."
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <p className="text-[10px] text-slate-400 dark:text-gray-500 select-none">
                * Ensure the <code className="bg-slate-100 dark:bg-gray-950 px-1.5 py-0.5 rounded font-bold">{`{requirements}`}</code> placeholder is preserved inside the file to support runtime dynamic text injection.
              </p>
              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm px-8 py-3.5 rounded-xl shadow-lg shadow-indigo-500/10 flex items-center gap-2.5 active:scale-[0.98] transition-all duration-200"
              >
                <Save size={16} />
                <span>{promptsSaved ? 'Prompt Updated successfully!' : 'Publish Prompt Edits'}</span>
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  )
}

export default Settings
