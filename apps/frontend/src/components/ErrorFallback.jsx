import { RefreshCw } from 'lucide-react'

export function ErrorFallback() {
  return (
    <div className='flex flex-col items-center justify-center min-h-screen bg-[#F7F5F0] p-6 text-stone-900'>
      <div className='max-w-md w-full bg-white border border-neutral-200 rounded-sm p-8 shadow-sm text-center'>
        <h2 className='font-serif text-2xl mb-4 text-stone-800'>
          Something went wrong
        </h2>
        <p className='text-stone-600 mb-8 font-sans text-sm leading-relaxed'>
          We&apos;re sorry, but an unexpected error occurred. Our team has been
          notified. Please try reloading the page to continue your session.
        </p>

        <button
          onClick={() => window.location.reload()}
          className='inline-flex items-center justify-center px-6 py-2.5 bg-stone-900 text-white font-medium text-sm rounded-sm hover:bg-stone-800 transition-colors focus:outline-none focus:ring-2 focus:ring-stone-500 focus:ring-offset-2 focus:ring-offset-[#F7F5F0]'
        >
          <RefreshCw className='w-4 h-4 mr-2' />
          Reload Client
        </button>
      </div>
    </div>
  )
}
