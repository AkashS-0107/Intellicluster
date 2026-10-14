# IntelliCluster: ML-Driven Cloud Server Clustering & Workload Orchestration

## Overview
**IntelliCluster** is an intelligent cloud server clustering and workload orchestration system. The platform manages compute nodes, monitors time-series hardware telemetry, and orchestrates workload scheduling. Production scheduling uses a reliable, deterministic heuristic baseline (`HeuristicSchedulerStrategy`), complemented by empirical machine learning models for clustering, failure risk prediction, temporal forecasting, contextual anomaly detection, and reinforcement learning load balancing evaluation.

---

## Architecture & Directory Layout

```text
INTELLICLUSTER/
├── intellicluster/                    # Application package
│   ├── main.py                        # FastAPI entry point, CORS middleware, lifespan
│   ├── api/                           # Presentation layer
│   │   ├── exception_handlers.py      # HTTP error mapping (403, 404, 422, 503)
│   │   └── v1/                        # API v1 routers
│   │       ├── router.py              # Root router mounting clusters, nodes, workloads, telemetry, ml
│   │       ├── clusters.py            # /api/v1/clusters
│   │       ├── nodes.py               # /api/v1/nodes
│   │       ├── workloads.py           # /api/v1/workloads (Production Heuristic Scheduler)
│   │       ├── telemetry.py           # /api/v1/telemetry
│   │       └── ml.py                  # /api/v1/ml (Dedicated ML Inference & Catalog Router)
│   ├── core/                          # Constants, config (CORS_ORIGINS), domain exceptions, logging
│   ├── db/                            # SQLite WAL session & connection engine
│   ├── models/                        # SQLAlchemy 2.x ORM entities (Cluster, Node, Workload, TelemetrySnapshot)
│   ├── schemas/                       # Pydantic v2 DTOs (clusters, nodes, workloads, telemetry, ml)
│   ├── services/                      # ClusterService, NodeService, WorkloadService, TelemetryService
│   ├── ml/                            # ML Operational Runtime & Manifest
│   │   ├── architectures.py           # PyTorch modules (ResourceLSTM, QNetwork)
│   │   ├── manifest.py                # Read-only SHA-256 artifact integrity manifest & CLI
│   │   ├── registry.py                # Cached MLModelRegistry with security boundaries & quarantine
│   │   ├── services.py                # Inference services (KMeans, AI4I, LSTM, IForest, DQN)
│   │   ├── interfaces.py              # BaseSchedulerPredictor, BaseHealthPredictor ABCs
│   │   ├── schemas.py                 # Placement feature vectors and recommendations
│   │   └── heuristic.py               # Active production scheduler (HeuristicSchedulerStrategy)
│   └── utils/                         # UTC timezone datetime helpers
│
├── frontend/                          # Vite + React 18 + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── api/                       # Typed API clients with configurable VITE_API_BASE_URL
│   │   ├── pages/                     # Dashboard, Clusters, Nodes, Workloads, Telemetry, ML Registry, Hero
│   │   ├── components/                # UI design system, modals, capacity drawer, charts, layout
│   │   └── types/                     # Domain & ML TypeScript definitions
│   └── package.json                   # Scripts: dev, build, test, typecheck
│
├── ml_models/                         # Pre-trained ML runtime artifacts (.joblib, .pt)
├── data/                              # Historical CSV datasets and exploratory notebooks
└── tests/                             # 148 automated Pytest tests (unit, services, API, ML integration, manifest)
```

### Data Workspace (`data/`) vs Runtime Models (`ml_models/`)
- **`data/`**: Repository data science workspace containing 9 raw training CSV datasets (e.g. `ai4i2020.csv`, `cloud_ecommerce_performance_tradeoff_dataset.csv`, `machine_failure_data.csv`, `Workload_Dataset.csv`) and 2 reference evaluation notebooks. Used for offline analysis, training pipelines, and dataset integrity checks.
- **`ml_models/`**: Serialized binary artifacts (10 `.joblib` and `.pt` files) deployed with the application. These artifacts are evaluated at runtime by `MLModelRegistry` and verified by `intellicluster.ml.manifest`. Runtime services never modify, retrain, or overwrite files in this directory.

---

## Machine Learning Runtime & Operational Matrix

INTELLICLUSTER enforces strict separation between model artifact existence, mathematical validation status, and operational deployment eligibility. Non-generalizing models are permanently quarantined.

