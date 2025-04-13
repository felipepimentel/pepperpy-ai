"""
Mock API Service for PepperPy Playground

This module provides a mock implementation of the workflow service
used for the playground web application.
"""

import asyncio
import json
import os
import logging
import uuid
import yaml
import aiohttp
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApiSpec(TypedDict, total=False):
    """API specification structure."""
    
    openapi: str
    info: Dict[str, Any]
    paths: Dict[str, Dict[str, Any]]
    components: Dict[str, Any]


class WorkflowResult(TypedDict):
    """Result from workflow execution."""
    
    status: str
    message: str
    timestamp: str
    data: Dict[str, Any]


class MockWorkflowService:
    """Mock workflow service for playground demonstration."""
    
    def __init__(self) -> None:
        """Initialize the mock service."""
        self._initialized = False
        self._workflows = {
            "api-governance": {
                "id": "api-governance",
                "name": "API Governance Workflow",
                "description": "Assesses API specifications against governance rules",
                "schema": {
                    "type": "object",
                    "required": ["spec_url"],
                    "properties": {
                        "spec_url": {
                            "type": "string",
                            "title": "API Specification URL",
                            "description": "URL to OpenAPI specification"
                        },
                        "governance_rules": {
                            "type": "array",
                            "title": "Governance Rules",
                            "description": "List of governance rules to check",
                            "items": {
                                "type": "string",
                                "enum": ["security", "standards", "schema", "documentation"]
                            }
                        },
                        "output_format": {
                            "type": "string",
                            "title": "Output Format",
                            "description": "Format of the output report",
                            "enum": ["json", "markdown", "html"],
                            "default": "json"
                        }
                    }
                }
            },
            "simple-chat": {
                "id": "simple-chat",
                "name": "Simple LLM Chat",
                "description": "Basic chat interface with an LLM using PepperPy",
                "schema": {
                    "type": "object",
                    "required": ["message"],
                    "properties": {
                        "message": {
                            "type": "string",
                            "title": "Message",
                            "description": "Message to send to the LLM"
                        },
                        "model": {
                            "type": "string",
                            "title": "Model",
                            "description": "LLM model to use",
                            "enum": ["gpt-4", "gpt-4o-mini", "claude-3-haiku"],
                            "default": "gpt-4o-mini"
                        },
                        "system_prompt": {
                            "type": "string",
                            "title": "System Prompt",
                            "description": "Optional system prompt to use",
                            "default": "You are a helpful assistant."
                        }
                    }
                }
            },
            "api-blueprint": {
                "id": "api-blueprint",
                "name": "API Blueprint Workflow",
                "description": "Generates API specifications from user stories",
                "schema": {
                    "type": "object",
                    "required": ["user_stories"],
                    "properties": {
                        "user_stories": {
                            "type": "string",
                            "title": "User Stories",
                            "description": "User stories in Gherkin format"
                        },
                        "api_name": {
                            "type": "string",
                            "title": "API Name",
                            "description": "Name of the API"
                        },
                        "api_version": {
                            "type": "string",
                            "title": "API Version",
                            "description": "Version of the API",
                            "default": "1.0.0"
                        }
                    }
                }
            },
            "api-mock": {
                "id": "api-mock",
                "name": "API Mock Workflow",
                "description": "Creates mock servers from API specifications",
                "schema": {
                    "type": "object",
                    "required": ["spec_url"],
                    "properties": {
                        "spec_url": {
                            "type": "string",
                            "title": "API Specification URL",
                            "description": "URL to OpenAPI specification"
                        },
                        "port": {
                            "type": "integer",
                            "title": "Port",
                            "description": "Port to run the mock server on",
                            "default": 8080
                        }
                    }
                }
            },
            "api-evolution": {
                "id": "api-evolution",
                "name": "API Evolution Workflow",
                "description": "Analyzes API changes for compatibility",
                "schema": {
                    "type": "object",
                    "required": ["old_spec_url", "new_spec_url"],
                    "properties": {
                        "old_spec_url": {
                            "type": "string",
                            "title": "Old API Specification URL",
                            "description": "URL to old OpenAPI specification"
                        },
                        "new_spec_url": {
                            "type": "string",
                            "title": "New API Specification URL",
                            "description": "URL to new OpenAPI specification"
                        },
                        "check_breaking": {
                            "type": "boolean",
                            "title": "Check Breaking Changes",
                            "description": "Flag to check for breaking changes",
                            "default": True
                        }
                    }
                }
            }
        }
        
        # User-defined custom workflows
        self._user_workflows = {}
        self._workflow_templates = {}
        
        # Workflow components (blocks that can be used to build custom workflows)
        self._workflow_components = {
            "input": [
                {
                    "id": "url-input",
                    "name": "URL Input",
                    "description": "Input URL to a resource",
                    "schema": {
                        "type": "string",
                        "format": "uri"
                    }
                },
                {
                    "id": "text-input",
                    "name": "Text Input",
                    "description": "Free text input field",
                    "schema": {
                        "type": "string"
                    }
                },
                {
                    "id": "number-input",
                    "name": "Number Input",
                    "description": "Numeric input field",
                    "schema": {
                        "type": "number"
                    }
                },
                {
                    "id": "select-input",
                    "name": "Selection Input",
                    "description": "Selection from predefined options",
                    "schema": {
                        "type": "string",
                        "enum": []
                    }
                },
                {
                    "id": "boolean-input",
                    "name": "Boolean Input",
                    "description": "True/False toggle",
                    "schema": {
                        "type": "boolean"
                    }
                }
            ],
            "processor": [
                {
                    "id": "api-validator",
                    "name": "API Validator",
                    "description": "Validates API specifications",
                    "inputs": ["spec_url"],
                    "outputs": ["validation_result"]
                },
                {
                    "id": "api-linter",
                    "name": "API Linter",
                    "description": "Lints API specifications for best practices",
                    "inputs": ["spec_url"],
                    "outputs": ["lint_result"]
                },
                {
                    "id": "text-analyzer",
                    "name": "Text Analyzer",
                    "description": "Analyzes text for sentiment and key concepts",
                    "inputs": ["text"],
                    "outputs": ["analysis_result"]
                },
                {
                    "id": "url-fetcher",
                    "name": "URL Fetcher",
                    "description": "Fetches content from a URL",
                    "inputs": ["url"],
                    "outputs": ["content"]
                }
            ],
            "output": [
                {
                    "id": "json-output",
                    "name": "JSON Output",
                    "description": "Formats result as JSON",
                    "inputs": ["result"]
                },
                {
                    "id": "html-output",
                    "name": "HTML Output",
                    "description": "Formats result as HTML",
                    "inputs": ["result"]
                },
                {
                    "id": "markdown-output",
                    "name": "Markdown Output",
                    "description": "Formats result as Markdown",
                    "inputs": ["result"]
                }
            ]
        }
    
    async def initialize(self) -> None:
        """Initialize the service."""
        if self._initialized:
            return
        
        # Simulate initialization
        await asyncio.sleep(0.5)
        
        # Load saved user workflows if they exist
        try:
            await self._load_user_workflows()
        except Exception as e:
            print(f"Error loading user workflows: {e}")
        
        self._initialized = True
        print("Mock workflow service initialized")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self._initialized:
            return
        
        # Simulate cleanup
        await asyncio.sleep(0.1)
        
        # Save user workflows
        try:
            await self._save_user_workflows()
        except Exception as e:
            print(f"Error saving user workflows: {e}")
        
        self._initialized = False
        print("Mock workflow service cleaned up")
    
    async def _load_user_workflows(self) -> None:
        """Load user workflows from file."""
        file_path = os.path.join(os.path.dirname(__file__), "user_workflows.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    self._user_workflows = json.load(f)
                logger.info(f"Loaded {len(self._user_workflows)} user workflows")
            except Exception as e:
                print(f"Failed to load user workflows: {e}")
        else:
            logger.info("No user workflows file found, starting with empty user workflows")
            self._user_workflows = {}
    
    async def _save_user_workflows(self) -> None:
        """Save user workflows to file."""
        file_path = os.path.join(os.path.dirname(__file__), "user_workflows.json")
        try:
            with open(file_path, 'w') as f:
                json.dump(self._user_workflows, f, indent=2)
            logger.info(f"Saved {len(self._user_workflows)} user workflows")
            return True
        except Exception as e:
            logger.error(f"Error saving user workflows: {str(e)}")
            return False
    
    async def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get available workflows."""
        if not self._initialized:
            await self.initialize()
        
        # Combine built-in and user-defined workflows
        all_workflows = []
        
        # Add built-in workflows
        for workflow_id, workflow in self._workflows.items():
            all_workflows.append({
                "id": workflow_id,
                "name": workflow["name"],
                "description": workflow["description"],
                "type": "built-in"
            })
        
        # Add user-defined workflows
        for workflow_id, workflow in self._user_workflows.items():
            all_workflows.append({
                "id": workflow_id,
                "name": workflow["name"],
                "description": workflow["description"],
                "type": "custom"
            })
        
        return all_workflows
    
    async def get_workflow_schema(self, workflow_id: str) -> Dict[str, Any]:
        """Get schema for a specific workflow."""
        if not self._initialized:
            await self.initialize()
        
        if workflow_id in self._workflows:
            return self._workflows[workflow_id]
        elif workflow_id in self._user_workflows:
            return self._user_workflows[workflow_id]
        else:
            raise ValueError(f"Workflow not found: {workflow_id}")
    
    async def get_workflow_components(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get available workflow components for custom workflow building."""
        if not self._initialized:
            await self.initialize()
        
        return self._workflow_components
    
    async def create_custom_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new custom workflow."""
        if not self._initialized:
            await self.initialize()
        
        # Validate required fields
        required_fields = ["name", "description", "schema", "components"]
        for field in required_fields:
            if field not in workflow_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Generate a unique ID if not provided
        workflow_id = workflow_data.get("id", f"custom-{str(uuid.uuid4())[:8]}")
        
        # Check if workflow ID already exists
        if workflow_id in self._workflows or workflow_id in self._user_workflows:
            raise ValueError(f"Workflow ID already exists: {workflow_id}")
        
        # Create workflow entry
        workflow = {
            "id": workflow_id,
            "name": workflow_data["name"],
            "description": workflow_data["description"],
            "schema": workflow_data["schema"],
            "components": workflow_data["components"],
            "created_at": datetime.now().isoformat()
        }
        
        # Save to user workflows
        self._user_workflows[workflow_id] = workflow
        await self._save_user_workflows()
        
        return {"status": "success", "workflow": workflow}
    
    async def update_custom_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing custom workflow."""
        if not self._initialized:
            await self.initialize()
        
        # Check if workflow exists and is a custom one
        if workflow_id not in self._user_workflows:
            raise ValueError(f"Custom workflow not found: {workflow_id}")
        
        # Update workflow fields
        workflow = self._user_workflows[workflow_id]
        if "name" in workflow_data:
            workflow["name"] = workflow_data["name"]
        if "description" in workflow_data:
            workflow["description"] = workflow_data["description"]
        if "schema" in workflow_data:
            workflow["schema"] = workflow_data["schema"]
        if "components" in workflow_data:
            workflow["components"] = workflow_data["components"]
        
        # Save workflows to disk
        await self._save_user_workflows()
        
        return {"status": "success", "workflow": workflow}
    
    async def delete_custom_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete a custom workflow."""
        if not self._initialized:
            await self.initialize()
        
        # Check if workflow exists and is a custom one
        if workflow_id not in self._user_workflows:
            raise ValueError(f"Custom workflow not found: {workflow_id}")
        
        # Delete workflow
        del self._user_workflows[workflow_id]
        
        # Save workflows to disk
        await self._save_user_workflows()
        
        return {"status": "success"}
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """Execute a workflow.
        
        Args:
            workflow_id: ID of the workflow to execute
            input_data: Workflow input data
            config: Optional configuration overrides
            
        Returns:
            Workflow execution result
        """
        # Initialize if not already done
        if not self._initialized:
            await self.initialize()
            
        # Check if workflow exists
        workflow = self._workflows.get(workflow_id) or self._user_workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
            
        # For custom workflows, use custom execution logic
        if workflow_id in self._user_workflows:
            return await self._execute_custom_workflow(workflow, input_data)
            
        # Start execution
        start_time = datetime.now()
        
        # Execute workflow based on ID
        if workflow_id == "api-governance":
            result_data = await self._execute_api_governance(input_data)
        elif workflow_id == "api-blueprint":
            result_data = await self._execute_api_blueprint(input_data)
        elif workflow_id == "api-mock":
            result_data = await self._execute_api_mock(input_data)
        elif workflow_id == "api-evolution":
            result_data = await self._execute_api_evolution(input_data)
        elif workflow_id == "simple-chat":
            result_data = await self._execute_simple_chat(input_data)
        else:
            raise ValueError(f"Workflow execution not implemented: {workflow_id}")
            
        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Format and return result
        return WorkflowResult(
            status="success",
            message=f"Workflow {workflow_id} executed successfully",
            timestamp=end_time.isoformat(),
            data={
                **result_data, 
                "execution_time": execution_time
            }
        )
    
    async def _execute_custom_workflow(
        self,
        workflow: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> WorkflowResult:
        """Execute a custom workflow."""
        workflow_id = workflow["id"]
        components = workflow.get("components", [])
        
        if not components:
            raise ValueError(f"Custom workflow {workflow_id} has no components defined")
        
        logger.info(f"Executing custom workflow: {workflow_id} with {len(components)} components")
        
        # Process input data validation
        schema = workflow.get("schema", {})
        if schema and schema.get("properties"):
            for field, field_schema in schema.get("properties", {}).items():
                if field in schema.get("required", []) and field not in input_data:
                    raise ValueError(f"Required input field '{field}' not provided")
        
        # Initialize workflow state with input data
        workflow_state = {
            "input": input_data,
            "intermediate": {},
            "output": {}
        }
        
        # Execute each component in order
        for i, component_config in enumerate(components):
            component_id = component_config.get("id")
            component_type = component_config.get("type")
            
            if not component_id or not component_type:
                raise ValueError(f"Component {i} in workflow {workflow_id} is missing id or type")
            
            logger.info(f"Processing component {i}: {component_type}/{component_id}")
            
            try:
                # Find component definition
                component_def = None
                for comp in self._workflow_components.get(component_type, []):
                    if comp.get("id") == component_id:
                        component_def = comp
                        break
                
                if not component_def:
                    raise ValueError(f"Component {component_id} of type {component_type} not found")
                
                # Process component based on type
                if component_type == "input":
                    # Input components are handled by input validation above
                    pass
                elif component_type == "processor":
                    # Process data through processor
                    input_mapping = component_config.get("input_mapping", {})
                    output_mapping = component_config.get("output_mapping", {})
                    
                    # Prepare processor inputs
                    processor_inputs = {}
                    for dest, source in input_mapping.items():
                        # Source format: "section.key" (e.g., "input.spec_url" or "intermediate.validation_result")
                        if "." in source:
                            section, key = source.split(".", 1)
                            if section in workflow_state and key in workflow_state[section]:
                                processor_inputs[dest] = workflow_state[section][key]
                    
                    # Mock processor execution
                    processor_outputs = await self._mock_processor_execution(component_id, processor_inputs)
                    
                    # Store processor outputs
                    for source, dest in output_mapping.items():
                        if "." in dest:
                            section, key = dest.split(".", 1)
                            if section in workflow_state and source in processor_outputs:
                                if section == "intermediate":
                                    workflow_state[section][key] = processor_outputs[source]
                
                elif component_type == "output":
                    # Format output
                    input_mapping = component_config.get("input_mapping", {})
                    output_format = component_id.split("-")[0]  # e.g., "json" from "json-output"
                    
                    # Prepare output content
                    output_content = {}
                    for dest, source in input_mapping.items():
                        if "." in source:
                            section, key = source.split(".", 1)
                            if section in workflow_state and key in workflow_state[section]:
                                output_content[dest] = workflow_state[section][key]
                    
                    # Format the output
                    formatted_output = self._format_output(output_format, output_content)
                    workflow_state["output"]["result"] = formatted_output
                    workflow_state["output"]["format"] = output_format
            
            except Exception as e:
                logger.error(f"Error processing component {component_id}: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Component {component_id} execution failed: {str(e)}",
                    "workflow_id": workflow_id
                }
        
        # Return the final result
        return {
            "status": "success",
            "result": workflow_state["output"].get("result", {}),
            "format": workflow_state["output"].get("format", "json"),
            "workflow_id": workflow_id,
            "execution_time": 1.23  # Mock execution time
        }
    
    async def _mock_processor_execution(self, processor_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execution of a processor component."""
        # Mock implementations for different processors
        if processor_id == "api-validator":
            return {
                "validation_result": {
                    "valid": True,
                    "errors": [],
                    "warnings": ["Path /users missing description"]
                }
            }
        elif processor_id == "api-linter":
            return {
                "lint_result": {
                    "score": 85,
                    "issues": [
                        {"level": "warning", "message": "Missing rate limiting headers"},
                        {"level": "info", "message": "Consider adding pagination"}
                    ]
                }
            }
        elif processor_id == "text-analyzer":
            text = inputs.get("text", "")
            return {
                "analysis_result": {
                    "sentiment": "positive" if "good" in text.lower() else "neutral",
                    "entities": ["API", "microservice"],
                    "keywords": ["REST", "API", "design"]
                }
            }
        elif processor_id == "url-fetcher":
            url = inputs.get("url", "")
            return {
                "content": f"Mocked content from {url}",
                "status_code": 200,
                "headers": {"Content-Type": "application/json"}
            }
        else:
            return {"result": "Mocked processor result"}
    
    def _format_output(self, format_type: str, content: Dict[str, Any]) -> str:
        """Format output content based on format type."""
        if format_type == "json":
            return json.dumps(content, indent=2)
        elif format_type == "html":
            html = "<html><body><h1>Workflow Result</h1><pre>"
            html += json.dumps(content, indent=2)
            html += "</pre></body></html>"
            return html
        elif format_type == "markdown":
            md = "# Workflow Result\n\n```json\n"
            md += json.dumps(content, indent=2)
            md += "\n```\n"
            return md
        else:
            return str(content)
    
    async def _execute_api_governance(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execution of API governance workflow."""
        spec_url = input_data.get("spec_url", "")
        output_format = input_data.get("output_format", "json")
        
        # Mock governance check results
        findings = [
            {
                "severity": "high",
                "category": "security",
                "message": "API does not use HTTPS",
                "path": "/",
                "recommendation": "Enforce HTTPS for all endpoints"
            },
            {
                "severity": "medium",
                "category": "standards",
                "message": "Non-standard error response format",
                "path": "/error",
                "recommendation": "Use RFC 7807 Problem Details format"
            },
            {
                "severity": "low",
                "category": "documentation",
                "message": "Missing example responses",
                "path": "/users",
                "recommendation": "Add example responses to improve documentation"
            }
        ]
        
        governance_result = {
            "spec_url": spec_url,
            "assessed_at": datetime.now().isoformat(),
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "by_severity": {
                    "critical": 0,
                    "high": 1,
                    "medium": 1,
                    "low": 1
                },
                "by_category": {
                    "security": 1,
                    "standards": 1,
                    "schema": 0,
                    "documentation": 1
                }
            },
            "pass_rate": 75.0
        }
        
        # Format result based on output format
        if output_format == "json":
            result = json.dumps(governance_result, indent=2)
        elif output_format == "markdown":
            result = "# API Governance Assessment\n\n"
            result += f"**API:** {spec_url}\n"
            result += f"**Assessed at:** {governance_result['assessed_at']}\n\n"
            result += "## Summary\n\n"
            result += f"- Pass Rate: {governance_result['pass_rate']}%\n"
            result += f"- Total Findings: {governance_result['summary']['total_findings']}\n\n"
            result += "## Findings\n\n"
            for finding in findings:
                result += f"### {finding['severity'].upper()}: {finding['message']}\n\n"
                result += f"- **Category:** {finding['category']}\n"
                result += f"- **Path:** {finding['path']}\n"
                result += f"- **Recommendation:** {finding['recommendation']}\n\n"
        elif output_format == "html":
            result = f"""
            <html>
            <head><title>API Governance Assessment</title></head>
            <body>
                <h1>API Governance Assessment</h1>
                <p><strong>API:</strong> {spec_url}</p>
                <p><strong>Assessed at:</strong> {governance_result['assessed_at']}</p>
                
                <h2>Summary</h2>
                <p><strong>Pass Rate:</strong> {governance_result['pass_rate']}%</p>
                <p><strong>Total Findings:</strong> {governance_result['summary']['total_findings']}</p>
                
                <h2>Findings</h2>
                <div class="findings">
            """
            for finding in findings:
                severity_color = {
                    "critical": "#ff0000",
                    "high": "#ff6600",
                    "medium": "#ffcc00",
                    "low": "#66cc00"
                }.get(finding['severity'], "#888888")
                result += f"""
                <div class="finding" style="border-left: 5px solid {severity_color}; padding: 10px; margin: 10px 0;">
                    <h3>{finding['severity'].upper()}: {finding['message']}</h3>
                    <p><strong>Category:</strong> {finding['category']}</p>
                    <p><strong>Path:</strong> {finding['path']}</p>
                    <p><strong>Recommendation:</strong> {finding['recommendation']}</p>
                </div>
                """
            result += """
                </div>
            </body>
            </html>
            """
        else:
            result = str(governance_result)
        
        return {
            "status": "success",
            "result": result,
            "format": output_format,
            "workflow_id": "api-governance",
            "execution_time": 1.2  # Mock execution time
        }
    
    async def _execute_api_blueprint(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execution of API blueprint workflow."""
        user_stories = input_data.get("user_stories", "")
        api_name = input_data.get("api_name", "Generated API")
        api_version = input_data.get("api_version", "1.0.0")
        
        # Mock API specification generation
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": api_name,
                "version": api_version,
                "description": "Generated from user stories"
            },
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List all users",
                        "description": "Returns a list of users",
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "name": {"type": "string"},
                                                    "email": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "summary": "Create a user",
                        "description": "Creates a new user record",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        },
                                        "required": ["name", "email"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "User created successfully"
                            },
                            "400": {
                                "description": "Invalid input"
                            }
                        }
                    }
                }
            }
        }
        
        # Return the generated specification
        return {
            "status": "success",
            "result": json.dumps(openapi_spec, indent=2),
            "format": "json",
            "workflow_id": "api-blueprint",
            "execution_time": 0.8  # Mock execution time
        }
    
    async def _execute_api_mock(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execution of API mock workflow."""
        spec_url = input_data.get("spec_url", "")
        port = input_data.get("port", 8080)
        
        # Mock mock server creation
        mock_server = {
            "status": "running",
            "url": f"http://localhost:{port}",
            "spec_url": spec_url,
            "routes": [
                {"method": "GET", "path": "/users", "status": 200},
                {"method": "POST", "path": "/users", "status": 201},
                {"method": "GET", "path": "/users/{userId}", "status": 200},
                {"method": "PUT", "path": "/users/{userId}", "status": 200},
                {"method": "DELETE", "path": "/users/{userId}", "status": 204}
            ]
        }
        
        # Return the mock server info
        return {
            "status": "success",
            "result": json.dumps(mock_server, indent=2),
            "format": "json",
            "workflow_id": "api-mock",
            "execution_time": 0.5  # Mock execution time
        }
    
    async def _execute_api_evolution(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execution of API evolution workflow."""
        old_spec_url = input_data.get("old_spec_url", "")
        new_spec_url = input_data.get("new_spec_url", "")
        check_breaking = input_data.get("check_breaking", True)
        
        # Mock API evolution analysis
        changes = [
            {
                "type": "breaking",
                "severity": "high",
                "path": "/users/{userId}",
                "description": "Changed required parameter from optional"
            },
            {
                "type": "non-breaking",
                "severity": "info",
                "path": "/users",
                "description": "Added new optional query parameter"
            },
            {
                "type": "non-breaking",
                "severity": "info",
                "path": "/products",
                "description": "Added new endpoint"
            }
        ]
        
        if not check_breaking:
            changes = [c for c in changes if c["type"] != "breaking"]
        
        evolution_result = {
            "old_spec_url": old_spec_url,
            "new_spec_url": new_spec_url,
            "changes": changes,
            "summary": {
                "total_changes": len(changes),
                "breaking_changes": sum(1 for c in changes if c["type"] == "breaking"),
                "non_breaking_changes": sum(1 for c in changes if c["type"] == "non-breaking")
            },
            "compatibility": "incompatible" if any(c["type"] == "breaking" for c in changes) else "compatible"
        }
        
        # Return the evolution analysis
        return {
            "status": "success",
            "result": json.dumps(evolution_result, indent=2),
            "format": "json",
            "workflow_id": "api-evolution",
            "execution_time": 0.7  # Mock execution time
        }
    
    async def _execute_simple_chat(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute simple chat workflow.
        
        Args:
            input_data: Workflow input data including message, model and system_prompt
            
        Returns:
            Workflow result with LLM response
        """
        try:
            # Extract input parameters
            message = input_data.get("message", "")
            model_choice = input_data.get("model", "gpt-4o-mini")
            system_prompt = input_data.get("system_prompt", "You are a helpful assistant.")
            conversation_id = input_data.get("conversation_id", "")
            
            # Log the received input
            logger.info(f"Chat request: model={model_choice}, system_prompt={system_prompt}")
            logger.info(f"User message: {message}")
            
            # Import PepperPy framework
            from pepperpy import PepperPy
            from pepperpy.llm.base import Message
            
            # Simply use PepperPy's configuration from config.yaml
            # This is much simpler than manually implementing OpenRouter API calls
            async with PepperPy() as pepper:
                # Create message format
                messages = [
                    Message("system", system_prompt),
                    Message("user", message)
                ]
                
                # Call LLM - the config.yaml already has OpenRouter as default provider
                response = await pepper.llm.chat(messages)
                
            return {
                "response": response,
                "model_used": model_choice,
                "provider": "openrouter",
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error in simple chat workflow: {str(e)}")
            return {
                "error": True,
                "message": f"Failed to generate response: {str(e)}",
                "timestamp": datetime.now().isoformat()
            } 