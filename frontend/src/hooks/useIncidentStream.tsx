import { useEffect, useState } from 'react'

export interface StreamedIncident {
  id: string
  status: 'open' | 'resolved'
  severity: 'low' | 'medium' | 'high' | 'critical'
  created_at: string
  resolved_at: string | null
}

export function useIncidentStream() {
  const [newIncident, setNewIncident] = useState<StreamedIncident | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Connect to the proxy URL
    const eventSource = new EventSource('/api/v1/incidents/stream')

    eventSource.onopen = () => {
      setIsConnected(true)
      setError(null)
    }

    eventSource.addEventListener('new_incident', (event) => {
      try {
        const incident: StreamedIncident = JSON.parse(event.data)
        setNewIncident(incident)
      } catch (err) {
        console.error('Failed to parse SSE data', err)
      }
    })

    eventSource.onerror = () => {
      setIsConnected(false)
      setError('Live stream disconnected. Reconnecting...')
      // EventSource auto-reconnects natively, but we could close and retry manually if needed
    }

    return () => {
      eventSource.close()
    }
  }, [])

  return { newIncident, isConnected, error }
}
