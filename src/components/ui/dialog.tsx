import * as React from 'react'
import { cn } from '@/lib/utils'

export function Dialog({ open, children }: { open: boolean; children: React.ReactNode }) {
  if (!open) return null
  return <div className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm">{children}</div>
}

export function DialogContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'fixed left-1/2 top-1/2 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-4 shadow-xl',
        className,
      )}
      {...props}
    />
  )
}
