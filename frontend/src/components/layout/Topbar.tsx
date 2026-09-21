import { Zap, Bell, User, Loader2, X } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

export default function Topbar() {
  const [isTriggering, setIsTriggering] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  
  const [service, setService] = useState('orders-service')
  const [faultType, setFaultType] = useState('latency_spike')
  const [duration, setDuration] = useState('15')
  
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleTriggerFault = async () => {
    setIsTriggering(true)
    setShowDropdown(false)
    try {
      await fetch('/api/v1/services/trigger-fault', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_name: service,
          fault_type: faultType,
          duration_seconds: parseInt(duration, 10)
        })
      })
    } catch (e) {
      console.error(e)
    } finally {
      setIsTriggering(false)
    }
  }

  return (
    <div className="h-16 bg-surface border-b border-border flex items-center justify-between px-6 z-50">
      <div className="flex items-center">
        <h1 className="text-sm font-medium text-text-secondary">Incident Response Console</h1>
      </div>
      
      <div className="flex items-center space-x-4">
        {/* Dynamic Fault Trigger Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button 
            onClick={() => setShowDropdown(!showDropdown)}
            disabled={isTriggering}
            className="flex items-center px-3 py-1.5 bg-status-critical/10 text-status-critical border border-status-critical/20 rounded hover:bg-status-critical/20 transition-colors text-sm font-medium disabled:opacity-50"
          >
            {isTriggering ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Zap className="w-4 h-4 mr-2" />}
            {isTriggering ? 'Triggering...' : 'Trigger Demo Fault'}
          </button>

          {showDropdown && (
            <div className="absolute right-0 mt-2 w-72 bg-surfaceHover border border-border rounded-lg shadow-xl p-4 z-50">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-semibold text-text-primary">Inject Fault</h3>
                <button onClick={() => setShowDropdown(false)} className="text-text-muted hover:text-text-primary">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-text-muted mb-1 uppercase tracking-wider">Target Service</label>
                  <select 
                    value={service} 
                    onChange={e => setService(e.target.value)}
                    className="w-full bg-background border border-border rounded px-2 py-1.5 text-sm text-text-primary focus:outline-none focus:border-status-critical"
                  >
                    <option value="api-gateway">api-gateway</option>
                    <option value="auth-service">auth-service</option>
                    <option value="orders-service">orders-service</option>
                    <option value="payments-service">payments-service</option>
                    <option value="inventory-service">inventory-service</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-text-muted mb-1 uppercase tracking-wider">Fault Type</label>
                  <select 
                    value={faultType} 
                    onChange={e => setFaultType(e.target.value)}
                    className="w-full bg-background border border-border rounded px-2 py-1.5 text-sm text-text-primary focus:outline-none focus:border-status-critical"
                  >
                    <option value="latency_spike">Latency Spike (10-20x)</option>
                    <option value="error_burst">Error Burst (50-80%)</option>
                    <option value="dependency_timeout">Dependency Timeout</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-text-muted mb-1 uppercase tracking-wider">Duration</label>
                  <select 
                    value={duration} 
                    onChange={e => setDuration(e.target.value)}
                    className="w-full bg-background border border-border rounded px-2 py-1.5 text-sm text-text-primary focus:outline-none focus:border-status-critical"
                  >
                    <option value="15">15 seconds</option>
                    <option value="30">30 seconds</option>
                    <option value="60">60 seconds</option>
                  </select>
                </div>

                <button
                  onClick={handleTriggerFault}
                  className="w-full mt-2 bg-status-critical hover:bg-status-critical/80 text-white py-2 rounded-md font-medium text-sm transition-colors"
                >
                  Execute Fault
                </button>
              </div>
            </div>
          )}
        </div>
        
        <div className="w-px h-6 bg-border mx-2"></div>
        
        <button className="text-text-muted hover:text-text-primary transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-0 right-0 w-2 h-2 bg-status-critical rounded-full"></span>
        </button>
        
        <button className="w-8 h-8 rounded-full bg-border flex items-center justify-center text-text-secondary hover:text-text-primary transition-colors">
          <User className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
