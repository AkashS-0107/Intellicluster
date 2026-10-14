import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { listClusters } from '@/api/clusters'
import { listNodes } from '@/api/nodes'
import {
  getClusterAggregate,
  getNodeTelemetryHistory,
  getNodeHistoryReadiness,
  getSimulatorStatus,
  startSimulator,
  stopSimulator,
} from '@/api/telemetry'
import { Card, CardHeader, CardTitle, CardContent, MetricCard } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { TableSkeleton } from '@/components/ui/LoadingSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import {
  runNodeForecasting,
  runOfflineEvaluation,
  LSTMForecastingResponse,
} from '@/api/ml'
import { OfflineEvaluationResponse } from '@/types'
import {
  formatDateTime,
  formatLatency,
  formatPct,
} from '@/utils/format'
import {
  Activity,
  Layers,
  Server,
  Radio,
  Clock,
  Brain,
  AlertTriangle,
  Play,
  Square,
  CheckCircle2,
  Database,
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  AreaChart,
  Area,
} from 'recharts'

export function TelemetryPage() {
  const queryClient = useQueryClient()
  const [selectedClusterId, setSelectedClusterId] = useState<string>('')
  const [selectedNodeId, setSelectedNodeId] = useState<string>('')

  // LSTM Live Node Forecasting State
  const [forecastData, setForecastData] = useState<LSTMForecastingResponse | null>(null)
  const [forecastError, setForecastError] = useState<string | null>(null)
  const [isForecastLoading, setIsForecastLoading] = useState(false)

  // Simulator Control State
  const [simInterval, setSimInterval] = useState<number>(10)
  const [simActionError, setSimActionError] = useState<string | null>(null)
  const [isSimActionLoading, setIsSimActionLoading] = useState<boolean>(false)

  // Offline Dataset Benchmark State
  const [offlineData, setOfflineData] = useState<OfflineEvaluationResponse | null>(null)
  const [offlineError, setOfflineError] = useState<string | null>(null)
  const [isOfflineLoading, setIsOfflineLoading] = useState<boolean>(false)

  // 1. Clusters query
  const { data: clusters = [], isLoading: isClustersLoading } = useQuery({
    queryKey: ['clusters'],
    queryFn: ({ signal }) => listClusters({ limit: 100 }, signal),
  })

  const isFleetMode = selectedClusterId === 'ALL'
  const activeClusterId = isFleetMode
    ? (clusters.length > 0 ? clusters[0].id : '')
    : (selectedClusterId || (clusters.length > 0 ? clusters[0].id : ''))

  // 2. Nodes query
  const { data: nodes = [], isLoading: isNodesLoading } = useQuery({
    queryKey: ['nodes', isFleetMode ? 'ALL' : activeClusterId],
    queryFn: ({ signal }) =>
      listNodes(
        {
          cluster_id: isFleetMode ? undefined : (activeClusterId || undefined),
          limit: 100,
        },
        signal
      ),
  })

  const activeNodeId = selectedNodeId || (nodes.length > 0 ? nodes[0].id : '')

  // 3. Cluster aggregate telemetry query
  const {
    data: aggregate,
    isLoading: isAggregateLoading,
    error: aggregateError,
    refetch: refetchAggregate,
  } = useQuery({
    queryKey: ['cluster-aggregate', activeClusterId],
    queryFn: ({ signal }) => getClusterAggregate(activeClusterId, signal),
    enabled: !!activeClusterId,
    refetchInterval: 15000,
  })

  // 4. Node historical telemetry query
  const {
    data: history = [],
    isLoading: isHistoryLoading,
    error: historyError,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['node-telemetry-history', activeNodeId],
    queryFn: ({ signal }) => getNodeTelemetryHistory(activeNodeId, 50, signal),
    enabled: !!activeNodeId,
    refetchInterval: 15000,
  })

  // 5. Node History Readiness Query (for 168h LSTM validation)
  const { data: readiness } = useQuery({
    queryKey: ['node-history-readiness', activeNodeId],
    queryFn: ({ signal }) => getNodeHistoryReadiness(activeNodeId, signal),
    enabled: !!activeNodeId,
    refetchInterval: 10000,
  })

  // 6. Opt-In Simulator Status Query
  const { data: simStatus } = useQuery({
    queryKey: ['simulator-status'],
    queryFn: ({ signal }) => getSimulatorStatus(signal),
    refetchInterval: 5000,
  })

  // Format node history chronologically for Recharts
  const chartData = [...history].reverse().map((sample) => {
    let timeLabel = ''
    try {
      const d = new Date(sample.recorded_at)
      timeLabel = d.toTimeString().split(' ')[0]
    } catch {
      timeLabel = '—'
    }

    return {
      time: timeLabel,
      fullTime: formatDateTime(sample.recorded_at),
      cpu: sample.cpu_usage_pct,
      memory: sample.memory_usage_pct,
      disk: sample.disk_usage_pct,
      latency: sample.network_latency_ms,
      tx: sample.network_tx_mbps,
      rx: sample.network_rx_mbps,
      sockets: sample.active_connections,
    }
  })

  // Simulator Handlers
  const handleStartSimulator = async () => {
    setIsSimActionLoading(true)
    setSimActionError(null)
    try {
      await startSimulator(simInterval, activeNodeId || undefined)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['simulator-status'] }),
        queryClient.invalidateQueries({ queryKey: ['node-history-readiness'] }),
        queryClient.invalidateQueries({ queryKey: ['node-telemetry-history'] }),
      ])
    } catch (err: any) {
      setSimActionError(err.message || 'Failed to start telemetry simulator')
    } finally {
      setIsSimActionLoading(false)
    }
  }

  const handleStopSimulator = async () => {
    setIsSimActionLoading(true)
    setSimActionError(null)
    try {
      await stopSimulator()
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['simulator-status'] }),
        queryClient.invalidateQueries({ queryKey: ['node-history-readiness'] }),
      ])
    } catch (err: any) {
      setSimActionError(err.message || 'Failed to stop telemetry simulator')
    } finally {
      setIsSimActionLoading(false)
    }
  }

  // Live Node Forecast Request
  const handleRequestForecast = async () => {
    if (!activeNodeId) return
    setIsForecastLoading(true)
    setForecastError(null)
    setForecastData(null)
    try {
      const res = await runNodeForecasting(activeNodeId)
      setForecastData(res)
    } catch (err: any) {
      setForecastError(err.message || 'Failed to generate 24h LSTM forecast')
    } finally {
      setIsForecastLoading(false)
    }
  }

  // Offline Dataset Benchmark Request
  const handleRunOfflineBenchmark = async () => {
    setIsOfflineLoading(true)
    setOfflineError(null)
    setOfflineData(null)
    try {
      const res = await runOfflineEvaluation(0)
      setOfflineData(res)
    } catch (err: any) {
      setOfflineError(err.message || 'Failed to evaluate offline historical dataset')
    } finally {
      setIsOfflineLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Scope Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl border border-[#DCE2ED] bg-white shadow-sm">
        <div className="flex flex-wrap items-center gap-4">
          {/* Cluster Selector */}
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#244DE8]" />
            <span className="text-xs font-mono font-semibold text-[#667085]">CLUSTER:</span>
            <select
              value={selectedClusterId || (clusters.length > 0 ? clusters[0].id : '')}
              onChange={(e) => {
                setSelectedClusterId(e.target.value)
                setSelectedNodeId('') // Reset node selection on cluster switch
              }}
              className="h-8 rounded-lg border border-[#DCE2ED] bg-[#F5F7FB] px-2.5 text-xs text-[#101828] font-mono focus-visible:outline-none focus-visible:border-[#244DE8] focus-visible:ring-1 focus-visible:ring-[#244DE8]"
              disabled={isClustersLoading}
              aria-label="Select Cluster"
            >
              <option value="ALL">ALL FLEET NODES</option>
              {clusters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.status})
                </option>
              ))}
            </select>
          </div>

          {/* Node Selector */}
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-[#244DE8]" />
            <span className="text-xs font-mono font-semibold text-[#667085]">NODE HISTORICAL:</span>
            <select
              value={activeNodeId}
              onChange={(e) => setSelectedNodeId(e.target.value)}
              className="h-8 rounded-lg border border-[#DCE2ED] bg-[#F5F7FB] px-2.5 text-xs text-[#101828] font-mono focus-visible:outline-none focus-visible:border-[#244DE8] focus-visible:ring-1 focus-visible:ring-[#244DE8]"
              disabled={isNodesLoading || nodes.length === 0}
              aria-label="Select Node for Historical Metrics"
            >
              {nodes.length === 0 ? (
                <option value="">No nodes in selected cluster</option>
              ) : (
                nodes.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.hostname} ({n.status})
                  </option>
                ))
              )}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-[#667085]">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#244DE8] opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#244DE8]" />
          </span>
          <span>POLLING: 15s CADENCE</span>
        </div>
      </div>

      {/* SECTION 1: Cluster Real-Time Aggregated Telemetry */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#101828] font-mono flex items-center gap-2">
            <Radio className="w-4 h-4 text-[#244DE8]" />
            Cluster Real-Time Aggregates
          </h2>
          {aggregate && (
            <span className="text-[11px] font-mono text-[#667085]">
              Aggregated from {aggregate.total_reporting_nodes} nodes // {formatDateTime(aggregate.recorded_at)}
            </span>
          )}
        </div>

        {aggregateError && (
          <ErrorState
            title="Cluster Aggregation Failure"
            message={(aggregateError as Error).message}
            onRetry={() => refetchAggregate()}
          />
        )}

        {isAggregateLoading ? (
          <TableSkeleton rows={2} cols={4} />
        ) : aggregate && aggregate.total_reporting_nodes > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <MetricCard
              label="Avg CPU Usage"
              value={formatPct(aggregate.avg_cpu_usage_pct)}
              subtext={`Peak: ${formatPct(aggregate.max_cpu_usage_pct)}`}
              variant="cyan"
            />
            <MetricCard
              label="Max CPU Usage"
              value={formatPct(aggregate.max_cpu_usage_pct)}
              subtext="Highest node thread"
              variant={aggregate.max_cpu_usage_pct > 85 ? 'warning' : 'default'}
            />
            <MetricCard
              label="Avg RAM Usage"
              value={formatPct(aggregate.avg_memory_usage_pct)}
              subtext={`Peak: ${formatPct(aggregate.max_memory_usage_pct)}`}
              variant="default"
            />
            <MetricCard
              label="Max RAM Usage"
              value={formatPct(aggregate.max_memory_usage_pct)}
              subtext="Highest node RAM"
              variant={aggregate.max_memory_usage_pct > 85 ? 'warning' : 'default'}
            />
            <MetricCard
              label="Mean Ping Latency"
              value={formatLatency(aggregate.avg_latency_ms)}
              subtext="Round-trip echo"
              variant={aggregate.avg_latency_ms > 20 ? 'warning' : 'default'}
            />
            <MetricCard
              label="Active Sockets"
              value={aggregate.total_active_connections}
              subtext={`Across ${aggregate.total_reporting_nodes} nodes`}
              variant="cyan"
            />
          </div>
        ) : (
          <div className="p-6 rounded-xl border border-[#DCE2ED] bg-white text-center text-xs font-mono text-[#667085] shadow-sm space-y-1">
            <div className="font-semibold text-[#101828]">No Reporting Nodes in Selected Cluster</div>
            <div>There are currently zero nodes transmitting heartbeats for this cluster. Register nodes and transmit heartbeats to observe live telemetry measurements.</div>
          </div>
        )}
      </div>

      {/* SECTION 2: Node Historical Time-Series Telemetry */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#101828] font-mono flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#244DE8]" />
            Historical Node Telemetry Time-Series
          </h2>
          {history.length > 0 && (
            <span className="text-[11px] font-mono text-[#667085]">
              {history.length} snapshots recorded (most recent 50 samples)
            </span>
          )}
        </div>

        {historyError && (
          <ErrorState
            title="Historical Query Failure"
            message={(historyError as Error).message}
            onRetry={() => refetchHistory()}
          />
        )}

        {isHistoryLoading ? (
          <TableSkeleton rows={6} cols={2} />
        ) : chartData.length === 0 ? (
          <EmptyState
            title="No Telemetry History for Selected Node"
            description="This compute node has not yet submitted any periodic heartbeat or telemetry snapshots. Use the Node Inventory to transmit simulated heartbeats."
            icon={<Activity className="w-6 h-6 stroke-[1.5]" />}
          />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart 1: CPU, RAM, & Disk Utilization */}
            <Card>
              <CardHeader>
                <CardTitle>
                  <span>Resource Utilization (% Capacity)</span>
                  <span className="text-[11px] font-mono text-[#667085] font-normal">
                    CPU / RAM / Disk
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#244DE8" stopOpacity={0.25} />
                          <stop offset="95%" stopColor="#244DE8" stopOpacity={0.0} />
                        </linearGradient>
                        <linearGradient id="memGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#027A48" stopOpacity={0.25} />
                          <stop offset="95%" stopColor="#027A48" stopOpacity={0.0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#EAEFF7" />
                      <XAxis dataKey="time" stroke="#667085" fontSize={11} tickLine={false} />
                      <YAxis stroke="#667085" fontSize={11} domain={[0, 100]} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#FFFFFF',
                          borderColor: '#DCE2ED',
                          borderRadius: '8px',
                          boxShadow: '0 4px 12px rgba(16,24,40,0.08)',
                          color: '#101828',
                          fontSize: '11px',
                          fontFamily: 'monospace',
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />
                      <Area
                        type="monotone"
                        dataKey="cpu"
                        name="CPU Usage %"
                        stroke="#244DE8"
                        fillOpacity={1}
                        fill="url(#cpuGradient)"
                        strokeWidth={2}
                      />
                      <Area
                        type="monotone"
                        dataKey="memory"
                        name="RAM Usage %"
                        stroke="#027A48"
                        fillOpacity={1}
                        fill="url(#memGradient)"
                        strokeWidth={2}
                      />
                      <Line
                        type="monotone"
                        dataKey="disk"
                        name="Disk %"
                        stroke="#B54708"
                        strokeWidth={1.5}
                        dot={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Chart 2: Network Latency & Throughput */}
            <Card>
              <CardHeader>
                <CardTitle>
                  <span>Network Latency & Throughput</span>
                  <span className="text-[11px] font-mono text-[#667085] font-normal">
                    Ping (ms) & TX/RX (Mbps)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#EAEFF7" />
                      <XAxis dataKey="time" stroke="#667085" fontSize={11} tickLine={false} />
                      <YAxis stroke="#667085" fontSize={11} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#FFFFFF',
                          borderColor: '#DCE2ED',
                          borderRadius: '8px',
                          boxShadow: '0 4px 12px rgba(16,24,40,0.08)',
                          color: '#101828',
                          fontSize: '11px',
                          fontFamily: 'monospace',
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />
                      <Line
                        type="monotone"
                        dataKey="latency"
                        name="Ping Latency (ms)"
                        stroke="#B42318"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="tx"
                        name="TX (Mbps)"
                        stroke="#0284C7"
                        strokeWidth={1.5}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="rx"
                        name="RX (Mbps)"
                        stroke="#7C3AED"
                        strokeWidth={1.5}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* SECTION 3: Model 3 — Temporal Multivariate Resource Forecasting */}
      <div className="space-y-6 pt-6 border-t border-[#DCE2ED]">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-[#244DE8]" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#101828] font-mono">
                Model 3: Temporal Multivariate Resource Forecasting (24h Ahead)
              </h2>
            </div>
            <p className="text-xs font-mono text-[#667085] mt-1">
              Dual-layer Stacked LSTM &bull; 168h Lookback (7 Days) &bull; 24h Output Horizon &bull; Targets: CPU, Memory, Workload
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={handleRunOfflineBenchmark}
              isLoading={isOfflineLoading}
              className="font-mono text-xs border-[#DCE2ED]"
            >
              <Database className="w-3.5 h-3.5 mr-1 text-[#244DE8]" />
              Run Offline Dataset Benchmark
            </Button>
            <Button
              size="sm"
              variant="primary"
              onClick={handleRequestForecast}
              isLoading={isForecastLoading}
              disabled={!activeNodeId || isNodesLoading || !readiness?.is_ready}
              className={`font-mono text-xs shrink-0 ${
                readiness?.is_ready
                  ? 'bg-[#244DE8] text-white'
                  : 'bg-[#98A2B3] text-white cursor-not-allowed opacity-60'
              }`}
            >
              <Brain className="w-3.5 h-3.5 mr-1" />
              {readiness?.is_ready
                ? 'Request 24h Live Node Forecast'
                : `Forecast Locked (${readiness?.valid_hourly_observations || 0}/168h)`}
            </Button>
          </div>
        </div>

        {/* 1. Historical Telemetry Readiness Card */}
        <Card className="border border-[#DCE2ED] shadow-sm">
          <CardHeader className="pb-3 border-b border-[#EAEFF7]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <CardTitle className="text-xs font-mono font-semibold text-[#101828] flex items-center gap-2">
                <Clock className="w-4 h-4 text-[#244DE8]" />
                <span>Historical Lookback Timeline Readiness (Selected Node: {nodes.find(n => n.id === activeNodeId)?.hostname || activeNodeId || 'None'})</span>
              </CardTitle>
              {readiness?.is_ready ? (
                <span className="px-2.5 py-0.5 text-[11px] font-mono font-semibold rounded-md bg-[#ECFDF3] text-[#027A48] border border-[#A6F4C5] flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  168/168 CONTIGUOUS HOURS READY
                </span>
              ) : (
                <span className="px-2.5 py-0.5 text-[11px] font-mono font-semibold rounded-md bg-[#FFFAEB] text-[#B54708] border border-[#FEDF89] flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  INSUFFICIENT HISTORY ({readiness?.valid_hourly_observations || 0} / 168 HOURS)
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            {/* Readiness Progress Bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono text-[#475467]">
                <span>Contiguous 7-Day Window Completion</span>
                <span className="font-semibold text-[#101828]">
                  {readiness?.valid_hourly_observations || 0} of {readiness?.required_observations || 168} hours ({readiness?.readiness_percentage || 0}%)
                </span>
              </div>
              <div className="w-full h-2.5 bg-[#F2F4F7] rounded-full overflow-hidden border border-[#EAECF0]">
                <div
                  className="h-full bg-gradient-to-r from-[#244DE8] to-[#444CE7] transition-all duration-300"
                  style={{ width: `${Math.min(100, Math.max(0, readiness?.readiness_percentage || 0))}%` }}
                />
              </div>
            </div>

            {/* Metrics Breakdown Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-1">
              <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0]">
                <div className="text-[11px] font-mono text-[#64748B]">CONTIGUOUS VALID HOURS</div>
                <div className="text-base font-mono font-bold text-[#0F172A] mt-0.5">
                  {readiness?.valid_hourly_observations || 0} / 168
                </div>
                <div className="text-[10px] font-mono text-[#64748B] mt-0.5">
                  {readiness?.is_ready ? 'Full lookback window' : `${Math.round(readiness?.estimated_hours_remaining || 168)}h accumulation needed`}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0]">
                <div className="text-[11px] font-mono text-[#64748B]">TOTAL RAW SNAPSHOTS</div>
                <div className="text-base font-mono font-bold text-[#0F172A] mt-0.5">
                  {readiness?.total_raw_snapshots ?? history.length}
                </div>
                <div className="text-[10px] font-mono text-[#64748B] mt-0.5">
                  Binned to 1h UTC buckets
                </div>
              </div>

              <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0]">
                <div className="text-[11px] font-mono text-[#64748B]">USABLE TIMELINE SPAN</div>
                <div className="text-[11px] font-mono font-semibold text-[#0F172A] mt-1 truncate" title={readiness?.earliest_usable_timestamp ? formatDateTime(readiness.earliest_usable_timestamp) : '—'}>
                  From: {readiness?.earliest_usable_timestamp ? formatDateTime(readiness.earliest_usable_timestamp) : '—'}
                </div>
                <div className="text-[11px] font-mono font-semibold text-[#0F172A] truncate" title={readiness?.latest_usable_timestamp ? formatDateTime(readiness.latest_usable_timestamp) : '—'}>
                  To: {readiness?.latest_usable_timestamp ? formatDateTime(readiness.latest_usable_timestamp) : '—'}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0]">
                <div className="text-[11px] font-mono text-[#64748B]">DATA PIPELINE SOURCE</div>
                <div className="mt-1">
                  <span className={`px-2 py-0.5 text-[10px] font-mono font-semibold rounded ${
                    simStatus?.is_running
                      ? 'bg-[#EFF8FF] text-[#175CD3] border border-[#B2DDFF]'
                      : readiness?.is_simulated
                      ? 'bg-[#FEF6EE] text-[#B93815] border border-[#F9DBAF]'
                      : 'bg-[#ECFDF3] text-[#027A48] border border-[#A6F4C5]'
                  }`}>
                    {simStatus?.is_running
                      ? 'SIMULATOR ACTIVE'
                      : readiness?.is_simulated
                      ? 'SIMULATED DATA'
                      : 'LIVE HARDWARE AGENT'}
                  </span>
                </div>
                <div className="text-[10px] font-mono text-[#64748B] mt-1">
                  {simStatus?.is_running ? `Cadence: ${simStatus.interval_seconds}s` : 'Periodic heartbeats'}
                </div>
              </div>
            </div>

            {/* Validation Explanation / Insufficient Notice */}
            {readiness && !readiness.is_ready && (
              <div className="p-3.5 rounded-lg border border-[#FEDF89] bg-[#FFFAEB] text-xs font-mono space-y-1.5">
                <div className="font-bold text-[#B54708] flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>Validation Status: {readiness.validation_reason}</span>
                </div>
                {readiness.missing_ranges && readiness.missing_ranges.length > 0 && (
                  <div className="text-[11px] text-[#7A271A] pt-1">
                    <strong>Detected Missing Interval Gaps:</strong>
                    <ul className="list-disc list-inside mt-0.5 space-y-0.5">
                      {readiness.missing_ranges.map((gap, i) => (
                        <li key={i}>{gap}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <p className="text-[11px] text-[#475467]">
                  <strong>Operational Rule:</strong> The LSTM model requires 168 contiguous hourly snapshots (7 full days) without temporal gaps. Multiple snapshots within the same hour are aggregated into one hourly sample and do not inflate the valid hour count.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 2. Opt-In Telemetry Simulator Controls */}
        <Card className="border border-[#DCE2ED] shadow-sm bg-[#FCFCFD]">
          <CardHeader className="pb-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <CardTitle className="text-xs font-mono font-semibold text-[#101828] flex items-center gap-2">
                  <Radio className="w-4 h-4 text-[#244DE8]" />
                  <span>Opt-In Development Telemetry Simulator</span>
                </CardTitle>
                <p className="text-[11px] font-mono text-[#667085] mt-0.5">
                  Controlled background process that transmits genuine timestamped TelemetrySnapshots without backdating.
                </p>
              </div>

              {/* Status Indicator */}
              <div className="flex items-center gap-2 text-xs font-mono">
                {simStatus?.is_running ? (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#ECFDF3] text-[#027A48] border border-[#A6F4C5] font-semibold text-[11px]">
                    <span className="w-2 h-2 rounded-full bg-[#12B76A] animate-pulse" />
                    RUNNING ({simStatus.snapshots_emitted} snapshots emitted)
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#F2F4F7] text-[#475467] border border-[#D0D5DD] font-semibold text-[11px]">
                    <span className="w-2 h-2 rounded-full bg-[#98A2B3]" />
                    STOPPED (IDLE)
                  </span>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            {simActionError && (
              <div className="mb-3 p-2.5 text-xs font-mono text-[#B42318] bg-[#FEF3F2] rounded-lg border border-[#FECDCA]">
                {simActionError}
              </div>
            )}

            <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-[#475467]">Emission Cadence:</span>
                <select
                  value={simInterval}
                  onChange={(e) => setSimInterval(Number(e.target.value))}
                  disabled={simStatus?.is_running || isSimActionLoading}
                  className="h-8 rounded-lg border border-[#DCE2ED] bg-white px-2.5 text-xs text-[#101828] font-mono focus-visible:outline-none focus-visible:border-[#244DE8]"
                  aria-label="Simulator Interval"
                >
                  <option value={5}>5 seconds (Rapid test)</option>
                  <option value={10}>10 seconds (Standard demo)</option>
                  <option value={30}>30 seconds</option>
                  <option value={60}>60 seconds (1 minute)</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                {simStatus?.is_running ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleStopSimulator}
                    isLoading={isSimActionLoading}
                    className="text-[#B42318] hover:bg-[#FEF3F2] border border-[#FECDCA] font-mono text-xs"
                  >
                    <Square className="w-3.5 h-3.5 mr-1 fill-current" />
                    Stop Simulator
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={handleStartSimulator}
                    isLoading={isSimActionLoading}
                    disabled={!activeNodeId}
                    className="bg-[#244DE8] text-white font-mono text-xs"
                  >
                    <Play className="w-3.5 h-3.5 mr-1 fill-current" />
                    Start Simulator (Opt-In)
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Insufficient History / Live Forecast Error Box */}
        {forecastError && (
          <div className="p-4 rounded-xl border border-[#FEDF89] bg-[#FFFAEB] text-[#B54708] text-xs font-mono space-y-1">
            <div className="font-bold flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4" />
              Live Forecasting Request Rejected:
            </div>
            <p className="text-[11px] text-[#7A271A] leading-relaxed">
              {forecastError}
            </p>
            <p className="text-[11px] text-[#475467] pt-1">
              <strong>Tip:</strong> While historical timeline accumulates, use the <strong>Run Offline Dataset Benchmark</strong> action above to verify Model 3 inference against the genuine training corpus.
            </p>
          </div>
        )}

        {/* Live Forecast Output Visualization */}
        {forecastData && (
          <Card className="border border-[#A6F4C5] shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-[#027A48]" />
                  <span>Live Node 24-Hour Multivariate Forecast</span>
                  <span className="text-[11px] font-mono text-[#667085] font-normal">
                    Node: {forecastData.node_id || activeNodeId}
                  </span>
                </CardTitle>
                <span className="text-[10px] font-mono font-semibold bg-[#ECFDF3] text-[#027A48] px-2 py-0.5 rounded border border-[#A6F4C5]">
                  168h CONTIGUOUS TELEMETRY EVALUATED
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={forecastData.predictions}
                    margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#EAEFF7" />
                    <XAxis
                      dataKey="step_hour"
                      stroke="#667085"
                      fontSize={11}
                      tickLine={false}
                      tickFormatter={(val) => `+${val}h`}
                    />
                    <YAxis stroke="#667085" fontSize={11} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#FFFFFF',
                        borderColor: '#DCE2ED',
                        borderRadius: '8px',
                        boxShadow: '0 4px 12px rgba(16,24,40,0.08)',
                        color: '#101828',
                        fontSize: '11px',
                        fontFamily: 'monospace',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />
                    <Line
                      type="monotone"
                      dataKey="predicted_cpu_utilization"
                      name="Forecast CPU %"
                      stroke="#244DE8"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="predicted_memory_usage"
                      name="Forecast RAM %"
                      stroke="#027A48"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="predicted_workload"
                      name="Forecast Workload"
                      stroke="#E11D48"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Offline Dataset Benchmark Visualization */}
        {offlineError && (
          <div className="p-3.5 text-xs font-mono text-[#B42318] bg-[#FEF3F2] rounded-lg border border-[#FECDCA]">
            Offline Benchmark Error: {offlineError}
          </div>
        )}

        {offlineData && (
          <Card className="border border-[#B2DDFF] bg-[#F8FAFC] shadow-sm">
            <CardHeader className="border-b border-[#E2E8F0] pb-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <CardTitle className="flex items-center gap-2 text-xs font-mono font-bold text-[#0F172A]">
                  <Database className="w-4 h-4 text-[#244DE8]" />
                  <span>Offline Dataset Benchmark (24h Ahead Forecast)</span>
                </CardTitle>
                <span className="text-[10px] font-mono font-semibold bg-[#EFF8FF] text-[#175CD3] px-2 py-0.5 rounded border border-[#B2DDFF]">
                  HISTORICAL DATASET: {offlineData.dataset_name}
                </span>
              </div>
              <p className="text-[11px] font-mono text-[#64748B] mt-1">
                {offlineData.advisory}
              </p>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={offlineData.predictions}
                    margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis
                      dataKey="step_hour"
                      stroke="#64748B"
                      fontSize={11}
                      tickLine={false}
                      tickFormatter={(val) => `+${val}h`}
                    />
                    <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#FFFFFF',
                        borderColor: '#E2E8F0',
                        borderRadius: '8px',
                        boxShadow: '0 4px 12px rgba(15,23,42,0.08)',
                        color: '#0F172A',
                        fontSize: '11px',
                        fontFamily: 'monospace',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />
                    <Line
                      type="monotone"
                      dataKey="predicted_cpu_utilization"
                      name="Benchmark Forecast CPU %"
                      stroke="#244DE8"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="predicted_memory_usage"
                      name="Benchmark Forecast RAM %"
                      stroke="#027A48"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="predicted_workload"
                      name="Benchmark Forecast Workload"
                      stroke="#E11D48"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
