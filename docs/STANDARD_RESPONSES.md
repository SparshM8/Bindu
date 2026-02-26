# Standardized Response Schema

## Overview

Bindu uses a **standardized response format** across all agent features (streaming, integrations, transports) to improve:

- ✅ **Frontend integration** - Consistent structure for UI components
- ✅ **Debugging and logging** - Traceable requests with trace_id and timestamps
- ✅ **Transport consistency** - Works seamlessly with HTTP, gRPC, WebSocket
- ✅ **Observability** - Built-in support for tracing and monitoring

## Response Structure

All responses follow this standardized schema:

```json
{
  "status": "success" | "error",
  "message": "Human-readable message",
  "data": { /* Response payload */ },
  "metadata": {
    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-02-27T10:30:00Z",
    "version": "1.0.0",
    "request_id": "req-123",
    "duration_ms": 42.5
  },
  "error": {  /* Only present for errors */
    "code": "ERROR_CODE",
    "message": "Detailed error message",
    "details": { /* Additional context */ },
    "field": "fieldName"  /* For validation errors */
  }
}
```

## Quick Start

### Success Response

```python
from bindu.utils.response_utils import success_response, to_json_response

# Simple success
response = success_response(
    message="Agent processed message successfully",
    data={"result": "Hello, world!"}
)

# Convert to JSON for HTTP endpoint
return to_json_response(response)
```

### Error Response

```python
from bindu.utils.response_utils import error_response
from bindu.common.responses import ErrorCodes

# Error with details
response = error_response(
    message="Failed to process request",
    error_code=ErrorCodes.INVALID_INPUT,
    error_details={"reason": "Missing required field 'message'"}
)

return to_json_response(response)
```

### Using the Response Builder

For complex workflows with timing:

```python
from bindu.utils.response_utils import ResponseBuilder, to_json_response

# Create builder with request correlation
builder = ResponseBuilder(request_id="req-123", version="1.0.0")

try:
    # Do work...
    result = process_agent_request()
    
    # Success (duration automatically tracked)
    response = builder.success(
        message="Processing completed",
        data=result
    )
except ValueError as e:
    # Error (duration automatically tracked)
    response = builder.error(
        message="Processing failed",
        error_code=ErrorCodes.VALIDATION_ERROR,
        error_details={"exception": str(e)}
    )

return to_json_response(response)
```

## Common Response Helpers

### Validation Errors

```python
from bindu.utils.response_utils import validation_error_response

response = validation_error_response(
    field="email",
    message="Invalid email format",
    details={"value": "not-an-email"}
)
```

### Not Found Errors

```python
from bindu.utils.response_utils import not_found_response

response = not_found_response(
    resource="agent",
    resource_id="did:bindu:example:123"
)
```

### Paginated Responses

```python
from bindu.utils.response_utils import paginated_response

skills = get_skills(page=1, limit=10)

response = paginated_response(
    items=skills,
    total=total_count,
    page=1,
    page_size=10
)

# Response includes: items, total, page, page_size, has_more, total_pages
```

### Stream Chunks

```python
from bindu.utils.response_utils import stream_chunk

for i, chunk in enumerate(agent_stream()):
    yield stream_chunk(
        sequence=i,
        content=chunk,
        is_final=(i == total_chunks - 1),
        metadata={"tokens": len(chunk)}
    )
```

## Error Codes

Standard error codes ensure consistency:

```python
from bindu.common.responses import ErrorCodes

# Client errors (4xx)
ErrorCodes.INVALID_INPUT        # 400
ErrorCodes.VALIDATION_ERROR     # 400
ErrorCodes.UNAUTHORIZED         # 401
ErrorCodes.FORBIDDEN            # 403
ErrorCodes.NOT_FOUND            # 404
ErrorCodes.CONFLICT             # 409
ErrorCodes.PAYMENT_REQUIRED     # 402
ErrorCodes.RATE_LIMITED         # 429

# Server errors (5xx)
ErrorCodes.INTERNAL_ERROR       # 500
ErrorCodes.SERVICE_UNAVAILABLE  # 503
ErrorCodes.TIMEOUT              # 504

# Agent-specific
ErrorCodes.AGENT_NOT_READY
ErrorCodes.HANDLER_ERROR
ErrorCodes.PROTOCOL_ERROR
ErrorCodes.EXTENSION_ERROR
```

## Backward Compatibility

Endpoints support both legacy and standard formats:

```python
# Legacy format (default)
GET /health

# Standard format (opt-in)
GET /health?format=standard
```

This allows gradual migration without breaking existing clients.

## Example: Full Endpoint

