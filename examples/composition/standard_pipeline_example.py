#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example demonstrating the use of standard pipelines in the PepperPy framework.

This example shows how to create a simple data processing pipeline using the
composition API to fetch data from an RSS feed, process it, and output the results.
"""

import asyncio
from typing import Dict, Any, List

from pepperpy.core.composition import compose
from pepperpy.core.composition.base import SourceComponentBase, ProcessorComponentBase, OutputComponentBase


class RSSFeedSource(SourceComponentBase[List[Dict[str, Any]]]):
    """Source component that fetches data from an RSS feed."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the RSS feed source.

        Args:
            config: Configuration dictionary containing the RSS feed URL.
        """
        super().__init__(config)
        self.url = config.get("url", "https://example.com/rss")

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch data from the RSS feed.

        Returns:
            List of dictionaries containing the RSS feed items.
        """
        print(f"Fetching RSS feed from {self.url}")
        # In a real implementation, this would use aiohttp or similar to fetch the feed
        # For this example, we'll return mock data
        return [
            {
                "title": "Item 1",
                "description": "Description 1",
                "link": "https://example.com/1",
            },
            {
                "title": "Item 2",
                "description": "Description 2",
                "link": "https://example.com/2",
            },
            {
                "title": "Item 3",
                "description": "Description 3",
                "link": "https://example.com/3",
            },
        ]


class ContentExtractorProcessor(ProcessorComponentBase[List[Dict[str, Any]], List[Dict[str, Any]]]):
    """Processor component that extracts content from RSS feed items."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the content extractor processor.

        Args:
            config: Configuration dictionary.
        """
        super().__init__(config)

    async def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and enhance content from RSS feed items.

        Args:
            data: List of dictionaries containing RSS feed items.

        Returns:
            Enhanced list of dictionaries with extracted content.
        """
        print(f"Processing {len(data)} RSS feed items")
        result = []
        for item in data:
            # In a real implementation, this might fetch the full article content
            enhanced_item = item.copy()
            enhanced_item["extracted_content"] = f"Extended content for {item['title']}"
            result.append(enhanced_item)
        return result


class JSONOutputComponent(OutputComponentBase[List[Dict[str, Any]]]):
    """Output component that formats data as JSON."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the JSON output component.

        Args:
            config: Configuration dictionary.
        """
        super().__init__(config)
        self.output_file = config.get("output_file", "output.json")

    async def output(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format and output the data as JSON.

        Args:
            data: List of dictionaries to output.

        Returns:
            Dictionary containing the result information.
        """
        print(f"Outputting {len(data)} items to {self.output_file}")
        # In a real implementation, this would write to a file
        # For this example, we'll just print the data
        for item in data:
            print(f"Title: {item['title']}")
            print(f"Description: {item['description']}")
            print(f"Extracted Content: {item.get('extracted_content', 'N/A')}")
            print("-" * 50)

        return {
            "status": "success",
            "count": len(data),
            "output_file": self.output_file,
        }


async def main():
    """Run the example pipeline."""
    # Create a pipeline using the composition API
    pipeline = (
        compose("RSS Processing Pipeline")
        .source(RSSFeedSource({"url": "https://news.example.com/rss"}))
        .process(ContentExtractorProcessor({}))
        .output(JSONOutputComponent({"output_file": "processed_feed.json"}))
    )

    # Execute the pipeline
    result = await pipeline.execute()

    print("\nPipeline execution completed!")
    print(f"Status: {result['status']}")
    print(f"Processed items: {result['count']}")
    print(f"Output file: {result['output_file']}")


if __name__ == "__main__":
    asyncio.run(main())
