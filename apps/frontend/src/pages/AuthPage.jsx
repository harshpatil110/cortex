import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Spinner } from '../components/ui/Spinner'
import { useAuth } from '../contexts/AuthContext'

export function AuthPage() {
  const [view, setView] = useState('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState({})

  const { signIn, signUp, signInWithGoogle } = useAuth()
  const navigate = useNavigate()

  const validate = () => {
    const newErrors = {}
    if (!email) newErrors.email = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(email))
      newErrors.email = 'Invalid email address'

    if (!password) newErrors.password = 'Password is required'
    else if (password.length < 6)
      newErrors.password = 'Password must be at least 6 characters'

    if (view === 'signup' && !name.trim()) newErrors.name = 'Name is required'

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setIsLoading(true)
    setErrors({})

    try {
      if (view === 'login') {
        const { error } = await signIn(email, password)
        if (error) throw error
      } else {
        const { error } = await signUp(email, password, {
          options: { data: { full_name: name } },
        })
        if (error) throw error
      }
      navigate('/dashboard')
    } catch (err) {
      setErrors({ form: err.message || 'Authentication failed' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogle = async () => {
    try {
      setIsLoading(true)
      const { error } = await signInWithGoogle()
      if (error) throw error
    } catch (err) {
      setErrors({ form: err.message || 'Google Auth failed' })
      setIsLoading(false)
    }
  }

  return (
    <div className='flex min-h-screen w-full items-center justify-center bg-canvas p-4 sm:p-6'>
      <div className='w-full max-w-md bg-white border border-stone-200 shadow-sm rounded-lg p-6 sm:p-8'>
        <div className='text-center mb-8'>
          <h1 className='font-display text-4xl font-bold tracking-tight text-stone-900 mb-2'>
            Cortex
          </h1>
          <p className='text-sm text-stone-500'>
            Your personal AI memory engine
          </p>
        </div>

        <div className='flex mb-6 border-b border-stone-200'>
          <button
            onClick={() => {
              setView('login')
              setErrors({})
            }}
            className={`flex-1 pb-3 text-sm font-medium transition-colors ${view === 'login' ? 'border-b-2 border-stone-900 text-stone-900' : 'text-stone-500 hover:text-stone-700'}`}
          >
            Sign In
          </button>
          <button
            onClick={() => {
              setView('signup')
              setErrors({})
            }}
            className={`flex-1 pb-3 text-sm font-medium transition-colors ${view === 'signup' ? 'border-b-2 border-stone-900 text-stone-900' : 'text-stone-500 hover:text-stone-700'}`}
          >
            Create Account
          </button>
        </div>

        {errors.form && (
          <div className='mb-4 p-3 rounded-sm bg-red-50 border border-red-200 text-red-600 text-sm'>
            {errors.form}
          </div>
        )}

        <form onSubmit={handleSubmit} className='space-y-4'>
          {view === 'signup' && (
            <div>
              <label className='block text-xs font-medium tracking-wider uppercase text-stone-500 mb-1'>
                Display Name
              </label>
              <Input
                type='text'
                placeholder='Ada Lovelace'
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={isLoading}
              />
              {errors.name && (
                <p className='mt-1 text-xs text-red-600'>{errors.name}</p>
              )}
            </div>
          )}

          <div>
            <label className='block text-xs font-medium tracking-wider uppercase text-stone-500 mb-1'>
              Email
            </label>
            <Input
              type='email'
              placeholder='name@example.com'
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
            />
            {errors.email && (
              <p className='mt-1 text-xs text-red-600'>{errors.email}</p>
            )}
          </div>

          <div>
            <label className='block text-xs font-medium tracking-wider uppercase text-stone-500 mb-1'>
              Password
            </label>
            <Input
              type='password'
              placeholder='••••••••'
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
            />
            {errors.password && (
              <p className='mt-1 text-xs text-red-600'>{errors.password}</p>
            )}
          </div>

          <Button type='submit' className='w-full mt-2' disabled={isLoading}>
            {isLoading ? <Spinner className='w-4 h-4 mr-2' /> : null}
            {view === 'login' ? 'Sign In' : 'Create Account'}
          </Button>
        </form>

        <div className='mt-6 flex items-center justify-center'>
          <div className='w-full border-t border-stone-200'></div>
          <span className='px-3 bg-white text-xs font-medium tracking-wider uppercase text-stone-400'>
            OR
          </span>
          <div className='w-full border-t border-stone-200'></div>
        </div>

        <Button
          type='button'
          variant='secondary'
          className='w-full mt-6'
          onClick={handleGoogle}
          disabled={isLoading}
        >
          <svg
            className='w-4 h-4 mr-2'
            viewBox='0 0 24 24'
            fill='none'
            xmlns='http://www.w3.org/2000/svg'
          >
            <path
              d='M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z'
              fill='#4285F4'
            />
            <path
              d='M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z'
              fill='#34A853'
            />
            <path
              d='M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z'
              fill='#FBBC05'
            />
            <path
              d='M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z'
              fill='#EA4335'
            />
          </svg>
          Continue with Google
        </Button>
      </div>
    </div>
  )
}
