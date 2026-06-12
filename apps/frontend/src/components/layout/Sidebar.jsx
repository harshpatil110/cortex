import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Search,
  Network,
  MessageSquare,
  BookOpen,
  LogOut,
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { cn } from '../../lib/utils'

export function Sidebar() {
  const { signOut } = useAuth()

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Search', path: '/search', icon: Search },
    { name: 'Knowledge Graph', path: '/graph', icon: Network },
    { name: 'Chat', path: '/chat', icon: MessageSquare },
    { name: 'Syllabus', path: '/syllabus', icon: BookOpen },
  ]

  return (
    <div className='flex h-full w-64 flex-col border-r border-stone-200 bg-[#FAFAF9] px-4 py-8'>
      <div className='mb-10 px-2'>
        <h1 className='font-display text-2xl font-bold tracking-tight text-stone-900'>
          Cortex
        </h1>
      </div>

      <nav className='flex-1 space-y-1'>
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-sm px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-800'
                  : 'text-stone-600 hover:bg-stone-100 hover:text-stone-900'
              )
            }
          >
            <item.icon className='h-4 w-4' />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className='mt-auto border-t border-stone-200 pt-4'>
        <button
          onClick={() => signOut()}
          className='flex w-full items-center gap-3 rounded-sm px-3 py-2 text-sm font-medium text-stone-600 hover:bg-stone-100 hover:text-stone-900'
        >
          <LogOut className='h-4 w-4' />
          Sign Out
        </button>
      </div>
    </div>
  )
}
