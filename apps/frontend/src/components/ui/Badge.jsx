import { cn } from '../../lib/utils'

export function Badge({ className, variant = 'default', ...props }) {
  const baseStyles =
    'inline-flex items-center rounded-sm border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-blue-300 uppercase tracking-wider'

  const variants = {
    default:
      'border-transparent bg-stone-900 text-stone-50 hover:bg-stone-900/80',
    secondary:
      'border-transparent bg-stone-100 text-stone-900 hover:bg-stone-100/80',
    outline: 'text-stone-950 border-stone-200',
    accent: 'border-transparent bg-blue-100 text-blue-800',
  }

  return (
    <div className={cn(baseStyles, variants[variant], className)} {...props} />
  )
}
