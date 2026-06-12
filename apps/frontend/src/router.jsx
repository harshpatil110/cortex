import { createBrowserRouter, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AppLayout } from './components/layout/AppLayout'
import {
  AuthPage,
  DashboardPage,
  SearchPage,
  MemoryDetailPage,
  GraphPage,
  ChatPage,
  SyllabusPage,
} from './pages'

export const router = createBrowserRouter([
  {
    path: '/auth',
    element: <AuthPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: '/',
        element: <Navigate to='/dashboard' replace />,
      },
      {
        element: <AppLayout />,
        children: [
          { path: '/dashboard', element: <DashboardPage /> },
          { path: '/search', element: <SearchPage /> },
          { path: '/memory/:id', element: <MemoryDetailPage /> },
          { path: '/graph', element: <GraphPage /> },
          { path: '/chat', element: <ChatPage /> },
          { path: '/syllabus', element: <SyllabusPage /> },
        ],
      },
    ],
  },
])
