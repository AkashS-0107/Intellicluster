import { request } from './client'
import {
  NodeCapacitySummary,
  NodeRegister,
  NodeResponse,
  NodeStatus,
  NodeUpdate,
  TelemetryCreate,
} from '@/types'

export interface ListNodesParams {
  cluster_id?: string
  status?: NodeStatus
  skip?: number
  limit?: number
}

export async function listNodes(
  params?: ListNodesParams,
  signal?: AbortSignal
): Promise<NodeResponse[]> {
  return request<NodeResponse[]>('/api/v1/nodes/', {
    method: 'GET',
    params: {
      cluster_id: params?.cluster_id,
      status: params?.status,
      skip: params?.skip,
      limit: params?.limit,
    },
    signal,
  })
}

export async function getNode(
  nodeId: string,
  signal?: AbortSignal
): Promise<NodeResponse> {
  return request<NodeResponse>(`/api/v1/nodes/${encodeURIComponent(nodeId)}`, {
    method: 'GET',
    signal,
  })
}

export async function registerNode(
  data: NodeRegister,
  signal?: AbortSignal
): Promise<NodeResponse> {
  return request<NodeResponse>('/api/v1/nodes/', {
    method: 'POST',
    body: data,
    signal,
  })
}

export async function updateNode(
  nodeId: string,
  data: NodeUpdate,
  signal?: AbortSignal
): Promise<NodeResponse> {
  return request<NodeResponse>(`/api/v1/nodes/${encodeURIComponent(nodeId)}`, {
    method: 'PUT',
    body: data,
    signal,
  })
}

export async function cordonNode(
  nodeId: string,
  signal?: AbortSignal
): Promise<NodeResponse> {
  return request<NodeResponse>(`/api/v1/nodes/${encodeURIComponent(nodeId)}/cordon`, {
    method: 'POST',
    signal,
  })
}

export async function uncordonNode(
  nodeId: string,
  signal?: AbortSignal
): Promise<NodeResponse> {
  return request<NodeResponse>(`/api/v1/nodes/${encodeURIComponent(nodeId)}/uncordon`, {
    method: 'POST',
    signal,
  })
}

export async function getNodeCapacity(
  nodeId: string,
  signal?: AbortSignal
): Promise<NodeCapacitySummary> {
  return request<NodeCapacitySummary>(
    `/api/v1/nodes/${encodeURIComponent(nodeId)}/capacity`,
    {
      method: 'GET',
      signal,
    }
  )
}

export async function sendNodeHeartbeat(
  nodeId: string,
  data: TelemetryCreate,
  signal?: AbortSignal
): Promise<NodeResponse> {
  return request<NodeResponse>(
    `/api/v1/nodes/${encodeURIComponent(nodeId)}/heartbeat`,
    {
      method: 'POST',
      body: data,
      signal,
    }
  )
}
