"""Utility functions for creating standardized responses.

This module provides convenient helper functions to create standardized
responses across the Bindu application, ensuring consistency and reducing
boilerplate code.
"""

from __future__ import annotations

from time import monotonic
from typing import Any, Optional, TypeVar

from starlette.responses import JSONResponse

from bindu.common.responses import (
    ErrorCodes,
    ErrorDetail,
    PaginatedResponse,
    ResponseMetadata,
    StandardResponse,
    StreamChunk,
)

T = TypeVar("T")


class ResponseBuilder:
    """Builder class for creating standardized responses with timing.

    Usage:
        ```python
        builder = ResponseBuilder(request_id="req-123")
        # ... do work ...
        response = builder.success(
            message="Task completed",
            data={"result": "value"}
        )
        ```
    """

    def __init__(
        self,
        request_id: Optional[str] = None,
        version: str = "1.0.0",
        trace_id: Optional[str] = None,
    ):
        """Initialize response builder.

        Args:
            request_id: Request ID for correlation
            version: API/protocol version
            trace_id: Custom trace ID (auto-generated if None)
        """
        self.request_id = request_id
        self.version = version
        self.trace_id = trace_id
        self._start_time = monotonic()

    def _get_duration_ms(self) -> float:
        """Calculate duration since builder creation."""
        return round((monotonic() - self._start_time) * 1000, 2)

    def _create_metadata(self) -> ResponseMetadata:
        """Create metadata with timing and request correlation."""
        return ResponseMetadata(
            trace_id=self.trace_id,
            version=self.version,
            request_id=self.request_id,
            duration_ms=self._get_duration_ms(),
        )

    def success(
        self,
        message: str,
        data: Optional[Any] = None,
    ) -> StandardResponse:
        """Create a successful response.

        Args:
            message: Human-readable success message
            data: Response payload

        Returns:
            StandardResponse with status="success"
        """
        return StandardResponse(
            status="success",
            message=message,
            data=data,
            metadata=self._create_metadata(),
        )

    def error(
        self,
        message: str,
        error_code: str,
        error_message: Optional[str] = None,
        error_details: Optional[dict[str, Any]] = None,
        field: Optional[str] = None,
        data: Optional[Any] = None,
    ) -> StandardResponse:
        """Create an error response.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            error_message: Detailed error message (defaults to message)
            error_details: Additional error context
            field: Field name for validation errors
            data: Optional partial data

        Returns:
            StandardResponse with status="error"
        """
        return StandardResponse(
            status="error",
            message=message,
            data=data,
            metadata=self._create_metadata(),
            error=ErrorDetail(
                code=error_code,
                message=error_message or message,
                details=error_details,
                field=field,
            ),
        )


def success_response(
    message: str,
    data: Optional[Any] = None,
    request_id: Optional[str] = None,
    version: str = "1.0.0",
) -> StandardResponse:
    """Create a simple success response.

    Args:
        message: Human-readable success message
        data: Response payload
        request_id: Request ID for correlation
        version: API/protocol version

    Returns:
        StandardResponse with status="success"

    Example:
        ```python
        return success_response(
            message="Agent processed successfully",
            data={"result": agent_output}
        )
        ```
    """
    builder = ResponseBuilder(request_id=request_id, version=version)
    return builder.success(message=message, data=data)


def error_response(
    message: str,
    error_code: str = ErrorCodes.INTERNAL_ERROR,
    error_message: Optional[str] = None,
    error_details: Optional[dict[str, Any]] = None,
    field: Optional[str] = None,
    request_id: Optional[str] = None,
    version: str = "1.0.0",
) -> StandardResponse:
    """Create a simple error response.

    Args:
        message: Human-readable error message
        error_code: Machine-readable error code
        error_message: Detailed error message
        error_details: Additional error context
        field: Field name for validation errors
        request_id: Request ID for correlation
        version: API/protocol version

    Returns:
        StandardResponse with status="error"

    Example:
        ```python
        return error_response(
            message="Failed to process request",
            error_code=ErrorCodes.INVALID_INPUT,
            error_details={"reason": "Missing required field"}
        )
        ```
    """
    builder = ResponseBuilder(request_id=request_id, version=version)
    return builder.error(
        message=message,
        error_code=error_code,
        error_message=error_message,
        error_details=error_details,
        field=field,
    )


