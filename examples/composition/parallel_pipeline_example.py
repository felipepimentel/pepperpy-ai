#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example demonstrating the use of parallel pipelines in the PepperPy framework.

This example shows how to create a parallel data processing pipeline using the
composition API to fetch data from multiple sources concurrently, process it in
parallel, and output the combined results.
"""

import asyncio
import time
from typing import Any, Dict, List

from pepperpy.core.composition import compose, compose_parallel
from pepperpy.core.composition.base import (
    OutputComponentBase,
    ProcessorComponentBase,
    SourceComponentBase,
)


class WebAPISource(SourceComponentBase[List[Dict[str, Any]]]):
    """Source component that fetches data from a web API."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the web API source.

        Args:
            config: Configuration dictionary containing the API endpoint and parameters.
        """
        super().__init__(config)
        self.endpoint = config.get("endpoint", "https://api.example.com/data")
        self.category = config.get("category", "general")

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch data from the web API.

        Returns:
            List of dictionaries containing the API response items.
        """
        print(f"Fetching data from {self.endpoint} for category: {self.category}")
        # Simulate network delay
        await asyncio.sleep(1)
        # In a real implementation, this would use aiohttp or similar to fetch the data
        # For this example, we'll return mock data
        return [
            {"id": 1, "title": f"{self.category} Item 1", "data": "Data 1"},
            {"id": 2, "title": f"{self.category} Item 2", "data": "Data 2"},
            {"id": 3, "title": f"{self.category} Item 3", "data": "Data 3"},
        ]


class DataEnricherProcessor(
    ProcessorComponentBase[List[Dict[str, Any]], List[Dict[str, Any]]]
):
    """Processor component that enriches data with additional information."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the data enricher processor.

        Args:
            config: Configuration dictionary.
        """
        super().__init__(config)
        self.enrichment_type = config.get("enrichment_type", "basic")
        self.processing_time = config.get(
            "processing_time", 0.5
        )  # Simulated processing time

    async def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich data with additional information.

        Args:
            data: List of dictionaries containing data items.

        Returns:
            Enhanced list of dictionaries with additional information.
        """
        print(f"Enriching {len(data)} items with {self.enrichment_type} enrichment")
        # Simulate processing time
        await asyncio.sleep(self.processing_time)

        result = []
        for item in data:
            # In a real implementation, this might call other APIs or databases
            enhanced_item = item.copy()
            enhanced_item["enriched"] = True
            enhanced_item["enrichment_type"] = self.enrichment_type
            enhanced_item["enrichment_data"] = (
                f"Additional {self.enrichment_type} data for {item['title']}"
            )
            enhanced_item["timestamp"] = time.time()
            result.append(enhanced_item)
        return result


class CSVOutputComponent(OutputComponentBase[List[Dict[str, Any]]]):
    """Output component that formats data as CSV."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the CSV output component.

        Args:
            config: Configuration dictionary.
        """
        super().__init__(config)
        self.output_file = config.get("output_file", "output.csv")

    async def output(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format and output the data as CSV.

        Args:
            data: List of dictionaries to output.

        Returns:
            Dictionary containing the result information.
        """
        print(f"Outputting {len(data)} items to {self.output_file}")
        # In a real implementation, this would write to a CSV file
        # For this example, we'll just print the data
        for item in data:
            print(f"ID: {item['id']}")
            print(f"Title: {item['title']}")
            print(f"Enrichment Type: {item.get('enrichment_type', 'N/A')}")
            print(f"Enrichment Data: {item.get('enrichment_data', 'N/A')}")
            print("-" * 50)

        return {
            "status": "success",
            "count": len(data),
            "output_file": self.output_file,
        }


async def main():
    """Run the example parallel pipeline."""
    # Create a parallel pipeline using the composition API
    pipeline = (
        compose_parallel("Parallel Data Processing Pipeline")
        .source(
            WebAPISource({
                "endpoint": "https://api.example.com/news",
                "category": "news",
            })
        )
        .process(
            DataEnricherProcessor({"enrichment_type": "news", "processing_time": 0.8})
        )
        .process(
            DataEnricherProcessor({
                "enrichment_type": "sentiment",
                "processing_time": 0.5,
            })
        )
        .output(CSVOutputComponent({"output_file": "enriched_data.csv"}))
    )

    # Execute the pipeline
    start_time = time.time()
    result = await pipeline.execute()
    end_time = time.time()

    print("\nParallel pipeline execution completed!")
    print(f"Execution time: {end_time - start_time:.2f} seconds")
    print(f"Status: {result['status']}")
    print(f"Processed items: {result['count']}")
    print(f"Output file: {result['output_file']}")

    # For comparison, let's run the same pipeline in standard (sequential) mode
    print("\nRunning the same pipeline in sequential mode for comparison...")
    sequential_pipeline = (
        compose("Sequential Data Processing Pipeline")
        .source(
            WebAPISource({
                "endpoint": "https://api.example.com/news",
                "category": "news",
            })
        )
        .process(
            DataEnricherProcessor({"enrichment_type": "news", "processing_time": 0.8})
        )
        .process(
            DataEnricherProcessor({
                "enrichment_type": "sentiment",
                "processing_time": 0.5,
            })
        )
        .output(CSVOutputComponent({"output_file": "enriched_data_sequential.csv"}))
    )

    start_time = time.time()
    sequential_result = await sequential_pipeline.execute()
    end_time = time.time()

    print("\nSequential pipeline execution completed!")
    print(f"Execution time: {end_time - start_time:.2f} seconds")
    print(f"Status: {sequential_result['status']}")
    print(f"Processed items: {sequential_result['count']}")
    print(f"Output file: {sequential_result['output_file']}")


if __name__ == "__main__":
    asyncio.run(main())
