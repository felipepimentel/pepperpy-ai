"""
API Dependencies

This module provides FastAPI dependency functions to obtain service instances.
"""

from fastapi import Depends

from api.services.a2a import a2a_service
from api.services.governance import governance_service
from api.services.workflow import workflow_service

async def get_a2a_service():
    """
    Provides a singleton instance of the A2A simulation service.
    Used as a FastAPI dependency for routes that require A2A functionality.
    """
    return a2a_service

async def get_governance_service():
    """
    Provides a singleton instance of the API governance service.
    Used as a FastAPI dependency for routes that require governance functionality.
    """
    return governance_service 

async def get_workflow_service():
    """
    Provides a singleton instance of the workflow service.
    Used as a FastAPI dependency for routes that require workflow orchestration.
    """
    return workflow_service 