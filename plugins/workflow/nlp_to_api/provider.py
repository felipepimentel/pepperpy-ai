"""
NLP-to-API Workflow Provider.

This module implements a workflow for translating natural language queries into
structured API calls, with options for execution and response handling.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple, TypedDict, cast
import aiohttp
import yaml

from pepperpy.core.logging import get_logger
from pepperpy.plugin import ProviderPlugin
from pepperpy.workflow import WorkflowProvider
from pepperpy.llm import create_provider as create_llm_provider

logger = get_logger(__name__)


class APIInfo(TypedDict):
    """Information about an API."""
    
    name: str
    description: str
    spec_path: str
    base_url: str
    auth_type: Optional[str]
    auth_location: Optional[str]


class IntentAnalysis(TypedDict):
    """Analysis of user intent for API query."""
    
    api_name: str
    operation_type: str
    parameters: Dict[str, Any]
    required_auth: bool
    constraints: Optional[List[str]]


class APICallTemplate(TypedDict):
    """Template for an API call."""
    
    http_method: str
    endpoint: str
    path_params: Dict[str, Any]
    query_params: Dict[str, Any]
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]]


class APIQueryResult(TypedDict):
    """Result of an API query."""
    
    query: str
    intent: IntentAnalysis
    call_template: APICallTemplate
    formatted_call: str
    response: Optional[Dict[str, Any]]
    execution_status: str
    execution_time: Optional[float]


class NLPToAPIProvider(WorkflowProvider, ProviderPlugin):
    """NLP-to-API workflow provider.
    
    This provider translates natural language queries into structured API 
    calls, with options to execute them and return the results.
    """
    
    def __init__(self) -> None:
        """Initialize the NLP-to-API provider."""
        self._initialized = False
        self._config: Dict[str, Any] = {}
        self._llm = None
        self._api_specs: Dict[str, APIInfo] = {}
        self._http_client = None
    
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
            
            # Load API specifications
            await self._load_api_specs()
            
            # Initialize HTTP client
            self._http_client = aiohttp.ClientSession()
            
            self._initialized = True
            logger.info("NLP-to-API provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize NLP-to-API provider: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if not self._initialized:
            return
        
        try:
            if self._llm and hasattr(self._llm, "cleanup"):
                await self._llm.cleanup()
            
            if self._http_client:
                await self._http_client.close()
                self._http_client = None
            
            self._initialized = False
            logger.info("NLP-to-API provider resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up NLP-to-API provider resources: {e}")
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
        """Execute the NLP-to-API workflow.
        
        Args:
            input_data: Input data for the workflow with the following structure:
                - query: Natural language query (required)
                - api_context: Specific API to query (optional)
                - auth_credentials: Authentication credentials (optional)
                - execute: Whether to execute the API call (optional)
        
        Returns:
            Results of the workflow execution, including the generated API call
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get the natural language query
            query = input_data.get("query")
            if not query:
                return {
                    "status": "error",
                    "message": "No query provided"
                }
            
            # Get API context if specified
            api_context = input_data.get("api_context")
            
            # Get authentication credentials
            auth_credentials = input_data.get("auth_credentials", {})
            
            # Determine whether to execute the API call
            execute = input_data.get("execute", self._config.get("execute_queries", False))
            
            # Process the query and generate API call
            intent_analysis = await self._analyze_intent(query, api_context)
            
            # Generate API call template
            api_call = await self._generate_api_call(intent_analysis, api_context)
            
            # Format the API call
            output_format = input_data.get("output_format", self._config.get("output_format", "python"))
            formatted_call = self._format_api_call(api_call, output_format)
            
            # Execute the API call if requested
            response = None
            execution_status = "not_executed"
            execution_time = None
            
            if execute:
                response, execution_status, execution_time = await self._execute_api_call(
                    api_call, 
                    intent_analysis["api_name"],
                    auth_credentials
                )
            
            # Prepare result
            result = APIQueryResult(
                query=query,
                intent=intent_analysis,
                call_template=api_call,
                formatted_call=formatted_call,
                response=response,
                execution_status=execution_status,
                execution_time=execution_time
            )
            
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing NLP-to-API workflow: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _load_api_specs(self) -> None:
        """Load API specifications from configured location."""
        # Get API spec location
        spec_location = self._config.get("api_spec_location", "./api_specs")
        
        # Get supported APIs list (if empty, load all APIs found)
        supported_apis = self._config.get("supported_apis", [])
        
        logger.info(f"Loading API specs from {spec_location}")
        
        # Check if spec location is a directory
        if os.path.isdir(spec_location):
            for filename in os.listdir(spec_location):
                if filename.endswith((".json", ".yaml", ".yml")):
                    file_path = os.path.join(spec_location, filename)
                    
                    try:
                        # Load API spec
                        with open(file_path, "r") as file:
                            if filename.endswith(".json"):
                                spec = json.load(file)
                            else:
                                spec = yaml.safe_load(file)
                        
                        # Extract API info
                        api_name = spec.get("info", {}).get("title", filename.split(".")[0])
                        
                        # Skip if not in supported APIs (if list is not empty)
                        if supported_apis and api_name not in supported_apis:
                            continue
                        
                        # Add to API specs
                        self._api_specs[api_name] = APIInfo(
                            name=api_name,
                            description=spec.get("info", {}).get("description", ""),
                            spec_path=file_path,
                            base_url=self._extract_base_url(spec),
                            auth_type=self._extract_auth_type(spec),
                            auth_location=self._extract_auth_location(spec)
                        )
                        
                        logger.info(f"Loaded API spec: {api_name}")
                    except Exception as e:
                        logger.error(f"Error loading API spec {file_path}: {e}")
            
            logger.info(f"Loaded {len(self._api_specs)} API specifications")
        else:
            # TODO: Handle single file or URL scenarios
            logger.warning(f"API spec location is not a directory: {spec_location}")
    
    def _extract_base_url(self, spec: Dict[str, Any]) -> str:
        """Extract base URL from API specification.
        
        Args:
            spec: API specification
            
        Returns:
            Base URL for the API
        """
        # Try to get from servers
        servers = spec.get("servers", [])
        if servers and "url" in servers[0]:
            return servers[0]["url"]
        
        # Fallback to constructed URL
        scheme = "https"
        host = spec.get("host", "api.example.com")
        base_path = spec.get("basePath", "")
        
        return f"{scheme}://{host}{base_path}"
    
    def _extract_auth_type(self, spec: Dict[str, Any]) -> Optional[str]:
        """Extract authentication type from API specification.
        
        Args:
            spec: API specification
            
        Returns:
            Authentication type or None
        """
        # Check security schemes in OpenAPI 3.0
        security_schemes = spec.get("components", {}).get("securitySchemes", {})
        if security_schemes:
            # Return the first auth type found
            for scheme_name, scheme in security_schemes.items():
                return scheme.get("type")
        
        # Check securityDefinitions in Swagger 2.0
        security_defs = spec.get("securityDefinitions", {})
        if security_defs:
            # Return the first auth type found
            for def_name, def_info in security_defs.items():
                return def_info.get("type")
        
        return None
    
    def _extract_auth_location(self, spec: Dict[str, Any]) -> Optional[str]:
        """Extract authentication location from API specification.
        
        Args:
            spec: API specification
            
        Returns:
            Authentication location or None
        """
        # Check security schemes in OpenAPI 3.0
        security_schemes = spec.get("components", {}).get("securitySchemes", {})
        if security_schemes:
            for scheme_name, scheme in security_schemes.items():
                if scheme.get("type") == "apiKey":
                    return scheme.get("in")
                elif scheme.get("type") == "http":
                    return "header"
                elif scheme.get("type") == "oauth2":
                    return "header"
        
        # Check securityDefinitions in Swagger 2.0
        security_defs = spec.get("securityDefinitions", {})
        if security_defs:
            for def_name, def_info in security_defs.items():
                if def_info.get("type") == "apiKey":
                    return def_info.get("in")
                elif def_info.get("type") == "oauth2":
                    return "header"
        
        return None
    
    async def _analyze_intent(self, query: str, api_context: Optional[str] = None) -> IntentAnalysis:
        """Analyze natural language query to determine intent.
        
        Args:
            query: Natural language query
            api_context: Specific API to query (optional)
            
        Returns:
            Intent analysis
        """
        # TODO: Implement real intent analysis with LLM
        # For now, return a simple mock implementation
        
        # Determine API name from context or extract from query
        api_name = api_context
        if not api_name:
            # Simple heuristic to extract API name
            for name in self._api_specs:
                if name.lower() in query.lower():
                    api_name = name
                    break
            
            # Fallback to first API if none found
            if not api_name and self._api_specs:
                api_name = next(iter(self._api_specs))
        
        # Simple heuristic to determine operation type
        operation_type = "get"
        if any(term in query.lower() for term in ["add", "create", "post", "insert"]):
            operation_type = "post"
        elif any(term in query.lower() for term in ["update", "modify", "change", "put"]):
            operation_type = "put"
        elif any(term in query.lower() for term in ["delete", "remove"]):
            operation_type = "delete"
        
        # Extract parameters (very simplified)
        parameters = {}
        
        # Look for key-value patterns
        param_pattern = r'(\w+)[:\s]+["\'"]?([^"\'",]+)["\'"]?'
        for match in re.finditer(param_pattern, query):
            key, value = match.groups()
            parameters[key] = value
        
        # Determine if authentication is required
        required_auth = True  # Assume auth is required by default
        
        return IntentAnalysis(
            api_name=api_name or "unknown",
            operation_type=operation_type,
            parameters=parameters,
            required_auth=required_auth,
            constraints=None
        )
    
    async def _generate_api_call(
        self, 
        intent: IntentAnalysis,
        api_context: Optional[str] = None
    ) -> APICallTemplate:
        """Generate API call template from intent analysis.
        
        Args:
            intent: Intent analysis
            api_context: Specific API to query (optional)
            
        Returns:
            API call template
        """
        # TODO: Implement real API call generation based on OpenAPI spec
        # For now, return a simple mock implementation
        
        api_name = api_context or intent["api_name"]
        api_info = self._api_specs.get(api_name)
        
        if not api_info:
            # Fallback to a default structure
            return APICallTemplate(
                http_method=intent["operation_type"].upper(),
                endpoint=f"/api/{intent['operation_type']}",
                path_params={},
                query_params=intent["parameters"],
                headers={"Content-Type": "application/json"},
                body=None if intent["operation_type"] in ["get", "delete"] else intent["parameters"]
            )
        
        # Use API info to construct a more realistic template
        base_endpoint = "/api/v1"
        resource = api_name.lower()
        
        # Construct endpoint based on operation type
        if intent["operation_type"] in ["get", "put", "delete"] and "id" in intent["parameters"]:
            endpoint = f"{base_endpoint}/{resource}/{intent['parameters']['id']}"
            path_params = {"id": intent["parameters"]["id"]}
            # Remove id from parameters as it's in the path
            parameters = {k: v for k, v in intent["parameters"].items() if k != "id"}
        else:
            endpoint = f"{base_endpoint}/{resource}"
            path_params = {}
            parameters = intent["parameters"]
        
        # Determine query params and body based on operation type
        query_params = {}
        body = None
        
        if intent["operation_type"] == "get":
            query_params = parameters
        else:
            body = parameters
        
        # Build headers
        headers = {"Content-Type": "application/json"}
        if api_info["auth_type"] == "apiKey" and api_info["auth_location"] == "header":
            headers["Authorization"] = "API_KEY_PLACEHOLDER"
        
        return APICallTemplate(
            http_method=intent["operation_type"].upper(),
            endpoint=endpoint,
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            body=body
        )
    
    def _format_api_call(self, api_call: APICallTemplate, output_format: str) -> str:
        """Format API call template in the specified format.
        
        Args:
            api_call: API call template
            output_format: Output format (curl, python, javascript, raw)
            
        Returns:
            Formatted API call
        """
        if output_format == "curl":
            return self._format_as_curl(api_call)
        elif output_format == "python":
            return self._format_as_python(api_call)
        elif output_format == "javascript":
            return self._format_as_javascript(api_call)
        else:
            # Raw format (JSON)
            return json.dumps(api_call, indent=2)
    
    def _format_as_curl(self, api_call: APICallTemplate) -> str:
        """Format API call as curl command.
        
        Args:
            api_call: API call template
            
        Returns:
            curl command
        """
        method = api_call["http_method"]
        url = api_call["endpoint"]
        
        # Add query parameters
        if api_call["query_params"]:
            query_string = "&".join(f"{k}={v}" for k, v in api_call["query_params"].items())
            url = f"{url}?{query_string}"
        
        # Start building curl command
        curl_parts = [f"curl -X {method} '{url}'"]
        
        # Add headers
        for header, value in api_call["headers"].items():
            curl_parts.append(f"-H '{header}: {value}'")
        
        # Add body if present
        if api_call["body"]:
            body_json = json.dumps(api_call["body"])
            curl_parts.append(f"-d '{body_json}'")
        
        return " \\\n  ".join(curl_parts)
    
    def _format_as_python(self, api_call: APICallTemplate) -> str:
        """Format API call as Python code using requests.
        
        Args:
            api_call: API call template
            
        Returns:
            Python code
        """
        method = api_call["http_method"].lower()
        url = api_call["endpoint"]
        
        python_code = [
            "import requests",
            "",
            f"url = '{url}'",
            f"headers = {json.dumps(api_call['headers'], indent=4)}"
        ]
        
        if api_call["query_params"]:
            python_code.append(f"params = {json.dumps(api_call['query_params'], indent=4)}")
        
        if api_call["body"]:
            python_code.append(f"data = {json.dumps(api_call['body'], indent=4)}")
        
        # Build the request line
        request_args = ["url"]
        if api_call["headers"]:
            request_args.append("headers=headers")
        if api_call["query_params"]:
            request_args.append("params=params")
        if api_call["body"]:
            request_args.append("json=data")
        
        python_code.append(f"response = requests.{method}({', '.join(request_args)})")
        python_code.append("")
        python_code.append("# Process the response")
        python_code.append("print(response.status_code)")
        python_code.append("print(response.json())")
        
        return "\n".join(python_code)
    
    def _format_as_javascript(self, api_call: APICallTemplate) -> str:
        """Format API call as JavaScript code using fetch.
        
        Args:
            api_call: API call template
            
        Returns:
            JavaScript code
        """
        method = api_call["http_method"]
        url = api_call["endpoint"]
        
        # Add query parameters
        if api_call["query_params"]:
            query_string = "&".join(f"{k}={v}" for k, v in api_call["query_params"].items())
            url = f"{url}?{query_string}"
        
        js_code = [
            "// Using fetch API",
            f"const url = '{url}';",
            f"const headers = {json.dumps(api_call['headers'], indent=4)};"
        ]
        
        fetch_options = [f"  method: '{method}'", "  headers: headers"]
        
        if api_call["body"]:
            js_code.append(f"const data = {json.dumps(api_call['body'], indent=4)};")
            fetch_options.append("  body: JSON.stringify(data)")
        
        js_code.append("const options = {")
        js_code.append(",\n".join(fetch_options))
        js_code.append("};")
        js_code.append("")
        js_code.append("fetch(url, options)")
        js_code.append("  .then(response => response.json())")
        js_code.append("  .then(data => console.log(data))")
        js_code.append("  .catch(error => console.error('Error:', error));")
        
        return "\n".join(js_code)
    
    async def _execute_api_call(
        self, 
        api_call: APICallTemplate,
        api_name: str,
        auth_credentials: Dict[str, str]
    ) -> Tuple[Optional[Dict[str, Any]], str, Optional[float]]:
        """Execute the API call and return the response.
        
        Args:
            api_call: API call template
            api_name: Name of the API
            auth_credentials: Authentication credentials
            
        Returns:
            Response data, execution status, and execution time
        """
        # Currently not implemented - would make actual HTTP requests
        # This would handle authentication, transform the template into a real request,
        # execute it, and return the results
        
        return {
            "message": "API call execution simulation",
            "status": "success",
            "data": {
                "id": "sample-id",
                "timestamp": "2023-07-12T15:30:45Z",
                "result": "This is a simulated API response"
            }
        }, "simulated", 0.1 