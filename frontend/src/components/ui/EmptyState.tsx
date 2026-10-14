import React from 'react'
import { cn } from '@/utils/cn'
import { Inbox } from 'lucide-react'
import { Button } from './Button'

export interface EmptyStateProps {
  title: string
  description?: string
  icon?: React.ReactNode
  action?: {
    label: string
    onClick: () => void
    icon?: React.ReactNode
  }
  className?: string
}

export function EmptyState({
  title,
  description,
  icon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-dashed border-[#DCE2ED] p-8 text-center flex flex-col items-center justify-center bg-white/70 shadow-xs',
        className
      )}
    >
      <div className="rounded-full bg-[#F8FAFC] p-3 text-[#667085] mb-3 border border-[#DCE2ED]">
        {icon || <Inbox className="w-6 h-6 stroke-[1.5]" />}
      </div>
      <h4 className="text-sm font-semibold text-[#101828]">{title}</h4>
      {description && (
        <p className="mt-1 text-xs text-[#667085] max-w-sm leading-relaxed">{description}</p>
      )}
      {action && (
        <div className="mt-4">
          <Button
            size="sm"
            variant="secondary"
            onClick={action.onClick}
            icon={action.icon}
          >
            {action.label}
          </Button>
        </div>
      )}
    </div>
  )
}

export { ErrorState } from './ErrorState'
export type { ErrorStateProps } from './ErrorState'
