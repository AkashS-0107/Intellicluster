# Technical Requirements Document (TRD)

```text
Project: INTELLICLUSTER
Document: TRD.md
Version: 1.2
Status: Approved Operational Baseline (Deployment Readiness & Integrity Verified)
```

---

## 1. Technical Overview

INTELLICLUSTER is architected as a modular, domain-driven orchestration system written in Python. The technical stack prioritizes explicit type safety, decoupled boundaries, predictable local execution, and low operational overhead.

### Core Technology Stack
- **Language**: Python 3.10+ (Tested and verified on Python 3.13).
- **Web & Application Framework**: FastAPI (`>=0.115.0`) with ASGI server Uvicorn (`[standard]>=0.32.0`).
- **Data Validation & Settings**: Pydantic v2 (`>=2.10.0`) and Pydantic Settings (`>=2.7.0`).
- **Persistence & ORM**: SQLAlchemy 2.x (`>=2.0.36`) utilizing typed Declarative Models.
- **Development Database**: SQLite 3 with Write-Ahead Logging (WAL) and enforced foreign keys.
- **Machine Learning Runtime**: PyTorch (`torch>=2.0.0`), scikit-learn (`>=1.4.0`), XGBoost (`>=2.0.0`), joblib (`>=1.3.0`).
- **Testing Framework**: pytest (`>=8.3.0`), pytest-asyncio (`>=0.24.0`), and HTTPX (`>=0.28.0`).
- **Frontend Framework**: React 18, TypeScript 5, Vite 5, TanStack Query, Tailwind CSS, Lucide React, Vitest.

---

## 2. Current Architecture

The codebase follows a strict layered architecture where domain business logic is decoupled from transport layers, persistence engines, and machine learning models.

