"""
Common Pydantic models, pagination schemas, and base configurations.
"""

from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema enabling ORM mode attribute access and clean serialization."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class PaginationParams(BaseSchema):
    """Standard query parameters for pagination."""

    skip: int = Field(default=0, ge=0, description="Offset of items to skip")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum number of items to return")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Standard generic envelope for paginated lists."""

    items: list[T]
    total: int = Field(ge=0, description="Total count of available matching items")
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)


class StatusResponse(BaseSchema):
    """Generic status/acknowledgment response."""

    success: bool = True
    message: str
    details: Optional[dict[str, object]] = None


class ErrorResponse(BaseSchema):
    """Standard error response envelope for API consumers."""

    error_code: str
    message: str
    details: Optional[dict[str, object]] = None