def validation_error_response(
    field: str,
    message: str,
    details: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> StandardResponse:
    """Create a validation error response.

    Args:
        field: Field that failed validation
        message: Validation error message
        details: Additional validation context
        request_id: Request ID for correlation

    Returns:
        StandardResponse with VALIDATION_ERROR code

    Example:
        ```python
        return validation_error_response(
            field="email",
            message="Invalid email format",
            details={"value": "invalid-email"}
        )
        ```
    """
    return error_response(
        message=f"Validation failed for field '{field}'",
        error_code=ErrorCodes.VALIDATION_ERROR,
        error_message=message,
        error_details=details,
        field=field,
        request_id=request_id,
    )


def not_found_response(
    resource: str,
    resource_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> StandardResponse:
    """Create a not found error response.

    Args:
        resource: Type of resource not found
        resource_id: ID of the missing resource
        request_id: Request ID for correlation

    Returns:
        StandardResponse with NOT_FOUND code

    Example:
        ```python
        return not_found_response(
            resource="agent",
            resource_id="did:bindu:example:123"
        )
        ```
    """
    message = f"{resource.capitalize()} not found"
    if resource_id:
        message += f": {resource_id}"

    return error_response(
        message=message,
        error_code=ErrorCodes.NOT_FOUND,
        error_details={"resource": resource, "resource_id": resource_id},
        request_id=request_id,
    )


def paginated_response(
    items: list[T],
    total: int,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[T]:
    """Create a paginated response.

    Args:
        items: Items for current page
        total: Total number of items across all pages
        page: Current page number (1-indexed)
        page_size: Number of items per page

    Returns:
        PaginatedResponse with pagination metadata

    Example:
        ```python
        skills = get_skills(page=1, page_size=10)
        return paginated_response(
            items=skills,
            total=total_count,
            page=1,
            page_size=10
        )
        ```
    """
    has_more = (page * page_size) < total

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


def to_json_response(
    response: StandardResponse,
    status_code: int = 200,
) -> JSONResponse:
    """Convert StandardResponse to Starlette JSONResponse.

    Args:
        response: Standardized response object
        status_code: HTTP status code

    Returns:
        JSONResponse ready to return from endpoint

    Example:
        ```python
        std_response = success_response("Done", data={...})
        return to_json_response(std_response, status_code=200)
        ```
    """
    # Automatically set status code based on response status
    if response.status == "error" and status_code == 200:
        # Map error codes to HTTP status codes
        error_code_to_status = {
            ErrorCodes.INVALID_INPUT: 400,
            ErrorCodes.VALIDATION_ERROR: 400,
            ErrorCodes.NOT_FOUND: 404,
            ErrorCodes.UNAUTHORIZED: 401,
            ErrorCodes.FORBIDDEN: 403,
            ErrorCodes.CONFLICT: 409,
            ErrorCodes.RATE_LIMITED: 429,
            ErrorCodes.PAYMENT_REQUIRED: 402,
            ErrorCodes.INTERNAL_ERROR: 500,
            ErrorCodes.SERVICE_UNAVAILABLE: 503,
            ErrorCodes.TIMEOUT: 504,
            ErrorCodes.AGENT_NOT_READY: 503,
        }

        if response.error:
            status_code = error_code_to_status.get(response.error.code, 500)

    return JSONResponse(
        content=response.model_dump(exclude_none=True),
        status_code=status_code,
    )


def stream_chunk(
    sequence: int,
    content: Any,
    is_final: bool = False,
    metadata: Optional[dict[str, Any]] = None,
) -> StreamChunk:
    """Create a stream chunk for streaming responses.

    Args:
        sequence: Chunk sequence number (0-indexed)
        content: Chunk content
        is_final: Whether this is the last chunk
        metadata: Optional chunk metadata

    Returns:
        StreamChunk object

    Example:
        ```python
        for i, chunk in enumerate(agent_stream()):
            yield stream_chunk(
                sequence=i,
                content=chunk,
                is_final=(i == total_chunks - 1)
            )
        ```
    """
    return StreamChunk(
        sequence=sequence,
        content=content,
        is_final=is_final,
        metadata=metadata,
    )
