/**
 * IntelliCluster Domain Types and Schema Contracts
 * Mapped 1:1 with backend Pydantic models and core constants.
 */

export type ClusterStatus = 'ACTIVE' | 'DEGRADED' | 'MAINTENANCE' | 'OFFLINE'

export interface ClusterResponse {
  id: string
  name: string
  description?: string | null
  status: ClusterStatus
  created_at: string
  updated_at: string
}

export interface ClusterCreate {
  name: string
  description?: string | null
  status?: ClusterStatus
}

export interface ClusterUpdate {
  name?: string | null
  description?: string | null
  status?: ClusterStatus | null
}

export interface ClusterCapacitySummary {
  cluster_id: string
  cluster_name: string
  total_nodes: number
  ready_nodes: number
  total_cpu_cores: number
  allocated_cpu_cores: number
  allocatable_cpu_cores: number
  total_memory_mb: number
  allocated_memory_mb: number
  allocatable_memory_mb: number
  average_cpu_usage_pct: number
  average_memory_usage_pct: number
  active_workload_count: number
}

export type NodeStatus =
  | 'INITIALIZING'
  | 'READY'
  | 'BUSY'
  | 'DEGRADED'
  | 'UNREACHABLE'
  | 'DRAINING'
  | 'OFFLINE'

export interface NodeResponse {
  id: string
  cluster_id?: string | null
  hostname: string
  ip_address?: string | null
  status: NodeStatus

  // Hardware Capacities
  cpu_cores: number
  memory_mb: number
  storage_gb: number
  network_bandwidth_mbps: number

  // Dynamic / Cached Metrics
  current_cpu_usage_pct: number
  current_memory_usage_mb: number
  current_disk_usage_gb: number
  current_network_tx_mbps: number
  current_network_rx_mbps: number
  current_network_latency_ms: number
  active_connections: number

  // Health & Scoring
  health_score: number
  risk_score: number

  // Operational Status
  active_workload_count: number
  last_heartbeat: string
  is_cordoned: boolean

  created_at: string
  updated_at: string
}

export interface NodeRegister {
  hostname: string
  ip_address?: string | null
  cluster_id?: string | null
  cpu_cores: number
  memory_mb: number
  storage_gb?: number
  network_bandwidth_mbps?: number
}

export interface NodeUpdate {
  hostname?: string | null
  ip_address?: string | null
  cluster_id?: string | null
  status?: NodeStatus | null
  is_cordoned?: boolean | null
}

export interface NodeCapacitySummary {
  node_id: string
  hostname: string
  status: NodeStatus
  is_cordoned: boolean
  is_allocatable: boolean
  total_cpu_cores: number
  allocated_cpu_cores: number
  allocatable_cpu_cores: number
  total_memory_mb: number
  allocated_memory_mb: number
  allocatable_memory_mb: number
  active_workload_count: number
  health_score: number
}

export type WorkloadStatus =
  | 'PENDING'
  | 'SCHEDULED'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'

export type WorkloadPriority = 'LOW' | 'NORMAL' | 'HIGH' | 'CRITICAL'

export type WorkloadType =
  | 'BATCH'
  | 'REALTIME_API'
  | 'ML_TRAINING'
  | 'BACKGROUND_JOB'
  | 'DATA_PROCESSING'

export interface WorkloadResponse {
  id: string
  cluster_id?: string | null
  assigned_node_id?: string | null
  name: string
  workload_type: WorkloadType

  // Demands
  cpu_cores_requested: number
  memory_mb_requested: number
  storage_gb_requested: number
  network_mbps_requested: number
  max_latency_tolerance_ms?: number | null
  estimated_duration_sec?: number | null

  // Priority & Status
  priority: WorkloadPriority
  status: WorkloadStatus
  failure_reason?: string | null
  retry_count: number
  max_retries: number

  // Timestamps
  created_at: string
  scheduled_at?: string | null
  started_at?: string | null
  completed_at?: string | null
  updated_at: string
}

export interface WorkloadCreate {
  name: string
  cluster_id?: string | null
  workload_type?: WorkloadType
  cpu_cores_requested: number
  memory_mb_requested: number
  storage_gb_requested?: number
  network_mbps_requested?: number
  max_latency_tolerance_ms?: number | null
  estimated_duration_sec?: number | null
  priority?: WorkloadPriority
  max_retries?: number
}

export interface WorkloadUpdate {
  name?: string | null
  assigned_node_id?: string | null
  priority?: WorkloadPriority | null
  max_retries?: number | null
}

export interface WorkloadTransition {
  target_status: WorkloadStatus
  failure_reason?: string | null
}

export interface TelemetryCreate {
  cpu_usage_pct: number
  memory_usage_mb: number
  memory_usage_pct: number
  disk_usage_gb: number
  disk_usage_pct: number
  network_rx_mbps: number
  network_tx_mbps: number
  network_latency_ms: number
  active_connections?: number
  running_processes?: number | null
  temperature_celsius?: number | null
  reported_status?: NodeStatus
  workload?: number | null
  resource_allocation?: number | null
}

export interface TelemetryResponse {
  id: string
  node_id: string
  recorded_at: string
  cpu_usage_pct: number
  memory_usage_mb: number
  memory_usage_pct: number
  disk_usage_gb: number
  disk_usage_pct: number
  network_rx_mbps: number
  network_tx_mbps: number
  network_latency_ms: number
  active_connections: number
  running_processes?: number | null
  temperature_celsius?: number | null
  reported_status: NodeStatus
  workload?: number | null
  resource_allocation?: number | null
}

export interface AggregatedMetricsSummary {
  cluster_id?: string | null
  total_reporting_nodes: number
  avg_cpu_usage_pct: number
  max_cpu_usage_pct: number
  avg_memory_usage_pct: number
  max_memory_usage_pct: number
  avg_latency_ms: number
  total_active_connections: number
  recorded_at: string
}

export interface NodeHistoryReadiness {
  node_id: string
  is_ready: boolean
  valid_hourly_observations: number
  required_observations: number
  readiness_percentage: number
  total_raw_snapshots: number
  earliest_usable_timestamp?: string | null
  latest_usable_timestamp?: string | null
  missing_intervals_count: number
  missing_ranges: string[]
  validation_reason: string
  estimated_hours_remaining: number
  collector_active: boolean
  is_simulated: boolean
  feature_readiness: Record<string, boolean>
}

export interface SimulatorStatus {
  is_running: boolean
  interval_seconds: number
  target_node_id?: string | null
  snapshots_emitted: number
  started_at?: string | null
  collector_mode: string
}

export interface OfflineEvaluationResponse {
  dataset_name: string
  dataset_total_records: number
  evaluation_range: string
  forecast_horizon_hours: number
  lookback_window_hours: number
  target_variables: string[]
  input_features_used: string[]
  predictions: Array<{
    step_hour: number
    predicted_cpu_utilization: number
    predicted_memory_usage: number
    predicted_workload: number
  }>
  is_offline_benchmark: boolean
  advisory: string
  strategy_used: string
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | string
  app_name: string
  environment: string
  version: string
  database: string
  timestamp: string
  step: string
}

export interface ApiErrorDetail {
  errorCode?: string
  message: string
  details?: Record<string, unknown> | unknown[]
  status: number
}
