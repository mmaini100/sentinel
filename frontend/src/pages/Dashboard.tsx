import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Activity, ShieldCheck, Server, BrainCircuit, WifiOff } from 'lucide-react'
import { IncidentsService } from '../api/client'
import { useIncidentStream } from '../hooks/useIncidentStream'
import IncidentList from '../components/dashboard/IncidentList'

export default function Dashboard() {
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const { newIncident, isConnected, error: streamError } = useIncidentStream()

  // Fetch initial incidents list using the generated OpenAPI client
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['incidents', filterStatus],
    queryFn: () => IncidentsService.listIncidentsApiV1IncidentsGet(
      1, 
      50, 
      filterStatus === 'all' ? undefined : filterStatus as any
    )
  })

  // When a new incident streams in, we just refetch the list for simplicity in this demo.
  // In a highly optimized app, we'd prepend it to the cache directly.
  useEffect(() => {
    if (newIncident) {
      refetch()
    }
  }, [newIncident, refetch])

  const incidents = data?.incidents || []
  
  // Calculate summary metrics based on fetched data
  const openCount = incidents.filter(i => i.status === 'open').length
  const criticalCount = incidents.filter(i => i.severity === 'critical' && i.status === 'open').length

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500">
      {/* SSE Connection Error Toast */}
      {streamError && (
        <div className="p-3 bg-status-critical/10 border border-status-critical/20 rounded-lg flex items-center text-status-critical">
          <WifiOff className="w-5 h-5 mr-3" />
          <span className="text-sm font-medium">{streamError}</span>
        </div>
      )}

      {/* Top Summary Bar */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-surface border border-border p-4 rounded-lg flex flex-col">
          <div className="flex items-center text-text-secondary mb-2">
            <Activity className="w-4 h-4 mr-2" />
            <span className="text-sm font-medium">Active Incidents</span>
          </div>
          <span className="text-3xl font-bold text-text-primary">{openCount}</span>
        </div>
        
        <div className="bg-surface border border-border p-4 rounded-lg flex flex-col">
          <div className="flex items-center text-status-critical mb-2">
            <ShieldCheck className="w-4 h-4 mr-2" />
            <span className="text-sm font-medium">Critical Open</span>
          </div>
          <span className="text-3xl font-bold text-status-critical">{criticalCount}</span>
        </div>

        <div className="bg-surface border border-border p-4 rounded-lg flex flex-col">
          <div className="flex items-center text-text-secondary mb-2">
            <Server className="w-4 h-4 mr-2" />
            <span className="text-sm font-medium">Monitored Services</span>
          </div>
          {/* Hardcoded for demo, normally fetched from /services */}
          <span className="text-3xl font-bold text-text-primary">5</span> 
        </div>

        <div className="bg-surface border border-border p-4 rounded-lg flex flex-col justify-between">
          <div className="flex items-center text-status-low mb-2">
            <BrainCircuit className="w-4 h-4 mr-2" />
            <span className="text-sm font-medium">AI Copilot</span>
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold text-text-primary">Active</span>
            <span className="text-xs text-text-muted">Provider: Gemini 1.5 Flash</span>
          </div>
        </div>
      </div>

      {/* Main Incident Feed */}
      <div className="bg-surface border border-border rounded-lg flex flex-col overflow-hidden h-[calc(100vh-250px)]">
        <div className="p-4 border-b border-border flex items-center justify-between bg-surfaceHover">
          <div className="flex items-center space-x-3">
            <h2 className="text-lg font-semibold text-text-primary">Live Incident Feed</h2>
            {isConnected && (
              <span className="flex items-center text-xs text-status-healthy font-medium px-2 py-1 bg-status-healthy/10 rounded-full border border-status-healthy/20">
                <span className="w-1.5 h-1.5 bg-status-healthy rounded-full mr-1.5 animate-pulse"></span>
                Live
              </span>
            )}
          </div>
          
          <div className="flex space-x-2">
            <select 
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-background border border-border text-sm rounded-md px-3 py-1.5 text-text-primary focus:outline-none focus:border-status-low"
            >
              <option value="all">All Statuses</option>
              <option value="open">Open Only</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>
        
        <div className="p-4 overflow-y-auto flex-1">
          <IncidentList incidents={incidents} isLoading={isLoading} />
        </div>
      </div>
    </div>
  )
}
