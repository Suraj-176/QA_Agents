import React, { useState, useEffect } from 'react'
import { Save, ShieldCheck, Eye, EyeOff } from 'lucide-react'

function Settings() {
  const [provider, setProvider] = useState('gemini')
  const [model, setModel] = useState('gemini-1.5-flash')
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)

  // Jira configs
  const [jiraDomain, setJiraDomain] = useState('')
  const [jiraEmail, setJiraEmail] = useState('')
  const [jiraToken, setJiraToken] = useState('')
  const [showJiraToken, setShowJiraToken] = useState(false)
  const [jiraProject, setJiraProject] = useState('')

  const [saved, setSaved] = useState(false)

  // Load existing configs from localStorage on mount
  useEffect(() => {
    setProvider(localStorage.getItem('llm_provider') || 'gemini')
    setModel(localStorage.getItem('llm_model') || 'gemini-1.5-flash')
    setApiKey(localStorage.getItem('llm_api_key') || '')
    setJiraDomain(localStorage.getItem('jira_domain') || '')
    setJiraEmail(localStorage.getItem('jira_email') || '')
    setJiraToken(localStorage.getItem('jira_token') || '')
    setJiraProject(localStorage.getItem('jira_project') || '')
  }, [])

  // Auto update model options based on selected provider
  const handleProviderChange = (p) => {
    setProvider(p)
    if (p === 'gemini') {
      setModel('gemini-1.5-flash')
    } else if (p === 'openai') {
      setModel('gpt-4o-mini')
    } else if (p === 'anthropic') {
      setModel('claude-3-5-sonnet-20241022')
    }
  }

  const handleSave = (e) => {
    e.preventDefault()
    localStorage.setItem('llm_provider', provider)
    localStorage.setItem('llm_model', model)
    localStorage.setItem('llm_api_key', apiKey)
    localStorage.setItem('jira_domain', jiraDomain)
    localStorage.setItem('jira_email', jiraEmail)
    localStorage.setItem('jira_token', jiraToken)
    localStorage.setItem('jira_project', jiraProject)

    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
      {/* Privacy Notice Banner */}
      <div className="bg-indigo-600/10 border border-indigo-500/20 p-5 rounded-2xl flex items-start gap-4 shadow-sm">
        <ShieldCheck className="text-indigo-400 shrink-0 mt-0.5" size={24} />
        <div>
          <h3 className="font-bold text-indigo-200 text-base">"Bring Your Own Key" (BYOK) Architecture</h3>
          <p className="text-sm text-indigo-300/80 leading-relaxed mt-1">
            Your credentials are kept 100% private. All API keys and JIRA passwords are saved in your local browser storage. 
            They are never committed to any remote database. They are only sent in transient request headers to your local host server.
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-8">
        {/* LLM API configurations */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 space-y-6">
          <h2 className="text-lg font-bold text-white border-b border-gray-800 pb-4">🧠 Large Language Model (LLM) Settings</h2>
          
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-300">LLM Provider</label>
              <select
                value={provider}
                onChange={(e) => handleProviderChange(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3.5 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors"
              >
                <option value="gemini">Google Gemini AI</option>
                <option value="openai">OpenAI (GPT)</option>
                <option value="anthropic">Anthropic Claude</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-300">Selected Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3.5 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors"
              >
                {provider === 'gemini' && (
                  <>
                    <option value="gemini-1.5-flash">gemini-1.5-flash (Fast & Lightweight)</option>
                    <option value="gemini-1.5-pro">gemini-1.5-pro (Highly Logical)</option>
                  </>
                )}
                {provider === 'openai' && (
                  <>
                    <option value="gpt-4o-mini">gpt-4o-mini (Speed Optimized)</option>
                    <option value="gpt-4o">gpt-4o (Strongest Visual Auditor)</option>
                  </>
                )}
                {provider === 'anthropic' && (
                  <>
                    <option value="claude-3-5-sonnet-20241022">claude-3-5-sonnet (Industry Standard)</option>
                  </>
                )}
              </select>
            </div>
          </div>

          <div className="space-y-2 relative">
            <label className="text-sm font-semibold text-gray-300">API Key</label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={`Enter your ${provider.toUpperCase()} API credentials...`}
                className="w-full bg-gray-950 border border-gray-800 rounded-xl pl-4 pr-12 py-3.5 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-gray-600"
                required
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
              >
                {showKey ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
        </div>

        {/* Jira Cloud integration settings */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 space-y-6">
          <h2 className="text-lg font-bold text-white border-b border-gray-800 pb-4">💼 Atlassian JIRA Cloud Settings (Optional)</h2>
          
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-300">Jira Domain Workspace</label>
              <div className="flex items-center">
                <input
                  type="text"
                  value={jiraDomain}
                  onChange={(e) => setJiraDomain(e.target.value)}
                  placeholder="my-company"
                  className="w-full bg-gray-950 border border-gray-800 rounded-l-xl px-4 py-3.5 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-gray-600"
                />
                <span className="bg-gray-800 border-t border-b border-r border-gray-800 rounded-r-xl px-4 py-3.5 text-sm font-semibold text-gray-400 select-none shrink-0">
                  .atlassian.net
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-300">Project Key</label>
              <input
                type="text"
                value={jiraProject}
                onChange={(e) => setJiraProject(e.target.value)}
                placeholder="e.g. PROJ"
                className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3.5 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-gray-600 uppercase"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-300">Account Email</label>
              <input
                type="email"
                value={jiraEmail}
                onChange={(e) => setJiraEmail(e.target.value)}
                placeholder="your-atlassian-email@company.com"
                className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3.5 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-gray-600"
              />
            </div>

            <div className="space-y-2 relative">
              <label className="text-sm font-semibold text-gray-300">JIRA API Token</label>
              <div className="relative">
                <input
                  type={showJiraToken ? 'text' : 'password'}
                  value={jiraToken}
                  onChange={(e) => setJiraToken(e.target.value)}
                  placeholder="Enter JIRA API Token..."
                  className="w-full bg-gray-950 border border-gray-800 rounded-xl pl-4 pr-12 py-3.5 text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-gray-600"
                />
                <button
                  type="button"
                  onClick={() => setShowJiraToken(!showJiraToken)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showJiraToken ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-end">
          <button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm px-8 py-3.5 rounded-xl shadow-lg shadow-indigo-500/10 flex items-center gap-2.5 active:scale-[0.98] transition-all duration-200"
          >
            <Save size={16} />
            <span>{saved ? 'Configurations Saved!' : 'Save Configurations'}</span>
          </button>
        </div>
      </form>
    </div>
  )
}

export default Settings
