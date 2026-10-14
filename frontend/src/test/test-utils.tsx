import React from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { HealthGateProvider } from '@/context/HealthGateContext'

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

interface WrapperProps {
  children: React.ReactNode
}

export function renderWithProviders(
  ui: React.ReactElement,
  {
    initialEntries = ['/'],
    queryClient = createTestQueryClient(),
    initialVerified = true,
    ...renderOptions
  }: {
    initialEntries?: string[]
    queryClient?: QueryClient
    initialVerified?: boolean
  } & Omit<RenderOptions, 'wrapper'> = {}
) {
  function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        <HealthGateProvider initialVerified={initialVerified}>
          <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
        </HealthGateProvider>
      </QueryClientProvider>
    )
  }

  return {
    queryClient,
    ...render(ui, { wrapper: Wrapper as React.ComponentType, ...renderOptions }),
  }
}
