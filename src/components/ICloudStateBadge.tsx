import { Cloud } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export function ICloudStateBadge({
  state,
  onManage,
}: {
  state?: string | null
  onManage?: () => void
}) {
  if (state !== 'evicted' && state !== 'downloading') return null

  return (
    <span className="inline-flex items-center gap-2">
      <Badge className="gap-1" title="Stored in iCloud only — scanning this folder without downloading won't affect your local storage.">
        <Cloud className="h-3 w-3" />
        {state === 'evicted' ? 'iCloud only' : 'Downloading'}
      </Badge>
      {state === 'evicted' && onManage && (
        <Button onClick={onManage} size="sm" type="button" variant="ghost">
          Manage in iCloud
        </Button>
      )}
    </span>
  )
}

export function canRevealICloudFile(state?: string | null) {
  return state !== 'evicted'
}
