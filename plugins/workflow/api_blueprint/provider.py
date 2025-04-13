"""
API Blueprint Workflow Provider for PepperPy.

This workflow generates API contracts, documentation, and code
implementations from natural language user stories.
"""

import os
import json
import asyncio
import tempfile
from pathlib import Path
from enum import Enum
from typing import Dict, List, Any, Optional, TypedDict, Union, Literal

from pepperpy.core.logging import get_logger
from pepperpy.plugin import ProviderPlugin
from pepperpy.workflow import BaseWorkflowProvider

logger = get_logger(__name__)

class OutputFormat(str, Enum):
    """Output formats for API specifications."""
    OPENAPI = "openapi"
    RAML = "raml"
    JSON_SCHEMA = "json_schema"
    POSTMAN = "postman"


class APIResource(TypedDict):
    """Structure for an API resource."""
    name: str
    description: str
    endpoints: List[Dict[str, Any]]
    schema: Dict[str, Any]


class APIBlueprint(TypedDict):
    """Structure for a complete API blueprint."""
    title: str
    version: str
    description: str
    resources: List[APIResource]
    security_schemes: List[Dict[str, Any]]
    tags: List[Dict[str, Any]]
    servers: List[Dict[str, Any]]


class DocumentationOutput(TypedDict):
    """Structure for documentation output."""
    format: str
    content: str
    path: Optional[str]


class ProjectStructure(TypedDict):
    """Structure for generated project code."""
    language: str
    files: List[Dict[str, Any]]
    dependencies: List[str]
    setup_instructions: str


class BlueprintResult(TypedDict):
    """Result of API blueprint generation."""
    blueprint: APIBlueprint
    documentation: List[DocumentationOutput]
    project: Optional[ProjectStructure]


