#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example demonstrating the use of workflows in the PepperPy framework.

This example shows how to create and execute a simple workflow with multiple steps,
including conditional branching and error handling.
"""

import asyncio
import random

# Import the necessary workflow components
# Note: This is a placeholder import - adjust based on actual implementation
from pepperpy.workflows.public import (
    StepResult,
    StepStatus,
    WorkflowBuilder,
    WorkflowContext,
    WorkflowStep,
)


# Define some example workflow steps
class DataFetchStep(WorkflowStep):
    """Step that fetches data from a simulated source."""

    async def execute(self, context: WorkflowContext) -> StepResult:
        """Execute the data fetch step.

        Args:
            context: The workflow context.

        Returns:
            The result of the step execution.
        """
        print("Fetching data...")

        # Simulate data fetching with random success/failure
        if random.random() < 0.8:  # 80% success rate
            data = [
                {"id": 1, "name": "Item 1", "value": random.randint(10, 100)},
                {"id": 2, "name": "Item 2", "value": random.randint(10, 100)},
                {"id": 3, "name": "Item 3", "value": random.randint(10, 100)},
            ]
            context.set("data", data)
            return StepResult(
                status=StepStatus.SUCCESS,
                message="Data fetched successfully",
                data={"count": len(data)},
            )
        else:
            return StepResult(
                status=StepStatus.FAILURE,
                message="Failed to fetch data",
                error="Connection error",
            )


class DataProcessStep(WorkflowStep):
    """Step that processes the fetched data."""

    async def execute(self, context: WorkflowContext) -> StepResult:
        """Execute the data processing step.

        Args:
            context: The workflow context.

        Returns:
            The result of the step execution.
        """
        print("Processing data...")

        # Get data from context
        data = context.get("data")
        if not data:
            return StepResult(
                status=StepStatus.FAILURE,
                message="No data available for processing",
                error="Missing data",
            )

        # Process the data (calculate total and average)
        total = sum(item["value"] for item in data)
        average = total / len(data)

        # Store processed results in context
        processed_data = {
            "items": data,
            "total": total,
            "average": average,
        }
        context.set("processed_data", processed_data)

        return StepResult(
            status=StepStatus.SUCCESS,
            message="Data processed successfully",
            data={"total": total, "average": average},
        )


class ReportGenerationStep(WorkflowStep):
    """Step that generates a report from the processed data."""

    async def execute(self, context: WorkflowContext) -> StepResult:
        """Execute the report generation step.

        Args:
            context: The workflow context.

        Returns:
            The result of the step execution.
        """
        print("Generating report...")

        # Get processed data from context
        processed_data = context.get("processed_data")
        if not processed_data:
            return StepResult(
                status=StepStatus.FAILURE,
                message="No processed data available for report generation",
                error="Missing processed data",
            )

        # Generate a simple report
        report = {
            "title": "Data Analysis Report",
            "timestamp": context.get("timestamp", "N/A"),
            "summary": {
                "item_count": len(processed_data["items"]),
                "total_value": processed_data["total"],
                "average_value": processed_data["average"],
            },
            "items": processed_data["items"],
        }

        # Store the report in context
        context.set("report", report)

        return StepResult(
            status=StepStatus.SUCCESS,
            message="Report generated successfully",
            data={"report_title": report["title"]},
        )


class ErrorHandlingStep(WorkflowStep):
    """Step that handles errors from previous steps."""

    async def execute(self, context: WorkflowContext) -> StepResult:
        """Execute the error handling step.

        Args:
            context: The workflow context.

        Returns:
            The result of the step execution.
        """
        print("Handling error...")

        # Get error information from context
        error = context.get("error", "Unknown error")

        # Log the error (in a real implementation, this might send alerts or notifications)
        print(f"Error occurred: {error}")

        return StepResult(
            status=StepStatus.SUCCESS,
            message="Error handled",
            data={"error": error},
        )


async def main():
    """Run the example workflow."""
    # Create a workflow context with initial data
    context = WorkflowContext()
    context.set("timestamp", "2023-06-15T10:30:00Z")

    # Create a workflow using the builder
    workflow = (
        WorkflowBuilder("Data Processing Workflow")
        .add_step("fetch_data", DataFetchStep())
        .add_conditional_step(
            "process_data",
            DataProcessStep(),
            condition=lambda ctx: ctx.get_step_result("fetch_data").status
            == StepStatus.SUCCESS,
        )
        .add_conditional_step(
            "generate_report",
            ReportGenerationStep(),
            condition=lambda ctx: ctx.get_step_result("process_data").status
            == StepStatus.SUCCESS,
        )
        .add_error_handler("handle_error", ErrorHandlingStep())
        .build()
    )

    # Execute the workflow
    result = await workflow.execute(context)

    # Print the workflow results
    print("\nWorkflow execution completed!")
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")

    # Print the final report if available
    report = context.get("report")
    if report:
        print("\nFinal Report:")
        print(f"Title: {report['title']}")
        print(f"Timestamp: {report['timestamp']}")
        print("Summary:")
        for key, value in report["summary"].items():
            print(f"  - {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
