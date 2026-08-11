import { createContext, useContext } from 'react'

const AuthContext = createContext()

// Permanent local user for single-user mode — no Supabase auth calls.
// Must match the backend's hardcoded user ID
// (see apps/backend/middleware/auth.py).
const LOCAL_USER = { id: 'local-cortex-user-001', email: 'admin@cortex.local' }
const LOCAL_SESSION = { access_token: 'dummy-token' }

export function AuthProvider({ children }) {
  const value = {
    user: LOCAL_USER,
    session: LOCAL_SESSION,
    loading: false,
    authError: null,
    signIn: async () => {},
    signUp: async () => {},
    signInWithGoogle: async () => {},
    signOut: async () => {},
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext)
