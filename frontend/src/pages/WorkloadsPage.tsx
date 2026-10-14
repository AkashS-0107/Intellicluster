import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listWorkloads,
  createWorkload,
  scheduleWorkload,
  transitionWorkloadStatus,
  cancelWorkload,
} from '@/api/workloads'
import { listClusters } from '@/api/clusters'
import { listNodes } from '@/api/nodes'
import {
  WorkloadCreate,
  WorkloadPriority,
  WorkloadResponse,
  WorkloadStatus,
  WorkloadType,
} from '@/types'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { TableSkeleton } from '@/components/ui/LoadingSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { Button } from '@/components/ui/Button'
import { StatusBadge, PriorityBadge, WorkloadTypeBadge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Input, Select } from '@/components/ui/FormControls'
import {
  formatDateTime,
  formatMemoryMb,
  formatLatency,
  truncateId,
} from '@/utils/format'
import {
  Plus,
  Play,
  RotateCw,
  XCircle,
  Cpu,
  Info,
} from 'lucide-react'

export function WorkloadsPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<string>('ALL')
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL')

  // Submission Modal state
  const [isSubmitOpen, setIsSubmitOpen] = useState(false)
  const [name, setName] = useState('')
  const [clusterId, setClusterId] = useState('')
  const [workloadType, setWorkloadType] = useState<WorkloadType>('BATCH')
  const [cpuCores, setCpuCores] = useState('2.0')
  const [memoryMb, setMemoryMb] = useState('4096')
  const [storageGb, setStorageGb] = useState('10')
  const [networkMbps, setNetworkMbps] = useState('50')
  const [latencyTolerance, setLatencyTolerance] = useState('100')
  const [durationSec, setDurationSec] = useState('300')
  const [priority, setPriority] = useState<WorkloadPriority>('NORMAL')
  const [maxRetries, setMaxRetries] = useState('3')
  const [submitError, setSubmitError] = useState<string | null>(null)

  // Scheduling state
  const [schedulingId, setSchedulingId] = useState<string | null>(null)
  const [schedulingError, setSchedulingError] = useState<{ id: string; message: string } | null>(null)

  // Transition Modal state
  const [transitionTarget, setTransitionTarget] = useState<WorkloadResponse | null>(null)
  const [targetStatus, setTargetStatus] = useState<WorkloadStatus>('RUNNING')
  const [failureReason, setFailureReason] = useState('')
  const [transitionError, setTransitionError] = useState<string | null>(null)

  // Cancel Confirmation state
  const [cancelTarget, setCancelTarget] = useState<WorkloadResponse | null>(null)

  // Queries
  const { data: clusters = [] } = useQuery({
    queryKey: ['clusters'],
    queryFn: ({ signal }) => listClusters({ limit: 100 }, signal),
  })

  const { data: nodes = [] } = useQuery({
    queryKey: ['nodes'],
    queryFn: ({ signal }) => listNodes({ limit: 200 }, signal),
  })

  const {
    data: workloads = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['workloads', statusFilter, priorityFilter],
    queryFn: ({ signal }) =>
      listWorkloads(
        {
          status: statusFilter === 'ALL' ? undefined : (statusFilter as WorkloadStatus),
          priority: priorityFilter === 'ALL' ? undefined : (priorityFilter as WorkloadPriority),
          limit: 200,
        },
        signal
      ),
  })

  // Submit Mutation
  const createMutation = useMutation({
    mutationFn: (payload: WorkloadCreate) => createWorkload(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workloads'] })
      setIsSubmitOpen(false)
      setName('')
      setClusterId('')
      setSubmitError(null)
    },
    onError: (err: any) => {
      setSubmitError(err.message || 'Failed to submit workload')
    },
  })

  // Schedule Mutation
  const scheduleMutation = useMutation({
    mutationFn: (id: string) => scheduleWorkload(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workloads'] })
      queryClient.invalidateQueries({ queryKey: ['nodes'] })
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      queryClient.invalidateQueries({ queryKey: ['cluster-capacity'] })
      queryClient.invalidateQueries({ queryKey: ['node-capacity'] })
      setSchedulingId(null)
      setSchedulingError(null)
    },
    onError: (err: any, id: string) => {
      setSchedulingId(null)
      setSchedulingError({ id, message: err.message || 'Heuristic placement scheduling failed' })
    },
  })

  // Status Transition Mutation
  const transitionMutation = useMutation({
    mutationFn: ({ id, status, reason }: { id: string; status: WorkloadStatus; reason?: string }) =>
      transitionWorkloadStatus(id, { target_status: status, failure_reason: reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workloads'] })
      queryClient.invalidateQueries({ queryKey: ['nodes'] })
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      queryClient.invalidateQueries({ queryKey: ['cluster-capacity'] })
      queryClient.invalidateQueries({ queryKey: ['node-capacity'] })
      setTransitionTarget(null)
      setTransitionError(null)
    },
    onError: (err: any) => {
      setTransitionError(err.message || 'Failed to transition workload state')
    },
  })

  // Cancel Mutation
  const cancelMutation = useMutation({
    mutationFn: (id: string) => cancelWorkload(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workloads'] })
      queryClient.invalidateQueries({ queryKey: ['nodes'] })
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      queryClient.invalidateQueries({ queryKey: ['cluster-capacity'] })
      queryClient.invalidateQueries({ queryKey: ['node-capacity'] })
      setCancelTarget(null)
    },
    onError: (err: any) => {
      alert(`Cancellation failed: ${err.message}`)
      setCancelTarget(null)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setSubmitError('Workload name is required')
      return
    }
    const cpu = parseFloat(cpuCores)
    const mem = parseFloat(memoryMb)
    if (isNaN(cpu) || cpu <= 0 || isNaN(mem) || mem <= 0) {
      setSubmitError('CPU and RAM requests must be valid positive values')
      return
    }

    setSubmitError(null)
    createMutation.mutate({
      name: name.trim(),
      cluster_id: clusterId || undefined,
      workload_type: workloadType,
      cpu_cores_requested: cpu,
      memory_mb_requested: mem,
      storage_gb_requested: parseFloat(storageGb) || 10,
      network_mbps_requested: parseFloat(networkMbps) || 10,
      max_latency_tolerance_ms: latencyTolerance ? parseFloat(latencyTolerance) : undefined,
      estimated_duration_sec: durationSec ? parseFloat(durationSec) : undefined,
      priority,
      max_retries: parseInt(maxRetries, 10) || 3,
    })
  }

  const handleOpenTransition = (workload: WorkloadResponse) => {
    setTransitionTarget(workload)
    setFailureReason('')
    setTransitionError(null)
    // Suggest next sensible transition
    if (workload.status === 'SCHEDULED') setTargetStatus('RUNNING')
    else if (workload.status === 'RUNNING') setTargetStatus('COMPLETED')
    else setTargetStatus('FAILED')
  }

  return (
    <div className="space-y-6">
      {/* Informative Strategy Notice */}
      <div className="rounded-xl border border-[#C7D7FE] bg-[#E8EEFF]/40 p-4 text-xs text-[#101828] flex items-start gap-3 shadow-2xs">
        <Info className="w-4 h-4 text-[#244DE8] shrink-0 mt-0.5" />
        <div>
          <strong className="text-[#244DE8] font-bold">Active Scheduler: Heuristic Placement Engine</strong>
          <p className="mt-0.5 text-[#475467] leading-relaxed">
            Workload placement requests are processed by the backend <code className="font-mono text-[#244DE8] font-semibold">HeuristicSchedulerStrategy</code>. Candidate nodes are filtered by allocatable headroom and network latency SLAs, and ranked by a multi-factor fitness score. <em>Offline-trained DQN load balancing models are not connected to the active API.</em>
          </p>
        </div>
      </div>

      {/* Action and Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#667085]">STATUS:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-8 rounded-lg border border-[#DCE2ED] bg-white px-2.5 text-xs text-[#101828] font-mono focus-visible:outline-none focus-visible:border-[#244DE8] shadow-2xs"
            >
              <option value="ALL">ALL STATUSES</option>
              <option value="PENDING">PENDING</option>
              <option value="SCHEDULED">SCHEDULED</option>
              <option value="RUNNING">RUNNING</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="FAILED">FAILED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#667085]">PRIORITY:</span>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="h-8 rounded-lg border border-[#DCE2ED] bg-white px-2.5 text-xs text-[#101828] font-mono focus-visible:outline-none focus-visible:border-[#244DE8] shadow-2xs"
            >
              <option value="ALL">ALL PRIORITIES</option>
              <option value="LOW">LOW</option>
              <option value="NORMAL">NORMAL</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={() => {
            setSubmitError(null)
            setIsSubmitOpen(true)
          }}
          icon={<Plus className="w-3.5 h-3.5" />}
        >
          Submit Workload
        </Button>
      </div>

      {/* Scheduling Error Banner if placement failed */}
      {schedulingError && (
        <ErrorState
          title="Heuristic Placement Failed"
          message={schedulingError.message}
          onRetry={() => {
            const id = schedulingError.id
            setSchedulingError(null)
            scheduleMutation.mutate(id)
          }}
        />
      )}

      {error && (
        <ErrorState
          title="Workload Query Failed"
          message={error instanceof Error ? error.message : 'Failed to query workloads'}
          onRetry={() => refetch()}
        />
      )}

      {/* Workload Queue Table */}
      {isLoading ? (
        <TableSkeleton rows={6} cols={8} />
      ) : workloads.length === 0 ? (
        <EmptyState
          title="No Workloads in Queue"
          description={
            statusFilter !== 'ALL' || priorityFilter !== 'ALL'
              ? 'No workloads match the filter criteria.'
              : 'There are currently no tasks or compute workloads registered in the queue.'
          }
          icon={<Cpu className="w-6 h-6 stroke-[1.5]" />}
          action={{
            label: 'Submit Workload',
            onClick: () => setIsSubmitOpen(true),
            icon: <Plus className="w-4 h-4" />,
          }}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Workload Task</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Demands (CPU / RAM)</TableHead>
              <TableHead>Assigned Node</TableHead>
              <TableHead>Retries</TableHead>
              <TableHead>Created / Scheduled</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {workloads.map((w) => {
              const assignedNode = nodes.find((n) => n.id === w.assigned_node_id)
              const isPending = w.status === 'PENDING'
              const canCancel = ['PENDING', 'SCHEDULED', 'RUNNING'].includes(w.status)
              const canTransition = ['SCHEDULED', 'RUNNING'].includes(w.status)
              const isCurrentScheduling = schedulingId === w.id

              return (
                <TableRow key={w.id}>
                  <TableCell>
                    <div className="font-semibold text-[#101828] font-sans">{w.name}</div>
                    <div className="text-[10px] text-[#667085]" title={w.id}>
                      {truncateId(w.id, 8)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <WorkloadTypeBadge type={w.workload_type} />
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={w.status} />
                    {w.failure_reason && (
                      <div className="text-[10px] text-[#B42318] mt-0.5 truncate max-w-xs font-mono" title={w.failure_reason}>
                        Err: {w.failure_reason}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <PriorityBadge priority={w.priority} />
                  </TableCell>
                  <TableCell>
                    <div className="font-medium text-[#101828]">{w.cpu_cores_requested.toFixed(1)} Cores</div>
                    <div className="text-[#667085] text-[11px]">
                      {formatMemoryMb(w.memory_mb_requested)}
                      {w.max_latency_tolerance_ms && ` • <${formatLatency(w.max_latency_tolerance_ms)}`}
                    </div>
                  </TableCell>
                  <TableCell className="font-sans">
                    {assignedNode ? (
                      <span className="text-[#101828] font-medium">{assignedNode.hostname}</span>
                    ) : w.assigned_node_id ? (
                      <span className="text-[#667085] font-mono">{truncateId(w.assigned_node_id, 8)}</span>
                    ) : (
                      <span className="text-[#98A2B3]">Unscheduled</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className={w.retry_count > 0 ? 'text-[#B54708] font-bold' : 'text-[#667085]'}>
                      {w.retry_count} / {w.max_retries}
                    </span>
                  </TableCell>
                  <TableCell className="text-[11px] text-[#667085]">
                    <div>{formatDateTime(w.created_at)}</div>
                    {w.scheduled_at && (
                      <div className="text-[#244DE8] text-[10px] font-semibold">
                        Sched: {formatDateTime(w.scheduled_at)}
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {/* Schedule Button for PENDING */}
                      {isPending && (
                        <Button
                          size="xs"
                          variant="primary"
                          onClick={() => {
                            setSchedulingId(w.id)
                            setSchedulingError(null)
                            scheduleMutation.mutate(w.id)
                          }}
                          isLoading={isCurrentScheduling}
                          icon={<Play className="w-3 h-3" />}
                          title="Run Heuristic Placement"
                        >
                          Schedule
                        </Button>
                      )}

                      {/* State Transition Button */}
                      {canTransition && (
                        <Button
                          size="xs"
                          variant="secondary"
                          onClick={() => handleOpenTransition(w)}
                          icon={<RotateCw className="w-3 h-3 text-[#244DE8]" />}
                          title="Transition lifecycle state"
                        >
                          State
                        </Button>
                      )}

                      {/* Retry Action for FAILED workloads */}
                      {w.status === 'FAILED' && w.retry_count < w.max_retries && (
                        <Button
                          size="xs"
                          variant="secondary"
                          onClick={() =>
                            transitionMutation.mutate({
                              id: w.id,
                              status: 'PENDING',
                            })
                          }
                          isLoading={transitionMutation.isPending}
                          icon={<RotateCw className="w-3 h-3 text-[#244DE8]" />}
                          title={`Retry failed workload (${w.retry_count}/${w.max_retries} attempts used)`}
                        >
                          Retry
                        </Button>
                      )}

                      {w.status === 'FAILED' && w.retry_count >= w.max_retries && (
                        <span className="text-[10px] text-[#B42318] font-mono px-1.5 py-0.5 bg-[#FEF3F2] rounded border border-[#FECDCA]">
                          Max Retries
                        </span>
                      )}

                      {/* Cancel Action */}
                      {canCancel && (
                        <Button
                          size="xs"
                          variant="ghost"
                          onClick={() => setCancelTarget(w)}
                          icon={<XCircle className="w-3 h-3 text-[#B42318]" />}
                          title="Cancel workload"
                        >
                          Cancel
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      )}

      {/* Workload Submission Modal */}
      <Modal
        isOpen={isSubmitOpen}
        onClose={() => setIsSubmitOpen(false)}
        title="Submit New Compute Workload"
        description="Register a task in the PENDING queue with resource constraints and latency SLAs."
        maxWidth="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {submitError && (
            <div className="p-3 text-xs font-mono text-[#B42318] bg-[#FEF3F2] rounded-lg border border-[#FECDCA]">
              {submitError}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input
              label="Workload Identifier Name"
              placeholder="e.g. data-aggregation-batch-01"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              isMono
            />

            <Select
              label="Target Cluster"
              value={clusterId}
              onChange={(e) => setClusterId(e.target.value)}
            >
              <option value="">Any Cluster</option>
              {clusters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.status})
                </option>
              ))}
            </Select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Select
              label="Workload Category Profile"
              value={workloadType}
              onChange={(e) => setWorkloadType(e.target.value as WorkloadType)}
            >
              <option value="BATCH">BATCH</option>
              <option value="REALTIME_API">REALTIME_API</option>
              <option value="ML_TRAINING">ML_TRAINING</option>
              <option value="BACKGROUND_JOB">BACKGROUND_JOB</option>
              <option value="DATA_PROCESSING">DATA_PROCESSING</option>
            </Select>

            <Select
              label="Scheduling Priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value as WorkloadPriority)}
            >
              <option value="LOW">LOW</option>
              <option value="NORMAL">NORMAL</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </Select>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Input
              label="CPU Cores"
              type="number"
              step="0.5"
              min="0.1"
              value={cpuCores}
              onChange={(e) => setCpuCores(e.target.value)}
              required
              isMono
            />
            <Input
              label="RAM (MB)"
              type="number"
              step="1"
              min="64"
              value={memoryMb}
              onChange={(e) => setMemoryMb(e.target.value)}
              required
              isMono
            />
            <Input
              label="Disk (GB)"
              type="number"
              step="1"
              min="0"
              value={storageGb}
              onChange={(e) => setStorageGb(e.target.value)}
              isMono
            />
            <Input
              label="Network (Mbps)"
              type="number"
              step="1"
              min="0"
              value={networkMbps}
              onChange={(e) => setNetworkMbps(e.target.value)}
              isMono
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Input
              label="Latency SLA (Max ms)"
              type="number"
              step="1"
              min="1"
              placeholder="e.g. 50"
              value={latencyTolerance}
              onChange={(e) => setLatencyTolerance(e.target.value)}
              isMono
            />
            <Input
              label="Duration Est (sec)"
              type="number"
              step="1"
              min="1"
              placeholder="e.g. 300"
              value={durationSec}
              onChange={(e) => setDurationSec(e.target.value)}
              isMono
            />
            <Input
              label="Max Retries"
              type="number"
              step="1"
              min="0"
              max="10"
              value={maxRetries}
              onChange={(e) => setMaxRetries(e.target.value)}
              isMono
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-[#EAEFF7]">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsSubmitOpen(false)}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createMutation.isPending}>
              Submit to Queue
            </Button>
          </div>
        </form>
      </Modal>

      {/* Workload Transition Modal */}
      {transitionTarget && (
        <Modal
          isOpen={true}
          onClose={() => setTransitionTarget(null)}
          title={`Transition Status: ${transitionTarget.name}`}
          description={`Current Status: ${transitionTarget.status}`}
        >
          <div className="space-y-4">
            {transitionError && (
              <div className="p-3 text-xs font-mono text-[#B42318] bg-[#FEF3F2] rounded-lg border border-[#FECDCA]">
                {transitionError}
              </div>
            )}

            <Select
              label="Target Lifecycle Status"
              value={targetStatus}
              onChange={(e) => setTargetStatus(e.target.value as WorkloadStatus)}
            >
              {transitionTarget.status === 'SCHEDULED' && (
                <>
                  <option value="RUNNING">RUNNING (Execution Commenced)</option>
                  <option value="FAILED">FAILED (Placement / Launch Crash)</option>
                  <option value="CANCELLED">CANCELLED (Administrative Abort)</option>
                </>
              )}
              {transitionTarget.status === 'RUNNING' && (
                <>
                  <option value="COMPLETED">COMPLETED (Successful Finish)</option>
                  <option value="FAILED">FAILED (Execution Error / Crash)</option>
                  <option value="CANCELLED">CANCELLED (Administrative Abort)</option>
                </>
              )}
            </Select>

            {targetStatus === 'FAILED' && (
              <Input
                label="Failure Reason (Optional)"
                placeholder="e.g. OOM killed, task timeout, network exception"
                value={failureReason}
                onChange={(e) => setFailureReason(e.target.value)}
              />
            )}

            <div className="flex justify-end gap-2 pt-3 border-t border-[#EAEFF7]">
              <Button
                variant="ghost"
                onClick={() => setTransitionTarget(null)}
                disabled={transitionMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() =>
                  transitionMutation.mutate({
                    id: transitionTarget.id,
                    status: targetStatus,
                    reason: failureReason,
                  })
                }
                isLoading={transitionMutation.isPending}
              >
                Confirm Transition
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Cancel Confirmation Dialog */}
      {cancelTarget && (
        <ConfirmDialog
          isOpen={true}
          onClose={() => setCancelTarget(null)}
          onConfirm={() => cancelMutation.mutate(cancelTarget.id)}
          title={`Cancel Workload ${cancelTarget.name}?`}
          message={`This will move the workload from ${cancelTarget.status} to CANCELLED. Any assigned compute resources will be reclaimed.`}
          confirmLabel="Cancel Workload"
          variant="danger"
          isLoading={cancelMutation.isPending}
        />
      )}
    </div>
  )
}
