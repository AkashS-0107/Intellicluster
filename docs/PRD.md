# Product Requirements Document (PRD)

```text
Project: INTELLICLUSTER
Document: PRD.md
Version: 1.2
Status: Approved Operational Baseline (Deployment Readiness & Integrity Verified)
```

---

## 1. Product Overview

### 1.1 Product Name
**INTELLICLUSTER**: Machine-Learning-Driven Cloud Server Clustering and Workload Orchestration System.

### 1.2 Product Vision
INTELLICLUSTER is an intelligent, automated compute management platform engineered to orchestrate server clusters, ingest high-frequency performance telemetry, evaluate node health, and schedule heterogeneous computational workloads. By combining deterministic operational guardrails with specialized machine-learning models, INTELLICLUSTER optimizes compute resource utilization, mitigates node degradation, and prevents cascading infrastructure failures.

### 1.3 Problem Statement
Modern distributed server clusters face critical operational challenges:
1. **Inefficient Workload Distribution**: Traditional static, round-robin, or purely reactive scheduling strategies fail to anticipate resource contention, causing CPU/memory bottlenecks on subset nodes while others idle.
2. **Unpredicted Server Degradation**: Physical and virtual compute nodes degrade over time due to thermal stress, memory leaks, disk I/O exhaustion, and network instability. Without predictive health forecasting, workloads are assigned to failing nodes, leading to execution failures and expensive retries.
3. **Network Anomaly Blindspots**: Clusters operating under dynamic traffic patterns often encounter latent network saturation, latency spikes, or security anomalies that static rule engines fail to flag before service-level agreements (SLAs) are breached.
4. **Complex Operational Overhead**: Infrastructure operators lack unified, automated scheduling and monitoring systems that combine cluster capacity tracking, node health scoring, and workload placement into a single cohesive control plane.

### 1.4 Core Value Proposition
- **Adaptive Workload Placement**: Intelligently matches workload compute requirements (CPU cores, RAM, network bandwidth, latency sensitivity) to optimal candidate nodes using a verified deterministic best-fit scheduler.
- **Predictive Failure Avoidance**: Proactively identifies node risk profiles and contextual density anomalies.
- **Phased & Decoupled Intelligence**: Employs deterministic baseline heuristics for dependable active operations while providing a cached ML runtime registry for specialized inferences.
- **High Operational Visibility**: Provides structured time-series telemetry snapshots and real-time cluster capacity aggregation.

---

## 2. Product Scope

### 2.1 What INTELLICLUSTER Is
- A custom, domain-driven cluster control plane and workload scheduler.
- A central management service for tracking compute nodes, their hardware capacities, and runtime telemetry.
- An extensible orchestrator supporting deterministic baseline scheduling and specialized ML inference engines.
- A structured orchestration platform developed under a strict 10-step engineering process.

### 2.2 What INTELLICLUSTER Is Not
- **Not a Commercial Cloud Provider Clone**: It does not attempt to reproduce AWS, GCP, or Azure hyperscaler ecosystems, multi-tenant billing platforms, or global identity management systems.
- **Not a Kubernetes Replacement**: It does not implement CRI/CNI/CSI specifications, multi-container pod abstractions, or massive distributed consensus protocols (e.g., Raft/etcd).
- **Not a General-Purpose Hypervisor**: It does not manage bare-metal virtualization, QEMU/KVM virtual machine disk imaging, or hardware-level PCI passthrough.
- **Not a Monolithic ML Engine**: It explicitly rejects blending unrelated data domains (e.g., network traffic, machine tool wear, and request loads) into a single uninterpretable "black box" model.

---

## 3. Target Users & Personas

