import { request } from './client'
import { HealthResponse } from '@/types'

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request<HealthResponse>('/health', { signal })
}
