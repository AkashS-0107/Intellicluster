import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from './test-utils'
import { NodesPage } from '@/pages/NodesPage'
import * as nodeApi from '@/api/nodes'
import * as clusterApi from '@/api/clusters'
import { NodeResponse } from '@/types'

vi.mock('@/api/nodes')
vi.mock('@/api/clusters')

describe('Nodes Page', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(clusterApi.listClusters).mockResolvedValue([])
  })

  const mockNodes: NodeResponse[] = [
    {
      id: 'node-uuid-01',
      hostname: 'compute-alpha.infra',
      ip_address: '10.0.0.12',
      status: 'READY',
      cpu_cores: 32,
      memory_mb: 131072,
      storage_gb: 2000,
      network_bandwidth_mbps: 10000,
      current_cpu_usage_pct: 22.4,
      current_memory_usage_mb: 45000,
      current_disk_usage_gb: 500,
      current_network_tx_mbps: 15,
      current_network_rx_mbps: 45,
      current_network_latency_ms: 1.8,
      active_connections: 120,
      health_score: 98.2,
      risk_score: 0.15,
      active_workload_count: 2,
      last_heartbeat: '2026-10-09T10:00:00Z',
      is_cordoned: false,
      created_at: '2026-10-09T08:00:00Z',
      updated_at: '2026-10-09T08:00:00Z',
    },
    {
      id: 'node-uuid-02',
      hostname: 'compute-beta.infra',
      ip_address: '10.0.0.13',
      status: 'READY',
      cpu_cores: 16,
      memory_mb: 65536,
      storage_gb: 1000,
      network_bandwidth_mbps: 10000,
      current_cpu_usage_pct: 12.0,
      current_memory_usage_mb: 12000,
      current_disk_usage_gb: 200,
      current_network_tx_mbps: 5,
      current_network_rx_mbps: 10,
      current_network_latency_ms: 2.1,
      active_connections: 30,
      health_score: 95.0,
      risk_score: 0.05,
      active_workload_count: 0,
      last_heartbeat: '2026-10-09T10:00:00Z',
      is_cordoned: true,
      created_at: '2026-10-09T08:00:00Z',
      updated_at: '2026-10-09T08:00:00Z',
    },
  ]

  it('renders node inventory with explicit "ML adapter not connected" badge', async () => {
    vi.mocked(nodeApi.listNodes).mockResolvedValue(mockNodes)

    renderWithProviders(<NodesPage />)

    await waitFor(() => {
      expect(screen.getByText('compute-alpha.infra')).toBeInTheDocument()
      expect(screen.getByText('compute-beta.infra')).toBeInTheDocument()
    })

    // Confirm prompt requirement: "ML adapter not connected" indicator
    const badges = screen.getAllByText('ML adapter not connected')
    expect(badges.length).toBeGreaterThanOrEqual(2)
  })

  it('triggers cordon modal and executes mutation upon confirmation', async () => {
    const user = userEvent.setup()
    vi.mocked(nodeApi.listNodes).mockResolvedValue(mockNodes)
    const cordonSpy = vi.mocked(nodeApi.cordonNode).mockResolvedValue({
      ...mockNodes[0],
      is_cordoned: true,
    })

    renderWithProviders(<NodesPage />)

    await waitFor(() => {
      expect(screen.getByText('compute-alpha.infra')).toBeInTheDocument()
    })

    // Click Cordon button for compute-alpha
    const cordonBtn = screen.getByRole('button', { name: /^Cordon$/i })
    await user.click(cordonBtn)

    // Verify confirmation dialog appeared
    expect(screen.getByText(/Cordon Node compute-alpha.infra\?/i)).toBeInTheDocument()
    expect(
      screen.getByText(/Cordoning isolates "compute-alpha.infra" from new workload scheduling placements/i)
    ).toBeInTheDocument()

    // Confirm action
    const confirmBtn = screen.getByRole('button', { name: /^Cordon Node$/i })
    await user.click(confirmBtn)

    await waitFor(() => {
      expect(cordonSpy).toHaveBeenCalledWith('node-uuid-01')
    })
  })

  it('triggers uncordon modal and executes mutation upon confirmation', async () => {
    const user = userEvent.setup()
    vi.mocked(nodeApi.listNodes).mockResolvedValue(mockNodes)
    const uncordonSpy = vi.mocked(nodeApi.uncordonNode).mockResolvedValue({
      ...mockNodes[1],
      is_cordoned: false,
    })

    renderWithProviders(<NodesPage />)

    await waitFor(() => {
      expect(screen.getByText('compute-beta.infra')).toBeInTheDocument()
    })

    // Click Uncordon button for compute-beta
    const uncordonBtn = screen.getByRole('button', { name: /^Uncordon$/i })
    await user.click(uncordonBtn)

    expect(screen.getByText(/Uncordon Node compute-beta.infra\?/i)).toBeInTheDocument()

    const confirmBtn = screen.getByRole('button', { name: /^Uncordon Node$/i })
    await user.click(confirmBtn)

    await waitFor(() => {
      expect(uncordonSpy).toHaveBeenCalledWith('node-uuid-02')
    })
  })
})
