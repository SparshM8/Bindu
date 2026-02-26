"""Tests for environment variable validation utilities."""

import os
import pytest
import sys
from io import StringIO
from bindu.utils.env_validation import (
    get_required_env,
    get_optional_env,
    validate_api_keys,
)


class TestGetRequiredEnv:
    """Tests for get_required_env function."""

    def test_returns_value_when_set(self):
        """Test that the function returns the value when environment variable is set."""
        os.environ["TEST_VAR"] = "test_value"
        try:
            result = get_required_env("TEST_VAR")
            assert result == "test_value"
        finally:
            del os.environ["TEST_VAR"]

    def test_exits_when_not_set(self):
        """Test that the function exits when environment variable is not set."""
        # Ensure the variable is not set
        if "TEST_VAR_MISSING" in os.environ:
            del os.environ["TEST_VAR_MISSING"]

        with pytest.raises(SystemExit) as exc_info:
            get_required_env("TEST_VAR_MISSING")

        assert exc_info.value.code == 1

    def test_custom_error_message(self):
        """Test that custom error messages are displayed."""
        if "TEST_VAR_CUSTOM" in os.environ:
            del os.environ["TEST_VAR_CUSTOM"]

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            with pytest.raises(SystemExit):
                get_required_env("TEST_VAR_CUSTOM", "Custom error message")

            stderr_output = sys.stderr.getvalue()
            assert "Custom error message" in stderr_output
        finally:
            sys.stderr = old_stderr


class TestGetOptionalEnv:
    """Tests for get_optional_env function."""

    def test_returns_value_when_set(self):
        """Test that the function returns the value when environment variable is set."""
        os.environ["TEST_OPTIONAL"] = "optional_value"
        try:
            result = get_optional_env("TEST_OPTIONAL", "default_value")
            assert result == "optional_value"
        finally:
            del os.environ["TEST_OPTIONAL"]

    def test_returns_default_when_not_set(self):
        """Test that the function returns default value when envvar is not set."""
        if "TEST_OPTIONAL_MISSING" in os.environ:
            del os.environ["TEST_OPTIONAL_MISSING"]

        result = get_optional_env("TEST_OPTIONAL_MISSING", "default_value")
        assert result == "default_value"

    def test_returns_empty_string_when_no_default(self):
        """Test that the function returns empty string when no default is provided."""
        if "TEST_OPTIONAL_NO_DEFAULT" in os.environ:
            del os.environ["TEST_OPTIONAL_NO_DEFAULT"]

        result = get_optional_env("TEST_OPTIONAL_NO_DEFAULT")
        assert result == ""


class TestValidateApiKeys:
    """Tests for validate_api_keys function."""

    def test_all_keys_present(self):
        """Test that all keys are returned when present."""
        os.environ["KEY1"] = "value1"
        os.environ["KEY2"] = "value2"
        try:
            result = validate_api_keys("KEY1", "KEY2")
            assert result == {"KEY1": "value1", "KEY2": "value2"}
        finally:
            del os.environ["KEY1"]
            del os.environ["KEY2"]

    def test_exits_when_keys_missing(self):
        """Test that the function exits when any key is missing."""
        if "KEY_MISSING_1" in os.environ:
            del os.environ["KEY_MISSING_1"]
        if "KEY_MISSING_2" in os.environ:
            del os.environ["KEY_MISSING_2"]

        with pytest.raises(SystemExit) as exc_info:
            validate_api_keys("KEY_MISSING_1", "KEY_MISSING_2")

        assert exc_info.value.code == 1

    def test_exits_when_some_keys_missing(self):
        """Test that the function exits when some keys are missing."""
        os.environ["KEY_PRESENT"] = "value"
        if "KEY_MISSING" in os.environ:
            del os.environ["KEY_MISSING"]

        try:
            with pytest.raises(SystemExit) as exc_info:
                validate_api_keys("KEY_PRESENT", "KEY_MISSING")

            assert exc_info.value.code == 1
        finally:
            del os.environ["KEY_PRESENT"]
