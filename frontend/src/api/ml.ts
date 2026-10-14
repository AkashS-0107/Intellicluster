import { request } from './client'

export type ModelOperationalStatus =
  | 'READY'
  | 'REJECTED'
  | 'EXPERIMENTAL'
  | 'ERROR'
  | 'UNAVAILABLE'

export interface ModelCatalogItem {
  model_id: string
  name: string
  system_role: string
  algorithm: string
  artifact_files: string[]
  operational_status: ModelOperationalStatus
  is_inference_enabled: boolean
  rejection_reason?: string | null
  capabilities: string[]
  limitations?: string | null
  verified_metrics: Record<string, any>
  schema_contract?: string | null
  is_loaded: boolean
  load_error?: string | null
}

export interface ModelCatalogResponse {
  total_models: number
  models: ModelCatalogItem[]
}

export interface KMeansInferenceRequest {
  cpu_cores: number
  memory_gb: number
  vm_instances: number
  container_replicas: number
  storage_iops: number
  network_bandwidth_mbps: number
  cpu_utilization_pct: number
  memory_utilization_pct: number
  network_utilization_pct: number
  disk_utilization_pct: number
  request_rate_rps: number
  load_balancer_capacity: number
  application_tier: string
}

export interface KMeansInferenceResponse {
  predicted_cluster: number
  archetype_name: string
  archetype_profile: Record<string, any>
  transformed_feature_dim: number
  strategy_used: string
}

export interface AI4IInferenceRequest {
  air_temperature_k: number
  process_temperature_k: number
  rotational_speed_rpm: number
  torque_nm: number
  tool_wear_min: number
  machine_type: string
}

export interface AI4IInferenceResponse {
  failure_probability: number
  predicted_class: number
  threshold_used: number
  risk_level: string
  domain_advisory: string
  strategy_used: string
}

export interface ForecastStep {
  step_hour: number
  predicted_cpu_utilization: number
  predicted_memory_usage: number
  predicted_workload: number
}

export interface LSTMForecastingResponse {
  forecast_horizon_hours: number
  lookback_window_hours: number
  target_variables: string[]
  input_features_used: string[]
  predictions: ForecastStep[]
  historical_snapshots_evaluated: number
  node_id?: string | null
  strategy_used: string
}

export interface InfrastructureAnomalyRequest {
  cpu_utilization: number
  memory_usage: number
  storage_usage: number
  workload: number
  resource_allocation: number
}

export interface InfrastructureAnomalyResponse {
  anomaly_score: number
  is_anomaly: boolean
  contamination_rate: number
  advisory: string
  strategy_used: string
}

export interface DQNPlacementRequest {
  state_vector?: number[]
  workload_id?: string
  candidate_node_ids?: string[]
}

export interface DQNPlacementResponse {
  recommended_action: number
  recommended_archetype_name: string
  archetype_profile: Record<string, any>
  q_values: number[]
  confidence_score: number
  is_state_mutated: boolean
  active_scheduler_policy: string
  heuristic_comparison?: Record<string, any> | null
  strategy_used: string
}

export async function getMlModels(signal?: AbortSignal): Promise<ModelCatalogResponse> {
  return request<ModelCatalogResponse>('/api/v1/ml/models', {
    method: 'GET',
    signal,
  })
}

export async function runClusterInference(
  data: KMeansInferenceRequest,
  signal?: AbortSignal
): Promise<KMeansInferenceResponse> {
  return request<KMeansInferenceResponse>('/api/v1/ml/cluster-archetype', {
    method: 'POST',
    body: data,
    signal,
  })
}

export async function runFailurePrediction(
  data: AI4IInferenceRequest,
  signal?: AbortSignal
): Promise<AI4IInferenceResponse> {
  return request<AI4IInferenceResponse>('/api/v1/ml/predict-failure', {
    method: 'POST',
    body: data,
    signal,
  })
}

export async function runForecasting(
  sequence: number[][],
  signal?: AbortSignal
): Promise<LSTMForecastingResponse> {
  return request<LSTMForecastingResponse>('/api/v1/ml/forecast-resources', {
    method: 'POST',
    body: { sequence },
    signal,
  })
}

export async function runNodeForecasting(
  nodeId: string,
  signal?: AbortSignal
): Promise<LSTMForecastingResponse> {
  return request<LSTMForecastingResponse>(
    `/api/v1/ml/forecast-node/${encodeURIComponent(nodeId)}`,
    {
      method: 'POST',
      signal,
    }
  )
}

export async function runAnomalyDetection(
  data: InfrastructureAnomalyRequest,
  signal?: AbortSignal
): Promise<InfrastructureAnomalyResponse> {
  return request<InfrastructureAnomalyResponse>('/api/v1/ml/detect-anomaly', {
    method: 'POST',
    body: data,
    signal,
  })
}

export async function runDqnComparison(
  data: DQNPlacementRequest,
  signal?: AbortSignal
): Promise<DQNPlacementResponse> {
  return request<DQNPlacementResponse>('/api/v1/ml/dqn-placement-recommendation', {
    method: 'POST',
    body: data,
    signal,
  })
}

export async function runGenericInfer(
  modelId: string,
  signal?: AbortSignal
): Promise<{ message: string }> {
  return request<{ message: string }>(
    `/api/v1/ml/models/${encodeURIComponent(modelId)}/infer`,
    {
      method: 'POST',
      signal,
    }
  )
}

export async function runOfflineEvaluation(
  startHourIndex: number = 0,
  signal?: AbortSignal
): Promise<import('@/types').OfflineEvaluationResponse> {
  return request<import('@/types').OfflineEvaluationResponse>(
    '/api/v1/ml/offline-evaluation',
    {
      method: 'POST',
      body: { start_hour_index: startHourIndex },
      signal,
    }
  )
}
