"""
API Ready Workflow Provider.

This module implements a workflow for enhancing APIs with AI-ready capabilities.
"""

import json
from typing import Any, Dict, List, Optional, TypedDict, Union, cast
from datetime import datetime

from pepperpy.core.logging import get_logger
from pepperpy.core.workflow import ProviderPlugin, WorkflowProvider
from pepperpy.core.llm import create_llm_provider

logger = get_logger(__name__)


class DiscoveryEnhancement(TypedDict):
    """Discovery enhancement for AI-ready APIs."""
    
    title: str
    description: str
    ai_agent_endpoint: str
    capabilities: List[str]
    schema_url: str
    documentation_url: Optional[str]


class AuthenticationEnhancement(TypedDict):
    """Authentication enhancement for AI-ready APIs."""
    
    auth_type: str
    description: str
    setup_instructions: str
    token_endpoint: Optional[str]
    scopes: Optional[List[str]]
    example_code: Optional[str]


class ObservabilityEnhancement(TypedDict):
    """Observability enhancement for AI-ready APIs."""
    
    tracing_enabled: bool
    telemetry_endpoints: List[str]
    request_tracking: bool
    usage_metrics: bool
    audit_trail: bool
    rate_limiting_info: Dict[str, Any]


class DocumentationEnhancement(TypedDict):
    """Documentation enhancement for AI-ready APIs."""
    
    ai_targeted_docs: bool
    examples_for_agents: List[Dict[str, Any]]
    capability_definitions: List[Dict[str, str]]
    structured_responses: bool
    interactive_playground: Optional[str]


class EnhancementResult(TypedDict):
    """Result of API enhancements."""
    
    api_name: str
    api_version: str
    enhancement_date: str
    original_spec_summary: Dict[str, Any]
    enhancements: Dict[str, Any]
    implementation_steps: List[Dict[str, Any]]
    code_samples: Optional[Dict[str, Dict[str, str]]]


