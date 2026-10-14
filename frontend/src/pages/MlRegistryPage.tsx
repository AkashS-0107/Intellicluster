import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input, Select } from '@/components/ui/FormControls'
import {
  Brain,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  Info,
  ChevronDown,
  ArrowRight,
  TrendingUp,
  Play,
  Activity,
  AlertTriangle,
} from 'lucide-react'
import { cn } from '@/utils/cn'
import {
  getMlModels,
  runClusterInference,
  runFailurePrediction,
  runForecasting,
  runAnomalyDetection,
  runDqnComparison,
  ModelCatalogItem,
} from '@/api/ml'

interface ModelSpec {
  id: string
  name: string
  systemRole: string
  architecture: string
  artifactName: string
  endpointPath?: string
  targetFeatures?: string[]
  metrics: { label: string; value: string; note?: string }[]
  caveats: string
  operationalDecision: 'VALIDATED_OFFLINE' | 'REJECTED'
  currentStage: 1 | 2 | 3 | 4
}

const MODELS: ModelSpec[] = [
  {
    id: 'model-1',
    name: 'Model 1: Server Resource Clustering',
    systemRole: 'Workload & Node Profiling',
    architecture: 'K-Means (k=4)',
    artifactName: 'server_clustering_kmeans.joblib',
    endpointPath: '/api/v1/ml/cluster-archetype',
    metrics: [
      { label: 'Optimal Clusters (K)', value: '4' },
      { label: 'Silhouette Score', value: '0.1478', note: 'Weak geometric separation' },
      { label: 'Davies-Bouldin Index', value: '1.9840' },
      { label: 'Seed Stability', value: '100%', note: 'Consistent assignment across seeds' },
    ],
    caveats:
      'Cluster distribution is balanced without singleton anomalies, but low silhouette score indicates overlapping feature densities rather than sharp spatial partitions.',
    operationalDecision: 'VALIDATED_OFFLINE',
    currentStage: 3,
  },
  {
    id: 'model-2a',
    name: 'Model 2A: Hardware Failure Prediction (AI4I)',
    systemRole: 'Predictive Node Maintenance',
    architecture: 'XGBoost Classifier (Stratified 5-Fold)',
    artifactName: 'failure_prediction_ai4i_xgboost.joblib',
    endpointPath: '/api/v1/ml/predict-failure',
    metrics: [
      { label: 'Out-of-Fold ROC-AUC', value: '0.9748' },
      { label: 'Out-of-Fold PR-AUC', value: '0.7281' },
      { label: 'Failure Prevalence', value: '~3.39%' },
      { label: 'Recall', value: '87.32%' },
      { label: 'Precision', value: '38.64%', note: 'Trade-off for early warning' },
    ],
    caveats:
      'High recall ensures capturing the majority of imminent server failures. Lower precision (38.64%) produces false alarms; operational alerts must be weighted accordingly before draining nodes.',
    operationalDecision: 'VALIDATED_OFFLINE',
    currentStage: 3,
  },
  {
    id: 'model-2b',
    name: 'Model 2B: Environmental Failure Prediction',
    systemRole: 'Ambient Telemetry Risk Assessment',
    architecture: 'XGBoost Classifier (Stratified 5-Fold)',
    artifactName: 'failure_prediction_environmental_xgboost.joblib',
    metrics: [
      { label: 'Out-of-Fold ROC-AUC', value: '0.4891', note: 'Approximately random' },
      { label: 'Out-of-Fold PR-AUC', value: '0.1026' },
      { label: 'In-Sample ROC-AUC', value: '0.9990', note: 'Severe memorization/overfit' },
    ],
    caveats:
      'Disqualified for operational deployment. In-sample metrics showed perfect memorization while out-of-fold performance collapsed to random coin-flip parity (ROC-AUC 0.4891).',
    operationalDecision: 'REJECTED',
    currentStage: 1,
  },
  {
    id: 'model-3',
    name: 'Model 3: Temporal Resource Utilization Forecasting',
    systemRole: 'Headroom & Load Forecasting',
    architecture: 'Dual-Layer Stacked LSTM (168h Lookback → 24h Horizon)',
    artifactName: 'resource_forecasting_lstm.pt',
    endpointPath: '/api/v1/ml/forecast-resources',
    targetFeatures: ['cpu_utilization (%)', 'memory_usage (%)', 'workload (tasks)'],
    metrics: [
      { label: 'Holdout MAE', value: '14.81', note: 'vs Naive Persistence 22.59' },
      { label: 'Holdout RMSE', value: '20.24', note: 'vs Naive Persistence 32.54' },
      { label: 'Lookback Window', value: '168 Hours (7 Days)' },
      { label: 'Forecast Horizon', value: '24 Hours (Next Day)' },
    ],
    caveats:
      'Decisively beats naive persistence baseline by >34% MAE reduction. Forecast targets are normalized CPU utilization, memory usage, and concurrent workload count. Telemetry values legitimately peak >100% under saturation.',
    operationalDecision: 'VALIDATED_OFFLINE',
    currentStage: 3,
  },
  {
    id: 'model-4a',
    name: 'Model 4A: Network Anomaly Detection',
    systemRole: 'Network Packet Anomaly Filter',
    architecture: 'Isolation Forest',
    artifactName: 'network_anomaly_iforest.joblib',
    metrics: [
      { label: 'Validation ROC-AUC', value: '0.498', note: 'Near random parity' },
      { label: 'Decision Policy', value: 'REJECTED' },
    ],
    caveats:
      'Rejected for operational use. Unsupervised anomaly scoring showed zero discriminative ability against network intrusion benchmarks.',
    operationalDecision: 'REJECTED',
    currentStage: 1,
  },
  {
    id: 'model-4b',
    name: 'Model 4B: Infrastructure Anomaly Detection',
    systemRole: 'Host Telemetry Outlier Scoring',
    architecture: 'Isolation Forest (Contamination=5%)',
    artifactName: 'infrastructure_anomaly_iforest.joblib',
    endpointPath: '/api/v1/ml/detect-anomaly',
    metrics: [
      { label: 'Contamination', value: '5.0%' },
      { label: 'Extreme Saturation Capture', value: '25.05%' },
      { label: 'Evaluation Baseline', value: 'Contextual Only' },
    ],
    caveats:
      'Captures ~25% of extreme infrastructure saturation events. Provides contextual outlier signals only; must not be used as an autonomous node cordoning trigger.',
    operationalDecision: 'VALIDATED_OFFLINE',
    currentStage: 3,
  },
  {
    id: 'model-5',
    name: 'Model 5: Dynamic Load Balancer & Scheduler',
    systemRole: 'Reinforcement Learning Placement Policy',
    architecture: 'Deep Q-Network (DQN with Experience Replay)',
    artifactName: 'load_balancer_dqn.pt',
    endpointPath: '/api/v1/ml/dqn-placement-recommendation',
    metrics: [
      { label: 'Holdout Reward', value: '+80.88 ± 3.80' },
      { label: 'Placement Success', value: '98.3%' },
      { label: 'Overload / Rejection', value: '1.7%' },
      { label: 'Mean Latency', value: '10.60 ms' },
      { label: 'Evaluated Cost', value: '154.6 CNY', note: 'Heuristic baseline was 138.0 CNY' },
    ],
    caveats:
      'High placement success (98.3%), but the deterministic HeuristicSchedulerStrategy achieved higher cost efficiency (138.0 CNY vs 154.6 CNY). Active FastAPI scheduler remains deterministic heuristic.',
    operationalDecision: 'VALIDATED_OFFLINE',
    currentStage: 3,
  },
]

