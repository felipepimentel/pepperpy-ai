"""API middleware for security and logging."""
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

def setup_middleware(app: FastAPI) -> None:
    """Set up all middleware for the application."""
    
    # Add CORS middleware with strict settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:*; "
                "style-src 'self' 'unsafe-inline'; "
                "connect-src 'self' http://localhost:* ws://localhost:*; "
                "img-src 'self' data: blob: http://localhost:*; "
                "font-src 'self' data:;"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
        }
        
        for key, value in headers.items():
            response.headers[key] = value
            
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request timing and status."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        formatted_process_time = '{0:.2f}'.format(process_time)
        
        request.app.logger.info(
            f"{request.client.host}:{request.client.port} - "
            f"\"{request.method} {request.url.path}\" {response.status_code} "
            f"completed in {formatted_process_time}ms"
        )
        
        return response 