import type { CrossSourceGroup, DuplicateGroup, ScanResult, Source } from '@/types'

const GB = 1024 ** 3
const MB = 1024 ** 2

export const DEMO_SOURCES: Source[] = [
  {
    id: 'demo-icloud',
    type: 'icloud',
    label: 'iCloud Drive',
    path: '/Users/me/Library/Mobile Documents/com~apple~CloudDocs',
    quota: { used: 34.2 * GB, total: 50 * GB },
    lastScanned: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    fileCount: 9_841,
    totalBytes: 34.2 * GB,
    status: 'ready',
  },
  {
    id: 'demo-local',
    type: 'local',
    label: 'Downloads',
    path: '/Users/me/Downloads',
    lastScanned: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
    fileCount: 2_304,
    totalBytes: 12.8 * GB,
    status: 'ready',
  },
]

function fakeFile(name: string, sizeBytes: number, category: string, sourceId: string) {
  return { id: name, name, path: `/demo/${name}`, size_bytes: sizeBytes, category, source_id: sourceId }
}

export const DEMO_SCAN_RESULTS: Record<string, ScanResult> = {
  'demo-icloud': {
    sourceId: 'demo-icloud',
    quota: { used: 34.2 * GB, total: 50 * GB },
    audit: { opportunities: { image_optimization_bytes: 2.1 * GB } },
    files: [
      fakeFile('Photos Library.photoslibrary', 18.4 * GB, 'image', 'demo-icloud'),
      fakeFile('Documents.zip', 4.2 * GB, 'archive', 'demo-icloud'),
      fakeFile('Screenflow Recordings', 6.1 * GB, 'video', 'demo-icloud'),
      fakeFile('Desktop Notes', 124 * MB, 'document', 'demo-icloud'),
      fakeFile('Xcode Backups', 5.4 * GB, 'other', 'demo-icloud'),
    ],
  },
  'demo-local': {
    sourceId: 'demo-local',
    audit: { opportunities: { image_optimization_bytes: 340 * MB } },
    files: [
      fakeFile('design-assets.zip', 3.1 * GB, 'archive', 'demo-local'),
      fakeFile('meet-recording-2024.mp4', 2.8 * GB, 'video', 'demo-local'),
      fakeFile('Photos Library.photoslibrary', 4.9 * GB, 'image', 'demo-local'),
      fakeFile('node_modules backup', 1.4 * GB, 'other', 'demo-local'),
      fakeFile('Misc screenshots', 640 * MB, 'image', 'demo-local'),
    ],
  },
}

export const DEMO_CROSS_SOURCE_GROUPS: CrossSourceGroup[] = [
  {
    id: 'demo-cross-1',
    name: 'Photos Library.photoslibrary',
    recoverableBytes: 4.9 * GB,
    confidence: 'high',
    files: [
      { source_id: 'demo-icloud', source_type: 'icloud', file_id: 'icloud-photos', name: 'Photos Library.photoslibrary', size_bytes: 18.4 * GB, path: '/iCloud Drive/Photos Library.photoslibrary' },
      { source_id: 'demo-local', source_type: 'local', file_id: 'local-photos', name: 'Photos Library.photoslibrary', size_bytes: 4.9 * GB, path: '/Downloads/Photos Library.photoslibrary' },
    ],
  },
  {
    id: 'demo-cross-2',
    name: 'design-assets.zip',
    recoverableBytes: 3.1 * GB,
    confidence: 'high',
    files: [
      { source_id: 'demo-icloud', source_type: 'icloud', file_id: 'icloud-design', name: 'design-assets.zip', size_bytes: 3.1 * GB, path: '/iCloud Drive/Documents/design-assets.zip' },
      { source_id: 'demo-local', source_type: 'local', file_id: 'local-design', name: 'design-assets.zip', size_bytes: 3.1 * GB, path: '/Downloads/design-assets.zip' },
    ],
  },
]

export const DEMO_DUPLICATE_GROUPS: DuplicateGroup[] = [
  { id: 'demo-dup-1', name: 'meet-recording-2024.mp4 (3 copies)', recoverableBytes: 5.6 * GB, files: [] },
  { id: 'demo-dup-2', name: 'Xcode Simulator cache (7 copies)', recoverableBytes: 3.2 * GB, files: [] },
]
