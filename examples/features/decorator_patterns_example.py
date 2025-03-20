#!/usr/bin/env python
"""Example demonstrating the use of decorator patterns for cross-cutting concerns.

This example demonstrates the use of various decorator patterns provided by
the PepperPy framework for cross-cutting concerns, including logging, validation,
caching, and more.
"""

import random
import time
from typing import Any, Dict, List

from pepperpy.core.decorators import (
    deprecated,
    log_entry_exit,
    memoize,
    profile,
    rate_limit,
    retry_on_exception,
    synchronized,
    timeout,
    trace,
    validate_args,
    validate_return,
)
from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)


def example_log_entry_exit() -> None:
    """Example demonstrating the use of the log_entry_exit decorator."""
    print("\n=== Log Entry Exit Decorator Example ===")

    @log_entry_exit(level="info", include_args=True, include_result=True)
    def add(a: int, b: int) -> int:
        """Add two numbers.

        Args:
            a: The first number
            b: The second number

        Returns:
            The sum of the two numbers
        """
        return a + b

    @log_entry_exit(level="info", include_args=True, include_result=False)
    def generate_large_result() -> List[int]:
        """Generate a large result.

        Returns:
            A large list of integers
        """
        return list(range(1000))

    print("Calling add(2, 3)...")
    result = add(2, 3)
    print(f"Result: {result}")

    print("\nCalling generate_large_result()...")
    result = generate_large_result()
    print(f"Result length: {len(result)}")


def example_validate_args() -> None:
    """Example demonstrating the use of the validate_args decorator."""
    print("\n=== Validate Args Decorator Example ===")

    @validate_args(
        name=lambda x: isinstance(x, str) and len(x) > 0,
        age=lambda x: isinstance(x, int) and x >= 0,
        email=lambda x: isinstance(x, str) and "@" in x,
    )
    def register_user(name: str, age: int, email: str) -> Dict[str, Any]:
        """Register a user.

        Args:
            name: The user's name
            age: The user's age
            email: The user's email

        Returns:
            A dictionary containing the user's information
        """
        return {"name": name, "age": age, "email": email}

    try:
        print("Registering user with valid arguments...")
        user = register_user(name="John Doe", age=30, email="john.doe@example.com")
        print(f"User registered: {user}")
    except PepperpyError as e:
        print(f"Error: {e}")

    try:
        print("\nRegistering user with invalid name...")
        user = register_user(name="", age=30, email="john.doe@example.com")
        print(f"User registered: {user}")
    except PepperpyError as e:
        print(f"Error: {e}")

    try:
        print("\nRegistering user with invalid age...")
        user = register_user(name="John Doe", age=-5, email="john.doe@example.com")
        print(f"User registered: {user}")
    except PepperpyError as e:
        print(f"Error: {e}")

    try:
        print("\nRegistering user with invalid email...")
        user = register_user(name="John Doe", age=30, email="invalid-email")
        print(f"User registered: {user}")
    except PepperpyError as e:
        print(f"Error: {e}")


def example_deprecated() -> None:
    """Example demonstrating the use of the deprecated decorator."""
    print("\n=== Deprecated Decorator Example ===")

    @deprecated(
        message="This function is deprecated and will be removed in version 2.0.",
        alternative="get_user_by_id",
    )
    def get_user(user_id: int) -> Dict[str, Any]:
        """Get a user by ID.

        Args:
            user_id: The user's ID

        Returns:
            A dictionary containing the user's information
        """
        return {"id": user_id, "name": f"User {user_id}"}

    print("Calling deprecated function...")
    user = get_user(123)
    print(f"User: {user}")


def example_memoize() -> None:
    """Example demonstrating the use of the memoize decorator."""
    print("\n=== Memoize Decorator Example ===")

    @memoize(maxsize=10, typed=True, ttl=5.0)
    def fibonacci(n: int) -> int:
        """Calculate the nth Fibonacci number.

        Args:
            n: The index of the Fibonacci number to calculate

        Returns:
            The nth Fibonacci number
        """
        print(f"Computing fibonacci({n})...")
        if n <= 1:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    print("Calculating fibonacci(10) for the first time...")
    start_time = time.time()
    result = fibonacci(10)
    elapsed = time.time() - start_time
    print(f"Result: {result} (took {elapsed:.6f} seconds)")

    print("\nCalculating fibonacci(10) again (should be cached)...")
    start_time = time.time()
    result = fibonacci(10)
    elapsed = time.time() - start_time
    print(f"Result: {result} (took {elapsed:.6f} seconds)")

    print("\nCache info:", fibonacci.cache_info())  # type: ignore

    print("\nClearing cache...")
    fibonacci.cache_clear()  # type: ignore
    print("Cache info after clearing:", fibonacci.cache_info())  # type: ignore

    print("\nCalculating fibonacci(10) after clearing cache...")
    start_time = time.time()
    result = fibonacci(10)
    elapsed = time.time() - start_time
    print(f"Result: {result} (took {elapsed:.6f} seconds)")


def example_retry_on_exception() -> None:
    """Example demonstrating the use of the retry_on_exception decorator."""
    print("\n=== Retry On Exception Decorator Example ===")

    @retry_on_exception(
        exceptions=ValueError,
        max_retries=3,
        delay=0.5,
        backoff=2.0,
        logger_level="warning",
    )
    def unreliable_function() -> str:
        """A function that sometimes fails.

        Returns:
            A success message

        Raises:
            ValueError: If the function fails
        """
        if random.random() < 0.7:  # 70% chance of failure
            raise ValueError("Random failure")
        return "Success!"

    try:
        print("Calling unreliable function...")
        result = unreliable_function()
        print(f"Result: {result}")
    except ValueError as e:
        print(f"All retries failed: {e}")


