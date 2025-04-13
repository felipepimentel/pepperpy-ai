"""
Utility module for generating client code for the mock API server.

This module provides functions to generate client code in various languages
based on the OpenAPI specification.
"""

import os
import re
from typing import Dict, Any, List, Optional, Union, Tuple

def _sanitize_name(name: str) -> str:
    """Sanitize a name to be used as a method name."""
    # Replace special characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'op_' + sanitized
    return sanitized

def _convert_to_camel_case(snake_str: str) -> str:
    """Convert a string from snake_case to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def _extract_base_url(spec: Dict[str, Any]) -> str:
    """Extract the base URL from the OpenAPI specification."""
    # Try to get from servers list
    if 'servers' in spec and spec['servers']:
        return spec['servers'][0]['url']
    
    # Default fallback
    return 'http://localhost:8000'

def _extract_endpoints(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract endpoints from the OpenAPI specification."""
    endpoints = []
    
    if 'paths' not in spec:
        return endpoints
    
    for path, path_item in spec['paths'].items():
        for method, operation in path_item.items():
            if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                endpoints.append({
                    'path': path,
                    'method': method.lower(),
                    'operation_id': operation.get('operationId', f"{method.lower()}_{_sanitize_name(path)}"),
                    'summary': operation.get('summary', ''),
                    'description': operation.get('description', ''),
                    'parameters': operation.get('parameters', []),
                    'request_body': operation.get('requestBody', {}),
                    'responses': operation.get('responses', {})
                })
    
    return endpoints

def _openapi_to_python_type(schema: Dict[str, Any]) -> str:
    """Convert OpenAPI type to Python type."""
    if not schema or 'type' not in schema:
        return 'Any'
    
    type_map = {
        'string': 'str',
        'integer': 'int',
        'number': 'float',
        'boolean': 'bool',
        'array': 'List',
        'object': 'Dict[str, Any]'
    }
    
    if schema['type'] == 'array' and 'items' in schema:
        items_type = _openapi_to_python_type(schema['items'])
        return f"List[{items_type}]"
    
    return type_map.get(schema['type'], 'Any')

def _openapi_to_js_type(schema: Dict[str, Any]) -> str:
    """Convert OpenAPI type to JavaScript type."""
    if not schema or 'type' not in schema:
        return 'any'
    
    type_map = {
        'string': 'string',
        'integer': 'number',
        'number': 'number',
        'boolean': 'boolean',
        'array': 'Array',
        'object': 'object'
    }
    
    if schema['type'] == 'array' and 'items' in schema:
        items_type = _openapi_to_js_type(schema['items'])
        return f"Array<{items_type}>"
    
    return type_map.get(schema['type'], 'any')

