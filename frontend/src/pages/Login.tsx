import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { ShieldAlert, LogIn, Lock, Mail } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      // Using Vite proxy to avoid CORS/Host issues
      const response = await axios.post('/api/v1/auth/login', {
        email,
        password
      })
      
      const { access_token, user } = response.data
      login(access_token, user)
      navigate('/dashboard')
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Invalid credentials. Use password "admin".')
      } else {
        setError('Connection failed. Is the backend running?')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-status-low/10 rounded-full blur-[100px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-status-critical/10 rounded-full blur-[100px] pointer-events-none"></div>
      
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-surface border border-border shadow-2xl mb-6">
            <ShieldAlert className="w-8 h-8 text-status-healthy" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary mb-2">Sentinel</h1>
          <p className="text-text-secondary">Incident Response Console</p>
        </div>

        <div className="bg-surface border border-border rounded-xl shadow-2xl p-8 relative z-10">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 bg-status-critical/10 border border-status-critical/20 rounded-md">
                <p className="text-sm text-status-critical font-medium text-center">{error}</p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Operator Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-text-muted" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2.5 bg-background border border-border rounded-md text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-status-low focus:border-transparent transition-shadow sm:text-sm"
                  placeholder="admin@sentinel.local"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-text-muted" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2.5 bg-background border border-border rounded-md text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-status-low focus:border-transparent transition-shadow sm:text-sm"
                  placeholder="admin"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-status-low hover:bg-status-low/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-surface focus:ring-status-low transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <>
                  <LogIn className="w-4 h-4 mr-2" />
                  Sign In
                </>
              )}
            </button>
          </form>
        </div>
        
        <p className="text-center text-text-muted text-xs mt-8">
          Sentinel operates on a zero-trust model. Ensure you are connected to the corporate VPN.
        </p>
      </div>
    </div>
  )
}
