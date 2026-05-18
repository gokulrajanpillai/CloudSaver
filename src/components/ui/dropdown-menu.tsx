import * as React from 'react'
import { cn } from '@/lib/utils'

export function DropdownMenu({ children }: { children: React.ReactNode }) {
  return <div className="relative inline-block">{children}</div>
}

export function DropdownMenuContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'absolute right-0 z-40 mt-2 min-w-44 rounded-md border border-border bg-surface p-1 shadow-lg',
        className,
      )}
      {...props}
    />
  )
}

export function DropdownMenuItem({ className, ...props }: React.HTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn('block w-full rounded px-3 py-2 text-left text-sm hover:bg-surface-overlay', className)}
      {...props}
    />
  )
}
