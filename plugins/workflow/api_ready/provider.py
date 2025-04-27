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
from typing import Any, Optional, TypedDict, Union, Literal
from enum import Enum
from datetime import datetime

from pepperpy.core.logging import get_logger
from pepperpy.workflow.base import WorkflowProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.workflow.base import WorkflowError

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
    added_endpoints: list[str]
    enhancement_summary: str
    spec_path: str


class ReadinessLevel(Enum):
    """Readiness levels for API evaluation."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReadinessCategory(Enum):
    """Categories for API readiness evaluation."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    OBSERVABILITY = "observability"
    DOCUMENTATION = "documentation"
    STANDARDS = "standards"


class ReadinessFinding:
    """Represents a finding during API readiness evaluation."""

    def __init__(
        self,
        title: str,
        description: str,
        level: ReadinessLevel,
        category: ReadinessCategory,
        path: Optional[str] = None,
        recommendation: Optional[str] = None,
    ):
        self.title = title
        self.description = description
        self.level = level
        self.category = category
        self.path = path
        self.recommendation = recommendation

    def to_dict(self) -> dict[str, Any]:
        """Convert finding to dictionary.

        Returns:
            Return description
        """
        return {
            "title": self.title,
            "description": self.description,
            "level": self.level.value,
            "category": self.category.value,
            "path": self.path,
            "recommendation": self.recommendation,
        }


