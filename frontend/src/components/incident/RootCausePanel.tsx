import { HelpCircle, CheckCircle, Search, Zap } from 'lucide-react'

interface RCAProps {
  rca: any
  onCitationClick: (eventId: string) => void
}

export default function RootCausePanel({ rca, onCitationClick }: RCAProps) {
  if (!rca) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-text-muted text-center bg-surface border border-border rounded-lg">
        <Search className="w-12 h-12 mb-4 text-border" />
        <h3 className="text-lg font-medium text-text-primary mb-2">Analyzing telemetry...</h3>
        <p className="text-sm">The AI Copilot is currently correlating events and generating a root cause hypothesis.</p>
      </div>
    )
  }

  if (rca.status === 'insufficient_evidence') {
    return (
      <div className="flex flex-col h-full p-6 bg-surface border border-border rounded-lg">
        <div className="flex items-center text-status-medium mb-4">
          <HelpCircle className="w-6 h-6 mr-3" />
          <h3 className="text-lg font-semibold text-text-primary">Insufficient Evidence</h3>
        </div>
        <p className="text-text-secondary leading-relaxed mb-6">
          The AI Copilot analyzed the telemetry but could not form a confident root cause hypothesis. This usually happens when the failure mode spans systems without tracing headers, or when critical debug logs are missing.
        </p>
        <div className="mt-auto pt-4 border-t border-border">
          <span className="text-sm font-medium text-text-primary block mb-2">Recommended Action:</span>
          <p className="text-sm text-text-muted">
            Manual investigation required. Review the raw event timeline and consider enabling verbose logging on the implicated services.
          </p>
        </div>
      </div>
    )
  }

  // Parse text to find citations like [event:1234-5678-...] and convert to buttons
  const renderTextWithCitations = (text: string) => {
    const regex = /\[event:([a-f0-9\-]+)\]/g
    const parts = []
    let lastIndex = 0
    let match

    while ((match = regex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index))
      }
      
      const eventId = match[1]
      parts.push(
        <button
          key={`${eventId}-${match.index}`}
          onClick={() => onCitationClick(eventId)}
          className="inline-flex items-center px-1.5 py-0.5 mx-1 text-xs font-mono bg-primary/10 text-primary border border-primary/20 rounded hover:bg-primary/20 hover:border-primary/40 transition-colors"
        >
          <Search className="w-3 h-3 mr-1" />
          {eventId.substring(0, 8)}
        </button>
      )
      
      lastIndex = regex.lastIndex
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex))
    }

    return parts
  }

  return (
    <div className="flex flex-col h-full bg-surface border border-border rounded-lg overflow-hidden">
      <div className="p-4 border-b border-border bg-surfaceHover flex justify-between items-center">
        <div className="flex items-center">
          <BrainIcon />
          <h3 className="font-semibold text-text-primary ml-2">AI Copilot Analysis</h3>
        </div>
        
        {/* Confidence Meter */}
        <div className="flex items-center space-x-3">
          <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Confidence</span>
          <div className="w-24 h-2 bg-background rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full ${
                rca.confidence > 0.8 ? 'bg-status-healthy' : 
                rca.confidence > 0.5 ? 'bg-status-medium' : 'bg-status-low'
              }`}
              style={{ width: `${Math.max(5, rca.confidence * 100)}%` }}
            />
          </div>
          <span className="text-sm font-bold text-text-primary">
            {Math.round(rca.confidence * 100)}%
          </span>
        </div>
      </div>

      <div className="p-6 flex-1 overflow-y-auto space-y-6">
        <div>
          <h4 className="text-sm font-medium text-text-primary mb-2 flex items-center">
            <Zap className="w-4 h-4 text-status-medium mr-2" />
            Root Cause Hypothesis
          </h4>
          <p className="text-text-secondary leading-relaxed text-sm">
            {renderTextWithCitations(rca.hypothesis)}
          </p>
          
          {rca.cited_event_ids && rca.cited_event_ids.length > 0 && (
            <div className="mt-4 pt-4 border-t border-border/50">
              <h5 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Cited Evidence</h5>
              <div className="flex flex-wrap gap-2">
                {rca.cited_event_ids.map((eventId: string) => (
                  <button
                    key={eventId}
                    onClick={() => onCitationClick(eventId)}
                    className="inline-flex items-center px-2 py-1 text-xs font-mono bg-primary/10 text-primary border border-primary/20 rounded hover:bg-primary/20 hover:border-primary/40 transition-colors"
                  >
                    <Search className="w-3 h-3 mr-1.5" />
                    {eventId.substring(0, 8)}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {rca.recommended_action && (
          <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
            <h4 className="text-sm font-medium text-primary mb-2 flex items-center">
              <CheckCircle className="w-4 h-4 mr-2" />
              Recommended Action
            </h4>
            <p className="text-sm text-text-secondary">
              {renderTextWithCitations(rca.recommended_action)}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function BrainIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
      <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
      <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>
      <path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/>
      <path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/>
      <path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/>
      <path d="M3.477 10.896a4 4 0 0 1 .585-.396"/>
      <path d="M19.938 10.5a4 4 0 0 1 .585.396"/>
      <path d="M6 18a4 4 0 0 1-1.967-.516"/>
      <path d="M19.967 17.484A4 4 0 0 1 18 18"/>
    </svg>
  )
}
