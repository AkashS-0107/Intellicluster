import { useState } from 'react'
import {
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  X,
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { BranchedMenu } from '@/components/navigation/BranchedMenu'

interface SidebarProps {
  isMobile?: boolean
  onCloseMobile?: () => void
  className?: string
}

export function Sidebar({ isMobile = false, onCloseMobile, className }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  // In mobile drawer mode, never collapse to narrow rail
  const effectivelyCollapsed = !isMobile && isCollapsed

  return (
    <aside
      className={cn(
        'relative flex flex-col border-r border-[#DCE2ED] bg-white transition-all duration-200 select-none shrink-0 z-20',
        effectivelyCollapsed ? 'w-16' : 'w-64',
        isMobile ? 'h-full border-r-0' : 'h-screen',
        className
      )}
    >
      {/* Brand Header */}
      <div className="flex h-15 items-center justify-between border-b border-[#DCE2ED] px-3.5 shrink-0">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#244DE8] text-white shadow-xs shrink-0">
            <ShieldCheck className="h-4 w-4" />
          </div>
          {!effectivelyCollapsed && (
            <div className="flex flex-col">
              <span className="font-mono text-xs font-bold tracking-wider text-[#101828] uppercase">
                INTELLICLUSTER
              </span>
              <span className="text-[10px] text-[#667085] tracking-tight font-mono font-medium">
                MANAGEMENT CONSOLE
              </span>
            </div>
          )}
        </div>

        {/* Desktop collapse toggle or Mobile close button */}
        {isMobile ? (
          <button
            type="button"
            onClick={onCloseMobile}
            className="rounded-lg p-1 text-[#667085] hover:bg-[#F1F5F9] hover:text-[#101828] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#244DE8]"
            title="Close navigation"
            aria-label="Close navigation"
          >
            <X className="h-4 w-4" />
          </button>
        ) : (
          <button
            type="button"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="rounded-lg p-1 text-[#667085] hover:bg-[#F1F5F9] hover:text-[#101828] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#244DE8]"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        )}
      </div>

      {/* Hierarchical Branched Navigation */}
      <div className="flex-1 overflow-y-auto p-3">
        <BranchedMenu
          isCollapsed={effectivelyCollapsed}
          onNavigate={onCloseMobile}
        />
      </div>

      {/* Footer Info */}
      {!effectivelyCollapsed && (
        <div className="border-t border-[#EAEFF7] bg-[#F8FAFC] p-3 text-[10px] text-[#667085] font-mono space-y-0.5 shrink-0">
          <div className="flex justify-between">
            <span>CORE SPEC</span>
            <span className="text-[#344054] font-medium">v1.0.0</span>
          </div>
          <div className="flex justify-between">
            <span>ENGINE</span>
            <span className="text-[#244DE8] font-bold">HEURISTIC</span>
          </div>
        </div>
      )}
    </aside>
  )
}
