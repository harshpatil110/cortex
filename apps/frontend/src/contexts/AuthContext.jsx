import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

const AuthContext = createContext()

const clearLocalAuthTokens = () => {
  try {
    Object.keys(localStorage).forEach((key) => {
      if (key.includes('-auth-token')) {
        localStorage.removeItem(key)
      }
    })
  } catch (_) {
    // Ignore storage errors
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [authError, setAuthError] = useState(null)

  useEffect(() => {
    let isMounted = true

    const initAuth = async () => {
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(
          () => reject(new Error('Authentication server timeout')),
          2500
        )
      )

      try {
        const { data, error } = await Promise.race([
          supabase.auth.getSession(),
          timeoutPromise,
        ])

        if (error) {
          console.error('Auth initialization error:', error)
          if (isMounted) {
            setAuthError(
              error.message || 'Cannot connect to authentication server'
            )
            setSession(null)
            setUser(null)
          }
          clearLocalAuthTokens()
        } else if (isMounted) {
          const currentSession = data?.session || null
          if (
            currentSession?.expires_at &&
            currentSession.expires_at * 1000 < Date.now()
          ) {
            setSession(null)
            setUser(null)
            clearLocalAuthTokens()
          } else {
            setSession(currentSession)
            setUser(currentSession?.user || null)
          }
        }
      } catch (err) {
        console.error('Network or Supabase auth error:', err)
        if (isMounted) {
          setAuthError('Cannot connect to authentication server')
          setSession(null)
          setUser(null)
        }
        clearLocalAuthTokens()
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    initAuth()

    let subscription = null
    try {
      const { data } = supabase.auth.onAuthStateChange((event, newSession) => {
        if (isMounted) {
          if (event === 'SIGNED_OUT') {
            setSession(null)
            setUser(null)
          } else if (event === 'SIGNED_IN') {
            setSession(newSession || null)
            setUser(newSession?.user || null)
            if (newSession) setAuthError(null)
          } else if (newSession) {
            if (
              newSession.expires_at &&
              newSession.expires_at * 1000 < Date.now()
            ) {
              setSession(null)
              setUser(null)
              clearLocalAuthTokens()
            } else {
              setSession(newSession)
              setUser(newSession.user || null)
            }
          } else {
            setSession(null)
            setUser(null)
          }
        }
      })
      subscription = data?.subscription
    } catch (err) {
      console.error('Failed to subscribe to auth state changes:', err)
    }

    return () => {
      isMounted = false
      if (subscription) {
        subscription.unsubscribe()
      }
    }
  }, [])

  const signIn = (email, password) =>
    supabase.auth.signInWithPassword({ email, password })
  const signUp = (email, password, options = {}) =>
    supabase.auth.signUp({ email, password, ...options })
  const signOut = () => {
    clearLocalAuthTokens()
    return supabase.auth.signOut()
  }
  const signInWithGoogle = () =>
    supabase.auth.signInWithOAuth({ provider: 'google' })

  const value = {
    user,
    session,
    loading,
    authError,
    signIn,
    signUp,
    signOut,
    signInWithGoogle,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext)
