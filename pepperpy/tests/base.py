"""Base test module.

This module provides the base test infrastructure for the framework,
including the base test class, test context, and test utilities.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar, runtime_checkable

from pepperpy.core.base import ComponentBase
from pepperpy.core.metrics import Counter, Histogram


class TestError(Exception):
    """Test error.

    This error is raised when a test operation fails.
    """

    def __init__(self, message: str) -> None:
        """Initialize error.

        Args:
            message: Error message
        """
        super().__init__(message)
        self.message = message


@runtime_checkable
class Validatable(Protocol):
    """Protocol for validatable objects."""

    def is_valid(self) -> bool:
        """Check if object is valid.

        Returns:
            bool: True if object is valid
        """
        ...


@dataclass
class TestContext:
    """Test execution context.

    This class encapsulates the context for a test execution,
    including test configuration, resources, and metrics.
    """

    test_id: str
    test_name: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    resources: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """Test execution result.

    This class encapsulates the result of a test execution,
    including status, errors, and metrics.
    """

    test_id: str
    test_name: str
    status: str
    start_time: datetime
    end_time: datetime
    duration: float
    errors: List[Exception] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


T = TypeVar("T")


class BaseTest(ComponentBase):
    """Base test class.

    This class provides common functionality for all tests,
    including lifecycle management, resource management,
    error handling, and logging.
    """

    def __init__(self) -> None:
        """Initialize test."""
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._context: Optional[TestContext] = None

        # Initialize metrics
        self._test_executions = Counter(
            "test_executions_total", "Total number of test executions"
        )
        self._test_failures = Counter(
            "test_failures_total", "Total number of test failures"
        )
        self._test_duration = Histogram(
            "test_duration_seconds", "Test execution duration in seconds"
        )

    async def _initialize(self) -> None:
        """Initialize test resources."""
        await super()._initialize()
        self.logger.info("Initializing test resources")
        self._context = TestContext(
            test_id=self._generate_test_id(),
            test_name=self.__class__.__name__,
        )
        self._test_executions.inc()

    async def _cleanup(self) -> None:
        """Clean up test resources."""
        self.logger.info("Cleaning up test resources")
        if self._context:
            self._context.end_time = datetime.now()
            if self._context.resources:
                for resource in self._context.resources.values():
                    if hasattr(resource, "cleanup"):
                        await resource.cleanup()
        await super()._cleanup()

    async def run_test(self) -> TestResult:
        """Run test.

        This method executes the test and returns the result.

        Returns:
            TestResult: Test execution result
        """
        try:
            await self._initialize()
            await self.test()
            return self._create_result(status="passed")
        except Exception as e:
            self.logger.error(f"Test failed: {e}", exc_info=True)
            self._test_failures.inc()
            return self._create_result(status="failed", error=e)
        finally:
            await self._cleanup()

    async def test(self) -> None:
        """Execute test.

        This method must be implemented by subclasses.
        """
        raise NotImplementedError("Test method must be implemented by subclass")

    def _create_result(
        self, status: str, error: Optional[Exception] = None
    ) -> TestResult:
        """Create test result.

        Args:
            status: Test status
            error: Optional error

        Returns:
            TestResult: Test execution result
        """
        if not self._context:
            raise TestError("Test context not initialized")

        end_time = datetime.now()
        duration = (end_time - self._context.start_time).total_seconds()

        self._test_duration.observe(duration)

        result = TestResult(
            test_id=self._context.test_id,
            test_name=self._context.test_name,
            status=status,
            start_time=self._context.start_time,
            end_time=end_time,
            duration=duration,
            metrics=self._context.metrics,
        )

        if error:
            result.errors.append(error)

        return result

    def _generate_test_id(self) -> str:
        """Generate unique test ID.

        Returns:
            str: Unique test ID
        """
        return f"{self.__class__.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


class TestUtils:
    """Test utilities.

    This class provides static methods for creating test contexts
    and results, validating resources, and creating mock resources.
    """

    @staticmethod
    def create_test_context(test_name: str, **kwargs: Any) -> TestContext:
        """Create test context.

        Args:
            test_name: Test name
            **kwargs: Additional context attributes

        Returns:
            TestContext: Test context
        """
        return TestContext(
            test_id=f"{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            test_name=test_name,
            **kwargs,
        )

    @staticmethod
    def create_test_result(
        test_name: str,
        status: str,
        start_time: Optional[datetime] = None,
        **kwargs: Any,
    ) -> TestResult:
        """Create test result.

        Args:
            test_name: Test name
            status: Test status
            start_time: Optional start time
            **kwargs: Additional result attributes

        Returns:
            TestResult: Test result
        """
        start = start_time or datetime.now()
        return TestResult(
            test_id=f"{test_name}_{start.strftime('%Y%m%d_%H%M%S')}",
            test_name=test_name,
            status=status,
            start_time=start,
            end_time=datetime.now(),
            duration=0.0,
            **kwargs,
        )

    @staticmethod
    def validate_resource(resource: Any, resource_type: Type[T]) -> bool:
        """Validate resource.

        Args:
            resource: Resource to validate
            resource_type: Expected resource type

        Returns:
            bool: True if resource is valid
        """
        if not isinstance(resource, resource_type):
            return False

        if isinstance(resource, Validatable):
            return resource.is_valid()

        return True

    @staticmethod
    async def create_mock_resource(resource_type: Type[T], **kwargs: Any) -> T:
        """Create mock resource.

        Args:
            resource_type: Resource type to mock
            **kwargs: Resource attributes

        Returns:
            T: Mock resource
        """
        if asyncio.iscoroutinefunction(getattr(resource_type, "__init__", None)):
            resource = await resource_type(**kwargs)  # type: ignore
        else:
            resource = resource_type(**kwargs)

        return resource
