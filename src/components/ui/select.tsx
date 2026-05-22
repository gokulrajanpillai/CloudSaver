import * as React from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Select({ className, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="relative inline-flex items-center">
      <select
        className={cn(
          'h-9 appearance-none rounded-md border border-border bg-surface py-0 pl-3 pr-8 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent',
          className,
        )}
        {...props}
      />
      <ChevronDown className="pointer-events-none absolute right-2.5 h-3.5 w-3.5 text-text-muted" />
    </div>
  )
}
