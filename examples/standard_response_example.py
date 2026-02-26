"""Example demonstrating standardized response usage.

This example shows how to use the standardized response schema
in a simple agent endpoint.
"""

from starlette.requests import Request
from starlette.responses import Response

from bindu.common.responses import ErrorCodes
from bindu.utils.response_utils import (
    ResponseBuilder,
    success_response,
    error_response,
    validation_error_response,
    not_found_response,
    to_json_response,
)


async def simple_success_example() -> Response:
    """Example: Simple success response."""
    
    response = success_response(
        message="Operation completed successfully",
        data={"result": "Hello, world!", "count": 42}
    )
    
    return to_json_response(response)


async def error_example() -> Response:
    """Example: Error response with details."""
    
    response = error_response(
        message="Failed to process request",
        error_code=ErrorCodes.INVALID_INPUT,
        error_details={
            "reason": "Missing required field",
            "field": "message"
        }
    )
    
    # Automatically returns 400 Bad Request
    return to_json_response(response)


async def validation_example() -> Response:
    """Example: Validation error."""
    
    response = validation_error_response(
        field="email",
        message="Invalid email format",
        details={"value": "not-an-email", "expected": "user@example.com"}
    )
    
    # Automatically returns 400 Bad Request
    return to_json_response(response)


async def not_found_example() -> Response:
    """Example: Resource not found."""
    
    response = not_found_response(
        resource="agent",
        resource_id="did:bindu:example:123"
    )
    
    # Automatically returns 404 Not Found
    return to_json_response(response)


async def builder_example(request: Request) -> Response:
    """Example: Using ResponseBuilder with automatic timing."""
    
    # Extract request ID for correlation
    request_id = request.headers.get("X-Request-ID")
    
    # Create builder (starts timing automatically)
    builder = ResponseBuilder(request_id=request_id, version="1.0.0")
    
    try:
        # Parse and validate request
        data = await request.json()
        
        if not data.get("message"):
            return to_json_response(
                builder.error(
                    message="Validation failed",
                    error_code=ErrorCodes.VALIDATION_ERROR,
                    error_message="Message is required",
                    field="message"
                )
            )
        
        # Process the request
        result = process_message(data["message"])
        
        # Return success (duration automatically tracked)
        return to_json_response(
            builder.success(
                message="Message processed successfully",
                data={"result": result}
            )
        )
        
    except ValueError as e:
        # Validation error
        return to_json_response(
            builder.error(
                message="Invalid input",
                error_code=ErrorCodes.INVALID_INPUT,
                error_details={"exception": str(e)}
            )
        )
        
    except Exception as e:
        # Internal error
        return to_json_response(
            builder.error(
                message="Internal server error",
                error_code=ErrorCodes.INTERNAL_ERROR,
                error_details={
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                }
            )
        )


def process_message(message: str) -> str:
    """Dummy message processing function."""
    return f"Processed: {message}"


# Example response formats:

SUCCESS_RESPONSE_EXAMPLE = {
    "status": "success",
    "message": "Operation completed successfully",
    "data": {
        "result": "Hello, world!",
        "count": 42
    },
    "metadata": {
        "trace_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2026-02-27T10:30:00Z",
        "version": "1.0.0",
        "request_id": "req-123",
        "duration_ms": 42.5
    }
}

ERROR_RESPONSE_EXAMPLE = {
    "status": "error",
    "message": "Failed to process request",
    "data": None,
    "metadata": {
        "trace_id": "550e8400-e29b-41d4-a716-446655440001",
        "timestamp": "2026-02-27T10:30:00Z",
        "version": "1.0.0"
    },
    "error": {
        "code": "INVALID_INPUT",
        "message": "Missing required field",
        "details": {
            "reason": "Missing required field",
            "field": "message"
        }
    }
}

VALIDATION_ERROR_EXAMPLE = {
    "status": "error",
    "message": "Validation failed for field 'email'",
    "data": None,
    "metadata": {
        "trace_id": "550e8400-e29b-41d4-a716-446655440002",
        "timestamp": "2026-02-27T10:30:00Z",
        "version": "1.0.0"
    },
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid email format",
        "field": "email",
        "details": {
            "value": "not-an-email",
            "expected": "user@example.com"
        }
    }
}
