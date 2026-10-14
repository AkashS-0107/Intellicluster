import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import { renderWithProviders } from './test-utils'
import { Routes, Route } from 'react-router-dom'
import { HeroLandingPage } from '@/pages/HeroLandingPage'
import { OperationalGuard } from '@/components/layout/OperationalGuard'
import { DashboardPage } from '@/pages/DashboardPage'
import { ClustersPage } from '@/pages/ClustersPage'
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

describe('Hero Landing Page & Operational Health Gate', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    sessionStorage.clear()
    vi.mocked(systemApi.getHealth).mockResolvedValue({
      status: 'healthy',
      app_name: 'IntelliCluster',
      environment: 'development',
      version: '1.0.0',
      database: 'healthy',
      timestamp: '2026-10-12T10:00:00Z',
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
      recorded_at: '2026-10-12T10:00:00Z',
    })
  })

  function renderHeroWithRoutes(initialPath = '/', initialVerified = false) {
    return renderWithProviders(
      <Routes>
        <Route path="/" element={<HeroLandingPage />} />
        <Route element={<OperationalGuard />}>
          <Route path="/app" element={<DashboardPage />} />
          <Route path="/clusters" element={<ClustersPage />} />
        </Route>
      </Routes>,
      { initialEntries: [initialPath], initialVerified }
    )
  }

  it('renders initial hero screen with branding, factual description, and prominent Check button', () => {
    renderHeroWithRoutes('/', false)

    // Branding
    expect(screen.getAllByText('INTELLICLUSTER')[0]).toBeInTheDocument()
    expect(screen.getByText('CONSOLE')).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'ML-Driven Cloud Server Clustering & Workload Orchestration'
    )

    // Factual developer workflow terminal guidance
    expect(screen.getByText(/Terminal 1: FastAPI Backend/i)).toBeInTheDocument()
    expect(screen.getByText(/Terminal 2: React \/ Vite Frontend/i)).toBeInTheDocument()
    expect(
      screen.getByText(/uvicorn intellicluster\.main:app --reload --host 127\.0\.0\.1 --port 8000/i)
    ).toBeInTheDocument()

    // Pre-flight check section with prominent Check button
    const checkBtn = screen.getByRole('button', { name: /^Check$/i })
    expect(checkBtn).toBeInTheDocument()
    expect(checkBtn).toBeEnabled()

    // Does not show Enter Dashboard before checking
    expect(screen.queryByRole('button', { name: /^Enter Dashboard$/i })).not.toBeInTheDocument()
  })

  it('displays checking loading state and prevents duplicate requests when Check is clicked', async () => {
    let resolveHealthPromise: (value: any) => void
    const pendingPromise = new Promise((resolve) => {
      resolveHealthPromise = resolve
    })
    vi.mocked(systemApi.getHealth).mockReturnValue(pendingPromise as any)

    renderHeroWithRoutes('/', false)

    const checkBtn = screen.getByRole('button', { name: /^Check$/i })
    fireEvent.click(checkBtn)

    // Immediately shows loading state
    expect(screen.getByText(/Probing Backend Health\.\.\./i)).toBeInTheDocument()

    // Check button should be in loading state and disabled against duplicate clicks
    const loadingBtn = screen.getByRole('button', { name: /Checking/i })
    expect(loadingBtn).toBeDisabled()

    // Fire duplicate click to verify idempotency
    fireEvent.click(loadingBtn)
    expect(systemApi.getHealth).toHaveBeenCalledTimes(1)

    // Resolve promise
    resolveHealthPromise!({
      status: 'healthy',
      app_name: 'IntelliCluster',
      environment: 'development',
      version: '1.0.0',
      database: 'healthy',
      timestamp: '2026-10-12T10:00:00Z',
      step: '1 (Backend)',
    })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^Enter Dashboard$/i })).toBeInTheDocument()
    })
  })

  it('displays grounded health parameters and enables Enter Dashboard on successful health check without auto-navigating', async () => {
    vi.mocked(systemApi.getHealth).mockResolvedValue({
      status: 'healthy',
      app_name: 'IntelliCluster',
      environment: 'development',
      version: '1.0.0',
      database: 'healthy',
      timestamp: '2026-10-12T10:00:00Z',
      step: '1 (Backend)',
    })

    renderHeroWithRoutes('/', false)

    const checkBtn = screen.getByRole('button', { name: /^Check$/i })
    fireEvent.click(checkBtn)

    await waitFor(() => {
      expect(screen.getByText(/Backend Health Probe Verified/i)).toBeInTheDocument()
    })

    // Grounded parameters from response
    expect(screen.getByText('v1.0.0')).toBeInTheDocument()
    expect(screen.getByText(/development/i)).toBeInTheDocument()
    expect(screen.getByText('1 (Backend)')).toBeInTheDocument()
    expect(screen.getByText(/STATUS:\s*healthy/i)).toBeInTheDocument()

    // Clicking Check alone must NOT navigate away from the hero page
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()

    // Prominent Enter Dashboard button is now available
    const enterDashboardBtn = screen.getByRole('button', { name: /^Enter Dashboard$/i })
    expect(enterDashboardBtn).toBeInTheDocument()
  })

  it('displays backend-unavailable error and functional Retry Check button when health check fails', async () => {
    vi.mocked(systemApi.getHealth).mockRejectedValue(new Error('Connection refused at 127.0.0.1:8000'))

    renderHeroWithRoutes('/', false)

    const checkBtn = screen.getByRole('button', { name: /^Check$/i })
    fireEvent.click(checkBtn)

    await waitFor(() => {
      expect(screen.getByText(/Backend Unavailable/i)).toBeInTheDocument()
      expect(screen.getByText(/Error detail: Connection refused at 127\.0\.0\.1:8000/i)).toBeInTheDocument()
    })

    // Shows helpful instructions to start Terminal 1
    expect(screen.getByText(/How to resolve:/i)).toBeInTheDocument()

    // Does NOT show Enter Dashboard button
    expect(screen.queryByRole('button', { name: /^Enter Dashboard$/i })).not.toBeInTheDocument()

    // Functional Retry Check button is available
    const retryBtn = screen.getByRole('button', { name: /^Retry Check$/i })
    expect(retryBtn).toBeInTheDocument()

    // Clicking Retry Check re-executes getHealth
    vi.mocked(systemApi.getHealth).mockResolvedValue({
      status: 'healthy',
      app_name: 'IntelliCluster',
      environment: 'development',
      version: '1.0.0',
      database: 'healthy',
      timestamp: '2026-10-12T10:00:00Z',
      step: '1 (Backend)',
    })

    fireEvent.click(retryBtn)

    await waitFor(() => {
      expect(screen.getByText(/Backend Health Probe Verified/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /^Enter Dashboard$/i })).toBeInTheDocument()
    })
  })

  it('navigates to the operational dashboard at "/app" only after selecting Enter Dashboard', async () => {
    vi.mocked(systemApi.getHealth).mockResolvedValue({
      status: 'healthy',
      app_name: 'IntelliCluster',
      environment: 'development',
      version: '1.0.0',
      database: 'healthy',
      timestamp: '2026-10-12T10:00:00Z',
      step: '1 (Backend)',
    })

    renderHeroWithRoutes('/', false)

    fireEvent.click(screen.getByRole('button', { name: /^Check$/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^Enter Dashboard$/i })).toBeInTheDocument()
    })

    const enterDashboardBtn = screen.getByRole('button', { name: /^Enter Dashboard$/i })
    fireEvent.click(enterDashboardBtn)

    // Should navigate to DashboardPage (Operational interface)
    await waitFor(() => {
      expect(screen.getByText('Total Clusters')).toBeInTheDocument()
    })
  })

  it('redirects direct route access back to the landing page when health check was not completed in session', async () => {
    // Attempt direct access to operational route /app with initialVerified: false
    renderHeroWithRoutes('/app', false)

    // Should be redirected to Hero landing page
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^Check$/i })).toBeInTheDocument()
      expect(screen.queryByText('Total Clusters')).not.toBeInTheDocument()
    })
  })

  it('redirects direct access to /clusters back to the landing page when session is not verified', async () => {
    renderHeroWithRoutes('/clusters', false)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^Check$/i })).toBeInTheDocument()
      expect(screen.queryByText('Cluster Management')).not.toBeInTheDocument()
    })
  })

  it('allows direct access to operational routes when health check has been verified in session', async () => {
    renderHeroWithRoutes('/app', true)

    await waitFor(() => {
      expect(screen.getByText('Total Clusters')).toBeInTheDocument()
    })
  })
})