class APIReadyProvider(WorkflowProvider, ProviderPlugin):
    """API Ready workflow provider.
    
    This provider enhances existing APIs with AI-ready capabilities including
    discovery mechanisms, authentication for AI consumers, observability features,
    and enhanced documentation.
    """
    
    def __init__(self) -> None:
        """Initialize the API Ready provider."""
        self._initialized = False
        self._config: Dict[str, Any] = {}
        self._llm = None
    
    @property
    def initialized(self) -> bool:
        """Return whether the provider is initialized."""
        return self._initialized
    
    async def initialize(self) -> None:
        """Initialize provider resources."""
        if self._initialized:
            return
        
        try:
            # Initialize LLM if configured
            llm_config = self._config.get("llm_config", {})
            if llm_config:
                provider = llm_config.get("provider", "openai")
                model = llm_config.get("model", "gpt-4")
                self._llm = await create_llm_provider(provider, model=model)
            
            self._initialized = True
            logger.info("API Ready provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize API Ready provider: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if not self._initialized:
            return
        
        try:
            if self._llm and hasattr(self._llm, "cleanup"):
                await self._llm.cleanup()
            
            self._initialized = False
            logger.info("API Ready provider resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up API Ready provider resources: {e}")
            raise
    
    async def get_config(self) -> Dict[str, Any]:
        """Return the current configuration."""
        return self._config
    
    def has_config(self) -> bool:
        """Return whether the provider has a configuration."""
        return bool(self._config)
    
    async def update_config(self, config: Dict[str, Any]) -> None:
        """Update the configuration."""
        self._config = config
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the API Ready workflow.
        
        Args:
            input_data: Input data for the workflow with the following structure:
                - api_spec: OpenAPI specification (can be JSON or YAML)
                - api_name: Name of the API (optional)
                - api_version: Version of the API (optional)
                - enhancement_types: Types of enhancements to apply (optional)
        
        Returns:
            Enhanced API specification and implementation steps
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Extract API specification 
            api_spec = input_data.get("api_spec")
            if not api_spec:
                return {
                    "status": "error",
                    "message": "No API specification provided"
                }
            
            # Get API metadata
            api_name = input_data.get("api_name", "Unnamed API")
            api_version = input_data.get("api_version", "1.0.0")
            
            # Get enhancement types from input or config
            enhancement_types = input_data.get(
                "enhancement_types", 
                self._config.get("enhancement_types", ["all"])
            )
            
            # Apply enhancements
            enhanced_spec, implementation_steps = await self._enhance_api(
                api_spec, 
                api_name, 
                api_version, 
                enhancement_types
            )
            
            # Generate code samples if configured
            code_samples = None
            if self._config.get("add_code_samples", True):
                code_samples = await self._generate_code_samples(
                    enhanced_spec,
                    implementation_steps
                )
            
            # Prepare result
            result = EnhancementResult(
                api_name=api_name,
                api_version=api_version,
                enhancement_date=datetime.now().isoformat(),
                original_spec_summary=self._summarize_api_spec(api_spec),
                enhancements=enhanced_spec,
                implementation_steps=implementation_steps,
                code_samples=code_samples
            )
            
            # Format output
            output_format = self._config.get("output_format", "json")
            formatted_result = self._format_result(result, output_format)
            
            return {
                "status": "success",
                "result": formatted_result
            }
        except Exception as e:
            logger.error(f"Error executing API Ready workflow: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _summarize_api_spec(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the original API specification.
        
        Args:
            api_spec: OpenAPI specification
            
        Returns:
            API specification summary
        """
        paths = api_spec.get("paths", {})
        components = api_spec.get("components", {})
        
        return {
            "title": api_spec.get("info", {}).get("title", "Unknown API"),
            "version": api_spec.get("info", {}).get("version", "unknown"),
            "description": api_spec.get("info", {}).get("description", "No description"),
            "path_count": len(paths),
            "endpoint_count": sum(
                len([m for m in operations.keys() if m in ["get", "post", "put", "delete", "patch"]])
                for operations in paths.values()
            ),
            "schema_count": len(components.get("schemas", {})),
            "security_schemes": list(components.get("securitySchemes", {}).keys()),
        }
    
    async def _enhance_api(
        self, 
        api_spec: Dict[str, Any], 
        api_name: str,
        api_version: str,
        enhancement_types: List[str]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Enhance API with AI-ready capabilities.
        
        Args:
            api_spec: OpenAPI specification
            api_name: Name of the API
            api_version: Version of the API
            enhancement_types: Types of enhancements to apply
            
        Returns:
            Enhanced API specification and implementation steps
        """
        # Determine which enhancements to apply
        apply_all = "all" in enhancement_types
        apply_discovery = apply_all or "discovery" in enhancement_types
        apply_auth = apply_all or "authentication" in enhancement_types
        apply_observability = apply_all or "observability" in enhancement_types
        apply_documentation = apply_all or "documentation" in enhancement_types
        
        # Apply the enhancements
        enhancements = {}
        implementation_steps = []
        
        # Discovery enhancements
        if apply_discovery:
            discovery_enhancements, discovery_steps = await self._enhance_discovery(api_spec, api_name, api_version)
            enhancements["discovery"] = discovery_enhancements
            implementation_steps.extend(discovery_steps)
        
        # Authentication enhancements
        if apply_auth:
            auth_enhancements, auth_steps = await self._enhance_authentication(api_spec, api_name, api_version)
            enhancements["authentication"] = auth_enhancements
            implementation_steps.extend(auth_steps)
        
        # Observability enhancements
        if apply_observability:
            obs_enhancements, obs_steps = await self._enhance_observability(api_spec, api_name, api_version)
            enhancements["observability"] = obs_enhancements
            implementation_steps.extend(obs_steps)
        
        # Documentation enhancements
        if apply_documentation:
            doc_enhancements, doc_steps = await self._enhance_documentation(api_spec, api_name, api_version)
            enhancements["documentation"] = doc_enhancements
            implementation_steps.extend(doc_steps)
        
        return enhancements, implementation_steps
    
    async def _enhance_discovery(
        self, 
        api_spec: Dict[str, Any],
        api_name: str,
        api_version: str
    ) -> tuple[DiscoveryEnhancement, List[Dict[str, Any]]]:
        """Enhance API with discovery capabilities.
        
        Args:
            api_spec: OpenAPI specification
            api_name: Name of the API
            api_version: Version of the API
            
        Returns:
            Discovery enhancements and implementation steps
        """
        # Extract API paths and capabilities
        paths = api_spec.get("paths", {})
        operations = []
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                operations.append({
                    "path": path,
                    "method": method,
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "tags": operation.get("tags", []),
                })
        
        # Extract unique capabilities (tags)
        capabilities = set()
        for op in operations:
            capabilities.update(op.get("tags", []))
        
        # Create discovery endpoint
        discovery_endpoint = f"/{api_name.lower().replace(' ', '-')}/ai-discovery"
        
        # Create discovery enhancement
        discovery_enhancement = DiscoveryEnhancement(
            title=f"{api_name} AI Discovery",
            description=f"Discovery endpoint for AI agents to learn about {api_name} capabilities",
            ai_agent_endpoint=discovery_endpoint,
            capabilities=list(capabilities) if capabilities else ["general"],
            schema_url=f"/{api_name.lower().replace(' ', '-')}/swagger.json",
            documentation_url=f"/{api_name.lower().replace(' ', '-')}/docs"
        )
        
        # Create implementation steps
        implementation_steps = [
            {
                "step": "Create AI Discovery Endpoint",
                "description": f"Implement a new endpoint at {discovery_endpoint} that returns AI-friendly discovery information",
                "priority": "high",
                "implementation_notes": "The endpoint should return capability listings and metadata in a format optimized for AI agents"
            },
            {
                "step": "Update OpenAPI Specification",
                "description": "Add the discovery endpoint to the OpenAPI specification",
                "priority": "medium",
                "implementation_notes": "Include detailed descriptions and examples tailored for AI consumption"
            },
            {
                "step": "Implement Content Negotiation",
                "description": "Add support for multiple response formats (JSON, YAML, RDF)",
                "priority": "medium",
                "implementation_notes": "AI agents may request different formats based on their capabilities"
            }
        ]
        
        return discovery_enhancement, implementation_steps
    
    async def _enhance_authentication(
        self, 
        api_spec: Dict[str, Any],
        api_name: str,
        api_version: str
    ) -> tuple[AuthenticationEnhancement, List[Dict[str, Any]]]:
        """Enhance API with AI-friendly authentication.
        
        Args:
            api_spec: OpenAPI specification
            api_name: Name of the API
            api_version: Version of the API
            
        Returns:
            Authentication enhancements and implementation steps
        """
        # Check existing security schemes
        security_schemes = api_spec.get("components", {}).get("securitySchemes", {})
        has_oauth = any(s.get("type") == "oauth2" for s in security_schemes.values())
        has_api_key = any(s.get("type") == "apiKey" for s in security_schemes.values())
        
        # Determine best authentication approach
        if has_oauth:
            auth_type = "oauth2"
            token_endpoint = next(
                (s.get("flows", {}).get("clientCredentials", {}).get("tokenUrl", "")
                for s in security_schemes.values() 
                if s.get("type") == "oauth2"),
                f"/{api_name.lower().replace(' ', '-')}/token"
            )
            scopes = next(
                (list(s.get("flows", {}).get("clientCredentials", {}).get("scopes", {}).keys())
                for s in security_schemes.values() 
                if s.get("type") == "oauth2"),
                ["ai.read", "ai.write"]
            )
        elif has_api_key:
            auth_type = "apiKey"
            token_endpoint = None
            scopes = None
        else:
            # Default to OAuth2 with client credentials
            auth_type = "oauth2"
            token_endpoint = f"/{api_name.lower().replace(' ', '-')}/token"
            scopes = ["ai.read", "ai.write"]
        
        # Create auth enhancement
        auth_enhancement = AuthenticationEnhancement(
            auth_type=auth_type,
            description=f"AI-optimized {auth_type} authentication",
            setup_instructions=f"Register your AI agent to obtain credentials for {api_name}",
            token_endpoint=token_endpoint,
            scopes=scopes,
            example_code=None  # Will be populated in code samples
        )
        
        # Create implementation steps
        implementation_steps = [
            {
                "step": "AI Agent Registration Portal",
                "description": "Create a registration portal specifically for AI agents",
                "priority": "high",
                "implementation_notes": "Allow AI agents to register programmatically and obtain credentials"
            }
        ]
        
        if auth_type == "oauth2":
            implementation_steps.extend([
                {
                    "step": "Implement OAuth2 Client Credentials Flow",
                    "description": "Set up OAuth2 endpoint optimized for machine-to-machine communication",
                    "priority": "high",
                    "implementation_notes": "Use client credentials flow for AI agents, with appropriate scopes"
                },
                {
                    "step": "Add AI-specific Scopes",
                    "description": "Define scopes that represent AI-specific permissions",
                    "priority": "medium",
                    "implementation_notes": "Consider scopes like 'ai.read', 'ai.write', 'ai.analyze'"
                }
            ])
        else:
            implementation_steps.append({
                "step": "Enhance API Key Management",
                "description": "Update API key management to support AI agent identification",
                "priority": "high",
                "implementation_notes": "Add metadata to API keys to identify AI vs human consumers"
            })
        
        # Add rate limiting
        implementation_steps.append({
            "step": "Implement AI-specific Rate Limiting",
            "description": "Set up separate rate limits for AI consumers",
            "priority": "medium",
            "implementation_notes": "Configure different rate limits based on agent type and credentials"
        })
        
        return auth_enhancement, implementation_steps
    
    async def _enhance_observability(
        self, 
        api_spec: Dict[str, Any],
        api_name: str,
        api_version: str
    ) -> tuple[ObservabilityEnhancement, List[Dict[str, Any]]]:
        """Enhance API with observability features.
        
        Args:
            api_spec: OpenAPI specification
            api_name: Name of the API
            api_version: Version of the API
            
        Returns:
            Observability enhancements and implementation steps
        """
        # Create observability enhancement
        obs_enhancement = ObservabilityEnhancement(
            tracing_enabled=True,
            telemetry_endpoints=[
                f"/{api_name.lower().replace(' ', '-')}/metrics",
                f"/{api_name.lower().replace(' ', '-')}/health"
            ],
            request_tracking=True,
            usage_metrics=True,
            audit_trail=True,
            rate_limiting_info={
                "default_limit": "100 requests per minute",
                "burst_limit": "150 requests per minute",
                "quota_endpoint": f"/{api_name.lower().replace(' ', '-')}/quota",
                "headers": [
                    "X-RateLimit-Limit",
                    "X-RateLimit-Remaining",
                    "X-RateLimit-Reset"
                ]
            }
        )
        
        # Create implementation steps
        implementation_steps = [
            {
                "step": "Add Request Tracing",
                "description": "Implement request tracing for AI agent calls",
                "priority": "high",
                "implementation_notes": "Use correlation IDs to track AI agent activities across endpoints"
            },
            {
                "step": "Implement Telemetry Endpoints",
                "description": "Add metrics and health endpoints for AI monitoring",
                "priority": "medium",
                "implementation_notes": "Provide performance data that's useful for AI agents to optimize their calls"
            },
            {
                "step": "Add Usage Tracking",
                "description": "Create a system to track and report AI agent usage",
                "priority": "medium",
                "implementation_notes": "Track usage patterns to identify optimization opportunities"
            },
            {
                "step": "Set Up Quota Management",
                "description": "Implement quota tracking and reporting for AI consumers",
                "priority": "medium",
                "implementation_notes": "Allow AI agents to check their remaining quota programmatically"
            },
            {
                "step": "Add Rate Limiting Headers",
                "description": "Implement rate limiting headers in all responses",
                "priority": "high",
                "implementation_notes": "Include headers that inform AI agents about rate limits and remaining quota"
            }
        ]
        
        return obs_enhancement, implementation_steps
    
    async def _enhance_documentation(
        self, 
        api_spec: Dict[str, Any],
        api_name: str,
        api_version: str
    ) -> tuple[DocumentationEnhancement, List[Dict[str, Any]]]:
        """Enhance API with AI-targeted documentation.
        
        Args:
            api_spec: OpenAPI specification
            api_name: Name of the API
            api_version: Version of the API
            
        Returns:
            Documentation enhancements and implementation steps
        """
        # Extract paths and operations
        paths = api_spec.get("paths", {})
        endpoints = []
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", "")
                })
        
        # Create example endpoints for agents
        examples = []
        for i, endpoint in enumerate(endpoints[:3]):  # Use first 3 endpoints for examples
            examples.append({
                "title": f"Example {i+1}: {endpoint['summary'] or endpoint['path']}",
                "description": endpoint['description'] or f"Using the {endpoint['path']} endpoint",
                "path": endpoint['path'],
                "method": endpoint['method'],
                "request": {"sample": "request"},
                "response": {"sample": "response"}
            })
        
        # Create capability definitions
        capabilities = [
            {"name": "Data Retrieval", "description": "Access and retrieve data from the API"},
            {"name": "Data Modification", "description": "Create, update, or delete resources"},
            {"name": "Analysis", "description": "Analyze data or execute business logic"}
        ]
        
        # Create documentation enhancement
        doc_enhancement = DocumentationEnhancement(
            ai_targeted_docs=True,
            examples_for_agents=examples,
            capability_definitions=capabilities,
            structured_responses=True,
            interactive_playground=f"/{api_name.lower().replace(' ', '-')}/playground"
        )
        
        # Create implementation steps
        implementation_steps = [
            {
                "step": "Create AI-targeted Documentation",
                "description": "Develop documentation specifically for AI agents",
                "priority": "high",
                "implementation_notes": "Use structured formats that can be consumed programmatically"
            },
            {
                "step": "Add Comprehensive Examples",
                "description": "Create detailed examples for each API capability",
                "priority": "medium",
                "implementation_notes": "Include request/response examples in multiple formats"
            },
            {
                "step": "Implement Interactive Playground",
                "description": "Create an interactive playground for testing API calls",
                "priority": "medium",
                "implementation_notes": "Allow AI agents to experiment with the API in a sandbox environment"
            },
            {
                "step": "Enhance OpenAPI Specification",
                "description": "Add AI-friendly annotations to the OpenAPI spec",
                "priority": "high",
                "implementation_notes": "Include machine-readable metadata for capabilities and constraints"
            }
        ]
        
        return doc_enhancement, implementation_steps
    
    async def _generate_code_samples(
        self,
        enhanced_spec: Dict[str, Any],
        implementation_steps: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, str]]:
        """Generate code samples for implementing the enhancements.
        
        Args:
            enhanced_spec: Enhanced API specification
            implementation_steps: Implementation steps
            
        Returns:
            Code samples by language and feature
        """
        target_languages = self._config.get("target_languages", ["python", "javascript"])
        
        # Initialize result structure
        code_samples = {lang: {} for lang in target_languages}
        
        # Discovery endpoint samples
        if "discovery" in enhanced_spec:
            discovery = enhanced_spec["discovery"]
            endpoint = discovery.get("ai_agent_endpoint", "/ai-discovery")
            
            # Python sample
            if "python" in target_languages:
                code_samples["python"]["discovery_endpoint"] = f"""from fastapi import FastAPI, Request

app = FastAPI()

@app.get("{endpoint}")
async def ai_discovery():
    \"\"\"AI Discovery endpoint for agent capability advertisement.\"\"\"
    return {{
        "title": "{discovery.get('title', 'API Discovery')}",
        "description": "{discovery.get('description', 'API capability discovery for AI agents')}",
        "capabilities": {discovery.get('capabilities', ['general'])},
        "schema_url": "{discovery.get('schema_url', '/swagger.json')}",
        "documentation_url": "{discovery.get('documentation_url', '/docs')}"
    }}
"""
            
            # JavaScript sample
            if "javascript" in target_languages:
                code_samples["javascript"]["discovery_endpoint"] = f"""const express = require('express');
const app = express();

// AI Discovery endpoint
app.get('{endpoint}', (req, res) => {{
  res.json({{
    title: '{discovery.get('title', 'API Discovery')}',
    description: '{discovery.get('description', 'API capability discovery for AI agents')}',
    capabilities: {json.dumps(discovery.get('capabilities', ['general']))},
    schema_url: '{discovery.get('schema_url', '/swagger.json')}',
    documentation_url: '{discovery.get('documentation_url', '/docs')}'
  }});
}});
"""
        
        # Authentication samples
        if "authentication" in enhanced_spec:
            auth = enhanced_spec["authentication"]
            auth_type = auth.get("auth_type", "oauth2")
            
            if auth_type == "oauth2" and "python" in target_languages:
                code_samples["python"]["oauth2_implementation"] = """from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel

# Secret key and algorithm
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Token model
class Token(BaseModel):
    access_token: str
    token_type: str

app = FastAPI()

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Authenticate client (AI agent)
    client = authenticate_client(form_data.username, form_data.password)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect client credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": client["id"], "scopes": form_data.scopes},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Helper functions would be defined here
"""
            
            if auth_type == "apiKey" and "python" in target_languages:
                code_samples["python"]["api_key_implementation"] = """from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader, APIKey

app = FastAPI()

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header not found"
        )
    
    # Verify API key (implementation would check against database)
    if not is_valid_api_key(api_key_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    # Return client info for the API key
    return get_client_for_api_key(api_key_header)

@app.get("/protected-resource")
async def protected_endpoint(client: dict = Depends(get_api_key)):
    return {"message": f"Hello, {client['name']}!", "data": "This is protected data"}

# Helper functions would be defined here
"""
        
        # Observability samples
        if "observability" in enhanced_spec:
            obs = enhanced_spec["observability"]
            
            if "python" in target_languages:
                code_samples["python"]["observability_implementation"] = """from fastapi import FastAPI, Request, Response
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI()

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'client_type'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])
AI_REQUEST_COUNT = Counter('ai_requests_total', 'Total AI Agent Requests', ['agent_id', 'capability'])

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # Start timer
    start_time = time.time()
    
    # Get path
    path = request.url.path
    
    # Process request
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    REQUEST_LATENCY.labels(method=request.method, endpoint=path).observe(duration)
    
    # Determine if request is from AI agent
    client_type = "ai" if "X-AI-Agent" in request.headers else "human"
    REQUEST_COUNT.labels(method=request.method, endpoint=path, client_type=client_type).inc()
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = "99"  # Would be dynamic in real implementation
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/quota")
async def quota(request: Request):
    # Would retrieve actual quota from database based on client identity
    return {
        "limit": 100,
        "remaining": 99,
        "reset": int(time.time()) + 60
    }
"""
        
        return code_samples
    
    def _format_result(self, result: EnhancementResult, output_format: str) -> Any:
        """Format the result in the specified output format.
        
        Args:
            result: Enhancement result
            output_format: Output format (json, yaml, markdown, code)
            
        Returns:
            Formatted result
        """
        if output_format == "json":
            return result
        elif output_format == "yaml":
            # In a real implementation, this would convert to YAML
            # For now, just return with a note
            return {
                "format": "yaml",
                "note": "Would be converted to YAML format",
                "data": result
            }
        elif output_format == "markdown":
            # In a real implementation, this would convert to Markdown
            # For now, just return with a note
            return {
                "format": "markdown",
                "note": "Would be converted to Markdown format",
                "data": result
            }
        elif output_format == "code":
            # In a real implementation, this would return only the code samples
            # For now, just return the code_samples part
            return {
                "format": "code",
                "note": "Would return only code samples in requested languages",
                "data": result.get("code_samples", {})
            }
        else:
            # Default to JSON
            return result 