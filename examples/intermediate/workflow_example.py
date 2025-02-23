"""Example Name: Workflow Example
Description: Example showing how to create and run workflows
Category: intermediate
Dependencies: pepperpy
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from examples.utils import ExampleComponent, example

# Configure logging
logger = logging.getLogger(__name__)


class WorkflowStep(ExampleComponent):
    """Workflow step implementation."""

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process step data.

        Args:
            data: Input data

        Returns:
            Dict[str, Any]: Output data
        """
        self._operations.inc()
        try:
            # Simulate work
            await asyncio.sleep(0.1)

            # Process data
            result = {
                "step": self.name,
                "input": data,
                "processed": True,
                "timestamp": datetime.now().isoformat(),
            }

            self._duration.observe(0.1)
            logger.info(f"Step {self.name} processed data: {result}")
            return result

        except Exception:
            self._errors.inc()
            raise

    async def _execute(self) -> None:
        """Execute step operation."""
        self._operations.inc()
        try:
            # Process test data
            data = {"message": f"Hello from {self.name}!"}
            result = await self.process(data)
            logger.info(f"Step result: {result}")
            self._duration.observe(0.1)

        except Exception:
            self._errors.inc()
            raise


class Workflow(ExampleComponent):
    """Workflow implementation."""

    def __init__(self, name: str) -> None:
        """Initialize workflow.

        Args:
            name: Workflow name
        """
        super().__init__(name)
        self._steps: List[WorkflowStep] = []

    def add_step(self, step: WorkflowStep) -> None:
        """Add workflow step.

        Args:
            step: Workflow step
        """
        self._steps.append(step)

    async def run(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run workflow.

        Args:
            data: Input data

        Returns:
            List[Dict[str, Any]]: Step results
        """
        self._operations.inc()
        results = []

        try:
            # Initialize steps
            for step in self._steps:
                await step._initialize()

            # Process data through steps
            current_data = data
            for step in self._steps:
                try:
                    # Process step
                    result = await step.process(current_data)
                    results.append(result)
                    current_data = result

                except Exception as e:
                    self._errors.inc()
                    logger.error(f"Step {step.name} failed: {e}")
                    raise

            self._duration.observe(0.1)
            return results

        finally:
            # Clean up steps
            for step in reversed(self._steps):
                await step._cleanup()

    async def _execute(self) -> None:
        """Execute workflow operation."""
        self._operations.inc()
        try:
            # Run workflow with test data
            data = {"message": "Hello, Workflow!"}
            results = await self.run(data)
            logger.info(f"Workflow results: {results}")
            self._duration.observe(0.1)

        except Exception:
            self._errors.inc()
            raise


@example(
    name="Workflow Example",
    category="intermediate",
    description="Example showing how to create and run workflows",
)
async def main() -> Dict[str, Any]:
    """Run workflow example.

    Returns:
        Dict[str, Any]: Example output
    """
    # Create workflow and steps
    workflow = Workflow("example_workflow")
    step1 = WorkflowStep("step1")
    step2 = WorkflowStep("step2")
    step3 = WorkflowStep("step3")

    # Add steps to workflow
    workflow.add_step(step1)
    workflow.add_step(step2)
    workflow.add_step(step3)

    try:
        # Initialize workflow
        await workflow._initialize()

        # Run workflow
        data = {"message": "Hello, World!"}
        results = await workflow.run(data)

        # Get metrics
        operations = workflow._operations.get_value()
        duration = workflow._duration.get_value()["count"]
        logger.info(
            f"Executed {operations} workflow operations in {duration:.2f} seconds"
        )

        # Get step metrics
        for step in workflow._steps:
            step_ops = step._operations.get_value()
            step_duration = step._duration.get_value()["count"]
            logger.info(
                f"Step {step.name}: {step_ops} operations "
                f"in {step_duration:.2f} seconds"
            )

        return {
            "workflow": workflow.name,
            "steps": len(workflow._steps),
            "results": results,
        }

    finally:
        # Clean up workflow
        await workflow._cleanup()


if __name__ == "__main__":
    # Run example
    asyncio.run(main())
