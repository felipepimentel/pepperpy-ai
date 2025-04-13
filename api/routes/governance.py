"""
API Governance routes.

This module provides the FastAPI routes for API governance assessment.
"""

import os
import uuid
import tempfile
from typing import Optional, List, Dict, Any, Union
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime

from api.services.governance import execute_api_governance_check
from playground.workflows.api_governance_workflow import execute_api_governance_workflow


# Models
class GovernanceAssessmentRequest(BaseModel):
    """Request model for governance assessment."""
    file_path: Optional[str] = None
    output_format: str = "json"


class ApiInfoResponse(BaseModel):
    """Response model for API info."""
    api_name: str
    api_version: str
    assessment_date: str


class GovernanceRules(BaseModel):
    """Governance rules configuration."""
    security: List[Dict[str, Any]] = []
    standards: List[Dict[str, Any]] = []
    performance: Dict[str, Any] = {}


class GovernanceRequest(BaseModel):
    """Request model for API governance assessment."""
    output_format: str = "json"
    rules: Optional[GovernanceRules] = None


# Router
router = APIRouter(
    prefix="/governance",
    tags=["governance"],
    responses={404: {"description": "Not found"}},
)


@router.post("/assess")
async def assess_api(
    spec_file: UploadFile = File(...),
    output_format: str = Form("json")
):
    """
    Assess an API specification against governance rules.
    
    Args:
        spec_file: The API specification file (OpenAPI/Swagger)
        output_format: The output format (json, markdown, html)
    
    Returns:
        The assessment report in the specified format
    """
    # Create a temporary file to store the uploaded spec
    temp_dir = tempfile.mkdtemp()
    try:
        # Get the file extension
        file_extension = os.path.splitext(spec_file.filename)[1]
        if not file_extension:
            # Default to yaml if no extension
            file_extension = ".yaml"
        
        # Save the uploaded file
        temp_file_path = os.path.join(temp_dir, f"api_spec{file_extension}")
        contents = await spec_file.read()
        
        with open(temp_file_path, "wb") as f:
            f.write(contents)
        
        # Execute governance check
        result = await execute_api_governance_check(temp_file_path, output_format)
        
        # Set correct content type based on format
        content_type = "application/json"
        if output_format.lower() == "markdown":
            content_type = "text/markdown"
        elif output_format.lower() == "html":
            content_type = "text/html"
        
        return JSONResponse(
            content=result if output_format.lower() == "json" else {"result": result},
            media_type=content_type
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to assess API: {str(e)}"
        )
    finally:
        # Clean up the temporary directory
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)


@router.post("/check")
async def check_api_specification(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    output_format: str = Form("json")
):
    """
    Assess an API specification against governance rules.
    
    Args:
        background_tasks: FastAPI background tasks manager
        file: The API specification file (OpenAPI/Swagger)
        output_format: Format for the assessment report (json, markdown, html)
        
    Returns:
        JSON response with the assessment results or a status message
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    # Validate file type
    if not file.filename.endswith(('.json', '.yaml', '.yml')):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Only JSON and YAML files are supported."
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file with timestamp to avoid name conflicts
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = f"{upload_dir}/{timestamp}_{file.filename}"
    
    try:
        # Save uploaded file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
            
        # Execute the governance workflow
        result = execute_api_governance_workflow(
            api_spec_path=file_path,
            output_format=output_format
        )
        
        # Clean up the file in the background after processing
        background_tasks.add_task(os.remove, file_path)
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except Exception as e:
        # Make sure to clean up the file even if there's an error
        if os.path.exists(file_path):
            background_tasks.add_task(os.remove, file_path)
        
        raise HTTPException(status_code=500, detail=f"Error processing API: {str(e)}")


@router.post("/check-url")
async def check_api_url(request: GovernanceRequest):
    """
    Assess an API specification available at a URL.
    
    Args:
        request: GovernanceRequest with URL and output format
        
    Returns:
        JSON response with the assessment results
    """
    # This endpoint would fetch the API spec from a URL and assess it
    # For now, we'll return a placeholder response
    return JSONResponse(
        status_code=501,
        content={"message": "URL-based API assessment not implemented yet"}
    ) 