class APIReadinessReport:
    """Represents a comprehensive API readiness evaluation report."""

    def __init__(
        self,
        api_name: str,
        api_version: str,
        api_spec: dict[str, Any],
        findings: list[ReadinessFinding],
    ):
        self.api_name = api_name
        self.api_version = api_version
        self.api_spec = api_spec
        self.findings = findings
        self.summary = self._generate_summary()

    def _generate_summary(self) -> dict[str, Any]:
        """Generate a summary of findings by level and category.

        Returns:
            Return description
        """
        total_findings = len(self.findings)
        findings_by_level = {level.value: 0 for level in ReadinessLevel}
        findings_by_category = {category.value: 0 for category in ReadinessCategory}

        for finding in self.findings:
            findings_by_level[finding.level.value] += 1
            findings_by_category[finding.category.value] += 1

        readiness_score = self._calculate_readiness_score()

        return {
            "total_findings": total_findings,
            "findings_by_level": findings_by_level,
            "findings_by_category": findings_by_category,
            "readiness_score": readiness_score,
        }

    def _calculate_readiness_score(self) -> int:
        """Calculate an overall readiness score (0-100).

        Returns:
            Return description
        """
        if not self.findings:
            return 100

        # Weight factors for different levels
        weights = {
            ReadinessLevel.CRITICAL.value: 10,
            ReadinessLevel.HIGH.value: 5,
            ReadinessLevel.MEDIUM.value: 2,
            ReadinessLevel.LOW.value: 1,
        }

        # Calculate weighted sum of findings
        weighted_sum = sum(
            weights[finding.level.value] for finding in self.findings
        )

        # Max possible score is 100
        # We deduct points based on findings
        max_deduction = 100
        score = max(0, 100 - min(weighted_sum, max_deduction))
        
        return score

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary.

        Returns:
            Return description
        """
        return {
            "api_name": self.api_name,
            "api_version": self.api_version,
            "summary": self.summary,
            "findings": [finding.to_dict() for finding in self.findings],
        }

    def to_markdown(self) -> str:
        """Convert report to markdown format.

        Returns:
            Return description
        """
        md = [
            f"# API Readiness Report: {self.api_name} v{self.api_version}",
            "",
            "## Summary",
            f"- **Readiness Score**: {self.summary['readiness_score']}/100",
            f"- **Total Findings**: {self.summary['total_findings']}",
            "",
            "### Findings by Severity",
        ]

        for level in ReadinessLevel:
            count = self.summary["findings_by_level"][level.value]
            md.append(f"- **{level.value.capitalize()}**: {count}")

        md.extend([
            "",
            "### Findings by Category",
        ])

        for category in ReadinessCategory:
            count = self.summary["findings_by_category"][category.value]
            md.append(f"- **{category.value.capitalize()}**: {count}")

        if self.findings:
            md.extend([
                "",
                "## Detailed Findings",
            ])

            for finding in self.findings:
                md.extend([
                    f"### {finding.title}",
                    f"- **Level**: {finding.level.value.capitalize()}",
                    f"- **Category**: {finding.category.value.capitalize()}",
                ])
                
                if finding.path:
                    md.append(f"- **Path**: `{finding.path}`")
                    
                md.extend([
                    "",
                    f"{finding.description}",
                    "",
                ])
                
                if finding.recommendation:
                    md.extend([
                        "**Recommendation:**",
                        "",
                        f"{finding.recommendation}",
                        "",
                    ])

        return "\n".join(md)


class APIReadyProvider(WorkflowProvider, ProviderPlugin):
    """Provider for evaluating APIs for production readiness.
    
    This workflow evaluates an existing API specification against industry best practices
    and provides a detailed report on its readiness for production deployment, focusing on
    security, performance, reliability, documentation, standards compliance, and observability.
    """
    
    # Type-annotated config attributes
    output_format: str
    min_readiness_score: int
    checks: dict[str, bool]
    default_scaffold_config: APIScaffoldConfig
    _initialized: bool = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    @initialized.setter
    def initialized(self, value: bool) -> None:
        self._initialized = value
    
    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
        """
        if self.initialized:
            return
        
        logger.info("Initializing API Ready workflow provider")
        
        # Initialize properties from config
        self.output_format = self.config.get("output_format", "json")
        self.min_readiness_score = self.config.get("min_readiness_score", 80)
        self.checks = self.config.get("checks", {
            "security": True,
            "performance": True,
            "reliability": True,
            "documentation": True,
            "standards": True,
            "observability": True
        })
        
        # For API enhancement
        self.default_scaffold_config = APIScaffoldConfig(
            agent_discovery=True,
            auth_mechanism="api_key",
            observability=True,
            rate_limiting=True,
            documentation=True
        )
        
        self._initialized = True
        logger.info("API Ready workflow provider initialized")
    
    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
        """
        if not self.initialized:
            return
        
        logger.info("Cleaning up API Ready workflow provider")
        self._initialized = False
    
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the API Ready workflow.
        
        Args:
            input_data: dict containing:
                - spec_path: Path to the API spec file
                - mode: "evaluate" (default) or "enhance"
                - enhancement_options: Options for API enhancement (if mode is "enhance")
                - output_dir: Directory to save enhanced spec (if mode is "enhance")
        
        Returns:
            Results of the evaluation or enhancement process
        """
        try:
            if not self.initialized:
                await self.initialize()
            
            # Extract and validate input
            spec_path = input_data.get("spec_path")
            if not spec_path or not os.path.exists(spec_path):
                return {"error": "Missing or invalid API specification path"}
            
            # Load the API spec
            spec_content = await self._load_api_spec(spec_path)
            
            # Determine mode: evaluate or enhance
            mode = input_data.get("mode", "evaluate")
            
            if mode == "evaluate":
                # Evaluate API readiness
                findings = await self._evaluate_api_readiness(
                    spec_content,
                    enabled_checks=self.checks
                )
                
                # Extract API metadata
                api_name, api_version = await self._extract_api_metadata(spec_content)
                
                # Generate report
                report = APIReadinessReport(
                    api_name=api_name,
                    api_version=api_version,
                    api_spec=spec_content,
                    findings=findings
                )
                
                # Check if API meets minimum readiness score
                meets_minimum = report.summary["readiness_score"] >= self.min_readiness_score
                
                # Return appropriate format
                if self.output_format == "markdown":
                    return {
                        "status": "success",
                        "result": {
                            "report": report.to_markdown(),
                            "readiness_score": report.summary["readiness_score"],
                            "meets_minimum": meets_minimum
                        }
                    }
                else:
                    return {
                        "status": "success",
                        "result": {
                            "report": report.to_dict(),
                            "readiness_score": report.summary["readiness_score"],
                            "meets_minimum": meets_minimum
                        }
                    }
                
            elif mode == "enhance":
                enhancement_options = input_data.get("enhancement_options", {})
                output_dir = input_data.get("output_dir", os.path.dirname(spec_path))
                
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
            else:
                return {
                    "status": "error",
                    "error": f"Invalid mode: {mode}. Must be 'evaluate' or 'enhance'."
                }
            
        except Exception as e:
            logger.error(f"Error executing API Ready workflow: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _load_api_spec(self, spec_path: str) -> dict[str, Any]:
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
                               spec: dict[str, Any], 
                               scaffold_config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Enhance the API specification with agent-ready features.
        
        Args:
            spec: Original API specification
            scaffold_config: Enhancement configuration
            
        Returns:
            tuple of (enhanced spec, enhancement details)
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
                                 spec: dict[str, Any], 
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
    
    async def _extract_api_metadata(self, spec: dict[str, Any]) -> tuple[str, str]:
        """Extract API name and version from specification.
        
        Args:
            spec: API specification
            
        Returns:
            tuple of (api_name, api_version)
        """
        api_name = "Unknown API"
        api_version = "1.0.0"
        
        # Extract from info section if available
        if "info" in spec:
            if "title" in spec["info"]:
                api_name = spec["info"]["title"]
            
            if "version" in spec["info"]:
                api_version = spec["info"]["version"]
        
        return api_name, api_version
    
    async def _evaluate_api_readiness(self, 
                                    spec: dict[str, Any],
                                    enabled_checks: dict[str, bool]) -> list[ReadinessFinding]:
        """Evaluate API readiness against best practices.
        
        Args:
            spec: API specification
            enabled_checks: Dictionary of enabled check categories
            
        Returns:
            list of readiness findings
        """
        findings = []
        
        # Security checks
        if enabled_checks.get("security", True):
            findings.extend(await self._evaluate_security(spec))
        
        # Performance checks
        if enabled_checks.get("performance", True):
            findings.extend(await self._evaluate_performance(spec))
        
        # Reliability checks
        if enabled_checks.get("reliability", True):
            findings.extend(await self._evaluate_reliability(spec))
        
        # Documentation checks
        if enabled_checks.get("documentation", True):
            findings.extend(await self._evaluate_documentation(spec))
        
        # Standards compliance checks
        if enabled_checks.get("standards", True):
            findings.extend(await self._evaluate_standards(spec))
        
        # Observability checks
        if enabled_checks.get("observability", True):
            findings.extend(await self._evaluate_observability(spec))
        
        return findings
    
    async def _evaluate_security(self, spec: dict[str, Any]) -> list[ReadinessFinding]:
        """Evaluate API security readiness.
        
        Args:
            spec: API specification
            
        Returns:
            list of security findings
        """
        findings = []
        
        # Check if HTTPS is enforced
        if "schemes" in spec and ("http" in spec["schemes"] and "https" not in spec["schemes"]):
            findings.append(ReadinessFinding(
                title="HTTP Used Without HTTPS",
                description="The API allows HTTP connections without requiring HTTPS, which exposes data to potential interception.",
                level=ReadinessLevel.CRITICAL,
                category=ReadinessCategory.SECURITY,
                recommendation="Add HTTPS support and consider disabling HTTP for production environments."
            ))
        elif "schemes" not in spec:
            findings.append(ReadinessFinding(
                title="No Transport Protocol Defined",
                description="The API specification does not define transport protocols (HTTP/HTTPS), which may lead to insecure implementations.",
                level=ReadinessLevel.HIGH,
                category=ReadinessCategory.SECURITY,
                recommendation="Explicitly define 'https' as the transport protocol in the API specification."
            ))
        
        # Check for authentication
        has_security_requirement = False
        if "security" in spec and spec["security"]:
            has_security_requirement = True
        
        if not has_security_requirement:
            # Check if there are any security definitions that aren't used
            if "components" in spec and "securitySchemes" in spec["components"] and spec["components"]["securitySchemes"]:
                findings.append(ReadinessFinding(
                    title="Security Schemes Defined But Not Required",
                    description="Security schemes are defined but not required globally or on any endpoints.",
                    level=ReadinessLevel.HIGH,
                    category=ReadinessCategory.SECURITY,
                    recommendation="Apply security requirements either globally or on specific endpoints."
                ))
            else:
                findings.append(ReadinessFinding(
                    title="No Authentication Mechanism",
                    description="The API does not define any authentication mechanism, allowing anonymous access to all endpoints.",
                    level=ReadinessLevel.CRITICAL,
                    category=ReadinessCategory.SECURITY,
                    recommendation="Implement an appropriate authentication mechanism such as API keys, OAuth, or JWT."
                ))
        
        # Check for rate limiting
        has_rate_limiting = False
        
        # Check standard extensions
        if "x-rate-limit" in spec or "x-ratelimit" in spec:
            has_rate_limiting = True
        
        # Check for rate limit headers in responses
        for path in spec.get("paths", {}):
            for method in spec["paths"][path]:
                if method not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                for status_code in spec["paths"][path][method].get("responses", {}):
                    headers = spec["paths"][path][method]["responses"][status_code].get("headers", {})
                    if any(header.lower().startswith(("x-rate-limit", "x-ratelimit")) for header in headers):
                        has_rate_limiting = True
                        break
        
        if not has_rate_limiting:
            findings.append(ReadinessFinding(
                title="No Rate Limiting",
                description="The API does not implement rate limiting, which may expose it to abuse and denial of service attacks.",
                level=ReadinessLevel.HIGH,
                category=ReadinessCategory.SECURITY,
                recommendation="Implement rate limiting and expose rate limit headers in API responses."
            ))
        
        return findings
    
    async def _evaluate_performance(self, spec: dict[str, Any]) -> list[ReadinessFinding]:
        """Evaluate API performance readiness.
        
        Args:
            spec: API specification
            
        Returns:
            list of performance findings
        """
        findings = []
        
        # Check for pagination in collection endpoints
        for path, path_item in spec.get("paths", {}).items():
            for method, operation in path_item.items():
                if method not in ["get"]:
                    continue
                
                # Check if this looks like a collection endpoint
                is_collection = False
                if path.endswith("s") and not path.endswith("/{id}"):
                    is_collection = True
                
                # Check description or summary for collection indicators
                if operation.get("description", "").lower().find("list") >= 0 or operation.get("summary", "").lower().find("list") >= 0:
                    is_collection = True
                
                if is_collection:
                    # Check for pagination parameters
                    has_pagination = False
                    pagination_params = ["page", "limit", "offset", "size", "per_page"]
                    
                    for param in operation.get("parameters", []):
                        param_name = param.get("name", "").lower()
                        if any(pagination_term in param_name for pagination_term in pagination_params):
                            has_pagination = True
                            break
                    
                    if not has_pagination:
                        findings.append(ReadinessFinding(
                            title="Collection Endpoint Without Pagination",
                            description=f"The collection endpoint {path} doesn't support pagination, which may lead to performance issues with large datasets.",
                            level=ReadinessLevel.MEDIUM,
                            category=ReadinessCategory.PERFORMANCE,
                            path=path,
                            recommendation="Add pagination parameters such as 'page' and 'limit' or 'offset' and 'limit'."
                        ))
        
        return findings
    
    async def _evaluate_reliability(self, spec: dict[str, Any]) -> list[ReadinessFinding]:
        """Evaluate API reliability readiness.
        
        Args:
            spec: API specification
            
        Returns:
            list of reliability findings
        """
        findings = []
        
        # Check for error responses
        for path, path_item in spec.get("paths", {}).items():
            for method, operation in path_item.items():
                if method not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                # Check if common error status codes are defined
                responses = operation.get("responses", {})
                error_codes = ["400", "401", "403", "404", "500"]
                defined_error_codes = [code for code in error_codes if code in responses]
                
                if len(defined_error_codes) < 3:  # Arbitrary threshold
                    findings.append(ReadinessFinding(
                        title="Insufficient Error Responses",
                        description=f"The {method.upper()} endpoint for {path} doesn't define enough error responses ({', '.join(defined_error_codes)}).",
                        level=ReadinessLevel.MEDIUM,
                        category=ReadinessCategory.RELIABILITY,
                        path=path,
                        recommendation="Define common error responses (400, 401, 403, 404, 500) with appropriate schemas."
                    ))
        
        return findings
    
    async def _evaluate_documentation(self, spec: dict[str, Any]) -> list[ReadinessFinding]:
        """Evaluate API documentation readiness.
        
        Args:
            spec: API specification
            
        Returns:
            list of documentation findings
        """
        findings = []
        
        # Check if API info section is complete
        if "info" in spec:
            info = spec["info"]
            
            if not info.get("description") or len(info.get("description", "")) < 20:
                findings.append(ReadinessFinding(
                    title="Insufficient API Description",
                    description="The API description is missing or too brief, which makes it difficult for consumers to understand its purpose.",
                    level=ReadinessLevel.MEDIUM,
                    category=ReadinessCategory.DOCUMENTATION,
                    recommendation="Add a comprehensive description that explains the API's purpose, audience, and key features."
                ))
            
            if not info.get("contact"):
                findings.append(ReadinessFinding(
                    title="Missing Contact Information",
                    description="The API specification doesn't include contact information for support or questions.",
                    level=ReadinessLevel.LOW,
                    category=ReadinessCategory.DOCUMENTATION,
                    recommendation="Add contact information including at least an email address and optionally a name and URL."
                ))
        
        # Check for undocumented endpoints or parameters
        for path, path_item in spec.get("paths", {}).items():
            for method, operation in path_item.items():
                if method not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                # Check operation summary and description
                if not operation.get("summary") and not operation.get("description"):
                    findings.append(ReadinessFinding(
                        title="Undocumented Endpoint",
                        description=f"The {method.upper()} endpoint for {path} lacks both summary and description.",
                        level=ReadinessLevel.MEDIUM,
                        category=ReadinessCategory.DOCUMENTATION,
                        path=path,
                        recommendation="Add a concise summary and detailed description for the endpoint."
                    ))
                
                # Check parameter descriptions
                for param in operation.get("parameters", []):
                    if not param.get("description"):
                        findings.append(ReadinessFinding(
                            title="Undocumented Parameter",
                            description=f"Parameter '{param.get('name')}' in {method.upper()} {path} has no description.",
                            level=ReadinessLevel.LOW,
                            category=ReadinessCategory.DOCUMENTATION,
                            path=path,
                            recommendation=f"Add a description for the '{param.get('name')}' parameter."
                        ))
        
        return findings
    
    async def _evaluate_standards(self, spec: dict[str, Any]) -> list[ReadinessFinding]:
        """Evaluate API standards compliance.
        
        Args:
            spec: API specification
            
        Returns:
            list of standards findings
        """
        findings = []
        
        # Check for OpenAPI version
        openapi_version = spec.get("openapi", spec.get("swagger", ""))
        if not openapi_version:
            findings.append(ReadinessFinding(
                title="Missing OpenAPI Version",
                description="The API specification doesn't declare an OpenAPI or Swagger version.",
                level=ReadinessLevel.MEDIUM,
                category=ReadinessCategory.STANDARDS,
                recommendation="Add an 'openapi' field with the appropriate version (e.g., '3.0.0')."
            ))
        elif openapi_version.startswith("2."):
            findings.append(ReadinessFinding(
                title="Outdated OpenAPI Version",
                description=f"The API uses OpenAPI/Swagger version {openapi_version}, which is outdated.",
                level=ReadinessLevel.LOW,
                category=ReadinessCategory.STANDARDS,
                recommendation="Consider upgrading to OpenAPI 3.x for access to newer features and better tooling support."
            ))
        
        # Check URL pattern consistency
        url_styles = {"kebab-case": 0, "snake_case": 0, "camelCase": 0}
        for path in spec.get("paths", {}):
            parts = [p for p in path.split("/") if p and not p.startswith("{")]
            for part in parts:
                if "-" in part:
                    url_styles["kebab-case"] += 1
                elif "_" in part:
                    url_styles["snake_case"] += 1
                elif part != part.lower() and part[0].islower():
                    url_styles["camelCase"] += 1
        
        # Determine dominant style
        dominant_style = max(url_styles.items(), key=lambda x: x[1])[0] if any(url_styles.values()) else None
        inconsistent = sum(1 for count in url_styles.values() if count > 0) > 1
        
        if inconsistent:
            findings.append(ReadinessFinding(
                title="Inconsistent URL Naming Conventions",
                description="The API uses inconsistent URL naming conventions, mixing different styles.",
                level=ReadinessLevel.MEDIUM,
                category=ReadinessCategory.STANDARDS,
                recommendation=f"Standardize on a single URL naming convention, preferably {dominant_style if dominant_style else 'kebab-case'}."
            ))
        
        return findings
    
    async def _evaluate_observability(self, spec: dict[str, Any]) -> list[ReadinessFinding]:
        """Evaluate API observability readiness.
        
        Args:
            spec: API specification
            
        Returns:
            list of observability findings
        """
        findings = []
        
        # Check for health check endpoint
        has_health_endpoint = False
        for path in spec.get("paths", {}):
            if path.lower().find("health") >= 0:
                has_health_endpoint = True
                break
        
        if not has_health_endpoint:
            findings.append(ReadinessFinding(
                title="Missing Health Check Endpoint",
                description="The API doesn't provide a health check endpoint, which is essential for monitoring and orchestration.",
                level=ReadinessLevel.MEDIUM,
                category=ReadinessCategory.OBSERVABILITY,
                recommendation="Add a '/health' endpoint that returns the operational status of the API and its dependencies."
            ))
        
        # Check for metrics or monitoring endpoint
        has_metrics_endpoint = False
        for path in spec.get("paths", {}):
            if path.lower().find("metric") >= 0 or path.lower().find("monitor") >= 0:
                has_metrics_endpoint = True
                break
        
        if not has_metrics_endpoint:
            findings.append(ReadinessFinding(
                title="Missing Metrics Endpoint",
                description="The API doesn't provide a metrics endpoint for monitoring performance and usage.",
                level=ReadinessLevel.MEDIUM,
                category=ReadinessCategory.OBSERVABILITY,
                recommendation="Add a '/metrics' endpoint that returns operational metrics in a standard format (e.g., Prometheus)."
            ))
        
        # Check for correlation ID/request ID
        has_correlation_id = False
        for path, path_item in spec.get("paths", {}).items():
            for method, operation in path_item.items():
                if method not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                for status_code in operation.get("responses", {}):
                    headers = operation["responses"][status_code].get("headers", {})
                    correlation_headers = ["x-correlation-id", "x-request-id", "request-id"]
                    if any(header.lower() in correlation_headers for header in headers):
                        has_correlation_id = True
                        break
        
        if not has_correlation_id:
            findings.append(ReadinessFinding(
                title="Missing Correlation ID",
                description="The API doesn't use correlation IDs, which makes it difficult to trace requests across distributed systems.",
                level=ReadinessLevel.LOW,
                category=ReadinessCategory.OBSERVABILITY,
                recommendation="Add a 'X-Correlation-ID' or 'X-Request-ID' header to all responses for request tracing."
            ))
        
        return findings 