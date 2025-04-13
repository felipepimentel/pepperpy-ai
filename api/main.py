"""
Main FastAPI application for PepperPy API Server.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from api.routes import governance, a2a, workflows

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api")

# Create FastAPI application
app = FastAPI(
    title="PepperPy API Server",
    description="REST API for PepperPy workflows and services",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(governance.router)
app.include_router(a2a.router)
app.include_router(workflows.router)

@app.get("/", tags=["root"])
async def root():
    """Root endpoint that returns API information."""
    return {
        "name": "PepperPy API",
        "version": "0.1.0",
        "description": "API for PepperPy workflows and services",
        "endpoints": {
            "governance": "/governance",
            "a2a": "/a2a",
            "workflows": "/workflows"
        }
    }

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

# Serve static files if they exist
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend/dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

@app.on_event("startup")
async def startup_event():
    """
    Perform initialization on startup.
    """
    logger.info("Starting PepperPy API Server")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Perform cleanup on shutdown.
    """
    logger.info("Shutting down PepperPy API Server")

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run the API server
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True) 