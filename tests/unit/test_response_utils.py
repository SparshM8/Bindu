"""Tests for response utility functions."""

import pytest
from time import sleep

from bindu.common.responses import ErrorCodes, StandardResponse, PaginatedResponse
from bindu.utils.response_utils import (
    ResponseBuilder,
    success_response,
    error_response,
    validation_error_response,
    not_found_response,
    paginated_response,
    to_json_response,
    stream_chunk,
)


class TestResponseBuilder:
    """Tests for ResponseBuilder class."""

    def test_builder_initialization(self):
        """Test builder initialization with custom values."""
        builder = ResponseBuilder(
            request_id="req-123",
            version="2.0.0",
            trace_id="trace-456",
        )

        assert builder.request_id == "req-123"
        assert builder.version == "2.0.0"
        assert builder.trace_id == "trace-456"

    def test_success_response(self):
        """Test creating success response with builder."""
        builder = ResponseBuilder(request_id="req-123")
        response = builder.success(
            message="Test successful",
            data={"result": "value"},
        )

        assert response.status == "success"
        assert response.message == "Test successful"
        assert response.data == {"result": "value"}
        assert response.metadata.request_id == "req-123"
        assert response.error is None

    def test_error_response(self):
        """Test creating error response with builder."""
        builder = ResponseBuilder(request_id="req-123")
        response = builder.error(
            message="Test failed",
            error_code=ErrorCodes.INVALID_INPUT,
            error_details={"field": "email"},
        )

        assert response.status == "error"
        assert response.message == "Test failed"
        assert response.error is not None
        assert response.error.code == ErrorCodes.INVALID_INPUT
        assert response.error.details == {"field": "email"}

    def test_duration_tracking(self):
        """Test that response duration is tracked."""
        builder = ResponseBuilder()

        # Wait a tiny bit
        sleep(0.01)

        response = builder.success(message="Done")

        # Duration should be tracked
        assert response.metadata.duration_ms is not None
        assert response.metadata.duration_ms > 0


class TestSuccessResponse:
    """Tests for success_response helper."""

    def test_simple_success(self):
        """Test creating simple success response."""
        response = success_response(
            message="Operation completed",
            data={"key": "value"},
        )

        assert isinstance(response, StandardResponse)
        assert response.status == "success"
        assert response.message == "Operation completed"
        assert response.data == {"key": "value"}

    def test_success_with_request_id(self):
        """Test success response with request correlation."""
        response = success_response(
            message="Done",
            request_id="req-999",
        )

        assert response.metadata.request_id == "req-999"

    def test_success_without_data(self):
        """Test success response without data payload."""
        response = success_response(message="Acknowledged")

        assert response.status == "success"
        assert response.data is None


class TestErrorResponse:
    """Tests for error_response helper."""

    def test_simple_error(self):
        """Test creating simple error response."""
        response = error_response(
            message="Something went wrong",
            error_code=ErrorCodes.INTERNAL_ERROR,
        )

        assert isinstance(response, StandardResponse)
        assert response.status == "error"
        assert response.message == "Something went wrong"
        assert response.error.code == ErrorCodes.INTERNAL_ERROR

    def test_error_with_details(self):
        """Test error response with detailed context."""
        response = error_response(
            message="Processing failed",
            error_code=ErrorCodes.HANDLER_ERROR,
            error_details={
                "handler": "message_handler",
                "exception": "ValueError",
            },
        )

        assert response.error.code == ErrorCodes.HANDLER_ERROR
        assert response.error.details["handler"] == "message_handler"

    def test_error_with_field(self):
        """Test error response with field information."""
        response = error_response(
            message="Invalid input",
            error_code=ErrorCodes.VALIDATION_ERROR,
            field="email",
        )

        assert response.error.field == "email"


class TestValidationErrorResponse:
    """Tests for validation_error_response helper."""

    def test_validation_error(self):
        """Test creating validation error response."""
        response = validation_error_response(
            field="email",
            message="Invalid email format",
        )

        assert response.status == "error"
        assert response.error.code == ErrorCodes.VALIDATION_ERROR
        assert response.error.field == "email"
        assert "email" in response.message.lower()

    def test_validation_error_with_details(self):
        """Test validation error with additional context."""
        response = validation_error_response(
            field="age",
            message="Must be positive integer",
            details={"value": -5, "min": 0},
        )

        assert response.error.details["value"] == -5
        assert response.error.details["min"] == 0


