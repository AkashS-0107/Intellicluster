# System & Development Workflow (WORKFLOW)

```text
Project: INTELLICLUSTER
Document: WORKFLOW.md
Version: 1.0
Status: Approved Baseline
```

---

## 1. Overview & Operational Principles

This document establishes the dual workflow governing INTELLICLUSTER:
- **Part A: Runtime System Workflow**: The operational sequence through which clusters, compute nodes, telemetry metrics, and workloads move through ingestion, health evaluation, scheduling, and execution.
- **Part B: Development Workflow**: The immutable 10-step development sequence and the rigid two-prompt engineering discipline governing all code, test, and infrastructure modifications.

---

## Part A: Runtime System Workflow

The runtime pipeline coordinates telemetry ingestion, state evaluation, and workload placement across the cluster:

```mermaid
graph TD
    subgraph Ingestion["1. Telemetry & Heartbeat Ingestion"]
        A[Compute Node / Agent] -->|POST Heartbeat & Metrics| B[NodeService / TelemetryService]
        B -->|Append Immutable Record| C[(telemetry_snapshots)]
        B -->|Update Live Cache| D[Node Record in DB]
    end

    subgraph Evaluation["2. Health & Capacity Evaluation"]
        D --> E{Health Evaluator}
        E -->|Step 1: Deterministic Heuristic| F[Heuristic Penalty Scoring<br/>CPU / RAM / Latency]
        E -.->|Step 3: ML Anomaly Model| G[ML Model Health Predictor]
        F --> H[Update node.health_score]
        G -.-> H
        H --> I{Heartbeat Timeout Check}
        I -->|age > 60s| J[Mark Node UNREACHABLE]
        I -->|health < 30.0| K[Mark Node DEGRADED]
        I -->|healthy| L[Mark Node READY / BUSY]
    end

    subgraph Submission["3. Workload Submission"]
        M[Developer / System Client] -->|Submit Workload Specs| N[WorkloadService.create_workload]
        N -->|Validate Constraints| O[Workload in PENDING State]
    end

    subgraph Scheduling["4. Orchestration & Placement"]
        O --> P[WorkloadService.schedule_pending_workload]
        P --> Q[Query Active Candidate Nodes]
        Q --> R{Scheduler Engine}
        R -->|Step 1: Deterministic Best-Fit| S[HeuristicSchedulerStrategy<br/>Filter Headroom & Latency SLA]
        R -.->|Step 3: ML Placement Model| T[ML Placement Predictor]
        S --> U[PlacementRecommendation]
        T -.-> U
        U -->|No Node Qualifies| V[Raise NoAvailableNodeException<br/>Remain PENDING]
        U -->|Node Selected| W[Bind assigned_node_id<br/>Transition to SCHEDULED]
    end

    subgraph Execution["5. Execution & Lifecycle Tracking"]
        W --> X[Node Agent Executes Task]
        X -->|Started| Y[Workload RUNNING]
        X -->|Successful Completion| Z[Workload COMPLETED]
        X -->|Execution Failure| AA[Workload FAILED]
        AA -->|retry_count < max_retries| AB[Reset to PENDING for Rescheduling]
        Z --> AC[Decrement Node Workload Count<br/>Reclaim Allocatable Headroom]
        AA --> AC
    end
```

### Detailed Operational Stages

#### 1. Ingestion Stage
- Compute nodes submit periodic heartbeats containing telemetry data: CPU usage %, memory usage MB, disk usage GB, network TX/RX Mbps, network latency ms, and active socket connections.
- This ingestion occurs via `NodeService.process_heartbeat` or `TelemetryService.record_telemetry`, exposed over HTTP via `POST /api/v1/nodes/{node_id}/heartbeat`.
- Each report atomically appends an immutable record to the `telemetry_snapshots` table and updates the node's live cached counters and `last_heartbeat` timestamp.


#### 2. Health & Capacity Evaluation Stage
- Node health is evaluated immediately upon telemetry arrival.
- **Active Production Path**: Evaluated deterministically via `calculate_deterministic_health_score`. Points are deducted for high CPU, high memory, and network latency exceeding 20ms. If health falls below 30.0, the node status degrades automatically to `DEGRADED`.
- **ML Advisory Path**: Evaluated by ML services (`AI4IInferenceService`, `InfrastructureAnomalyService`) or classes implementing `BaseHealthPredictor` for contextual risk scoring.
- **Liveness Monitoring**: Background sweep calls `NodeService.mark_stale_nodes`. Any active node failing to report within `NODE_HEARTBEAT_TIMEOUT_SECONDS` (default: 60s) is marked `UNREACHABLE` and isolated from scheduling.


#### 3. Workload Submission Stage
- A compute task is registered via `WorkloadService.create_workload` with resource requirements (CPU cores requested, RAM MB requested, network bandwidth, latency tolerance SLA, execution duration estimate, and priority).
- The workload is persisted in the database in the `PENDING` state.

#### 4. Orchestration & Placement Stage
- Workload scheduling is triggered via `WorkloadService.schedule_pending_workload`.
- The service queries candidate nodes within the target cluster, excluding cordoned nodes (`is_cordoned=True`) and inactive nodes (`UNREACHABLE`, `DEGRADED`, `DRAINING`, `OFFLINE`).
- **Active Production Path**: `HeuristicSchedulerStrategy` filters nodes lacking allocatable CPU or RAM headroom and eliminates nodes breaching the workload's latency SLA. Eligible nodes are scored using a balanced fitness function rewarding low utilization, low latency, and high health.
- **ML Benchmark Path**: Model 5 (DQN) implements `BaseSchedulerPredictor` evaluating placement feature vectors for read-only shadow benchmarks without mutating cluster state.

