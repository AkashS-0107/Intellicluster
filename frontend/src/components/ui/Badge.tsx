import React from 'react'
import { cn } from '@/utils/cn'
import {
  ClusterStatus,
  NodeStatus,
  WorkloadPriority,
  WorkloadStatus,
  WorkloadType,
} from '@/types'

export interface BadgeProps {
  className?: string
  children: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'critical' | 'cyan' | 'neutral'
}

export function Badge({ className, children, variant = 'default' }: BadgeProps) {
  const variantStyles = {
    default: 'bg-[#F1F5F9] text-[#344054] border-[#DCE2ED]',
    neutral: 'bg-[#F8FAFC] text-[#475467] border-[#DCE2ED]',
    success: 'bg-[#ECFDF3] text-[#027A48] border-[#A6F4C5]',
    warning: 'bg-[#FFFAEB] text-[#B54708] border-[#FEDF89]',
    critical: 'bg-[#FEF3F2] text-[#B42318] border-[#FECDCA]',
    cyan: 'bg-[#E8EEFF] text-[#244DE8] border-[#C7D7FE]',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium tracking-wide uppercase border select-none',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  )
}

export function StatusBadge({ status }: { status: ClusterStatus | NodeStatus | WorkloadStatus }) {
  let variant: BadgeProps['variant'] = 'default'

  switch (status) {
    // Healthy / Success states
    case 'ACTIVE':
    case 'READY':
    case 'COMPLETED':
      variant = 'success'
      break

    // Progressing / Busy states
    case 'BUSY':
    case 'RUNNING':
    case 'SCHEDULED':
      variant = 'cyan'
      break

    // Warning / Degraded / Transition states
    case 'PENDING':
    case 'INITIALIZING':
    case 'DRAINING':
    case 'MAINTENANCE':
    case 'DEGRADED':
      variant = 'warning'
      break

    // Critical / Offline / Cancelled / Failed
    case 'FAILED':
    case 'UNREACHABLE':
    case 'OFFLINE':
    case 'CANCELLED':
      variant = 'critical'
      break
  }

  return <Badge variant={variant}>{status}</Badge>
}

export function PriorityBadge({ priority }: { priority: WorkloadPriority }) {
  const config: Record<WorkloadPriority, { variant: BadgeProps['variant']; label: string }> = {
    LOW: { variant: 'neutral', label: 'LOW' },
    NORMAL: { variant: 'default', label: 'NORMAL' },
    HIGH: { variant: 'warning', label: 'HIGH' },
    CRITICAL: { variant: 'critical', label: 'CRITICAL' },
  }

  const { variant, label } = config[priority] || { variant: 'default', label: priority }
  return <Badge variant={variant}>{label}</Badge>
}

export function WorkloadTypeBadge({ type }: { type: WorkloadType }) {
  return <Badge variant="cyan">{type}</Badge>
}

export function RiskScoreBadge({ riskScore }: { riskScore?: number | null }) {
  return (
    <div className="inline-flex items-center gap-1.5" title="Static backend default score; ML inference adapter is not connected">
      <span className="font-mono text-xs text-[#475467]">
        {riskScore !== undefined && riskScore !== null ? riskScore.toFixed(2) : '—'}
      </span>
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono tracking-tight bg-[#F1F5F9] text-[#667085] border border-[#DCE2ED]">
        ML adapter not connected
      </span>
    </div>
  )
}
