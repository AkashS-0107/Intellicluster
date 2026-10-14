import { cn } from '@/utils/cn'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from './Button'

export interface ErrorStateProps {
  title?: string
  message: string
  errorCode?: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({
  title = 'Operational Error',
  message,
  errorCode,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-[#FECDCA] bg-[#FEF3F2] p-5 text-left flex items-start gap-3.5 shadow-xs',
        className
      )}
    >
      <div className="rounded-lg bg-white p-2 text-[#D92D20] shrink-0 border border-[#FECDCA] shadow-2xs">
        <AlertCircle className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-semibold text-[#B42318]">{title}</h4>
          {errorCode && (
            <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-white text-[#B42318] uppercase tracking-wider border border-[#FECDCA]">
              {errorCode}
            </span>
          )}
        </div>
        <p className="mt-1 text-xs text-[#7A271A] leading-relaxed break-words font-mono">
          {message}
        </p>
        {onRetry && (
          <div className="mt-3">
            <Button
              size="xs"
              variant="outline"
              onClick={onRetry}
              icon={<RefreshCw className="w-3 h-3" />}
              className="border-[#FDA29B] bg-white hover:bg-[#FEE4E2] text-[#B42318]"
            >
              Retry Action
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
