"""@file: utils.py
@purpose: Core utility functions for the Pepperpy framework
@component: Core
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import asyncio
import functools
import importlib
import logging
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Optional, Type, TypeVar, Union

from pepperpy.core.errors import ConfigurationError, PepperpyError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def import_optional(module_name: str) -> Optional[Any]:
    """Import an optional module.

    Args:
        module_name: Name of the module to import

    Returns:
        The imported module or None if not available

    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying operations that may fail.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated function

    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            "Attempt %d/%d failed: %s. Retrying in %.2f seconds...",
                            attempt + 1,
                            max_attempts,
                            str(e),
                            current_delay,
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "All %d attempts failed. Last error: %s",
                            max_attempts,
                            str(e),
                        )

            if last_exception:
                raise last_exception
            raise RuntimeError("All retry attempts failed")

        return wrapper

    return decorator


async def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Async version of retry decorator.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated async function

    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            "Attempt %d/%d failed: %s. Retrying in %.2f seconds...",
                            attempt + 1,
                            max_attempts,
                            str(e),
                            current_delay,
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "All %d attempts failed. Last error: %s",
                            max_attempts,
                            str(e),
                        )

            if last_exception:
                raise last_exception
            raise RuntimeError("All retry attempts failed")

        return wrapper

    return decorator


@contextmanager
def timer() -> Generator[Callable[[], float], None, None]:
    """Context manager for timing operations.

    Returns:
        Function to get elapsed time

    Example:
        with timer() as get_elapsed:
            do_something()
            print(f"Operation took {get_elapsed():.2f} seconds")

    """
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start


def get_package_root() -> Path:
    """Get the root directory of the package.

    Returns:
        Path to package root

    """
    return Path(__file__).parent.parent


def load_config_from_env(prefix: str = "PEPPERPY_") -> Dict[str, str]:
    """Load configuration from environment variables.

    Args:
        prefix: Prefix for environment variables

    Returns:
        Dictionary of configuration values

    """
    return {
        key[len(prefix) :].lower(): value
        for key, value in os.environ.items()
        if key.startswith(prefix)
    }


def validate_path(path: Union[str, Path], must_exist: bool = True) -> Path:
    """Validate a file system path.

    Args:
        path: Path to validate
        must_exist: Whether the path must exist

    Returns:
        Validated Path object

    Raises:
        ConfigurationError: If path validation fails

    """
    try:
        path_obj = Path(path).resolve()
        if must_exist and not path_obj.exists():
            raise ConfigurationError(f"Path does not exist: {path}")
        return path_obj
    except Exception as e:
        raise ConfigurationError(f"Invalid path: {path}") from e


def setup_logging(
    level: Union[str, int] = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    format_string: Optional[str] = None,
) -> None:
    """Set up logging configuration.

    Args:
        level: Logging level
        log_file: Optional log file path
        format_string: Optional format string

    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    format_string = format_string or (
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(str(log_file)))

    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
    )


def is_running_in_test() -> bool:
    """Check if code is running in a test environment.

    Returns:
        True if running in test, False otherwise

    """
    return "pytest" in sys.modules


def is_running_in_notebook() -> bool:
    """Check if code is running in a Jupyter notebook.

    Returns:
        True if running in notebook, False otherwise

    """
    try:
        shell = sys.modules.get("IPython", None)
        if shell is None:
            return False
        return shell.get_ipython() is not None
    except Exception:
        return False


def safe_issubclass(
    obj: Any, class_or_tuple: Union[Type[Any], tuple[Type[Any], ...]]
) -> bool:
    """Safely check if an object is a subclass of another.

    Args:
        obj: Object to check
        class_or_tuple: Class or tuple of classes to check against

    Returns:
        True if obj is a subclass, False otherwise

    """
    try:
        return issubclass(obj, class_or_tuple)
    except TypeError:
        return False


def safe_isinstance(
    obj: Any, class_or_tuple: Union[Type[Any], tuple[Type[Any], ...]]
) -> bool:
    """Safely check if an object is an instance of a class.

    Args:
        obj: Object to check
        class_or_tuple: Class or tuple of classes to check against

    Returns:
        True if obj is an instance, False otherwise

    """
    try:
        return isinstance(obj, class_or_tuple)
    except TypeError:
        return False


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to a maximum length.

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated string

    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def format_exception(e: Exception) -> str:
    """Format an exception for display.

    Args:
        e: Exception to format

    Returns:
        Formatted exception string

    """
    if isinstance(e, PepperpyError):
        return str(e)
    return f"{type(e).__name__}: {str(e)}"
