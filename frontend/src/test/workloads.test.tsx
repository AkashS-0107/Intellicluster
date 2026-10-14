import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from './test-utils'
import { WorkloadsPage } from '@/pages/WorkloadsPage'
import * as workloadApi from '@/api/workloads'
import * as clusterApi from '@/api/clusters'
import * as nodeApi from '@/api/nodes'
import { WorkloadResponse } from '@/types'

vi.mock('@/api/workloads')
vi.mock('@/api/clusters')
vi.mock('@/api/nodes')

describe('Workloads Page', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(clusterApi.listClusters).mockResolvedValue([])
    vi.mocked(nodeApi.listNodes).mockResolvedValue([])
  })

  const mockWorkloads: WorkloadResponse[] = [
    {
      id: 'workload-pending-01',
      name: 'critical-fintech-job',
      workload_type: 'REALTIME_API',
      cpu_cores_requested: 4.0,
      memory_mb_requested: 16384.0,
      storage_gb_requested: 20.0,
      network_mbps_requested: 100.0,
      max_latency_tolerance_ms: 10.0,
      priority: 'CRITICAL',
      status: 'PENDING',
      retry_count: 0,
      max_retries: 3,
      created_at: '2026-10-09T09:00:00Z',
      updated_at: '2026-10-09T09:00:00Z',
    },
  ]

  it('renders workload queue and communicates heuristic scheduler policy', async () => {
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue(mockWorkloads)

    renderWithProviders(<WorkloadsPage />)

    await waitFor(() => {
      expect(screen.getByText('critical-fintech-job')).toBeInTheDocument()
      expect(screen.getAllByText('PENDING').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('CRITICAL').length).toBeGreaterThanOrEqual(1)
    })

    // Confirm prompt requirement: Explicitly labeled as Heuristic Placement Engine, not DQN
    expect(screen.getByText(/Active Scheduler: Heuristic Placement Engine/i)).toBeInTheDocument()
    expect(
      screen.getByText(/Offline-trained DQN load balancing models are not connected to the active API/i)
    ).toBeInTheDocument()
  })

  it('executes scheduling action and renders error banner if no eligible node is available', async () => {
    const user = userEvent.setup()
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue(mockWorkloads)
    vi.mocked(workloadApi.scheduleWorkload).mockRejectedValue(
      new Error('No available compute nodes in cluster satisfy the 10.0ms latency SLA.')
    )

  renderWithProviders(<WorkloadsPage />)

    await waitFor(() => {
      expect(screen.getByText('critical-fintech-job')).toBeInTheDocument()
    })

    const scheduleBtn = screen.getByRole('button', { name: /schedule/i })
    await user.click(scheduleBtn)

    await waitFor(() => {
      expect(screen.getByText(/Heuristic Placement Failed/i)).toBeInTheDocument()
      expect(
        screen.getByText(/No available compute nodes in cluster satisfy the 10.0ms latency SLA/i)
      ).toBeInTheDocument()
    })
  })

  it('renders retry button on FAILED workload and triggers state transition', async () => {
    const user = userEvent.setup()
    const failedWorkload: WorkloadResponse = {
      ...mockWorkloads[0],
      id: 'workload-failed-01',
      status: 'FAILED',
      failure_reason: 'Task timeout after 300s',
      retry_count: 1,
      max_retries: 3,
    }
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue([failedWorkload])
    vi.mocked(workloadApi.transitionWorkloadStatus).mockResolvedValue({
      ...failedWorkload,
      status: 'PENDING',
      retry_count: 2,
    })

    renderWithProviders(<WorkloadsPage />)

    await waitFor(() => {
      expect(screen.getByText('critical-fintech-job')).toBeInTheDocument()
      expect(screen.getByText(/Err: Task timeout after 300s/i)).toBeInTheDocument()
    })

    const retryBtn = screen.getByRole('button', { name: /retry/i })
    expect(retryBtn).toBeInTheDocument()
    await user.click(retryBtn)

    await waitFor(() => {
      expect(workloadApi.transitionWorkloadStatus).toHaveBeenCalledWith(
        'workload-failed-01',
        { target_status: 'PENDING', failure_reason: undefined }
      )
    })
  })

  it('renders max retries badge when workload reaches maximum retry limit', async () => {
    const exhaustedWorkload: WorkloadResponse = {
      ...mockWorkloads[0],
      id: 'workload-exhausted-01',
      status: 'FAILED',
      failure_reason: 'Persistent OOM',
      retry_count: 3,
      max_retries: 3,
    }
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue([exhaustedWorkload])

    renderWithProviders(<WorkloadsPage />)

    await waitFor(() => {
      expect(screen.getByText('critical-fintech-job')).toBeInTheDocument()
      expect(screen.getByText('Max Retries')).toBeInTheDocument()
    })

    expect(screen.queryByRole('button', { name: /^retry$/i })).not.toBeInTheDocument()
  })
})
