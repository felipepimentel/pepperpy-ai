"""Monitoring dashboard for Pepperpy.

This module provides a web-based monitoring dashboard:
- System metrics visualization
- Health check status
- Trace visualization
- Log viewer
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.monitoring.health import HealthManager
from pepperpy.monitoring.metrics import MetricsManager
from pepperpy.monitoring.tracing import TracingManager

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Pepperpy Monitoring")

# Set up templates
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Serve static files
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)


class DashboardManager(Lifecycle):
    """Manages monitoring dashboard."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        """Initialize dashboard manager.

        Args:
            config: Optional dashboard configuration
        """
        super().__init__()
        self.config = config or {}
        self._health = HealthManager()
        self._metrics = MetricsManager()
        self._tracing = TracingManager()
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize dashboard manager.

        This sets up the monitoring components and web server.
        """
        try:
            # Initialize components
            await self._health.initialize()
            await self._metrics.initialize()
            await self._tracing.initialize()

            # Set up routes
            self._setup_routes()

            self._state = ComponentState.RUNNING
            logger.info("Dashboard manager initialized")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize dashboard: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up dashboard manager."""
        try:
            # Clean up components
            await self._health.cleanup()
            await self._metrics.cleanup()
            await self._tracing.cleanup()

            self._state = ComponentState.UNREGISTERED
            logger.info("Dashboard manager cleaned up")

        except Exception as e:
            logger.error(f"Failed to cleanup dashboard: {e}")
            raise

    def _setup_routes(self) -> None:
        """Set up dashboard routes."""

        @app.get("/", response_class=HTMLResponse)
        async def index():
            """Render dashboard index."""
            return templates.TemplateResponse(
                "index.html",
                {"request": None},
            )

        @app.get("/health")
        async def health():
            """Get health status."""
            if self._health.state != ComponentState.RUNNING:
                raise HTTPException(503, "Health manager not running")
            return self._health.get_status()

        @app.get("/metrics")
        async def metrics():
            """Get system metrics."""
            if self._metrics.state != ComponentState.RUNNING:
                raise HTTPException(503, "Metrics manager not running")
            return self._metrics.get_metrics()

        @app.get("/traces")
        async def traces():
            """Get active traces."""
            if self._tracing.state != ComponentState.RUNNING:
                raise HTTPException(503, "Tracing manager not running")
            return self._tracing.get_active_traces()
