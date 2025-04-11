"""
Validation module for AI Gateway multiport functionality.

This module provides tools to validate the configuration and proper functioning
of multiport setup and advanced features.
"""

import asyncio
import logging
import sys
from dataclasses import dataclass
from typing import Any

import aiohttp
import yaml

# Configure logging
logger = logging.getLogger("ai_gateway.validation")


@dataclass
class ValidationError:
    """Validation error details."""

    path: str
    message: str
    severity: str = "error"  # error, warning


@dataclass
class ValidationResult:
    """Result of workflow validation."""

    is_valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError]


class MultiportValidator:
    """Validator for multiport configurations and functionality."""

    def __init__(self, config_path: str | None = None):
        """Initialize validator with configuration.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = {}
        self.services = []
        self.validation_results = {}
        self.success_count = 0
        self.failure_count = 0
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []

    async def load_config(self) -> dict[str, Any]:
        """Load configuration from file.

        Returns:
            Loaded configuration
        """
        try:
            if not self.config_path:
                logger.error("No configuration path provided")
                return {}

            with open(self.config_path) as f:
                self.config = yaml.safe_load(f)

            # Extract services information
            multiport_config = self.config.get("multiport", {})
            self.services = multiport_config.get("services", [])

            if not self.services:
                logger.warning("No multiport services found in configuration")

            return self.config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}

    async def validate_configuration(self) -> dict[str, Any]:
        """Validate configuration structure and values.

        Returns:
            Validation results
        """
        logger.info("Validating configuration structure...")

        results = {"status": "success", "errors": [], "warnings": []}

        # Check if multiport is enabled
        if not self.config.get("multiport", {}).get("enabled", False):
            results["warnings"].append("Multiport is not enabled in configuration")

        # Check if services are defined
        if not self.services:
            results["errors"].append("No services defined in multiport configuration")
            results["status"] = "error"

        # Validate each service
        service_ports = set()
        for service in self.services:
            # Check required fields
            if "name" not in service:
                results["errors"].append("Service missing required field 'name'")
                results["status"] = "error"

            if "port" not in service:
                results["errors"].append(
                    f"Service {service.get('name', 'unnamed')} missing required field 'port'"
                )
                results["status"] = "error"

            if "type" not in service:
                results["warnings"].append(
                    f"Service {service.get('name', 'unnamed')} missing field 'type', defaulting to 'api'"
                )

            # Check for duplicate ports
            port = service.get("port")
            if port in service_ports:
                results["errors"].append(
                    f"Duplicate port {port} in service configuration"
                )
                results["status"] = "error"
            else:
                service_ports.add(port)

            # Check service type
            service_type = service.get("type", "api")
            if service_type not in ["api", "web", "metrics", "admin"]:
                results["warnings"].append(
                    f"Unknown service type '{service_type}' for service {service.get('name', 'unnamed')}"
                )

        # Validate advanced features configuration
        await self._validate_rag_config(results)
        await self._validate_function_calling_config(results)
        await self._validate_federation_config(results)
        await self._validate_guardrails_config(results)
        await self._validate_caching_config(results)
        await self._validate_compliance_config(results)

        self.validation_results["configuration"] = results
        return results

    async def _validate_rag_config(self, results: dict[str, Any]) -> None:
        """Validate RAG configuration.

        Args:
            results: Validation results dictionary to update
        """
        rag_config = self.config.get("rag", {})
        if not rag_config.get("enabled", False):
            return

        # Check vector stores
        vector_stores = rag_config.get("vector_stores", {})
        if not vector_stores:
            results["warnings"].append(
                "RAG is enabled but no vector stores are configured"
            )

        # Check embeddings
        embeddings = rag_config.get("embeddings", {})
        if not embeddings:
            results["errors"].append(
                "RAG is enabled but no embeddings provider is configured"
            )
            results["status"] = "error"

    async def _validate_function_calling_config(self, results: dict[str, Any]) -> None:
        """Validate function calling configuration.

        Args:
            results: Validation results dictionary to update
        """
        function_calling_config = self.config.get("function_calling", {})
        if not function_calling_config.get("enabled", False):
            return

        # Check built-in functions
        built_in_functions = function_calling_config.get("built_in_functions", {})
        if not built_in_functions:
            results["warnings"].append(
                "Function calling is enabled but no built-in functions are configured"
            )

    async def _validate_federation_config(self, results: dict[str, Any]) -> None:
        """Validate federation configuration.

        Args:
            results: Validation results dictionary to update
        """
        federation_config = self.config.get("federation", {})
        if not federation_config.get("enabled", False):
            return

        # Check strategy
        strategy = federation_config.get("strategy")
        if strategy not in ["cost_based", "performance_based", "availability_based"]:
            results["warnings"].append(f"Unknown federation strategy '{strategy}'")

        # Check model groups
        model_groups = federation_config.get("model_groups", {})
        if not model_groups:
            results["warnings"].append(
                "Federation is enabled but no model groups are configured"
            )

        # Check defined models exist in model configuration
        models_config = self.config.get("models", {})
        for group_name, models in model_groups.items():
            for model in models:
                if model not in models_config:
                    results["warnings"].append(
                        f"Model '{model}' in group '{group_name}' is not defined in models configuration"
                    )

    async def _validate_guardrails_config(self, results: dict[str, Any]) -> None:
        """Validate guardrails configuration.

        Args:
            results: Validation results dictionary to update
        """
        guardrails_config = self.config.get("guardrails", {})
        if not guardrails_config.get("enabled", False):
            return

        # Check content filtering
        content_filtering = guardrails_config.get("content_filtering", {})
        if content_filtering.get("enabled", False):
            level = content_filtering.get("level")
            if level not in ["low", "medium", "high"]:
                results["warnings"].append(f"Unknown content filtering level '{level}'")

        # Check prompt injection
        prompt_injection = guardrails_config.get("prompt_injection", {})
        if prompt_injection.get("enabled", False):
            action = prompt_injection.get("action")
            if action not in ["block", "warn", "log"]:
                results["warnings"].append(
                    f"Unknown prompt injection action '{action}'"
                )

    async def _validate_caching_config(self, results: dict[str, Any]) -> None:
        """Validate caching configuration.

        Args:
            results: Validation results dictionary to update
        """
        caching_config = self.config.get("caching", {})
        if not caching_config.get("enabled", False):
            return

        # Check backend
        backend = caching_config.get("backend")
        if backend not in ["memory", "redis", "memcached"]:
            results["warnings"].append(f"Unknown caching backend '{backend}'")

        # Check Redis configuration if Redis backend
        if backend == "redis":
            redis_config = caching_config.get("redis", {})
            if not redis_config:
                results["warnings"].append(
                    "Redis backend configured but no Redis configuration provided"
                )

    async def _validate_compliance_config(self, results: dict[str, Any]) -> None:
        """Validate compliance configuration.

        Args:
            results: Validation results dictionary to update
        """
        compliance_config = self.config.get("compliance", {})
        if not compliance_config.get("enabled", False):
            return

        # Check audit logging
        audit_logging = compliance_config.get("audit_logging", {})
        if audit_logging.get("enabled", False):
            storage = audit_logging.get("storage", {})
            if not storage:
                results["warnings"].append(
                    "Audit logging enabled but no storage configuration provided"
                )

    async def validate_connectivity(self) -> dict[str, Any]:
        """Validate connectivity to all configured service endpoints.

        Returns:
            Connectivity validation results
        """
        logger.info("Validating connectivity to services...")

        results = {
            "status": "success",
            "errors": [],
            "warnings": [],
            "service_results": {},
        }

        if not self.services:
            results["errors"].append("No services configured to validate")
            results["status"] = "error"
            self.validation_results["connectivity"] = results
            return results

        # Check connectivity to each service
        async with aiohttp.ClientSession() as session:
            connectivity_tasks = []

            for service in self.services:
                name = service.get("name", "unnamed")
                host = service.get("host", "localhost")
                port = service.get("port")

                if not port:
                    results["errors"].append(
                        f"Service {name} missing port configuration"
                    )
                    results["status"] = "error"
                    continue

                url = f"http://{host}:{port}/health"
                connectivity_tasks.append(
                    self._check_service_connectivity(session, name, url)
                )

            # Wait for all connectivity checks to complete
            service_results = await asyncio.gather(
                *connectivity_tasks, return_exceptions=True
            )

            # Process results
            for name, status, message in service_results:
                results["service_results"][name] = {
                    "status": status,
                    "message": message,
                }

                if status == "error":
                    results["errors"].append(f"Service {name}: {message}")
                    results["status"] = "error"

        self.validation_results["connectivity"] = results
        return results

    async def _check_service_connectivity(
        self, session: aiohttp.ClientSession, name: str, url: str
    ) -> tuple[str, str, str]:
        """Check connectivity to a service.

        Args:
            session: HTTP session
            name: Service name
            url: Service URL to check

        Returns:
            Tuple of (name, status, message)
        """
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        return (
                            name,
                            "success",
                            f"Connected successfully: {data.get('status', 'unknown')}",
                        )
                    except:
                        return (
                            name,
                            "success",
                            "Connected successfully but response not JSON",
                        )
                else:
                    return name, "error", f"Received status code {response.status}"
        except TimeoutError:
            return name, "error", "Connection timed out"
        except Exception as e:
            return name, "error", f"Connection error: {e!s}"

    async def validate_features(self) -> dict[str, Any]:
        """Validate advanced features functionality.

        Returns:
            Feature validation results
        """
        logger.info("Validating advanced features functionality...")

        results = {
            "status": "success",
            "errors": [],
            "warnings": [],
            "feature_results": {},
        }

        # Validate RAG functionality
        if self.config.get("rag", {}).get("enabled", False):
            rag_result = await self._validate_rag_functionality()
            results["feature_results"]["rag"] = rag_result
            if rag_result["status"] == "error":
                results["errors"].append(
                    f"RAG validation failed: {rag_result.get('message')}"
                )
                results["status"] = "error"

        # Validate function calling functionality
        if self.config.get("function_calling", {}).get("enabled", False):
            function_result = await self._validate_function_calling_functionality()
            results["feature_results"]["function_calling"] = function_result
            if function_result["status"] == "error":
                results["errors"].append(
                    f"Function calling validation failed: {function_result.get('message')}"
                )
                results["status"] = "error"

        # Validate federation functionality
        if self.config.get("federation", {}).get("enabled", False):
            federation_result = await self._validate_federation_functionality()
            results["feature_results"]["federation"] = federation_result
            if federation_result["status"] == "error":
                results["errors"].append(
                    f"Federation validation failed: {federation_result.get('message')}"
                )
                results["status"] = "error"

        # Additional feature validations can be added here

        self.validation_results["features"] = results
        return results

    async def _validate_rag_functionality(self) -> dict[str, Any]:
        """Validate RAG functionality.

        Returns:
            RAG validation results
        """
        # Find API service
        api_service = next(
            (s for s in self.services if s.get("type", "api") == "api"), None
        )
        if not api_service:
            return {
                "status": "error",
                "message": "No API service found to validate RAG functionality",
            }

        host = api_service.get("host", "localhost")
        port = api_service.get("port")

        if not port:
            return {
                "status": "error",
                "message": "API service missing port configuration",
            }

        # Test RAG query endpoint
        url = f"http://{host}:{port}/v1/rag/query"

        try:
            async with aiohttp.ClientSession() as session:
                test_query = {"query": "What is AI Gateway?", "top_k": 3}

                timeout = aiohttp.ClientTimeout(total=10)
                async with session.post(
                    url, json=test_query, timeout=timeout
                ) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return {
                                "status": "success",
                                "message": "RAG functionality working",
                                "details": data,
                            }
                        except:
                            return {
                                "status": "warning",
                                "message": "RAG endpoint returned non-JSON response",
                            }
                    elif response.status == 404:
                        return {
                            "status": "warning",
                            "message": "RAG endpoint not found",
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"RAG endpoint returned status code {response.status}",
                        }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error testing RAG functionality: {e!s}",
            }

    async def _validate_function_calling_functionality(self) -> dict[str, Any]:
        """Validate function calling functionality.

        Returns:
            Function calling validation results
        """
        # Find API service
        api_service = next(
            (s for s in self.services if s.get("type", "api") == "api"), None
        )
        if not api_service:
            return {
                "status": "error",
                "message": "No API service found to validate function calling functionality",
            }

        host = api_service.get("host", "localhost")
        port = api_service.get("port")

        if not port:
            return {
                "status": "error",
                "message": "API service missing port configuration",
            }

        # Test function calling endpoint
        url = f"http://{host}:{port}/v1/functions/call"

        try:
            async with aiohttp.ClientSession() as session:
                test_request = {
                    "function": "calculator",
                    "parameters": {"expression": "2+2"},
                }

                timeout = aiohttp.ClientTimeout(total=10)
                async with session.post(
                    url, json=test_request, timeout=timeout
                ) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return {
                                "status": "success",
                                "message": "Function calling functionality working",
                                "details": data,
                            }
                        except:
                            return {
                                "status": "warning",
                                "message": "Function calling endpoint returned non-JSON response",
                            }
                    elif response.status == 404:
                        return {
                            "status": "warning",
                            "message": "Function calling endpoint not found",
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Function calling endpoint returned status code {response.status}",
                        }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error testing function calling functionality: {e!s}",
            }

    async def _validate_federation_functionality(self) -> dict[str, Any]:
        """Validate federation functionality.

        Returns:
            Federation validation results
        """
        # For federation, we check if multiple model providers can be accessed
        models_config = self.config.get("models", {})
        federation_config = self.config.get("federation", {})
        model_groups = federation_config.get("model_groups", {})

        if not model_groups:
            return {
                "status": "warning",
                "message": "No model groups configured for federation",
            }

        # Find API service
        api_service = next(
            (s for s in self.services if s.get("type", "api") == "api"), None
        )
        if not api_service:
            return {
                "status": "error",
                "message": "No API service found to validate federation functionality",
            }

        host = api_service.get("host", "localhost")
        port = api_service.get("port")

        if not port:
            return {
                "status": "error",
                "message": "API service missing port configuration",
            }

        # Test model listing endpoint
        url = f"http://{host}:{port}/v1/models"

        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            models = data.get("models", [])

                            # Check if models from different groups are available
                            available_models = {model.get("id") for model in models}
                            found_groups = []

                            for group_name, group_models in model_groups.items():
                                if any(
                                    model in available_models for model in group_models
                                ):
                                    found_groups.append(group_name)

                            if len(found_groups) > 1:
                                return {
                                    "status": "success",
                                    "message": f"Federation functional with groups: {', '.join(found_groups)}",
                                    "details": {
                                        "available_models": list(available_models),
                                        "found_groups": found_groups,
                                    },
                                }
                            else:
                                return {
                                    "status": "warning",
                                    "message": f"Only found models from group: {found_groups[0] if found_groups else 'none'}",
                                    "details": {
                                        "available_models": list(available_models),
                                        "found_groups": found_groups,
                                    },
                                }
                        except:
                            return {
                                "status": "warning",
                                "message": "Models endpoint returned non-JSON response",
                            }
                    else:
                        return {
                            "status": "error",
                            "message": f"Models endpoint returned status code {response.status}",
                        }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error testing federation functionality: {e!s}",
            }

    async def run_validation(self) -> dict[str, Any]:
        """Run all validations.

        Returns:
            Complete validation results
        """
        logger.info(f"Starting validation for configuration: {self.config_path}")

        # Load configuration
        await self.load_config()

        # Validate configuration
        config_results = await self.validate_configuration()
        logger.info(f"Configuration validation: {config_results['status']}")

        # Validate connectivity
        connectivity_results = await self.validate_connectivity()
        logger.info(f"Connectivity validation: {connectivity_results['status']}")

        # Validate features
        feature_results = await self.validate_features()
        logger.info(f"Feature validation: {feature_results['status']}")

        # Compile overall results
        overall_status = "success"
        if (
            config_results["status"] == "error"
            or connectivity_results["status"] == "error"
            or feature_results["status"] == "error"
        ):
            overall_status = "error"

        self.validation_results["overall_status"] = overall_status
        logger.info(f"Overall validation status: {overall_status}")

        return self.validation_results

    def print_validation_report(self) -> None:
        """Print validation report to console."""
        if not self.validation_results:
            print("No validation results available. Run validation first.")
            return

        # Print overall status
        overall_status = self.validation_results.get("overall_status", "unknown")
        status_color = "\033[32m" if overall_status == "success" else "\033[31m"
        print(
            f"\n{status_color}=== AI Gateway Multiport Validation Report ==={'\033[0m'}"
        )
        print(f"{status_color}Overall Status: {overall_status.upper()}{'\033[0m'}\n")

        # Print configuration validation
        config_results = self.validation_results.get("configuration", {})
        config_status = config_results.get("status", "unknown")
        status_color = "\033[32m" if config_status == "success" else "\033[31m"
        print(
            f"{status_color}Configuration Validation: {config_status.upper()}{'\033[0m'}"
        )

        if config_results.get("errors"):
            print("  Errors:")
            for error in config_results.get("errors", []):
                print(f"    - \033[31m{error}\033[0m")

        if config_results.get("warnings"):
            print("  Warnings:")
            for warning in config_results.get("warnings", []):
                print(f"    - \033[33m{warning}\033[0m")

        print()

        # Print connectivity validation
        connectivity_results = self.validation_results.get("connectivity", {})
        connectivity_status = connectivity_results.get("status", "unknown")
        status_color = "\033[32m" if connectivity_status == "success" else "\033[31m"
        print(
            f"{status_color}Connectivity Validation: {connectivity_status.upper()}{'\033[0m'}"
        )

        service_results = connectivity_results.get("service_results", {})
        for service_name, result in service_results.items():
            status = result.get("status", "unknown")
            message = result.get("message", "")
            status_color = "\033[32m" if status == "success" else "\033[31m"
            print(
                f"  {service_name}: {status_color}{status.upper()}\033[0m - {message}"
            )

        print()

        # Print feature validation
        feature_results = self.validation_results.get("features", {})
        feature_status = feature_results.get("status", "unknown")
        status_color = "\033[32m" if feature_status == "success" else "\033[31m"
        print(f"{status_color}Feature Validation: {feature_status.upper()}{'\033[0m'}")

        feature_results_dict = feature_results.get("feature_results", {})
        for feature_name, result in feature_results_dict.items():
            status = result.get("status", "unknown")
            message = result.get("message", "")
            status_color = (
                "\033[32m"
                if status == "success"
                else "\033[33m"
                if status == "warning"
                else "\033[31m"
            )
            print(
                f"  {feature_name}: {status_color}{status.upper()}\033[0m - {message}"
            )

        print("\n=== End of Validation Report ===\n")


async def run_validation(config_path: str) -> int:
    """Run validation with the given configuration.

    Args:
        config_path: Path to configuration file

    Returns:
        Exit code (0 for success, 1 for error)
    """
    validator = MultiportValidator(config_path)
    results = await validator.run_validation()
    validator.print_validation_report()

    # Return appropriate exit code
    if results.get("overall_status") == "error":
        return 1
    return 0


async def main() -> int:
    """Main entry point for validation script.

    Returns:
        Exit code
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate AI Gateway multiport configuration"
    )
    parser.add_argument(
        "--config", "-c", help="Path to configuration file", required=True
    )
    parser.add_argument(
        "--verbose", "-v", help="Enable verbose output", action="store_true"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger("ai_gateway").setLevel(logging.DEBUG)

    # Run validation
    return await run_validation(args.config)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