| Model ID | Model Name & Algorithm | Trained Artifacts | Operational Status | Inference Capability / Endpoint | Operational Policy & Guardrails |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `model-1` | Server Clustering (KMeans K=4) | `server_clustering_kmeans.joblib`<br/>`server_clustering_scaler.joblib` | **READY** | `POST /api/v1/ml/cluster-archetype` | Operational. Transforms 13 input features into 18 dimensions using saved `StandardScaler` / `ColumnTransformer` and predicts one of 4 stable compute archetypes (General Purpose, Compute Intensive, Memory Intensive, High Density). |
| `model-2a` | Failure Prediction (AI4I XGBoost) | `failure_prediction_ai4i_xgboost.joblib` | **READY** | `POST /api/v1/ml/predict-failure` | Operational with Domain Boundary: Predicts failure probability on industrial milling machine features (`air_temp`, `process_temp`, `rpm`, `torque`, `tool_wear`). Server OS compute telemetry is **not** silently converted. Lower precision (38.64%) produces false alarms. |
| `model-2b` | Environmental Failure (XGBoost) | `failure_prediction_environmental_xgboost.joblib` | **REJECTED** | *None (Quarantined)* | **Permanently Quarantined.** OOF ROC-AUC ≈ 0.4891 proves zero generalization (synthetic uniform noise). Production inference blocked with HTTP 403 `ModelRejectedException`. |
| `model-3` | Resource Forecasting (Stacked LSTM) | `resource_forecasting_lstm.pt`<br/>`resource_forecasting_metadata.joblib` | **READY** | `POST /api/v1/ml/forecast-resources`<br/>`POST /api/v1/ml/forecast-node/{node_id}` | Operational. PyTorch `ResourceLSTM` (2 layers, 168h lookback, 24h horizon). Input features (5): `[cpu_utilization, memory_usage, storage_usage, workload, Resource Allocation]`. Forecast targets (3): `[cpu_utilization, memory_usage, workload]`. Requires strictly 168 continuous hourly observations; zero synthetic padding (HTTP 422 if insufficient history). |
| `model-4a` | Network Anomaly (Isolation Forest) | `network_anomaly_iforest.joblib` | **REJECTED** | *None (Quarantined)* | **Permanently Quarantined.** ROC-AUC ≈ 0.4980 shows normal vs attack score parity. Production inference blocked with HTTP 403 `ModelRejectedException`. |
| `model-4b` | Infrastructure Anomaly (Isolation Forest) | `infrastructure_anomaly_iforest.joblib` | **READY** | `POST /api/v1/ml/detect-anomaly` | Operational (Advisory Only). Contextual multivariate density scoring. Does **not** trigger autonomous node cordoning or workload eviction. |
| `model-5` | Dynamic Load Balancer (DQN) | `load_balancer_dqn.pt`<br/>`load_balancer_metadata.joblib` | **EXPERIMENTAL** | `POST /api/v1/ml/dqn-placement-recommendation` | **Experimental Shadow Benchmark Only.** Deterministic heuristic scheduler remains the active production scheduler. DQN computes recommendations and Q-values for evaluation with zero database state mutations (`is_state_mutated: false`). |

### Safety Rules & Guardrails
1. **Artifact Path Security:** Artifacts are strictly resolved relative to the trusted repository root (`ml_models/`). Arbitrary user-supplied artifact paths or path traversals (`..`) are rejected.
2. **Quarantine Enforcement:** Invocations of Model 2B or Model 4A are trapped by `MLModelRegistry.get_loaded_artifact()` and the API gateway, returning HTTP 403 `ModelRejectedException`.
3. **Strict History Verification:** Resource forecasting demands 168 hourly snapshots per node. Nodes with fewer historical records return an explicit, actionable HTTP 422 error.
4. **Active Scheduler Invariance:** `HeuristicSchedulerStrategy` remains the sole active scheduler for all cluster workload placements. DQN is read-only and experimental.

---

## Artifact Manifest & Integrity Verification

INTELLICLUSTER includes a standalone, read-only integrity manifest utility (`intellicluster.ml.manifest`). It inventories expected runtime model artifacts, verifies companion files (scalers, metadata bundles), and computes SHA-256 checksums by binary streaming without deserializing model objects.

### Run Manifest Integrity Check

```powershell
cd E:\career\INTELLICLUSTER
.\.venv\Scripts\python.exe -m intellicluster.ml.manifest
```

