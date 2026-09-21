import { useEffect, useRef } from 'react'
import { format } from 'date-fns'
import { Activity, FileText } from 'lucide-react'
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts'

interface TimelineProps {
  events: any[]
  highlightedEventId: string | null
}

export default function Timeline({ events, highlightedEventId }: TimelineProps) {
  const eventRefs = useRef<{ [key: string]: HTMLDivElement | null }>({})

  // Smooth scroll and highlight when highlightedEventId changes
  useEffect(() => {
    if (highlightedEventId) {
      const el = eventRefs.current[highlightedEventId]
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
        // Add a brief highlight flash via class manipulation
        el.classList.add('bg-primary/20', 'border-primary', 'shadow-[0_0_15px_rgba(59,130,246,0.3)]')
        
        setTimeout(() => {
          el.classList.remove('bg-primary/20', 'border-primary', 'shadow-[0_0_15px_rgba(59,130,246,0.3)]')
        }, 3000)
      }
    }
  }, [highlightedEventId])

  // Group events visually by drawing lines between same-service events, 
  // but we keep them strictly chronological for reality.
  
  return (
    <div className="space-y-4">
      {events.map((evt, idx) => {
        const isMetric = evt.event_type === 'metric'
        const payload = typeof evt.payload === 'string' ? JSON.parse(evt.payload) : evt.payload
        const Icon = isMetric ? Activity : FileText
        
        return (
          <div 
            key={evt.id}
            id={`event-${evt.id}`}
            ref={(el) => (eventRefs.current[evt.id] = el)}
            className="flex items-start space-x-4 p-4 bg-surface border border-border rounded-lg transition-all duration-700 relative"
          >
            {/* Visual connector line for chronological flow */}
            {idx < events.length - 1 && (
              <div className="absolute left-8 top-12 bottom-[-1rem] w-0.5 bg-border -z-10" />
            )}

            <div className={`p-2 rounded-full border ${
              isMetric ? 'bg-status-low/10 text-status-low border-status-low/20' : 'bg-status-medium/10 text-status-medium border-status-medium/20'
            }`}>
              <Icon className="w-4 h-4" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-start mb-1">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-text-primary text-sm">
                    {evt.service_name || 'Unknown Service'}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-background border border-border text-text-secondary uppercase">
                    {evt.event_type}
                  </span>
                </div>
                <span className="text-xs text-text-muted font-mono">
                  {format(new Date(evt.timestamp), 'HH:mm:ss.SSS')}
                </span>
              </div>

              {/* Payload Preview */}
              <div className="mt-2 text-sm text-text-secondary font-mono bg-background p-2 rounded border border-border/50 overflow-x-auto whitespace-pre-wrap">
                {isMetric ? (
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-status-medium">{payload.metric_name}</span> = <span className="font-bold text-text-primary">{payload.value}</span> {payload.unit}
                    </div>
                    {/* Tiny inline sparkline using Recharts */}
                    <div className="w-24 h-8 ml-4 hidden sm:block">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={[{v: payload.value * 0.8}, {v: payload.value * 0.9}, {v: payload.value}, {v: payload.value * 1.1}, {v: payload.value * 0.85}]}>
                          <YAxis domain={['auto', 'auto']} hide />
                          <Line type="monotone" dataKey="v" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ) : (
                  <div>
                    {payload.message}
                    {payload.status_code && ` (HTTP ${payload.status_code})`}
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })}
      
      {events.length === 0 && (
        <div className="text-center py-12 text-text-muted">
          No telemetry events found for this incident.
        </div>
      )}
    </div>
  )
}
