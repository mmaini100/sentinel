import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import { OpenAPI } from '../api/client'

interface User {
  sub: string
  role: string
  name: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (token: string, user: User) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

// In a real app, storing tokens in localStorage is susceptible to XSS.
// However, for cross-domain local dev where HttpOnly cookies are hard to manage,
// we fall back to localStorage. A production app should use HttpOnly cookies.
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('sentinel_token'))
  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('sentinel_user')
    return savedUser ? JSON.parse(savedUser) : null
  })

  const login = (newToken: string, newUser: User) => {
    setToken(newToken)
    setUser(newUser)
    localStorage.setItem('sentinel_token', newToken)
    localStorage.setItem('sentinel_user', JSON.stringify(newUser))
    
    // Inject token into generated OpenAPI client
    OpenAPI.TOKEN = newToken
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('sentinel_token')
    localStorage.removeItem('sentinel_user')
    delete axios.defaults.headers.common['Authorization']
    OpenAPI.TOKEN = undefined
  }

  // Set default header on initial load if token exists
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      OpenAPI.TOKEN = token
    }
  }, [token])

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
