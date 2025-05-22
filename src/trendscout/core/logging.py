"""
Logging configuration for the Trendscout application.
Provides structured logging with request/response tracking and performance monitoring.
"""

import json
import logging
import sys
import time
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import Request, Response
from pythonjsonlogger import jsonlogger

# Context variables for request tracking
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")
current_user_ctx_var: ContextVar[Optional[str]] = ContextVar(
    "current_user", default=None
)

# Configure the JSON logger
logger = logging.getLogger("trendscout")
logHandler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(request_id)s %(message)s"
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


class RequestContextMiddleware:
    """Middleware to add request context to logs."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request_id = str(uuid4())
        request_id_ctx_var.set(request_id)

        # Wrap the send function to capture response
        start_time = time.time()

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                status_code = message.get("status", 0)
                logger.info(
                    "Request completed",
                    extra={
                        "request_id": request_id,
                        "duration_ms": round(duration * 1000, 2),
                        "status_code": status_code,
                    },
                )
            return await send(message)

        return await self.app(scope, receive, wrapped_send)


def log_request(request: Request) -> None:
    """Log incoming request details."""
    logger.info(
        "Request received",
        extra={
            "request_id": request_id_ctx_var.get(),
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
    )


def log_response(response: Response, duration_ms: float) -> None:
    """Log response details."""
    logger.info(
        "Response sent",
        extra={
            "request_id": request_id_ctx_var.get(),
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )


def log_error(error: Exception, request: Optional[Request] = None) -> None:
    """Log error details with request context if available."""
    error_details = {
        "request_id": request_id_ctx_var.get(),
        "error_type": type(error).__name__,
        "error_message": str(error),
    }

    if request:
        error_details.update(
            {
                "method": request.method,
                "url": str(request.url),
                "client_host": request.client.host if request.client else None,
            }
        )

    logger.error("Error occurred", extra=error_details, exc_info=True)


def log_agent_task(
    agent_type: str,
    task_id: str,
    action: str,
    details: Dict[str, Any],
) -> None:
    """Log agent task details."""
    logger.info(
        f"Agent task {action}",
        extra={
            "request_id": request_id_ctx_var.get(),
            "agent_type": agent_type,
            "task_id": task_id,
            "action": action,
            "details": json.dumps(details),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str = "ms",
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """Log performance metrics."""
    logger.info(
        f"Performance metric: {metric_name}",
        extra={
            "request_id": request_id_ctx_var.get(),
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "tags": json.dumps(tags or {}),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
