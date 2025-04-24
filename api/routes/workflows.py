"""
API routes for workflows.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any

from api.services.workflow import (
    workflow_service
)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.get("/")
async def get_workflows():
    """
    Get a list of all available workflows.
    """
    try:
        return await workflow_service.get_workflows()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflows: {str(e)}")


@router.get("/{workflow_id}/schema")
async def get_workflow_schema(workflow_id: str):
    """
    Get the schema for a specific workflow.
    """
    try:
        return await workflow_service.get_workflow_schema(workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflow schema: {str(e)}")


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, request: Dict[str, Any]):
    """
    Execute a workflow with the provided input data.
    """
    try:
        return await workflow_service.execute_workflow(
            workflow_id=workflow_id,
            input_data=request.get("input_data", {}),
            config=request.get("config", {})
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}") 