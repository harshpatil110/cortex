import { Outlet, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { Sidebar } from './Sidebar'
import { AddContentPanel } from '../AddContentPanel'

export function AppLayout() {
  const navigate = useNavigate()

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        // If we're already on search, the SearchPage handles focus
        if (window.location.pathname !== '/search') {
          e.preventDefault()
          navigate('/search')
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [navigate])

  return (
    <div className='flex h-screen overflow-hidden bg-canvas'>
      <Sidebar />
      <main className='flex-1 overflow-y-auto'>
        <div className='mx-auto max-w-6xl px-6 py-8 md:px-12'>
          <Outlet />
        </div>
      </main>
      <AddContentPanel />
    </div>
  )
}