def _generate_python_client(spec: Dict[str, Any]) -> str:
    """Generate Python client code for the API."""
    base_url = _extract_base_url(spec)
    endpoints = _extract_endpoints(spec)
    api_title = spec.get('info', {}).get('title', 'API').replace(' ', '')
    
    code = f"""# Generated Python client for {api_title}
# This file was automatically generated, do not edit manually.

import requests
from typing import Dict, List, Any, Optional, Union

class {api_title}Client:
    \"\"\"Client for interacting with the {api_title} API.\"\"\"
    
    def __init__(self, base_url: str = "{base_url}", headers: Optional[Dict[str, str]] = None):
        \"\"\"Initialize the API client.
        
        Args:
            base_url: Base URL of the API
            headers: Optional headers to include in all requests
        \"\"\"
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {{}}
        
    def _make_request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        \"\"\"Make a request to the API.
        
        Args:
            method: HTTP method
            path: Path to request
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            JSON response from the API
        \"\"\"
        url = f"{{self.base_url}}{{path}}"
        
        # Merge default headers with request-specific headers
        headers = {{**self.headers}}
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        
        try:
            return response.json()
        except:
            return {{"status": "success"}}

"""
    
    # Generate methods for each endpoint
    for endpoint in endpoints:
        method_name = _sanitize_name(endpoint['operation_id'])
        path = endpoint['path']
        http_method = endpoint['method']
        description = endpoint['description'] or endpoint['summary'] or f"{http_method.upper()} {path}"
        
        # Collect parameters
        path_params = []
        query_params = []
        header_params = []
        for param in endpoint['parameters']:
            param_name = param['name']
            param_in = param.get('in', '')
            required = param.get('required', False)
            param_schema = param.get('schema', {})
            param_type = _openapi_to_python_type(param_schema)
            
            if param_in == 'path':
                path_params.append((param_name, param_type, required))
            elif param_in == 'query':
                query_params.append((param_name, param_type, required))
            elif param_in == 'header':
                header_params.append((param_name, param_type, required))
        
        # Check for request body
        has_body = False
        body_content_type = None
        if endpoint['request_body'] and 'content' in endpoint['request_body']:
            has_body = True
            body_content_type = next(iter(endpoint['request_body']['content']))
        
        # Build method signature
        signature_parts = []
        
        # Add path parameters
        for name, type_hint, required in path_params:
            if required:
                signature_parts.append(f"{name}: {type_hint}")
            else:
                signature_parts.append(f"{name}: Optional[{type_hint}] = None")
        
        # Add request body if needed
        if has_body:
            signature_parts.append("data: Dict[str, Any]")
        
        # Add query parameters
        for name, type_hint, required in query_params:
            if required:
                signature_parts.append(f"{name}: {type_hint}")
            else:
                signature_parts.append(f"{name}: Optional[{type_hint}] = None")
        
        # Add header parameters
        for name, type_hint, required in header_params:
            if required:
                signature_parts.append(f"{name}_header: {type_hint}")
            else:
                signature_parts.append(f"{name}_header: Optional[{type_hint}] = None")
        
        # Generate method
        code += f"""
    def {method_name}(self, {', '.join(signature_parts)}) -> Dict[str, Any]:
        \"\"\"
        {description}
        
        Args:
        {chr(10).join([f'    {name}: {desc}' for name, _, _, desc in [(param, _, req, f"{'Required p' if req else 'P'}arameter for {in_type}") for param, _, req, in_type in [(p[0], p[1], p[2], 'path') for p in path_params] + [(p[0], p[1], p[2], 'query') for p in query_params] + [(f"{p[0]}_header", p[1], p[2], 'header') for p in header_params]]])}
        {f'    data: Request body' if has_body else ''}
        
        Returns:
            API response
        \"\"\"
        # Build the URL with path parameters
        path = f"{path}"
        {chr(10).join([f'        path = path.replace("{{{name}}}", str({name}))' for name, _, _ in path_params])}
        
        # Prepare query parameters
        params = {{}}
        {chr(10).join([f'        if {name} is not None:\n            params["{name}"] = {name}' for name, _, _ in query_params])}
        
        # Prepare headers
        headers = {{}}
        {chr(10).join([f'        if {name}_header is not None:\n            headers["{name}"] = {name}_header' for name, _, _ in header_params])}
        
        # Make the request
        return self._make_request(
            method="{http_method}",
            path=path,
            {f'json=data,' if has_body and body_content_type == 'application/json' else ''}
            {f'data=data,' if has_body and body_content_type != 'application/json' else ''}
            params=params,
            headers=headers
        )
"""
    
    return code

