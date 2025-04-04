#!/usr/bin/env python3
"""
Intelligent agents example showing how to use PepperPy for different agent tasks.

This example demonstrates using PepperPy's intelligent agents for:
- Code analysis
- Content generation
- Technical writing
- Data extraction
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Output directory
OUTPUT_DIR = Path(__file__).parent / "output" / "agents"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def code_analysis_agent() -> None:
    """Run a code analysis agent."""
    # Sample code to analyze
    code = """
    def fibonacci(n):
        if n <= 0:
            return 0
        elif n == 1:
            return 1
        else:
            return fibonacci(n-1) + fibonacci(n-2)
            
    # Calculate the 10th Fibonacci number
    result = fibonacci(10)
    print(f"Fibonacci(10) = {result}")
    """

    # PepperPy internalizes the complexity of configuring, communicating, and saving results
    async with PepperPy().with_llm() as pepper:
        # The library handles prompt engineering, logging, and saving results
        await pepper.execute(
            "Analyze this code for efficiency, correctness, and improvements:",
            context={"code": code},
            output_path=OUTPUT_DIR / "code_analysis_result.txt",
        )


async def content_generation_agent() -> None:
    """Run a content generation agent."""
    # PepperPy handles all the prompt engineering, logging, and result management
    async with PepperPy().with_llm() as pepper:
        # The library creates proper prompts, logs operations, and saves results
        await pepper.execute(
            "Generate an informative blog post about AI in Healthcare for healthcare professionals, approximately 500 words long.",
            output_path=OUTPUT_DIR / "generated_content.txt",
        )


async def technical_writing_agent() -> None:
    """Run a technical writing agent."""
    # API endpoints to document
    endpoints = [
        {
            "name": "createDevice",
            "method": "POST",
            "path": "/devices",
            "params": ["name", "type", "location"],
            "description": "Creates a new IoT device",
        },
        {
            "name": "getDevice",
            "method": "GET",
            "path": "/devices/{deviceId}",
            "params": ["deviceId"],
            "description": "Gets a device by ID",
        },
        {
            "name": "updateDevice",
            "method": "PUT",
            "path": "/devices/{deviceId}",
            "params": ["deviceId", "name", "type", "location"],
            "description": "Updates a device",
        },
        {
            "name": "deleteDevice",
            "method": "DELETE",
            "path": "/devices/{deviceId}",
            "params": ["deviceId"],
            "description": "Deletes a device by ID",
        },
    ]

    # The library handles forming well-structured prompts and logging
    async with PepperPy().with_llm() as pepper:
        # All the complexity of prompt engineering and logging is handled internally
        await pepper.execute(
            "Create detailed API Documentation for SmartIoT Hub, covering all provided endpoints.",
            context={"endpoints": endpoints},
            output_path=OUTPUT_DIR / "technical_documentation.md",
        )


async def data_extraction_agent() -> None:
    """Run a data extraction agent."""
    # Sample text with structured information
    text = """
    Product Information:
    Name: Ultra HD Smart TV X9000
    SKU: TV-X9000-65
    Price: $1,499.99
    Availability: In Stock (15 units)
    
    Features:
    - 65" 4K Ultra HD Display (3840x2160)
    - HDR10+ and Dolby Vision Support
    - Smart TV with AI Assistant
    - 4 HDMI ports, 3 USB ports
    - Wireless Connectivity: Wi-Fi 6, Bluetooth 5.0
    
    Customer Reviews:
    Average Rating: 4.7/5 (based on 128 reviews)
    
    Contact Information:
    Phone: (800) 555-1234
    Email: support@electronics-store.com
    """

    # Schema for data extraction
    schema = {
        "product_name": "string",
        "sku": "string",
        "price": "float",
        "availability": {"status": "string", "quantity": "integer"},
        "features": "list of strings",
        "rating": "float",
        "review_count": "integer",
        "contact": {"phone": "string", "email": "string"},
    }

    # The library handles everything from extraction to saving and logging
    async with PepperPy().with_llm() as pepper:
        # The library should handle complex prompts, JSON parsing, and logging
        await pepper.execute_json(
            prompt="Extract product information according to the schema",
            text=text,
            schema=schema,
            output_path=OUTPUT_DIR / "extracted_data.json",
        )


async def main() -> None:
    """Run all intelligent agents examples."""
    # PepperPy should handle both console output and logging
    pepper = PepperPy()
    await pepper.initialize(
        output_dir=OUTPUT_DIR, log_level="INFO", log_to_console=True, log_to_file=True
    )

    await pepper.log_header("PEPPERPY INTELLIGENT AGENTS EXAMPLE")

    await code_analysis_agent()
    await content_generation_agent()
    await technical_writing_agent()
    await data_extraction_agent()

    # Finalize with automatic summary of results
    await pepper.finalize(
        summary_message="All agent examples completed!", output_dir=OUTPUT_DIR
    )


if __name__ == "__main__":
    asyncio.run(main())
