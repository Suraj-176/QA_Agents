import React, { useState } from 'react'
import { LayoutDashboard, Eye, ClipboardList, Bug, Settings as SettingsIcon } from 'lucide-react'

// Components
import Dashboard from './components/Dashboard'
import RegressionModule from './components/RegressionModule'
import TestCaseModule from './components/TestCaseModule'
import BugReporterModule from './components/BugReporterModule'
import Settings from './components/Settings'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-950 text-gray-100 font-sans">
      {/* Sidebar navigation */}
      <aside className="w-72 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0 select-none">
        {/* Brand Header */}
        <div className="h-20 flex items-center px-6 gap-3 border-b border-gray-800 shrink-0">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center font-bold text-xl text-white shadow-lg shadow-indigo-500/20">
            QA
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight tracking-wide text-white">QA.AI Platform</h1>
            <p className="text-xs text-indigo-400 font-medium tracking-wider uppercase">Smart Testing Suite</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 py-6 px-4 space-y-1.5 overflow-y-auto">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-3.5 w-full px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200 ${
              activeTab === 'dashboard'
                ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 font-semibold shadow-inner shadow-indigo-500/5'
                : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
            }`}
          >
            <LayoutDashboard size={18} />
            <span>📊 Dashboard Overview</span>
          </button>

          <button
            onClick={() => setActiveTab('regression')}
            className={`flex items-center gap-3.5 w-full px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200 ${
              activeTab === 'regression'
                ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 font-semibold shadow-inner shadow-indigo-500/5'
                : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
            }`}
          >
            <Eye size={18} />
            <span>🔍 Smart Visual testing</span>
          </button>

          <button
            onClick={() => setActiveTab('testcases')}
            className={`flex items-center gap-3.5 w-full px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200 ${
              activeTab === 'testcases'
                ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 font-semibold shadow-inner shadow-indigo-500/5'
                : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
            }`}
          >
            <ClipboardList size={18} />
            <span>📋 Auto TestCase generator</span>
          </button>

          <button
            onClick={() => setActiveTab('bugreporter')}
            className={`flex items-center gap-3.5 w-full px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200 ${
              activeTab === 'bugreporter'
                ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 font-semibold shadow-inner shadow-indigo-500/5'
                : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
            }`}
          >
            <Bug size={18} />
            <span>🐛 Visual Bug Reporter</span>
          </button>
        </nav>

        {/* Footer/Settings button */}
        <div className="p-4 border-t border-gray-800 shrink-0 bg-gray-900/50">
          <button
            onClick={() => setActiveTab('settings')}
            className={`flex items-center gap-3.5 w-full px-4 py-3.5 rounded-xl font-medium text-sm transition-all duration-200 ${
              activeTab === 'settings'
                ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 font-semibold shadow-inner shadow-indigo-500/5'
                : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
            }`}
          >
            <SettingsIcon size={18} />
            <span>⚙️ Configuration Panel</span>
          </button>
        </div>
      </aside>

      {/* Main viewport area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-gray-950">
        <header className="h-20 bg-gray-900 border-b border-gray-800 px-8 flex items-center justify-between shrink-0 select-none">
          <h2 className="text-xl font-bold tracking-tight text-white capitalize">
            {activeTab === 'testcases' ? 'Auto TestCase generator' : activeTab === 'bugreporter' ? 'Visual Bug Reporter' : activeTab === 'regression' ? 'Smart Visual testing' : activeTab === 'settings' ? 'Configuration Panel' : 'Dashboard Overview'}
          </h2>
          <div className="flex items-center gap-4">
            <span className="flex h-2.5 w-2.5 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-500 bg-emerald-500/5 border border-emerald-500/10 px-3 py-1 rounded-full">
              Live Core Engine Connected
            </span>
          </div>
        </header>

        {/* Interactive Workspace Area */}
        <section className="flex-1 overflow-y-auto p-8 max-w-[1600px] w-full mx-auto">
          {activeTab === 'dashboard' && <Dashboard setActiveTab={setActiveTab} />}
          {activeTab === 'regression' && <RegressionModule />}
          {activeTab === 'testcases' && <TestCaseModule />}
          {activeTab === 'bugreporter' && <BugReporterModule />}
          {activeTab === 'settings' && <Settings />}
        </section>
      </main>
    </div>
  )
}

export default App