def _generate_javascript_client(spec: Dict[str, Any]) -> str:
    """Generate JavaScript client code for the API."""
    base_url = _extract_base_url(spec)
    endpoints = _extract_endpoints(spec)
    api_title = spec.get('info', {}).get('title', 'API').replace(' ', '')
    
    code = f"""// Generated JavaScript client for {api_title}
// This file was automatically generated, do not edit manually.

class {api_title}Client {{
  /**
   * Client for interacting with the {api_title} API.
   * @param {{string}} baseUrl - Base URL of the API
   * @param {{Object}} headers - Optional headers to include in all requests
   */
  constructor(baseUrl = "{base_url}", headers = {{}}) {{
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    this.headers = headers;
  }}

  /**
   * Make a request to the API.
   * @param {{string}} method - HTTP method
   * @param {{string}} path - Path to request
   * @param {{Object}} options - Request options
   * @returns {{Promise<Object>}} - JSON response from the API
   * @private
   */
  async _makeRequest(method, path, options = {{}}) {{
    const url = `${{this.baseUrl}}${{path}}`;
    
    // Merge default headers with request-specific headers
    const headers = {{
      'Content-Type': 'application/json',
      ...this.headers,
      ...(options.headers || {{}})
    }};
    
    const fetchOptions = {{
      method,
      headers,
      ...options
    }};
    
    // Remove undefined values from query params
    if (options.params) {{
      const searchParams = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {{
        if (value !== undefined) {{
          searchParams.append(key, value);
        }}
      }});
      
      const queryString = searchParams.toString();
      if (queryString) {{
        url += `?${{queryString}}`;
      }}
    }}
    
    const response = await fetch(url, fetchOptions);
    
    if (!response.ok) {{
      throw new Error(`API request failed: ${{response.status}} ${{response.statusText}}`);
    }}
    
    try {{
      return await response.json();
    }} catch (e) {{
      return {{ status: 'success' }};
    }}
  }}

"""
    
    # Generate methods for each endpoint
    for endpoint in endpoints:
        method_name = _convert_to_camel_case(_sanitize_name(endpoint['operation_id']))
        path = endpoint['path']
        http_method = endpoint['method']
        description = endpoint['description'] or endpoint['summary'] or f"{http_method.toUpperCase()} {path}"
        
        # Collect parameters
        path_params = []
        query_params = []
        header_params = []
        for param in endpoint['parameters']:
            param_name = param['name']
            param_in = param.get('in', '')
            required = param.get('required', False)
            param_schema = param.get('schema', {})
            param_type = _openapi_to_js_type(param_schema)
            
            if param_in == 'path':
                path_params.append((param_name, param_type, required))
            elif param_in == 'query':
                query_params.append((param_name, param_type, required))
            elif param_in == 'header':
                header_params.append((param_name, param_type, required))
        
        # Check for request body
        has_body = False
        body_content_type = None
        if endpoint['request_body'] and 'content' in endpoint['request_body']:
            has_body = True
            body_content_type = next(iter(endpoint['request_body']['content']))
        
        # Build JSDoc for method parameters
        jsdoc_params = []
        
        # Add path parameters
        for name, type_hint, required in path_params:
            jsdoc_params.append(f" * @param {{{type_hint}}} {name} - {'Required p' if required else 'P'}arameter for path")
        
        # Add request body if needed
        if has_body:
            jsdoc_params.append(f" * @param {{Object}} data - Request body")
        
        # Add query parameters
        for name, type_hint, required in query_params:
            jsdoc_params.append(f" * @param {{{type_hint}}} {name} - {'Required p' if required else 'P'}arameter for query")
        
        # Add header parameters
        for name, type_hint, required in header_params:
            jsdoc_params.append(f" * @param {{{type_hint}}} {name}Header - {'Required p' if required else 'P'}arameter for header")
        
        # Build parameter list
        param_names = []
        default_params = []
        
        # Add path parameters
        for name, _, required in path_params:
            param_names.append(name)
            if not required:
                default_params.append(f"{name} = undefined")
        
        # Add request body if needed
        if has_body:
            param_names.append("data")
        
        # Add query parameters
        for name, _, required in query_params:
            param_names.append(name)
            if not required:
                default_params.append(f"{name} = undefined")
        
        # Add header parameters
        for name, _, required in header_params:
            param_names.append(f"{name}Header")
            if not required:
                default_params.append(f"{name}Header = undefined")
        
        # Replace required params with their names and non-required with default values
        params_signature = []
        for name in param_names:
            if any(name == p.split(' = ')[0] for p in default_params):
                params_signature.append(next(p for p in default_params if p.startswith(name)))
            else:
                params_signature.append(name)
        
        # Generate method
        code += f"""
  /**
   * {description}
   *
{chr(10).join(jsdoc_params)}
   * @returns {{Promise<Object>}} - API response
   */
  async {method_name}({', '.join(params_signature)}) {{
    // Build the URL with path parameters
    let path = "{path}";
    {chr(10).join([f'    path = path.replace("{{{name}}}", {name});' for name, _, _ in path_params])}
    
    // Prepare query parameters
    const params = {{}};
    {chr(10).join([f'    if ({name} !== undefined) {{\n      params["{name}"] = {name};\n    }}' for name, _, _ in query_params])}
    
    // Prepare headers
    const headers = {{}};
    {chr(10).join([f'    if ({name}Header !== undefined) {{\n      headers["{name}"] = {name}Header;\n    }}' for name, _, _ in header_params])}
    
    // Make the request
    return this._makeRequest(
      "{http_method}",
      path,
      {{
        {f'body: JSON.stringify(data),' if has_body and body_content_type == 'application/json' else ''}
        {f'body: data,' if has_body and body_content_type != 'application/json' else ''}
        params,
        headers
      }}
    );
  }}
"""
    
    # Close the class
    code += "}\n\n// Export the client\n"
    code += f"export default {api_title}Client;\n"
    
    return code

def generate_client_code(spec: Dict[str, Any], language: str) -> str:
    """Generate client code for the OpenAPI specification.
    
    Args:
        spec: OpenAPI specification
        language: Target language (python, javascript)
        
    Returns:
        Generated client code
    """
    if language.lower() == 'python':
        return _generate_python_client(spec)
    elif language.lower() in ['javascript', 'js']:
        return _generate_javascript_client(spec)
    else:
        raise ValueError(f"Unsupported language: {language}") 