"""
PepperPy HTTP Server Module.

This module provides HTTP server functionality for the PepperPy framework.
"""

# Define empty __all__ by default
__all__ = []

# Try to import server components, but don't fail if dependencies are missing
try:
    # Check if starlette is available
    import starlette

    # Import server components
    from starlette.applications import Starlette as HTTPServer
    from starlette.middleware import Middleware
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Route, Router
    from starlette.websockets import WebSocket, WebSocketDisconnect

    # Update exports
    __all__ = [
        "HTTPServer",
        "Route",
        "Router",
        "Middleware",
        "Request",
        "Response",
        "WebSocket",
        "WebSocketDisconnect",
    ]
except ImportError:
    # Starlette is not installed, provide minimal interface
    pass
