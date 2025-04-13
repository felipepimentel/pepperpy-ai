"""
API routes for workflows.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any

from api.services.mock_workflow_service import (
    WorkflowInfo, 
    WorkflowSchema,
    WorkflowExecuteRequest,
    WorkflowResult,
    mock_workflow_service
)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.get("/", response_model=List[WorkflowInfo])
async def get_workflows():
    """
    Get a list of all available workflows.
    """
    try:
        return await mock_workflow_service.get_available_workflows()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflows: {str(e)}")


@router.get("/{workflow_id}/schema", response_model=WorkflowSchema)
async def get_workflow_schema(workflow_id: str):
    """
    Get the schema for a specific workflow.
    """
    try:
        return await mock_workflow_service.get_workflow_schema(workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflow schema: {str(e)}")


@router.post("/{workflow_id}/execute", response_model=WorkflowResult)
async def execute_workflow(workflow_id: str, request: WorkflowExecuteRequest):
    """
    Execute a workflow with the provided input data.
    """
    try:
        return await mock_workflow_service.execute_workflow(
            workflow_id=workflow_id,
            input_data=request.input_data,
            config=request.config
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}") 