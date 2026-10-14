import { request } from './client'
import {
  AggregatedMetricsSummary,
  TelemetryCreate,
  TelemetryResponse,
} from '@/types'

export async function recordTelemetry(
  nodeId: string,
  data: TelemetryCreate,
  signal?: AbortSignal
): Promise<TelemetryResponse> {
  return request<TelemetryResponse>(
    `/api/v1/telemetry/nodes/${encodeURIComponent(nodeId)}`,
    {
      method: 'POST',
      body: data,
      signal,
    }
  )
}

export async function getNodeTelemetryHistory(
  nodeId: string,
  limit: number = 50,
  signal?: AbortSignal
): Promise<TelemetryResponse[]> {
  return request<TelemetryResponse[]>(
    `/api/v1/telemetry/nodes/${encodeURIComponent(nodeId)}`,
    {
      method: 'GET',
      params: { limit },
      signal,
    }
  )
}

export async function getClusterAggregate(
  clusterId: string,
  signal?: AbortSignal
): Promise<AggregatedMetricsSummary> {
  return request<AggregatedMetricsSummary>(
    `/api/v1/telemetry/clusters/${encodeURIComponent(clusterId)}/aggregate`,
    {
      method: 'GET',
      signal,
    }
  )
}

export async function getNodeHistoryReadiness(
  nodeId: string,
  signal?: AbortSignal
): Promise<import('@/types').NodeHistoryReadiness> {
  return request<import('@/types').NodeHistoryReadiness>(
    `/api/v1/telemetry/nodes/${encodeURIComponent(nodeId)}/readiness`,
    {
      method: 'GET',
      signal,
    }
  )
}

export async function getSimulatorStatus(
  signal?: AbortSignal
): Promise<import('@/types').SimulatorStatus> {
  return request<import('@/types').SimulatorStatus>('/api/v1/telemetry/simulator/status', {
    method: 'GET',
    signal,
  })
}

export async function startSimulator(
  intervalSeconds: number = 60,
  targetNodeId?: string,
  signal?: AbortSignal
): Promise<import('@/types').SimulatorStatus> {
  return request<import('@/types').SimulatorStatus>('/api/v1/telemetry/simulator/start', {
    method: 'POST',
    body: {
      interval_seconds: intervalSeconds,
      target_node_id: targetNodeId || null,
    },
    signal,
  })
}

export async function stopSimulator(
  signal?: AbortSignal
): Promise<import('@/types').SimulatorStatus> {
  return request<import('@/types').SimulatorStatus>('/api/v1/telemetry/simulator/stop', {
    method: 'POST',
    signal,
  })
}
