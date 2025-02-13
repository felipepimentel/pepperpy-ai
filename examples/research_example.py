"""Example demonstrating the research functionality of Pepperpy.

This example shows how to:
1. Initialize Pepperpy with minimal configuration
2. Perform research on a topic
3. Access research results in different formats
"""

import asyncio

from pepperpy import Pepperpy


async def main():
    # Initialize with auto-configuration
    pepper = await Pepperpy.create()

    # Perform research with different options
    result = await pepper.research(
        "Impact of AI in Healthcare",
        depth="comprehensive",  # Options: basic, detailed, comprehensive
        style="academic",  # Options: academic, business, casual
        format="report",  # Options: report, summary, bullets
        max_sources=5,  # Maximum number of sources to use
    )

    # Access results in different formats
    print("\nQuick Summary:")
    print(result.tldr)

    print("\nMain Points:")
    for point in result.bullets:
        print(f"- {point}")

    print("\nDetailed Report:")
    print(result.full)

    print("\nReferences:")
    for ref in result.references:
        print(f"- {ref['title']} ({ref['year']})")
        print(f"  {ref['url']}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
