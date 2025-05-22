"""Tests for the logging system."""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from trendscout.core.logging import (
    RequestContextMiddleware,
    log_request,
    log_response,
    log_error,
    log_agent_task,
    log_performance_metric,
    request_id_ctx_var,
)

# Test app setup
app = FastAPI()
app.add_middleware(RequestContextMiddleware)


@app.get("/test")
async def test_endpoint():
    return {"message": "test"}


@app.get("/error")
async def error_endpoint():
    raise ValueError("Test error")


client = TestClient(app)


@pytest.fixture
def mock_logger():
    """Fixture to capture log records."""
    with patch("trendscout.core.logging.logger") as mock:
        yield mock


def test_request_context_middleware(mock_logger):
    """Test that RequestContextMiddleware adds request_id and logs requests."""
    response = client.get("/test")
    assert response.status_code == 200

    # Check that request_id was set
    assert request_id_ctx_var.get() != ""

    # Verify logging calls
    mock_logger.info.assert_any_call(
        "Request completed",
        extra={
            "request_id": request_id_ctx_var.get(),
            "duration_ms": pytest.approx(0, abs=1000),
            "status_code": 200,
        },
    )


def test_log_request(mock_logger):
    """Test request logging."""
    mock_request = MagicMock(spec=Request)
    mock_request.method = "GET"
    mock_request.url = "http://test.com/path"
    mock_request.client.host = "127.0.0.1"
    mock_request.headers = {"user-agent": "test-agent"}

    log_request(mock_request)

    mock_logger.info.assert_called_once_with(
        "Request received",
        extra={
            "request_id": request_id_ctx_var.get(),
            "method": "GET",
            "url": "http://test.com/path",
            "client_host": "127.0.0.1",
            "user_agent": "test-agent",
        },
    )


def test_log_error_with_request(mock_logger):
    """Test error logging with request context."""
    mock_request = MagicMock(spec=Request)
    mock_request.method = "GET"
    mock_request.url = "http://test.com/path"
    mock_request.client.host = "127.0.0.1"

    error = ValueError("Test error")
    log_error(error, mock_request)

    mock_logger.error.assert_called_once_with(
        "Error occurred",
        extra={
            "request_id": request_id_ctx_var.get(),
            "error_type": "ValueError",
            "error_message": "Test error",
            "method": "GET",
            "url": "http://test.com/path",
            "client_host": "127.0.0.1",
        },
        exc_info=True,
    )


def test_log_agent_task(mock_logger):
    """Test agent task logging."""
    task_details = {
        "input": "test input",
        "output": "test output",
    }

    log_agent_task(
        agent_type="trend_analyzer",
        task_id="123",
        action="process",
        details=task_details,
    )

    # Get the call arguments
    call_args = mock_logger.info.call_args
    assert call_args is not None
    message, kwargs = call_args

    assert message[0] == "Agent task process"
    extra = kwargs["extra"]
    assert extra["agent_type"] == "trend_analyzer"
    assert extra["task_id"] == "123"
    assert extra["action"] == "process"
    # Verify details were JSON serialized
    assert json.loads(extra["details"]) == task_details
    # Verify timestamp is present
    assert "timestamp" in extra


def test_log_performance_metric(mock_logger):
    """Test performance metric logging."""
    tags = {"endpoint": "/test", "method": "GET"}

    log_performance_metric(
        metric_name="response_time",
        value=150.5,
        unit="ms",
        tags=tags,
    )

    # Get the call arguments
    call_args = mock_logger.info.call_args
    assert call_args is not None
    message, kwargs = call_args

    assert message[0] == "Performance metric: response_time"
    extra = kwargs["extra"]
    assert extra["metric_name"] == "response_time"
    assert extra["value"] == 150.5
    assert extra["unit"] == "ms"
    assert json.loads(extra["tags"]) == tags
    assert "timestamp" in extra


def test_error_endpoint_logging(mock_logger):
    """Test that error endpoint properly logs errors."""
    with pytest.raises(ValueError):
        client.get("/error")

    # Verify error was logged
    mock_logger.error.assert_called_with(
        "Error occurred",
        extra={
            "request_id": request_id_ctx_var.get(),
            "error_type": "ValueError",
            "error_message": "Test error",
            "method": "GET",
            "url": "http://testserver/error",
            "client_host": "testclient",
        },
        exc_info=True,
    )