class APIBlueprintProvider(BaseWorkflowProvider, ProviderPlugin):
    """Provider for generating API blueprints from user stories.
    
    This workflow takes natural language user stories and converts them
    into API contracts, documentation, and optionally code implementations.
    """
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return
        
        logger.info("Initializing API Blueprint workflow provider")
        
        # Initialize properties from config
        self.llm_provider = self.config.get("llm_config", {}).get("provider", "openai")
        self.llm_model = self.config.get("llm_config", {}).get("model", "gpt-4")
        
        # Set default output formats
        self.default_output_formats = [OutputFormat.OPENAPI]
        
        self.initialized = True
        logger.info("API Blueprint workflow provider initialized")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return
        
        logger.info("Cleaning up API Blueprint workflow provider")
        self.initialized = False
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the API Blueprint workflow.
        
        Args:
            input_data: Dict containing:
                - user_stories: User stories text
                - output_formats: List of output formats
                - generate_code: Whether to generate code
                - language: Programming language for code generation
                - output_dir: Directory for saving outputs
        
        Returns:
            Result of the blueprint generation
        """
        try:
            if not self.initialized:
                await self.initialize()
            
            # Extract and validate input
            user_stories = input_data.get("user_stories")
            if not user_stories:
                return {"error": "User stories are required"}
            
            output_formats = input_data.get("output_formats", [self.default_output_formats[0].value])
            if isinstance(output_formats, str):
                output_formats = [output_formats]
                
            generate_code = input_data.get("generate_code", False)
            language = input_data.get("language", "python") if generate_code else None
            output_dir = input_data.get("output_dir")
            
            # Create output directory if provided
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Analyze user stories
            analysis = await self._analyze_user_stories(user_stories)
            
            # Design API structure
            api_blueprint = await self._design_api_structure(analysis)
            
            # Generate documentation in requested formats
            documentation = await self._generate_outputs(api_blueprint, output_formats, output_dir)
            
            # Generate code implementation if requested
            project = None
            if generate_code and language:
                project = await self._generate_code(api_blueprint, language, output_dir)
            
            # Create result
            result = BlueprintResult(
                blueprint=api_blueprint,
                documentation=documentation,
                project=project
            )
            
            return {
                "status": "success",
                "result": result,
                "message": "API blueprint generated successfully"
            }
        
        except Exception as e:
            logger.error(f"Error executing API Blueprint workflow: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _analyze_user_stories(self, user_stories: str) -> Dict[str, Any]:
        """Analyze user stories to extract API requirements.
        
        Args:
            user_stories: User stories text
            
        Returns:
            Analysis of the user stories
        """
        # In a real implementation, this would use an LLM to analyze the user stories
        # For now, we'll implement a basic analysis
        
        # Split stories and process each one
        stories = [s.strip() for s in user_stories.split("\n") if s.strip()]
        
        entities = set()
        actions = set()
        relationships = []
        
        for story in stories:
            # Basic extraction of entities and actions
            words = story.split()
            for i, word in enumerate(words):
                if word.lower() in ["user", "admin", "customer", "member"]:
                    entities.add(word.lower())
                if i > 0 and word.lower() in ["create", "read", "update", "delete", "list", "search", "filter"]:
                    actions.add(word.lower())
                    if i + 1 < len(words) and words[i+1] not in ["to", "for", "the", "a", "an"]:
                        entity = words[i+1].lower().rstrip(".,;:s")
                        entities.add(entity)
                        relationships.append((word.lower(), entity))
        
        return {
            "entities": list(entities),
            "actions": list(actions),
            "relationships": relationships,
            "stories": stories
        }
    
    async def _design_api_structure(self, analysis: Dict[str, Any]) -> APIBlueprint:
        """Design API structure based on analysis.
        
        Args:
            analysis: Analysis of user stories
            
        Returns:
            API blueprint structure
        """
        # Generate API title from entities
        entities = analysis.get("entities", [])
        title = "API"
        if entities:
            main_entities = sorted(entities, key=len, reverse=True)[:3]
            title = f"{' '.join(e.title() for e in main_entities)} API"
        
        # Generate resources from entities and relationships
        resources = []
        for entity in entities:
            # Skip common user types as they're typically not resources
            if entity in ["user", "admin", "customer", "member"]:
                continue
                
            # Create endpoints for this resource
            endpoints = []
            
            # GET collection
            endpoints.append({
                "path": f"/{entity}s",
                "method": "get",
                "summary": f"List all {entity}s",
                "description": f"Returns a list of {entity}s with pagination",
                "parameters": [
                    {"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}},
                    {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {
                        "description": "Successful operation",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": f"#/components/schemas/{entity.title()}"}
                                }
                            }
                        }
                    }
                }
            })
            
            # GET single
            endpoints.append({
                "path": f"/{entity}s/{{{entity}_id}}",
                "method": "get",
                "summary": f"Get a {entity} by ID",
                "description": f"Returns a single {entity}",
                "parameters": [
                    {"name": f"{entity}_id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {
                        "description": "Successful operation",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{entity.title()}"}
                            }
                        }
                    },
                    "404": {
                        "description": f"{entity.title()} not found"
                    }
                }
            })
            
            # POST
            endpoints.append({
                "path": f"/{entity}s",
                "method": "post",
                "summary": f"Create a new {entity}",
                "description": f"Creates a new {entity} with the provided data",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{entity.title()}Create"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": f"{entity.title()} created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{entity.title()}"}
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid input"
                    }
                }
            })
            
            # PUT
            endpoints.append({
                "path": f"/{entity}s/{{{entity}_id}}",
                "method": "put",
                "summary": f"Update a {entity}",
                "description": f"Updates an existing {entity} with the provided data",
                "parameters": [
                    {"name": f"{entity}_id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{entity.title()}Update"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": f"{entity.title()} updated",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{entity.title()}"}
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid input"
                    },
                    "404": {
                        "description": f"{entity.title()} not found"
                    }
                }
            })
            
            # DELETE
            endpoints.append({
                "path": f"/{entity}s/{{{entity}_id}}",
                "method": "delete",
                "summary": f"Delete a {entity}",
                "description": f"Deletes a {entity}",
                "parameters": [
                    {"name": f"{entity}_id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {
                    "204": {
                        "description": f"{entity.title()} deleted"
                    },
                    "404": {
                        "description": f"{entity.title()} not found"
                    }
                }
            })
            
            # Generate schema
            schema = {
                entity.title(): {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    },
                    "required": ["id", "name"]
                },
                f"{entity.title()}Create": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["name"]
                },
                f"{entity.title()}Update": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"}
                    }
                }
            }
            
            # Create resource
            resources.append({
                "name": entity,
                "description": f"Operations related to {entity}s",
                "endpoints": endpoints,
                "schema": schema
            })
        
        # Create API blueprint
        api_blueprint = APIBlueprint(
            title=title,
            version="1.0.0",
            description=f"API for managing {', '.join(e for e in entities if e not in ['user', 'admin', 'customer', 'member'])}",
            resources=resources,
            security_schemes=[
                {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "name": "BearerAuth"
                }
            ],
            tags=[{"name": entity.title(), "description": f"Operations related to {entity}s"} for entity in entities if entity not in ["user", "admin", "customer", "member"]],
            servers=[
                {
                    "url": "https://api.example.com/v1",
                    "description": "Production server"
                },
                {
                    "url": "https://staging-api.example.com/v1",
                    "description": "Staging server"
                }
            ]
        )
        
        return api_blueprint
    
    async def _generate_outputs(self, 
                              blueprint: APIBlueprint, 
                              output_formats: List[str],
                              output_dir: Optional[str]) -> List[DocumentationOutput]:
        """Generate API documentation in the requested formats.
        
        Args:
            blueprint: API blueprint
            output_formats: List of output formats
            output_dir: Directory for saving outputs
            
        Returns:
            List of documentation outputs
        """
        documentation = []
        
        for format_name in output_formats:
            output_format = format_name.lower()
            
            if output_format == OutputFormat.OPENAPI.value:
                # Generate OpenAPI 3.0 spec
                openapi_spec = await self._generate_openapi_spec(blueprint)
                
                # Convert to string
                content = json.dumps(openapi_spec, indent=2)
                
                # Save to file if output_dir is provided
                path = None
                if output_dir:
                    path = os.path.join(output_dir, f"{blueprint['title'].lower().replace(' ', '_')}_openapi.json")
                    with open(path, "w") as f:
                        f.write(content)
                
                documentation.append({
                    "format": output_format,
                    "content": content,
                    "path": path
                })
                
            elif output_format == OutputFormat.RAML.value:
                # Generate RAML spec
                raml_spec = await self._generate_raml_spec(blueprint)
                
                # Save to file if output_dir is provided
                path = None
                if output_dir:
                    path = os.path.join(output_dir, f"{blueprint['title'].lower().replace(' ', '_')}.raml")
                    with open(path, "w") as f:
                        f.write(raml_spec)
                
                documentation.append({
                    "format": output_format,
                    "content": raml_spec,
                    "path": path
                })
                
            elif output_format == OutputFormat.JSON_SCHEMA.value:
                # Generate JSON Schema
                json_schema = await self._generate_json_schema(blueprint)
                
                # Convert to string
                content = json.dumps(json_schema, indent=2)
                
                # Save to file if output_dir is provided
                path = None
                if output_dir:
                    path = os.path.join(output_dir, f"{blueprint['title'].lower().replace(' ', '_')}_schema.json")
                    with open(path, "w") as f:
                        f.write(content)
                
                documentation.append({
                    "format": output_format,
                    "content": content,
                    "path": path
                })
                
            elif output_format == OutputFormat.POSTMAN.value:
                # Generate Postman collection
                postman_collection = await self._generate_postman_collection(blueprint)
                
                # Convert to string
                content = json.dumps(postman_collection, indent=2)
                
                # Save to file if output_dir is provided
                path = None
                if output_dir:
                    path = os.path.join(output_dir, f"{blueprint['title'].lower().replace(' ', '_')}_postman.json")
                    with open(path, "w") as f:
                        f.write(content)
                
                documentation.append({
                    "format": output_format,
                    "content": content,
                    "path": path
                })
        
        return documentation
    
    async def _generate_openapi_spec(self, blueprint: APIBlueprint) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification from blueprint.
        
        Args:
            blueprint: API blueprint
            
        Returns:
            OpenAPI specification
        """
        # Create base OpenAPI structure
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": blueprint["title"],
                "version": blueprint["version"],
                "description": blueprint["description"]
            },
            "servers": blueprint["servers"],
            "tags": blueprint["tags"],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {}
            }
        }
        
        # Add security schemes
        for scheme in blueprint["security_schemes"]:
            openapi_spec["components"]["securitySchemes"][scheme["name"]] = {
                "type": scheme["type"],
                "scheme": scheme["scheme"]
            }
            if "bearerFormat" in scheme:
                openapi_spec["components"]["securitySchemes"][scheme["name"]]["bearerFormat"] = scheme["bearerFormat"]
        
        # Add global security requirement
        openapi_spec["security"] = [
            {scheme["name"]: []} for scheme in blueprint["security_schemes"]
        ]
        
        # Add paths and schemas
        for resource in blueprint["resources"]:
            # Add endpoints
            for endpoint in resource["endpoints"]:
                path = endpoint["path"]
                method = endpoint["method"]
                
                # Initialize path if not exists
                if path not in openapi_spec["paths"]:
                    openapi_spec["paths"][path] = {}
                
                # Add operation
                openapi_spec["paths"][path][method] = {
                    "summary": endpoint["summary"],
                    "description": endpoint["description"],
                    "tags": [resource["name"].title()],
                    "responses": endpoint["responses"]
                }
                
                # Add parameters if present
                if "parameters" in endpoint:
                    openapi_spec["paths"][path][method]["parameters"] = endpoint["parameters"]
                
                # Add request body if present
                if "requestBody" in endpoint:
                    openapi_spec["paths"][path][method]["requestBody"] = endpoint["requestBody"]
            
            # Add schemas
            for schema_name, schema in resource["schema"].items():
                openapi_spec["components"]["schemas"][schema_name] = schema
        
        return openapi_spec
    
    async def _generate_raml_spec(self, blueprint: APIBlueprint) -> str:
        """Generate RAML specification from blueprint.
        
        Args:
            blueprint: API blueprint
            
        Returns:
            RAML specification
        """
        # Simple RAML generation
        raml = f"#%RAML 1.0\n"
        raml += f"title: {blueprint['title']}\n"
        raml += f"version: {blueprint['version']}\n"
        raml += f"description: {blueprint['description']}\n\n"
        
        # Add types
        raml += "types:\n"
        for resource in blueprint["resources"]:
            for schema_name, schema in resource["schema"].items():
                raml += f"  {schema_name}:\n"
                raml += f"    type: object\n"
                raml += f"    properties:\n"
                for prop_name, prop in schema.get("properties", {}).items():
                    raml += f"      {prop_name}: {prop.get('type', 'string')}\n"
        
        # Add resources
        for resource in blueprint["resources"]:
            base_path = f"/{resource['name']}s"
            raml += f"\n{base_path}:\n"
            raml += f"  displayName: {resource['name'].title()} Collection\n"
            
            # Add methods for collection endpoints
            for endpoint in resource["endpoints"]:
                if endpoint["path"] == base_path:
                    raml += f"  {endpoint['method']}:\n"
                    raml += f"    description: {endpoint['description']}\n"
                    
                    # Add request body if present
                    if "requestBody" in endpoint:
                        body_schema = endpoint["requestBody"]["content"]["application/json"]["schema"]["$ref"].split("/")[-1]
                        raml += f"    body:\n"
                        raml += f"      application/json:\n"
                        raml += f"        type: {body_schema}\n"
                    
                    # Add responses
                    raml += f"    responses:\n"
                    for status, response in endpoint["responses"].items():
                        raml += f"      {status}:\n"
                        raml += f"        description: {response['description']}\n"
                        if "content" in response:
                            content_schema = response["content"]["application/json"]["schema"]
                            if "$ref" in content_schema:
                                schema_ref = content_schema["$ref"].split("/")[-1]
                                raml += f"        body:\n"
                                raml += f"          application/json:\n"
                                raml += f"            type: {schema_ref}\n"
                            elif "type" in content_schema and content_schema["type"] == "array":
                                item_ref = content_schema["items"]["$ref"].split("/")[-1]
                                raml += f"        body:\n"
                                raml += f"          application/json:\n"
                                raml += f"            type: array\n"
                                raml += f"            items: {item_ref}\n"
            
            # Add item resource
            raml += f"\n  /{{{resource['name']}_id}}:\n"
            raml += f"    displayName: {resource['name'].title()} Item\n"
            
            # Add methods for item endpoints
            for endpoint in resource["endpoints"]:
                if endpoint["path"] == f"{base_path}/{{{resource['name']}_id}}":
                    raml += f"    {endpoint['method']}:\n"
                    raml += f"      description: {endpoint['description']}\n"
                    
                    # Add request body if present
                    if "requestBody" in endpoint:
                        body_schema = endpoint["requestBody"]["content"]["application/json"]["schema"]["$ref"].split("/")[-1]
                        raml += f"      body:\n"
                        raml += f"        application/json:\n"
                        raml += f"          type: {body_schema}\n"
                    
                    # Add responses
                    raml += f"      responses:\n"
                    for status, response in endpoint["responses"].items():
                        raml += f"        {status}:\n"
                        raml += f"          description: {response['description']}\n"
                        if "content" in response:
                            content_schema = response["content"]["application/json"]["schema"]
                            if "$ref" in content_schema:
                                schema_ref = content_schema["$ref"].split("/")[-1]
                                raml += f"          body:\n"
                                raml += f"            application/json:\n"
                                raml += f"              type: {schema_ref}\n"
        
        return raml
    
    async def _generate_json_schema(self, blueprint: APIBlueprint) -> Dict[str, Any]:
        """Generate JSON Schema from blueprint.
        
        Args:
            blueprint: API blueprint
            
        Returns:
            JSON Schema
        """
        # Create JSON Schema
        json_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": blueprint["title"],
            "description": blueprint["description"],
            "definitions": {}
        }
        
        # Add schema definitions
        for resource in blueprint["resources"]:
            for schema_name, schema in resource["schema"].items():
                # Convert OpenAPI schema to JSON Schema
                json_schema["definitions"][schema_name] = {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", [])
                }
        
        return json_schema
    
    async def _generate_postman_collection(self, blueprint: APIBlueprint) -> Dict[str, Any]:
        """Generate Postman collection from blueprint.
        
        Args:
            blueprint: API blueprint
            
        Returns:
            Postman collection
        """
        # Create Postman collection
        collection = {
            "info": {
                "name": blueprint["title"],
                "description": blueprint["description"],
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        
        # Add resources as folders
        for resource in blueprint["resources"]:
            resource_folder = {
                "name": f"{resource['name'].title()}s",
                "description": resource["description"],
                "item": []
            }
            
            # Add endpoints as requests
            for endpoint in resource["endpoints"]:
                # Replace path parameters with Postman variables
                url = endpoint["path"]
                for param in endpoint.get("parameters", []):
                    if param["in"] == "path":
                        url = url.replace(f"{{{param['name']}}}", f":{param['name']}")
                
                # Create request
                request = {
                    "name": endpoint["summary"],
                    "description": endpoint["description"],
                    "request": {
                        "method": endpoint["method"].upper(),
                        "url": {
                            "raw": f"{{baseUrl}}{url}",
                            "host": ["{{baseUrl}}"],
                            "path": url.strip("/").split("/")
                        },
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "description": endpoint["description"]
                    },
                    "response": []
                }
                
                # Add query parameters
                if endpoint.get("parameters"):
                    query_params = [p for p in endpoint["parameters"] if p["in"] == "query"]
                    if query_params:
                        request["request"]["url"]["query"] = []
                        for param in query_params:
                            request["request"]["url"]["query"].append({
                                "key": param["name"],
                                "value": "",
                                "description": param.get("description", ""),
                                "disabled": not param.get("required", False)
                            })
                
                # Add request body if present
                if "requestBody" in endpoint:
                    request["request"]["body"] = {
                        "mode": "raw",
                        "raw": "{}",
                        "options": {
                            "raw": {
                                "language": "json"
                            }
                        }
                    }
                
                # Add to folder
                resource_folder["item"].append(request)
            
            # Add folder to collection
            collection["item"].append(resource_folder)
        
        return collection
    
    async def _generate_code(self, 
                           blueprint: APIBlueprint, 
                           language: str,
                           output_dir: Optional[str]) -> ProjectStructure:
        """Generate code implementation for API.
        
        Args:
            blueprint: API blueprint
            language: Programming language
            output_dir: Directory for saving outputs
            
        Returns:
            Project structure with generated code
        """
        language = language.lower()
        files = []
        dependencies = []
        setup_instructions = ""
        
        # Generate OpenAPI spec first (needed for code generation)
        openapi_spec = await self._generate_openapi_spec(blueprint)
        
        if language == "python":
            # Generate Python FastAPI implementation
            dependencies = ["fastapi", "uvicorn", "pydantic", "sqlalchemy", "alembic", "python-jose", "passlib"]
            setup_instructions = "pip install " + " ".join(dependencies)
            
            # Create project files
            api_name = blueprint["title"].lower().replace(" ", "_")
            
            # Main app file
            app_py = """
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="{title}",
    description="{description}",
    version="{version}"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
{router_imports}

# Add routers
{router_mounts}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
""".format(
                title=blueprint["title"],
                description=blueprint["description"],
                version=blueprint["version"],
                router_imports="\n".join([f"from routers import {r['name']}_router" for r in blueprint["resources"]]),
                router_mounts="\n".join([f"app.include_router({r['name']}_router.router)" for r in blueprint["resources"]])
            )
            
            files.append({
                "name": "app.py",
                "content": app_py
            })
            
            # Create models
            for resource in blueprint["resources"]:
                model_py = """
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

class {resource_title}Base(BaseModel):
    name: str
    description: Optional[str] = None

class {resource_title}Create({resource_title}Base):
    pass

class {resource_title}Update(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class {resource_title}({resource_title}Base):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
""".format(resource_title=resource["name"].title())
                
                files.append({
                    "name": f"models/{resource['name']}.py",
                    "content": model_py
                })
                
                # Create router
                router_py = """
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID

from models.{resource} import {resource_title}, {resource_title}Create, {resource_title}Update

router = APIRouter(
    prefix="/{resources}",
    tags=["{resource_title}s"]
)

@router.get("/", response_model=List[{resource_title}])
async def get_{resources}(skip: int = 0, limit: int = 100):
    # In a real app, this would query a database
    return []

@router.post("/", response_model={resource_title}, status_code=status.HTTP_201_CREATED)
async def create_{resource}({resource}_in: {resource_title}Create):
    # In a real app, this would create a database record
    return {{
        "id": "00000000-0000-0000-0000-000000000000",
        "name": {resource}_in.name,
        "description": {resource}_in.description,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    }}

@router.get("/{{id}}", response_model={resource_title})
async def get_{resource}(id: UUID):
    # In a real app, this would fetch from a database
    return {{
        "id": id,
        "name": "Sample {resource_title}",
        "description": "This is a sample {resource}",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    }}

@router.put("/{{id}}", response_model={resource_title})
async def update_{resource}(id: UUID, {resource}_in: {resource_title}Update):
    # In a real app, this would update a database record
    return {{
        "id": id,
        "name": {resource}_in.name or "Sample {resource_title}",
        "description": {resource}_in.description or "This is a sample {resource}",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    }}

@router.delete("/{{id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{resource}(id: UUID):
    # In a real app, this would delete from a database
    return None
""".format(
                    resource=resource["name"],
                    resources=f"{resource['name']}s",
                    resource_title=resource["name"].title()
                )
                
                files.append({
                    "name": f"routers/{resource['name']}_router.py",
                    "content": router_py
                })
            
            # Create init files
            files.append({
                "name": "models/__init__.py",
                "content": "# Models package"
            })
            
            files.append({
                "name": "routers/__init__.py",
                "content": "# Routers package"
            })
            
            # Create README
            readme = f"""# {blueprint["title"]}

{blueprint["description"]}

## Setup

1. Install dependencies:
   ```
   {setup_instructions}
   ```

2. Run the application:
   ```
   python app.py
   ```

3. API will be available at http://localhost:8000

4. Swagger documentation: http://localhost:8000/docs
"""
            
            files.append({
                "name": "README.md",
                "content": readme
            })
            
            # Save files if output directory is provided
            if output_dir:
                project_dir = os.path.join(output_dir, api_name)
                os.makedirs(project_dir, exist_ok=True)
                os.makedirs(os.path.join(project_dir, "models"), exist_ok=True)
                os.makedirs(os.path.join(project_dir, "routers"), exist_ok=True)
                
                for file in files:
                    file_path = os.path.join(project_dir, file["name"])
                    with open(file_path, "w") as f:
                        f.write(file["content"])
        
        # Create project structure
        project = ProjectStructure(
            language=language,
            files=files,
            dependencies=dependencies,
            setup_instructions=setup_instructions
        )
        
        return project 