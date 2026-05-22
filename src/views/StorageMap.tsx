import { ResponsiveTreeMap } from '@nivo/treemap'
import { useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { formatBytes } from '@/lib/format'
import { useStore } from '@/store'

interface FileNode {
  id: string
  name: string
  path: string
  value: number
  category: string
  sourceLabel: string
}

export function StorageMap() {
  const sources = useStore((state) => state.sources)
  const scanResults = useStore((state) => state.scanResults)
  const [selectedSource, setSelectedSource] = useState('all')
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null)

  const sourceOptions = [{ id: 'all', label: 'All Sources' }, ...sources.map((source) => ({ id: source.id, label: source.label }))]
  const tree = useMemo(() => {
    const children = Object.entries(scanResults)
      .filter(([sourceId]) => selectedSource === 'all' || selectedSource === sourceId)
      .flatMap(([sourceId, result]) => {
        const source = sources.find((item) => item.id === sourceId)
        return result.files.map((file) => ({
          id: `${source?.label || sourceId}/${String(file.path || file.name || file.id)}`,
          name: String(file.name || file.path || file.id || 'Untitled'),
          path: String(file.path || file.id || ''),
          value: Number(file.size_bytes || 0),
          category: String(file.category || 'other'),
          sourceLabel: source?.label || sourceId,
        }))
      })
      .filter((file) => file.value > 0)
    return { name: 'Storage', children }
  }, [scanResults, selectedSource, sources])

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-lg font-semibold">Storage Map</h1>
        <div className="inline-flex rounded-md bg-surface-overlay p-1">
          {sourceOptions.map((source) => (
            <button
              className={`rounded px-3 py-1.5 text-sm ${selectedSource === source.id ? 'bg-surface text-text-primary' : 'text-text-secondary'}`}
              key={source.id}
              onClick={() => setSelectedSource(source.id)}
              type="button"
            >
              {source.label}
            </button>
          ))}
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-[1fr_300px]">
        <div className="h-[560px] rounded-lg border border-border bg-surface-raised p-2">
          {tree.children.length ? (
            <ResponsiveTreeMap
              data={tree}
              identity="id"
              value="value"
              colors={{ scheme: 'category10' }}
              labelSkipSize={18}
              nodeOpacity={0.92}
              borderColor={{ from: 'color', modifiers: [['darker', 0.4]] }}
              onClick={(node) => setSelectedFile(node.data as FileNode)}
            />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-text-muted">
              Scan a source to populate the storage map.
            </div>
          )}
        </div>
        <aside className="rounded-lg border border-border bg-surface-raised p-4">
          <h2 className="text-sm font-semibold">Details</h2>
          {selectedFile ? (
            <div className="mt-4 space-y-2 text-sm">
              <div className="font-medium">{selectedFile.name}</div>
              <div className="text-text-muted">{formatBytes(selectedFile.value)}</div>
              <div className="text-text-muted">{selectedFile.category}</div>
              <div className="break-all text-xs text-text-muted">{selectedFile.path}</div>
              <div className="text-xs text-text-secondary">{selectedFile.sourceLabel}</div>
              <Button className="mt-2" size="sm" type="button" variant="outline">
                Reveal
              </Button>
            </div>
          ) : (
            <p className="mt-4 text-sm text-text-muted">Select a file block to inspect it.</p>
          )}
        </aside>
      </div>
    </section>
  )
}
