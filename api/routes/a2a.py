"""
A2A API Routes

Routes for Agent-to-Agent communication simulation API.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator

from api.services.a2a import A2ASimulationService
from api.dependencies import get_a2a_service

# Configure route-specific logging
logger = logging.getLogger("api.routes.a2a")

router = APIRouter(prefix="/a2a", tags=["A2A Simulation"])

# Request and response models

class SimulationConfig(BaseModel):
    """Configuration for an A2A simulation."""
    max_turns: int = Field(5, description="Maximum number of message exchanges")
    timeout_seconds: int = Field(60, description="Maximum runtime in seconds")
    enable_reflection: bool = Field(False, description="Enable agent reflection capabilities")
    response_format: Optional[str] = Field(None, description="Desired format for agent responses")

class SimulationRequest(BaseModel):
    """Request to run an A2A simulation."""
    agent1_prompt: str = Field(..., description="Initial prompt for the first agent")
    agent2_prompt: str = Field(..., description="Initial prompt for the second agent")
    initial_message: str = Field(..., description="Message to start the conversation")
    config: Optional[SimulationConfig] = Field(None, description="Simulation configuration")

class SimulationResponse(BaseModel):
    """Response from an A2A simulation run."""
    simulation_id: str
    conversation: List[Dict[str, Any]]
    completed: bool
    turns_executed: int
    runtime_seconds: float
    terminated_reason: Optional[str] = None

class StatusResponse(BaseModel):
    """Status of the A2A simulation service."""
    status: str
    active_simulations: int
    uptime_seconds: float
    version: str

# Routes

@router.post("/simulate", response_model=SimulationResponse)
async def run_simulation(
    request: SimulationRequest,
    a2a_service: A2ASimulationService = Depends(get_a2a_service)
):
    """
    Run an Agent-to-Agent (A2A) simulation with the provided configuration.
    Returns the conversation history and simulation metrics.
    """
    try:
        result = await a2a_service.run_simulation(
            agent1_prompt=request.agent1_prompt,
            agent2_prompt=request.agent2_prompt,
            initial_message=request.initial_message,
            config=request.config.dict() if request.config else {}
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {str(e)}"
        )

@router.get("/status", response_model=StatusResponse)
async def get_status(
    a2a_service: A2ASimulationService = Depends(get_a2a_service)
):
    """
    Get the current status of the A2A simulation service.
    Returns metrics about service health and active simulations.
    """
    return await a2a_service.get_status()

@router.post("/reset", response_model=StatusResponse)
async def reset_service(
    background_tasks: BackgroundTasks,
    a2a_service: A2ASimulationService = Depends(get_a2a_service)
):
    """
    Reset the A2A simulation service.
    Cleans up resources and reinitializes the service.
    """
    # Use background tasks to avoid blocking the request
    background_tasks.add_task(a2a_service.reset)
    
    # Return current status before reset completes
    return await a2a_service.get_status() 