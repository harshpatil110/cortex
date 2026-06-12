import { cn } from '../../lib/utils'

export function Toast({ message, type = 'default', className, onClose }) {
  const types = {
    default: 'bg-white border-stone-200 text-stone-900',
    error: 'bg-red-50 border-red-200 text-red-900',
    success: 'bg-green-50 border-green-200 text-green-900',
  }

  return (
    <div
      className={cn(
        'pointer-events-auto flex w-full max-w-md rounded-sm shadow-sm border p-4',
        types[type],
        className
      )}
    >
      <div className='flex-1 text-sm font-medium'>{message}</div>
      {onClose && (
        <button
          onClick={onClose}
          className='ml-4 text-stone-400 hover:text-stone-900'
        >
          ×
        </button>
      )}
    </div>
  )
}
