import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useHealthGate } from '@/context/HealthGateContext'

export function OperationalGuard() {
  const { isVerified } = useHealthGate()
  const location = useLocation()

  if (!isVerified) {
    // If the user opens an operational route directly without completing the check in the current session,
    // redirect them to the hero landing page.
    return <Navigate to="/" replace state={{ from: location }} />
  }

  return <Outlet />
}
