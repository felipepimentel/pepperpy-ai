"""API routes module."""

# Import all route modules here
from api.routes import workflows, a2a, governance, todos 

from fastapi import FastAPI

def register_routes(app: FastAPI) -> None:
    """Register all API routes.
    
    Args:
        app: FastAPI application instance
    """
    # Include routers
    app.include_router(governance.router, prefix="/api/governance", tags=["governance"])
    app.include_router(a2a.router, prefix="/api/a2a", tags=["a2a"])
    app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
    app.include_router(todos.router, prefix="/api/todos", tags=["todos"]) 