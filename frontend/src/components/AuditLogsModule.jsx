import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { ScrollText, RefreshCw, FileSpreadsheet, Trash, Search, ChevronRight } from 'lucide-react'

const API_BASE_URL = 'http://127.0.0.1:5000/api'

function AuditLogsModule() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [actionFilter, setActionFilter] = useState('all')

  useEffect(() => {
    fetchLogs()
  }, [])

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_BASE_URL}/audit-logs/`)
      setLogs(response.data)
    } catch (err) {
      console.error('Failed to fetch system audit logs:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleClearLogs = async () => {
    if (!confirm('Are you sure you want to permanently clear all system audit logs? This action is irreversible.')) return
    setLoading(true)
    try {
      await axios.delete(`${API_BASE_URL}/audit-logs/clear`)
      setLogs([])
    } catch (err) {
      alert(`Clear logs failed: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleExportCSV = () => {
    if (logs.length === 0) {
      alert('There are no audit logs to export.')
      return
    }

    // Format headers and rows cleanly
    const headers = ['Log ID', 'Action Category', 'Details', 'Timestamp']
    const rows = filteredLogs.map(log => [
      log.id,
      log.action,
      `"${log.details.replace(/"/g, '""')}"`, // escape double quotes for CSV
      new Date(log.created_at).toLocaleString()
    ])

    const csvContent = [headers, ...rows].map(e => e.join(',')).join('\n')
    
    // Add UTF-8 BOM to support perfect Microsoft Excel encoding formats
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `QA_AI_Platform_Audit_Logs_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Filter logs dynamically based on search query and action category selection
  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.details.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          log.action.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = actionFilter === 'all' || log.action === actionFilter
    return matchesSearch && matchesCategory
  })

  // Format Action labels with stylized colors
  const getActionBadge = (action) => {
    switch (action) {
      case 'visual_testing':
        return (
          <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/10">
            🔍 Visual testing
          </span>
        )
      case 'testcase_generator':
        return (
          <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/10">
            📋 TestCase Creator
          </span>
        )
      case 'bug_reporter':
        return (
          <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/10">
            🐛 Bug Reporter
          </span>
        )
      case 'config':
        return (
          <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/10">
            ⚙️ System Config
          </span>
        )
      default:
        return (
          <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-gray-500/10 text-gray-400 border border-gray-500/10">
            💻 System Info
          </span>
        )
    }
  }

  return (
    <div className="space-y-8 animate-fadeIn select-none text-slate-800 dark:text-white">
      {/* Search and Action Filtering Header card */}
      <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-2xl p-6 flex flex-wrap gap-5 items-center justify-between shadow-sm transition-all">
        <div className="flex items-center gap-4 flex-1 min-w-[300px]">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 dark:text-gray-500" size={16} />
            <input
              type="text"
              placeholder="Search logs details or actions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-11 pr-4 py-2.5 text-xs text-slate-800 dark:text-gray-200 placeholder-slate-400 dark:placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          {/* Category Dropdown */}
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-2.5 text-xs font-semibold text-slate-650 dark:text-gray-400 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="all" className="bg-white dark:bg-gray-950">All Action Categories</option>
            <option value="visual_testing" className="bg-white dark:bg-gray-950">🔍 Visual Testing</option>
            <option value="testcase_generator" className="bg-white dark:bg-gray-950">📋 TestCase Creator</option>
            <option value="bug_reporter" className="bg-white dark:bg-gray-950">🐛 Bug Reporter</option>
            <option value="config" className="bg-white dark:bg-gray-950">⚙️ System Config</option>
          </select>
        </div>

        {/* Action Button Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 hover:border-slate-300 dark:hover:border-gray-700 text-slate-500 dark:text-gray-400 hover:text-slate-700 dark:hover:text-gray-200 p-2.5 rounded-xl transition-all active:scale-[0.96] disabled:opacity-50"
            title="Refresh Logs list"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
          
          <button
            onClick={handleExportCSV}
            disabled={loading || filteredLogs.length === 0}
            className="bg-indigo-600/10 hover:bg-indigo-600/20 border border-indigo-500/20 text-indigo-600 dark:text-indigo-400 px-4 py-2.5 rounded-xl font-bold text-xs flex items-center gap-1.5 transition-all active:scale-[0.96] disabled:opacity-50"
            title="Export Logs directly to Microsoft Excel CSV"
          >
            <FileSpreadsheet size={14} />
            <span>Export to CSV</span>
          </button>

          <button
            onClick={handleClearLogs}
            disabled={loading || logs.length === 0}
            className="bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-600 dark:text-rose-400 px-4 py-2.5 rounded-xl font-bold text-xs flex items-center gap-1.5 transition-all active:scale-[0.96] disabled:opacity-50"
            title="Clear Central Audit History"
          >
            <Trash size={14} />
            <span>Clear History</span>
          </button>
        </div>
      </div>

      {/* Logs Listing Viewer Table card */}
      <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-2xl overflow-hidden shadow-sm transition-all">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/40 dark:bg-gray-950/40 border-b border-slate-200 dark:border-gray-800/80 text-slate-500 dark:text-gray-500 text-[10px] font-bold uppercase tracking-wider select-none">
                <th className="p-5 w-16 text-center">ID</th>
                <th className="p-5 w-44">Category</th>
                <th className="p-5">Execution Details</th>
                <th className="p-5 w-52">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-gray-800/40 text-xs">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-10 text-center text-slate-500 dark:text-gray-500">
                    <ScrollText size={36} className="mx-auto text-slate-300 dark:text-gray-800 mb-3" />
                    <p className="font-semibold text-sm text-slate-700 dark:text-gray-300">No Audit Logs found</p>
                    <p className="text-xs text-slate-500 dark:text-gray-500 max-w-xs mx-auto mt-1 leading-normal">
                      Trigger visual baselines, generate test suites, or draft bug reports to populate your central log.
                    </p>
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/40 dark:hover:bg-gray-950/20 transition-colors">
                    <td className="p-5 text-center text-slate-400 dark:text-gray-500 font-mono font-bold">{log.id}</td>
                    <td className="p-5 font-semibold">{getActionBadge(log.action)}</td>
                    <td className="p-5 text-slate-700 dark:text-gray-300 font-medium leading-relaxed max-w-xl truncate-3-lines">{log.details}</td>
                    <td className="p-5 text-slate-400 dark:text-gray-500 font-semibold font-mono">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default AuditLogsModule
