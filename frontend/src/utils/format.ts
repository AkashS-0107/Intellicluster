/**
 * Formatting helpers for precision telemetry and identifiers
 */

export function formatDateTime(isoString?: string | null): string {
  if (!isoString) return '—'
  try {
    const d = new Date(isoString)
    if (isNaN(d.getTime())) return '—'
    return d.toISOString().replace('T', ' ').substring(0, 19) + ' UTC'
  } catch {
    return '—'
  }
}

export function formatRelativeTime(isoString?: string | null): string {
  if (!isoString) return '—'
  try {
    const d = new Date(isoString)
    if (isNaN(d.getTime())) return '—'
    const now = Date.now()
    const diffSec = Math.floor((now - d.getTime()) / 1000)

    if (diffSec < 5) return 'just now'
    if (diffSec < 60) return `${diffSec}s ago`
    const diffMin = Math.floor(diffSec / 60)
    if (diffMin < 60) return `${diffMin}m ago`
    const diffHr = Math.floor(diffMin / 60)
    if (diffHr < 24) return `${diffHr}h ago`
    const diffDay = Math.floor(diffHr / 24)
    return `${diffDay}d ago`
  } catch {
    return '—'
  }
}

export function formatPct(val?: number | null, decimals: number = 1): string {
  if (val === undefined || val === null || isNaN(val)) return '—'
  return `${val.toFixed(decimals)}%`
}

export function formatMemoryMb(mb?: number | null): string {
  if (mb === undefined || mb === null || isNaN(mb)) return '—'
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(1)} GB`
  }
  return `${mb.toFixed(0)} MB`
}

export function formatStorageGb(gb?: number | null): string {
  if (gb === undefined || gb === null || isNaN(gb)) return '—'
  if (gb >= 1024) {
    return `${(gb / 1024).toFixed(1)} TB`
  }
  return `${gb.toFixed(1)} GB`
}

export function formatLatency(ms?: number | null): string {
  if (ms === undefined || ms === null || isNaN(ms)) return '—'
  return `${ms.toFixed(1)} ms`
}

export function formatThroughput(mbps?: number | null): string {
  if (mbps === undefined || mbps === null || isNaN(mbps)) return '—'
  return `${mbps.toFixed(1)} Mbps`
}

export function truncateId(id: string, len: number = 8): string {
  if (!id) return ''
  if (id.length <= len) return id
  return `${id.substring(0, len)}…`
}
