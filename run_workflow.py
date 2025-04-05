#!/usr/bin/env python3

import asyncio
import json
import sys

from plugins.workflow.repository_analyzer.provider import RepositoryAnalyzerAdapter


async def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print('Usage: python run_workflow.py [task] --input \'{"key": "value"}\'')
        print(
            "Available tasks: analyze_repository, analyze_structure, analyze_code_quality, analyze_complexity"
        )
        sys.exit(1)

    task = sys.argv[1]

    # Parse input data if provided
    input_data = {"repository_path": "."}
    for i, arg in enumerate(sys.argv):
        if arg == "--input" and i + 1 < len(sys.argv):
            try:
                input_data.update(json.loads(sys.argv[i + 1]))
            except json.JSONDecodeError:
                print("Error parsing input JSON. Make sure it's valid JSON.")
                sys.exit(1)

    # Add task to input data
    input_data["task"] = task

    # Add topic for ContentGeneratorWorkflow compatibility
    input_data["topic"] = "repository analysis"

    print(f"Running task: {task}")
    print(f"Input data: {input_data}")

    # Create and initialize the workflow provider
    workflow = RepositoryAnalyzerAdapter()
    await workflow.initialize()

    try:
        # Execute the workflow
        result = await workflow.execute(input_data)

        # Print the result
        print("\nWorkflow execution result:")
        print(json.dumps(result, indent=2, default=str))

    finally:
        # Clean up
        await workflow.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
