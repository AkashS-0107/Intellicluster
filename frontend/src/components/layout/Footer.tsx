import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getHealth } from '@/api/system'
import { ShieldCheck, Terminal, Boxes, Sparkles } from 'lucide-react'
import { cn } from '@/utils/cn'

export function Footer() {
  const currentYear = new Date().getFullYear()

  const {
    data: health,
    isError,
    isLoading,
  } = useQuery({
    queryKey: ['system-health'],
    queryFn: ({ signal }) => getHealth(signal),
    refetchInterval: 30000,
    retry: 1,
  })

  const isConnected = !isError && !!health && health.status === 'healthy'
  const isDegraded = !isError && !!health && health.status === 'degraded'
  const isOffline = isError || (!isLoading && (!health || (health.status !== 'healthy' && health.status !== 'degraded')))

  return (
    <footer
      role="contentinfo"
      className="border-t border-[#DCE2ED] bg-white text-[#101828] select-none shrink-0"
    >
      <div className="max-w-[1600px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
        {/* Main 3-column Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 lg:gap-12">
          {/* Column 1: Product Identity & Architectural Scope (col-span-5) */}
          <div className="md:col-span-5 space-y-3">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-[#244DE8] text-white shadow-2xs shrink-0">
                <ShieldCheck className="h-3.5 w-3.5" />
              </div>
              <span className="font-mono text-xs font-bold tracking-wider text-[#101828] uppercase">
                INTELLICLUSTER
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono border border-[#C7D7FE] bg-[#E8EEFF] text-[#244DE8] font-semibold">
                CONTROL PLANE
              </span>
            </div>

            <p className="text-xs font-medium text-[#475467] leading-relaxed">
              ML-Driven Cloud Server Clustering and Workload Orchestration
            </p>

            <p className="text-[11px] text-[#667085] leading-relaxed font-sans">
              Active workload placement is deterministic, driven by the Heuristic Placement Engine evaluating CPU/RAM headroom and latency SLAs. Machine learning models provide specialized inference, telemetry trajectory forecasting, and shadow placement evaluation.
            </p>
          </div>

          {/* Column 2: Structured Navigation Directory (col-span-4) */}
          <nav aria-label="Footer Navigation" className="md:col-span-4">
            <div className="grid grid-cols-3 gap-4">
              {/* Group: Operations */}
              <div className="space-y-2.5">
                <div className="flex items-center gap-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-[#475467]">
                  <Terminal className="w-3 h-3 text-[#244DE8]" />
                  <span>Operations</span>
                </div>
                <ul className="space-y-1.5 text-xs font-medium">
                  <li>
                    <Link
                      to="/app"
                      className="text-[#667085] hover:text-[#244DE8] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#244DE8] rounded px-1 -mx-1 py-0.5"
                      aria-label="Footer navigation: System Overview"
                    >
                      Overview
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/workloads"
                      className="text-[#667085] hover:text-[#244DE8] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#244DE8] rounded px-1 -mx-1 py-0.5"
                      aria-label="Footer navigation: Task Orchestration"
                    >
                      Task Queue
                    </Link>
                  </li>
                </ul>
              </div>

              {/* Group: Infrastructure */}
              <div className="space-y-2.5">
                <div className="flex items-center gap-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-[#475467]">
                  <Boxes className="w-3 h-3 text-[#244DE8]" />
                  <span>Infrastructure</span>
                </div>
                <ul className="space-y-1.5 text-xs font-medium">
                  <li>
                    <Link
                      to="/clusters"
                      className="text-[#667085] hover:text-[#244DE8] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#244DE8] rounded px-1 -mx-1 py-0.5"
                      aria-label="Footer navigation: Compute Clusters"
                    >
                      Clusters
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/nodes"
                      className="text-[#667085] hover:text-[#244DE8] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#244DE8] rounded px-1 -mx-1 py-0.5"
                      aria-label="Footer navigation: Server Hardware"
                    >
                      Hardware Nodes
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/telemetry"
                      className="text-[#667085] hover:text-[#244DE8] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#244DE8] rounded px-1 -mx-1 py-0.5"
                      aria-label="Footer navigation: Live Telemetry"
                    >
                      Telemetry
                    </Link>
                  </li>
                </ul>
              </div>

              {/* Group: Intelligence */}
              <div className="space-y-2.5">
                <div className="flex items-center gap-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-[#475467]">
                  <Sparkles className="w-3 h-3 text-[#244DE8]" />
                  <span>Intelligence</span>
                </div>
                <ul className="space-y-1.5 text-xs font-medium">
                  <li>
                    <Link
                      to="/ml-registry"
                      className="text-[#667085] hover:text-[#244DE8] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#244DE8] rounded px-1 -mx-1 py-0.5"
                      aria-label="Footer navigation: Offline Model Registry"
                    >
                      Model Registry
                    </Link>
                  </li>
                </ul>
              </div>
            </div>
          </nav>

          {/* Column 3: Grounded Runtime & System Diagnostics (col-span-3) */}
          <div className="md:col-span-3 space-y-2.5 font-mono text-xs">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-[#475467]">
              System Runtime
            </div>

            {/* Live Service Status */}
            <div className="p-3 rounded-xl bg-[#F8FAFC] border border-[#DCE2ED] space-y-1.5 shadow-2xs">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-[#667085]">API STATUS:</span>
                <span
                  className={cn(
                    'font-semibold inline-flex items-center gap-1.5',
                    isConnected && 'text-emerald-700',
                    isDegraded && 'text-amber-700',
                    isOffline && 'text-red-700',
                    isLoading && 'text-[#667085]'
                  )}
                >
                  <span
                    className={cn(
                      'h-1.5 w-1.5 rounded-full shrink-0',
                      isConnected && 'bg-emerald-500',
                      isDegraded && 'bg-amber-500',
                      isOffline && 'bg-red-500',
                      isLoading && 'bg-[#98A2B3] animate-pulse'
                    )}
                  />
                  <span>
                    {isLoading
                      ? 'PROBING'
                      : isConnected
                      ? 'ONLINE'
                      : isDegraded
                      ? 'DEGRADED'
                      : 'OFFLINE'}
                  </span>
                </span>
              </div>

              {/* Version (only when valid in health response) */}
              {health?.version && (
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#667085]">VERSION:</span>
                  <span className="text-[#101828] font-semibold">v{health.version}</span>
                </div>
              )}

              {/* Environment (only when valid in health response) */}
              {health?.environment && (
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#667085]">ENVIRONMENT:</span>
                  <span className="text-[#244DE8] font-semibold uppercase">{health.environment}</span>
                </div>
              )}

              {/* Database Status (only when valid in health response) */}
              {health?.database && (
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#667085]">DATABASE:</span>
                  <span className="text-[#101828] truncate max-w-[120px]" title={health.database}>
                    {health.database === 'healthy' ? 'SQLITE (WAL)' : health.database}
                  </span>
                </div>
              )}

              {/* Scheduler Engine Specification */}
              <div className="flex items-center justify-between text-[11px] pt-1.5 border-t border-[#EAEFF7]">
                <span className="text-[#667085]">SCHEDULER:</span>
                <span className="text-[#101828] font-semibold">HEURISTIC v1.0</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Sub-footer: Zero em-dashes */}
        <div className="border-t border-[#EAEFF7] mt-8 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] font-mono text-[#667085]">
          <div>
            © {currentYear} INTELLICLUSTER - Operational Control Plane
          </div>
          <div className="flex items-center gap-3">
            <span>Deterministic Placement</span>
            <span>//</span>
            <span>Empirical ML Benchmarks</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
