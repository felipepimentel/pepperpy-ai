#!/usr/bin/env python
"""
Timer Test Example for PepperPy.

This simple example demonstrates the usage of the Timer class from pepperpy.core.monitoring.
It does not depend on other complex components of the framework.
"""

import time

from pepperpy.core.monitoring import Timer


def main():
    """Run a simple demonstration of the Timer class."""
    print("=== PepperPy Timer Example ===")

    # Basic timer usage
    print("\n1. Basic timer usage:")
    timer = Timer("basic_timer")
    timer.start()
    time.sleep(1)  # Simulate work
    elapsed = timer.stop()
    print(f"Elapsed time: {elapsed:.2f} ms")

    # Method chaining
    print("\n2. Method chaining:")
    elapsed = Timer("chained_timer").start().stop()
    print(f"Elapsed time (empty operation): {elapsed:.2f} ms")

    # Multiple measurements
    print("\n3. Multiple measurements with the same timer:")
    timer = Timer("reused_timer")

    for i in range(3):
        timer.start()
        time.sleep(0.5)  # Simulate work
        elapsed = timer.stop()
        print(f"Iteration {i+1}: {elapsed:.2f} ms")

    # Auto-recording (just for demonstration, requires metrics collection setup)
    print("\n4. Timer with auto-recording:")
    timer = Timer("auto_timer", auto_record=True)
    timer.start()
    time.sleep(0.3)  # Simulate work
    elapsed = timer.stop()
    print(f"Elapsed time: {elapsed:.2f} ms (also auto-recorded)")

    # Using the elapsed property while timer is running
    print("\n5. Checking elapsed time during execution:")
    timer = Timer("running_timer").start()
    time.sleep(0.2)
    print(f"Elapsed while running: {timer.elapsed:.2f} ms")
    time.sleep(0.2)
    print(f"Elapsed after more time: {timer.elapsed:.2f} ms")
    timer.stop()

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