```text
INTELLICLUSTER/
├── intellicluster/                    # Primary application package
│   ├── __init__.py                    # Version declaration (0.1.0)
│   ├── main.py                        # FastAPI entry point, lifespan, & base health probes
│   │
│   ├── api/                           # Presentation layer
│   │   ├── exception_handlers.py      # Domain and ML HTTP exception handlers
│   │   └── v1/                        # API Version 1 Routers
│   │       ├── router.py              # Root v1 aggregator router
│   │       ├── clusters.py            # /api/v1/clusters
│   │       ├── nodes.py               # /api/v1/nodes
│   │       ├── workloads.py           # /api/v1/workloads (Production Heuristic Scheduler)
│   │       ├── telemetry.py           # /api/v1/telemetry
│   │       └── ml.py                  # /api/v1/ml (Dedicated ML router)
│   │
│   ├── core/                          # Cross-cutting foundational concerns
│   │   ├── config.py                  # Pydantic BaseSettings loading from .env
│   │   ├── constants.py               # Domain StringEnums (NodeStatus, WorkloadStatus, etc.)
│   │   ├── exceptions.py              # Domain exception hierarchy
│   │   └── logging.py                 # Structured logging setup
│   │
│   ├── db/                            # Persistence engine & session lifecycle
│   │   ├── base.py                    # DeclarativeBase, UUIDPrimaryKeyMixin, TimestampMixin
│   │   └── session.py                 # Engine factory, WAL/foreign-key pragmas, sessionmaker
│   │
│   ├── models/                        # SQLAlchemy 2.x ORM entities
│   │   ├── cluster.py                 # Cluster model
│   │   ├── node.py                    # Node / compute server model
│   │   ├── workload.py                # Workload / task model
│   │   └── telemetry.py               # TelemetrySnapshot time-series model
│   │
│   ├── schemas/                       # Pydantic v2 data transfer objects (DTOs)
│   │   ├── common.py                  # BaseSchema, pagination queries, & responses
│   │   ├── cluster.py                 # Cluster request/response DTOs & capacity summaries
│   │   ├── node.py                    # Node registration, update, & capacity DTOs
│   │   ├── workload.py                # Workload creation, update, & response DTOs
│   │   ├── telemetry.py               # Telemetry ingestion schemas & aggregate summaries
│   │   └── ml.py                      # Dedicated ML schemas (Catalog, KMeans, AI4I, LSTM, IForest, DQN)
│   │
│   ├── services/                      # Pure business logic and domain operations
│   │   ├── cluster_service.py         # Cluster lifecycle & aggregate capacity calculations
│   │   ├── node_service.py            # Node registration, heartbeats, cordoning, & liveness
│   │   ├── workload_service.py        # Workload queueing, state transitions, & placement
│   │   └── telemetry_service.py       # Metrics ingestion & cluster-wide aggregations
│   │
│   ├── ml/                            # Machine Learning Operational Runtime & Manifest
│   │   ├── architectures.py           # Exact PyTorch modules (ResourceLSTM, QNetwork)
│   │   ├── manifest.py                # Standalone SHA-256 artifact integrity manifest & CLI
│   │   ├── registry.py                # Cached MLModelRegistry with security boundaries & quarantine
│   │   ├── services.py                # Inference services (KMeans, AI4I, LSTM, IForest, DQN)
│   │   ├── interfaces.py              # Abstract Base Classes (BaseSchedulerPredictor, BaseHealthPredictor)
│   │   ├── schemas.py                 # Feature vectors & recommendation DTOs
│   │   └── heuristic.py               # Production deterministic heuristic scheduler
│   │
│   └── utils/                         # Shared utilities
│       └── datetime_utils.py          # UTC timezone helper functions
│
├── frontend/                          # React + TypeScript Dashboard
│   ├── src/
│   │   ├── api/                       # API clients with configurable VITE_API_BASE_URL
│   │   ├── pages/                     # Dashboard, Clusters, Nodes, Workloads, Telemetry, ML Registry, Hero
│   │   ├── components/                # Modular UI components, modals, capacity drawer, charts
│   │   └── types/                     # Shared TypeScript interfaces
│   └── package.json                   # Scripts: dev, build, test, typecheck
│
├── ml_models/                         # Trained model artifacts (.joblib, .pt)
├── data/                              # Baseline datasets and training references
└── tests/                             # Automated test suite (148 tests)

    ├── conftest.py                    # Isolated in-memory SQLite fixtures & TestClient
    ├── services/                      # Domain service tests
    ├── unit/                          # Unit tests (config, db, models, schemas, exceptions, ml runtime)
    ├── test_api_v1_integration.py     # Core API integration tests
    ├── test_api_v1_ml_integration.py  # ML API endpoint integration tests
    ├── test_ml_artifacts.py           # Checkpoint and Joblib artifact validation tests
    └── test_ml_validation.py          # ML statistical boundary tests
```

---

## 3. Database Architecture

The persistence architecture is designed for transactional consistency, rapid local execution during development, and future seamless migration to enterprise relational engines.

```mermaid
erDiagram
    CLUSTERS ||--o{ NODES : "contains"
    CLUSTERS ||--o{ WORKLOADS : "manages"
    NODES ||--o{ WORKLOADS : "hosts"
    NODES ||--o{ TELEMETRY_SNAPSHOTS : "records"
```

---

## 4. Domain Services

Domain business logic is encapsulated in four stateless services:

### 4.1 ClusterService (`cluster_service.py`)
- `create_cluster(session, data)`: Enforces uniqueness on cluster name and initializes status.
- `get_cluster_by_id(session, cluster_id)`: Retrieves cluster or raises `ClusterNotFoundException`.
- `list_clusters(session, skip, limit, status)`: Returns paginated list with optional status filtering.
- `update_cluster(session, cluster_id, data)`: Modifies metadata or status while protecting uniqueness.
- `calculate_cluster_capacity(session, cluster_id)`: Aggregates total vs. allocated CPU and memory across active nodes, computes average utilization, and tallies active workloads.

