"""
Mock API Service for PepperPy API

This module provides a mock implementation of the workflow service
used for the API.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict, Union, Literal

from pydantic import BaseModel, Field


class ApiSpec(TypedDict, total=False):
    """API specification structure."""
    
    openapi: str
    info: Dict[str, Any]
    paths: Dict[str, Dict[str, Any]]
    components: Dict[str, Any]


class WorkflowResult(BaseModel):
    """Result from workflow execution."""
    
    status: str = Field(description="Status of the workflow execution (success, error, etc.)")
    message: str = Field(description="Message describing the result")
    timestamp: str = Field(description="ISO format timestamp of the execution")
    data: Dict[str, Any] = Field(description="Result data from the workflow execution")


class WorkflowInfo(BaseModel):
    """Information about a workflow."""
    
    id: str = Field(description="Unique identifier for the workflow")
    name: str = Field(description="Display name of the workflow")
    description: str = Field(description="Description of what the workflow does")
    category: str = Field(description="Category of the workflow (governance, design, etc.)")


class WorkflowSchema(BaseModel):
    """Schema for a workflow."""
    
    id: str = Field(description="Unique identifier for the workflow")
    name: str = Field(description="Display name of the workflow")
    description: str = Field(description="Description of what the workflow does")
    schema: Dict[str, Any] = Field(description="JSON Schema for the workflow's inputs and outputs")


class WorkflowExecuteRequest(BaseModel):
    """Request for executing a workflow."""
    
    input_data: Dict[str, Any] = Field(description="Input data for the workflow")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Optional configuration for the workflow")


class MockWorkflowService:
    """Mock workflow service for API demonstration."""
    
    def __init__(self) -> None:
        """Initialize the mock service."""
        self._initialized = False
        self._workflows = {
            "api_governance": {
                "name": "API Governance Workflow",
                "description": "Assesses API specifications against governance rules",
                "category": "governance",
                "schema": {
                    "input": {
                        "type": "object",
                        "properties": {
                            "api_spec": {"type": "object", "description": "OpenAPI specification to assess"},
                            "output_format": {"type": "string", "enum": ["json", "markdown", "html"]},
                            "rule_set": {"type": "string", "default": "default"}
                        },
                        "required": ["api_spec"]
                    },
                    "output": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "findings": {"type": "object"},
                            "pass_rate": {"type": "string"},
                            "recommendations": {"type": "array"}
                        }
                    }
                }
            },
            "api_blueprint": {
                "name": "API Blueprint Workflow",
                "description": "Generates API specifications from user stories",
                "category": "design",
                "schema": {
                    "input": {
                        "type": "object",
                        "properties": {
                            "user_stories": {"type": "array", "items": {"type": "string"}},
                            "output_format": {"type": "string", "enum": ["openapi", "raml", "json_schema"]},
                            "target_tech": {"type": "string", "description": "Target technology stack"}
                        },
                        "required": ["user_stories"]
                    },
                    "output": {
                        "type": "object",
                        "properties": {
                            "specification": {"type": "object"},
                            "documentation_url": {"type": "string"},
                            "project_files": {"type": "integer"}
                        }
                    }
                }
            },
            "api_mock": {
                "name": "API Mock Workflow",
                "description": "Creates mock servers from API specifications",
                "category": "testing",
                "schema": {
                    "input": {
                        "type": "object",
                        "properties": {
                            "api_spec": {"type": "object", "description": "OpenAPI specification to mock"},
                            "port": {"type": "integer", "default": 8080},
                            "response_delay": {"type": "integer", "description": "Simulated delay in ms"}
                        },
                        "required": ["api_spec"]
                    },
                    "output": {
                        "type": "object",
                        "properties": {
                            "server_url": {"type": "string"},
                            "docs_url": {"type": "string"},
                            "endpoints": {"type": "array"}
                        }
                    }
                }
            },
            "api_evolution": {
                "name": "API Evolution Workflow",
                "description": "Analyzes API changes for compatibility",
                "category": "governance",
                "schema": {
                    "input": {
                        "type": "object",
                        "properties": {
                            "current_api": {"type": "object", "description": "Current API specification"},
                            "proposed_api": {"type": "object", "description": "Proposed API specification"},
                            "output_format": {"type": "string", "enum": ["json", "markdown"]}
                        },
                        "required": ["current_api", "proposed_api"]
                    },
                    "output": {
                        "type": "object",
                        "properties": {
                            "changes": {"type": "object"},
                            "breaking_changes": {"type": "array"},
                            "compatibility_score": {"type": "number"},
                            "migration_plan": {"type": "object"}
                        }
                    }
                }
            },
            "api_ready": {
                "name": "API Ready Workflow",
                "description": "Enhances APIs with agent-ready capabilities",
                "category": "enhancement",
                "schema": {
                    "input": {
                        "type": "object",
                        "properties": {
                            "spec_path": {"type": "string", "description": "Path to the API spec file"},
                            "enhancement_options": {
                                "type": "object",
                                "properties": {
                                    "agent_discovery": {"type": "boolean", "default": true},
                                    "auth_mechanism": {"type": "string", "enum": ["api_key", "oauth", "jwt", "none"], "default": "api_key"},
                                    "observability": {"type": "boolean", "default": true},
                                    "rate_limiting": {"type": "boolean", "default": true},
                                    "documentation": {"type": "boolean", "default": true}
                                }
                            },
                            "output_dir": {"type": "string", "description": "Directory to save enhanced spec"}
                        },
                        "required": ["spec_path"]
                    },
                    "output": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "result": {
                                "type": "object",
                                "properties": {
                                    "original_endpoints": {"type": "integer"},
                                    "enhanced_endpoints": {"type": "integer"},
                                    "added_endpoints": {"type": "array"},
                                    "enhancement_summary": {"type": "string"},
                                    "spec_path": {"type": "string"}
                                }
                            },
                            "message": {"type": "string"}
                        }
                    }
                }
            }
        }
    
    async def initialize(self) -> None:
        """Initialize the service."""
        if self._initialized:
            return
        
        # Simulate initialization
        await asyncio.sleep(0.5)
        self._initialized = True
        print("Mock workflow service initialized")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self._initialized:
            return
        
        # Simulate cleanup
        await asyncio.sleep(0.2)
        self._initialized = False
        print("Mock workflow service cleaned up")
    
    async def get_available_workflows(self) -> List[WorkflowInfo]:
        """Get available workflows."""
        if not self._initialized:
            await self.initialize()
        
        # Return list of available workflows with their details
        return [
            WorkflowInfo(
                id=wf_id,
                name=details["name"],
                description=details["description"],
                category=details.get("category", "other")
            )
            for wf_id, details in self._workflows.items()
        ]
    
    async def get_workflow_schema(self, workflow_id: str) -> WorkflowSchema:
        """Get schema for a specific workflow."""
        if not self._initialized:
            await self.initialize()
        
        # Check if workflow exists
        if workflow_id not in self._workflows:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        
        workflow = self._workflows[workflow_id]
        return WorkflowSchema(
            id=workflow_id,
            name=workflow["name"],
            description=workflow["description"],
            schema=workflow.get("schema", {})
        )
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """Execute a workflow."""
        if not self._initialized:
            await self.initialize()
        
        # Check if workflow exists
        if workflow_id not in self._workflows:
            return WorkflowResult(
                status="error",
                message=f"Unknown workflow: {workflow_id}",
                timestamp=datetime.now().isoformat(),
                data={}
            )
        
        # Simulate processing time based on complexity
        print(f"Executing {workflow_id} workflow...")
        await asyncio.sleep(1.5)
        
        # Generate different results based on workflow type
        result_data: Dict[str, Any] = {
            "status": "success",
            "message": f"{workflow_id} executed successfully",
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        # Customize result based on workflow type
        if workflow_id == "api_governance":
            api_spec = input_data.get("api_spec", {})
            result_data = self._generate_governance_result(api_spec)
        
        elif workflow_id == "api_blueprint":
            user_stories = input_data.get("user_stories", [])
            target_tech = input_data.get("target_tech", "node")
            result_data = self._generate_blueprint_result(user_stories, target_tech)
        
        elif workflow_id == "api_mock":
            api_spec = input_data.get("api_spec", {})
            port = input_data.get("port", 8080)
            result_data = self._generate_mock_result(api_spec, port)
        
        elif workflow_id == "api_evolution":
            current_api = input_data.get("current_api", {})
            proposed_api = input_data.get("proposed_api", {})
            result_data = self._generate_evolution_result(current_api, proposed_api)
        
        elif workflow_id == "api_ready":
            spec_path = input_data.get("spec_path", "")
            enhancement_options = input_data.get("enhancement_options", {})
            output_dir = input_data.get("output_dir", "/tmp")
            result_data = self._generate_api_ready_result(spec_path, enhancement_options, output_dir)
        
        return WorkflowResult(**result_data)
    
    def _generate_governance_result(self, api_spec: ApiSpec) -> Dict[str, Any]:
        """Generate governance assessment result."""
        paths = api_spec.get("paths", {})
        path_count = len(paths)
        
        # Count security definitions
        security_schemes = api_spec.get("components", {}).get("securitySchemes", {})
        security_count = len(security_schemes)
        
        # Generate findings
        findings = {
            "security": 3 if security_count == 0 else 1,
            "standards": 1,
            "documentation": 2
        }
        
        # Calculate pass rate
        total_issues = sum(findings.values())
        max_issues = 10
        pass_rate = int(100 * (1 - total_issues / max_issues))
        
        # Generate recommendations
        recommendations = []
        if findings["security"] > 1:
            recommendations.append("Add OAuth2 security scheme")
        if findings["documentation"] > 1:
            recommendations.append("Improve endpoint documentation")
        if findings["standards"] > 0:
            recommendations.append("Add response schemas for all endpoints")
        
        return {
            "status": "success",
            "message": "API governance assessment completed",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "findings": findings,
                "pass_rate": f"{pass_rate}%",
                "recommendations": recommendations,
                "details": {
                    "endpoints_assessed": path_count,
                    "security_schemes": security_count,
                    "compliance_status": "Needs Improvement" if pass_rate < 80 else "Compliant"
                }
            }
        }
    
    def _generate_blueprint_result(
        self, user_stories: List[str], target_tech: str
    ) -> Dict[str, Any]:
        """Generate API blueprint result."""
        # Count stories for entity detection
        story_count = len(user_stories)
        
        # Generate API spec based on stories
        entities = ["User", "Profile"]
        endpoints = []
        
        for entity in entities:
            endpoints.extend([
                f"/{entity.lower()}s",
                f"/{entity.lower()}s/{{id}}"
            ])
        
        # Generate specification
        specification = {
            "openapi": "3.0.0",
            "info": {
                "title": "Generated API",
                "version": "1.0.0",
                "description": f"API generated from {story_count} user stories"
            },
            "paths": {
                endpoint: {
                    "get": {
                        "summary": f"Get {endpoint.split('/')[-1]}",
                        "responses": {
                            "200": {
                                "description": "Success"
                            }
                        }
                    }
                } for endpoint in endpoints
            }
        }
        
        # Add POST operations
        for entity in entities:
            endpoint = f"/{entity.lower()}s"
            specification["paths"][endpoint]["post"] = {
                "summary": f"Create {entity.lower()}",
                "responses": {
                    "201": {
                        "description": "Created"
                    }
                }
            }
        
        return {
            "status": "success",
            "message": "API blueprint generated",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "specification": specification,
                "documentation_url": "http://example.com/docs",
                "project_files": 14,
                "implementation": {
                    "language": "javascript" if target_tech == "node" else target_tech,
                    "framework": "express" if target_tech == "node" else "django" if target_tech == "python" else "other",
                    "entities": entities,
                    "endpoints": endpoints,
                    "authentication": "jwt"
                }
            }
        }
    
    def _generate_mock_result(self, api_spec: ApiSpec, port: int) -> Dict[str, Any]:
        """Generate API mock server result."""
        paths = api_spec.get("paths", {})
        endpoints = [path for path in paths.keys()]
        
        return {
            "status": "success",
            "message": "API mock server created",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "server_url": f"http://localhost:{port}",
                "docs_url": f"http://localhost:{port}/docs",
                "endpoints": [
                    {
                        "path": endpoint,
                        "methods": ["GET", "POST"] if "users" in endpoint else ["GET"],
                        "sample_response": {
                            "data": [{"id": 1, "name": "Sample"}] if endpoint.endswith("s") else {"id": 1, "name": "Sample"}
                        }
                    }
                    for endpoint in endpoints
                ]
            }
        }
    
    def _generate_evolution_result(
        self, current_api: ApiSpec, proposed_api: ApiSpec
    ) -> Dict[str, Any]:
        """Generate API evolution analysis result."""
        # Compare paths
        current_paths = set(current_api.get("paths", {}).keys())
        proposed_paths = set(proposed_api.get("paths", {}).keys())
        
        # Find changes
        added_paths = proposed_paths - current_paths
        removed_paths = current_paths - proposed_paths
        common_paths = current_paths.intersection(proposed_paths)
        
        # Check for breaking changes
        breaking_changes = []
        if removed_paths:
            for path in removed_paths:
                breaking_changes.append({
                    "type": "removed_endpoint",
                    "path": path,
                    "impact": "high"
                })
        
        # Check common paths for parameter changes
        for path in common_paths:
            current_params = self._extract_params(current_api, path)
            proposed_params = self._extract_params(proposed_api, path)
            
            # Find required params added (breaking change)
            for param, details in proposed_params.items():
                if param not in current_params and details.get("required", False):
                    breaking_changes.append({
                        "type": "added_required_parameter",
                        "path": path,
                        "parameter": param,
                        "impact": "medium"
                    })
        
        # Calculate compatibility score
        total_endpoints = len(current_paths.union(proposed_paths))
        breaking_count = len(breaking_changes)
        compatibility_score = round(100 * (1 - breaking_count / (total_endpoints or 1)), 1)
        
        # Generate migration plan
        migration_plan = {
            "steps": [
                {
                    "description": f"Update client code to handle removed endpoint: {path}",
                    "priority": "high"
                }
                for path in removed_paths
            ]
        }
        
        # Add steps for parameter changes
        for change in breaking_changes:
            if change["type"] == "added_required_parameter":
                migration_plan["steps"].append({
                    "description": f"Update clients to include required parameter: {change['parameter']} for {change['path']}",
                    "priority": "medium"
                })
        
        return {
            "status": "success",
            "message": "API evolution analysis completed",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "changes": {
                    "added_endpoints": list(added_paths),
                    "removed_endpoints": list(removed_paths),
                    "modified_endpoints": len(common_paths),
                    "total_changes": len(added_paths) + len(removed_paths) + breaking_count
                },
                "breaking_changes": breaking_changes,
                "compatibility_score": compatibility_score,
                "migration_plan": migration_plan,
                "versioning_recommendation": "major" if breaking_count > 0 else "minor"
            }
        }
    
    def _extract_params(self, api_spec: ApiSpec, path: str) -> Dict[str, Any]:
        """Extract parameters from an API path."""
        path_obj = api_spec.get("paths", {}).get(path, {})
        result = {}
        
        # Extract from all methods (GET, POST, etc.)
        for method, details in path_obj.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                for param in details.get("parameters", []):
                    name = param.get("name", "")
                    if name:
                        result[name] = param
        
        return result
        
    def _generate_api_ready_result(
        self, 
        spec_path: str,
        enhancement_options: Dict[str, Any],
        output_dir: str
    ) -> Dict[str, Any]:
        """Generate API Ready result."""
        # Mock enhancement process
        
        # Default enhancement options merged with provided ones
        default_options = {
            "agent_discovery": True,
            "auth_mechanism": "api_key",
            "observability": True,
            "rate_limiting": True,
            "documentation": True
        }
        
        # Merge with provided options
        for key, value in enhancement_options.items():
            if key in default_options:
                default_options[key] = value
                
        # Mock endpoints added based on options
        added_endpoints = []
        
        if default_options.get("agent_discovery"):
            added_endpoints.append("/.well-known/ai-plugin.json")
            
        if default_options.get("auth_mechanism") == "oauth":
            added_endpoints.append("/oauth/token")
            
        if default_options.get("observability"):
            added_endpoints.append("/metrics")
            added_endpoints.append("/health")
            
        # Generate mock file path
        mock_file_path = f"{output_dir}/enhanced_api_spec.json"
        if spec_path.endswith((".yaml", ".yml")):
            mock_file_path = f"{output_dir}/enhanced_api_spec.yaml"
        
        # Generate enhancement summary
        summary = f"""
API Enhancement Summary:
- Original endpoints: 8
- Enhanced endpoints: {8 + len(added_endpoints)}
- Added endpoints: {len(added_endpoints)}
- Enhancement features:
  - Agent discovery: {"Added" if default_options.get("agent_discovery") else "Skipped"}
  - Authentication: {default_options.get("auth_mechanism", "none").upper()}
  - Observability: {"Added" if default_options.get("observability") else "Skipped"}
  - Rate limiting: {"Added" if default_options.get("rate_limiting") else "Skipped"}
  - Documentation: {"Enhanced" if default_options.get("documentation") else "Unchanged"}
"""
        
        return {
            "status": "success",
            "message": "API successfully enhanced with agent-ready capabilities",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "result": {
                    "original_endpoints": 8,
                    "enhanced_endpoints": 8 + len(added_endpoints),
                    "added_endpoints": added_endpoints,
                    "enhancement_summary": summary,
                    "spec_path": mock_file_path
                }
            }
        }


# Initialize a singleton instance
mock_workflow_service = MockWorkflowService() 