def example_rate_limit() -> None:
    """Example demonstrating the use of the rate_limit decorator."""
    print("\n=== Rate Limit Decorator Example ===")

    @rate_limit(calls=3, period=1.0, raise_on_limit=False)
    def limited_function(i: int) -> None:
        """A function with a rate limit.

        Args:
            i: The iteration number
        """
        print(f"Function called with i={i} at {time.time():.3f}")

    print("Calling limited function 5 times in quick succession...")
    print("(Should be limited to 3 calls per second)")
    for i in range(5):
        limited_function(i)

    @rate_limit(calls=2, period=1.0, raise_on_limit=True)
    def limited_function_with_error(i: int) -> None:
        """A function with a rate limit that raises an error.

        Args:
            i: The iteration number
        """
        print(f"Function called with i={i} at {time.time():.3f}")

    print("\nCalling limited function with error 5 times in quick succession...")
    print("(Should raise an error after 2 calls)")
    try:
        for i in range(5):
            limited_function_with_error(i)
    except PepperpyError as e:
        print(f"Error: {e}")


def example_trace() -> None:
    """Example demonstrating the use of the trace decorator."""
    print("\n=== Trace Decorator Example ===")

    @trace(level="info", include_locals=True, max_depth=5)
    def recursive_function(n: int) -> int:
        """A recursive function.

        Args:
            n: The recursion depth

        Returns:
            The result of the recursion
        """
        if n <= 0:
            return 0
        return n + recursive_function(n - 1)

    print("Calling recursive function...")
    result = recursive_function(3)
    print(f"Result: {result}")


def example_validate_return() -> None:
    """Example demonstrating the use of the validate_return decorator."""
    print("\n=== Validate Return Decorator Example ===")

    @validate_return(
        validator=lambda x: isinstance(x, int) and x > 0,
        error_message="Result must be a positive integer",
    )
    def divide(a: int, b: int) -> int:
        """Divide two numbers.

        Args:
            a: The dividend
            b: The divisor

        Returns:
            The quotient
        """
        return a // b

    try:
        print("Calling divide(10, 2)...")
        result = divide(10, 2)
        print(f"Result: {result}")
    except PepperpyError as e:
        print(f"Error: {e}")

    try:
        print("\nCalling divide(10, -2)...")
        result = divide(10, -2)
        print(f"Result: {result}")
    except PepperpyError as e:
        print(f"Error: {e}")


def example_profile() -> None:
    """Example demonstrating the use of the profile decorator."""
    print("\n=== Profile Decorator Example ===")

    @profile(level="info", threshold=0.1)
    def slow_function() -> None:
        """A slow function."""
        print("Sleeping for 0.2 seconds...")
        time.sleep(0.2)

    @profile(level="info", threshold=0.1)
    def fast_function() -> None:
        """A fast function."""
        print("Sleeping for 0.05 seconds...")
        time.sleep(0.05)

    print("Calling slow function (should be profiled)...")
    slow_function()

    print("\nCalling fast function (should not be profiled)...")
    fast_function()


def example_synchronized() -> None:
    """Example demonstrating the use of the synchronized decorator."""
    print("\n=== Synchronized Decorator Example ===")

    import threading

    # A shared counter
    counter = 0

    # A lock for synchronization
    lock = threading.RLock()

    @synchronized(lock)
    def increment_counter() -> None:
        """Increment the counter."""
        global counter
        # Simulate some work
        time.sleep(0.01)
        # Read the counter
        local_counter = counter
        # Simulate some more work
        time.sleep(0.01)
        # Increment the counter
        counter = local_counter + 1

    def unsynchronized_increment_counter() -> None:
        """Increment the counter without synchronization."""
        global counter
        # Simulate some work
        time.sleep(0.01)
        # Read the counter
        local_counter = counter
        # Simulate some more work
        time.sleep(0.01)
        # Increment the counter
        counter = local_counter + 1

    def run_threads(func: callable, num_threads: int) -> None:
        """Run multiple threads that call the given function.

        Args:
            func: The function to call
            num_threads: The number of threads to run
        """
        global counter
        counter = 0

        # Create and start the threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=func)
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        print(f"Final counter value: {counter}")

    print("Running 10 threads with synchronized increment...")
    run_threads(increment_counter, 10)

    print("\nRunning 10 threads with unsynchronized increment...")
    run_threads(unsynchronized_increment_counter, 10)


def example_timeout() -> None:
    """Example demonstrating the use of the timeout decorator."""
    print("\n=== Timeout Decorator Example ===")

    @timeout(1.0)
    def slow_function() -> None:
        """A slow function that will time out."""
        print("Sleeping for 2 seconds...")
        time.sleep(2)

    @timeout(1.0)
    def fast_function() -> None:
        """A fast function that will not time out."""
        print("Sleeping for 0.5 seconds...")
        time.sleep(0.5)

    try:
        print("Calling fast function (should not time out)...")
        fast_function()
        print("Function completed successfully")
    except PepperpyError as e:
        print(f"Error: {e}")

    try:
        print("\nCalling slow function (should time out)...")
        slow_function()
        print("Function completed successfully")
    except PepperpyError as e:
        print(f"Error: {e}")


def main() -> None:
    """Run all examples."""
    example_log_entry_exit()
    example_validate_args()
    example_deprecated()
    example_memoize()
    example_retry_on_exception()
    example_rate_limit()
    example_trace()
    example_validate_return()
    example_profile()
    example_synchronized()
    example_timeout()


if __name__ == "__main__":
    main()