### 4.2 NodeService (`node_service.py`)
- `register_node(session, data)`: Validates hostname uniqueness, attaches to optional cluster, and initializes hardware limits.
- `process_heartbeat(session, node_id, telemetry)`: Updates `last_heartbeat`, refreshes cached current utilization, recalculates deterministic health score, adjusts status (`READY`, `DEGRADED`, `UNREACHABLE`), and persists an append-only `TelemetrySnapshot`.
- `mark_stale_nodes(session, timeout_seconds)`: Identifies active nodes that have not reported a heartbeat within the configured threshold (`NODE_HEARTBEAT_TIMEOUT_SECONDS=60`) and transitions them to `UNREACHABLE`.
- `cordon_node(session, node_id)` / `uncordon_node(session, node_id)`: Manages administrative isolation to prevent new workload placements.
- `get_allocatable_capacity(session, node_id)`: Computes remaining CPU cores and RAM MB by subtracting actively scheduled/running workload requests from node hardware limits.

### 4.3 WorkloadService (`workload_service.py`)
- `create_workload(session, data)`: Validates resource requirements and places task into `PENDING` state.
- `schedule_pending_workload(session, workload_id, strategy)`: Queries candidate nodes, invokes a `BaseSchedulerPredictor` strategy (defaults to `HeuristicSchedulerStrategy`), binds the optimal node, increments node workload counts, transitions state to `SCHEDULED`, and records `scheduled_at`.
- `transition_workload_status(session, workload_id, target_status, failure_reason)`: Enforces strict state machine rules (`VALID_TRANSITIONS`), tracks lifecycle timestamps (`started_at`, `completed_at`), and decrements node workload counts upon completion or failure.
- `cancel_workload(session, workload_id)`: Transitions eligible workloads to `CANCELLED`.

### 4.4 TelemetryService (`telemetry_service.py`)
- `record_telemetry(session, node_id, data)`: Ingests metric payloads, updates node state, and records snapshots.
- `get_node_telemetry_history(session, node_id, limit)`: Returns historical snapshots ordered chronologically descending.
- `get_cluster_aggregated_metrics(session, cluster_id)`: Computes real-time average/maximum CPU, memory, and latency across active reporting nodes.

---

## 5. Machine Learning Runtime Architecture

The ML runtime operates as a dedicated subsystem under `intellicluster.ml`, providing real model loading, inference pipelines, and safety quarantine.

```mermaid
graph TD
    subgraph Core_Backend["Core Backend Operations"]
        WS[WorkloadService]
        NS[NodeService]
        HSS["HeuristicSchedulerStrategy<br/>(ACTIVE PRODUCTION SCHEDULER)"]
        WS --> HSS
    end

    subgraph ML_Runtime["Operational ML Subsystem (intellicluster/ml)"]
        REG["MLModelRegistry<br/>(Cached Singleton, Quarantine Guards)"]
        
        SRV_KMEANS["KMeansInferenceService<br/>(Model 1: Server Archetyping)"]
        SRV_AI4I["AI4IInferenceService<br/>(Model 2A: Machine Failure)"]
        SRV_LSTM["LSTMForecastingService<br/>(Model 3: 24h Resource Trajectory)"]
        SRV_IFOREST["InfrastructureAnomalyService<br/>(Model 4B: Contextual Density)"]
        SRV_DQN["DQNBenchmarkService<br/>(Model 5: Shadow Recommendation)"]
        
        REG --> SRV_KMEANS
        REG --> SRV_AI4I
        REG --> SRV_LSTM
        REG --> SRV_IFOREST
        REG --> SRV_DQN
    end

    subgraph API_Layer["API Presentation Layer (/api/v1/ml)"]
        API_CAT["GET /models"]
        API_KM["POST /cluster-archetype"]
        API_AI["POST /predict-failure"]
        API_LSTM["POST /forecast-resources"]
        API_NODE["POST /forecast-node/{id}"]
        API_ANO["POST /detect-anomaly"]
        API_DQN["POST /dqn-placement-recommendation"]
    end

    API_CAT --> REG
    API_KM --> SRV_KMEANS
    API_AI --> SRV_AI4I
    API_LSTM --> SRV_LSTM
    API_NODE --> SRV_LSTM
    API_ANO --> SRV_IFOREST
    API_DQN --> SRV_DQN
```