- If no node qualifies, `NoAvailableNodeException` is raised, keeping the workload safely in the `PENDING` queue.
- If a node is selected, `assigned_node_id` is assigned, the node's `active_workload_count` is incremented, and status transitions to `SCHEDULED`.

#### 5. Execution & Lifecycle Tracking Stage
- The workload transitions to `RUNNING` when compute execution commences.
- Upon completion, status moves to `COMPLETED`, recording `completed_at` and releasing the node's active workload count.
- If execution fails, status moves to `FAILED`. If `retry_count < max_retries`, the workload is automatically reset to `PENDING` for rescheduled placement on an alternative node.

---

## 2. State Machine Specifications

### 2.1 Workload Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING: Submission
    PENDING --> SCHEDULED: Optimal Node Assigned
    PENDING --> CANCELLED: Administrative Cancel
    SCHEDULED --> RUNNING: Task Started
    SCHEDULED --> CANCELLED: Administrative Cancel
    SCHEDULED --> FAILED: Placement Failure
    RUNNING --> COMPLETED: Execution Success
    RUNNING --> FAILED: Execution Crash / Timeout
    RUNNING --> CANCELLED: Administrative Cancel
    FAILED --> PENDING: Retry (retry_count < max_retries)
    COMPLETED --> [*]
    CANCELLED --> [*]
```

### 2.2 Node Operational State Machine

```mermaid
stateDiagram-v2
    [*] --> INITIALIZING: Node Registered
    INITIALIZING --> READY: Initial Heartbeat Received
    READY --> BUSY: Workloads Scheduled (count > 0)
    BUSY --> READY: All Workloads Completed (count == 0)
    READY --> DEGRADED: Health Score < 30.0
    BUSY --> DEGRADED: Health Score < 30.0
    DEGRADED --> READY: Health Score >= 50.0
    READY --> UNREACHABLE: Missed Heartbeats (> 60s)
    BUSY --> UNREACHABLE: Missed Heartbeats (> 60s)
    DEGRADED --> UNREACHABLE: Missed Heartbeats (> 60s)
    UNREACHABLE --> READY: Heartbeat Restored & Healthy
    READY --> DRAINING: Cordoned with Active Tasks
    BUSY --> DRAINING: Cordoned with Active Tasks
    DRAINING --> OFFLINE: Workloads Drained & Decommissioned
    OFFLINE --> [*]
```

---

## Part B: Development Workflow

Development of INTELLICLUSTER is strictly serialized across ten immutable steps. Skipping steps, combining steps, or executing future phases prematurely is **categorically forbidden**.

```text
┌────────────────────────────────────────────────────────┐
│             10-STEP DEVELOPMENT SEQUENCE               │
├───────────────────┬────────────────────────────────────┤
│ Step 1            │ Backend Foundation (Completed)     │
│ Step 2            │ REST API & HTTP Routers (Completed)│
│ Step 3            │ ML Model Training in Jupyter (Done)│
│ Step 4            │ ML Model Testing & Benchmarking (✓)│
│ Step 5            │ Frontend Application Building (✓)  │
│ Step 6 (Completed)│ Full Feature & Integration Testing │
│ Step 7 (Completed)│ UI Polish, CORS & Manifest Integrity│
│ Step 8 (Next)     │ Full Project Testing & Load Tests  │
│ Step 9 (Planned)  │ Cloud Deployment & AWS Verification│
│ Step 10 (Planned) │ Error Fixing & Final Stabilization │
└───────────────────┴────────────────────────────────────┘
```


---

## 3. Two-Prompt Engineering Cadence

Every development step follows a mandatory two-prompt protocol. No implementation may begin until the corresponding plan has been reviewed and approved by the user.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Agent as Antigravity Agent
    participant Repo as Codebase / Tests

    Note over User, Agent: PHASE 1: PLANNING & ANALYSIS
    User->>Agent: Prompt 1: Request Implementation Plan for Step N
    Agent->>Repo: Inspect current repository, code, and test suite
    Note over Agent: STRICT RULE: Read-only inspection<br/>ZERO file creations or edits
    Agent->>User: Deliver Detailed Implementation Plan & Findings

    Note over User, Agent: USER REVIEW & APPROVAL
    User->>Agent: Prompt 2: Approved, proceed with implementation

    Note over User, Agent: PHASE 2: IMPLEMENTATION & VERIFICATION
    Agent->>Repo: Implement approved code/docs within Step N scope
    Agent->>Repo: Run test suite (.venv/Scripts/pytest.exe)
    Note over Agent: Verify all tests pass & zero unintended diffs
    Agent->>User: Deliver Implementation & Verification Report
```

### Prompt 1: Plan & Analyze Only
- **Objective**: Thoroughly inspect the current repository, verify existing test suite status, analyze dependencies, and formulate a detailed implementation plan.
- **Absolute Restrictions**:
  - **DO NOT** create, modify, delete, or rename any project files.
  - **DO NOT** modify source code, tests, configurations, or database files.
  - **DO NOT** install dependencies.
- **Required Output**: Comprehensive assessment, component mappings, potential risks, and exact file changes proposed for Prompt 2.

### Prompt 2: Implement & Verify
- **Objective**: Implement precisely what was approved in Prompt 1.
- **Operational Rules**:
  - Restrict all modifications strictly to the deliverables of the active step.
  - Run the automated test suite (`.venv\Scripts\pytest.exe -v`) to confirm regressions have not been introduced.
  - Report all created or modified files, test results, and any ambiguities encountered.
  - **DO NOT** commence work on the subsequent step.