class TestNotFoundResponse:
    """Tests for not_found_response helper."""

    def test_not_found_simple(self):
        """Test simple not found response."""
        response = not_found_response(resource="agent")

        assert response.status == "error"
        assert response.error.code == ErrorCodes.NOT_FOUND
        assert "agent" in response.message.lower()

    def test_not_found_with_id(self):
        """Test not found with resource ID."""
        response = not_found_response(
            resource="skill",
            resource_id="skill-123",
        )

        assert "skill-123" in response.message
        assert response.error.details["resource"] == "skill"
        assert response.error.details["resource_id"] == "skill-123"


class TestPaginatedResponse:
    """Tests for paginated_response helper."""

    def test_first_page(self):
        """Test creating first page response."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = paginated_response(
            items=items,
            total=10,
            page=1,
            page_size=3,
        )

        assert isinstance(response, PaginatedResponse)
        assert response.items == items
        assert response.total == 10
        assert response.page == 1
        assert response.has_more is True

    def test_last_page(self):
        """Test creating last page response."""
        items = [{"id": 10}]
        response = paginated_response(
            items=items,
            total=10,
            page=4,
            page_size=3,
        )

        assert response.has_more is False

    def test_empty_results(self):
        """Test pagination with no results."""
        response = paginated_response(
            items=[],
            total=0,
            page=1,
            page_size=10,
        )

        assert len(response.items) == 0
        assert response.total == 0
        assert response.has_more is False


class TestToJsonResponse:
    """Tests for to_json_response converter."""

    def test_success_to_json(self):
        """Test converting success response to JSONResponse."""
        std_response = success_response("Done", data={"value": 123})
        json_response = to_json_response(std_response)

        assert json_response.status_code == 200
        assert json_response.media_type == "application/json"

    def test_error_status_code_mapping(self):
        """Test that error codes map to appropriate HTTP status codes."""
        # Validation error -> 400
        validation_resp = error_response(
            "Invalid",
            error_code=ErrorCodes.VALIDATION_ERROR,
        )
        json_resp = to_json_response(validation_resp)
        assert json_resp.status_code == 400

        # Not found -> 404
        not_found_resp = error_response(
            "Not found",
            error_code=ErrorCodes.NOT_FOUND,
        )
        json_resp = to_json_response(not_found_resp)
        assert json_resp.status_code == 404

        # Unauthorized -> 401
        unauth_resp = error_response(
            "Unauthorized",
            error_code=ErrorCodes.UNAUTHORIZED,
        )
        json_resp = to_json_response(unauth_resp)
        assert json_resp.status_code == 401

        # Internal error -> 500
        internal_resp = error_response(
            "Server error",
            error_code=ErrorCodes.INTERNAL_ERROR,
        )
        json_resp = to_json_response(internal_resp)
        assert json_resp.status_code == 500

    def test_custom_status_code(self):
        """Test overriding status code."""
        response = success_response("Done")
        json_response = to_json_response(response, status_code=201)

        assert json_response.status_code == 201


class TestStreamChunk:
    """Tests for stream_chunk helper."""

    def test_create_chunk(self):
        """Test creating a stream chunk."""
        chunk = stream_chunk(
            sequence=0,
            content="Hello",
        )

        assert chunk.sequence == 0
        assert chunk.content == "Hello"
        assert chunk.is_final is False
        assert chunk.chunk_id is not None

    def test_final_chunk(self):
        """Test creating final chunk."""
        chunk = stream_chunk(
            sequence=5,
            content="Done",
            is_final=True,
        )

        assert chunk.is_final is True

    def test_chunk_with_metadata(self):
        """Test chunk with custom metadata."""
        chunk = stream_chunk(
            sequence=1,
            content="data",
            metadata={"tokens": 10},
        )

        assert chunk.metadata == {"tokens": 10}
