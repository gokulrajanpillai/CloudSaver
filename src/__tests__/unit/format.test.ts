import { describe, expect, it } from 'vitest'
import { formatBytes, relativeTime } from '@/lib/format'

describe('formatBytes', () => {
  it('returns "0 B" for 0', () => expect(formatBytes(0)).toBe('0 B'))
  it('returns "0 B" for undefined', () => expect(formatBytes(undefined)).toBe('0 B'))
  it('returns "0 B" for negative numbers', () => expect(formatBytes(-1024)).toBe('0 B'))
  it('formats 1 byte', () => expect(formatBytes(1)).toBe('1 B'))
  it('formats 1023 bytes stays in B', () => expect(formatBytes(1023)).toBe('1023 B'))
  it('formats 1024 as KB', () => expect(formatBytes(1024)).toBe('1.0 KB'))
  it('formats 1 MB', () => expect(formatBytes(1024 ** 2)).toBe('1.0 MB'))
  it('formats 1 GB', () => expect(formatBytes(1024 ** 3)).toBe('1.0 GB'))
  it('formats 1 TB', () => expect(formatBytes(1024 ** 4)).toBe('1.0 TB'))
  it('formats fractional MB', () => expect(formatBytes(1.5 * 1024 ** 2)).toBe('1.5 MB'))
  it('formats fractional GB', () => expect(formatBytes(34.2 * 1024 ** 3)).toBe('34.2 GB'))
  it('rounds to 1 decimal for KB+', () => {
    const val = formatBytes(1536) // 1.5 KB
    expect(val).toBe('1.5 KB')
  })
})

describe('relativeTime', () => {
  it('returns "Never scanned" for undefined', () => expect(relativeTime(undefined)).toBe('Never scanned'))
  it('returns "Never scanned" for empty string', () => expect(relativeTime('')).toBe('Never scanned'))

  it('shows minutes for recent scans', () => {
    const iso = new Date(Date.now() - 4 * 60 * 1000).toISOString()
    expect(relativeTime(iso)).toBe('Scanned 4m ago')
  })

  it('shows at least 1m for very recent scans', () => {
    const iso = new Date(Date.now() - 10 * 1000).toISOString()
    expect(relativeTime(iso)).toBe('Scanned 1m ago')
  })

  it('shows hours when >= 60 minutes', () => {
    const iso = new Date(Date.now() - 120 * 60 * 1000).toISOString()
    expect(relativeTime(iso)).toBe('Scanned 2h ago')
  })

  it('shows days when >= 48 hours', () => {
    const iso = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
    expect(relativeTime(iso)).toBe('Scanned 3d ago')
  })

  it('shows hours for 47 hours (below 48h threshold)', () => {
    const iso = new Date(Date.now() - 47 * 60 * 60 * 1000).toISOString()
    expect(relativeTime(iso)).toBe('Scanned 47h ago')
  })
})
