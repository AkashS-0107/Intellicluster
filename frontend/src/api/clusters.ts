import { request } from './client'
import {
  ClusterCapacitySummary,
  ClusterCreate,
  ClusterResponse,
  ClusterStatus,
  ClusterUpdate,
} from '@/types'

export interface ListClustersParams {
  skip?: number
  limit?: number
  status?: ClusterStatus
}

export async function listClusters(
  params?: ListClustersParams,
  signal?: AbortSignal
): Promise<ClusterResponse[]> {
  return request<ClusterResponse[]>('/api/v1/clusters/', {
    method: 'GET',
    params: {
      skip: params?.skip,
      limit: params?.limit,
      status: params?.status,
    },
    signal,
  })
}

export async function getCluster(
  clusterId: string,
  signal?: AbortSignal
): Promise<ClusterResponse> {
  return request<ClusterResponse>(`/api/v1/clusters/${encodeURIComponent(clusterId)}`, {
    method: 'GET',
    signal,
  })
}

export async function createCluster(
  data: ClusterCreate,
  signal?: AbortSignal
): Promise<ClusterResponse> {
  return request<ClusterResponse>('/api/v1/clusters/', {
    method: 'POST',
    body: data,
    signal,
  })
}

export async function updateCluster(
  clusterId: string,
  data: ClusterUpdate,
  signal?: AbortSignal
): Promise<ClusterResponse> {
  return request<ClusterResponse>(`/api/v1/clusters/${encodeURIComponent(clusterId)}`, {
    method: 'PUT',
    body: data,
    signal,
  })
}

export async function getClusterCapacity(
  clusterId: string,
  signal?: AbortSignal
): Promise<ClusterCapacitySummary> {
  return request<ClusterCapacitySummary>(
    `/api/v1/clusters/${encodeURIComponent(clusterId)}/capacity`,
    {
      method: 'GET',
      signal,
    }
  )
}