### 5.1 Model Registry & Lifecycle Management (`registry.py`)
- **Cached Loading:** The `MLModelRegistry` loads each artifact once on startup or initial demand and stores it in memory.
- **Path Isolation:** Artifacts are strictly resolved relative to the project root (`repo_root / "ml_models"`). Arbitrary external file paths are rejected.
- **Quarantine Enforcement:** Models `model-2b` and `model-4a` are flagged as `REJECTED`. The registry method `get_loaded_artifact` throws a `PermissionError` if an attempt is made to fetch them for execution.

- **Operational Status Tracking:** Each model tracks `loading_status` (`LOADED`, `NOT_LOADED`, `FAILED`), `validation_status` (`VALIDATED`, `REJECTED`, `EXPERIMENTAL`), and overall `operational_status` (`READY`, `REJECTED`, `EXPERIMENTAL`, `ERROR`).

### 5.2 PyTorch Neural Architectures (`architectures.py`)
- **`ResourceLSTM`**: A 2-layer stacked LSTM network (`in_dim=5, h1=64, h2=32, out_horizon=24, out_vars=3, dropout=0.2`) matching the saved weights in `resource_forecasting_lstm.pt`. In evaluation mode, it generates multi-step resource trajectories.
- **`QNetwork`**: A 3-layer deep Q-network (`in_dim=25, out_actions=4`: `Linear(25, 128) -> ReLU -> Linear(128, 64) -> ReLU -> Linear(64, 4)`) matching `load_balancer_dqn.pt`.

### 5.3 Operational ML Services (`services.py`)
1. **KMeansInferenceService (Model 1):** Validates 13 features (12 numerical metrics + `region`), applies saved `ColumnTransformer` (scaling numerical features and one-hot encoding `region` to 18 dimensions), predicts cluster (0..3), and annotates with empirical compute archetypes.
2. **AI4IInferenceService (Model 2A):** Validates physical milling telemetry (`air_temperature_k`, `process_temperature_k`, `rpm`, `torque`, `tool_wear`, `product_variant`), one-hot encodes product type, executes XGBoost booster, and outputs calibrated failure probability and risk level.
3. **LSTMForecastingService (Model 3):** Validates 168-hour sequences of 5 features (`cpu_utilization`, `memory_usage`, `storage_usage`, `network_throughput_mbps`, `active_connections`). Imputes missing values with saved feature medians, transforms via `RobustScaler`, executes `ResourceLSTM`, and inversely transforms the 24x3 forecast outputs. Node forecast requires strictly $\ge 168$ historical database snapshots; returns `InsufficientHistoryException` (HTTP 422) if insufficient.
4. **InfrastructureAnomalyService (Model 4B):** Evaluates 5-variable server telemetry against the saved Isolation Forest density estimator, yielding decision scores and contextual anomaly alerts (advisory only).
5. **DQNBenchmarkService (Model 5):** Constructs 25-dimensional state vectors representing workload demands and candidate node resource headroom. Evaluates Q-values across 4 node action channels, proposes best candidate, and provides side-by-side comparison against the active heuristic scheduler with zero database state mutations.

### 5.4 Mandatory Operational Policies
1. **Heuristic Primacy:** `HeuristicSchedulerStrategy` remains the sole active scheduler for production cluster workload assignments. DQN is strictly an experimental shadow comparison tool.
2. **Domain Semantic Boundary:** Model 2A uses industrial milling machine features. Node OS telemetry is not silently mapped to industrial sensor inputs.
3. **Quarantined Models:** Model 2B (Environmental XGBoost) and Model 4A (Network Isolation Forest) are strictly blocked from production inference.
4. **Honest History:** LSTM forecasting requires 168 real hourly records. Zero synthetic padding is allowed.

---

## 6. Dataset Ingestion & Scientific Evaluation

