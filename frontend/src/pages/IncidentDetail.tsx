import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Clock, ShieldAlert, CheckCircle2, AlertTriangle, Info } from 'lucide-react'
import { formatDistanceToNow, format } from 'date-fns'

import { IncidentsService } from '../api/client'
import Timeline from '../components/incident/Timeline'
import RootCausePanel from '../components/incident/RootCausePanel'

const severityIcons = {
  low: Info,
  medium: AlertTriangle,
  high: ShieldAlert,
  critical: ShieldAlert,
}

const severityColors = {
  low: 'text-status-low bg-status-low/10 border-status-low/20',
  medium: 'text-status-medium bg-status-medium/10 border-status-medium/20',
  high: 'text-status-high bg-status-high/10 border-status-high/20',
  critical: 'text-status-critical bg-status-critical/10 border-status-critical/20',
}

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  // Lifted state for citation highlighting
  const [highlightedEventId, setHighlightedEventId] = useState<string | null>(null)

  const { data: incident, isLoading, error } = useQuery({
    queryKey: ['incident', id],
    queryFn: () => IncidentsService.getIncidentApiV1IncidentsIncidentIdGet(id!),
    enabled: !!id,
    refetchInterval: 2000 // Poll every 2s for live event timeline and RCA updates
  })

  // Optimistic resolve mutation
  const resolveMutation = useMutation({
    mutationFn: () => IncidentsService.resolveIncidentApiV1IncidentsIncidentIdResolvePost(id!),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['incident', id] })
      const previousIncident = queryClient.getQueryData(['incident', id])
      
      // Optimistically update
      queryClient.setQueryData(['incident', id], (old: any) => ({
        ...old,
        status: 'resolved',
        resolved_at: new Date().toISOString()
      }))
      
      return { previousIncident }
    },
    onError: (err, _variables, context) => {
      queryClient.setQueryData(['incident', id], context?.previousIncident)
      console.error('Failed to resolve incident', err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['incident', id] })
      queryClient.invalidateQueries({ queryKey: ['incidents'] })
    }
  })

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (error || !incident) {
    return (
      <div className="p-8 text-center text-status-critical">
        Error loading incident {id}.
      </div>
    )
  }

  const isResolved = incident.status === 'resolved'
  const SeverityIcon = severityIcons[incident.severity as keyof typeof severityIcons] || Info
  const colors = severityColors[incident.severity as keyof typeof severityColors] || severityColors.medium

  return (
    <div className="h-[calc(100vh-80px)] flex flex-col animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex-none pb-4 border-b border-border mb-6 flex items-start justify-between">
        <div>
          <button 
            onClick={() => navigate('/dashboard')}
            className="flex items-center text-text-muted hover:text-text-primary transition-colors text-sm mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Dashboard
          </button>
          
          <div className="flex items-center space-x-3 mb-2">
            <div className={`p-2 rounded-lg border ${colors}`}>
              <SeverityIcon className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-bold text-text-primary">
              {incident.title || `Incident in ${incident.service_names?.[0] || 'Unknown'}`}
            </h1>
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-text-secondary ml-12">
            <span className="flex items-center">
              <Clock className="w-4 h-4 mr-1.5 opacity-70" />
              Created {format(new Date(incident.created_at), 'MMM d, HH:mm:ss')}
            </span>
            {isResolved && incident.resolved_at && (
              <span className="flex items-center text-status-healthy">
                <CheckCircle2 className="w-4 h-4 mr-1.5" />
                Resolved {formatDistanceToNow(new Date(incident.resolved_at), { addSuffix: true })}
              </span>
            )}
            <div className="flex gap-2">
              {incident.service_names?.map((svc: string) => (
                <span key={svc} className="px-2 py-0.5 rounded bg-surface border border-border text-xs">
                  {svc}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end space-y-3">
          <div className="flex space-x-2">
            <span className={`px-3 py-1 rounded-full uppercase tracking-wider font-bold text-xs border ${colors}`}>
              {incident.severity}
            </span>
            <span className={`px-3 py-1 rounded-full uppercase tracking-wider font-bold text-xs border ${
              isResolved ? 'bg-status-healthy/10 text-status-healthy border-status-healthy/20' : 'bg-status-critical/10 text-status-critical border-status-critical/20'
            }`}>
              {incident.status}
            </span>
          </div>

          <button
            onClick={() => resolveMutation.mutate()}
            disabled={isResolved || resolveMutation.isPending}
            className={`px-4 py-2 rounded-md font-medium text-sm transition-all shadow-sm ${
              isResolved 
                ? 'bg-surface border border-border text-text-muted cursor-not-allowed opacity-75' 
                : 'bg-primary hover:bg-primary-hover text-white'
            }`}
          >
            {resolveMutation.isPending ? 'Resolving...' : isResolved ? 'Resolved' : 'Resolve Incident'}
          </button>
        </div>
      </div>

      {/* Split View */}
      <div className="flex-1 min-h-0 flex gap-6">
        {/* Left: Timeline */}
        <div className="w-1/2 flex flex-col bg-surface border border-border rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-border bg-surfaceHover font-medium text-text-primary">
            Event Timeline ({incident.events?.length || 0})
          </div>
          <div className="p-4 overflow-y-auto flex-1">
            <Timeline 
              events={incident.events || []} 
              highlightedEventId={highlightedEventId}
            />
          </div>
        </div>

        {/* Right: RCA Panel */}
        <div className="w-1/2 flex flex-col">
          <RootCausePanel 
            rca={incident.root_cause_analyses?.[0]} 
            onCitationClick={(id) => setHighlightedEventId(id)}
          />
        </div>
      </div>
    </div>
  )
}
