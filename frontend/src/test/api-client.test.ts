import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { request, ApiClientError, resolveApiUrl } from '@/api/client'

describe('API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('successfully returns parsed JSON data on 200 OK', async () => {
    const mockData = { id: 'cluster-123', name: 'prod-cluster', status: 'ACTIVE' }
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockData,
    })

    const result = await request<typeof mockData>('/api/v1/clusters/cluster-123')
    expect(result).toEqual(mockData)
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/v1/clusters/cluster-123',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ Accept: 'application/json' }),
      })
    )
  })

  it('handles 204 No Content correctly without JSON parsing error', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
    })

    const result = await request<null>('/api/v1/workloads/w-1/cancel', { method: 'POST' })
    expect(result).toBeNull()
  })

  it('parses FastAPI domain exception format into ApiClientError', async () => {
    const errorBody = {
      error_code: 'NO_AVAILABLE_NODES',
      message: 'No candidate node has sufficient allocatable resources or satisfies SLA constraints.',
      details: { required_cpu: 4.0 },
    }
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => errorBody,
    })

    await expect(request('/api/v1/workloads/w-1/schedule', { method: 'POST' })).rejects.toThrow(
      ApiClientError
    )

    try {
      await request('/api/v1/workloads/w-1/schedule', { method: 'POST' })
    } catch (err) {
      const apiErr = err as ApiClientError
      expect(apiErr.status).toBe(422)
      expect(apiErr.errorCode).toBe('NO_AVAILABLE_NODES')
      expect(apiErr.message).toBe(errorBody.message)
      expect(apiErr.details).toEqual(errorBody)
    }
  })

  it('formats FastAPI validation error details array properly', async () => {
    const errorBody = {
      detail: [
        { loc: ['body', 'hostname'], msg: 'Field required', type: 'missing' },
        { loc: ['body', 'cpu_cores'], msg: 'Input should be greater than 0', type: 'greater_than' },
      ],
    }
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => errorBody,
    })

    try {
      await request('/api/v1/nodes/', { method: 'POST', body: {} })
    } catch (err) {
      const apiErr = err as ApiClientError
      expect(apiErr.status).toBe(422)
      expect(apiErr.errorCode).toBe('VALIDATION_ERROR')
      expect(apiErr.message).toContain('body.hostname: Field required')
      expect(apiErr.message).toContain('body.cpu_cores: Input should be greater than 0')
    }
  })

  it('translates network fetch throws into ApiClientError with NETWORK_FAILURE code', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch'))

    try {
      await request('/health')
    } catch (err) {
      const apiErr = err as ApiClientError
      expect(apiErr.status).toBe(0)
      expect(apiErr.errorCode).toBe('NETWORK_FAILURE')
      expect(apiErr.message).toContain('Backend connection failure')
    }
  })

  describe('API Base URL Resolution', () => {
    const originalEnv = import.meta.env.VITE_API_BASE_URL

    afterEach(() => {
      import.meta.env.VITE_API_BASE_URL = originalEnv
    })

    it('returns relative endpoint when VITE_API_BASE_URL is unset or empty', () => {
      import.meta.env.VITE_API_BASE_URL = ''
      expect(resolveApiUrl('/api/v1/clusters')).toBe('/api/v1/clusters')
      expect(resolveApiUrl('/health', { check: true })).toBe('/health?check=true')
    })

    it('joins configured base URL correctly without duplicate slashes', () => {
      import.meta.env.VITE_API_BASE_URL = 'http://127.0.0.1:8000'
      expect(resolveApiUrl('/api/v1/clusters')).toBe('http://127.0.0.1:8000/api/v1/clusters')

      // Trailing slash on base URL
      import.meta.env.VITE_API_BASE_URL = 'http://api.production.internal:8000/'
      expect(resolveApiUrl('/api/v1/nodes')).toBe('http://api.production.internal:8000/api/v1/nodes')

      // Query parameters
      expect(resolveApiUrl('/api/v1/nodes', { limit: 50, skip: 10 })).toBe(
        'http://api.production.internal:8000/api/v1/nodes?limit=50&skip=10'
      )
    })

    it('request() uses configured base URL when VITE_API_BASE_URL is set', async () => {
      import.meta.env.VITE_API_BASE_URL = 'https://api.intellicluster.io'
      const mockData = { status: 'healthy' }
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockData,
      })

      const res = await request<typeof mockData>('/health')
      expect(res).toEqual(mockData)
      expect(globalThis.fetch).toHaveBeenCalledWith(
        'https://api.intellicluster.io/health',
        expect.anything()
      )
    })
  })
})
