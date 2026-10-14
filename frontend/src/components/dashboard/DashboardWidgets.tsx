import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getClusterCapacity } from '@/api/clusters'
import { getClusterAggregate } from '@/api/telemetry'
import { getHealth } from '@/api/system'
import {
  ClusterResponse,
  NodeResponse,
  WorkloadResponse,
  ClusterCapacitySummary,
} from '@/types'
import { StatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { TableSkeleton } from '@/components/ui/LoadingSkeleton'
import { formatPct, formatMemoryMb, formatLatency, formatDateTime } from '@/utils/format'
import {
  HeartPulse,
  Brain,
  ArrowRight,
  TrendingUp,
  RefreshCw,
  Radio,
  CheckCircle2,
  XCircle,
  Plus,
} from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'

// 1. Cluster Overview and Capacity Widget
interface ClusterCapacityWidgetProps {
  clusters: ClusterResponse[]
  activeClusterId: string
  onSelectCluster: (id: string) => void
  isClustersLoading: boolean
  capacity?: ClusterCapacitySummary
  isCapacityLoading?: boolean
  capacityError?: unknown
  refetchCapacity?: () => void
}

export function ClusterCapacityWidget({
  clusters,
  activeClusterId,
  onSelectCluster,
  isClustersLoading,
  capacity: propCapacity,
  isCapacityLoading: propIsCapacityLoading,
  capacityError: propCapacityError,
  refetchCapacity: propRefetchCapacity,
}: ClusterCapacityWidgetProps) {
  // Query fallback if not provided via props
  const {
    data: queriedCapacity,
    isLoading: isInternalCapacityLoading,
    isFetching: isInternalFetching,
    error: internalCapacityError,
    refetch: internalRefetch,
  } = useQuery({
    queryKey: ['cluster-capacity', activeClusterId],
    queryFn: ({ signal }) => getClusterCapacity(activeClusterId, signal),
    enabled: !!activeClusterId && propCapacity === undefined,
  })

  const capacity = propCapacity !== undefined ? propCapacity : queriedCapacity
  const isCapacityLoading = propIsCapacityLoading !== undefined ? propIsCapacityLoading : isInternalCapacityLoading
  const capacityError = propCapacityError !== undefined ? propCapacityError : internalCapacityError
  const isFetching = propIsCapacityLoading || isInternalFetching
  const refetch = propRefetchCapacity || internalRefetch

  if (isClustersLoading) {
    return <TableSkeleton rows={4} cols={2} />
  }

  if (clusters.length === 0) {
    return (
      <div className="py-8 text-center text-xs text-[#667085] space-y-3">
        <p>No compute clusters registered in the system database.</p>
        <Link to="/clusters" onPointerDown={(e) => e.stopPropagation()}>
          <Button size="xs" variant="primary" icon={<Plus className="w-3 h-3" />}>
            Create First Cluster
          </Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Cluster selector & quick status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2 border-b border-[#EAEFF7]">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-[#667085]">TARGET:</span>
          <select
            value={activeClusterId}
            onChange={(e) => onSelectCluster(e.target.value)}
            onPointerDown={(e) => e.stopPropagation()}
            className="h-8 rounded-lg border border-[#DCE2ED] bg-white px-2.5 text-xs text-[#101828] font-mono focus-visible:outline-none focus-visible:border-[#244DE8] shadow-2xs"
            aria-label="Target Cluster"
          >
            {clusters.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.status})
              </option>
            ))}
          </select>
        </div>

        <Link
          to="/clusters"
          onPointerDown={(e) => e.stopPropagation()}
          className="text-xs text-[#244DE8] hover:underline flex items-center gap-1 font-sans font-medium"
        >
          Manage Clusters <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {isCapacityLoading ? (
        <TableSkeleton rows={3} cols={2} />
      ) : capacityError ? (
        <div className="p-3 text-xs font-mono text-[#B54708] bg-[#FFFAEB] rounded-lg border border-[#FEDF89] flex items-center justify-between">
          <span>Failed to load capacity: {(capacityError as Error).message}</span>
          <Button
            size="xs"
            variant="ghost"
            onClick={() => refetch()}
            isLoading={isFetching}
            onPointerDown={(e) => e.stopPropagation()}
          >
            Retry
          </Button>
        </div>
      ) : capacity ? (
        <div className="space-y-4">
          {/* CPU Cores Breakdown */}
          <div>
            <div className="flex justify-between items-center text-xs mb-1 font-mono">
              <span className="text-[#475467]">CPU CORES HEADROOM</span>
              <span className="text-[#101828]">
                <strong>{capacity.allocated_cpu_cores.toFixed(1)}</strong> allocated /{' '}
                {capacity.total_cpu_cores.toFixed(1)} total ({capacity.allocatable_cpu_cores.toFixed(1)} allocatable)
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-[#F1F5F9] overflow-hidden border border-[#DCE2ED]">
              <div
                className="h-full bg-[#244DE8] transition-all duration-300"
                style={{
                  width: `${
                    capacity.total_cpu_cores > 0
                      ? Math.min(100, (capacity.allocated_cpu_cores / capacity.total_cpu_cores) * 100)
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>

          {/* Memory Breakdown */}
          <div>
            <div className="flex justify-between items-center text-xs mb-1 font-mono">
              <span className="text-[#475467]">RAM MEMORY HEADROOM</span>
              <span className="text-[#101828]">
                <strong>{formatMemoryMb(capacity.allocated_memory_mb)}</strong> allocated /{' '}
                {formatMemoryMb(capacity.total_memory_mb)} total ({formatMemoryMb(capacity.allocatable_memory_mb)} allocatable)
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-[#F1F5F9] overflow-hidden border border-[#DCE2ED]">
              <div
                className="h-full bg-[#027A48] transition-all duration-300"
                style={{
                  width: `${
                    capacity.total_memory_mb > 0
                      ? Math.min(100, (capacity.allocated_memory_mb / capacity.total_memory_mb) * 100)
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>

          {/* 4 Metrics Summary Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-[#EAEFF7] font-mono text-center">
            <div className="bg-[#F8FAFC] p-2.5 rounded-lg border border-[#DCE2ED]">
              <div className="text-[10px] text-[#667085] uppercase">Ready Nodes</div>
              <div className="text-sm font-bold text-[#101828] mt-0.5">
                {capacity.ready_nodes} / {capacity.total_nodes}
              </div>
            </div>
            <div className="bg-[#F8FAFC] p-2.5 rounded-lg border border-[#DCE2ED]">
              <div className="text-[10px] text-[#667085] uppercase">Avg CPU</div>
              <div className="text-sm font-bold text-[#101828] mt-0.5">
                {formatPct(capacity.average_cpu_usage_pct)}
              </div>
            </div>
            <div className="bg-[#F8FAFC] p-2.5 rounded-lg border border-[#DCE2ED]">
              <div className="text-[10px] text-[#667085] uppercase">Avg RAM</div>
              <div className="text-sm font-bold text-[#101828] mt-0.5">
                {formatPct(capacity.average_memory_usage_pct)}
              </div>
            </div>
            <div className="bg-[#F8FAFC] p-2.5 rounded-lg border border-[#DCE2ED]">
              <div className="text-[10px] text-[#667085] uppercase">Tasks</div>
              <div className="text-sm font-bold text-[#244DE8] mt-0.5">
                {capacity.active_workload_count}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

// 2. Compute Fleet Inventory Widget
interface FleetInventoryWidgetProps {
  nodes: NodeResponse[]
  isNodesLoading: boolean
}

export function FleetInventoryWidget({ nodes, isNodesLoading }: FleetInventoryWidgetProps) {
  if (isNodesLoading) {
    return <TableSkeleton rows={4} cols={2} />
  }

  const total = nodes.length
  const ready = nodes.filter((n) => n.status === 'READY').length
  const busy = nodes.filter((n) => n.status === 'BUSY').length
  const degraded = nodes.filter((n) => n.status === 'DEGRADED').length
  const unreachable = nodes.filter((n) => n.status === 'UNREACHABLE').length
  const cordoned = nodes.filter((n) => n.is_cordoned).length

  const meanHealth =
    total > 0
      ? (nodes.reduce((acc, n) => acc + n.health_score, 0) / total).toFixed(1)
      : null

  return (
    <div className="space-y-4">
      {/* Fleet health score banner */}
      <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#F8FAFC] border border-[#DCE2ED]">
        <div>
          <div className="text-xs text-[#475467] font-mono uppercase font-semibold">Fleet Mean Health</div>
          <div className="text-xl font-bold font-mono text-[#101828] mt-0.5">
            {meanHealth !== null ? `${meanHealth} / 100` : '—'}
          </div>
          <div className="text-[10px] text-[#667085] font-mono">
            Derived from deterministic heuristic scoring
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-[#475467] font-mono uppercase font-semibold">Cordoned</div>
          <div className="text-xl font-bold font-mono text-[#B54708] mt-0.5">
            {cordoned}
          </div>
          <div className="text-[10px] text-[#667085] font-mono">Excluded from scheduler</div>
        </div>
      </div>

      {/* Node status breakdown bars */}
      <div className="space-y-2 font-mono text-xs">
        <div className="flex items-center justify-between py-1.5 border-b border-[#EAEFF7]">
          <span className="flex items-center gap-2 text-[#027A48] font-medium">
            <span className="h-2 w-2 rounded-full bg-[#027A48]" /> READY
          </span>
          <span className="font-bold text-[#101828]">{ready}</span>
        </div>
        <div className="flex items-center justify-between py-1.5 border-b border-[#EAEFF7]">
          <span className="flex items-center gap-2 text-[#244DE8] font-medium">
            <span className="h-2 w-2 rounded-full bg-[#244DE8]" /> BUSY
          </span>
          <span className="font-bold text-[#101828]">{busy}</span>
        </div>
        <div className="flex items-center justify-between py-1.5 border-b border-[#EAEFF7]">
          <span className="flex items-center gap-2 text-[#B54708] font-medium">
            <span className="h-2 w-2 rounded-full bg-[#B54708]" /> DEGRADED
          </span>
          <span className="font-bold text-[#101828]">{degraded}</span>
        </div>
        <div className="flex items-center justify-between py-1.5 border-b border-[#EAEFF7]">
          <span className="flex items-center gap-2 text-[#B42318] font-medium">
            <span className="h-2 w-2 rounded-full bg-[#B42318]" /> UNREACHABLE
          </span>
          <span className="font-bold text-[#101828]">{unreachable}</span>
        </div>
      </div>

      <div className="pt-2 flex justify-end">
        <Link
          to="/nodes"
          onPointerDown={(e) => e.stopPropagation()}
          className="text-xs text-[#244DE8] hover:underline flex items-center gap-1 font-sans font-medium"
        >
          View All Nodes ({total}) <ArrowRight className="w-3 h-3" />
        </Link>
      </div>
    </div>
  )
}

// 3. Workload Operations Widget
interface WorkloadOperationsWidgetProps {
  workloads: WorkloadResponse[]
  isWorkloadsLoading: boolean
}

export function WorkloadOperationsWidget({
  workloads,
  isWorkloadsLoading,
}: WorkloadOperationsWidgetProps) {
  if (isWorkloadsLoading) {
    return <TableSkeleton rows={4} cols={2} />
  }

  const counts = {
    PENDING: workloads.filter((w) => w.status === 'PENDING').length,
    SCHEDULED: workloads.filter((w) => w.status === 'SCHEDULED').length,
    RUNNING: workloads.filter((w) => w.status === 'RUNNING').length,
    COMPLETED: workloads.filter((w) => w.status === 'COMPLETED').length,
    FAILED: workloads.filter((w) => w.status === 'FAILED').length,
    CANCELLED: workloads.filter((w) => w.status === 'CANCELLED').length,
  }

  return (
    <div className="space-y-4 font-mono">
      {/* High-level status counters */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-[#E8EEFF] border border-[#C7D7FE] p-2.5 rounded-lg">
          <div className="text-[10px] text-[#244DE8] font-bold uppercase">Pending</div>
          <div className="text-xl font-bold text-[#101828] mt-0.5">{counts.PENDING}</div>
        </div>
        <div className="bg-[#ECFDF3] border border-[#A6F4C5] p-2.5 rounded-lg">
          <div className="text-[10px] text-[#027A48] font-bold uppercase">Running</div>
          <div className="text-xl font-bold text-[#101828] mt-0.5">{counts.RUNNING}</div>
        </div>
        <div className="bg-[#F8FAFC] border border-[#DCE2ED] p-2.5 rounded-lg">
          <div className="text-[10px] text-[#667085] uppercase">Completed</div>
          <div className="text-xl font-bold text-[#101828] mt-0.5">{counts.COMPLETED}</div>
        </div>
      </div>

      {/* Full status list */}
      <div className="space-y-1.5 text-xs">
        {Object.entries(counts).map(([status, count]) => (
          <div
            key={status}
            className="flex items-center justify-between p-2 rounded-lg bg-[#F8FAFC] border border-[#EAEFF7]"
          >
            <StatusBadge status={status as any} />
            <span className="font-bold text-[#101828]">{count}</span>
          </div>
        ))}
      </div>

      <div className="pt-2 flex justify-between items-center">
        <span className="text-[11px] text-[#667085]">
          Total workloads: {workloads.length}
        </span>
        <Link
          to="/workloads"
          onPointerDown={(e) => e.stopPropagation()}
          className="text-xs text-[#244DE8] hover:underline flex items-center gap-1 font-sans font-medium"
        >
          Manage Queue <ArrowRight className="w-3 h-3" />
        </Link>
      </div>
    </div>
  )
}

// 4. Telemetry Observability Widget
interface TelemetryObservabilityWidgetProps {
  activeClusterId: string
  activeClusterName?: string
  aggregate?: import('@/types').AggregatedMetricsSummary
  isAggregateLoading?: boolean
  refetchAggregate?: () => void
}

export function TelemetryObservabilityWidget({
  activeClusterId,
  activeClusterName,
  aggregate: propAggregate,
  isAggregateLoading: propIsAggregateLoading,
  refetchAggregate: propRefetchAggregate,
}: TelemetryObservabilityWidgetProps) {
  const {
    data: queriedAggregate,
    isLoading: isInternalLoading,
    refetch: internalRefetch,
    isFetching,
  } = useQuery({
    queryKey: ['cluster-aggregate', activeClusterId],
    queryFn: ({ signal }) => getClusterAggregate(activeClusterId, signal),
    enabled: !!activeClusterId && propAggregate === undefined,
    refetchInterval: 15000,
  })

  const aggregate = propAggregate !== undefined ? propAggregate : queriedAggregate
  const isLoading = propIsAggregateLoading !== undefined ? propIsAggregateLoading : isInternalLoading
  const refetch = propRefetchAggregate || internalRefetch

  if (!activeClusterId) {
    return (
      <div className="py-8 text-center text-xs text-[#667085]">
        Select a cluster to observe telemetry aggregates.
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="h-44 flex items-center justify-center">
        <TableSkeleton rows={3} cols={2} />
      </div>
    )
  }

  if (!aggregate || aggregate.total_reporting_nodes === 0) {
    return (
      <div className="py-8 text-center text-xs text-[#667085] font-mono space-y-2">
        <p>No active reporting nodes for cluster {activeClusterName || activeClusterId}.</p>
        <p className="text-[11px] text-[#98A2B3]">
          Register compute nodes and transmit heartbeats via Node Inventory to observe live telemetry.
        </p>
      </div>
    )
  }

  const chartData = [
    { name: 'Avg CPU', value: aggregate.avg_cpu_usage_pct },
    { name: 'Max CPU', value: aggregate.max_cpu_usage_pct },
    { name: 'Avg RAM', value: aggregate.avg_memory_usage_pct },
    { name: 'Max RAM', value: aggregate.max_memory_usage_pct },
  ]

  return (
    <div className="space-y-4">
      {/* Chart visualization */}
      <div className="h-40 w-full" onPointerDown={(e) => e.stopPropagation()}>
        <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={120}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#EAEFF7" opacity={0.9} />
            <XAxis dataKey="name" stroke="#667085" fontSize={11} tickLine={false} />
            <YAxis stroke="#667085" fontSize={11} domain={[0, 100]} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#FFFFFF',
                borderColor: '#DCE2ED',
                color: '#101828',
                fontSize: '12px',
                fontFamily: 'monospace',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(16, 24, 40, 0.08)',
              }}
            />
            <Bar dataKey="value" fill="#244DE8" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Aggregate metadata summary */}
      <div className="flex flex-wrap items-center justify-between text-xs font-mono pt-2 border-t border-[#EAEFF7] text-[#475467] gap-2">
        <span>
          Avg Latency: <strong className="text-[#101828]">{formatLatency(aggregate.avg_latency_ms)}</strong>
        </span>
        <span>
          Active Sockets: <strong className="text-[#101828]">{aggregate.total_active_connections}</strong>
        </span>
        <span>
          Reporting: <strong className="text-[#101828]">{aggregate.total_reporting_nodes} nodes</strong>
        </span>
      </div>

      <div className="flex items-center justify-between text-[10px] text-[#667085] font-mono">
        <span>Recorded: {formatDateTime(aggregate.recorded_at)}</span>
        <button
          type="button"
          onClick={() => refetch()}
          onPointerDown={(e) => e.stopPropagation()}
          className="text-[#244DE8] hover:underline flex items-center gap-1 font-semibold"
          aria-label="Refresh telemetry aggregate"
        >
          <RefreshCw className={`w-2.5 h-2.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>
    </div>
  )
}

// 5. Backend Health and Engine Status Widget
export function BackendHealthWidget() {
  const {
    data: health,
    isLoading,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['system-health'],
    queryFn: ({ signal }) => getHealth(signal),
    refetchInterval: 30000,
  })

  const isConnected = !!health && health.status === 'healthy'
  const isDegraded = !!health && health.status === 'degraded'

  return (
    <div className="space-y-3.5 text-xs">
      {/* Service Connection Status */}
      <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#F8FAFC] border border-[#DCE2ED] font-mono">
        <div>
          <div className="text-[10px] text-[#667085] uppercase">FastAPI Backend Status</div>
          <div className="text-sm font-bold flex items-center gap-2 mt-0.5">
            {isLoading ? (
              <span className="text-[#667085]">CONNECTING...</span>
            ) : isConnected ? (
              <span className="text-[#027A48] flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#027A48]" /> ONLINE (v{health?.version || '1.0'})
              </span>
            ) : isDegraded ? (
              <span className="text-[#B54708] flex items-center gap-1.5">
                <Radio className="w-4 h-4 text-[#B54708]" /> DEGRADED DATABASE
              </span>
            ) : (
              <span className="text-[#B42318] flex items-center gap-1.5">
                <XCircle className="w-4 h-4 text-[#B42318]" /> DISCONNECTED
              </span>
            )}
          </div>
        </div>

        <Button
          size="xs"
          variant="outline"
          onClick={() => refetch()}
          isLoading={isFetching}
          onPointerDown={(e) => e.stopPropagation()}
          aria-label="Probe backend health"
        >
          Probe
        </Button>
      </div>

      {/* Operational Engine Policy Notice */}
      <div className="space-y-2 p-3.5 rounded-xl bg-[#F8FAFC] border border-[#EAEFF7] text-[#475467] leading-relaxed">
        <div className="flex items-start gap-2">
          <TrendingUp className="w-4 h-4 text-[#244DE8] shrink-0 mt-0.5" />
          <div>
            <strong className="text-[#101828]">Placement Engine:</strong>
            <p className="mt-0.5">
              Active scheduler: <code className="text-[#244DE8] font-mono font-semibold">HeuristicSchedulerStrategy</code>. Evaluates resource headroom (CPU/RAM) and latency SLAs deterministically.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-2 pt-2 border-t border-[#EAEFF7]">
          <HeartPulse className="w-4 h-4 text-[#027A48] shrink-0 mt-0.5" />
          <div>
            <strong className="text-[#101828]">Health Scoring:</strong>
            <p className="mt-0.5">
              Deterministic penalty formula based on CPU, RAM, and ping latency. Nodes below score 30 degrade automatically.
            </p>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center text-[10px] text-[#667085] font-mono pt-1">
        <span>SQLite WAL: {health?.database || 'OK'}</span>
        <span>Env: {health?.environment || 'dev'}</span>
      </div>
    </div>
  )
}

// 6. Scientific ML Model Registry Summary Widget
export function MlRegistrySummaryWidget() {
  return (
    <div className="space-y-3.5 text-xs text-[#475467]">
      <div className="p-3.5 rounded-xl bg-[#E8EEFF]/40 border border-[#C7D7FE] text-[#101828] space-y-1.5">
        <div className="flex items-center gap-2 text-[#244DE8] font-bold">
          <Brain className="w-4 h-4" />
          <span>Scientific ML Intelligence Boundary</span>
        </div>
        <p className="text-xs text-[#475467] leading-relaxed">
          7 specialized machine learning models have been trained and evaluated offline in Jupyter notebooks across separated baseline datasets.
        </p>
      </div>

      {/* Validation Scorecard */}
      <div className="grid grid-cols-2 gap-3 font-mono text-center">
        <div className="bg-[#ECFDF3] border border-[#A6F4C5] p-3 rounded-xl">
          <div className="text-[10px] text-[#027A48] font-bold uppercase">Validated Offline</div>
          <div className="text-base font-bold text-[#027A48] mt-0.5">5 Models</div>
          <div className="text-[10px] text-[#667085] mt-0.5">K-Means, XGBoost, LSTM, IForest, DQN</div>
        </div>
        <div className="bg-[#FEF3F2] border border-[#FECDCA] p-3 rounded-xl">
          <div className="text-[10px] text-[#B42318] font-bold uppercase">Disqualified / Rejected</div>
          <div className="text-base font-bold text-[#B42318] mt-0.5">2 Models</div>
          <div className="text-[10px] text-[#667085] mt-0.5">Overfit or random parity</div>
        </div>
      </div>

      <div className="p-3 rounded-xl bg-[#F8FAFC] border border-[#DCE2ED] text-[11px] text-[#667085]">
        <strong className="text-[#101828]">Governance Notice:</strong> Machine learning models operate as advisory classifiers, forecasting engines, and shadow placement benchmarks. Active production workload placement is governed by the deterministic heuristic scheduler.
      </div>

      <div className="pt-1 flex justify-end">
        <Link
          to="/ml-registry"
          onPointerDown={(e) => e.stopPropagation()}
          className="text-xs text-[#244DE8] hover:underline flex items-center gap-1 font-sans font-medium"
        >
          Inspect Scientific ML Registry <ArrowRight className="w-3 h-3" />
        </Link>
      </div>
    </div>
  )
}