Output:
```text
================================================================================
INTELLICLUSTER — ML Artifact Integrity & Manifest Report
================================================================================
Verified At: 2026-10-13T12:42:59.858483+00:00
Artifacts Directory: E:\career\INTELLICLUSTER\ml_models
Status: [PASSED] All artifacts intact
Summary: 10/10 verified, 0 missing, 0 mismatched
--------------------------------------------------------------------------------
Filename                                       Status         Bytes      Model ID  
--------------------------------------------------------------------------------
server_clustering_kmeans.joblib                VERIFIED       49922      model-1   
server_clustering_scaler.joblib                VERIFIED       3460       model-1   
failure_prediction_ai4i_xgboost.joblib         VERIFIED       252502     model-2a  
failure_prediction_environmental_xgboost.joblib VERIFIED       234867     model-2b  
resource_forecasting_lstm.pt                   VERIFIED       136805     model-3   
resource_forecasting_metadata.joblib           VERIFIED       2006       model-3   
network_anomaly_iforest.joblib                 VERIFIED       3407650    model-4a  
infrastructure_anomaly_iforest.joblib          VERIFIED       1849378    model-4b  
load_balancer_dqn.pt                           VERIFIED       50573      model-5   
load_balancer_metadata.joblib                  VERIFIED       1100       model-5   
================================================================================
```

JSON output is also supported:
```powershell
.\.venv\Scripts\python.exe -m intellicluster.ml.manifest --json
```

---

## Environment Configuration

Copy `.env.example` to `.env` in the repository root:

```env
APP_NAME="IntelliCluster Backend"
APP_ENV="development"
DEBUG=true

# Database Persistence
DATABASE_URL="sqlite:///./intellicluster.db"
DB_ECHO=false

# Node Heartbeat & Liveness
NODE_HEARTBEAT_TIMEOUT_SECONDS=60

# Workload Scheduling Strategy (Default: heuristic baseline)
SCHEDULER_STRATEGY="heuristic"

# CORS Configuration (Comma-separated allowed origins for frontend web UI)
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"

# ML Model Registry Path
ML_MODEL_REGISTRY_PATH="./ml_models"

# Logging
LOG_LEVEL="INFO"
LOG_FORMAT="text"
```

### Production API Base URL & CORS Setup
- **Backend CORS:** In production, set `CORS_ORIGINS` to the exact protocol, domain, and port of your hosted frontend (e.g. `CORS_ORIGINS="https://cluster.example.com"`).
- **Frontend Base URL:** If the React frontend is hosted on a different origin or behind a CDN without a reverse proxy, configure `VITE_API_BASE_URL` in `frontend/.env` (e.g. `VITE_API_BASE_URL="https://api.example.com"`). In local development and reverse-proxy setups, leave `VITE_API_BASE_URL` empty to preserve relative URL paths (`/api`, `/health`).

---

## Starting the Application

### 1. Backend Server
```powershell
cd E:\career\INTELLICLUSTER
.\.venv\Scripts\python.exe -m uvicorn intellicluster.main:app --reload --host 127.0.0.1 --port 8000
```
- API Documentation (Swagger): `http://127.0.0.1:8000/docs`
- Health probe: `http://127.0.0.1:8000/health`
- ML Model Catalog: `http://127.0.0.1:8000/api/v1/ml/models`

### 2. Frontend Development Server
```powershell
cd E:\career\INTELLICLUSTER\frontend
npm run dev
```
- Dashboard UI: `http://localhost:3000`
- Access **Machine Learning Model Catalog** (`/ml-registry`) to inspect operational statuses and execute interactive inference test modals.
- Access **Telemetry** (`/telemetry`) to view real-time metrics and trigger 24h LSTM resource forecasts.

---

## Running Automated Verification

### Backend Test Suite (Pytest)
```powershell
cd E:\career\INTELLICLUSTER
.\.venv\Scripts\pytest.exe -v
```
**Result:** **148 passed**, 1 warning in 13.80s (100% pass rate across services, API, ML integration, ML artifacts, statistical validation, operational recovery, CORS, and artifact manifest integrity).

### Frontend Verification (TypeScript, Tests & Build)
```powershell
cd E:\career\INTELLICLUSTER\frontend

# 1. Typecheck
npm run typecheck
# Result: 0 errors

# 2. Component and Unit Tests
npm test -- --run
# Result: 8 test files passed, 55 of 55 tests passed

# 3. Production Build
npm run build
# Result: Built cleanly in 5.20s (dist/index.html, dist/assets)
```

---

## Operational Status & Demonstration CLI

INTELLICLUSTER includes a non-destructive demonstration tool (`intellicluster.demo`) to inspect operational state and test workflows without resetting existing database tables:

```powershell
cd E:\career\INTELLICLUSTER

# Inspect current operational state across clusters, nodes, workloads, and telemetry
.\.venv\Scripts\python.exe -m intellicluster.demo --status
```

---

## Deployment Status Note

- **Local Verification:** Fully verified across unit, integration, manifest integrity, TypeScript typecheck, and Vite production bundle builds.
- **Cloud Deployment:** Remote cloud infrastructure (AWS/Kubernetes) has not been provisioned or connected. Cloud deployment remains unverified until deployed to a live target environment.
