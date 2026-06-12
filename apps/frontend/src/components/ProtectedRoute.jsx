import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Spinner } from './ui/Spinner'

export function ProtectedRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className='flex h-screen w-full items-center justify-center bg-canvas'>
        <Spinner className='h-8 w-8' />
      </div>
    )
  }

  if (!user) {
    return <Navigate to='/auth' replace />
  }

  return <Outlet />
}
