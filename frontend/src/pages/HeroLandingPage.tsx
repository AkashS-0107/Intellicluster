import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHealthGate } from '@/context/HealthGateContext'
import { Button } from '@/components/ui/Button'
import {
  ShieldCheck,
  Activity,
  ArrowRight,
  RefreshCw,
  Terminal,
  Server,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  Database,
  Cpu,
  Network,
} from 'lucide-react'
import { cn } from '@/utils/cn'

export function HeroLandingPage() {
  const navigate = useNavigate()
  const {
    isVerified,
    isChecking,
    healthData,
    errorMessage,
    checkHealth,
  } = useHealthGate()

  // Track if check has been triggered at least once in this component view
  const [hasAttemptedCheck, setHasAttemptedCheck] = useState<boolean>(() => isVerified || !!healthData)

  const handleCheck = async () => {
    setHasAttemptedCheck(true)
    await checkHealth()
  }

  const handleEnterDashboard = () => {
    navigate('/app')
  }

  const isFailed = hasAttemptedCheck && !isChecking && !isVerified

  return (
    <div className="relative min-h-[100dvh] w-full overflow-x-hidden bg-[#F5F7FB] text-[#101828] flex flex-col justify-between selection:bg-[#E8EEFF] selection:text-[#244DE8]">
      {/* Background Graphic: Restrained Technical Grid & Subtle Ambient Radial Light Blue Accent */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-60 bg-hero4-grid"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-40"
        style={{
          background: 'radial-gradient(ellipse 70% 40% at 50% -5%, rgba(36, 77, 232, 0.08) 0%, transparent 75%)',
        }}
        aria-hidden="true"
      />

      {/* Top Application Header Bar: Hero4 Refined Hierarchy */}
      <header className="relative z-10 flex h-16 items-center justify-between border-b border-[#DCE2ED] bg-white/90 backdrop-blur-md px-4 sm:px-8 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#244DE8] text-white shadow-xs">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-bold tracking-wider text-[#101828] uppercase">
                INTELLICLUSTER
              </span>
              <span className="rounded border border-[#C7D7FE] bg-[#E8EEFF] px-1.5 py-0.5 text-[10px] font-mono text-[#244DE8] font-semibold">
                CONSOLE
              </span>
            </div>
            <span className="text-[10px] text-[#667085] font-mono tracking-wider">
              CLUSTER CONTROL PLANE
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-md border border-[#DCE2ED] bg-[#F8FAFC] text-[#475467]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#244DE8] animate-pulse" />
            <span>ENGINE:</span>
            <span className="text-[#244DE8] font-bold">HEURISTIC v1.0</span>
          </div>
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-[#DCE2ED] bg-white text-[11px] text-[#667085]">
            <span>PORT 8000 & 3000</span>
          </div>
        </div>
      </header>

      {/* Main Hero Container */}
      <main className="relative z-10 flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 flex flex-col justify-center space-y-8">
        {/* Hero Header & Value Proposition */}
        <div className="text-center max-w-3xl mx-auto space-y-4 pt-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#C7D7FE] bg-[#E8EEFF] text-[#244DE8] text-xs font-mono tracking-wide font-medium shadow-2xs">
            <Activity className="h-3.5 w-3.5 animate-pulse text-[#244DE8]" />
            <span>Local Runtime Verification</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-[#101828] font-sans leading-tight">
            ML-Driven Cloud Server Clustering & Workload Orchestration
          </h1>

          <p className="text-sm sm:text-base text-[#475467] leading-relaxed font-sans max-w-2xl mx-auto">
            High-precision compute cluster topology, live telemetry observation, and deterministic heuristic task scheduling. Designed with strict operational decoupling between FastAPI REST backend and Vite React frontend.
          </p>
        </div>

        {/* Restrained Technical Topology Visualization */}
        <div className="rounded-xl border border-[#DCE2ED] bg-white p-4 sm:p-5 shadow-xs overflow-hidden">
          <div className="flex items-center justify-between pb-3 border-b border-[#EAEFF7] mb-3">
            <div className="flex items-center gap-2 text-xs font-mono font-semibold text-[#101828]">
              <Network className="w-4 h-4 text-[#244DE8]" />
              <span>LOGICAL ARCHITECTURE TOPOLOGY</span>
            </div>
            <span className="text-[11px] font-mono text-[#667085]">
              Decoupled Two-Tier Protocol
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
            {/* Tier 1 Node */}
            <div className="p-3.5 rounded-lg border border-[#DCE2ED] bg-[#F8FAFC] space-y-1.5 relative">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#667085] uppercase">Frontend Layer</span>
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
              </div>
              <div className="text-sm font-bold text-[#101828]">Web Dashboard</div>
              <p className="text-[11px] text-[#475467] font-sans">
                Port 3000 • TanStack Query state cache • Responsive Draggable grid.
              </p>
            </div>

            {/* Tier 2 Node */}
            <div className="p-3.5 rounded-lg border border-[#C7D7FE] bg-[#E8EEFF]/60 space-y-1.5 relative">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#244DE8] font-bold uppercase">Orchestration Gateway</span>
                <span className="h-2 w-2 rounded-full bg-[#244DE8] animate-pulse" />
              </div>
              <div className="text-sm font-bold text-[#101828]">FastAPI Services</div>
              <p className="text-[11px] text-[#475467] font-sans">
                Port 8000 • Heuristic Placement Engine • REST telemetry & nodes APIs.
              </p>
            </div>

            {/* Tier 3 Node */}
            <div className="p-3.5 rounded-lg border border-[#DCE2ED] bg-[#F8FAFC] space-y-1.5 relative">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#667085] uppercase">Data & Model State</span>
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
              </div>
              <div className="text-sm font-bold text-[#101828]">SQLite & Model Artifacts</div>
              <p className="text-[11px] text-[#475467] font-sans">
                WAL mode storage • 7 offline validated machine learning benchmark weights.
              </p>
            </div>
          </div>
        </div>

        {/* Developer Workflow Terminal Architecture Card */}
        <section
          aria-labelledby="workflow-architecture-heading"
          className="rounded-xl border border-[#DCE2ED] bg-white shadow-xs p-5 sm:p-6"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#EAEFF7] pb-3 mb-4">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-[#244DE8]" />
              <h2 id="workflow-architecture-heading" className="text-xs font-mono font-bold tracking-wider uppercase text-[#101828]">
                Required Developer Workflow
              </h2>
            </div>
            <span className="text-[11px] font-mono text-[#667085]">
              Manual dual-terminal startup • No automatic browser process spawning
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 min-w-0">
            {/* Terminal 1 Spec */}
            <div className="rounded-lg border border-[#DCE2ED] bg-[#F8FAFC] p-3.5 space-y-2 min-w-0">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#244DE8] font-bold">Terminal 1: FastAPI Backend</span>
                <span className="text-[10px] text-[#667085] bg-white px-2 py-0.5 rounded border border-[#DCE2ED]">
                  127.0.0.1:8000
                </span>
              </div>
              <div className="text-[11px] font-mono text-[#667085] truncate">
                Working directory: <code className="text-[#101828]">E:\career\INTELLICLUSTER</code>
              </div>
              <pre className="rounded-md bg-white p-2.5 text-[11px] font-mono text-[#101828] max-w-full overflow-x-auto whitespace-pre-wrap break-all sm:whitespace-pre sm:break-normal border border-[#DCE2ED] select-all shadow-2xs">
                <code>.\.venv\Scripts\python.exe -m uvicorn intellicluster.main:app --reload --host 127.0.0.1 --port 8000</code>
              </pre>
            </div>

            {/* Terminal 2 Spec */}
            <div className="rounded-lg border border-[#DCE2ED] bg-[#F8FAFC] p-3.5 space-y-2 min-w-0">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#244DE8] font-bold">Terminal 2: React / Vite Frontend</span>
                <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
                  Active (Port 3000)
                </span>
              </div>
              <div className="text-[11px] font-mono text-[#667085] truncate">
                Working directory: <code className="text-[#101828]">E:\career\INTELLICLUSTER\frontend</code>
              </div>
              <pre className="rounded-md bg-white p-2.5 text-[11px] font-mono text-[#101828] max-w-full overflow-x-auto whitespace-pre-wrap break-all sm:whitespace-pre sm:break-normal border border-[#DCE2ED] select-all shadow-2xs">
                <code>npm run dev</code>
              </pre>
            </div>
          </div>
        </section>

        {/* System Health Check Interactive Gate */}
        <section
          role="region"
          aria-label="System Health Verification"
          className="rounded-xl border border-[#DCE2ED] bg-white shadow-sm overflow-hidden"
        >
          <div className="p-5 sm:p-6 border-b border-[#EAEFF7] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Server className="h-4 w-4 text-[#244DE8]" />
                <h2 className="text-sm font-mono font-bold tracking-wider uppercase text-[#101828]">
                  System Pre-Flight Health Gate
                </h2>
              </div>
              <p className="text-xs text-[#667085] font-sans">
                Verify backend API connectivity and SQLite database probe before entering operational controls.
              </p>
            </div>

            {/* Main Action Trigger Area */}
            <div className="flex items-center gap-3 shrink-0">
              {!isVerified ? (
                <Button
                  id="btn-health-check"
                  variant="primary"
                  size="md"
                  onClick={handleCheck}
                  isLoading={isChecking}
                  disabled={isChecking}
                  icon={isFailed ? <RefreshCw className="h-4 w-4" /> : <Activity className="h-4 w-4" />}
                  className="font-mono text-xs uppercase tracking-wider font-bold shadow-sm"
                  aria-label={isChecking ? 'Checking backend' : isFailed ? 'Retry Check' : 'Check'}
                >
                  {isChecking ? 'Checking...' : isFailed ? 'Retry Check' : 'Check'}
                </Button>
              ) : (
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCheck}
                    isLoading={isChecking}
                    disabled={isChecking}
                    icon={<RefreshCw className="h-3.5 w-3.5" />}
                    className="font-mono text-xs text-[#475467] hover:text-[#101828]"
                    title="Re-run health probe"
                    aria-label="Re-run health probe"
                  >
                    Re-check
                  </Button>
                  <Button
                    id="btn-enter-dashboard"
                    variant="primary"
                    size="md"
                    onClick={handleEnterDashboard}
                    icon={<ArrowRight className="h-4 w-4" />}
                    className="font-mono text-xs uppercase tracking-wider font-bold shadow-sm bg-[#244DE8] hover:bg-[#1D40C7] text-white"
                    aria-label="Enter Dashboard"
                  >
                    Enter Dashboard
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* Interactive Status & Telemetry Body */}
          <div className="p-5 sm:p-6" aria-live="polite">
            {/* 1. Initial State: Check not yet run */}
            {!hasAttemptedCheck && !isChecking && (
              <div className="flex flex-col sm:flex-row items-center gap-4 rounded-xl border border-[#DCE2ED] bg-[#F8FAFC] p-4 text-center sm:text-left">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#E8EEFF] text-[#244DE8] border border-[#C7D7FE]">
                  <Activity className="h-5 w-5" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-xs font-mono font-bold uppercase text-[#101828]">
                    Probe Pending
                  </h3>
                  <p className="text-xs text-[#475467]">
                    FastAPI health probe has not been executed yet. Click <span className="font-mono text-[#244DE8] font-bold">Check</span> above to query <code className="bg-white border border-[#DCE2ED] px-1.5 py-0.5 rounded text-[#101828]">/health</code> through the Vite proxy.
                  </p>
                </div>
              </div>
            )}

            {/* 2. Loading State: Checking in progress */}
            {isChecking && (
              <div className="flex flex-col items-center justify-center p-8 space-y-3 rounded-xl border border-[#C7D7FE] bg-[#E8EEFF]/30 text-center animate-pulse">
                <RefreshCw className="h-7 w-7 text-[#244DE8] animate-spin" />
                <div className="space-y-1">
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#244DE8]">
                    Probing Backend Health...
                  </h3>
                  <p className="text-xs text-[#667085] font-mono">
                    Querying GET /health on target proxy (127.0.0.1:8000)...
                  </p>
                </div>
              </div>
            )}

            {/* 3. Error State: Backend unreachable */}
            {isFailed && (
              <div className="space-y-4">
                <div className="rounded-xl border border-[#FECDCA] bg-[#FEF3F2] p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-[#D92D20] shrink-0 mt-0.5" />
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#B42318]">
                          Backend Unavailable
                        </h3>
                        <span className="text-[10px] font-mono font-semibold text-[#B42318] bg-white px-2 py-0.5 rounded border border-[#FECDCA]">
                          CONNECTION REFUSED
                        </span>
                      </div>
                      <p className="text-xs text-[#7A271A] leading-relaxed font-sans">
                        Unable to connect to the FastAPI backend server at{' '}
                        <code className="font-mono bg-white border border-[#FECDCA] px-1.5 py-0.5 rounded text-[#B42318]">
                          http://127.0.0.1:8000
                        </code>
                        . The operational dashboard requires an active backend session.
                      </p>
                      {errorMessage && (
                        <div className="text-[11px] font-mono text-[#B42318] bg-white p-2 rounded border border-[#FECDCA]">
                          Error detail: {errorMessage}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-[#DCE2ED] bg-[#F8FAFC] p-4 space-y-2 text-xs min-w-0">
                  <div className="font-mono text-[#101828] font-semibold flex items-center gap-1.5">
                    <Terminal className="h-3.5 w-3.5 text-[#244DE8]" />
                    <span>How to resolve:</span>
                  </div>
                  <ol className="list-decimal list-inside text-[#475467] space-y-1 font-sans text-xs break-words">
                    <li>Open <strong>Terminal 1</strong> in your terminal emulator.</li>
                    <li>Ensure you are in the workspace root: <code className="font-mono bg-white border border-[#DCE2ED] px-1.5 py-0.5 rounded text-[#101828] break-all">E:\career\INTELLICLUSTER</code></li>
                    <li>Start the uvicorn development server:</li>
                  </ol>
                  <pre className="rounded-md bg-white p-2.5 text-[11px] font-mono text-[#244DE8] border border-[#DCE2ED] select-all max-w-full overflow-x-auto whitespace-pre-wrap break-all sm:whitespace-pre sm:break-normal shadow-2xs">
                    <code>.\.venv\Scripts\python.exe -m uvicorn intellicluster.main:app --reload --host 127.0.0.1 --port 8000</code>
                  </pre>
                  <p className="text-[11px] text-[#667085]">
                    Once the server prints <code className="text-[#027A48] font-mono font-semibold break-all">Uvicorn running on http://127.0.0.1:8000</code>, click the <strong>Retry Check</strong> button above.
                  </p>
                </div>
              </div>
            )}

            {/* 4. Success State: Real health data displayed without fabrication */}
            {isVerified && healthData && (
              <div className="space-y-4">
                <div className="rounded-xl border border-[#A6F4C5] bg-[#ECFDF3] p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <CheckCircle2 className="h-5 w-5 text-[#027A48] shrink-0" />
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#027A48]">
                            Backend Health Probe Verified
                          </h3>
                          <span
                            className={cn(
                              'text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase',
                              healthData.status === 'healthy'
                                ? 'bg-white text-[#027A48] border-[#A6F4C5]'
                                : 'bg-white text-[#B54708] border-[#FEDF89]'
                            )}
                          >
                            STATUS: {healthData.status}
                          </span>
                        </div>
                        <p className="text-xs text-[#054F31] mt-0.5">
                          Connection established. Operational dashboard access granted.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Grounded Health Parameters Matrix */}
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  <div className="rounded-lg border border-[#DCE2ED] bg-[#F8FAFC] p-3 space-y-1">
                    <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase text-[#667085]">
                      <Layers className="h-3 w-3 text-[#244DE8]" />
                      <span>Application</span>
                    </div>
                    <div className="text-xs font-mono font-bold text-[#101828] truncate" title={healthData.app_name}>
                      {healthData.app_name}
                    </div>
                  </div>

                  <div className="rounded-lg border border-[#DCE2ED] bg-[#F8FAFC] p-3 space-y-1">
                    <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase text-[#667085]">
                      <Cpu className="h-3 w-3 text-[#244DE8]" />
                      <span>Version</span>
                    </div>
                    <div className="text-xs font-mono font-bold text-[#244DE8] truncate">
                      v{healthData.version}
                    </div>
                  </div>

                  <div className="rounded-lg border border-[#DCE2ED] bg-[#F8FAFC] p-3 space-y-1">
                    <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase text-[#667085]">
                      <Server className="h-3 w-3 text-[#244DE8]" />
                      <span>Environment</span>
                    </div>
                    <div className="text-xs font-mono font-bold text-[#101828] uppercase truncate">
                      {healthData.environment}
                    </div>
                  </div>

                  <div className="rounded-lg border border-[#DCE2ED] bg-[#F8FAFC] p-3 space-y-1">
                    <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase text-[#667085]">
                      <Database className="h-3 w-3 text-[#244DE8]" />
                      <span>Database</span>
                    </div>
                    <div
                      className={cn(
                        'text-xs font-mono font-bold uppercase truncate',
                        healthData.database.includes('healthy') ? 'text-[#027A48]' : 'text-[#B54708]'
                      )}
                      title={healthData.database}
                    >
                      {healthData.database}
                    </div>
                  </div>

                  <div className="rounded-lg border border-[#DCE2ED] bg-[#F8FAFC] p-3 space-y-1">
                    <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase text-[#667085]">
                      <Activity className="h-3 w-3 text-[#244DE8]" />
                      <span>Pipeline Step</span>
                    </div>
                    <div className="text-xs font-mono font-bold text-[#101828] truncate">
                      {healthData.step}
                    </div>
                  </div>

                  <div className="rounded-lg border border-[#DCE2ED] bg-[#F8FAFC] p-3 space-y-1">
                    <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase text-[#667085]">
                      <Clock className="h-3 w-3 text-[#244DE8]" />
                      <span>Timestamp</span>
                    </div>
                    <div
                      className="text-xs font-mono font-bold text-[#101828] truncate"
                      title={healthData.timestamp}
                    >
                      {new Date(healthData.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>

      {/* Global Bottom Architectural Scope Footer */}
      <footer className="relative z-10 border-t border-[#DCE2ED] bg-white/90 backdrop-blur-md px-4 sm:px-8 py-5 text-xs text-[#667085] font-mono flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="font-bold text-[#101828]">INTELLICLUSTER</span>
          <span>•</span>
          <span>MANAGEMENT CONSOLE & WORKLOAD SCHEDULER</span>
        </div>
        <div className="flex items-center gap-4 text-[11px]">
          <span>SCHEDULER: HEURISTIC ENGINE v1.0</span>
          <span>•</span>
          <span>LOCAL DUAL PROCESS</span>
          <span>•</span>
          <span>&copy; {new Date().getFullYear()}</span>
        </div>
      </footer>
    </div>
  )
}
