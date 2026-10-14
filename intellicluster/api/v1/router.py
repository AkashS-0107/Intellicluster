"""
Aggregated API v1 router including all domain sub-routers.
Rate limiting is applied at this level to cover all /api/v1/ endpoints
while leaving root-level routes (/, /health) unaffected.
"""

from fastapi import APIRouter, Depends

from intellicluster.api.deps import rate_limiter
from intellicluster.api.v1.clusters import router as clusters_router
from intellicluster.api.v1.ml import router as ml_router
from intellicluster.api.v1.nodes import router as nodes_router
from intellicluster.api.v1.telemetry import router as telemetry_router
from intellicluster.api.v1.workloads import router as workloads_router

api_v1_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(rate_limiter)],
)

api_v1_router.include_router(clusters_router)
api_v1_router.include_router(nodes_router)
api_v1_router.include_router(workloads_router)
api_v1_router.include_router(telemetry_router)
api_v1_router.include_router(ml_router)
