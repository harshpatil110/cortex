import { cn } from '../../lib/utils'

export function Sheet({ open, onClose, children, className }) {
  if (!open) return null

  return (
    <div className='fixed inset-0 z-50 flex justify-end'>
      <div
        className='fixed inset-0 bg-stone-900/10 backdrop-blur-[2px]'
        onClick={onClose}
      />
      <div
        className={cn(
          'relative z-50 w-full max-w-md bg-canvas p-6 shadow-sm h-full border-l border-stone-200 overflow-y-auto',
          className
        )}
      >
        {children}
      </div>
    </div>
  )
}
