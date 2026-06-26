import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { LayoutDashboard, Eye, ClipboardList, Bug, Code2, Settings as SettingsIcon, ScrollText, Sun, Moon, ChevronLeft, ChevronRight, HelpCircle } from 'lucide-react'

// Components
import Dashboard from './components/Dashboard'
import RegressionModule from './components/RegressionModule'
import TestCaseModule from './components/TestCaseModule'
import BugReporterModule from './components/BugReporterModule'
import Settings from './components/Settings'
import AutomationModule from './components/AutomationModule'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark')
  
  // Symmetrical dynamic guide states
  const [showGuide, setShowGuide] = useState(false)
  const [guideContent, setGuideContent] = useState('')
  
  // Sidebar collapsible state persisted in local storage
  const [isCollapsed, setIsCollapsed] = useState(localStorage.getItem('sidebar_collapsed') === 'true')

  useEffect(() => {
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    localStorage.setItem('sidebar_collapsed', isCollapsed)
  }, [isCollapsed])

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed)
  }

  // Symmetrical Global Dynamic User Guide Handler
  const handleOpenGuide = async () => {
    setShowGuide(true)
    setGuideContent('Loading step-by-step user guide from disk...')
    
    let filename = 'VisualTestingGuide.md'
    if (activeTab === 'testcases') {
      filename = 'TestCaseGuide.md'
    } else if (activeTab === 'bugreporter') {
      filename = 'BugReporterGuide.md'
    } else if (activeTab === 'automation') {
      filename = 'AutomationGuide.md'
    } else if (activeTab === 'settings') {
      filename = 'ConfigurationGuide.md'
    } else if (activeTab === 'dashboard') {
      filename = 'VisualTestingGuide.md' // Fallback
    } else {
      setShowGuide(false)
      return
    }

    try {
      const response = await axios.get(`http://127.0.0.1:5000/static/guides/${filename}`)
      setGuideContent(response.data)
    } catch (err) {
      setGuideContent('### ❌ Failed to load guide file from static storage on server disk. Please check your folder structure.')
    }
  }

  return (
    <div className={`${theme === 'dark' ? 'dark' : ''} flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-gray-950 text-slate-800 dark:text-gray-100 font-sans transition-colors duration-200`}>
      {/* Sidebar navigation */}
      <aside className={`${isCollapsed ? 'w-20' : 'w-72'} bg-white dark:bg-gray-900 border-r border-slate-200 dark:border-gray-800 flex flex-col shrink-0 select-none transition-all duration-300 relative`}>
        
        {/* Brand Header with Interactive Logo Toggle */}
        <div className={`h-20 flex items-center border-b border-slate-200 dark:border-gray-800 shrink-0 relative overflow-hidden transition-all ${
          isCollapsed ? 'justify-center px-0' : 'px-6 justify-start gap-3.5'
        }`}>
          {/* Interactive Toggle Logo */}
          <div 
            onClick={toggleSidebar}
            className="w-10 h-10 bg-indigo-600 hover:bg-indigo-500 rounded-xl flex items-center justify-center font-bold text-xl text-white shadow-lg shadow-indigo-500/20 shrink-0 select-none cursor-pointer transition-all duration-200 group"
            title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {/* Show 'QA' text by default, show arrow icon on hover */}
            <span className="block group-hover:hidden select-none animate-fadeIn">QA</span>
            <span className="hidden group-hover:block select-none animate-fadeIn">
              {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
            </span>
          </div>

          {!isCollapsed && (
            <div className="animate-fadeIn">
              <h1 className="font-bold text-base leading-tight tracking-wide text-slate-900 dark:text-white">QA AI Platform</h1>
              <p className="text-[10px] text-indigo-500 dark:text-indigo-400 font-bold tracking-wider uppercase">Smart Testing Suite</p>
            </div>
          )}
        </div>

        {/* Navigation Items */}
        <nav className={`flex-1 py-6 px-3 space-y-1.5 ${isCollapsed ? '' : 'overflow-y-auto'}`}>
          {/* Item 1: Dashboard */}
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`group relative flex items-center rounded-xl font-medium text-sm transition-all duration-200 w-full ${
              isCollapsed ? 'p-3.5 justify-center' : 'px-4 py-3 justify-start gap-3.5'
            } ${
              activeTab === 'dashboard'
                ? 'bg-indigo-600/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 dark:border-indigo-500/10 font-semibold shadow-inner'
                : 'text-slate-500 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-gray-800/50 hover:text-slate-800 dark:hover:text-gray-200 border border-transparent'
            }`}
          >
            <LayoutDashboard size={18} className="shrink-0" />
            {!isCollapsed && <span className="animate-fadeIn">Dashboard Overview</span>}
            
            {/* Custom Tailwind hover tooltip when collapsed */}
            {isCollapsed && (
              <span className="absolute left-16 scale-0 group-hover:scale-100 transition-all duration-150 rounded-lg bg-gray-900 border border-gray-800 p-2.5 text-xs text-white font-semibold shadow-xl pointer-events-none select-none z-50 whitespace-nowrap">
                Dashboard Overview
              </span>
            )}
          </button>

          {/* Item 2: Regression */}
          <button
            onClick={() => setActiveTab('regression')}
            className={`group relative flex items-center rounded-xl font-medium text-sm transition-all duration-200 w-full ${
              isCollapsed ? 'p-3.5 justify-center' : 'px-4 py-3 justify-start gap-3.5'
            } ${
              activeTab === 'regression'
                ? 'bg-indigo-600/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 dark:border-indigo-500/10 font-semibold shadow-inner'
                : 'text-slate-500 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-gray-800/50 hover:text-slate-800 dark:hover:text-gray-200 border border-transparent'
            }`}
          >
            <Eye size={18} className="shrink-0" />
            {!isCollapsed && <span className="animate-fadeIn">Smart Visual testing</span>}
            
            {isCollapsed && (
              <span className="absolute left-16 scale-0 group-hover:scale-100 transition-all duration-150 rounded-lg bg-gray-900 border border-gray-800 p-2.5 text-xs text-white font-semibold shadow-xl pointer-events-none select-none z-50 whitespace-nowrap">
                Smart Visual testing
              </span>
            )}
          </button>

          {/* Item 3: Test Case Generator */}
          <button
            onClick={() => setActiveTab('testcases')}
            className={`group relative flex items-center rounded-xl font-medium text-sm transition-all duration-200 w-full ${
              isCollapsed ? 'p-3.5 justify-center' : 'px-4 py-3 justify-start gap-3.5'
            } ${
              activeTab === 'testcases'
                ? 'bg-indigo-600/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 dark:border-indigo-500/10 font-semibold shadow-inner'
                : 'text-slate-500 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-gray-800/50 hover:text-slate-800 dark:hover:text-gray-200 border border-transparent'
            }`}
          >
            <ClipboardList size={18} className="shrink-0" />
            {!isCollapsed && <span className="animate-fadeIn">Auto TestCase generator</span>}
            
            {isCollapsed && (
              <span className="absolute left-16 scale-0 group-hover:scale-100 transition-all duration-150 rounded-lg bg-gray-900 border border-gray-800 p-2.5 text-xs text-white font-semibold shadow-xl pointer-events-none select-none z-50 whitespace-nowrap">
                Auto TestCase generator
              </span>
            )}
          </button>

          {/* Item 4: Bug Reporter */}
          <button
            onClick={() => setActiveTab('bugreporter')}
            className={`group relative flex items-center rounded-xl font-medium text-sm transition-all duration-200 w-full ${
              isCollapsed ? 'p-3.5 justify-center' : 'px-4 py-3 justify-start gap-3.5'
            } ${
              activeTab === 'bugreporter'
                ? 'bg-indigo-600/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 dark:border-indigo-500/10 font-semibold shadow-inner'
                : 'text-slate-500 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-gray-800/50 hover:text-slate-800 dark:hover:text-gray-200 border border-transparent'
            }`}
          >
            <Bug size={18} className="shrink-0" />
            {!isCollapsed && <span className="animate-fadeIn">Visual Bug Reporter</span>}
            
            {isCollapsed && (
              <span className="absolute left-16 scale-0 group-hover:scale-100 transition-all duration-150 rounded-lg bg-gray-900 border border-gray-800 p-2.5 text-xs text-white font-semibold shadow-xl pointer-events-none select-none z-50 whitespace-nowrap">
                Visual Bug Reporter
              </span>
            )}
          </button>

          {/* Item 5: Automation Architect (Agent 4) */}
          <button
            onClick={() => setActiveTab('automation')}
            className={`group relative flex items-center rounded-xl font-medium text-sm transition-all duration-200 w-full ${
              isCollapsed ? 'p-3.5 justify-center' : 'px-4 py-3 justify-start gap-3.5'
            } ${
              activeTab === 'automation'
                ? 'bg-indigo-600/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 dark:border-indigo-500/10 font-semibold shadow-inner'
                : 'text-slate-500 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-gray-800/50 hover:text-slate-800 dark:hover:text-gray-200 border border-transparent'
            }`}
          >
            <Code2 size={18} className="shrink-0" />
            {!isCollapsed && <span className="animate-fadeIn">Automation Architect</span>}
            
            {isCollapsed && (
              <span className="absolute left-16 scale-0 group-hover:scale-100 transition-all duration-150 rounded-lg bg-gray-900 border border-gray-800 p-2.5 text-xs text-white font-semibold shadow-xl pointer-events-none select-none z-50 whitespace-nowrap">
                Automation Architect
              </span>
            )}
          </button>
        </nav>

        {/* Footer/Settings button */}
        {!isCollapsed && (
          <div className="p-4 border-t border-slate-200 dark:border-gray-800 shrink-0 bg-slate-50/50 dark:bg-gray-900/50 transition-colors duration-200">
            <button
              onClick={() => setActiveTab('settings')}
              className={`flex items-center gap-3.5 w-full px-4 py-3.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                activeTab === 'settings'
                  ? 'bg-indigo-600/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 dark:border-indigo-500/10 font-semibold shadow-inner'
                  : 'text-slate-500 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-gray-800/50 hover:text-slate-800 dark:hover:text-gray-200'
              }`}
            >
              <SettingsIcon size={18} />
              <span>Configuration Panel</span>
            </button>
          </div>
        )}

        {/* If collapsed, show settings as an icon only with tooltip */}
        {isCollapsed && (
          <div className="p-3.5 border-t border-slate-200 dark:border-gray-800 shrink-0 bg-slate-50/50 dark:bg-gray-900/50 flex justify-center transition-colors duration-200">
            <button
              onClick={() => setActiveTab('settings')}
              className={`group relative p-3.5 rounded-xl font-medium text-sm transition-all duration-200 flex justify-center ${
                activeTab === 'settings'
                  ? 'bg-indigo-600/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 dark:border-indigo-500/10 font-semibold shadow-inner'
                  : 'text-slate-500 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-gray-800/50 hover:text-slate-800 dark:hover:text-gray-200 border border-transparent'
              }`}
            >
              <SettingsIcon size={18} className="shrink-0" />
              <span className="absolute left-16 scale-0 group-hover:scale-100 transition-all duration-150 rounded-lg bg-gray-900 border border-gray-800 p-2.5 text-xs text-white font-semibold shadow-xl pointer-events-none select-none z-50 whitespace-nowrap">
                ⚙️ Configuration Panel
              </span>
            </button>
          </div>
        )}
      </aside>

      {/* Main viewport area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50 dark:bg-gray-950 transition-colors duration-200">
        <header className="h-20 bg-white dark:bg-gray-900 border-b border-slate-200 dark:border-gray-800 px-8 flex items-center justify-between shrink-0 select-none transition-colors duration-200">
          <h2 className="text-xl font-bold tracking-tight text-slate-800 dark:text-white capitalize">
            {activeTab === 'testcases' ? 'Auto TestCase generator' : activeTab === 'bugreporter' ? 'Visual Bug Reporter' : activeTab === 'regression' ? 'Smart Visual testing' : activeTab === 'settings' ? 'Configuration Panel' : activeTab === 'automation' ? 'Automation Architect' : 'Dashboard Overview'}
          </h2>
          <div className="flex items-center gap-6">
            {/* Global Dynamic User Guide Button - High Visibility Pill */}
            <button
              type="button"
              onClick={handleOpenGuide}
              className="bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-indigo-500 dark:text-indigo-400 transition-all flex items-center gap-1.5 text-xs font-extrabold px-3.5 py-2.5 rounded-xl shadow-sm active:scale-[0.95]"
              title={`Open step-by-step non-technical User Guide for active tab`}
            >
              <HelpCircle size={14} />
              <span>User Guide</span>
            </button>

            {/* Dynamic Theme Toggle Switch */}
            <button
              onClick={toggleTheme}
              className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-slate-600 hover:text-slate-800 dark:text-gray-300 dark:hover:text-white transition-all active:scale-[0.95]"
              title="Toggle Theme Mode"
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <div className="flex items-center gap-4">
              <span className="flex h-2.5 w-2.5 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 bg-emerald-500/5 border border-emerald-500/10 px-3 py-1 rounded-full">
                Live Core Engine Connected
              </span>
            </div>
          </div>
        </header>

        {/* Interactive Workspace Area */}
        <section className="flex-1 overflow-y-auto p-8 max-w-[1600px] w-full mx-auto animate-fadeIn">
          {activeTab === 'dashboard' && <Dashboard setActiveTab={setActiveTab} />}
          {activeTab === 'regression' && <RegressionModule />}
          {activeTab === 'testcases' && <TestCaseModule />}
          {activeTab === 'bugreporter' && <BugReporterModule />}
          {activeTab === 'settings' && <Settings />}
          {activeTab === 'automation' && <AutomationModule />}
        </section>
      </main>

      {/* Global Dynamic User Guide Lightbox Modal */}
      {showGuide && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6 animate-fadeIn select-none">
          <div className="relative w-full max-w-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-2xl shadow-2xl p-8 max-h-[85vh] overflow-y-auto space-y-6">
            <div className="border-b border-slate-200 dark:border-gray-800 pb-4 flex items-center justify-between">
              <h3 className="font-bold text-lg text-slate-800 dark:text-white flex items-center gap-2">
                <HelpCircle className="text-indigo-500 animate-pulse" size={20} />
                <span className="capitalize">{activeTab === 'testcases' ? 'Auto TestCase generator' : activeTab === 'bugreporter' ? 'Visual Bug Reporter' : activeTab === 'regression' ? 'Smart Visual testing' : activeTab === 'automation' ? 'Automation Architect' : 'Dashboard Overview'} Guide</span>
              </h3>
              <button 
                onClick={() => setShowGuide(false)}
                className="text-slate-400 dark:text-gray-500 hover:text-slate-600 dark:hover:text-gray-300 text-xs font-bold px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-gray-800 transition-colors"
              >
                Close Guide
              </button>
            </div>
            
            <div className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-850 p-6 rounded-xl font-sans text-xs text-slate-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap select-text h-[400px] overflow-y-auto shadow-inner">
              {guideContent}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
