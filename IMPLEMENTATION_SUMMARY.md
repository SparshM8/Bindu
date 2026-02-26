# Standardized Response Schema Implementation

## Summary

This implementation introduces a **unified response structure** for all agent operations across Bindu, addressing the issue of inconsistent response formats across different features (streaming, integrations, transports).

## What Was Implemented

### 1. **Core Response Models** (`bindu/common/responses.py`)

- **`StandardResponse`** - Generic response model with:
  - `status`: "success" or "error"
  - `message`: Human-readable description
  - `data`: Response payload (generic type)
  - `metadata`: Observability fields (trace_id, timestamp, version, duration_ms)
  - `error`: Error details when applicable

- **`ErrorDetail`** - Structured error information:
  - `code`: Machine-readable error code
  - `message`: Human-readable error message  
  - `details`: Additional context
  - `field`: Field name for validation errors

- **`ResponseMetadata`** - Observability metadata:
  - `trace_id`: Unique request identifier (auto-generated UUID)
  - `timestamp`: ISO 8601 timestamp
  - `version`: API/protocol version
  - `request_id`: Original request ID for correlation
  - `duration_ms`: Request processing time

- **`PaginatedResponse`** - Standardized pagination
- **`StreamChunk`** - Standardized streaming format
- **`ErrorCodes`** - Standard error code constants

### 2. **Utility Functions** (`bindu/utils/response_utils.py`)

Convenience helpers to reduce boilerplate:

- `success_response()` - Quick success response creation
- `error_response()` - Quick error response creation
- `validation_error_response()` - Validation errors
- `not_found_response()` - Resource not found errors
- `paginated_response()` - Paginated data
- `stream_chunk()` - Streaming chunks
- `to_json_response()` - Convert to Starlette JSONResponse with auto status codes
- `ResponseBuilder` - Builder class with automatic timing

### 3. **Backward Compatibility**

Updated `/health` endpoint to demonstrate:
- **Default behavior**: Returns legacy format (unchanged)
- **Opt-in standard format**: `?format=standard` query parameter
- **No breaking changes**: Existing clients continue to work

### 4. **Comprehensive Tests**

- `tests/unit/test_standard_responses.py` - 25+ tests for models
- `tests/unit/test_response_utils.py` - 30+ tests for utilities
- Full test coverage for all response types and error codes

### 5. **Developer Documentation**

- `docs/STANDARD_RESPONSES.md` - Complete developer guide with:
  - Quick start examples
  - Common patterns
  - Frontend integration guide
  - Migration guide
  - Best practices

## Benefits Delivered

✅ **Cleaner Frontend Integration**
```typescript
// Universal response handling
interface StandardResponse<T> {
  status: 'success' | 'error';
  message: string;
  data?: T;
  metadata: { trace_id, timestamp, duration_ms, ... };
  error?: { code, message, details };
}
```

✅ **Better Debugging and Logging**
```python
# Automatic trace ID for request correlation
logger.info(
    "Request processed",
    extra={"trace_id": response.metadata.trace_id}
)
```

✅ **Improved Transport Consistency**
- Same format works for HTTP, gRPC, WebSocket
- Automatic HTTP status code mapping from error codes
- Built-in streaming support

✅ **Foundation for Observability**
- Trace IDs for distributed tracing
- Duration tracking for performance monitoring
- Structured error logging

## Usage Examples

### Simple Success

```python
from bindu.utils.response_utils import success_response, to_json_response

response = success_response(
    message="Agent processed successfully",
    data={"result": "Hello, world!"}
)

return to_json_response(response)
```

### Error with Context

```python
from bindu.utils.response_utils import error_response
from bindu.common.responses import ErrorCodes

response = error_response(
    message="Failed to process request",
    error_code=ErrorCodes.INVALID_INPUT,
    error_details={"reason": "Missing required field 'message'"}
)

return to_json_response(response)  # Auto returns 400 status
```

### With Automatic Timing

```python
from bindu.utils.response_utils import ResponseBuilder, to_json_response

builder = ResponseBuilder(request_id="req-123")

# ... do work ...

response = builder.success(
    message="Processing completed",
    data=result
)
# Duration automatically tracked in metadata.duration_ms

return to_json_response(response)
```

## Response Format

```json
{
  "status": "success",
  "message": "Agent processed message successfully",
  "data": {
    "result": "Hello, world!"
  },
  "metadata": {
    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-02-27T10:30:00Z",
    "version": "1.0.0",
    "request_id": "req-123",
    "duration_ms": 42.5
  }
}
```

## Migration Path

1. **Opt-in by default** - Endpoints use query param `?format=standard`
2. **Gradual adoption** - Update endpoints one by one
3. **No breaking changes** - Legacy format remains default
4. **Future**: Make standard format the default (v2.0)

## Files Added

```
bindu/
  common/
    responses.py          # Core response models
  utils/
    response_utils.py     # Helper functions
    env_validation.py     # (Previous contribution)
    
tests/
  unit/
    test_env_validation.py
    test_standard_responses.py  # Response model tests
    test_response_utils.py      # Utility tests
    
docs/
  STANDARD_RESPONSES.md   # Developer documentation
  
examples/
  # Updated with env validation
```

## Files Modified

```
bindu/server/endpoints/health.py  # Demo of backward compatibility
```

## Standard Error Codes

```python
# Client errors (4xx)
INVALID_INPUT        # 400 - Bad request
VALIDATION_ERROR     # 400 - Validation failed
UNAUTHORIZED         # 401 - Not authenticated
FORBIDDEN            # 403 - Not authorized
NOT_FOUND            # 404 - Resource not found
CONFLICT             # 409 - Resource conflict
PAYMENT_REQUIRED     # 402 - Payment needed
RATE_LIMITED         # 429 - Too many requests

# Server errors (5xx)
INTERNAL_ERROR       # 500 - Server error
SERVICE_UNAVAILABLE  # 503 - Service down
TIMEOUT              # 504 - Request timeout

# Agent-specific
AGENT_NOT_READY      # Agent not initialized
HANDLER_ERROR        # Handler execution failed
PROTOCOL_ERROR       # Protocol violation
EXTENSION_ERROR      # Extension error
```

## Testing

All tests passing:
```bash
# Run response model tests
pytest tests/unit/test_standard_responses.py -v

# Run utility tests
pytest tests/unit/test_response_utils.py -v
```

## Next Steps for Full Adoption

1. Update more endpoints to support standard format
2. Add `?format=standard` to API documentation
3. Update frontend to use standard responses
4. Collect feedback from early adopters
5. Plan v2.0 where standard format becomes default

## Related Documentation

- [Developer Guide](docs/STANDARD_RESPONSES.md) - Complete usage guide
- [API Reference](bindu/common/responses.py) - Model definitions
- [Utilities](bindu/utils/response_utils.py) - Helper functions

---

**Implementation Status**: ✅ Complete and ready for review

This implementation provides the foundation for standardized responses while maintaining full backward compatibility. Endpoints can adopt the new format at their own pace.
