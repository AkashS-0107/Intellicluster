import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listNodes,
  registerNode,
  cordonNode,
  uncordonNode,
  getNodeCapacity,
  sendNodeHeartbeat,
} from '@/api/nodes'
import { listClusters } from '@/api/clusters'
import {
  NodeCapacitySummary,
  NodeRegister,
  NodeResponse,
  NodeStatus,
  TelemetryCreate,
} from '@/types'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { TableSkeleton } from '@/components/ui/LoadingSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { Button } from '@/components/ui/Button'
import { StatusBadge, RiskScoreBadge } from '@/components/ui/Badge'
import { Modal, Drawer } from '@/components/ui/Modal'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Input, Select } from '@/components/ui/FormControls'
import {
  formatDateTime,
  formatRelativeTime,
  formatMemoryMb,
  truncateId,
} from '@/utils/format'
import {
  Plus,
  Server,
  Shield,
  ShieldAlert,
  HardDrive,
  Radio,
} from 'lucide-react'

export function NodesPage() {
  const queryClient = useQueryClient()
  const [clusterFilter, setClusterFilter] = useState<string>('ALL')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')

  // Modals state
  const [isRegisterOpen, setIsRegisterOpen] = useState(false)
  const [registerError, setRegisterError] = useState<string | null>(null)
  const [regHostname, setRegHostname] = useState('')
  const [regIp, setRegIp] = useState('')
  const [regClusterId, setRegClusterId] = useState('')
  const [regCpus, setRegCpus] = useState('8')
  const [regMemoryMb, setRegMemoryMb] = useState('16384')
  const [regStorageGb, setRegStorageGb] = useState('500')
  const [regNetworkMbps, setRegNetworkMbps] = useState('1000')

  // Cordon / Uncordon confirmation state
  const [cordonTarget, setCordonTarget] = useState<{ node: NodeResponse; action: 'cordon' | 'uncordon' } | null>(null)

  // Node Capacity Drawer
  const [selectedCapacityNodeId, setSelectedCapacityNodeId] = useState<string | null>(null)

  // Heartbeat Simulator Drawer
  const [simulatorNode, setSimulatorNode] = useState<NodeResponse | null>(null)
  const [simCpu, setSimCpu] = useState('45.0')
  const [simMemMb, setSimMemMb] = useState('8192')
  const [simMemPct, setSimMemPct] = useState('50.0')
  const [simDiskGb, setSimDiskGb] = useState('120')
  const [simDiskPct, setSimDiskPct] = useState('24.0')
  const [simTx, setSimTx] = useState('12.5')
  const [simRx, setSimRx] = useState('25.0')
  const [simLatency, setSimLatency] = useState('4.2')
  const [simConnections, setSimConnections] = useState('24')
  const [simStatus, setSimStatus] = useState<NodeStatus>('READY')
  const [simulatorError, setSimulatorError] = useState<string | null>(null)

  // Query clusters for filter dropdown
  const { data: clusters = [] } = useQuery({
    queryKey: ['clusters'],
    queryFn: ({ signal }) => listClusters({ limit: 100 }, signal),
  })

  // Query nodes
  const {
    data: nodes = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['nodes', clusterFilter, statusFilter],
    queryFn: ({ signal }) =>
      listNodes(
        {
          cluster_id: clusterFilter === 'ALL' ? undefined : clusterFilter,
          status: statusFilter === 'ALL' ? undefined : (statusFilter as NodeStatus),
          limit: 200,
        },
        signal
      ),
  })

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: (payload: NodeRegister) => registerNode(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] })
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      queryClient.invalidateQueries({ queryKey: ['cluster-capacity'] })
      queryClient.invalidateQueries({ queryKey: ['cluster-aggregate'] })
      setIsRegisterOpen(false)
      setRegHostname('')
      setRegIp('')
      setRegClusterId('')
      setRegCpus('8')
      setRegMemoryMb('16384')
      setRegStorageGb('500')
      setRegNetworkMbps('1000')
      setRegisterError(null)
    },
    onError: (err: any) => {
      setRegisterError(err.message || 'Failed to register node')
    },
  })

  // Cordon mutation
  const cordonMutation = useMutation({
    mutationFn: (nodeId: string) => cordonNode(nodeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] })
      queryClient.invalidateQueries({ queryKey: ['cluster-capacity'] })
      queryClient.invalidateQueries({ queryKey: ['node-capacity'] })
      setCordonTarget(null)
    },
    onError: (err: any) => {
      alert(`Cordon failed: ${err.message}`)
      setCordonTarget(null)
    },
  })

  // Uncordon mutation
  const uncordonMutation = useMutation({
    mutationFn: (nodeId: string) => uncordonNode(nodeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] })
      queryClient.invalidateQueries({ queryKey: ['cluster-capacity'] })
      queryClient.invalidateQueries({ queryKey: ['node-capacity'] })
      setCordonTarget(null)
    },
    onError: (err: any) => {
      alert(`Uncordon failed: ${err.message}`)
      setCordonTarget(null)
    },
  })

  // Heartbeat mutation
  const heartbeatMutation = useMutation({
    mutationFn: ({ nodeId, data }: { nodeId: string; data: TelemetryCreate }) =>
      sendNodeHeartbeat(nodeId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] })
      queryClient.invalidateQueries({ queryKey: ['cluster-aggregate'] })
      queryClient.invalidateQueries({ queryKey: ['cluster-capacity'] })
      queryClient.invalidateQueries({ queryKey: ['node-capacity'] })
      queryClient.invalidateQueries({ queryKey: ['node-telemetry-history'] })
      setSimulatorNode(null)
      setSimulatorError(null)
    },
    onError: (err: any) => {
      setSimulatorError(err.message || 'Failed to submit heartbeat telemetry')
    },
  })

  const handleRegisterSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!regHostname.trim()) {
      setRegisterError('Hostname is required')
      return
    }
    const cpuVal = parseFloat(regCpus)
    const memVal = parseFloat(regMemoryMb)
    const diskVal = parseFloat(regStorageGb)
    const bwVal = parseFloat(regNetworkMbps)

    if (isNaN(cpuVal) || cpuVal <= 0) {
      setRegisterError('CPU cores must be a positive number')
      return
    }
    if (isNaN(memVal) || memVal <= 0) {
      setRegisterError('RAM must be a positive number')
      return
    }

    setRegisterError(null)
    registerMutation.mutate({
      hostname: regHostname.trim(),
      ip_address: regIp.trim() || undefined,
      cluster_id: regClusterId || undefined,
      cpu_cores: cpuVal,
      memory_mb: memVal,
      storage_gb: isNaN(diskVal) ? 100 : diskVal,
      network_bandwidth_mbps: isNaN(bwVal) ? 1000 : bwVal,
    })
  }

  const handleSimulatorSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!simulatorNode) return

    setSimulatorError(null)
    heartbeatMutation.mutate({
      nodeId: simulatorNode.id,
      data: {
        cpu_usage_pct: parseFloat(simCpu) || 0,
        memory_usage_mb: parseFloat(simMemMb) || 0,
        memory_usage_pct: parseFloat(simMemPct) || 0,
        disk_usage_gb: parseFloat(simDiskGb) || 0,
        disk_usage_pct: parseFloat(simDiskPct) || 0,
        network_tx_mbps: parseFloat(simTx) || 0,
        network_rx_mbps: parseFloat(simRx) || 0,
        network_latency_ms: parseFloat(simLatency) || 0,
        active_connections: parseInt(simConnections, 10) || 0,
        reported_status: simStatus,
      },
    })
  }

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Cluster filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#667085]">CLUSTER:</span>
            <select
              value={clusterFilter}
              onChange={(e) => setClusterFilter(e.target.value)}
              className="h-8 rounded-lg border border-[#DCE2ED] bg-white px-2.5 text-xs text-[#101828] font-mono focus-visible:outline-none focus-visible:border-[#244DE8] shadow-2xs"
            >
              <option value="ALL">ALL CLUSTERS</option>
              {clusters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#667085]">STATUS:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-8 rounded-lg border border-[#DCE2ED] bg-white px-2.5 text-xs text-[#101828] font-mono focus-visible:outline-none focus-visible:border-[#244DE8] shadow-2xs"
            >
              <option value="ALL">ALL STATUSES</option>
              <option value="READY">READY</option>
              <option value="BUSY">BUSY</option>
              <option value="INITIALIZING">INITIALIZING</option>
              <option value="DEGRADED">DEGRADED</option>
              <option value="UNREACHABLE">UNREACHABLE</option>
              <option value="DRAINING">DRAINING</option>
              <option value="OFFLINE">OFFLINE</option>
            </select>
          </div>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={() => {
            setRegisterError(null)
            setIsRegisterOpen(true)
          }}
          icon={<Plus className="w-3.5 h-3.5" />}
        >
          Register Compute Node
        </Button>
      </div>

      {/* Error state */}
      {error && (
        <ErrorState
          title="Node Inventory Query Failed"
          message={error instanceof Error ? error.message : 'Failed to query nodes'}
          onRetry={() => refetch()}
        />
      )}

      {/* Dense Inventory Table */}
      {isLoading ? (
        <TableSkeleton rows={6} cols={9} />
      ) : nodes.length === 0 ? (
        <EmptyState
          title="No Compute Nodes Found"
          description={
            clusterFilter !== 'ALL' || statusFilter !== 'ALL'
              ? 'No nodes match the active filter criteria.'
              : 'There are currently no compute nodes registered in the inventory.'
          }
          icon={<Server className="w-6 h-6 stroke-[1.5]" />}
          action={{
            label: 'Register Compute Node',
            onClick: () => setIsRegisterOpen(true),
            icon: <Plus className="w-4 h-4" />,
          }}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Hostname / Node ID</TableHead>
              <TableHead>IP Address</TableHead>
              <TableHead>Cluster</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Hardware (CPU / RAM)</TableHead>
              <TableHead>Health Score</TableHead>
              <TableHead>Risk Score</TableHead>
              <TableHead>Tasks</TableHead>
              <TableHead>Last Heartbeat</TableHead>
              <TableHead className="text-right">Operations</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {nodes.map((node) => {
              const cluster = clusters.find((c) => c.id === node.cluster_id)
              return (
                <TableRow key={node.id}>
                  <TableCell>
                    <div className="font-semibold text-[#101828] font-sans">{node.hostname}</div>
                    <div className="text-[10px] text-[#667085]" title={node.id}>
                      {truncateId(node.id, 8)}
                    </div>
                  </TableCell>
                  <TableCell className="text-[#667085]">
                    {node.ip_address || '—'}
                  </TableCell>
                  <TableCell className="text-[#475467] font-sans">
                    {cluster ? cluster.name : node.cluster_id ? truncateId(node.cluster_id, 8) : 'Unassigned'}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1.5">
                      <StatusBadge status={node.status} />
                      {node.is_cordoned && (
                        <span
                          className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-[#FFFAEB] text-[#B54708] border border-[#FEDF89] font-semibold"
                          title="Node cordoned: No new workloads scheduled"
                        >
                          CORDONED
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium text-[#101828]">{node.cpu_cores} Cores</div>
                    <div className="text-[#667085] text-[11px]">
                      {formatMemoryMb(node.memory_mb)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1.5">
                      <div
                        className={`h-2 w-2 rounded-full ${
                          node.health_score >= 70
                            ? 'bg-[#027A48]'
                            : node.health_score >= 30
                            ? 'bg-[#B54708]'
                            : 'bg-[#B42318]'
                        }`}
                      />
                      <span className="font-bold text-[#101828]">{node.health_score.toFixed(1)}</span>
                      <span className="text-[10px] text-[#667085]">/100</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <RiskScoreBadge riskScore={node.risk_score} />
                  </TableCell>
                  <TableCell className="text-[#244DE8] font-bold">
                    {node.active_workload_count}
                  </TableCell>
                  <TableCell className="text-[#667085] text-[11px]" title={formatDateTime(node.last_heartbeat)}>
                    {formatRelativeTime(node.last_heartbeat)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {/* Cordon / Uncordon Toggle */}
                      {node.is_cordoned ? (
                        <Button
                          size="xs"
                          variant="outline"
                          onClick={() => setCordonTarget({ node, action: 'uncordon' })}
                          icon={<Shield className="w-3 h-3 text-[#027A48]" />}
                          title="Uncordon node"
                        >
                          Uncordon
                        </Button>
                      ) : (
                        <Button
                          size="xs"
                          variant="ghost"
                          onClick={() => setCordonTarget({ node, action: 'cordon' })}
                          icon={<ShieldAlert className="w-3 h-3 text-[#B54708]" />}
                          title="Cordon node"
                        >
                          Cordon
                        </Button>
                      )}

                      {/* Capacity Inspector */}
                      <Button
                        size="xs"
                        variant="ghost"
                        onClick={() => setSelectedCapacityNodeId(node.id)}
                        icon={<HardDrive className="w-3 h-3" />}
                        title="Allocatable capacity"
                      >
                        Capacity
                      </Button>

                      {/* Heartbeat Simulator */}
                      <Button
                        size="xs"
                        variant="secondary"
                        onClick={() => {
                          setSimulatorNode(node)
                          setSimCpu(String(node.current_cpu_usage_pct || 40.0))
                          setSimMemMb(String(node.current_memory_usage_mb || 4096))
                          setSimStatus(node.status)
                          setSimulatorError(null)
                        }}
                        icon={<Radio className="w-3 h-3 text-[#244DE8]" />}
                        title="Simulate heartbeat report"
                      >
                        Heartbeat
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      )}

      {/* Node Registration Modal */}
      <Modal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        title="Register Compute Node"
        description="Register a new bare-metal, VM, or containerized server with capacity specifications."
        maxWidth="lg"
      >
        <form onSubmit={handleRegisterSubmit} className="space-y-4">
          {registerError && (
            <div className="p-3 text-xs font-mono text-[#B42318] bg-[#FEF3F2] rounded-lg border border-[#FECDCA]">
              {registerError}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input
              label="Node Hostname (FQDN)"
              placeholder="node-compute-01.local"
              value={regHostname}
              onChange={(e) => setRegHostname(e.target.value)}
              required
              isMono
            />
            <Input
              label="IP Address (IPv4 / IPv6)"
              placeholder="192.168.1.101"
              value={regIp}
              onChange={(e) => setRegIp(e.target.value)}
              isMono
            />
          </div>

          <Select
            label="Target Cluster Assignment"
            value={regClusterId}
            onChange={(e) => setRegClusterId(e.target.value)}
          >
            <option value="">Unassigned (Standalone)</option>
            {clusters.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.status})
              </option>
            ))}
          </Select>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Input
              label="CPU Cores"
              type="number"
              step="0.5"
              min="0.5"
              value={regCpus}
              onChange={(e) => setRegCpus(e.target.value)}
              required
              isMono
            />
            <Input
              label="RAM (MB)"
              type="number"
              step="1"
              min="256"
              value={regMemoryMb}
              onChange={(e) => setRegMemoryMb(e.target.value)}
              required
              isMono
            />
            <Input
              label="Storage (GB)"
              type="number"
              step="1"
              min="1"
              value={regStorageGb}
              onChange={(e) => setRegStorageGb(e.target.value)}
              isMono
            />
            <Input
              label="Bandwidth (Mbps)"
              type="number"
              step="10"
              min="10"
              value={regNetworkMbps}
              onChange={(e) => setRegNetworkMbps(e.target.value)}
              isMono
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-[#EAEFF7]">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsRegisterOpen(false)}
              disabled={registerMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={registerMutation.isPending}>
              Register Node
            </Button>
          </div>
        </form>
      </Modal>

      {/* Cordon / Uncordon Confirmation */}
      {cordonTarget && (
        <ConfirmDialog
          isOpen={true}
          onClose={() => setCordonTarget(null)}
          onConfirm={() => {
            if (cordonTarget.action === 'cordon') {
              cordonMutation.mutate(cordonTarget.node.id)
            } else {
              uncordonMutation.mutate(cordonTarget.node.id)
            }
          }}
          title={
            cordonTarget.action === 'cordon'
              ? `Cordon Node ${cordonTarget.node.hostname}?`
              : `Uncordon Node ${cordonTarget.node.hostname}?`
          }
          message={
            cordonTarget.action === 'cordon'
              ? `Cordoning isolates "${cordonTarget.node.hostname}" from new workload scheduling placements. Existing running tasks will not be disrupted.`
              : `Uncordoning "${cordonTarget.node.hostname}" will re-enable the node for workload placement in the scheduler.`
          }
          confirmLabel={cordonTarget.action === 'cordon' ? 'Cordon Node' : 'Uncordon Node'}
          variant={cordonTarget.action === 'cordon' ? 'danger' : 'primary'}
          isLoading={cordonMutation.isPending || uncordonMutation.isPending}
        />
      )}

      {/* Node Capacity Drawer */}
      {selectedCapacityNodeId && (
        <NodeCapacityDrawer
          nodeId={selectedCapacityNodeId}
          onClose={() => setSelectedCapacityNodeId(null)}
        />
      )}

      {/* Heartbeat Telemetry Simulator Drawer */}
      {simulatorNode && (
        <Drawer
          isOpen={true}
          onClose={() => setSimulatorNode(null)}
          title={
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-[#244DE8]" />
              <span>Simulate Node Heartbeat</span>
            </div>
          }
          description={`Submit telemetry payload to POST /api/v1/nodes/${truncateId(simulatorNode.id, 8)}/heartbeat`}
        >
          <form onSubmit={handleSimulatorSubmit} className="space-y-4">
            {simulatorError && (
              <div className="p-3 text-xs font-mono text-[#B42318] bg-[#FEF3F2] rounded-lg border border-[#FECDCA]">
                {simulatorError}
              </div>
            )}

            <div className="text-xs font-mono text-[#667085] pb-2 border-b border-[#EAEFF7]">
              Target Node: <strong className="text-[#101828]">{simulatorNode.hostname}</strong> ({simulatorNode.cpu_cores} cores, {formatMemoryMb(simulatorNode.memory_mb)})
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="CPU Usage (%)"
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={simCpu}
                onChange={(e) => setSimCpu(e.target.value)}
                required
                isMono
              />
              <Input
                label="Memory Usage (MB)"
                type="number"
                step="1"
                min="0"
                value={simMemMb}
                onChange={(e) => setSimMemMb(e.target.value)}
                required
                isMono
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Memory Usage (%)"
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={simMemPct}
                onChange={(e) => setSimMemPct(e.target.value)}
                required
                isMono
              />
              <Input
                label="Disk Storage (GB)"
                type="number"
                step="0.1"
                min="0"
                value={simDiskGb}
                onChange={(e) => setSimDiskGb(e.target.value)}
                required
                isMono
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Disk Storage (%)"
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={simDiskPct}
                onChange={(e) => setSimDiskPct(e.target.value)}
                required
                isMono
              />
              <Input
                label="Ping Latency (ms)"
                type="number"
                step="0.1"
                min="0"
                value={simLatency}
                onChange={(e) => setSimLatency(e.target.value)}
                required
                isMono
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Network TX (Mbps)"
                type="number"
                step="0.1"
                min="0"
                value={simTx}
                onChange={(e) => setSimTx(e.target.value)}
                required
                isMono
              />
              <Input
                label="Network RX (Mbps)"
                type="number"
                step="0.1"
                min="0"
                value={simRx}
                onChange={(e) => setSimRx(e.target.value)}
                required
                isMono
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Active Sockets"
                type="number"
                step="1"
                min="0"
                value={simConnections}
                onChange={(e) => setSimConnections(e.target.value)}
                required
                isMono
              />
              <Select
                label="Self-Reported Status"
                value={simStatus}
                onChange={(e) => setSimStatus(e.target.value as NodeStatus)}
              >
                <option value="READY">READY</option>
                <option value="BUSY">BUSY</option>
                <option value="DEGRADED">DEGRADED</option>
              </Select>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-[#EAEFF7]">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setSimulatorNode(null)}
                disabled={heartbeatMutation.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" isLoading={heartbeatMutation.isPending}>
                Transmit Heartbeat
              </Button>
            </div>
          </form>
        </Drawer>
      )}
    </div>
  )
}

function NodeCapacityDrawer({ nodeId, onClose }: { nodeId: string; onClose: () => void }) {
  const { data: cap, isLoading, error } = useQuery<NodeCapacitySummary>({
    queryKey: ['node-capacity', nodeId],
    queryFn: ({ signal }) => getNodeCapacity(nodeId, signal),
  })

  return (
    <Drawer
      isOpen={true}
      onClose={onClose}
      title="Allocatable Node Capacity"
      description={`Calculated capacity breakdown for Node ID: ${truncateId(nodeId, 10)}`}
    >
      {isLoading ? (
        <TableSkeleton rows={4} cols={2} />
      ) : error || !cap ? (
        <div className="p-3 text-xs font-mono text-[#B54708] bg-[#FFFAEB] rounded-lg border border-[#FEDF89]">
          Failed to load node capacity: {error instanceof Error ? error.message : 'Unknown'}
        </div>
      ) : (
        <div className="space-y-4 font-mono text-xs">
          <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#DCE2ED] space-y-1.5">
            <div className="flex justify-between">
              <span className="text-[#475467]">Hostname:</span>
              <span className="text-[#101828] font-bold">{cap.hostname}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#475467]">Status:</span>
              <StatusBadge status={cap.status} />
            </div>
            <div className="flex justify-between">
              <span className="text-[#475467]">Allocatable State:</span>
              <span className={cap.is_allocatable ? 'text-[#027A48] font-semibold' : 'text-[#B54708] font-semibold'}>
                {cap.is_allocatable ? 'ELIGIBLE FOR SCHEDULER' : 'BLOCKED FROM SCHEDULER'}
              </span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#DCE2ED] space-y-2">
            <div className="text-[10px] text-[#667085] uppercase tracking-wider font-semibold">
              CPU Cores Breakdown
            </div>
            <div className="flex justify-between">
              <span>Total Hardware:</span>
              <span>{cap.total_cpu_cores.toFixed(1)} Cores</span>
            </div>
            <div className="flex justify-between text-[#475467]">
              <span>Allocated:</span>
              <span>{cap.allocated_cpu_cores.toFixed(1)} Cores</span>
            </div>
            <div className="flex justify-between text-[#244DE8] font-bold border-t border-[#EAEFF7] pt-1">
              <span>Allocatable Headroom:</span>
              <span>{cap.allocatable_cpu_cores.toFixed(1)} Cores</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#DCE2ED] space-y-2">
            <div className="text-[10px] text-[#667085] uppercase tracking-wider font-semibold">
              Memory Breakdown
            </div>
            <div className="flex justify-between">
              <span>Total Hardware:</span>
              <span>{formatMemoryMb(cap.total_memory_mb)}</span>
            </div>
            <div className="flex justify-between text-[#475467]">
              <span>Allocated:</span>
              <span>{formatMemoryMb(cap.allocated_memory_mb)}</span>
            </div>
            <div className="flex justify-between text-[#027A48] font-bold border-t border-[#EAEFF7] pt-1">
              <span>Allocatable Headroom:</span>
              <span>{formatMemoryMb(cap.allocatable_memory_mb)}</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#DCE2ED] space-y-1.5">
            <div className="flex justify-between">
              <span className="text-[#475467]">Active Workload Tasks:</span>
              <span className="text-[#244DE8] font-bold">{cap.active_workload_count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#475467]">Health Evaluation Score:</span>
              <span className="text-[#101828] font-bold">{cap.health_score.toFixed(1)}/100</span>
            </div>
          </div>
        </div>
      )}
    </Drawer>
  )
}
