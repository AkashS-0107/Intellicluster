"""
Global exception handlers mapping domain exceptions to structured HTTP error responses.
Registered on the FastAPI application to provide consistent error contracts.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from intellicluster.core.exceptions import (
    CapacityExceededException,
    ConfigurationException,
    EntityAlreadyExistsException,
    EntityNotFoundException,
    IntelliClusterException,
    InvalidStateTransitionException,
    NoAvailableNodeException,
)
from intellicluster.core.logging import logger


async def entity_not_found_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """EntityNotFoundException and subclasses → 404 Not Found."""
    content = exc.to_dict() if isinstance(exc, IntelliClusterException) else {"message": str(exc)}
    return JSONResponse(status_code=404, content=content)


async def entity_already_exists_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """EntityAlreadyExistsException and subclasses → 409 Conflict."""
    content = exc.to_dict() if isinstance(exc, IntelliClusterException) else {"message": str(exc)}
    return JSONResponse(status_code=409, content=content)


async def invalid_state_transition_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """InvalidStateTransitionException → 400 Bad Request (per TRD §7)."""
    content = exc.to_dict() if isinstance(exc, IntelliClusterException) else {"message": str(exc)}
    return JSONResponse(status_code=400, content=content)


async def capacity_exceeded_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """CapacityExceededException → 400 Bad Request."""
    content = exc.to_dict() if isinstance(exc, IntelliClusterException) else {"message": str(exc)}
    return JSONResponse(status_code=400, content=content)


async def no_available_node_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """NoAvailableNodeException → 422 Unprocessable Entity."""
    content = exc.to_dict() if isinstance(exc, IntelliClusterException) else {"message": str(exc)}
    return JSONResponse(status_code=422, content=content)


async def configuration_error_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """ConfigurationException → 500 Internal Server Error."""
    logger.error("Configuration error: %s", str(exc))
    content = exc.to_dict() if isinstance(exc, IntelliClusterException) else {"message": str(exc)}
    return JSONResponse(status_code=500, content=content)


async def intellicluster_error_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """Catch-all for unhandled IntelliClusterException subclasses → 500."""
    logger.error("Domain error: %s", str(exc), exc_info=True)
    content = exc.to_dict() if isinstance(exc, IntelliClusterException) else {"message": str(exc)}
    return JSONResponse(status_code=500, content=content)


async def unhandled_exception_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """
    Catch-all for truly unexpected exceptions → 500.
    Returns a safe generic message without exposing internals.
    Does not interfere with FastAPI's built-in HTTPException or
    RequestValidationError handlers (Starlette resolves via MRO).
    """
    logger.error("Unexpected error on %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred.",
            "details": {},
        },
    )


async def model_rejected_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """ModelRejectedException → 403 Forbidden."""
    content = exc.to_dict() if isinstance(exc, IntelliClusterException) else {"message": str(exc)}
    return JSONResponse(status_code=403, content=content)


async def insufficient_history_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """InsufficientHistoryException → 422 Unprocessable Entity."""
    content = exc.to_dict() if isinstance(exc, IntelliClusterException) else {"message": str(exc)}
    return JSONResponse(status_code=422, content=content)


async def model_not_ready_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """ModelNotReadyException → 503 Service Unavailable."""
    content = exc.to_dict() if isinstance(exc, IntelliClusterException) else {"message": str(exc)}
    return JSONResponse(status_code=503, content=content)


async def simulator_already_running_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """SimulatorAlreadyRunningException → 409 Conflict."""
    content = exc.to_dict() if isinstance(exc, IntelliClusterException) else {"message": str(exc)}
    return JSONResponse(status_code=409, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all domain exception → HTTP response handlers on the FastAPI application.
    Starlette resolves handlers by walking the exception MRO, so registration
    order does not affect specificity—but specific types must be registered
    individually to receive their intended status codes.
    """
    from intellicluster.ml.services import (
        InsufficientHistoryException,
        ModelNotReadyException,
        ModelRejectedException,
    )
    from intellicluster.services.telemetry_simulator_service import (
        SimulatorAlreadyRunningException,
    )

    app.add_exception_handler(EntityNotFoundException, entity_not_found_handler)
    app.add_exception_handler(EntityAlreadyExistsException, entity_already_exists_handler)
    app.add_exception_handler(SimulatorAlreadyRunningException, simulator_already_running_handler)
    app.add_exception_handler(InvalidStateTransitionException, invalid_state_transition_handler)
    app.add_exception_handler(CapacityExceededException, capacity_exceeded_handler)
    app.add_exception_handler(NoAvailableNodeException, no_available_node_handler)
    app.add_exception_handler(ConfigurationException, configuration_error_handler)
    app.add_exception_handler(ModelRejectedException, model_rejected_handler)
    app.add_exception_handler(InsufficientHistoryException, insufficient_history_handler)
    app.add_exception_handler(ModelNotReadyException, model_not_ready_handler)
    app.add_exception_handler(IntelliClusterException, intellicluster_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