```python
from starlette.requests import Request
from starlette.responses import Response
from bindu.utils.response_utils import ResponseBuilder, to_json_response, error_response
from bindu.common.responses import ErrorCodes

async def my_endpoint(request: Request) -> Response:
    """Example endpoint using standardized responses."""
    
    # Extract request ID for correlation
    request_id = request.headers.get("X-Request-ID")
    
    # Create response builder with timing
    builder = ResponseBuilder(request_id=request_id)
    
    try:
        # Parse request
        data = await request.json()
        
        # Validate
        if not data.get("message"):
            return to_json_response(
                error_response(
                    message="Validation failed",
                    error_code=ErrorCodes.VALIDATION_ERROR,
                    error_details={"field": "message", "issue": "required"},
                    field="message",
                    request_id=request_id
                )
            )
        
        # Process
        result = await process_message(data["message"])
        
        # Success
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
                error_details={"exception": type(e).__name__}
            )
        )
```

## Frontend Integration

Standard responses make frontend code simpler:

```typescript
interface StandardResponse<T> {
  status: 'success' | 'error';
  message: string;
  data?: T;
  metadata: {
    trace_id: string;
    timestamp: string;
    version: string;
    request_id?: string;
    duration_ms?: number;
  };
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
    field?: string;
  };
}

// Universal error handling
async function callAgent<T>(endpoint: string, body: any): Promise<T> {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  
  const result: StandardResponse<T> = await response.json();
  
  if (result.status === 'error') {
    console.error(`[${result.metadata.trace_id}] ${result.error?.code}: ${result.error?.message}`);
    throw new Error(result.message);
  }
  
  return result.data!;
}
```

## Observability Integration

Standard responses include trace_id for correlation:

```python
# In logging
logger.info(
    "Request processed",
    extra={
        "trace_id": response.metadata.trace_id,
        "duration_ms": response.metadata.duration_ms,
        "status": response.status
    }
)

# In Sentry/monitoring
import sentry_sdk

with sentry_sdk.start_transaction(
    op="agent.process",
    name="message/send"
) as transaction:
    transaction.set_tag("trace_id", builder.trace_id)
    # ... process request ...
    response = builder.success(...)
```

## Migration Guide

### Step 1: Update Imports

```python
# Add new imports
from bindu.utils.response_utils import success_response, error_response, to_json_response
from bindu.common.responses import ErrorCodes
```

### Step 2: Wrap Existing Responses

```python
# Before
return JSONResponse({"result": data})

# After
return to_json_response(
    success_response(
        message="Operation completed",
        data={"result": data}
    )
)
```

### Step 3: Standardize Error Handling

```python
# Before
return JSONResponse(
    {"error": "Not found"},
    status_code=404
)

# After
return to_json_response(
    error_response(
        message="Resource not found",
        error_code=ErrorCodes.NOT_FOUND
    )
)
```

## Best Practices

1. **Always use meaningful messages** - Write human-readable messages for debugging
2. **Include request_id** - Pass request IDs for request correlation
3. **Use standard error codes** - Don't create custom codes unless necessary
4. **Add context to errors** - Use `error_details` for debugging information
5. **Track timing** - Use `ResponseBuilder` for automatic duration tracking
6. **Log trace_id** - Include trace_id in all logs for request tracking

## Testing

```python
def test_endpoint_success():
    """Test endpoint returns standardized success response."""
    response = await my_endpoint(request)
    
    data = response.json()
    
    # Check standard structure
    assert data["status"] == "success"
    assert "message" in data
    assert "data" in data
    assert "metadata" in data
    
    # Check metadata
    assert "trace_id" in data["metadata"]
    assert "timestamp" in data["metadata"]
    assert data["metadata"]["duration_ms"] > 0

def test_endpoint_error():
    """Test endpoint returns standardized error response."""
    response = await my_endpoint(invalid_request)
    
    data = response.json()
    
    # Check error structure
    assert data["status"] == "error"
    assert "error" in data
    assert data["error"]["code"] == ErrorCodes.VALIDATION_ERROR
```

## Resources

- **Models**: `bindu/common/responses.py`
- **Utilities**: `bindu/utils/response_utils.py`
- **Tests**: `tests/unit/test_standard_responses.py`, `tests/unit/test_response_utils.py`
- **Example**: `bindu/server/endpoints/health.py` (supports both formats)

## Support

For questions or suggestions about the standardized response schema:
- 💬 [Discord](https://discord.gg/3w5zuYUuwt)
- 🐛 [GitHub Issues](https://github.com/getbindu/Bindu/issues)
