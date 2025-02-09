"""Monitoring decorators."""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypedDict, TypeVar, cast

from pepperpy.monitoring.logger import get_logger
from pepperpy.monitoring.metrics import metrics
from pepperpy.monitoring.tracer import tracer
from pepperpy.monitoring.tracing import tracing_manager

T = TypeVar("T")
P = ParamSpec("P")

logger = get_logger(__name__)


class LogContext(TypedDict, total=False):
    """Type definition for log context."""

    function: str
    trace_name: str
    duration: float
    error: str


def with_trace(name: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to add tracing to a function.

    Args:
        name: Name of the trace span

    Returns:
        Decorated function
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            with tracing_manager.start_span(name):
                logger.debug(
                    "Starting traced function",
                    extra=cast(
                        dict[str, Any],
                        LogContext(
                            function=func.__name__,
                            trace_name=name,
                        ),
                    ),
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
                        extra=cast(
                            dict[str, Any],
                            LogContext(
                                function=func.__name__,
                                trace_name=name,
                                duration=duration,
                            ),
                        ),
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
                        extra=cast(
                            dict[str, Any],
                            LogContext(
                                function=func.__name__,
                                trace_name=name,
                                error=str(e),
                                duration=duration,
                            ),
                        ),
                    )
                    raise

        return cast(Callable[P, T], wrapper)

    return decorator


def trace(name: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to trace function execution.

    Args:
        name: Name of the trace.

    Returns:
        Decorated function.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            result = None
            with tracer.start_trace(name):
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    tracer.set_attribute("duration", duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    tracer.set_attribute("duration", duration)
                    tracer.set_attribute("error", str(e))
                    raise

        return cast(Callable[P, T], wrapper)

    return decorator