| Persona | Primary Role | Key Responsibilities & Needs | System Interaction |
| :--- | :--- | :--- | :--- |
| **Infrastructure / DevOps Engineer** | Cluster Operations & Reliability | - Monitor aggregate cluster health and resource capacity.<br/>- Register, update, cordon, or uncordon compute nodes.<br/>- Investigate stale heartbeats, node degradation, and system warnings. | Control plane dashboard, node management APIs, telemetry aggregates. |
| **Application / Workload Developer** | Workload Execution & SLA Management | - Submit batch jobs, data-processing pipelines, or real-time API tasks with explicit resource constraints.<br/>- Track workload lifecycle states (`PENDING` → `SCHEDULED` → `RUNNING` → `COMPLETED`/`FAILED`).<br/>- Review scheduling reasoning and failure diagnostics. | Workload submission APIs, job status endpoints, execution logs. |
| **ML / Data Engineer** | Model Research & Evaluation | - Analyze historical time-series telemetry records.<br/>- Train specialized prediction models in Jupyter notebooks using separated baseline datasets.<br/>- Evaluate model metrics (accuracy, F1, MAE) against deterministic baseline heuristics.<br/>- Test model inference via `/api/v1/ml/` test modals. | Exported telemetry snapshots, Jupyter training environments, model registry API. |

---

## 4. Feature Scope Matrix

