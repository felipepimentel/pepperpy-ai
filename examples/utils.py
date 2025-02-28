"""Example utilities module.

This module provides utilities for setting up and running examples.
"""

import asyncio
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pepperpy.common.base import ComponentBase
from pepperpy.common.metrics import Counter, Histogram

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ExampleContext:
    """Example execution context.

    This class encapsulates the context for example execution,
    including configuration, resources, and metrics.
    """

    name: str
    category: str
    description: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExampleResult:
    """Example execution result.

    This class encapsulates the result of example execution,
    including status, output, and metrics.
    """

    name: str
    category: str
    status: str
    start_time: datetime
    end_time: datetime
    duration: float
    output: Any
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[Exception] = field(default_factory=list)


class ExampleComponent(ComponentBase):
    """Example component implementation.

    This class provides a base for example components with metrics
    and resource management.
    """

    def __init__(self, name: str) -> None:
        """Initialize component.

        Args:
            name: Component name
        """
        super().__init__()
        self.name = name
        self._operations = Counter(
            "example_operations_total", "Total number of operations"
        )
        self._errors = Counter("example_errors_total", "Total number of errors")
        self._duration = Histogram(
            "example_duration_seconds", "Operation duration in seconds"
        )

    async def _initialize(self) -> None:
        """Initialize component."""
        await super()._initialize()
        self._operations.inc()
        logger.info(f"Initialized example component: {self.name}")

    async def _cleanup(self) -> None:
        """Clean up component."""
        self._operations.inc()
        logger.info(f"Cleaning up example component: {self.name}")
        await super()._cleanup()

    async def _execute(self) -> None:
        """Execute component operation."""
        self._operations.inc()
        try:
            # Simulate work
            await asyncio.sleep(0.1)
            self._duration.observe(0.1)
        except Exception:
            self._errors.inc()
            raise


class ExampleUtils:
    """Example utilities.

    This class provides static methods for setting up and running examples.
    """

    @staticmethod
    def setup_environment() -> None:
        """Set up example environment.

        This method sets up the environment for running examples,
        including logging and paths.
        """
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # Add examples directory to path
        examples_dir = Path(__file__).parent.absolute()
        if str(examples_dir) not in sys.path:
            sys.path.insert(0, str(examples_dir))

        # Set environment variables
        os.environ["PEPPERPY_EXAMPLES"] = "1"

    @staticmethod
    def cleanup_environment() -> None:
        """Clean up example environment.

        This method cleans up the environment after running examples.
        """
        # Remove environment variables
        os.environ.pop("PEPPERPY_EXAMPLES", None)

        # Clean up logging
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

    @staticmethod
    def create_example_context(
        name: str,
        category: str,
        description: str,
        **kwargs: Any,
    ) -> ExampleContext:
        """Create example context.

        Args:
            name: Example name
            category: Example category
            description: Example description
            **kwargs: Additional context attributes

        Returns:
            ExampleContext: Example context
        """
        return ExampleContext(
            name=name,
            category=category,
            description=description,
            config=kwargs.get("config", {}),
            resources=kwargs.get("resources", {}),
            metrics=kwargs.get("metrics", {}),
        )

    @staticmethod
    def create_example_result(
        context: ExampleContext,
        status: str,
        output: Any,
        error: Optional[Exception] = None,
    ) -> ExampleResult:
        """Create example result.

        Args:
            context: Example context
            status: Example status
            output: Example output
            error: Optional error

        Returns:
            ExampleResult: Example result
        """
        end_time = datetime.now()
        duration = (end_time - context.start_time).total_seconds()

        result = ExampleResult(
            name=context.name,
            category=context.category,
            status=status,
            start_time=context.start_time,
            end_time=end_time,
            duration=duration,
            output=output,
            metrics=context.metrics,
        )

        if error:
            result.errors.append(error)

        return result

    @staticmethod
    def validate_documentation(example_file: str) -> bool:
        """Validate example documentation.

        This method checks if an example file has proper documentation.

        Args:
            example_file: Path to example file

        Returns:
            bool: True if documentation is valid
        """
        required_fields = ["Example Name", "Description", "Category", "Dependencies"]

        try:
            with open(example_file, "r") as f:
                content = f.read()

            # Check for docstring
            if not content.startswith('"""'):
                return False

            # Check for required fields
            for field in required_fields:
                if field not in content.split('"""')[1]:
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to validate documentation: {e}")
            return False


def example(
    name: str,
    category: str = "basic",
    description: str = "",
) -> Any:
    """Decorator for example functions.

    This decorator handles setup, execution, and cleanup of examples.

    Args:
        name: Example name
        category: Example category
        description: Example description

    Returns:
        Any: Decorated function
    """

    def decorator(func: Any) -> Any:
        async def wrapper(*args: Any, **kwargs: Any) -> ExampleResult:
            # Set up environment
            ExampleUtils.setup_environment()

            # Create context
            context = ExampleUtils.create_example_context(
                name=name,
                category=category,
                description=description,
                **kwargs,
            )

            try:
                # Run example
                if asyncio.iscoroutinefunction(func):
                    output = await func(*args, **kwargs)
                else:
                    output = func(*args, **kwargs)

                # Create success result
                result = ExampleUtils.create_example_result(
                    context=context,
                    status="success",
                    output=output,
                )

            except Exception as e:
                # Create error result
                logger.error(f"Example failed: {e}", exc_info=True)
                result = ExampleUtils.create_example_result(
                    context=context,
                    status="error",
                    output=None,
                    error=e,
                )

            finally:
                # Clean up environment
                ExampleUtils.cleanup_environment()

            return result

        return wrapper

    return decorator
