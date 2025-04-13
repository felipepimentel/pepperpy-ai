#!/usr/bin/env python3
"""
Test script for API Governance workflow.
"""

import os
import json
import asyncio
from pathlib import Path

async def main():
    """Run a test of the API Governance workflow."""
    try:
        # Import playground workflow directly
        from playground.workflows.api_governance_workflow import execute_api_governance_workflow
        
        # Sample OpenAPI spec file
        sample_spec = Path('playground/workflows/sample_petstore.yaml')
        if not sample_spec.exists():
            print(f"Error: Sample spec file not found at {sample_spec}")
            return
        
        # Execute the workflow
        print(f"Running API governance check on {sample_spec}...")
        result = await execute_api_governance_workflow(str(sample_spec), "json")
        
        # Print the result
        print("\nExecution complete!")
        print(f"Result: {result[:100]}...")  # Show the first 100 chars
        
        # Save result to file
        output_file = Path('api_governance_result.json')
        with open(output_file, 'w') as f:
            f.write(result)
        
        print(f"Result saved to {output_file}")
    
    except ImportError as e:
        print(f"Error importing module: {e}")
    except Exception as e:
        print(f"Error executing workflow: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 