| Dataset Name | Ingestion Status | Designated ML System | Operational Role / Finding |
| :--- | :--- | :--- | :--- |
| `ai4i2020.csv` | **Actively Ingested** | Model 2A (Hardware Failure) | Forecasts component degradation (thermal, tool wear, torque). **Operational.** |
| `cloud_ecommerce_performance_tradeoff_dataset.csv` | **Actively Ingested** | Model 1 (Server Clustering) & Model 5 | Clusters server archetypes; calibrates DQN node capacities. **Operational.** |
| `Resource_utilization.csv` | **Actively Ingested** | Model 3 (LSTM) & Model 4B (Infra IF) | Chronological telemetry series; background utilization. **Operational.** |
| `Load Balancing Improved.csv` | **Actively Ingested** | Model 5 (DQN Load Balancer) | Empirical task demand stream (10,678 records). **Operational.** |
| `Workload_Dataset.csv` | **Actively Ingested** | Model 5 (DQN Load Balancer) | Workload category profiles (`Database`, `AI`, `Analytics`, `Web`). **Operational.** |
| `machine_failure_data.csv` | **Actively Ingested** | Model 2B (Environmental XGBoost) | Multi-sensor telemetry. Diagnosed as synthetic uniform noise with zero predictive signal (OOF ROC-AUC ≈ 0.4891). **Quarantined.** |
| `embedded_system_network_security_dataset.csv` | **Actively Ingested** | Model 4A (Network IF) | Network traffic features. Diagnosed with identical uniform distributions for normal and attack samples (ROC-AUC ≈ 0.4980). **Quarantined.** |

---

## 7. REST API Layer Specification

All REST APIs are versioned under `/api/v1/`:

```text
/api/v1/
├── /clusters
│   ├── POST   /                  # Create new cluster
│   ├── GET    /                  # List clusters (paginated)
│   ├── GET    /{cluster_id}      # Get cluster details
│   ├── PUT    /{cluster_id}      # Update cluster metadata
│   └── GET    /{cluster_id}/capacity  # Calculate aggregate capacity
│
├── /nodes
│   ├── POST   /                  # Register new node
│   ├── GET    /                  # List nodes (filterable by cluster/status)
│   ├── GET    /{node_id}         # Get node details
│   ├── PUT    /{node_id}         # Update node metadata
│   ├── POST   /{node_id}/heartbeat   # Ingest node heartbeat & live telemetry
│   ├── POST   /{node_id}/cordon      # Cordon node
│   ├── POST   /{node_id}/uncordon    # Uncordon node
│   └── GET    /{node_id}/capacity    # Get node allocatable capacity
│
├── /workloads
│   ├── POST   /                  # Submit new workload (PENDING)
│   ├── GET    /                  # List workloads (filterable by status/node)
│   ├── GET    /{workload_id}     # Get workload details
│   ├── PUT    /{workload_id}     # Update workload
│   ├── POST   /{workload_id}/schedule # Trigger heuristic scheduling placement
│   ├── POST   /{workload_id}/status   # Transition lifecycle state
│   └── POST   /{workload_id}/cancel   # Cancel workload
│
├── /telemetry
│   ├── POST   /nodes/{node_id}   # Record raw telemetry snapshot
│   ├── GET    /nodes/{node_id}   # Query historical telemetry snapshots
│   └── GET    /clusters/{cluster_id}/aggregate # Real-time aggregate telemetry
│
└── /ml
    ├── GET    /models            # Retrieve ML catalog and operational readiness
    ├── POST   /cluster-archetype # Predict server archetype via KMeans
    ├── POST   /predict-failure   # Predict machine failure via AI4I XGBoost
    ├── POST   /forecast-resources# Forecast 24h resources from 168h raw array
    ├── POST   /forecast-node/{id}# Forecast 24h resources from node DB telemetry
    ├── POST   /detect-anomaly    # Infrastructure anomaly detection via Isolation Forest
    ├── POST   /dqn-placement-recommendation # Read-only DQN shadow placement recommendation
    └── POST   /models/{id}/infer # Unified test gateway (blocks rejected models)
```

