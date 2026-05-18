export function formatBytes(bytes?: number) {
  const value = Number(bytes || 0)
  if (value <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1)
  return `${(value / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

export function relativeTime(iso?: string) {
  if (!iso) return 'Never scanned'
  const delta = Date.now() - new Date(iso).getTime()
  const minutes = Math.max(1, Math.round(delta / 60000))
  if (minutes < 60) return `Scanned ${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 48) return `Scanned ${hours}h ago`
  return `Scanned ${Math.round(hours / 24)}d ago`
}
