"""
HTTP Integration Tests for Mounted IntelliCluster API v1 Routers.

Verifies the HTTP application integration layer:
- Root (/) and health (/health) probes
- Cluster management routes (/api/v1/clusters/*)
- Node management and heartbeat routes (/api/v1/nodes/*)
- Workload lifecycle and orchestration routes (/api/v1/workloads/*)
- Telemetry ingestion, query, and aggregation routes (/api/v1/telemetry/*)
- Domain exception to HTTP response mapping (404, 409, 400, 422)
- OpenAPI schema route verification
"""

import pytest
from fastapi.testclient import TestClient


# ==============================================================================
# 1. ROOT & HEALTH PROBES
# ==============================================================================

def test_http_root_endpoint(client: TestClient):
    """GET / returns 200 with system welcome and navigation paths."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "IntelliCluster" in data["message"]
    assert data["docs_url"] == "/docs"
    assert data["health_url"] == "/health"


def test_http_health_check_endpoint(client: TestClient):
    """GET /health returns 200 and healthy database status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"
    assert "timestamp" in data


# ==============================================================================
# 2. CLUSTER API ROUTES (/api/v1/clusters/*)
# ==============================================================================

def test_cluster_http_lifecycle_and_capacity(client: TestClient):
    """Exercises POST, GET, PUT, and capacity inspection for clusters."""
    # 1. Create a cluster
    create_payload = {
        "name": "prod-us-east-1",
        "description": "Primary US East production cluster",
        "status": "ACTIVE",
    }
    create_resp = client.post("/api/v1/clusters/", json=create_payload)
    assert create_resp.status_code == 201
    cluster = create_resp.json()
    assert cluster["name"] == "prod-us-east-1"
    assert cluster["status"] == "ACTIVE"
    cluster_id = cluster["id"]

    # 2. List clusters
    list_resp = client.get("/api/v1/clusters/")
    assert list_resp.status_code == 200
    clusters = list_resp.json()
    assert any(c["id"] == cluster_id for c in clusters)

    # 3. Get cluster by ID
    get_resp = client.get(f"/api/v1/clusters/{cluster_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "prod-us-east-1"

    # 4. Update cluster
    update_payload = {"description": "Updated production cluster description"}
    update_resp = client.put(f"/api/v1/clusters/{cluster_id}", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Updated production cluster description"

    # 5. Cluster capacity summary
    cap_resp = client.get(f"/api/v1/clusters/{cluster_id}/capacity")
    assert cap_resp.status_code == 200
    cap_data = cap_resp.json()
    assert cap_data["cluster_id"] == cluster_id
    assert cap_data["total_nodes"] == 0
    assert cap_data["total_cpu_cores"] == 0.0


# ==============================================================================
# 3. NODE API ROUTES (/api/v1/nodes/*)
# ==============================================================================

def test_node_http_lifecycle_cordon_and_heartbeat(client: TestClient):
    """Exercises node registration, cordon/uncordon, capacity, and heartbeat."""
    # 1. Create parent cluster
    cluster_resp = client.post("/api/v1/clusters/", json={"name": "compute-pool-01"})
    assert cluster_resp.status_code == 201
    cluster_id = cluster_resp.json()["id"]

    # 2. Register node
    node_payload = {
        "hostname": "worker-node-01.local",
        "ip_address": "10.0.1.50",
        "cluster_id": cluster_id,
        "cpu_cores": 16.0,
        "memory_mb": 32768.0,
        "storage_gb": 500.0,
        "network_bandwidth_mbps": 1000.0,
    }
    reg_resp = client.post("/api/v1/nodes/", json=node_payload)
    assert reg_resp.status_code == 201
    node = reg_resp.json()
    assert node["hostname"] == "worker-node-01.local"
    assert node["cpu_cores"] == 16.0
    assert node["is_cordoned"] is False
    node_id = node["id"]

    # 3. List nodes
    list_resp = client.get("/api/v1/nodes/")
    assert list_resp.status_code == 200
    assert any(n["id"] == node_id for n in list_resp.json())

    # 4. Get node details
    get_resp = client.get(f"/api/v1/nodes/{node_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["hostname"] == "worker-node-01.local"

    # 5. Cordon node
    cordon_resp = client.post(f"/api/v1/nodes/{node_id}/cordon")
    assert cordon_resp.status_code == 200
    assert cordon_resp.json()["is_cordoned"] is True

    # 6. Uncordon node
    uncordon_resp = client.post(f"/api/v1/nodes/{node_id}/uncordon")
    assert uncordon_resp.status_code == 200
    assert uncordon_resp.json()["is_cordoned"] is False

    # 7. Check node allocatable capacity
    cap_resp = client.get(f"/api/v1/nodes/{node_id}/capacity")
    assert cap_resp.status_code == 200
    cap_data = cap_resp.json()
    assert cap_data["total_cpu_cores"] == 16.0
    assert cap_data["allocatable_cpu_cores"] == 16.0
    assert cap_data["is_allocatable"] is True

    # 8. Ingest heartbeat with telemetry
    heartbeat_payload = {
        "cpu_usage_pct": 25.5,
        "memory_usage_mb": 8192.0,
        "memory_usage_pct": 25.0,
        "disk_usage_gb": 50.0,
        "disk_usage_pct": 10.0,
        "network_rx_mbps": 5.0,
        "network_tx_mbps": 2.5,
        "network_latency_ms": 3.2,
        "active_connections": 12,
        "reported_status": "READY",
    }
    hb_resp = client.post(f"/api/v1/nodes/{node_id}/heartbeat", json=heartbeat_payload)
    assert hb_resp.status_code == 200
    updated_node = hb_resp.json()
    assert updated_node["current_cpu_usage_pct"] == 25.5
    assert updated_node["status"] == "READY"
    assert updated_node["health_score"] > 80.0


# ==============================================================================
# 4. WORKLOAD API ROUTES (/api/v1/workloads/*)
# ==============================================================================

def test_workload_http_lifecycle_scheduling_and_transition(client: TestClient):
    """Exercises workload creation, scheduling, status transitions, and cancellation."""
    # 1. Setup cluster and a healthy node
    c_resp = client.post("/api/v1/clusters/", json={"name": "workload-cluster"})
    cluster_id = c_resp.json()["id"]

    node_payload = {
        "hostname": "sched-worker-01.local",
        "cluster_id": cluster_id,
        "cpu_cores": 8.0,
        "memory_mb": 16384.0,
    }
    n_resp = client.post("/api/v1/nodes/", json=node_payload)
    node_id = n_resp.json()["id"]

    # Send initial heartbeat to transition node to READY
    client.post(
        f"/api/v1/nodes/{node_id}/heartbeat",
        json={
            "cpu_usage_pct": 10.0,
            "memory_usage_mb": 2048.0,
            "memory_usage_pct": 12.5,
            "disk_usage_gb": 20.0,
            "disk_usage_pct": 5.0,
            "network_rx_mbps": 1.0,
            "network_tx_mbps": 1.0,
            "network_latency_ms": 2.0,
        },
    )

    # 2. Submit new workload
    workload_payload = {
        "name": "etl-pipeline-batch-42",
        "cluster_id": cluster_id,
        "workload_type": "BATCH",
        "cpu_cores_requested": 2.0,
        "memory_mb_requested": 4096.0,
        "priority": "HIGH",
    }
    wl_resp = client.post("/api/v1/workloads/", json=workload_payload)
    assert wl_resp.status_code == 201
    wl = wl_resp.json()
    assert wl["name"] == "etl-pipeline-batch-42"
    assert wl["status"] == "PENDING"
    workload_id = wl["id"]

    # 3. List workloads
    list_resp = client.get("/api/v1/workloads/")
    assert list_resp.status_code == 200
    assert any(w["id"] == workload_id for w in list_resp.json())

    # 4. Schedule workload
    sched_resp = client.post(f"/api/v1/workloads/{workload_id}/schedule")
    assert sched_resp.status_code == 200
    scheduled_wl = sched_resp.json()
    assert scheduled_wl["status"] == "SCHEDULED"
    assert scheduled_wl["assigned_node_id"] == node_id

    # 5. Transition to RUNNING
    start_resp = client.post(
        f"/api/v1/workloads/{workload_id}/status",
        json={"target_status": "RUNNING"},
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "RUNNING"

    # 6. Transition to COMPLETED
    done_resp = client.post(
        f"/api/v1/workloads/{workload_id}/status",
        json={"target_status": "COMPLETED"},
    )
    assert done_resp.status_code == 200
    assert done_resp.json()["status"] == "COMPLETED"


def test_workload_cancellation_via_http(client: TestClient):
    """Exercises cancelling a pending workload over HTTP."""
    wl_resp = client.post(
        "/api/v1/workloads/",
        json={
            "name": "cancelable-task",
            "cpu_cores_requested": 1.0,
            "memory_mb_requested": 1024.0,
        },
    )
    assert wl_resp.status_code == 201
    wl_id = wl_resp.json()["id"]

    cancel_resp = client.post(f"/api/v1/workloads/{wl_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"


# ==============================================================================
# 5. TELEMETRY API ROUTES (/api/v1/telemetry/*)
# ==============================================================================

def test_telemetry_http_ingestion_and_aggregation(client: TestClient):
    """Exercises telemetry snapshot ingestion, history, and cluster aggregation."""
    # 1. Setup cluster and node
    c_resp = client.post("/api/v1/clusters/", json={"name": "telemetry-cluster"})
    cluster_id = c_resp.json()["id"]

    n_resp = client.post(
        "/api/v1/nodes/",
        json={
            "hostname": "telemetry-node-01.local",
            "cluster_id": cluster_id,
            "cpu_cores": 8.0,
            "memory_mb": 16384.0,
        },
    )
    node_id = n_resp.json()["id"]

    # 2. Record telemetry snapshot
    snapshot_payload = {
        "cpu_usage_pct": 42.0,
        "memory_usage_mb": 4096.0,
        "memory_usage_pct": 25.0,
        "disk_usage_gb": 80.0,
        "disk_usage_pct": 16.0,
        "network_rx_mbps": 15.0,
        "network_tx_mbps": 10.0,
        "network_latency_ms": 5.5,
        "active_connections": 25,
        "reported_status": "READY",
    }
    snap_resp = client.post(f"/api/v1/telemetry/nodes/{node_id}", json=snapshot_payload)
    assert snap_resp.status_code == 201
    snapshot = snap_resp.json()
    assert snapshot["node_id"] == node_id
    assert snapshot["cpu_usage_pct"] == 42.0

    # 3. Query telemetry history for node
    history_resp = client.get(f"/api/v1/telemetry/nodes/{node_id}")
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) >= 1
    assert history[0]["node_id"] == node_id

    # 4. Query cluster aggregated metrics
    agg_resp = client.get(f"/api/v1/telemetry/clusters/{cluster_id}/aggregate")
    assert agg_resp.status_code == 200
    agg_data = agg_resp.json()
    assert agg_data["cluster_id"] == cluster_id
    assert agg_data["total_reporting_nodes"] == 1
    assert agg_data["avg_cpu_usage_pct"] == 42.0


# ==============================================================================
# 6. DOMAIN EXCEPTION HANDLER VERIFICATION
# ==============================================================================

def test_entity_not_found_mapped_to_404(client: TestClient):
    """Verifies that EntityNotFoundException maps to 404 with structured error dict."""
    resp = client.get("/api/v1/clusters/non-existent-uuid-1234")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error_code"] == "CLUSTER_NOT_FOUND"
    assert "not found" in data["message"].lower()
    assert data["details"]["entity_type"] == "Cluster"


def test_entity_already_exists_mapped_to_409(client: TestClient):
    """Verifies that EntityAlreadyExistsException maps to 409 with structured error dict."""
    payload = {"name": "duplicate-cluster-name"}
    resp1 = client.post("/api/v1/clusters/", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/clusters/", json=payload)
    assert resp2.status_code == 409
    data = resp2.json()
    assert data["error_code"] == "CLUSTER_ALREADY_EXISTS"
    assert "already exists" in data["message"].lower()


def test_invalid_state_transition_mapped_to_400(client: TestClient):
    """Verifies that InvalidStateTransitionException maps to 400 Bad Request."""
    # Create workload (starts in PENDING)
    wl_resp = client.post(
        "/api/v1/workloads/",
        json={
            "name": "invalid-transition-task",
            "cpu_cores_requested": 1.0,
            "memory_mb_requested": 512.0,
        },
    )
    wl_id = wl_resp.json()["id"]

    # Attempt illegal transition PENDING -> COMPLETED directly
    bad_resp = client.post(
        f"/api/v1/workloads/{wl_id}/status",
        json={"target_status": "COMPLETED"},
    )
    assert bad_resp.status_code == 400
    data = bad_resp.json()
    assert data["error_code"] == "INVALID_STATE_TRANSITION"
    assert "Cannot transition" in data["message"]


def test_no_available_node_mapped_to_422(client: TestClient):
    """Verifies that NoAvailableNodeException maps to 422 Unprocessable Entity."""
    # Create cluster with NO nodes
    c_resp = client.post("/api/v1/clusters/", json={"name": "empty-cluster"})
    cluster_id = c_resp.json()["id"]

    # Submit workload requiring resources
    wl_resp = client.post(
        "/api/v1/workloads/",
        json={
            "name": "unschedulable-job",
            "cluster_id": cluster_id,
            "cpu_cores_requested": 64.0,
            "memory_mb_requested": 128000.0,
        },
    )
    wl_id = wl_resp.json()["id"]

    # Attempt to schedule when no candidate node exists
    sched_resp = client.post(f"/api/v1/workloads/{wl_id}/schedule")
    assert sched_resp.status_code == 422
    data = sched_resp.json()
    assert data["error_code"] == "NO_AVAILABLE_NODE"
    assert "No eligible node" in data["message"]


# ==============================================================================
# 7. OPENAPI SCHEMA INTEGRATION
# ==============================================================================

def test_openapi_schema_contains_all_api_routes(client: TestClient):
    """Verifies that the mounted application exposes all domain routes in OpenAPI schema."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]

    # Root and Health
    assert "/" in paths
    assert "/health" in paths

    # Clusters
    assert "/api/v1/clusters/" in paths
    assert "/api/v1/clusters/{cluster_id}" in paths
    assert "/api/v1/clusters/{cluster_id}/capacity" in paths

    # Nodes
    assert "/api/v1/nodes/" in paths
    assert "/api/v1/nodes/{node_id}" in paths
    assert "/api/v1/nodes/{node_id}/heartbeat" in paths
    assert "/api/v1/nodes/{node_id}/cordon" in paths
    assert "/api/v1/nodes/{node_id}/uncordon" in paths
    assert "/api/v1/nodes/{node_id}/capacity" in paths

    # Workloads
    assert "/api/v1/workloads/" in paths
    assert "/api/v1/workloads/{workload_id}" in paths
    assert "/api/v1/workloads/{workload_id}/schedule" in paths
    assert "/api/v1/workloads/{workload_id}/status" in paths
    assert "/api/v1/workloads/{workload_id}/cancel" in paths

    # Telemetry
    assert "/api/v1/telemetry/nodes/{node_id}" in paths
    assert "/api/v1/telemetry/clusters/{cluster_id}/aggregate" in paths
