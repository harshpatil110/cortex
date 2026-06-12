import { cn } from '../../lib/utils'

export function Button({
  className,
  variant = 'primary',
  size = 'default',
  ...props
}) {
  const baseStyles =
    'inline-flex items-center justify-center rounded-sm text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-300 disabled:pointer-events-none disabled:opacity-50'

  const variants = {
    primary: 'bg-stone-900 text-white hover:bg-stone-700 tracking-wide',
    secondary:
      'bg-transparent border border-stone-300 text-stone-800 hover:bg-stone-100',
    accent:
      'bg-blue-100 border border-blue-200 text-blue-800 hover:bg-blue-200',
    ghost: 'hover:bg-stone-100 text-stone-800',
  }

  const sizes = {
    default: 'h-9 px-6 py-2.5',
    sm: 'h-8 px-3 text-xs',
    lg: 'h-10 px-8',
    icon: 'h-9 w-9',
  }

  return (
    <button
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      {...props}
    />
  )
}