Development is governed across ten discrete development steps:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FEATURE SCOPE MATRIX                            │
├────────────────────────────┬───────────────────────────────────────────┤
│ Implemented & Verified     │ Step 1: Backend Foundation                │
│ Baseline                   │ Step 2: REST API & Routing                │
│                            │ Step 3: ML Model Training in Notebooks    │
│                            │ Step 4: ML Testing & Benchmarking         │
│                            │ Step 5: Frontend Dashboard Application    │
│                            │ Step 6: ML Operationalization & E2E Tests │
│                            │         (148 Pytest + 55 Vitest Tests)   │
├────────────────────────────┼───────────────────────────────────────────┤
│ Implemented & Verified     │ Step 7: UI Copy & Responsive Mobile Polish│
│                            │         (Manifest Integrity, CORS Ready)  │
├────────────────────────────┼───────────────────────────────────────────┤
│ Planned for Step 8         │ Entire Project Load & Concurrency Stress  │
├────────────────────────────┼───────────────────────────────────────────┤
│ Planned for Step 9         │ Cloud Deployment & AWS Verification       │
├────────────────────────────┼───────────────────────────────────────────┤
│ Planned for Step 10        │ Error Fixing, Bug Sweeps & Final Freeze   │
└────────────────────────────┴───────────────────────────────────────────┘
```

---

## 5. Functional Requirements

### 5.1 Cluster Management
- **FR-1.1**: The system must allow creating, retrieving, listing, and updating named compute clusters.
- **FR-1.2**: The system must calculate aggregate cluster capacity: total vs. allocated CPU cores, total vs. allocated memory, average CPU utilization percentage, average memory utilization percentage, and active workload counts.
- **FR-1.3**: The system must prevent duplicate cluster names (`ClusterAlreadyExistsException`).

### 5.2 Node Management & Liveness
- **FR-2.1**: The system must register compute nodes with specified hardware capacity (CPU cores, RAM MB, storage GB, network bandwidth Mbps).
- **FR-2.2**: The system must reject duplicate hostnames (`NodeAlreadyExistsException`).
- **FR-2.3**: The system must support administrative cordoning (`is_cordoned=True`) to prevent new workload placements while allowing existing workloads to drain.
- **FR-2.4**: The system must process node heartbeats, updating `last_heartbeat`, refreshing cached live metrics, recalculating health scores, and appending historical telemetry snapshots.
- **FR-2.5**: The system must detect silent nodes whose last heartbeat exceeds `NODE_HEARTBEAT_TIMEOUT_SECONDS` (default: 60s) and transition them to `UNREACHABLE`.

### 5.3 Workload Management & Lifecycle State Machine
- **FR-3.1**: The system must accept workload submissions into a `PENDING` state with defined resource requests (CPU, RAM, storage, network, latency SLA, priority).
- **FR-3.2**: The system must enforce valid lifecycle state transitions:
  - `PENDING` → `SCHEDULED`, `CANCELLED`
  - `SCHEDULED` → `RUNNING`, `CANCELLED`, `FAILED`
  - `RUNNING` → `COMPLETED`, `FAILED`, `CANCELLED`
  - `FAILED` → `PENDING` (Retry cycle, up to `max_retries`)
  - `COMPLETED`, `CANCELLED` → Terminal (No further transitions)
- **FR-3.3**: The system must update node active workload counts and adjust node status (`BUSY` when running workloads, `READY` when idle).

### 5.4 Telemetry Ingestion & Aggregation
- **FR-4.1**: The system must persist immutable, append-only telemetry snapshots indexed by `(node_id, recorded_at)`.
- **FR-4.2**: The system must query historical telemetry records for any node with configurable limits.
- **FR-4.3**: The system must compute real-time cluster-wide aggregated metrics (average/maximum CPU usage, average/maximum memory usage, average network latency, total active connections).

### 5.5 Workload Scheduling & Placement
- **FR-5.1**: The system evaluates candidate nodes using `HeuristicSchedulerStrategy`, filtering out cordoned, inactive, or capacity-constrained nodes and ranking eligible nodes via deterministic fitness scoring.
- **FR-5.2**: The system raises `NoAvailableNodeException` if no candidate node satisfies the workload's CPU, RAM, or latency SLA requirements.
- **FR-5.3**: The deterministic heuristic scheduler remains the sole active production scheduler. Experimental reinforcement learning models (DQN) operate strictly in read-only shadow benchmark mode.

### 5.6 Machine Learning Operational Runtime & Governance
- **FR-6.1 (Model Catalog & Discovery)**: The system exposes `GET /api/v1/ml/models` returning all models with their algorithm, loading state, validation status, operational status, and documented limitations.
- **FR-6.2 (Safe Artifact Loading)**: The system loads artifacts exclusively from trusted relative project paths (`ml_models/`) and caches them safely in memory.
- **FR-6.3 (Strict Quarantine)**: Models with unproven generalization (`model_2b` Environmental XGBoost and `model_4a` Network Isolation Forest) are strictly blocked from production inference with HTTP 403 `ModelRejectedException`.
- **FR-6.4 (Domain Semantic Guardrails)**: Model 2A (AI4I XGBoost) is constrained to physical industrial machine features; general server OS metrics are not silently mapped to industrial sensors.
- **FR-6.5 (Telemetry History Integrity)**: Model 3 (LSTM) demands strictly 168 hours of continuous historical observations. Forecasting requests on nodes with fewer snapshots return an explicit, actionable HTTP 422 `InsufficientHistoryException` without zero-padding.
- **FR-6.6 (Shadow-Mode DQN)**: Model 5 evaluates placement recommendations side-by-side with heuristic baseline without mutating database state (`is_state_mutated: false`).

---

## 6. Non-Functional Requirements

### 6.1 Reliability & Fault Tolerance
- **NFR-1**: Unreachable or degraded nodes must be isolated automatically to prevent scheduling failures.
- **NFR-2**: All database operations must be transactional, rolling back cleanly on errors.
- **NFR-3**: In-flight workloads on failed nodes must support controlled retries up to configured thresholds.

### 6.2 Performance & Responsiveness
- **NFR-4**: Scheduling evaluations for in-memory candidate sets must complete within sub-second thresholds.
- **NFR-5**: Database write operations for high-frequency telemetry snapshots must utilize WAL mode to prevent read/write lock contention.

### 6.3 Security & Data Integrity
- **NFR-6**: The system must enforce foreign key integrity across all relations.
- **NFR-7**: Database queries must use parameterized ORM constructs to prevent SQL injection.
- **NFR-8**: No raw credentials or secret keys may be committed to version control; configuration must load strictly from validated environment variables.
- **NFR-9**: The ML registry rejects external/user-supplied file paths to prevent arbitrary code execution via deserialization.

### 6.4 Maintainability & Modularity
- **NFR-10**: Domain services must remain decoupled from HTTP/transport logic, allowing testing without spinning up network servers.
- **NFR-11**: The machine learning runtime is isolated under `intellicluster.ml`, with PyTorch architectures decoupled from training scripts.

### 6.5 Observability & Testability
- **NFR-12**: The system must output structured logs with configurable verbosity and format (`text`, `json`).
- **NFR-13**: All domain services, models, scheduling logic, and ML inference pipelines must be fully verifiable via automated tests.

---

## 7. Acceptance Criteria per Development Step

| Phase | Milestone | Acceptance Criteria | Current Status |
| :--- | :--- | :--- | :--- |
| **Step 1** | Backend Foundation | - Complete ORM models for Cluster, Node, Workload, Telemetry.<br/>- Fully functioning domain services with state validation.<br/>- Deterministic heuristic scheduling and health scoring.<br/>- Isolated SQLite in-memory test suite. | **VERIFIED COMPLETE** |
| **Step 2** | REST API Endpoints | - REST routers implemented for all entities (`/clusters`, `/nodes`, `/workloads`, `/telemetry`).<br/>- Global exception mapping to standard HTTP errors.<br/>- OpenAPI docs accessible at `/docs`. | **VERIFIED COMPLETE** |
| **Step 3** | ML Model Training | - Independent Jupyter notebooks training specialized models.<br/>- Clean kernel top-to-bottom execution.<br/>- Exported serialized model artifacts saved to `./ml_models/`. | **VERIFIED COMPLETE** |
| **Step 4** | ML Model Testing | - Standalone model evaluation suite passing.<br/>- Documented metrics, limitations, and baseline comparisons. | **VERIFIED COMPLETE** |
| **Step 5** | Frontend Application | - Web UI successfully communicates with REST API.<br/>- Real-time display of cluster capacity, node health, and workloads.<br/>- Node cordoning and heartbeat simulation drawers. | **VERIFIED COMPLETE** |
| **Step 6** | ML Operationalization & E2E Testing | - Real inference services for KMeans, AI4I, LSTM, IForest, and DQN.<br/>- Dedicated `/api/v1/ml/` API router.<br/>- Quarantined non-generalizing models (2B, 4A).<br/>- Interactive ML testing modals and 24h LSTM forecasting in UI.<br/>- **148 backend tests and 55 frontend tests passing.** | **VERIFIED COMPLETE** |
| **Step 7** | UI/UX Copy, Responsive & Integrity | - UI copy refined, mobile terminal overflow resolved, CORS and API base URL configured, SHA-256 artifact manifest verified. | **VERIFIED COMPLETE** |
| **Step 8** | Full Project Testing & Benchmarking | - Comprehensive stress testing, concurrency validation, and load testing. | Planned |
| **Step 9** | Cloud Deployment & Verification | - Deployment to AWS infrastructure with PostgreSQL and RDS migrations. | Planned |
| **Step 10** | Error Fixing & Final Stabilization | - Zero outstanding critical/high bugs across the entire platform. | Planned |

---

## 8. Non-Goals (Explicit Out-of-Scope Items)

1. **Commercial Hyperscaler Parity**: No multi-region data replication, complex billing/metering engines, or IAM federation with external identity providers.
2. **Kubernetes Interoperability**: No Kubernetes operator development, custom resource definitions (CRDs), Helm charts, or Kubelet emulation.
3. **Premature Distributed Message Brokers**: No integration of Kafka, RabbitMQ, Celery, or Redis; scheduling operates directly through domain services and SQLite.
4. **Premature Cloud SDKs**: No AWS SDK (`boto3`) dependencies or cloud-specific calls before Step 9.
5. **Monolithic Dataset Fusion**: No merging of disparate datasets into a single model.
6. **Scheduler Hijacking**: The active heuristic scheduler must never be silently overridden by experimental models without separate formal approval and comparative benchmarks.
