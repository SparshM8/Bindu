"""Tests for standardized response models."""

import pytest
from datetime import datetime, timezone

from bindu.common.responses import (
    ErrorCodes,
    ErrorDetail,
    PaginatedResponse,
    ResponseMetadata,
    StandardResponse,
    StreamChunk,
)


class TestResponseMetadata:
    """Tests for ResponseMetadata model."""

    def test_default_values(self):
        """Test that metadata is created with sensible defaults."""
        metadata = ResponseMetadata()

        assert metadata.trace_id is not None
        assert len(metadata.trace_id) > 0
        assert metadata.timestamp is not None
        assert metadata.version == "1.0.0"
        assert metadata.request_id is None
        assert metadata.duration_ms is None

    def test_custom_values(self):
        """Test metadata with custom values."""
        metadata = ResponseMetadata(
            trace_id="custom-trace-id",
            version="2.0.0",
            request_id="req-123",
            duration_ms=42.5,
        )

        assert metadata.trace_id == "custom-trace-id"
        assert metadata.version == "2.0.0"
        assert metadata.request_id == "req-123"
        assert metadata.duration_ms == 42.5

    def test_timestamp_format(self):
        """Test that timestamp is in ISO 8601 format."""
        metadata = ResponseMetadata()

        # Should be parseable as ISO 8601
        parsed = datetime.fromisoformat(metadata.timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)


class TestErrorDetail:
    """Tests for ErrorDetail model."""

    def test_required_fields(self):
        """Test error detail with required fields only."""
        error = ErrorDetail(
            code="TEST_ERROR",
            message="Test error message",
        )

        assert error.code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.details is None
        assert error.field is None

    def test_all_fields(self):
        """Test error detail with all fields."""
        error = ErrorDetail(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Validation failed",
            details={"expected": "string", "got": "int"},
            field="email",
        )

        assert error.code == ErrorCodes.VALIDATION_ERROR
        assert error.message == "Validation failed"
        assert error.details == {"expected": "string", "got": "int"}
        assert error.field == "email"


class TestStandardResponse:
    """Tests for StandardResponse model."""

    def test_success_response(self):
        """Test creating a success response."""
        response = StandardResponse(
            status="success",
            message="Operation completed",
            data={"result": "test"},
        )

        assert response.status == "success"
        assert response.message == "Operation completed"
        assert response.data == {"result": "test"}
        assert response.success is True
        assert response.error is None
        assert response.metadata is not None

    def test_error_response(self):
        """Test creating an error response."""
        error_detail = ErrorDetail(
            code=ErrorCodes.INVALID_INPUT,
            message="Invalid input",
        )
        response = StandardResponse(
            status="error",
            message="Request failed",
            data=None,
            error=error_detail,
        )

        assert response.status == "error"
        assert response.message == "Request failed"
        assert response.data is None
        assert response.success is False
        assert response.error is not None
        assert response.error.code == ErrorCodes.INVALID_INPUT

    def test_success_property(self):
        """Test the success computed property."""
        success_resp = StandardResponse(status="success", message="OK")
        error_resp = StandardResponse(status="error", message="Failed")

        assert success_resp.success is True
        assert error_resp.success is False

    def test_serialization(self):
        """Test that response can be serialized to dict/JSON."""
        response = StandardResponse(
            status="success",
            message="Test",
            data={"key": "value"},
        )

        # Model should serialize to dict
        data = response.model_dump()
        assert isinstance(data, dict)
        assert data["status"] == "success"
        assert data["message"] == "Test"
        assert data["data"] == {"key": "value"}

        # Should be JSON serializable
        json_str = response.model_dump_json()
        assert isinstance(json_str, str)
        assert "success" in json_str


class TestStreamChunk:
    """Tests for StreamChunk model."""

    def test_stream_chunk_creation(self):
        """Test creating a stream chunk."""
        chunk = StreamChunk(
            sequence=0,
            content="Hello ",
            is_final=False,
        )

        assert chunk.chunk_id is not None
        assert chunk.sequence == 0
        assert chunk.content == "Hello "
        assert chunk.is_final is False
        assert chunk.metadata is None

    def test_final_chunk(self):
        """Test creating a final chunk."""
        chunk = StreamChunk(
            sequence=5,
            content="World!",
            is_final=True,
            metadata={"total_chunks": 6},
        )

        assert chunk.sequence == 5
        assert chunk.is_final is True
        assert chunk.metadata == {"total_chunks": 6}


class TestPaginatedResponse:
    """Tests for PaginatedResponse model."""

    def test_paginated_response(self):
        """Test creating a paginated response."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = PaginatedResponse(
            items=items,
            total=10,
            page=1,
            page_size=3,
            has_more=True,
        )

        assert response.items == items
        assert response.total == 10
        assert response.page == 1
        assert response.page_size == 3
        assert response.has_more is True

    def test_total_pages_calculation(self):
        """Test that total_pages is calculated correctly."""
        # 10 items, 3 per page = 4 pages
        response = PaginatedResponse(
            items=[],
            total=10,
            page=1,
            page_size=3,
            has_more=True,
        )
        assert response.total_pages == 4

        # 9 items, 3 per page = 3 pages (exact)
        response2 = PaginatedResponse(
            items=[],
            total=9,
            page=1,
            page_size=3,
            has_more=False,
        )
        assert response2.total_pages == 3

        # 1 item, 10 per page = 1 page
        response3 = PaginatedResponse(
            items=[{"id": 1}],
            total=1,
            page=1,
            page_size=10,
            has_more=False,
        )
        assert response3.total_pages == 1


class TestErrorCodes:
    """Tests for error code constants."""

    def test_error_codes_exist(self):
        """Test that common error codes are defined."""
        assert hasattr(ErrorCodes, "INVALID_INPUT")
        assert hasattr(ErrorCodes, "VALIDATION_ERROR")
        assert hasattr(ErrorCodes, "NOT_FOUND")
        assert hasattr(ErrorCodes, "UNAUTHORIZED")
        assert hasattr(ErrorCodes, "INTERNAL_ERROR")
        assert hasattr(ErrorCodes, "AGENT_NOT_READY")

    def test_error_codes_are_strings(self):
        """Test that error codes are string constants."""
        assert isinstance(ErrorCodes.INVALID_INPUT, str)
        assert isinstance(ErrorCodes.VALIDATION_ERROR, str)
        assert isinstance(ErrorCodes.NOT_FOUND, str)
