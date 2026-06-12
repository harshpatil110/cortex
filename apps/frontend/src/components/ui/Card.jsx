import { cn } from '../../lib/utils'

export function Card({ className, ...props }) {
  return (
    <div
      className={cn(
        'bg-white border border-stone-200 shadow-sm rounded-lg p-5',
        className
      )}
      {...props}
    />
  )
}
