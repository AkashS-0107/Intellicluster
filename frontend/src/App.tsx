import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { HealthGateProvider } from '@/context/HealthGateContext'
import { OperationalGuard } from '@/components/layout/OperationalGuard'
import { AppShell } from '@/components/layout/AppShell'
import { HeroLandingPage } from '@/pages/HeroLandingPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ClustersPage } from '@/pages/ClustersPage'
import { NodesPage } from '@/pages/NodesPage'
import { WorkloadsPage } from '@/pages/WorkloadsPage'
import { TelemetryPage } from '@/pages/TelemetryPage'
import { MlRegistryPage } from '@/pages/MlRegistryPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <HealthGateProvider>
        <BrowserRouter>
          <Routes>
            {/* Root Welcome Gate */}
            <Route path="/" element={<HeroLandingPage />} />

            {/* Operational Routes Gated behind Verified Health Check */}
            <Route element={<OperationalGuard />}>
              <Route element={<AppShell />}>
                <Route path="/app" element={<DashboardPage />} />
                <Route path="/dashboard" element={<Navigate to="/app" replace />} />
                <Route path="/clusters" element={<ClustersPage />} />
                <Route path="/nodes" element={<NodesPage />} />
                <Route path="/workloads" element={<WorkloadsPage />} />
                <Route path="/telemetry" element={<TelemetryPage />} />
                <Route path="/ml-registry" element={<MlRegistryPage />} />
              </Route>
            </Route>

            {/* Catch-all Not Found Route inside AppShell */}
            <Route element={<AppShell />}>
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </HealthGateProvider>
    </QueryClientProvider>
  )
}

export default App