### Exception Mapping Strategy
Domain exceptions map directly to HTTP status codes:
- `EntityNotFoundException` → `404 Not Found`
- `EntityAlreadyExistsException` → `409 Conflict`
- `NoAvailableNodeException` → `422 Unprocessable Entity`
- `InvalidStateTransitionException` → `400 Bad Request`
- `CapacityExceededException` → `400 Bad Request`
- `ModelRejectedException` → `403 Forbidden`
- `InsufficientHistoryException` → `422 Unprocessable Entity`
- `ModelNotReadyException` → `503 Service Unavailable`
- `ConfigurationException` → `500 Internal Server Error`

---

## 8. Testing Architecture & Empirical Verification

Testing is embedded into the project lifecycle with strict phase-appropriate scopes:

```text
tests/
├── conftest.py                    # In-memory SQLite fixture with StaticPool & TestClient
├── test_api_health.py             # API lifecycle and health probe tests
├── test_api_v1_integration.py     # Core cluster/node/workload API integration tests
├── test_api_v1_ml_integration.py  # ML API endpoints integration tests
├── test_ml_artifacts.py           # Checkpoint and Joblib artifact validation tests
├── test_ml_validation.py          # ML statistical boundary tests
├── test_operations_recovery.py    # Core operations recovery & lifecycle hardening tests
├── test_repair_hardening.py       # Hardening regression tests
├── services/                      # Domain service tests
│   ├── test_cluster_service.py
│   ├── test_node_service.py
│   ├── test_telemetry_service.py
│   └── test_workload_service.py
└── unit/                          # Unit tests
    ├── test_config.py
    ├── test_cors.py               # Backend CORS middleware & origins validation
    ├── test_database.py
    ├── test_exceptions.py
    ├── test_ml_boundary.py
    ├── test_ml_manifest.py        # ML artifact SHA-256 integrity & manifest tests
    ├── test_ml_runtime.py         # ML runtime services & registry unit tests
    ├── test_models.py
    └── test_schemas.py
```

### Verified Test Results
- **Backend (Pytest):** **148 passed**, 1 warning in 13.80s (100% pass rate).
  - 104 core foundation and service tests
  - 13 ML API integration tests
  - 8 ML runtime unit tests
  - 10 operational recovery & workflow hardening tests
  - 4 CORS middleware unit tests
  - 9 ML artifact manifest integrity tests
- **Frontend (Vitest):** **8 test files passed**, **55 of 55 tests passed** (including 8 API client base URL tests).
- **Frontend Typecheck (TypeScript):** Passed cleanly with 0 errors (`tsc --noEmit`).
- **Frontend Build (Vite):** Built production asset bundle cleanly in 5.20s (`dist/index.html`, `dist/assets`).

---

## 9. Persistence & Production Deployment Requirements

### Persistence Engine
- **Local/Development:** SQLite 3 with Write-Ahead Logging (`WAL`), `synchronous=NORMAL`, and foreign key enforcement enabled (`PRAGMA foreign_keys=ON`).
- **Production Target:** Multi-tenant or distributed production workloads require a PostgreSQL database backend. Set `DATABASE_URL` to a valid PostgreSQL connection string (e.g. `postgresql+psycopg2://user:pass@host:5432/intellicluster`).

### Network & Security Boundary
- **CORS Configuration:** `CORS_ORIGINS` must be populated with allowed origins in production. Wildcard origins (`*`) are disallowed when `allow_credentials=True`.
- **Frontend Connectivity:** When the frontend is hosted separately from the FastAPI server, configure `VITE_API_BASE_URL` in `frontend/.env`. When co-located or fronted by an NGINX reverse proxy, leave `VITE_API_BASE_URL` empty to preserve relative URL paths (`/api`, `/health`).

### Cloud Verification Status
- Local unit, integration, manifest integrity, and production bundle builds have been thoroughly verified.
- Cloud deployment (AWS / Kubernetes) remains unverified until deployed and validated on live remote infrastructure.

