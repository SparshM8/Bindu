"""Standardized response models for Bindu agent runtime.

This module provides a unified response structure across all agent features
(streaming, integrations, transports) to improve frontend integration,
debugging, observability, and transport-layer consistency.

Response Format:
    All agent responses follow a consistent schema with:
    - status: success/error indicator
    - message: human-readable description
    - data: response payload
    - metadata: trace_id, timestamp, version
    - error: error details when applicable
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, Literal, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

# Type variable for generic response data
T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Detailed error information for failed responses.

    Attributes:
        code: Error code (e.g., "INVALID_INPUT", "INTERNAL_ERROR")
        message: Human-readable error message
        details: Additional error context (stack trace, field errors, etc.)
        field: Field name for validation errors
    """

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(
        None, description="Additional error context"
    )
    field: Optional[str] = Field(None, description="Field name for validation errors")


class ResponseMetadata(BaseModel):
    """Metadata included in every response for observability.

    Attributes:
        trace_id: Unique identifier for request tracing
        timestamp: ISO 8601 timestamp when response was generated
        version: API/agent version
        request_id: Original request identifier (for correlation)
        duration_ms: Request processing duration in milliseconds
    """

    trace_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique trace ID for request tracking",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Response generation timestamp (ISO 8601)",
    )
    version: str = Field(default="1.0.0", description="API or protocol version")
    request_id: Optional[str] = Field(
        None, description="Original request ID for correlation"
    )
    duration_ms: Optional[float] = Field(
        None, description="Request processing time in milliseconds"
    )


class StandardResponse(BaseModel, Generic[T]):
    """Standardized response model for all agent operations.

    This is the base response format used across all endpoints, handlers,
    and transport layers to ensure consistency.

    Attributes:
        status: Response status ("success" or "error")
        message: Human-readable status message
        data: Response payload (type varies by endpoint)
        metadata: Observability metadata (trace_id, timestamp, etc.)
        error: Error details (only present when status="error")

    Examples:
        Success response:
        ```python
        response = StandardResponse(
            status="success",
            message="Agent processed message successfully",
            data={"result": "Hello, world!"},
            metadata=ResponseMetadata()
        )
        ```

        Error response:
        ```python
        response = StandardResponse(
            status="error",
            message="Failed to process message",
            data=None,
            metadata=ResponseMetadata(),
            error=ErrorDetail(
                code="INVALID_INPUT",
                message="Message content is required"
            )
        )
        ```
    """

    status: Literal["success", "error"] = Field(
        ..., description="Response status indicator"
    )
    message: str = Field(..., description="Human-readable status message")
    data: Optional[T] = Field(None, description="Response payload")
    metadata: ResponseMetadata = Field(
        default_factory=ResponseMetadata,
        description="Observability and tracing metadata",
    )
    error: Optional[ErrorDetail] = Field(
        None, description="Error details (present only when status='error')"
    )

    @computed_field
    @property
    def success(self) -> bool:
        """Convenience property to check if response is successful."""
        return self.status == "success"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "success",
                    "message": "Operation completed successfully",
                    "data": {"result": "example data"},
                    "metadata": {
                        "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2026-02-27T10:30:00Z",
                        "version": "1.0.0",
                    },
                },
                {
                    "status": "error",
                    "message": "Operation failed",
                    "data": None,
                    "metadata": {
                        "trace_id": "550e8400-e29b-41d4-a716-446655440001",
                        "timestamp": "2026-02-27T10:30:00Z",
                        "version": "1.0.0",
                    },
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid input parameters",
                        "details": {"field": "email", "issue": "Invalid format"},
                    },
                },
            ]
        }
    }


class StreamChunk(BaseModel):
    """Standardized format for streaming responses.

    Attributes:
        chunk_id: Unique identifier for this chunk
        sequence: Sequence number in the stream
        content: Chunk content
        is_final: Whether this is the last chunk
        metadata: Chunk metadata
    """

    chunk_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique chunk identifier"
    )
    sequence: int = Field(..., description="Chunk sequence number (0-indexed)")
    content: Any = Field(..., description="Chunk content")
    is_final: bool = Field(False, description="Indicates last chunk in stream")
    metadata: Optional[dict[str, Any]] = Field(None, description="Chunk metadata")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized format for paginated data responses.

    Attributes:
        items: List of items for current page
        total: Total number of items across all pages
        page: Current page number (1-indexed)
        page_size: Number of items per page
        has_more: Whether more pages are available
    """

    items: list[T] = Field(..., description="Items for current page")
    total: int = Field(..., description="Total items across all pages")
    page: int = Field(1, ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.page_size - 1) // self.page_size


# Common error codes for consistency
class ErrorCodes:
    """Standard error codes used across the application."""

    # Client errors (4xx)
    INVALID_INPUT = "INVALID_INPUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    PAYMENT_REQUIRED = "PAYMENT_REQUIRED"

    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"

    # Agent-specific errors
    AGENT_NOT_READY = "AGENT_NOT_READY"
    HANDLER_ERROR = "HANDLER_ERROR"
    PROTOCOL_ERROR = "PROTOCOL_ERROR"
    EXTENSION_ERROR = "EXTENSION_ERROR"
