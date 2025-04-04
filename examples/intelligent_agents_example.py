#!/usr/bin/env python3
"""
Intelligent Agents Example with PepperPy.

This example demonstrates how to use PepperPy's declarative API for intelligent
agent tasks such as code analysis, content generation, technical writing, and data extraction.
"""

import asyncio
from pathlib import Path

from pepperpy import PepperPy

# Define output directory
OUTPUT_DIR = Path(__file__).parent / "output" / "agents"


async def main():
    """Run intelligent agent examples using PepperPy's declarative API."""
    # Setup pipeline with configuration
    pepper = PepperPy().configure(
        output_dir=OUTPUT_DIR,
        log_level="INFO",
        log_to_console=True,
        auto_save_results=True,
    )

    # Sample data for tasks
    code_sample = """
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

    api_endpoints = [
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

    product_data = """
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

    # Define all agent tasks declaratively
    tasks = [
        # Code Analysis Task
        pepper.agent_task("code_analysis")
        .prompt("Analyze this code for efficiency, correctness, and improvements:")
        .context({"code": code_sample})
        .capability("code_analysis")
        .output("code_analysis_result.txt"),
        # Content Generation Task
        pepper.agent_task("content_generation")
        .prompt(
            "Generate an informative blog post about AI in Healthcare for healthcare professionals, approximately 500 words long."
        )
        .capability("content_generation")
        .parameters({"style": "professional", "max_words": 500})
        .output("generated_content.txt"),
        # Technical Writing Task
        pepper.agent_task("technical_writing")
        .prompt(
            "Create detailed API Documentation for SmartIoT Hub, covering all provided endpoints."
        )
        .context({"endpoints": api_endpoints})
        .capability("technical_writing")
        .format("markdown")
        .output("technical_documentation.md"),
        # Data Extraction Task
        pepper.agent_task("data_extraction")
        .prompt("Extract structured product information")
        .context({"text": product_data})
        .schema({
            "product_name": "string",
            "sku": "string",
            "price": "float",
            "availability": {"status": "string", "quantity": "integer"},
            "features": "list of strings",
            "rating": "float",
            "review_count": "integer",
            "contact": {"phone": "string", "email": "string"},
        })
        .capability("data_extraction")
        .output("extracted_data.json"),
    ]

    # Execute all tasks at once - potentially in parallel
    await pepper.run_tasks(tasks)

    # Display results
    print("\nAll intelligent agent tasks completed successfully!")
    print(f"Results saved to {OUTPUT_DIR}")
    for task in tasks:
        print(f"- {task.name}: Task completed")


if __name__ == "__main__":
    asyncio.run(main())
