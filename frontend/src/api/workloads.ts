import { request } from './client'
import {
  WorkloadCreate,
  WorkloadPriority,
  WorkloadResponse,
  WorkloadStatus,
  WorkloadTransition,
  WorkloadUpdate,
} from '@/types'

export interface ListWorkloadsParams {
  cluster_id?: string
  assigned_node_id?: string
  status?: WorkloadStatus
  priority?: WorkloadPriority
  skip?: number
  limit?: number
}

export async function listWorkloads(
  params?: ListWorkloadsParams,
  signal?: AbortSignal
): Promise<WorkloadResponse[]> {
  return request<WorkloadResponse[]>('/api/v1/workloads/', {
    method: 'GET',
    params: {
      cluster_id: params?.cluster_id,
      assigned_node_id: params?.assigned_node_id,
      status: params?.status,
      priority: params?.priority,
      skip: params?.skip,
      limit: params?.limit,
    },
    signal,
  })
}

export async function getWorkload(
  workloadId: string,
  signal?: AbortSignal
): Promise<WorkloadResponse> {
  return request<WorkloadResponse>(`/api/v1/workloads/${encodeURIComponent(workloadId)}`, {
    method: 'GET',
    signal,
  })
}

export async function createWorkload(
  data: WorkloadCreate,
  signal?: AbortSignal
): Promise<WorkloadResponse> {
  return request<WorkloadResponse>('/api/v1/workloads/', {
    method: 'POST',
    body: data,
    signal,
  })
}

export async function updateWorkload(
  workloadId: string,
  data: WorkloadUpdate,
  signal?: AbortSignal
): Promise<WorkloadResponse> {
  return request<WorkloadResponse>(`/api/v1/workloads/${encodeURIComponent(workloadId)}`, {
    method: 'PUT',
    body: data,
    signal,
  })
}

export async function scheduleWorkload(
  workloadId: string,
  signal?: AbortSignal
): Promise<WorkloadResponse> {
  return request<WorkloadResponse>(
    `/api/v1/workloads/${encodeURIComponent(workloadId)}/schedule`,
    {
      method: 'POST',
      signal,
    }
  )
}

export async function transitionWorkloadStatus(
  workloadId: string,
  data: WorkloadTransition,
  signal?: AbortSignal
): Promise<WorkloadResponse> {
  return request<WorkloadResponse>(
    `/api/v1/workloads/${encodeURIComponent(workloadId)}/status`,
    {
      method: 'POST',
      body: data,
      signal,
    }
  )
}

export async function cancelWorkload(
  workloadId: string,
  signal?: AbortSignal
): Promise<WorkloadResponse> {
  return request<WorkloadResponse>(
    `/api/v1/workloads/${encodeURIComponent(workloadId)}/cancel`,
    {
      method: 'POST',
      signal,
    }
  )
}
