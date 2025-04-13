#!/usr/bin/env python3
"""
Test script for Workflow Service (Mock Version)

This script demonstrates the usage pattern of the Workflow Service 
abstraction layer without requiring actual PepperPy modules.
"""

import asyncio
import json
from typing import Dict, Any, List

# Mock workflow service class for demonstration
class MockWorkflowService:
    """
    Mock implementation of the workflow service for testing.
    
    This demonstrates the abstraction pattern without requiring
    actual framework implementation.
    """
    
    def __init__(self):
        """Initialize the mock service."""
        self._initialized = False
        print("Mock workflow service created")
    
    async def initialize(self) -> None:
        """Initialize resources (mock)."""
        if self._initialized:
            return
            
        # Simulated initialization
        print("Initializing workflow service (mock)...")
        await asyncio.sleep(0.5)  # Simulate initialization time
        self._initialized = True
        print("Workflow service initialized")
    
    async def cleanup(self) -> None:
        """Clean up resources (mock)."""
        if not self._initialized:
            return
            
        # Simulated cleanup
        print("Cleaning up workflow service resources (mock)...")
        await asyncio.sleep(0.2)  # Simulate cleanup time
        self._initialized = False
        print("Workflow service resources cleaned up")
    
    async def get_available_workflows(self) -> List[str]:
        """
        Get available workflows (mock).
        
        Returns:
            List of workflow types.
        """
        # Simulated workflow list
        return ["api_governance", "api_blueprint", "api_evolution", "api_mock", "a2a_demo"]
    
    async def execute_workflow(self, 
                              workflow_type: str, 
                              input_data: Dict[str, Any],
                              config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute workflow (mock).
        
        This simulates workflow execution without actual framework calls.
        
        Args:
            workflow_type: Type of workflow
            input_data: Input data
            config: Configuration overrides
            
        Returns:
            Mock execution result.
        """
        # Simulate processing time
        print(f"Executing {workflow_type} workflow (mock)...")
        await asyncio.sleep(1)
        
        # Return simulated response based on workflow type
        if workflow_type == "api_governance":
            return {
                "status": "success",
                "message": "API governance assessment completed",
                "findings": {
                    "security": 3,
                    "standards": 1,
                    "documentation": 2
                },
                "pass_rate": "75%"
            }
        else:
            return {
                "status": "success",
                "message": f"{workflow_type} execution completed"
            }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow status (mock).
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Status information.
        """
        # Simulated status response
        return {
            "id": workflow_id,
            "status": "completed",
            "progress": 100,
            "started_at": "2023-07-15T10:30:00Z",
            "completed_at": "2023-07-15T10:31:05Z"
        }


# Dependency function - this would be in api/dependencies.py
async def get_workflow_service():
    """
    Provides the workflow service singleton.
    
    In a real implementation, this would return the
    actual service instance from api/services/workflow.py.
    """
    return workflow_service


# Singleton instance - this would be at the bottom of api/services/workflow.py
workflow_service = MockWorkflowService()


async def test_workflow_abstraction():
    """Test the workflow service abstraction pattern."""
    print("\n🔥 Testing Workflow Service Abstraction Pattern 🔥\n")

    # Get the service through the dependency function
    # This is how FastAPI endpoints would access it
    service = await get_workflow_service()
    
    # Initialize if needed
    await service.initialize()
    
    try:
        # 1. List available workflows
        print("\n📋 Available workflows:")
        workflows = await service.get_available_workflows()
        for workflow in workflows:
            print(f"  - {workflow}")
        
        # 2. Execute an API governance workflow
        print("\n🚀 Executing API governance workflow...")
        
        # Sample API spec
        sample_api = {
            "openapi": "3.0.0",
            "info": {
                "title": "Sample API",
                "version": "1.0.0"
            },
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get users"
                    }
                }
            }
        }
        
        input_data = {
            "task": "assess_api",
            "api_spec": sample_api,
            "output_format": "json"
        }
        
        # Custom configuration
        config = {
            "output_format": "json",
            "llm_config": {
                "provider": "openai",
                "model": "gpt-4"
            }
        }
        
        # Execute through the abstraction layer
        result = await service.execute_workflow(
            workflow_type="api_governance",
            input_data=input_data,
            config=config
        )
        
        # Display the result
        print(f"\n✅ Result status: {result.get('status', 'unknown')}")
        print(f"📊 Summary: {result.get('message', 'No message')}")
        print(f"🔍 Details:\n{json.dumps(result, indent=2)}")
        
        # 3. Check workflow status
        print("\n🔍 Checking workflow status...")
        status = await service.get_workflow_status("wf-12345")
        print(f"📊 Status:\n{json.dumps(status, indent=2)}")
        
    finally:
        # Clean up resources
        await service.cleanup()


# Run the demo
if __name__ == "__main__":
    print("\n==================================================")
    print("🚀 WORKFLOW ABSTRACTION DEMONSTRATION")
    print("==================================================")
    print("\nThis demonstrates how the API layer provides abstract")
    print("access to workflows without exposing plugin implementations.")
    print("\nKey principles demonstrated:")
    print("  - Dependency injection via get_workflow_service()")
    print("  - Abstract service interface")
    print("  - Configuration-based plugin selection")
    print("  - Resource lifecycle management")
    print("==================================================")
    
    asyncio.run(test_workflow_abstraction()) 