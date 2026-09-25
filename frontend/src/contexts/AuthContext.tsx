import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { authApi } from '../services/api'
import type { RegisterIn, UserOut } from '../services/api'

type AuthContextValue = {
  user: UserOut | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterIn) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null)
  const [loading, setLoading] = useState(() => localStorage.getItem('access_token') !== null)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      return
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('access_token')
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const token = await authApi.login({ email, password })
    localStorage.setItem('access_token', token.access_token)
    setUser(token.user)
  }, [])

  const register = useCallback(async (data: RegisterIn) => {
    const token = await authApi.register(data)
    localStorage.setItem('access_token', token.access_token)
    setUser(token.user)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth должен использоваться внутри AuthProvider')
  }
  return ctx
}
