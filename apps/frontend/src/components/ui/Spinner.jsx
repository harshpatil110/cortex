import { cn } from '../../lib/utils'
import { Loader2 } from 'lucide-react'

export function Spinner({ className, ...props }) {
  return (
    <Loader2
      className={cn('animate-spin text-stone-500', className)}
      {...props}
    />
  )
}
