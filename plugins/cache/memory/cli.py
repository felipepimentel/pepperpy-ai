#!/usr/bin/env python3
"""CLI for direct access to memory cache provider."""

import argparse
import asyncio
import json
import sys
from typing import Any

from plugins.cache.memory.provider import MemoryCacheProvider


async def main() -> None:
    """Direct CLI access to memory cache functionality."""
    parser = argparse.ArgumentParser(description="Memory Cache CLI")
    parser.add_argument(
        "task",
        choices=["get", "set", "delete", "invalidate_tag", "clear", "search"],
        help="Task to execute",
    )
    parser.add_argument("--key", help="Cache key")
    parser.add_argument("--value", help="Value to cache")
    parser.add_argument("--ttl", type=int, help="Time to live in seconds")
    parser.add_argument("--tag", help="Tag to invalidate")
    parser.add_argument("--tags", help="Comma-separated list of tags")
    parser.add_argument("--default", help="Default value if key not found")
    parser.add_argument(
        "--max-entries", type=int, default=10000, help="Maximum cache entries"
    )
    parser.add_argument(
        "--default-ttl", type=int, default=3600, help="Default TTL in seconds"
    )
    parser.add_argument(
        "--purge-only",
        action="store_true",
        help="For clear task: only purge expired entries",
    )
    parser.add_argument(
        "--query", help="JSON query for metadata search (for search task)"
    )

    args = parser.parse_args()

    # Create adapter directly
    adapter = MemoryCacheProvider(
        max_entries=args.max_entries, default_ttl=args.default_ttl
    )

    # Use context manager for proper resource management
    async with adapter:
        # Prepare input data
        input_data: dict[str, Any] = {"task": args.task}

        if args.key is not None:
            input_data["key"] = args.key

        if args.value is not None:
            input_data["value"] = args.value

        if args.ttl is not None:
            input_data["ttl"] = args.ttl

        if args.tag is not None:
            input_data["tag"] = args.tag

        if args.tags is not None:
            input_data["tags"] = args.tags.split(",")

        if args.default is not None:
            input_data["default"] = args.default

        if args.purge_only and args.task == "clear":
            input_data["purge_only"] = True

        if args.query and args.task == "search":
            try:
                input_data["query"] = json.loads(args.query)
            except json.JSONDecodeError:
                print("Error: query must be valid JSON")
                sys.exit(1)

        # Execute task
        result = await adapter.execute(input_data)

        # Print result as JSON
        print(json.dumps(result, indent=2))

        if result["status"] != "success":
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
