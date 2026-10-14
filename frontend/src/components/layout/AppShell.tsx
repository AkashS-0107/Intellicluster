import { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { Footer } from './Footer'
import { useQuery } from '@tanstack/react-query'
import { getHealth } from '@/api/system'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export function AppShell() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const {
    data: health,
    error: healthError,
    isError,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['system-health'],
    queryFn: ({ signal }) => getHealth(signal),
    refetchInterval: 30000,
    retry: 1,
  })

  // Handle Escape key to dismiss mobile drawer
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && isMobileMenuOpen) {
        setIsMobileMenuOpen(false)
      }
    }
    if (isMobileMenuOpen) {
      window.addEventListener('keydown', handleKeyDown)
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isMobileMenuOpen])

  const isBackendUnreachable = isError || (health && health.status !== 'healthy' && health.status !== 'degraded')

  return (
    <div className="relative flex h-screen w-screen overflow-hidden bg-[#F5F7FB] text-[#101828]">
      {/* Hero4-inspired subtle technical grid background pattern */}
      <div
        className="pointer-events-none absolute inset-0 z-0 opacity-40 bg-hero4-grid"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 opacity-40"
        style={{
          background: 'radial-gradient(ellipse at 50% 0%, rgba(36, 77, 232, 0.05) 0%, transparent 70%)',
        }}
        aria-hidden="true"
      />

      {/* Desktop Sidebar (visible on lg and above) */}
      <div className="hidden lg:flex z-20 shrink-0">
        <Sidebar />
      </div>

      {/* Mobile Navigation Drawer (slide-over with backdrop) */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 z-50 lg:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Mobile Navigation"
        >
          {/* Backdrop overlay */}
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={() => setIsMobileMenuOpen(false)}
            aria-hidden="true"
            data-testid="mobile-drawer-backdrop"
          />

          {/* Drawer container */}
          <div className="fixed inset-y-0 left-0 w-72 max-w-[85vw] bg-white border-r border-[#DCE2ED] shadow-2xl z-50">
            <Sidebar
              isMobile={true}
              onCloseMobile={() => setIsMobileMenuOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Application Viewport */}
      <div className="relative flex flex-1 flex-col overflow-hidden z-10">
        <Header onToggleMobileMenu={() => setIsMobileMenuOpen((prev) => !prev)} />

        {/* Global Connection Warning Banner if FastAPI is down */}
        {isBackendUnreachable && (
          <div className="flex items-center justify-between bg-[#FEF3F2] border-b border-[#FECDCA] px-4 sm:px-6 py-2.5 text-xs text-[#B42318] shrink-0 shadow-2xs">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-[#D92D20] shrink-0" />
              <span>
                <strong>Backend Unreachable:</strong> FastAPI server at{' '}
                <code className="font-mono bg-white px-1.5 py-0.5 rounded border border-[#FECDCA] text-[#B42318]">
                  http://127.0.0.1:8000
                </code>{' '}
                is not responding.
                {healthError instanceof Error && (
                  <span className="hidden md:inline text-[11px] text-[#7A271A] ml-1 font-mono">
                    ({healthError.message})
                  </span>
                )}
              </span>
            </div>
            <Button
              size="xs"
              variant="outline"
              onClick={() => refetch()}
              isLoading={isFetching}
              icon={<RefreshCw className="w-3 h-3" />}
              className="border-[#FDA29B] bg-white hover:bg-[#FEE4E2] text-[#B42318] shrink-0"
              aria-label="Retry connecting to backend"
            >
              Retry
            </Button>
          </div>
        )}

        {/* Unified Scrollable Container: Main Content Area + Global Footer */}
        <div className="flex-1 overflow-y-auto flex flex-col min-h-0">
          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1600px] w-full mx-auto">
            <Outlet />
          </main>
          <Footer />
        </div>
      </div>
    </div>
  )
}
