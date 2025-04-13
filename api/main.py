"""
PepperPy API Server

Main FastAPI application entry point.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from api.routes import governance, a2a

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api")

# Create FastAPI app
app = FastAPI(
    title="PepperPy API",
    description="API for PepperPy workflows and services",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(governance.router)
app.include_router(a2a.router)

@app.get("/", tags=["root"])
async def root():
    """Root endpoint that returns API information."""
    return {
        "name": "PepperPy API",
        "version": "0.1.0",
        "description": "API for PepperPy workflows and services",
        "endpoints": {
            "governance": "/governance",
            "a2a": "/a2a"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Serve static files if they exist
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend/dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run the API server
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True) 