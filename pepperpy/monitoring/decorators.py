"""Monitoring decorators."""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from pepperpy.monitoring.logger import get_logger
from pepperpy.monitoring.metrics import metrics
from pepperpy.monitoring.tracing import tracing_manager

T = TypeVar("T")

logger = get_logger(__name__)


def with_trace(name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add tracing to a function.

    Args:
        name: Name of the trace span

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            with tracing_manager.start_span(name) as span:
                span.set_attribute("function", func.__name__)
                logger.debug(
                    "Starting traced function",
                    function=func.__name__,
                    trace_name=name,
                )
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    metrics.histogram(
                        f"{func.__name__}_duration_seconds",
                        duration,
                        labels={"trace_name": name},
                    )
                    metrics.counter(
                        f"{func.__name__}_calls_total",
                        1.0,
                        labels={"trace_name": name, "status": "success"},
                    )
                    logger.debug(
                        "Completed traced function",
                        function=func.__name__,
                        trace_name=name,
                        duration=duration,
                    )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    metrics.histogram(
                        f"{func.__name__}_duration_seconds",
                        duration,
                        labels={"trace_name": name},
                    )
                    metrics.counter(
                        f"{func.__name__}_calls_total",
                        1.0,
                        labels={"trace_name": name, "status": "error"},
                    )
                    logger.error(
                        "Error in traced function",
                        function=func.__name__,
                        trace_name=name,
                        error=str(e),
                        duration=duration,
                    )
                    tracing_manager.record_exception(span, e)
                    raise

        return wrapper

    return decorator
