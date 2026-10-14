import '@testing-library/jest-dom'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Automatically clean up React DOM after each test
afterEach(() => {
  cleanup()
})

// Mock window.ResizeObserver which is not implemented in jsdom (required by Recharts)
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver = ResizeObserverMock as any
