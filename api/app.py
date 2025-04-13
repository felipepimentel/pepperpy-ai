#!/usr/bin/env python3
"""
PepperPy API Server.

This module provides a FastAPI server that exposes PepperPy functionality
through REST APIs.
"""

import os
import sys
import json
import uuid
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import our standalone modules to avoid PepperPy dependency issues
from api.services.governance import execute_api_governance_check

# Import route modules
from api.routes.a2a import router as a2a_router
from api.routes import governance

# Import services
from api.services.governance import governance_service
from api.services.a2a import a2a_service

# Import middleware
from api.middleware import LoggingMiddleware

# Configure API logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api")

# Create FastAPI app
app = FastAPI(
    title="PepperPy API",
    description="REST API for PepperPy functionality",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)

# Include route modules
app.include_router(a2a_router, prefix="/api")
app.include_router(governance.router, prefix="/api")

# Session storage
sessions = {}

class Session(BaseModel):
    """Session information."""
    id: str
    workspace: str
    created_at: int
    active_workflows: List[str] = []
    resources: Dict[str, Any] = {}

class SessionResponse(BaseModel):
    """Session creation response."""
    session_id: str
    workspace: str

@app.on_event("startup")
async def startup_event():
    """Initialize services when the API starts."""
    logger.info("Initializing API services...")
    try:
        await governance_service.initialize()
        logger.info("Governance service initialized")
    except Exception as e:
        logger.error(f"Error initializing governance service: {str(e)}")
    
    try:
        await a2a_service.initialize()
        logger.info("A2A simulation service initialized")
    except Exception as e:
        logger.error(f"Error initializing A2A service: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services when the API shuts down."""
    logger.info("Cleaning up API services...")
    try:
        await governance_service.cleanup()
        logger.info("Governance service cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up governance service: {str(e)}")
    
    try:
        await a2a_service.cleanup()
        logger.info("A2A simulation service cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up A2A service: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Check if the API is running."""
    return {"status": "healthy"}

@app.get("/")
async def root():
    """Root endpoint that redirects to the API documentation."""
    return {
        "message": "Welcome to PepperPy API",
        "documentation": "/docs",
        "resources": {
            "governance": "/api/governance",
            "a2a": "/api/a2a"
        }
    }

@app.post("/api/session", response_model=SessionResponse)
async def create_session():
    """Create a new session."""
    session_id = str(uuid.uuid4())
    workspace_dir = Path(tempfile.mkdtemp(prefix=f"pepperpy-api-{session_id[:8]}-"))
    
    session = Session(
        id=session_id,
        workspace=str(workspace_dir),
        created_at=int(os.path.getctime(workspace_dir)),
        active_workflows=[],
        resources={}
    )
    
    sessions[session_id] = session
    
    return {
        "session_id": session_id,
        "workspace": str(workspace_dir)
    }

@app.get("/api/workflows")
async def get_workflows():
    """Get available workflows."""
    return {
        "workflows": [
            {
                "id": "governance",
                "name": "API Governance Assessment",
                "description": "Assess OpenAPI specifications against governance rules",
                "endpoints": ["/api/governance"]
            },
            {
                "id": "a2a",
                "name": "Agent-to-Agent Simulation",
                "description": "Simulate interactions between agents",
                "endpoints": ["/api/a2a/simulate"]
            }
        ]
    }

@app.post("/api/governance")
async def run_governance(
    spec_file: UploadFile = File(...),
    output_format: str = Form("json")
):
    """Run API governance assessment."""
    try:
        # Save uploaded file to temp directory
        temp_dir = Path(tempfile.mkdtemp(prefix="pepperpy-governance-"))
        temp_file = temp_dir / spec_file.filename
        
        with open(temp_file, "wb") as f:
            content = await spec_file.read()
            f.write(content)
        
        # Run governance check
        result = await execute_api_governance_check(str(temp_file), output_format)
        
        # Clean up
        os.unlink(temp_file)
        os.rmdir(temp_dir)
        
        # Return result
        if output_format == "json":
            return json.loads(result)
        else:
            return JSONResponse(
                content={"result": result},
                media_type="application/json"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 