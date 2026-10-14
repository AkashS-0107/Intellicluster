import React, { createContext, useContext, useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getHealth } from '@/api/system'
import { HealthResponse } from '@/types'

export const SESSION_STORAGE_GATE_KEY = 'intellicluster_session_health_verified'
export const SESSION_STORAGE_DATA_KEY = 'intellicluster_session_health_data'

export interface HealthGateContextType {
  isVerified: boolean
  isChecking: boolean
  healthData: HealthResponse | null
  error: Error | null
  errorMessage: string | null
  checkHealth: () => Promise<HealthResponse | null>
  resetGate: () => void
  setVerifiedDirectly: (verified: boolean, data?: HealthResponse | null) => void
}

const HealthGateContext = createContext<HealthGateContextType | undefined>(undefined)

export interface HealthGateProviderProps {
  children: React.ReactNode
  initialVerified?: boolean
  initialHealthData?: HealthResponse | null
}

export function HealthGateProvider({
  children,
  initialVerified,
  initialHealthData,
}: HealthGateProviderProps) {
  const queryClient = useQueryClient()

  const [isVerified, setIsVerified] = useState<boolean>(() => {
    if (initialVerified !== undefined) {
      return initialVerified
    }
    try {
      return sessionStorage.getItem(SESSION_STORAGE_GATE_KEY) === 'true'
    } catch {
      return false
    }
  })

  const [healthData, setHealthData] = useState<HealthResponse | null>(() => {
    if (initialHealthData !== undefined) {
      return initialHealthData
    }
    try {
      const stored = sessionStorage.getItem(SESSION_STORAGE_DATA_KEY)
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  const [isChecking, setIsChecking] = useState<boolean>(false)
  const [error, setError] = useState<Error | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const checkHealth = useCallback(async (): Promise<HealthResponse | null> => {
    if (isChecking) {
      return null
    }

    setIsChecking(true)
    setError(null)
    setErrorMessage(null)

    try {
      const res = await getHealth()
      if (res && (res.status === 'healthy' || res.status === 'degraded')) {
        setIsVerified(true)
        setHealthData(res)
        queryClient.setQueryData(['system-health'], res)
        try {
          sessionStorage.setItem(SESSION_STORAGE_GATE_KEY, 'true')
          sessionStorage.setItem(SESSION_STORAGE_DATA_KEY, JSON.stringify(res))
        } catch {
          // Ignore session storage errors
        }
        return res
      } else {
        const msg = `Backend reported unexpected health state: ${res?.status || 'unknown'}`
        setIsVerified(false)
        setHealthData(null)
        setErrorMessage(msg)
        setError(new Error(msg))
        return null
      }
    } catch (err) {
      const parsedError = err instanceof Error ? err : new Error(String(err))
      setIsVerified(false)
      setHealthData(null)
      setError(parsedError)
      setErrorMessage(
        parsedError.message && parsedError.message !== 'Failed to fetch'
          ? parsedError.message
          : 'FastAPI backend server is unreachable at http://127.0.0.1:8000.'
      )
      try {
        sessionStorage.removeItem(SESSION_STORAGE_GATE_KEY)
        sessionStorage.removeItem(SESSION_STORAGE_DATA_KEY)
      } catch {
        // Ignore session storage errors
      }
      return null
    } finally {
      setIsChecking(false)
    }
  }, [isChecking, queryClient])

  const resetGate = useCallback(() => {
    setIsVerified(false)
    setHealthData(null)
    setError(null)
    setErrorMessage(null)
    try {
      sessionStorage.removeItem(SESSION_STORAGE_GATE_KEY)
      sessionStorage.removeItem(SESSION_STORAGE_DATA_KEY)
    } catch {
      // Ignore
    }
  }, [])

  const setVerifiedDirectly = useCallback((verified: boolean, data: HealthResponse | null = null) => {
    setIsVerified(verified)
    setHealthData(data)
    if (verified) {
      try {
        sessionStorage.setItem(SESSION_STORAGE_GATE_KEY, 'true')
        if (data) {
          sessionStorage.setItem(SESSION_STORAGE_DATA_KEY, JSON.stringify(data))
        }
      } catch {
        // Ignore
      }
    } else {
      try {
        sessionStorage.removeItem(SESSION_STORAGE_GATE_KEY)
        sessionStorage.removeItem(SESSION_STORAGE_DATA_KEY)
      } catch {
        // Ignore
      }
    }
  }, [])

  return (
    <HealthGateContext.Provider
      value={{
        isVerified,
        isChecking,
        healthData,
        error,
        errorMessage,
        checkHealth,
        resetGate,
        setVerifiedDirectly,
      }}
    >
      {children}
    </HealthGateContext.Provider>
  )
}

export function useHealthGate() {
  const context = useContext(HealthGateContext)
  if (!context) {
    throw new Error('useHealthGate must be used within a HealthGateProvider')
  }
  return context
}
