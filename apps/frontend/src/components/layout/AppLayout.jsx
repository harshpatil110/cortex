import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { AddContentPanel } from '../AddContentPanel'

export function AppLayout() {
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