const READINESS_LEVELS = [
  { level: 1, name: 'Offline Validated Artifact', desc: 'Artifact trained, evaluated, and serialized in ml_models/' },
  { level: 2, name: 'Backend Adapter Implemented', desc: 'BasePredictor interface mounted in Python service layer' },
  { level: 3, name: 'API Inference Endpoint Available', desc: 'HTTP route mounted under /api/v1/ml/ for live inference' },
  { level: 4, name: 'Live Prediction Confirmed', desc: 'End-to-end telemetry driving production placement & scoring' },
]

export function MlRegistryPage() {
  const [filter, setFilter] = useState<'ALL' | 'VALIDATED_OFFLINE' | 'REJECTED'>('ALL')
  const [expandedCaveats, setExpandedCaveats] = useState<Record<string, boolean>>({})

  // Interactive Test Modal State
  const [testingModel, setTestingModel] = useState<ModelSpec | null>(null)
  const [testResult, setTestResult] = useState<any>(null)
  const [testError, setTestError] = useState<string | null>(null)
  const [isTestRunning, setIsTestRunning] = useState(false)

  // Form states for test modal
  const [m1Cores, setM1Cores] = useState('16.0')
  const [m1Ram, setM1Ram] = useState('64.0')
  const [m1Tier, setM1Tier] = useState('Application_Server')

  const [m2AirTemp, setM2AirTemp] = useState('300.0')
  const [m2ProcessTemp, setM2ProcessTemp] = useState('310.0')
  const [m2Rpm, setM2Rpm] = useState('1500.0')
  const [m2Torque, setM2Torque] = useState('40.0')
  const [m2Wear, setM2Wear] = useState('100.0')
  const [m2Type, setM2Type] = useState('L')

  const [m4Cpu, setM4Cpu] = useState('85.0')
  const [m4Mem, setM4Mem] = useState('75.0')
  const [m4Storage, setM4Storage] = useState('60.0')
  const [m4Workload, setM4Workload] = useState('90.0')
  const [m4Alloc, setM4Alloc] = useState('80.0')

  // Live Catalog Query
  const { data: liveCatalog } = useQuery({
    queryKey: ['ml-models'],
    queryFn: ({ signal }) => getMlModels(signal),
    staleTime: 30000,
  })

  const toggleCaveats = (id: string) => {
    setExpandedCaveats((prev) => ({
      ...prev,
      [id]: !(prev[id] ?? true),
    }))
  }

  const filteredModels = MODELS.filter((model) => {
    if (filter === 'ALL') return true
    return model.operationalDecision === filter
  })

  const validatedCount = MODELS.filter((m) => m.operationalDecision === 'VALIDATED_OFFLINE').length
  const rejectedCount = MODELS.filter((m) => m.operationalDecision === 'REJECTED').length

  const handleOpenTestModal = (model: ModelSpec) => {
    setTestingModel(model)
    setTestResult(null)
    setTestError(null)
  }

  const handleExecuteInference = async () => {
    if (!testingModel) return
    setIsTestRunning(true)
    setTestResult(null)
    setTestError(null)

    try {
      if (testingModel.id === 'model-1') {
        const res = await runClusterInference({
          cpu_cores: parseFloat(m1Cores) || 16.0,
          memory_gb: parseFloat(m1Ram) || 64.0,
          vm_instances: 4,
          container_replicas: 12,
          storage_iops: 10000,
          network_bandwidth_mbps: 2500.0,
          cpu_utilization_pct: 50.0,
          memory_utilization_pct: 30.0,
          network_utilization_pct: 40.0,
          disk_utilization_pct: 25.0,
          request_rate_rps: 1500.0,
          load_balancer_capacity: 5000.0,
          application_tier: m1Tier,
        })
        setTestResult(res)
      } else if (testingModel.id === 'model-2a') {
        const res = await runFailurePrediction({
          air_temperature_k: parseFloat(m2AirTemp) || 300.0,
          process_temperature_k: parseFloat(m2ProcessTemp) || 310.0,
          rotational_speed_rpm: parseFloat(m2Rpm) || 1500.0,
          torque_nm: parseFloat(m2Torque) || 40.0,
          tool_wear_min: parseFloat(m2Wear) || 100.0,
          machine_type: m2Type,
        })
        setTestResult(res)
      } else if (testingModel.id === 'model-3') {
        // Run test with representative 168x5 sequence
        const testSeq = Array.from({ length: 168 }, () => [50.0, 45.0, 55.0, 75.0, 60.0])
        const res = await runForecasting(testSeq)
        setTestResult(res)
      } else if (testingModel.id === 'model-4b') {
        const res = await runAnomalyDetection({
          cpu_utilization: parseFloat(m4Cpu) || 85.0,
          memory_usage: parseFloat(m4Mem) || 75.0,
          storage_usage: parseFloat(m4Storage) || 60.0,
          workload: parseFloat(m4Workload) || 90.0,
          resource_allocation: parseFloat(m4Alloc) || 80.0,
        })
        setTestResult(res)
      } else if (testingModel.id === 'model-5') {
        const res = await runDqnComparison({
          state_vector: Array.from({ length: 25 }, () => 0.5),
        })
        setTestResult(res)
      }
    } catch (err: any) {
      setTestError(err.message || 'Inference execution failed')
    } finally {
      setIsTestRunning(false)
    }
  }

  // Get live catalog metadata if loaded
  const catalogMap = new Map<string, ModelCatalogItem>()
  if (liveCatalog?.models) {
    for (const m of liveCatalog.models) {
      catalogMap.set(m.model_id, m)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Advisory Banner */}
      <div className="rounded-xl border border-[#DCE2ED] bg-white p-5 text-xs text-[#475467] shadow-sm flex items-start gap-3">
        <Info className="w-5 h-5 text-[#244DE8] shrink-0 mt-0.5" />
        <div className="space-y-1">
          <strong className="text-[#101828] text-sm font-semibold">Scientific Model Governance & Integration Baseline</strong>
          <p className="leading-relaxed text-[#475467]">
            This registry catalogs the empirical evaluation benchmarks from offline ML validation (Step 3C & Step 4).
            All models currently reside as serialized artifacts in the <code className="font-mono text-[#244DE8] bg-[#E8EEFF] px-1 py-0.5 rounded text-[11px]">ml_models/</code> directory.
            <strong> Live ML inference endpoints are mounted on FastAPI under <code className="font-mono text-[#244DE8] bg-[#E8EEFF] px-1 py-0.5 rounded text-[11px]">/api/v1/ml/</code></strong> for eligible models.
            Production cluster scheduling remains deterministically handled by <code className="font-mono text-[#244DE8] bg-[#E8EEFF] px-1 py-0.5 rounded text-[11px]">HeuristicSchedulerStrategy</code>.
          </p>
          <div className="pt-2 flex items-center gap-4">
            <Link
              to="/workloads"
              className="inline-flex items-center gap-1.5 text-xs text-[#244DE8] hover:underline font-mono font-medium"
            >
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Inspect active Heuristic Workload Scheduler</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* 4-Tier Readiness Classification Architecture */}
      <Card>
        <CardHeader>
          <CardTitle>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#244DE8]" />
              <span>4-Tier Operational Readiness Lifecycle</span>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {READINESS_LEVELS.map((lvl) => {
              const isMounted = lvl.level <= 3
              return (
                <div
                  key={lvl.level}
                  className={`p-3.5 rounded-xl border font-mono text-xs ${
                    isMounted
                      ? 'border-[#A6F4C5] bg-[#ECFDF3] text-[#027A48]'
                      : 'border-[#DCE2ED] bg-[#F5F7FB] text-[#667085]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs">TIER {lvl.level}</span>
                    {isMounted ? (
                      <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-[#027A48] text-white">
                        {lvl.level === 3 ? 'ACTIVE MOUNT' : 'BASELINE'}
                      </span>
                    ) : (
                      <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-white text-[#667085] border border-[#DCE2ED]">
                        PENDING
                      </span>
                    )}
                  </div>
                  <div className="font-semibold text-[#101828] mt-2 font-sans">{lvl.name}</div>
                  <div className="text-[11px] text-[#475467] mt-1 font-sans leading-normal">
                    {lvl.desc}
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Models Inventory Section with Interactive Filter Tabs */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#101828] font-mono flex items-center gap-2">
            <Brain className="w-4 h-4 text-[#244DE8]" />
            <span>Offline Model Validation Audit ({filteredModels.length} of {MODELS.length} Models)</span>
          </h2>

          {/* Interactive Filter Tabs */}
          <div className="flex items-center gap-1.5 bg-[#F5F7FB] p-1 rounded-xl border border-[#DCE2ED] text-xs font-mono">
            <button
              type="button"
              onClick={() => setFilter('ALL')}
              className={cn(
                'px-3 py-1.5 rounded-lg transition-all',
                filter === 'ALL'
                  ? 'bg-white text-[#244DE8] font-semibold border border-[#DCE2ED] shadow-sm'
                  : 'text-[#667085] hover:text-[#101828]'
              )}
            >
              All ({MODELS.length})
            </button>
            <button
              type="button"
              onClick={() => setFilter('VALIDATED_OFFLINE')}
              className={cn(
                'px-3 py-1.5 rounded-lg transition-all',
                filter === 'VALIDATED_OFFLINE'
                  ? 'bg-[#ECFDF3] text-[#027A48] font-semibold border border-[#A6F4C5] shadow-sm'
                  : 'text-[#667085] hover:text-[#027A48]'
              )}
            >
              Validated ({validatedCount})
            </button>
            <button
              type="button"
              onClick={() => setFilter('REJECTED')}
              className={cn(
                'px-3 py-1.5 rounded-lg transition-all',
                filter === 'REJECTED'
                  ? 'bg-[#FEF3F2] text-[#B42318] font-semibold border border-[#FECDCA] shadow-sm'
                  : 'text-[#667085] hover:text-[#B42318]'
              )}
            >
              Rejected / Disqualified ({rejectedCount})
            </button>
          </div>
        </div>

        {/* Model Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredModels.map((model) => {
            const isRejected = model.operationalDecision === 'REJECTED'
            const isCaveatExpanded = expandedCaveats[model.id] ?? true
            const catalogItem = catalogMap.get(model.id)
            const isReadyOnApi = catalogItem?.operational_status === 'READY' || catalogItem?.operational_status === 'EXPERIMENTAL'

            return (
              <Card
                key={model.id}
                className={isRejected ? 'border-[#FECDCA] bg-[#FEF3F2]/20' : ''}
              >
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <CardTitle>
                        <span className="text-sm font-semibold text-[#101828] font-sans">{model.name}</span>
                      </CardTitle>
                      <div className="text-xs font-mono text-[#667085] mt-1">
                        {model.systemRole} // <span className="text-[#475467]">{model.architecture}</span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1.5">
                      {isRejected ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA]">
                          <XCircle className="w-3.5 h-3.5" /> REJECTED
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold bg-[#E8EEFF] text-[#244DE8] border border-[#C5D5FA]">
                          <CheckCircle2 className="w-3.5 h-3.5" /> OFFLINE ARTIFACT
                        </span>
                      )}

                      {/* Live API Mounted Badge */}
                      {isReadyOnApi && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-[#ECFDF3] text-[#027A48] border border-[#A6F4C5]">
                          API MOUNTED
                        </span>
                      )}
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4 text-xs font-mono">
                  {/* Artifact File info & Endpoint */}
                  <div className="space-y-1.5 p-2.5 rounded-lg bg-[#F5F7FB] border border-[#DCE2ED] text-[11px]">
                    <div className="flex items-center justify-between">
                      <span className="text-[#667085] font-semibold">ARTIFACT PATH:</span>
                      <span className="text-[#244DE8] font-bold">{model.artifactName}</span>
                    </div>
                    {model.endpointPath && (
                      <div className="flex items-center justify-between pt-1 border-t border-[#EAEFF7]">
                        <span className="text-[#667085] font-semibold">LIVE ROUTE:</span>
                        <code className="text-[#027A48] font-mono font-bold">{model.endpointPath}</code>
                      </div>
                    )}
                  </div>

                  {/* Target features if specified */}
                  {model.targetFeatures && (
                    <div className="flex items-center justify-between text-[11px] text-[#667085]">
                      <span>FORECAST TARGETS:</span>
                      <span className="text-[#101828] font-medium">{model.targetFeatures.join(', ')}</span>
                    </div>
                  )}

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {model.metrics.map((m, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-[#F5F7FB] border border-[#DCE2ED]"
                      >
                        <div className="text-[10px] text-[#667085] font-semibold uppercase tracking-wider truncate" title={m.label}>
                          {m.label}
                        </div>
                        <div className="text-sm font-bold text-[#101828] mt-0.5">{m.value}</div>
                        {m.note && (
                          <div className="text-[10px] text-[#475467] mt-0.5 leading-tight">{m.note}</div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Caveats / Empirical Findings with Toggle */}
                  <div className="rounded-lg bg-[#F5F7FB] border border-[#DCE2ED] overflow-hidden font-sans">
                    <button
                      type="button"
                      onClick={() => toggleCaveats(model.id)}
                      className="w-full flex items-center justify-between p-3 text-xs text-[#475467] hover:text-[#101828] hover:bg-[#EAEFF7]/50 transition-colors"
                      aria-expanded={isCaveatExpanded}
                    >
                      <strong className="font-mono text-[11px] uppercase tracking-wide text-[#101828]">
                        Scientific Finding & Operational Caveat:
                      </strong>
                      <ChevronDown
                        className={cn(
                          'w-3.5 h-3.5 text-[#667085] transition-transform duration-200',
                          isCaveatExpanded ? 'rotate-0' : '-rotate-90'
                        )}
                      />
                    </button>
                    {isCaveatExpanded && (
                      <div className="p-3 pt-2 text-xs text-[#475467] leading-relaxed border-t border-[#DCE2ED] bg-white">
                        {model.caveats}
                      </div>
                    )}
                  </div>

                  {/* Action / Test Inference Button */}
                  <div className="flex items-center justify-between pt-1">
                    <div className="text-[11px] font-mono text-[#667085]">
                      STATUS: {isRejected ? 'QUARANTINED' : 'INFERENCE READY'}
                    </div>
                    {isRejected ? (
                      <Button
                        size="xs"
                        variant="outline"
                        disabled
                        className="opacity-60 cursor-not-allowed text-[#B42318] border-[#FECDCA] bg-[#FEF3F2]"
                        title="Model disqualified due to validation failure. Production inference disabled."
                      >
                        <XCircle className="w-3.5 h-3.5 mr-1" />
                        Quarantined
                      </Button>
                    ) : (
                      <Button
                        size="xs"
                        variant="primary"
                        onClick={() => handleOpenTestModal(model)}
                        className="bg-[#244DE8] hover:bg-[#1D3EC4] text-white"
                      >
                        <Play className="w-3 h-3 mr-1" />
                        Test Live Inference
                      </Button>
                    )}
                  </div>

                  {/* Readiness Progress Bar */}
                  <div className="pt-2 border-t border-[#DCE2ED]">
                    <div className="flex justify-between items-center text-[10px] text-[#667085] mb-1.5">
                      <span className="font-semibold">INTEGRATION READINESS:</span>
                      <span className="text-[#101828] font-medium">
                        Tier {model.currentStage} of 4 ({isRejected ? 'Disqualified' : 'Offline Verified'})
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-[#EAEFF7] overflow-hidden border border-[#DCE2ED]">
                      <div
                        className={`h-full ${isRejected ? 'bg-[#D92D20]' : 'bg-[#244DE8]'}`}
                        style={{ width: `${(model.currentStage / 4) * 100}%` }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Interactive Inference Modal */}
      {testingModel && (
        <Modal
          isOpen={!!testingModel}
          onClose={() => setTestingModel(null)}
          title={`Test Inference: ${testingModel.name}`}
          maxWidth="lg"
        >
          <div className="space-y-4 text-xs font-mono">
            <div className="p-3 rounded-lg bg-[#F5F7FB] border border-[#DCE2ED] text-[#475467] leading-relaxed">
              <span className="font-bold text-[#101828]">Target Endpoint:</span>{' '}
              <code className="text-[#244DE8] font-mono">{testingModel.endpointPath}</code>
              <p className="mt-1 text-[11px]">{testingModel.systemRole} &bull; Algorithm: {testingModel.architecture}</p>
            </div>

            {/* Model 1: KMeans Form */}
            {testingModel.id === 'model-1' && (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="CPU Cores"
                    type="number"
                    value={m1Cores}
                    onChange={(e) => setM1Cores(e.target.value)}
                  />
                  <Input
                    label="RAM (GB)"
                    type="number"
                    value={m1Ram}
                    onChange={(e) => setM1Ram(e.target.value)}
                  />
                </div>
                <Select
                  label="Application Tier"
                  value={m1Tier}
                  onChange={(e) => setM1Tier(e.target.value)}
                >
                  <option value="Application_Server">Application_Server</option>
                  <option value="Database">Database</option>
                  <option value="Frontend">Frontend</option>
                  <option value="Cache">Cache</option>
                </Select>
              </div>
            )}

            {/* Model 2A: AI4I Form */}
            {testingModel.id === 'model-2a' && (
              <div className="space-y-3">
                <div className="p-2.5 rounded-lg bg-[#FFFAEB] border border-[#FEDF89] text-[#B54708] text-[11px]">
                  <AlertTriangle className="w-3.5 h-3.5 inline mr-1" />
                  <strong>Domain Notice:</strong> This model operates strictly on industrial milling sensors (temperatures, RPM, torque, tool wear), not server OS metrics.
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Air Temperature (K)"
                    type="number"
                    value={m2AirTemp}
                    onChange={(e) => setM2AirTemp(e.target.value)}
                  />
                  <Input
                    label="Process Temperature (K)"
                    type="number"
                    value={m2ProcessTemp}
                    onChange={(e) => setM2ProcessTemp(e.target.value)}
                  />
                  <Input
                    label="Rotational Speed (RPM)"
                    type="number"
                    value={m2Rpm}
                    onChange={(e) => setM2Rpm(e.target.value)}
                  />
                  <Input
                    label="Torque (Nm)"
                    type="number"
                    value={m2Torque}
                    onChange={(e) => setM2Torque(e.target.value)}
                  />
                  <Input
                    label="Tool Wear (min)"
                    type="number"
                    value={m2Wear}
                    onChange={(e) => setM2Wear(e.target.value)}
                  />
                  <Select
                    label="Variant Type"
                    value={m2Type}
                    onChange={(e) => setM2Type(e.target.value)}
                  >
                    <option value="L">L (Low Quality Variant)</option>
                    <option value="M">M (Medium Variant)</option>
                    <option value="H">H (High Quality Variant)</option>
                  </Select>
                </div>
              </div>
            )}

            {/* Model 3: LSTM Info */}
            {testingModel.id === 'model-3' && (
              <div className="p-3 rounded-lg bg-[#F5F7FB] border border-[#DCE2ED] text-[11px] text-[#475467] leading-relaxed">
                <Activity className="w-4 h-4 text-[#244DE8] mb-1" />
                Clicking Execute will submit a validated 168-hour (7 days) baseline telemetry window to evaluate the 24-hour horizon forward pass for CPU, RAM, and Workload.
              </div>
            )}

            {/* Model 4B: Infra Anomaly Form */}
            {testingModel.id === 'model-4b' && (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="CPU Utilization (%)"
                    type="number"
                    value={m4Cpu}
                    onChange={(e) => setM4Cpu(e.target.value)}
                  />
                  <Input
                    label="Memory Usage (MB)"
                    type="number"
                    value={m4Mem}
                    onChange={(e) => setM4Mem(e.target.value)}
                  />
                  <Input
                    label="Storage Usage (GB)"
                    type="number"
                    value={m4Storage}
                    onChange={(e) => setM4Storage(e.target.value)}
                  />
                  <Input
                    label="Workload Metric"
                    type="number"
                    value={m4Workload}
                    onChange={(e) => setM4Workload(e.target.value)}
                  />
                </div>
                <Input
                  label="Resource Allocation"
                  type="number"
                  value={m4Alloc}
                  onChange={(e) => setM4Alloc(e.target.value)}
                />
              </div>
            )}

            {/* Model 5: DQN Form */}
            {testingModel.id === 'model-5' && (
              <div className="p-3 rounded-lg bg-[#F5F7FB] border border-[#DCE2ED] text-[11px] text-[#475467] leading-relaxed">
                <Info className="w-4 h-4 text-[#244DE8] mb-1" />
                Clicking Execute will run the DQN QNetwork on a 25-dimensional task and candidate node state vector. This recommendation is <strong>read-only</strong> and will not mutate any database state.
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end gap-2 pt-2 border-t border-[#DCE2ED]">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setTestingModel(null)}
              >
                Close
              </Button>
              <Button
                size="sm"
                variant="primary"
                onClick={handleExecuteInference}
                isLoading={isTestRunning}
                className="bg-[#244DE8] text-white"
              >
                Execute Live Inference
              </Button>
            </div>

            {/* Error Display */}
            {testError && (
              <div className="p-3 rounded-lg bg-[#FEF3F2] border border-[#FECDCA] text-[#B42318] text-xs">
                <strong>Execution Error:</strong> {testError}
              </div>
            )}

            {/* Result Display */}
            {testResult && (
              <div className="mt-4 space-y-2">
                <div className="text-xs font-bold text-[#027A48] flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> Live Backend Response:
                </div>
                <pre className="p-3 rounded-lg bg-[#101828] text-[#A6F4C5] font-mono text-[11px] overflow-auto max-h-60 border border-[#244DE8]/30">
                  {JSON.stringify(testResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  )
}
