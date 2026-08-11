import { createBrowserRouter } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AppLayout } from './components/layout/AppLayout'
import { Spinner } from './components/ui/Spinner'
import { AuthPage } from './pages/AuthPage'
import { DashboardPage } from './pages/DashboardPage'
import { SearchPage } from './pages/SearchPage'
import { ErrorFallback } from './components/ErrorFallback'
import { MemoryDetailPage } from './pages/MemoryDetailPage'
import { SyllabusPage } from './pages/SyllabusPage'
import LandingPage from './pages/LandingPage'

const GraphPage = lazy(() =>
  import('./pages/GraphPage').then((m) => ({ default: m.GraphPage }))
)
const ChatPage = lazy(() =>
  import('./pages/ChatPage').then((m) => ({ default: m.ChatPage }))
)

const fallback = (
  <div className='flex h-full w-full items-center justify-center bg-[#F7F5F0]'>
    <Spinner className='w-8 h-8 text-stone-400' />
  </div>
)

export const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/auth',
    element: <AuthPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        errorElement: <ErrorFallback />,
        children: [
          { path: '/dashboard', element: <DashboardPage /> },
          { path: '/search', element: <SearchPage /> },
          { path: '/memory/:id', element: <MemoryDetailPage /> },
          {
            path: '/graph',
            element: (
              <Suspense fallback={fallback}>
                <GraphPage />
              </Suspense>
            ),
          },
          {
            path: '/chat',
            element: (
              <Suspense fallback={fallback}>
                <ChatPage />
              </Suspense>
            ),
          },
          { path: '/syllabus', element: <SyllabusPage /> },
        ],
      },
    ],
  },
])
