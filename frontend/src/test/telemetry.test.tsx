import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import { renderWithProviders } from './test-utils'
import { TelemetryPage } from '@/pages/TelemetryPage'
import * as clusterApi from '@/api/clusters'
import * as nodeApi from '@/api/nodes'
import * as telemetryApi from '@/api/telemetry'
import * as mlApi from '@/api/ml'

vi.mock('@/api/clusters')
vi.mock('@/api/nodes')
vi.mock('@/api/telemetry')
vi.mock('@/api/ml')

describe('Telemetry Page — History Readiness & Forecasting Guardrails', () => {
  const mockNode = {
    id: 'node-lstm-01',
    hostname: 'worker-lstm-01.us-east.compute',
    status: 'READY' as const,
    cpu_cores: 16,
    memory_mb: 32768,
    cluster_id: 'cluster-1',
    storage_gb: 500,
    network_bandwidth_mbps: 1000,
    health_score: 95.0,
    risk_score: 5.0,
    current_cpu_usage_pct: 45.0,
    current_memory_usage_mb: 16384,
    current_disk_usage_gb: 120,
    current_network_tx_mbps: 10,
    current_network_rx_mbps: 15,
    current_network_latency_ms: 5.0,
    active_connections: 20,
    active_workload_count: 2,
    last_heartbeat: '2026-10-13T12:00:00Z',
    is_cordoned: false,
    created_at: '2026-10-01T00:00:00Z',
    updated_at: '2026-10-13T12:00:00Z',
  }

  beforeEach(() => {
    vi.resetAllMocks()

    vi.mocked(clusterApi.listClusters).mockResolvedValue([
      {
        id: 'cluster-1',
        name: 'Core Compute',
        status: 'ACTIVE',
        description: 'Core cluster',
        created_at: '2026-10-01T00:00:00Z',
        updated_at: '2026-10-01T00:00:00Z',
      },
    ])

    vi.mocked(nodeApi.listNodes).mockResolvedValue([mockNode])

    vi.mocked(telemetryApi.getClusterAggregate).mockResolvedValue({
      cluster_id: 'cluster-1',
      total_reporting_nodes: 1,
      avg_cpu_usage_pct: 45.0,
      max_cpu_usage_pct: 45.0,
      avg_memory_usage_pct: 50.0,
      max_memory_usage_pct: 50.0,
      avg_latency_ms: 5.0,
      total_active_connections: 20,
      recorded_at: '2026-10-13T12:00:00Z',
    })

    vi.mocked(telemetryApi.getNodeTelemetryHistory).mockResolvedValue([
      {
        id: 'snap-1',
        node_id: 'node-lstm-01',
        recorded_at: '2026-10-13T12:00:00Z',
        cpu_usage_pct: 45.0,
        memory_usage_mb: 16384,
        memory_usage_pct: 50.0,
        disk_usage_gb: 120,
        disk_usage_pct: 24.0,
        network_rx_mbps: 10.0,
        network_tx_mbps: 10.0,
        network_latency_ms: 5.0,
        active_connections: 15,
        reported_status: 'READY',
      },
    ])

    vi.mocked(telemetryApi.getSimulatorStatus).mockResolvedValue({
      is_running: false,
      interval_seconds: 10,
      target_node_id: null,
      snapshots_emitted: 0,
      started_at: null,
      collector_mode: 'opt_in_development_simulator',
    })
  })

  it('renders history readiness and locks live forecasting when history is insufficient (<168h)', async () => {
    vi.mocked(telemetryApi.getNodeHistoryReadiness).mockResolvedValue({
      node_id: 'node-lstm-01',
      is_ready: false,
      valid_hourly_observations: 5,
      required_observations: 168,
      readiness_percentage: 3.0,
      total_raw_snapshots: 8,
      earliest_usable_timestamp: '2026-10-13T08:00:00Z',
      latest_usable_timestamp: '2026-10-13T12:00:00Z',
      missing_intervals_count: 163,
      missing_ranges: [],
      validation_reason:
        "Node 'worker-lstm-01' has 5 valid contiguous hourly observation(s). Model requires exactly 168 contiguous hourly snapshots (7 days). Remaining time needed: 163 hour(s).",
      estimated_hours_remaining: 163,
      collector_active: false,
      is_simulated: false,
      feature_readiness: {
        cpu_utilization: true,
        memory_usage: true,
        storage_usage: true,
        workload: false,
        resource_allocation: false,
      },
    })

    renderWithProviders(<TelemetryPage />)

    await waitFor(() => {
      expect(
        screen.getByText(/INSUFFICIENT HISTORY \(5 \/ 168 HOURS\)/i)
      ).toBeInTheDocument()
      expect(screen.getByText(/5 of 168 hours \(3%\)/i)).toBeInTheDocument()
      expect(
        screen.getByText(/Model requires exactly 168 contiguous hourly snapshots/i)
      ).toBeInTheDocument()
    })

    // Verify live forecast button is disabled with locked label
    const forecastBtn = screen.getByRole('button', {
      name: /Forecast Locked \(5\/168h\)/i,
    })
    expect(forecastBtn).toBeDisabled()
  })

  it('renders opt-in simulator controls and allows triggering start/stop', async () => {
    vi.mocked(telemetryApi.getNodeHistoryReadiness).mockResolvedValue({
      node_id: 'node-lstm-01',
      is_ready: false,
      valid_hourly_observations: 1,
      required_observations: 168,
      readiness_percentage: 0.6,
      total_raw_snapshots: 1,
      earliest_usable_timestamp: '2026-10-13T12:00:00Z',
      latest_usable_timestamp: '2026-10-13T12:00:00Z',
      missing_intervals_count: 167,
      missing_ranges: [],
      validation_reason: 'Remaining time needed: 167 hour(s).',
      estimated_hours_remaining: 167,
      collector_active: false,
      is_simulated: false,
      feature_readiness: {},
    })

    vi.mocked(telemetryApi.startSimulator).mockResolvedValue({
      is_running: true,
      interval_seconds: 10,
      target_node_id: 'node-lstm-01',
      snapshots_emitted: 0,
      started_at: '2026-10-13T12:01:00Z',
      collector_mode: 'opt_in_development_simulator',
    })

    renderWithProviders(<TelemetryPage />)

    await waitFor(() => {
      expect(
        screen.getByText(/Opt-In Development Telemetry Simulator/i)
      ).toBeInTheDocument()
      expect(screen.getByText(/STOPPED \(IDLE\)/i)).toBeInTheDocument()
    })

    await waitFor(() => {
      const startBtn = screen.getByRole('button', {
        name: /Start Simulator \(Opt-In\)/i,
      })
      expect(startBtn).toBeEnabled()
    })

    const startBtn = screen.getByRole('button', {
      name: /Start Simulator \(Opt-In\)/i,
    })
    fireEvent.click(startBtn)
    expect(telemetryApi.startSimulator).toHaveBeenCalledWith(10, 'node-lstm-01')
  })

  it('allows running the offline historical dataset benchmark without modifying live state', async () => {
    vi.mocked(telemetryApi.getNodeHistoryReadiness).mockResolvedValue({
      node_id: 'node-lstm-01',
      is_ready: false,
      valid_hourly_observations: 0,
      required_observations: 168,
      readiness_percentage: 0,
      total_raw_snapshots: 0,
      earliest_usable_timestamp: null,
      latest_usable_timestamp: null,
      missing_intervals_count: 168,
      missing_ranges: [],
      validation_reason: 'Zero historical snapshots found.',
      estimated_hours_remaining: 168,
      collector_active: false,
      is_simulated: false,
      feature_readiness: {},
    })

    vi.mocked(mlApi.runOfflineEvaluation).mockResolvedValue({
      dataset_name: 'Resource_utilization.csv',
      dataset_total_records: 26305,
      evaluation_range: '2022-01-01 to 2022-01-07',
      forecast_horizon_hours: 24,
      lookback_window_hours: 168,
      target_variables: ['cpu_utilization', 'memory_usage', 'workload'],
      input_features_used: [
        'cpu_utilization',
        'memory_usage',
        'storage_usage',
        'workload',
        'Resource Allocation',
      ],
      predictions: [
        {
          step_hour: 1,
          predicted_cpu_utilization: 57.43,
          predicted_memory_usage: 44.94,
          predicted_workload: 88.52,
        },
      ],
      is_offline_benchmark: true,
      advisory: 'OFFLINE DATASET BENCHMARK: Inference against genuine training dataset.',
      strategy_used: 'multivariate_lstm_v1_offline_dataset',
    })

    renderWithProviders(<TelemetryPage />)

    const benchmarkBtn = await screen.findByRole('button', {
      name: /Run Offline Dataset Benchmark/i,
    })
    expect(benchmarkBtn).toBeInTheDocument()

    fireEvent.click(benchmarkBtn)

    await waitFor(() => {
      expect(mlApi.runOfflineEvaluation).toHaveBeenCalledWith(0)
      expect(
        screen.getByText(/HISTORICAL DATASET: Resource_utilization.csv/i)
      ).toBeInTheDocument()
      expect(
        screen.getByText(/Offline Dataset Benchmark \(24h Ahead Forecast\)/i)
      ).toBeInTheDocument()
    })
  })

  it('enables live forecasting when 168 contiguous hours are ready', async () => {
    vi.mocked(telemetryApi.getNodeHistoryReadiness).mockResolvedValue({
      node_id: 'node-lstm-01',
      is_ready: true,
      valid_hourly_observations: 168,
      required_observations: 168,
      readiness_percentage: 100.0,
      total_raw_snapshots: 180,
      earliest_usable_timestamp: '2026-10-06T12:00:00Z',
      latest_usable_timestamp: '2026-10-13T12:00:00Z',
      missing_intervals_count: 0,
      missing_ranges: [],
      validation_reason: '168 contiguous hourly observations available.',
      estimated_hours_remaining: 0,
      collector_active: false,
      is_simulated: false,
      feature_readiness: {
        cpu_utilization: true,
        memory_usage: true,
        storage_usage: true,
        workload: true,
        resource_allocation: true,
      },
    })

    renderWithProviders(<TelemetryPage />)

    await waitFor(() => {
      expect(
        screen.getByText(/168\/168 CONTIGUOUS HOURS READY/i)
      ).toBeInTheDocument()
    })

    const liveBtn = screen.getByRole('button', {
      name: /Request 24h Live Node Forecast/i,
    })
    expect(liveBtn).toBeEnabled()
  })
})
