import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor, fireEvent, within } from '@testing-library/react'
import { renderWithProviders } from './test-utils'
import { Routes, Route } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { HeroLandingPage } from '@/pages/HeroLandingPage'
import { OperationalGuard } from '@/components/layout/OperationalGuard'
import { DashboardPage } from '@/pages/DashboardPage'
import { ClustersPage } from '@/pages/ClustersPage'
import { NodesPage } from '@/pages/NodesPage'
import { WorkloadsPage } from '@/pages/WorkloadsPage'
import { TelemetryPage } from '@/pages/TelemetryPage'
import { MlRegistryPage } from '@/pages/MlRegistryPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import * as systemApi from '@/api/system'
import * as clusterApi from '@/api/clusters'
import * as nodeApi from '@/api/nodes'
import * as workloadApi from '@/api/workloads'
import * as telemetryApi from '@/api/telemetry'

vi.mock('@/api/system')
vi.mock('@/api/clusters')
vi.mock('@/api/nodes')
vi.mock('@/api/workloads')
vi.mock('@/api/telemetry')

describe('Application Shell & Routing Navigation', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    sessionStorage.clear()
    vi.mocked(systemApi.getHealth).mockResolvedValue({
      status: 'healthy',
      app_name: 'IntelliCluster',
      environment: 'development',
      version: '1.0.0',
      database: 'healthy',
      timestamp: '2026-10-09T10:00:00Z',
      step: '1 (Backend)',
    })
    vi.mocked(clusterApi.listClusters).mockResolvedValue([])
    vi.mocked(nodeApi.listNodes).mockResolvedValue([])
    vi.mocked(workloadApi.listWorkloads).mockResolvedValue([])
    vi.mocked(telemetryApi.getClusterAggregate).mockResolvedValue({
      total_reporting_nodes: 0,
      avg_cpu_usage_pct: 0,
      max_cpu_usage_pct: 0,
      avg_memory_usage_pct: 0,
      max_memory_usage_pct: 0,
      avg_latency_ms: 0,
      total_active_connections: 0,
      recorded_at: '2026-10-09T10:00:00Z',
    })
    vi.mocked(telemetryApi.getSimulatorStatus).mockResolvedValue({
      is_running: false,
      interval_seconds: 60,
      target_node_id: null,
      snapshots_emitted: 0,
      started_at: null,
      collector_mode: 'opt_in_development_simulator',
    })
    vi.mocked(telemetryApi.getNodeHistoryReadiness).mockResolvedValue({
      node_id: 'test-node-1',
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
  })

  function renderApp(initialPath: string, initialVerified = true) {
    return renderWithProviders(
      <Routes>
        <Route path="/" element={<HeroLandingPage />} />
        <Route element={<OperationalGuard />}>
          <Route element={<AppShell />}>
            <Route path="/app" element={<DashboardPage />} />
            <Route path="/clusters" element={<ClustersPage />} />
            <Route path="/nodes" element={<NodesPage />} />
            <Route path="/workloads" element={<WorkloadsPage />} />
            <Route path="/telemetry" element={<TelemetryPage />} />
            <Route path="/ml-registry" element={<MlRegistryPage />} />
          </Route>
        </Route>
        <Route element={<AppShell />}>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>,
      { initialEntries: [initialPath], initialVerified }
    )
  }

  it('renders Hero landing page at root "/"', async () => {
    renderApp('/', false)
    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
        'ML-Driven Cloud Server Clustering & Workload Orchestration'
      )
      expect(screen.getByRole('button', { name: /^Check$/i })).toBeInTheDocument()
    })
  })

  it('renders Dashboard at dedicated route "/app"', async () => {
    renderApp('/app', true)
    await waitFor(() => {
      expect(screen.getByText('Fleet Overview')).toBeInTheDocument()
      expect(screen.getByText('Total Clusters')).toBeInTheDocument()
    })
  })

  it('renders Clusters page at "/clusters"', async () => {
    renderApp('/clusters', true)
    await waitFor(() => {
      expect(screen.getByText('Cluster Management')).toBeInTheDocument()
    })
  })

  it('renders Nodes page at "/nodes"', async () => {
    renderApp('/nodes', true)
    await waitFor(() => {
      expect(screen.getByText('Node Inventory')).toBeInTheDocument()
    })
  })

  it('renders Workloads page at "/workloads"', async () => {
    renderApp('/workloads', true)
    await waitFor(() => {
      expect(screen.getByText('Workload Orchestration')).toBeInTheDocument()
    })
  })

  it('renders Telemetry page at "/telemetry"', async () => {
    renderApp('/telemetry', true)
    await waitFor(() => {
      expect(screen.getByText('Telemetry Observability')).toBeInTheDocument()
    })
  })

  it('renders ML Registry page at "/ml-registry"', async () => {
    renderApp('/ml-registry', true)
    await waitFor(() => {
      expect(screen.getByText('Machine Learning Model Catalog')).toBeInTheDocument()
    })
  })

  it('renders 404 Not Found page for invalid route "/invalid-route"', async () => {
    renderApp('/invalid-route', true)
    await waitFor(() => {
      expect(screen.getByText('404 — ROUTE NOT FOUND')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /return to fleet overview/i })).toBeInTheDocument()
    })
  })

  it('navigates to "/app" when clicking Return to Fleet Overview on 404 page', async () => {
    renderApp('/invalid-route', true)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /return to fleet overview/i })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /return to fleet overview/i }))

    await waitFor(() => {
      expect(screen.getByText('Fleet Overview')).toBeInTheDocument()
      expect(screen.getByText('Total Clusters')).toBeInTheDocument()
    })
  })

  it('supports BranchedMenu section expand/collapse and synchronizes active route indicators', async () => {
    renderApp('/workloads', true)
    await waitFor(() => {
      expect(screen.getByText('Workload Orchestration')).toBeInTheDocument()
    })

    // Verify section accordion controls
    const operationsSectionBtn = screen.getByRole('button', { name: /^Operations$/i })
    expect(operationsSectionBtn).toHaveAttribute('aria-expanded', 'true')

    // Active item has aria-current="page"
    const activeLink = screen.getByRole('link', { name: /Workloads/i })
    expect(activeLink).toHaveAttribute('aria-current', 'page')

    // Collapse the operations section
    fireEvent.click(operationsSectionBtn)
    expect(operationsSectionBtn).toHaveAttribute('aria-expanded', 'false')

    // Expanding it again
    fireEvent.click(operationsSectionBtn)
    expect(operationsSectionBtn).toHaveAttribute('aria-expanded', 'true')
  })

  it('opens mobile navigation drawer on toggle and closes on Escape key', async () => {
    renderApp('/app', true)
    await waitFor(() => {
      expect(screen.getByText('Fleet Overview')).toBeInTheDocument()
    })

    // Initially mobile drawer dialog is not present
    expect(screen.queryByRole('dialog', { name: 'Mobile Navigation' })).not.toBeInTheDocument()

    // Click mobile hamburger toggle
    const hamburgerBtn = screen.getByRole('button', { name: 'Toggle navigation menu' })
    fireEvent.click(hamburgerBtn)

    // Mobile drawer dialog should now be open
    const drawer = screen.getByRole('dialog', { name: 'Mobile Navigation' })
    expect(drawer).toBeInTheDocument()

    // Press Escape to dismiss drawer
    fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' })

    expect(screen.queryByRole('dialog', { name: 'Mobile Navigation' })).not.toBeInTheDocument()
  })

  it('closes mobile navigation drawer when clicking the backdrop', async () => {
    renderApp('/app', true)
    await waitFor(() => {
      expect(screen.getByText('Fleet Overview')).toBeInTheDocument()
    })

    const hamburgerBtn = screen.getByRole('button', { name: 'Toggle navigation menu' })
    fireEvent.click(hamburgerBtn)

    expect(screen.getByRole('dialog', { name: 'Mobile Navigation' })).toBeInTheDocument()

    const backdrop = screen.getByTestId('mobile-drawer-backdrop')
    fireEvent.click(backdrop)

    expect(screen.queryByRole('dialog', { name: 'Mobile Navigation' })).not.toBeInTheDocument()
  })

  it('automatically closes mobile navigation drawer when a route link is clicked', async () => {
    renderApp('/app', true)
    await waitFor(() => {
      expect(screen.getByText('Fleet Overview')).toBeInTheDocument()
    })

    const hamburgerBtn = screen.getByRole('button', { name: 'Toggle navigation menu' })
    fireEvent.click(hamburgerBtn)

    const drawer = screen.getByRole('dialog', { name: 'Mobile Navigation' })
    expect(drawer).toBeInTheDocument()

    const clustersLink = within(drawer).getByRole('link', { name: /Clusters/i })
    fireEvent.click(clustersLink)

    expect(screen.queryByRole('dialog', { name: 'Mobile Navigation' })).not.toBeInTheDocument()
  })

  it('ensures collapsed section items are unmounted to prevent keyboard focus', async () => {
    renderApp('/app', true)
    await waitFor(() => {
      expect(screen.getByText('Fleet Overview')).toBeInTheDocument()
    })

    // Collapse operations section
    const operationsBtn = screen.getByRole('button', { name: /^Operations$/i })
    fireEvent.click(operationsBtn)
    expect(operationsBtn).toHaveAttribute('aria-expanded', 'false')

    // Dashboard link in that section is no longer rendered in the DOM
    expect(screen.queryByRole('link', { name: /^Dashboard$/i })).not.toBeInTheDocument()
  })

  it('renders global footer with grounded runtime metadata, dynamic year, and technical descriptors', async () => {
    renderApp('/app', true)
    const footer = await screen.findByRole('contentinfo')

    await waitFor(() => {
      expect(within(footer).getByText('ONLINE')).toBeInTheDocument()
    })

    expect(
      within(footer).getByText(/ML-Driven Cloud Server Clustering and Workload Orchestration/i)
    ).toBeInTheDocument()
    expect(
      within(footer).getByText(new RegExp(String(new Date().getFullYear())))
    ).toBeInTheDocument()
    expect(within(footer).getByText('v1.0.0')).toBeInTheDocument()
    expect(within(footer).getByText('SQLITE (WAL)')).toBeInTheDocument()
    expect(within(footer).getByText('HEURISTIC v1.0')).toBeInTheDocument()
  })

  it('renders global footer navigation links and supports direct internal routing', async () => {
    renderApp('/app', true)
    await waitFor(() => {
      expect(screen.getByRole('contentinfo')).toBeInTheDocument()
    })

    const footer = screen.getByRole('contentinfo')
    const taskQueueLink = within(footer).getByRole('link', {
      name: 'Footer navigation: Task Orchestration',
    })
    expect(taskQueueLink).toBeInTheDocument()

    // Click footer link to navigate to Workloads route
    fireEvent.click(taskQueueLink)
    await waitFor(() => {
      expect(screen.getByText('Workload Orchestration')).toBeInTheDocument()
    })
  })

  it('renders global footer on 404 Not Found route', async () => {
    renderApp('/unknown-endpoint', true)
    await waitFor(() => {
      expect(screen.getByText('404 — ROUTE NOT FOUND')).toBeInTheDocument()
      expect(screen.getByRole('contentinfo')).toBeInTheDocument()
    })
  })

  it('renders semantic breadcrumb navigation landmark in global header', async () => {
    renderApp('/clusters', true)
    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toBeInTheDocument()
      expect(screen.getByText('Cluster Management')).toBeInTheDocument()
    })
  })

  it('presents single prominent Retry action on warning banner when backend is offline without duplicate header button', async () => {
    vi.mocked(systemApi.getHealth).mockResolvedValue({
      status: 'offline',
      app_name: 'IntelliCluster',
      environment: 'development',
      version: '1.0.0',
      database: 'unreachable',
      timestamp: '2026-10-09T10:00:00Z',
      step: '1 (Backend)',
    })

    renderApp('/app', true)
    await waitFor(() => {
      expect(screen.getByText(/Backend Unreachable:/i)).toBeInTheDocument()
    })

    // Single prominent retry button in global banner
    const bannerRetryBtn = screen.getByRole('button', { name: 'Retry connecting to backend' })
    expect(bannerRetryBtn).toBeInTheDocument()

    // Header displays status without duplicate conflicting Retry button
    expect(screen.getByText('BACKEND OFFLINE')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Retry backend connection' })).not.toBeInTheDocument()
  })
})
