import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listClusters,
  createCluster,
  updateCluster,
  getClusterCapacity,
} from '@/api/clusters'
import {
  ClusterCreate,
  ClusterResponse,
  ClusterStatus,
  ClusterUpdate,
  ClusterCapacitySummary,
} from '@/types'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { TableSkeleton } from '@/components/ui/LoadingSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { Button } from '@/components/ui/Button'
import { StatusBadge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { Input, Select, Textarea } from '@/components/ui/FormControls'
import { formatDateTime, formatMemoryMb, formatPct, truncateId } from '@/utils/format'
import { Plus, Edit2, Layers, Cpu, ChevronDown, ChevronRight } from 'lucide-react'

export function ClustersPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<string>('ALL')
  const [expandedClusterId, setExpandedClusterId] = useState<string | null>(null)

  // Creation modal state
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createDescription, setCreateDescription] = useState('')
  const [createStatus, setCreateStatus] = useState<ClusterStatus>('ACTIVE')
  const [createError, setCreateError] = useState<string | null>(null)

  // Edit modal state
  const [editingCluster, setEditingCluster] = useState<ClusterResponse | null>(null)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editStatus, setEditStatus] = useState<ClusterStatus>('ACTIVE')
  const [editError, setEditError] = useState<string | null>(null)

  // Query clusters
  const {
    data: clusters = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['clusters', statusFilter],
    queryFn: ({ signal }) =>
      listClusters(
        {
          status: statusFilter === 'ALL' ? undefined : (statusFilter as ClusterStatus),
          limit: 100,
        },
        signal
      ),
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (payload: ClusterCreate) => createCluster(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      setIsCreateOpen(false)
      setCreateName('')
      setCreateDescription('')
      setCreateStatus('ACTIVE')
      setCreateError(null)
    },
    onError: (err: any) => {
      setCreateError(err.message || 'Failed to create cluster')
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ClusterUpdate }) => updateCluster(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      setEditingCluster(null)
      setEditError(null)
    },
    onError: (err: any) => {
      setEditError(err.message || 'Failed to update cluster')
    },
  })

  const handleOpenEdit = (cluster: ClusterResponse) => {
    setEditingCluster(cluster)
    setEditName(cluster.name)
    setEditDescription(cluster.description || '')
    setEditStatus(cluster.status)
    setEditError(null)
  }

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!createName.trim()) {
      setCreateError('Cluster name is required')
      return
    }
    setCreateError(null)
    createMutation.mutate({
      name: createName.trim(),
      description: createDescription.trim() || undefined,
      status: createStatus,
    })
  }

  const handleUpdateSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingCluster) return
    if (!editName.trim()) {
      setEditError('Cluster name is required')
      return
    }
    setEditError(null)
    updateMutation.mutate({
      id: editingCluster.id,
      data: {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
        status: editStatus,
      },
    })
  }

  return (
    <div className="space-y-6">
      {/* Action and Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#667085]">STATUS:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-8 rounded-lg border border-[#DCE2ED] bg-white px-2.5 text-xs text-[#101828] font-mono focus-visible:outline-none focus-visible:border-[#244DE8] shadow-2xs"
            >
              <option value="ALL">ALL STATUSES</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="DEGRADED">DEGRADED</option>
              <option value="MAINTENANCE">MAINTENANCE</option>
              <option value="OFFLINE">OFFLINE</option>
            </select>
          </div>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={() => {
            setCreateError(null)
            setIsCreateOpen(true)
          }}
          icon={<Plus className="w-3.5 h-3.5" />}
        >
          Create Cluster
        </Button>
      </div>

      {/* Error State */}
      {error && (
        <ErrorState
          title="Cluster Query Failed"
          message={error instanceof Error ? error.message : 'Failed to query clusters from API'}
          onRetry={() => refetch()}
        />
      )}

      {/* Cluster Inventory Table */}
      {isLoading ? (
        <TableSkeleton rows={5} cols={6} />
      ) : clusters.length === 0 ? (
        <EmptyState
          title="No Clusters Found"
          description={
            statusFilter !== 'ALL'
              ? `No clusters match the filter "${statusFilter}".`
              : 'There are currently no server clusters registered in the system.'
          }
          icon={<Layers className="w-6 h-6 stroke-[1.5]" />}
          action={{
            label: 'Create Cluster',
            onClick: () => setIsCreateOpen(true),
            icon: <Plus className="w-4 h-4" />,
          }}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8"></TableHead>
              <TableHead>Cluster Name</TableHead>
              <TableHead>Cluster ID</TableHead>
              <TableHead>Operational Status</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Created At</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {clusters.map((cluster) => {
              const isExpanded = expandedClusterId === cluster.id
              return (
                <React.Fragment key={cluster.id}>
                  <TableRow>
                    <TableCell className="w-8 pr-0">
                      <button
                        onClick={() => setExpandedClusterId(isExpanded ? null : cluster.id)}
                        className="p-1 rounded-md text-[#667085] hover:text-[#101828] hover:bg-[#F1F5F9] transition-colors"
                        title={isExpanded ? 'Collapse capacity' : 'Inspect capacity'}
                        aria-label={isExpanded ? 'Collapse capacity' : 'Inspect capacity'}
                      >
                        {isExpanded ? (
                          <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </TableCell>
                    <TableCell className="font-semibold text-[#101828] font-sans">
                      {cluster.name}
                    </TableCell>
                    <TableCell className="text-[#667085] text-[11px]" title={cluster.id}>
                      {truncateId(cluster.id, 10)}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={cluster.status} />
                    </TableCell>
                    <TableCell className="text-[#475467] font-sans max-w-xs truncate">
                      {cluster.description || '—'}
                    </TableCell>
                    <TableCell className="text-[#667085] text-[11px]">
                      {formatDateTime(cluster.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="xs"
                        variant="secondary"
                        onClick={() => handleOpenEdit(cluster)}
                        icon={<Edit2 className="w-3 h-3" />}
                      >
                        Edit
                      </Button>
                    </TableCell>
                  </TableRow>

                  {/* Expandable Cluster Capacity Row */}
                  {isExpanded && (
                    <TableRow className="bg-[#F8FAFC]/70 hover:bg-[#F8FAFC]/70">
                      <TableCell colSpan={7} className="p-4">
                        <ClusterCapacityView clusterId={cluster.id} clusterName={cluster.name} />
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              )
            })}
          </TableBody>
        </Table>
      )}

      {/* Create Cluster Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New Server Cluster"
        description="Register a new logical cluster for compute node grouping and workload scheduling."
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          {createError && (
            <div className="p-3 text-xs font-mono text-[#B42318] bg-[#FEF3F2] rounded-lg border border-[#FECDCA]">
              {createError}
            </div>
          )}

          <Input
            label="Cluster Identifier Name"
            placeholder="e.g. us-east-inference-cluster"
            value={createName}
            onChange={(e) => setCreateName(e.target.value)}
            required
            maxLength={100}
            isMono
          />

          <Textarea
            label="Description (Optional)"
            placeholder="Purpose and deployment tier for this cluster..."
            value={createDescription}
            onChange={(e) => setCreateDescription(e.target.value)}
            maxLength={500}
          />

          <Select
            label="Initial Operational Status"
            value={createStatus}
            onChange={(e) => setCreateStatus(e.target.value as ClusterStatus)}
          >
            <option value="ACTIVE">ACTIVE</option>
            <option value="DEGRADED">DEGRADED</option>
            <option value="MAINTENANCE">MAINTENANCE</option>
            <option value="OFFLINE">OFFLINE</option>
          </Select>

          <div className="flex justify-end gap-2 pt-3 border-t border-[#EAEFF7]">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsCreateOpen(false)}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createMutation.isPending}>
              Create Cluster
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Cluster Modal */}
      <Modal
        isOpen={!!editingCluster}
        onClose={() => setEditingCluster(null)}
        title={`Update Cluster: ${editingCluster?.name || ''}`}
        description="Modify cluster metadata and administrative status."
      >
        <form onSubmit={handleUpdateSubmit} className="space-y-4">
          {editError && (
            <div className="p-3 text-xs font-mono text-[#B42318] bg-[#FEF3F2] rounded-lg border border-[#FECDCA]">
              {editError}
            </div>
          )}

          <Input
            label="Cluster Identifier Name"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            required
            maxLength={100}
            isMono
          />

          <Textarea
            label="Description"
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            maxLength={500}
          />

          <Select
            label="Operational Status"
            value={editStatus}
            onChange={(e) => setEditStatus(e.target.value as ClusterStatus)}
          >
            <option value="ACTIVE">ACTIVE</option>
            <option value="DEGRADED">DEGRADED</option>
            <option value="MAINTENANCE">MAINTENANCE</option>
            <option value="OFFLINE">OFFLINE</option>
          </Select>

          <div className="flex justify-end gap-2 pt-3 border-t border-[#EAEFF7]">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setEditingCluster(null)}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={updateMutation.isPending}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

function ClusterCapacityView({ clusterId, clusterName }: { clusterId: string; clusterName: string }) {
  const {
    data: capacity,
    isLoading,
    error,
  } = useQuery<ClusterCapacitySummary>({
    queryKey: ['cluster-capacity', clusterId],
    queryFn: ({ signal }) => getClusterCapacity(clusterId, signal),
  })

  if (isLoading) {
    return <TableSkeleton rows={2} cols={4} />
  }

  if (error || !capacity) {
    return (
      <div className="text-xs font-mono text-[#B54708] bg-[#FFFAEB] p-3 rounded-lg border border-[#FEDF89]">
        Failed to load cluster capacity details: {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-[#DCE2ED] bg-white p-4 space-y-4 shadow-2xs">
      <div className="flex items-center justify-between border-b border-[#EAEFF7] pb-2">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-[#244DE8] font-mono flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5" />
          Hardware Capacity Summary: {clusterName}
        </h4>
        <span className="text-[11px] font-mono text-[#667085]">
          Nodes: {capacity.ready_nodes} ready / {capacity.total_nodes} total
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
        <div className="p-2.5 rounded-lg bg-[#F8FAFC] border border-[#EAEFF7]">
          <div className="text-[10px] text-[#667085]">CPU ALLOCATION</div>
          <div className="mt-1 font-semibold text-[#101828]">
            {capacity.allocated_cpu_cores.toFixed(1)} / {capacity.total_cpu_cores.toFixed(1)} Cores
          </div>
          <div className="text-[10px] text-[#244DE8] mt-0.5 font-bold">
            {capacity.allocatable_cpu_cores.toFixed(1)} allocatable
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-[#F8FAFC] border border-[#EAEFF7]">
          <div className="text-[10px] text-[#667085]">RAM ALLOCATION</div>
          <div className="mt-1 font-semibold text-[#101828]">
            {formatMemoryMb(capacity.allocated_memory_mb)} / {formatMemoryMb(capacity.total_memory_mb)}
          </div>
          <div className="text-[10px] text-[#027A48] mt-0.5 font-bold">
            {formatMemoryMb(capacity.allocatable_memory_mb)} allocatable
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-[#F8FAFC] border border-[#EAEFF7]">
          <div className="text-[10px] text-[#667085]">AVERAGE UTILIZATION</div>
          <div className="mt-1 font-semibold text-[#101828]">
            CPU: {formatPct(capacity.average_cpu_usage_pct)}
          </div>
          <div className="text-[10px] text-[#667085] mt-0.5">
            RAM: {formatPct(capacity.average_memory_usage_pct)}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-[#F8FAFC] border border-[#EAEFF7]">
          <div className="text-[10px] text-[#667085]">ACTIVE WORKLOADS</div>
          <div className="mt-1 font-semibold text-[#244DE8] text-base">
            {capacity.active_workload_count}
          </div>
          <div className="text-[10px] text-[#667085] mt-0.5">Assigned to nodes</div>
        </div>
      </div>
    </div>
  )
}
