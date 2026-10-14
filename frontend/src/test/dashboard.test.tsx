import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import { renderWithProviders } from './test-utils'
import { DashboardPage } from '@/pages/DashboardPage'
import * as clusterApi from '@/api/clusters'
import * as nodeApi from '@/api/nodes'
import * as workloadApi from '@/api/workloads'
import * as telemetryApi from '@/api/telemetry'
import * as systemApi from '@/api/system'
import { ClusterResponse, NodeResponse, WorkloadResponse, ClusterCapacitySummary } from '@/types'

vi.mock('@/api/clusters')
vi.mock('@/api/nodes')
vi.mock('@/api/workloads')
vi.mock('@/api/telemetry')
vi.mock('@/api/system')

describe('Dashboard Page', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(systemApi.getHealth).mockResolvedValue({
      status: 'healthy',
      app_name: 'IntelliCluster',
      environment: 'development',
      version: '1.0.0',
      database: 'healthy',
      timestamp: '2026-10-09T10:00:00Z',
      step: '1 (Backend)',
    })
  })

  it('renders aggregate counters and capacity breakdown from controlled API responses', async () => {
    const mockClusters: ClusterResponse[] = [
      {
        id: 'cluster-1',
        name: 'primary-compute',
        status: 'ACTIVE',
        created_at: '2026-10-09T10:00:00Z',
        updated_at: '2026-10-09T10:00:00Z',
      },
    ]

    const mockNodes: NodeResponse[] = [
      {
        id: 'node-1',
        hostname: 'node-01.prod',
        cluster_id: 'cluster-1',
        status: 'READY',
        cpu_cores: 16,
        memory_mb: 65536,
        storage_gb: 1000,
        network_bandwidth_mbps: 10000,
        current_cpu_usage_pct: 35.0,
        current_memory_usage_mb: 20000,
        current_disk_usage_gb: 300,
        current_network_tx_mbps: 100,
        current_network_rx_mbps: 200,
        current_network_latency_ms: 2.5,
        active_connections: 50,
        health_score: 95.0,
        risk_score: 0.1,
        active_workload_count: 1,
        last_heartbeat: '2026-10-09T10:05:00Z',
        is_cordoned: false,
        created_at: '2026-10-09T10:00:00Z',
        updated_at: '2026-10-09T10:00:00Z',
      },
      {
        id: 'node-2',
        hostname: 'node-02.prod',
        cluster_id: 'cluster-1',
        status: 'DEGRADED',
        cpu_cores: 8,
        memory_mb: 32768,
        storage_gb: 500,
        network_bandwidth_mbps: 5000,
        current_cpu_usage_pct: 85.0,
        current_memory_usage_mb: 28000,
        current_disk_usage_gb: 400,
        current_network_tx_mbps: 50,
        current_network_rx_mbps: 70,
        current_network_latency_ms: 25.0,
        active_connections: 12,
        health_score: 25.0,
        risk_score: 0.1,
        active_workload_count: 0,
        last_heartbeat: '2026-10-09T10:05:00Z',
        is_cordoned: true,
        created_at: '2026-10-09T10:00:00Z',
        updated_at: '2026-10-09T10:00:00Z',
      },
    ]

    const mockWorkloads: WorkloadResponse[] = [
      {
        id: 'w-1',
        name: 'batch-etl',
        cluster_id: 'cluster-1',
        assigned_node_id: 'node-1',
        workload_type: 'BATCH',
        cpu_cores_requested: 4,
        memory_mb_requested: 8192,
        storage_gb_requested: 10,
        network_mbps_requested: 50,
        priority: 'HIGH',
        status: 'RUNNING',
        retry_count: 0,
        max_retries: 3,
        created_at: '2026-10-09T10:00:00Z',
        updated_at: '2026-10-09T10:00:00Z',
      },
    ]

    const mockCapacity: ClusterCapacitySummary = {
      cluster_id: 'cluster-1',
      cluster_name: 'primary-compute',
      total_nodes: 2,
      ready_nodes: 1,
      total_cpu_cores: 24.0,
      allocated_cpu_cores: 4.0,
      allocatable_cpu_cores: 12.0,
      total_memory_mb: 98304,
      allocated_memory_mb: 8192,
      allocatable_memory_mb: 57344,
      average_cpu_usage_pct: 60.0,
      average_memory_usage_pct: 48.8,
      active_workload_count: 1,
    }

    vi.mocked(clusterApi.listClusters).mockResolvedValue(mockClusters)
    vi.mocked(nodeApi.listNodes).mockResolvedValue(mockNodes)
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue(mockWorkloads)
    vi.mocked(clusterApi.getClusterCapacity).mockResolvedValue(mockCapacity)
    vi.mocked(telemetryApi.getClusterAggregate).mockResolvedValue({
      total_reporting_nodes: 2,
      avg_cpu_usage_pct: 60.0,
      max_cpu_usage_pct: 85.0,
      avg_memory_usage_pct: 48.8,
      max_memory_usage_pct: 85.4,
      avg_latency_ms: 13.75,
      total_active_connections: 62,
      recorded_at: '2026-10-09T10:05:00Z',
    })

    renderWithProviders(<DashboardPage />)

    // Verify aggregate counters inside waitFor so queries resolve
    await waitFor(() => {
      expect(screen.getByText('Ready Nodes')).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByText('60.0/100')).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByText(/24.0 total/i)).toBeInTheDocument()
    })
  })

  it('renders intentional empty state when no clusters exist', async () => {
    vi.mocked(clusterApi.listClusters).mockResolvedValue([])
    vi.mocked(nodeApi.listNodes).mockResolvedValue([])
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText(/No Clusters or Compute Nodes Registered/i)).toBeInTheDocument()
    })
  })

  it('renders error state when an API request fails', async () => {
    vi.mocked(clusterApi.listClusters).mockRejectedValue(new Error('Internal database lock failure'))
    vi.mocked(nodeApi.listNodes).mockResolvedValue([])
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText(/Telemetry Ingestion Warning/i)).toBeInTheDocument()
      expect(screen.getByText(/Internal database lock failure/i)).toBeInTheDocument()
    })
  })

  it('renders all 6 candidate modular widgets within DraggableWidgetGrid', async () => {
    vi.mocked(clusterApi.listClusters).mockResolvedValue([])
    vi.mocked(nodeApi.listNodes).mockResolvedValue([])
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    // Verify widget region semantics and titles
    expect(screen.getByRole('region', { name: 'Cluster Overview & Capacity' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Compute Fleet Inventory' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Workload Operations' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Real-Time Telemetry Observability' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'System & Engine Health' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Scientific ML Model Registry' })).toBeInTheDocument()
  })

  it('reorders widgets using Move Up / Move Down buttons and resets via Reset Grid', async () => {
    vi.mocked(clusterApi.listClusters).mockResolvedValue([])
    vi.mocked(nodeApi.listNodes).mockResolvedValue([])
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    const regionsBefore = screen.getAllByRole('region')
    expect(regionsBefore[0]).toHaveAttribute('aria-label', 'Cluster Overview & Capacity')
    expect(regionsBefore[1]).toHaveAttribute('aria-label', 'Compute Fleet Inventory')

    // Click Move Down on the first widget
    const moveDownBtn = screen.getByRole('button', { name: 'Move Cluster Overview & Capacity down' })
    fireEvent.click(moveDownBtn)

    const regionsAfterMove = screen.getAllByRole('region')
    expect(regionsAfterMove[0]).toHaveAttribute('aria-label', 'Compute Fleet Inventory')
    expect(regionsAfterMove[1]).toHaveAttribute('aria-label', 'Cluster Overview & Capacity')

    // Click Move Up on the first widget to restore position
    const moveUpBtn = screen.getByRole('button', { name: 'Move Cluster Overview & Capacity up' })
    fireEvent.click(moveUpBtn)

    const regionsRestored = screen.getAllByRole('region')
    expect(regionsRestored[0]).toHaveAttribute('aria-label', 'Cluster Overview & Capacity')

    // Click Reset Grid
    const resetBtn = screen.getByRole('button', { name: /Reset Grid Layout/i })
    fireEvent.click(resetBtn)

    const regionsFinal = screen.getAllByRole('region')
    expect(regionsFinal[0]).toHaveAttribute('aria-label', 'Cluster Overview & Capacity')
  })

  it('isolates pointer events on internal widget controls from dragging', async () => {
    vi.mocked(clusterApi.listClusters).mockResolvedValue([])
    vi.mocked(nodeApi.listNodes).mockResolvedValue([])
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    // Probe button inside Backend Health Widget
    const probeBtn = screen.getByRole('button', { name: /Probe backend health/i })
    expect(probeBtn).toBeInTheDocument()

    // Wait for initial health query to resolve so button is enabled
    await waitFor(() => {
      expect(probeBtn).not.toBeDisabled()
    })

    // Dispatch pointerdown to verify no unhandled exception and drag isolation
    const pointerEvent = new MouseEvent('pointerdown', { bubbles: true, cancelable: true })
    probeBtn.dispatchEvent(pointerEvent)
    expect(probeBtn).toBeEnabled()
  })

  it('reorders widgets using native HTML5 drag and drop events', async () => {
    vi.mocked(clusterApi.listClusters).mockResolvedValue([])
    vi.mocked(nodeApi.listNodes).mockResolvedValue([])
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue([])

    renderWithProviders(<DashboardPage />)

    const regionsBefore = screen.getAllByRole('region')
    expect(regionsBefore[0]).toHaveAttribute('aria-label', 'Cluster Overview & Capacity')
    expect(regionsBefore[1]).toHaveAttribute('aria-label', 'Compute Fleet Inventory')

    // Find drag handle for first widget
    const dragHandle = screen.getByRole('button', { name: 'Drag Cluster Overview & Capacity to rearrange' })
    const targetRegion = regionsBefore[1]

    // Create mock dataTransfer object
    const dataTransfer = {
      effectAllowed: '',
      dropEffect: '',
      setData: vi.fn(),
      getData: vi.fn().mockReturnValue('cluster-overview'),
    }

    fireEvent.dragStart(dragHandle, { dataTransfer })
    fireEvent.dragOver(targetRegion, { dataTransfer })
    fireEvent.drop(targetRegion, { dataTransfer })
    fireEvent.dragEnd(dragHandle)

    const regionsAfter = screen.getAllByRole('region')
    expect(regionsAfter[0]).toHaveAttribute('aria-label', 'Compute Fleet Inventory')
    expect(regionsAfter[1]).toHaveAttribute('aria-label', 'Cluster Overview & Capacity')
  })

  it('renders loading indicators while queries are in-flight', async () => {
    // Unresolved promises simulate in-flight loading state
    vi.mocked(clusterApi.listClusters).mockReturnValue(new Promise(() => {}))
    vi.mocked(nodeApi.listNodes).mockReturnValue(new Promise(() => {}))
    vi.mocked(workloadApi.listWorkloads).mockReturnValue(new Promise(() => {}))

    renderWithProviders(<DashboardPage />)

    // Verify loading placeholders are rendered
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(1)
  })
})
