import { formatDistanceToNow } from 'date-fns'
import { AlertCircle, AlertTriangle, Info, ShieldAlert, CheckCircle2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface IncidentListProps {
  incidents: any[]
  isLoading: boolean
}

export const severityColors = {
  low: 'text-status-low bg-status-low/10 border-status-low/20',
  medium: 'text-status-medium bg-status-medium/10 border-status-medium/20',
  high: 'text-status-high bg-status-high/10 border-status-high/20',
  critical: 'text-status-critical bg-status-critical/10 border-status-critical/20 animate-pulse',
}

export const severityIcons = {
  low: Info,
  medium: AlertCircle,
  high: AlertTriangle,
  critical: ShieldAlert,
}

export default function IncidentList({ incidents, isLoading }: IncidentListProps) {
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-20 bg-surface border border-border rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (incidents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-text-muted">
        <CheckCircle2 className="w-12 h-12 text-status-healthy/50 mb-4" />
        <p>No active incidents. System is healthy.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {incidents.map((incident) => {
        const SeverityIcon = severityIcons[incident.severity as keyof typeof severityIcons]
        const colors = severityColors[incident.severity as keyof typeof severityColors]

        return (
          <div
            key={incident.id}
            onClick={() => navigate(`/incidents/${incident.id}`)}
            className="group flex items-center justify-between p-4 bg-surface border border-border rounded-lg hover:border-text-muted transition-all cursor-pointer relative overflow-hidden"
          >
            {/* Left accent bar */}
            <div className={`absolute left-0 top-0 bottom-0 w-1 ${colors.split(' ')[1]}`} />
            
            <div className="flex items-center space-x-4 pl-2">
              <div className={`p-2 rounded-md border ${colors}`}>
                <SeverityIcon className="w-5 h-5" />
              </div>
              
              <div>
                <h3 className="text-text-primary font-medium group-hover:text-white transition-colors">
                  {incident.title || `Incident in ${incident.service_names?.[0] || 'Unknown System'}`}
                </h3>
                <div className="flex flex-wrap gap-2 mt-1">
                  {incident.service_names?.map((svc: string) => (
                    <span key={svc} className="text-xs px-2 py-0.5 rounded-full bg-border text-text-secondary">
                      {svc}
                    </span>
                  ))}
                  <span className="text-xs text-text-muted flex items-center px-1">
                    • {incident.event_count} events
                  </span>
                </div>
              </div>
            </div>

            <div className="flex flex-col items-end space-y-1">
              <div className="flex items-center space-x-2">
                <span className={`text-xs px-2 py-0.5 rounded-full uppercase tracking-wider font-semibold border ${colors}`}>
                  {incident.severity}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full uppercase tracking-wider font-semibold border ${
                  incident.status === 'open' 
                    ? 'bg-status-critical/10 text-status-critical border-status-critical/20' 
                    : 'bg-status-healthy/10 text-status-healthy border-status-healthy/20'
                }`}>
                  {incident.status}
                </span>
              </div>
              <span className="text-xs text-text-muted font-mono">
                {formatDistanceToNow(new Date(incident.created_at), { addSuffix: true })}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
