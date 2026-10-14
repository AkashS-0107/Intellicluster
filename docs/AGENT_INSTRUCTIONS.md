# Agent Instructions & Development Guardrails (AGENT_INSTRUCTIONS)

```text
Project: INTELLICLUSTER
Document: AGENT_INSTRUCTIONS.md
Version: 1.0
Status: Approved Baseline
```

---

## 1. Primacy of Documentation (Authoritative Source of Truth)

This document establishes strict behavioral constraints, scope limitations, and engineering guardrails for any AI agent (including Antigravity) working on the INTELLICLUSTER project.

Before proposing an implementation plan or executing any code modification, the agent **MUST** review the four authoritative project documents:

1. [`docs/TRD.md`](file:///e:/career/INTELLICLUSTER/docs/TRD.md): Technical Requirements Document (System architecture, schemas, and technical contracts).
2. [`docs/PRD.md`](file:///e:/career/INTELLICLUSTER/docs/PRD.md): Product Requirements Document (Functional scope, personas, and non-goals).
3. [`docs/WORKFLOW.md`](file:///e:/career/INTELLICLUSTER/docs/WORKFLOW.md): System and Development Workflow (Runtime pipeline, state machines, and 10-step cadence).
4. [`docs/AGENT_INSTRUCTIONS.md`](file:///e:/career/INTELLICLUSTER/docs/AGENT_INSTRUCTIONS.md): Agent Guardrails (Negative constraints and change control protocols).

These documents represent the approved baseline and supersede all generic AI assumptions, external best practices, or default web application scaffolds.

---

## 2. Absolute Architectural Restrictions (Negative Constraints)

The agent is **STRICTLY FORBIDDEN** from making autonomous architectural or infrastructure alterations. Specifically, the agent must **NOT**:

1. **Replace Core Technologies**:
   - Do NOT replace **Python**, **FastAPI**, **SQLAlchemy**, **Pydantic**, or **pytest**.
   - Do NOT replace **SQLite** with another database engine during Steps 1 through 8.
2. **Introduce Distributed Infrastructure**:
   - Do NOT introduce message queues or brokers (**Redis**, **Kafka**, **RabbitMQ**, **Celery**).
   - Do NOT introduce container orchestration frameworks (**Kubernetes**, **K3s**, **Nomad**).
   - Do NOT introduce microservice splits; the application must remain a clean modular service within the approved directory structure.
3. **Premature Cloud Infrastructure**:
   - Do NOT add AWS SDKs (`boto3`) or invoke cloud APIs prior to **Step 9**.
   - Do NOT add cloud deployment templates (Terraform, CloudFormation, CDK) prior to Step 9.
4. **Mutate Relational Schemas Unilaterally**:
   - Do NOT add, delete, or rename columns/tables in ORM models unless explicitly instructed in an approved step prompt.
   - Do NOT bypass the established `UUIDPrimaryKeyMixin` or `TimestampMixin`.
5. **Merge Unrelated ML Datasets**:
   - Do NOT attempt to combine disparate data sources (`ai4i2020.csv`, `embedded_system_network_security_dataset.csv`, `Load Balancing Improved.csv`, `logs-dataset.ipynb`, etc.) into a single dataframe or monolithic model.
6. **Rewrite Working Components**:
   - Do NOT refactor or rewrite functioning modules simply because an alternative idiom or style is preferred.
   - Do NOT perform opportunistic refactoring outside the explicit boundaries of the active step.

---

## 3. Active-Step Scope Confinement

Development is strictly partitioned into ten sequential steps. The agent is authorized to modify only the files directly pertinent to the **currently active step**:

```text
Step 1: Backend Foundation (Completed & Verified)
Step 2: REST API Endpoints (Completed & Verified)
Step 3: ML Model Training using Jupyter (Completed & Verified)
Step 4: Testing of all ML Models (Completed & Verified)
Step 5: Frontend Application Building (Completed & Verified)
Step 6: Testing All Features & End-to-End Validation (Completed & Verified Baseline)
Step 7: UI/UX Redesign & Optimization (Current Step — AI-Slop Cleanup & UI Hardening)
Step 8: Full Project Testing & Performance Benchmarking (Next Step)
Step 9: Cloud Deployment & Verification (Planned)
Step 10: Error Fixing & Final Stabilization (Planned)
```

### Strict Step Boundary Rules:
- During **Step 7 (Current)**: Restrict work to UI/UX polish, domain-appropriate copy, AI-slop cleanup, and documentation synchronization. DO NOT alter backend ML weights, database schemas, API contracts, or scheduling algorithms.
- During **Step 8**: Restrict work to comprehensive load, concurrency, and end-to-end performance benchmarking.
- During **Step 9**: Restrict work to cloud infrastructure and AWS deployment verification.
- **Never implement future phases early** simply because their architecture is visible in the roadmap.


---

## 4. Prompt Discipline: The Two-Prompt Cadence

Every development step is split into two distinct phases. The agent must strictly respect the mode of the active prompt:

```text
┌────────────────────────────────────────────────────────┐
│  Prompt 1: READ → ANALYZE → PLAN                       │
│  - Inspect repository and tests                        │
│  - Formulate detailed implementation plan              │
│  - ZERO file modifications, ZERO code changes          │
├────────────────────────────────────────────────────────┤
│  Prompt 2: VERIFY PLAN → IMPLEMENT → TEST → REPORT     │
│  - Implement approved changes only                     │
│  - Run automated test suite (.venv\Scripts\pytest.exe) │
│  - Verify zero regressions and report results          │
└────────────────────────────────────────────────────────┘
```

If the user prompt is **Prompt 1 (Planning)**:
- The agent must **NOT** create, edit, delete, or move any project files.
- The agent must **NOT** install dependencies.
- The response must consist solely of analysis, repository findings, and an implementation plan.

If the user prompt is **Prompt 2 (Implementation)**:
- The agent implements the plan approved in Prompt 1.
- All modified code must be verified using the test suite.

---

## 5. Ambiguity & Conflict Escalation Protocol

If the agent detects a contradiction between:
- Existing code
- TRD.md
- PRD.md
- WORKFLOW.md
- AGENT_INSTRUCTIONS.md
- The user's active prompt

The agent is **STRICTLY FORBIDDEN** from silently choosing an interpretation or making an autonomous assumption. The agent must immediately pause and output an escalation block:

```text
[CONFLICT ESCALATION DETECTED]
1. Conflicting Requirements: <Detailed description of contradictory statements>
2. Affected Files / Components: <Specific file paths, classes, or methods impacted>
3. Potential Interpretations:
   - Interpretation A: <Description and implications>
   - Interpretation B: <Description and implications>
4. Recommended Resolution: <Agent's technical recommendation and rationale>
5. Required User Decision: <Explicit question requiring user confirmation>
```

After presenting this escalation block, the agent must **wait for explicit user direction** before writing any code.

---

## 6. Dependency & Package Governance

1. **No Autonomous Package Installation**: The agent must never run `pip install`, `npm install`, or update `requirements.txt` / `pyproject.toml` unless package additions are explicitly defined and approved in the active step plan.
2. **Phase-Gated Dependencies**:
   - Zero ML libraries (`torch`, `scikit-learn`, `xgboost`, `pandas`) in Step 1 and 2.
   - Zero cloud SDKs (`boto3`) in Steps 1 through 8.
   - Zero message queue clients (`redis`, `celery`, `pika`) unless an approved future requirement introduces them.
3. **Minimalist Footprint**: Favor standard library solutions and existing installed libraries before recommending third-party packages.

---

## 7. Testing & Verification Discipline

1. **Zero Test Bypassing**: The agent must **NEVER** delete, comment out, or weaken an existing test assertion simply to make a build pass.
2. **Regression Verification**: Every code modification must be verified by running the test suite:
   ```powershell
   .venv\Scripts\pytest.exe -v
   ```
3. **Current Verified Baseline**: All **148 backend tests** and **55 frontend tests** must continue to pass cleanly.

4. **Meaningful Test Coverage**: When writing new tests (e.g. for Step 2 API routes), tests must assert actual behavior, error branches, and edge cases. Do not write trivial tests to satisfy artificial coverage metrics.

---

## 8. Documentation Integrity & Maintenance

1. **Documentation Reflects Truth**: Documentation describes approved architecture. Code must conform to documentation.
2. **No Post-Hoc Justification**: The agent must never rewrite or distort documentation to retroactively justify unapproved architectural decisions or sloppy code.
3. **Explicit Documentation Edits**: Documentation may be updated only when an architectural change has been explicitly reviewed and approved by the user through the two-prompt cadence.
