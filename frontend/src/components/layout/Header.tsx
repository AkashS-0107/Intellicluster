import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import { getHealth } from '@/api/system'
import { RefreshCw, Radio, AlertOctagon, Menu, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'

const ROUTE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Fleet Overview', subtitle: 'Global cluster topology and active telemetry' },
  '/app': { title: 'Fleet Overview', subtitle: 'Global cluster topology and active telemetry' },
  '/clusters': { title: 'Cluster Management', subtitle: 'Compute clusters, capacity, and resource quotas' },
  '/nodes': { title: 'Node Inventory', subtitle: 'Server hardware, operational health, and cordoning' },
  '/workloads': { title: 'Workload Orchestration', subtitle: 'Heuristic placement scheduler and task state machines' },
  '/telemetry': { title: 'Telemetry Observability', subtitle: 'Cluster aggregates and time-series hardware metrics' },
  '/ml-registry': { title: 'Machine Learning Model Catalog', subtitle: 'Offline validation benchmark and integration status' },
}

interface HeaderProps {
  onToggleMobileMenu?: () => void
}

export function Header({ onToggleMobileMenu }: HeaderProps) {
  const location = useLocation()
  const queryClient = useQueryClient()
  const currentRoute = ROUTE_TITLES[location.pathname] || {
    title: 'Operational Control Plane',
    subtitle: 'System Control',
  }

  const {
    data: health,
    error: healthError,
    isLoading: isHealthLoading,
    isFetching: isHealthFetching,
  } = useQuery({
    queryKey: ['system-health'],
    queryFn: ({ signal }) => getHealth(signal),
    refetchInterval: 30000,
    retry: 1,
  })

  const isConnected = !!health && health.status === 'healthy'
  const isDegraded = !!health && health.status === 'degraded'

  const handleRefreshAll = () => {
    queryClient.invalidateQueries()
  }

  return (
    <header className="flex h-15 items-center justify-between border-b border-[#DCE2ED] bg-white/95 backdrop-blur-md px-4 sm:px-6 shrink-0 z-10 select-none shadow-2xs">
      {/* Left: Mobile Menu Toggle + Brand Mark & Semantic Breadcrumb */}
      <div className="flex items-center gap-3">
        {/* Mobile Hamburger Toggle (hidden on desktop lg) */}
        <button
          type="button"
          onClick={onToggleMobileMenu}
          className="lg:hidden p-1.5 rounded-lg text-[#667085] hover:text-[#101828] hover:bg-[#F1F5F9] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#244DE8]"
          aria-label="Toggle navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Brand Mark Icon on mobile / condensed view */}
        <div className="lg:hidden flex h-7 w-7 items-center justify-center rounded-lg bg-[#244DE8] text-white shadow-xs shrink-0">
          <ShieldCheck className="h-4 w-4" />
        </div>

        {/* Semantic Breadcrumb / Page Title */}
        <nav aria-label="Breadcrumb" className="flex items-center">
          <ol className="flex items-center gap-2 text-xs font-mono">
            <li className="flex items-center gap-1.5">
              <span className="font-bold text-[#244DE8] tracking-wider">INTELLICLUSTER</span>
              <span className="text-[#98A2B3] text-[11px]" aria-hidden="true">/</span>
            </li>
            <li className="flex items-center gap-2">
              <h1 className="text-sm font-semibold text-[#101828] tracking-tight font-sans">
                <span>{currentRoute.title}</span>
              </h1>
              <span className="hidden md:inline text-[11px] font-normal text-[#667085] font-mono border-l border-[#DCE2ED] pl-2">
                {currentRoute.subtitle}
              </span>
            </li>
          </ol>
        </nav>
      </div>

      {/* Right: Heuristic Engine Badge, Backend Connectivity & Actions */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Concise Product Descriptor */}
        <span className="hidden xl:inline text-[11px] font-mono text-[#667085] uppercase tracking-wide">
          OPERATIONAL CONTROL PLANE
        </span>

        {/* Engine Spec Indicator */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-[#DCE2ED] bg-[#F8FAFC] text-[10px] font-mono text-[#475467]">
          <span>SCHEDULER:</span>
          <span className="text-[#244DE8] font-bold">HEURISTIC v1.0</span>
        </div>

        {/* Backend Connectivity Indicator with Real Health Status */}
        <div
          className={cn(
            'flex items-center gap-2 px-2.5 py-1 rounded-md border text-xs font-mono transition-colors shadow-2xs',
            isHealthLoading
              ? 'border-[#DCE2ED] bg-[#F8FAFC] text-[#667085]'
              : isConnected
              ? 'border-[#A6F4C5] bg-[#ECFDF3] text-[#027A48]'
              : isDegraded
              ? 'border-[#FEDF89] bg-[#FFFAEB] text-[#B54708]'
              : 'border-[#FECDCA] bg-[#FEF3F2] text-[#B42318]'
          )}
          title={
            healthError
              ? `Backend Connection Failed: ${healthError instanceof Error ? healthError.message : 'Unreachable'}`
              : `FastAPI Backend: ${health?.version || 'Active'} | DB: ${health?.database || 'OK'}`
          }
        >
          {isConnected ? (
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#027A48]" />
            </span>
          ) : isDegraded ? (
            <Radio className="w-3.5 h-3.5 text-[#B54708] animate-pulse" />
          ) : (
            <AlertOctagon className="w-3.5 h-3.5 text-[#B42318]" />
          )}

          <span className="hidden sm:inline font-medium">
            {isHealthLoading
              ? 'PROBING...'
              : isConnected
              ? `FASTAPI v${health?.version || '1.0'}`
              : isDegraded
              ? 'DEGRADED DB'
              : 'BACKEND OFFLINE'}
          </span>
          <span className="sm:hidden font-medium">
            {isHealthLoading ? 'PROBING' : isConnected ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>

        {/* Global Cache Refresh / Sync Button */}
        <Button
          size="xs"
          variant="outline"
          onClick={handleRefreshAll}
          isLoading={isHealthFetching}
          icon={<RefreshCw className={cn('w-3 h-3', isHealthFetching && 'animate-spin')} />}
          title="Refresh active telemetry and caches"
          aria-label="Sync all data"
        >
          <span className="hidden sm:inline">Sync</span>
        </Button>
      </div>
    </header>
  )
}
