"""
API Ready Workflow Provider for PepperPy.

This workflow enhances existing APIs to make them AI/agent-ready by adding
discovery, authentication, and observability features.
"""

import os
import json
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, TypedDict, Union, Literal

from pepperpy.core.logging import get_logger
from pepperpy.plugin import ProviderPlugin
from pepperpy.workflow import BaseWorkflowProvider

logger = get_logger(__name__)

class APIScaffoldConfig(TypedDict):
    """Configuration for API scaffolding."""
    agent_discovery: bool
    auth_mechanism: Literal["api_key", "oauth", "jwt", "none"]
    observability: bool
    rate_limiting: bool
    documentation: bool


class EnhancementResult(TypedDict):
    """Results of API enhancement."""
    original_endpoints: int
    enhanced_endpoints: int
    added_endpoints: List[str]
    enhancement_summary: str
    spec_path: str


class APIReadyProvider(BaseWorkflowProvider, ProviderPlugin):
    """Provider for making APIs agent-ready.
    
    This workflow takes an existing API specification and enhances it with
    features necessary for effective agent interaction, including discovery,
    authentication, and observability.
    """
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return
        
        logger.info("Initializing API Ready workflow provider")
        
        # Initialize properties from config
        self.llm_provider = self.config.get("llm_config", {}).get("provider", "openai")
        self.llm_model = self.config.get("llm_config", {}).get("model", "gpt-4")
        
        # Default enhancement options
        self.default_scaffold_config = APIScaffoldConfig(
            agent_discovery=True,
            auth_mechanism="api_key",
            observability=True,
            rate_limiting=True,
            documentation=True
        )
        
        self.initialized = True
        logger.info("API Ready workflow provider initialized")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return
        
        logger.info("Cleaning up API Ready workflow provider")
        self.initialized = False
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the API Ready workflow.
        
        Args:
            input_data: Dict containing:
                - spec_path: Path to the API spec file
                - enhancement_options: Options for API enhancement
                - output_dir: Directory to save enhanced spec
        
        Returns:
            Results of the enhancement process
        """
        try:
            if not self.initialized:
                await self.initialize()
            
            # Extract and validate input
            spec_path = input_data.get("spec_path")
            if not spec_path or not os.path.exists(spec_path):
                return {"error": "Missing or invalid API specification path"}
            
            enhancement_options = input_data.get("enhancement_options", {})
            output_dir = input_data.get("output_dir", os.path.dirname(spec_path))
            
            # Load the API spec
            spec_content = await self._load_api_spec(spec_path)
            
            # Merge default scaffold config with provided options
            scaffold_config = {**self.default_scaffold_config}
            if enhancement_options:
                for key in scaffold_config:
                    if key in enhancement_options:
                        scaffold_config[key] = enhancement_options[key]
            
            # Enhance the API spec
            enhanced_spec, enhancements = await self._enhance_api_spec(
                spec_content, 
                scaffold_config
            )
            
            # Save the enhanced spec
            output_path = await self._save_enhanced_spec(
                enhanced_spec, 
                spec_path, 
                output_dir
            )
            
            # Generate enhancement report
            result = EnhancementResult(
                original_endpoints=enhancements["original_endpoints"],
                enhanced_endpoints=enhancements["enhanced_endpoints"],
                added_endpoints=enhancements["added_endpoints"],
                enhancement_summary=enhancements["summary"],
                spec_path=output_path
            )
            
            return {
                "status": "success", 
                "result": result,
                "message": f"API enhanced successfully. Output saved to {output_path}"
            }
            
        except Exception as e:
            logger.error(f"Error executing API Ready workflow: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _load_api_spec(self, spec_path: str) -> Dict[str, Any]:
        """Load an API specification from file.
        
        Args:
            spec_path: Path to the API spec file
            
        Returns:
            API specification as a dictionary
        """
        try:
            with open(spec_path, "r") as f:
                content = f.read()
            
            # Parse based on file extension
            if spec_path.endswith((".yaml", ".yml")):
                import yaml
                return yaml.safe_load(content)
            elif spec_path.endswith(".json"):
                return json.loads(content)
            else:
                # Try to guess format
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    import yaml
                    return yaml.safe_load(content)
        
        except Exception as e:
            raise ValueError(f"Failed to load API specification: {str(e)}")
    
    async def _enhance_api_spec(self, 
                               spec: Dict[str, Any], 
                               scaffold_config: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Enhance the API specification with agent-ready features.
        
        Args:
            spec: Original API specification
            scaffold_config: Enhancement configuration
            
        Returns:
            Tuple of (enhanced spec, enhancement details)
        """
        # Count original endpoints
        original_endpoints = 0
        for path in spec.get("paths", {}):
            original_endpoints += len([m for m in spec["paths"][path] 
                                    if m in ["get", "post", "put", "delete", "patch"]])
        
        # Initialize enhancement tracking
        added_endpoints = []
        
        # Clone the spec to avoid modifying the original
        enhanced_spec = json.loads(json.dumps(spec))
        
        # Ensure components section exists
        if "components" not in enhanced_spec:
            enhanced_spec["components"] = {}
        
        # 1. Add agent discovery if requested
        if scaffold_config.get("agent_discovery"):
            discovery_path = "/.well-known/ai-plugin.json"
            if discovery_path not in enhanced_spec.get("paths", {}):
                if "paths" not in enhanced_spec:
                    enhanced_spec["paths"] = {}
                
                enhanced_spec["paths"][discovery_path] = {
                    "get": {
                        "summary": "Agent discovery endpoint",
                        "description": "Returns information about this API for agent discovery",
                        "operationId": "getAgentDiscovery",
                        "tags": ["Discovery"],
                        "responses": {
                            "200": {
                                "description": "Agent discovery information",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/AgentDiscovery"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                added_endpoints.append(discovery_path)
                
                # Add schema for discovery response
                if "schemas" not in enhanced_spec["components"]:
                    enhanced_spec["components"]["schemas"] = {}
                
                enhanced_spec["components"]["schemas"]["AgentDiscovery"] = {
                    "type": "object",
                    "properties": {
                        "schema_version": {"type": "string"},
                        "name_for_human": {"type": "string"},
                        "name_for_model": {"type": "string"},
                        "description_for_human": {"type": "string"},
                        "description_for_model": {"type": "string"},
                        "auth": {"type": "object"},
                        "api": {"type": "object"},
                        "logo_url": {"type": "string"},
                        "contact_email": {"type": "string"},
                        "legal_info_url": {"type": "string"}
                    }
                }
        
        # 2. Add authentication mechanism if requested
        if scaffold_config.get("auth_mechanism") != "none":
            auth_type = scaffold_config.get("auth_mechanism")
            
            # Ensure securitySchemes section exists
            if "securitySchemes" not in enhanced_spec["components"]:
                enhanced_spec["components"]["securitySchemes"] = {}
            
            if auth_type == "api_key":
                enhanced_spec["components"]["securitySchemes"]["ApiKeyAuth"] = {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-KEY"
                }
                
                # Apply security globally if not already defined
                if "security" not in enhanced_spec:
                    enhanced_spec["security"] = [{"ApiKeyAuth": []}]
                    
            elif auth_type == "oauth":
                enhanced_spec["components"]["securitySchemes"]["OAuth2"] = {
                    "type": "oauth2",
                    "flows": {
                        "clientCredentials": {
                            "tokenUrl": "/oauth/token",
                            "scopes": {
                                "read": "Read access",
                                "write": "Write access"
                            }
                        }
                    }
                }
                
                # Apply security globally if not already defined
                if "security" not in enhanced_spec:
                    enhanced_spec["security"] = [{"OAuth2": ["read", "write"]}]
                    
            elif auth_type == "jwt":
                enhanced_spec["components"]["securitySchemes"]["BearerAuth"] = {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
                
                # Apply security globally if not already defined
                if "security" not in enhanced_spec:
                    enhanced_spec["security"] = [{"BearerAuth": []}]
            
            # Add auth endpoints if needed
            if auth_type == "oauth":
                if "/oauth/token" not in enhanced_spec.get("paths", {}):
                    enhanced_spec["paths"]["/oauth/token"] = {
                        "post": {
                            "summary": "Get OAuth token",
                            "description": "Exchange client credentials for an access token",
                            "operationId": "getOAuthToken",
                            "tags": ["Authentication"],
                            "security": [],  # No auth required for token endpoint
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/x-www-form-urlencoded": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "grant_type": {"type": "string", "enum": ["client_credentials"]},
                                                "client_id": {"type": "string"},
                                                "client_secret": {"type": "string"}
                                            },
                                            "required": ["grant_type", "client_id", "client_secret"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "OAuth token response",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "access_token": {"type": "string"},
                                                    "token_type": {"type": "string"},
                                                    "expires_in": {"type": "integer"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    added_endpoints.append("/oauth/token")
        
        # 3. Add observability if requested
        if scaffold_config.get("observability"):
            if "/metrics" not in enhanced_spec.get("paths", {}):
                enhanced_spec["paths"]["/metrics"] = {
                    "get": {
                        "summary": "Get API metrics",
                        "description": "Returns metrics about API usage and performance",
                        "operationId": "getMetrics",
                        "tags": ["Observability"],
                        "responses": {
                            "200": {
                                "description": "API metrics",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "requests": {"type": "integer"},
                                                "errors": {"type": "integer"},
                                                "average_response_time": {"type": "number"},
                                                "uptime": {"type": "number"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                added_endpoints.append("/metrics")
            
            if "/health" not in enhanced_spec.get("paths", {}):
                enhanced_spec["paths"]["/health"] = {
                    "get": {
                        "summary": "API health check",
                        "description": "Returns health status of the API",
                        "operationId": "getHealth",
                        "tags": ["Observability"],
                        "responses": {
                            "200": {
                                "description": "Health status",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
                                                "version": {"type": "string"},
                                                "details": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                added_endpoints.append("/health")
                
        # 4. Add rate limiting if requested
        if scaffold_config.get("rate_limiting"):
            # Add rate limiting extension to the spec
            enhanced_spec["x-rate-limit"] = {
                "default": {
                    "rate": 100,
                    "per": "minute"
                },
                "premium": {
                    "rate": 1000,
                    "per": "minute"
                }
            }
            
            # Add headers to responses for rate limiting info
            for path in enhanced_spec.get("paths", {}):
                for method in enhanced_spec["paths"][path]:
                    if method in ["get", "post", "put", "delete", "patch"]:
                        # Add rate limit headers to all responses
                        for status_code in enhanced_spec["paths"][path][method].get("responses", {}):
                            if "headers" not in enhanced_spec["paths"][path][method]["responses"][status_code]:
                                enhanced_spec["paths"][path][method]["responses"][status_code]["headers"] = {}
                            
                            enhanced_spec["paths"][path][method]["responses"][status_code]["headers"]["X-Rate-Limit-Limit"] = {
                                "schema": {"type": "integer"},
                                "description": "The number of allowed requests in the current period"
                            }
                            enhanced_spec["paths"][path][method]["responses"][status_code]["headers"]["X-Rate-Limit-Remaining"] = {
                                "schema": {"type": "integer"},
                                "description": "The number of remaining requests in the current period"
                            }
                            enhanced_spec["paths"][path][method]["responses"][status_code]["headers"]["X-Rate-Limit-Reset"] = {
                                "schema": {"type": "integer"},
                                "description": "The timestamp at which the current rate limit window resets"
                            }
                
        # 5. Enhance documentation if requested
        if scaffold_config.get("documentation"):
            # Make sure info section has adequate description
            if "info" in enhanced_spec:
                if not enhanced_spec["info"].get("description") or len(enhanced_spec["info"].get("description", "")) < 50:
                    # Improve description
                    enhanced_spec["info"]["description"] = (
                        enhanced_spec["info"].get("description", "") + 
                        "\n\nThis API is agent-ready, providing standard discovery, " +
                        "authentication, and observability endpoints for seamless integration with AI systems."
                    )
                
                # Add contact information if missing
                if "contact" not in enhanced_spec["info"]:
                    enhanced_spec["info"]["contact"] = {
                        "name": "API Support",
                        "email": "api-support@example.com"
                    }
            
            # Add examples to endpoints where missing
            for path in enhanced_spec.get("paths", {}):
                for method in enhanced_spec["paths"][path]:
                    if method in ["get", "post", "put", "delete", "patch"]:
                        # Ensure all endpoints have descriptions
                        if not enhanced_spec["paths"][path][method].get("description"):
                            # Use summary as description if available
                            if enhanced_spec["paths"][path][method].get("summary"):
                                enhanced_spec["paths"][path][method]["description"] = enhanced_spec["paths"][path][method]["summary"]
                            else:
                                # Generate a generic description
                                operation = method.upper()
                                resource = path.split("/")[-1] or "resource"
                                enhanced_spec["paths"][path][method]["description"] = f"Performs a {operation} operation on the {resource} resource."
        
        # Count enhanced endpoints
        enhanced_endpoints = 0
        for path in enhanced_spec.get("paths", {}):
            enhanced_endpoints += len([m for m in enhanced_spec["paths"][path] 
                                     if m in ["get", "post", "put", "delete", "patch"]])
        
        # Generate summary
        summary = f"""
API Enhancement Summary:
- Original endpoints: {original_endpoints}
- Enhanced endpoints: {enhanced_endpoints}
- Added endpoints: {len(added_endpoints)}
- Enhancement features:
  - Agent discovery: {"Added" if scaffold_config.get("agent_discovery") else "Skipped"}
  - Authentication: {scaffold_config.get("auth_mechanism", "none").upper()}
  - Observability: {"Added" if scaffold_config.get("observability") else "Skipped"}
  - Rate limiting: {"Added" if scaffold_config.get("rate_limiting") else "Skipped"}
  - Documentation: {"Enhanced" if scaffold_config.get("documentation") else "Unchanged"}
"""
        
        enhancements = {
            "original_endpoints": original_endpoints,
            "enhanced_endpoints": enhanced_endpoints,
            "added_endpoints": added_endpoints,
            "summary": summary
        }
        
        return enhanced_spec, enhancements
    
    async def _save_enhanced_spec(self, 
                                 spec: Dict[str, Any], 
                                 original_path: str, 
                                 output_dir: str) -> str:
        """Save the enhanced API specification.
        
        Args:
            spec: Enhanced API specification
            original_path: Path to the original spec file
            output_dir: Directory to save the enhanced spec
            
        Returns:
            Path to the saved specification
        """
        # Determine output format based on original file
        output_format = "json"
        if original_path.endswith((".yaml", ".yml")):
            output_format = "yaml"
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        original_filename = os.path.basename(original_path)
        filename_parts = os.path.splitext(original_filename)
        output_filename = f"{filename_parts[0]}_agent_ready.{output_format}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save the spec
        try:
            if output_format == "json":
                with open(output_path, "w") as f:
                    json.dump(spec, f, indent=2)
            else:
                import yaml
                with open(output_path, "w") as f:
                    yaml.dump(spec, f, sort_keys=False)
            
            return output_path
        except Exception as e:
            raise IOError(f"Failed to save enhanced API specification: {str(e)}") 