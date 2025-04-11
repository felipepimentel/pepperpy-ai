#!/usr/bin/env python3
"""
PepperPy AI Gateway Orchestrator

This module provides orchestration capabilities for routing requests between AI models
based on various criteria like task type, cost, latency, and accuracy requirements.
"""

import asyncio
import logging
import time
from enum import Enum

from plugins.workflow.ai_gateway.gateway import (
    AIGateway,
    GatewayRequest,
    GatewayResponse,
    GatewayStatus,
    ModelCapability,
    ModelProvider,
)


# Orchestration strategies
class RoutingStrategy(str, Enum):
    """Strategies for routing between models."""

    COST = "cost"  # Optimize for lowest cost
    LATENCY = "latency"  # Optimize for lowest latency
    ACCURACY = "accuracy"  # Optimize for highest accuracy
    FALLBACK = "fallback"  # Try primary, fallback to secondary
    ENSEMBLE = "ensemble"  # Use multiple models and combine results
    CONTEXTUAL = "contextual"  # Choose based on content analysis


class RouteSelector:
    """Base class for route selection strategies."""

    def __init__(self, gateway: AIGateway):
        """Initialize the route selector.

        Args:
            gateway: The AI Gateway instance
        """
        self.gateway = gateway
        self.logger = logging.getLogger(self.__class__.__name__)

    async def select_model(self, request: GatewayRequest) -> str | None:
        """Select a model for the request.

        Args:
            request: The gateway request

        Returns:
            Selected model ID or None if no suitable model
        """
        raise NotImplementedError("Subclasses must implement select_model")


class CostOptimizedSelector(RouteSelector):
    """Select the lowest cost model meeting requirements."""

    async def select_model(self, request: GatewayRequest) -> str | None:
        """Select lowest cost model.

        Args:
            request: The gateway request

        Returns:
            Selected model ID or None if no suitable model
        """
        # Extract the required capability from the request
        operation = request.operation
        capability = None

        if operation == "chat":
            capability = ModelCapability.CHAT
        elif operation == "completion":
            capability = ModelCapability.COMPLETION
        elif operation == "embedding":
            capability = ModelCapability.EMBEDDING
        elif operation == "image":
            capability = ModelCapability.IMAGE
        elif operation == "voice":
            capability = ModelCapability.VOICE
        else:
            # Default to chat for unknown operations
            capability = ModelCapability.CHAT

        # Get all models supporting this capability
        model_ids = await self.gateway.model_registry.get_models_by_capability(
            capability
        )

        if not model_ids:
            self.logger.warning(f"No models found supporting capability: {capability}")
            return None

        # Simple cost ranking (in a real implementation this would use actual costs)
        # Here we just use a predefined cost mapping for demonstration
        model_costs = {
            "gpt-3.5-turbo": 1,  # Lowest cost
            "claude-instant": 2,
            "gpt-4-turbo": 5,
            "claude-2": 6,
            "gpt-4": 10,  # Highest cost
        }

        # Get minimum token requirements if specified
        min_tokens = request.parameters.get("min_context_tokens", 0)

        # Filter models by token capacity
        model_tokens = {
            "gpt-3.5-turbo": 4096,
            "claude-instant": 8192,
            "gpt-4-turbo": 8192,
            "claude-2": 16384,
            "gpt-4": 8192,
        }

        # Find lowest cost model that meets requirements
        valid_models = [
            model_id
            for model_id in model_ids
            if model_id in model_tokens and model_tokens.get(model_id, 0) >= min_tokens
        ]

        if not valid_models:
            self.logger.warning(f"No models meet token requirement of {min_tokens}")
            return None

        # Sort by cost (lowest first)
        sorted_models = sorted(
            valid_models, key=lambda model_id: model_costs.get(model_id, float("inf"))
        )

        if sorted_models:
            return sorted_models[0]

        return None


class LatencyOptimizedSelector(RouteSelector):
    """Select the lowest latency model meeting requirements."""

    def __init__(self, gateway: AIGateway):
        """Initialize the selector.

        Args:
            gateway: The AI Gateway instance
        """
        super().__init__(gateway)
        self.model_latencies: dict[str, float] = {}
        self.request_times: dict[str, list[float]] = {}

    async def record_latency(
        self, model_id: str, request_id: str, latency: float
    ) -> None:
        """Record model latency.

        Args:
            model_id: Model identifier
            request_id: Request identifier
            latency: Request latency in seconds
        """
        # Update exponential moving average
        current = self.model_latencies.get(model_id, latency)
        alpha = 0.2  # Smoothing factor
        updated = (alpha * latency) + ((1 - alpha) * current)
        self.model_latencies[model_id] = updated

    async def select_model(self, request: GatewayRequest) -> str | None:
        """Select lowest latency model.

        Args:
            request: The gateway request

        Returns:
            Selected model ID or None if no suitable model
        """
        # Start tracking request time
        self.request_times[request.request_id] = [time.time()]

        # Extract the required capability from the request
        operation = request.operation
        capability = None

        if operation == "chat":
            capability = ModelCapability.CHAT
        elif operation == "completion":
            capability = ModelCapability.COMPLETION
        elif operation == "embedding":
            capability = ModelCapability.EMBEDDING
        else:
            # Default to chat for unknown operations
            capability = ModelCapability.CHAT

        # Get all models supporting this capability
        model_ids = await self.gateway.model_registry.get_models_by_capability(
            capability
        )

        if not model_ids:
            self.logger.warning(f"No models found supporting capability: {capability}")
            return None

        # If no latency data yet, use default model or first available
        if not self.model_latencies:
            # Use specifically requested model if available
            requested_model = request.parameters.get("model")
            if requested_model and requested_model in model_ids:
                return requested_model

            # Otherwise use first available model
            return model_ids[0]

        # Sort by latency (lowest first)
        sorted_models = sorted(
            [m for m in model_ids if m in self.model_latencies],
            key=lambda model_id: self.model_latencies.get(model_id, float("inf")),
        )

        # If we have models with latency data, return fastest
        if sorted_models:
            return sorted_models[0]

        # Fall back to first available model
        return model_ids[0]


class FallbackSelector(RouteSelector):
    """Try primary model, fall back to secondary if primary fails."""

    async def select_model(self, request: GatewayRequest) -> str | None:
        """Select primary model or fallback based on previous attempts.

        Args:
            request: The gateway request

        Returns:
            Selected model ID or None if no suitable model
        """
        # Check if this is a retry after a failure
        is_retry = request.parameters.get("is_retry", False)
        failed_model = request.parameters.get("failed_model")

        # If this is a retry, use the fallback model
        if is_retry and failed_model:
            # Get the fallback model based on the failed primary
            fallbacks = {
                "gpt-4": "claude-2",
                "claude-2": "gpt-4",
                "gpt-3.5-turbo": "claude-instant",
                "claude-instant": "gpt-3.5-turbo",
            }

            fallback_model = fallbacks.get(failed_model)
            if fallback_model:
                self.logger.info(
                    f"Using fallback model {fallback_model} after {failed_model} failed"
                )
                return fallback_model

        # For non-retry requests, use the explicitly requested model
        requested_model = request.parameters.get("model")
        if requested_model:
            return requested_model

        # If no model specified, default to a reliable model
        default_models = ["gpt-3.5-turbo", "claude-instant"]

        for model in default_models:
            if await self.gateway.model_registry.get_model(model):
                return model

        # If no default models are available, return None
        self.logger.warning("No suitable primary or fallback models available")
        return None


class ContextualSelector(RouteSelector):
    """Select model based on content analysis."""

    async def select_model(self, request: GatewayRequest) -> str | None:
        """Select model based on content analysis.

        Args:
            request: The gateway request

        Returns:
            Selected model ID or None if no suitable model
        """
        # Extract messages or content from request
        messages = request.inputs.get("messages", [])
        content = ""

        # Extract content from the last user message
        if messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    break

        # If no messages found, try direct content
        if not content:
            content = request.inputs.get("content", "")

        # Perform simple content analysis (in production, use embeddings or classifiers)
        # This is a simplified example based on keyword matching

        # Check for code-related content
        code_indicators = [
            "code",
            "function",
            "programming",
            "javascript",
            "python",
            "java",
            "c++",
            "code review",
        ]
        math_indicators = [
            "math",
            "equation",
            "calculate",
            "computation",
            "formula",
            "algebra",
            "calculus",
        ]
        creative_indicators = [
            "creative",
            "story",
            "poem",
            "fiction",
            "imagine",
            "art",
            "design",
        ]
        reasoning_indicators = [
            "analyze",
            "reason",
            "logic",
            "argument",
            "debate",
            "perspective",
        ]

        content_lower = content.lower()

        # Count indicators in each category
        code_score = sum(1 for word in code_indicators if word in content_lower)
        math_score = sum(1 for word in math_indicators if word in content_lower)
        creative_score = sum(1 for word in creative_indicators if word in content_lower)
        reasoning_score = sum(
            1 for word in reasoning_indicators if word in content_lower
        )

        # Determine the dominant category
        scores = {
            "code": code_score,
            "math": math_score,
            "creative": creative_score,
            "reasoning": reasoning_score,
        }

        dominant_category = max(scores, key=scores.get)

        # Map categories to preferred models
        category_models = {
            "code": ["gpt-4", "claude-2"],
            "math": ["gpt-4", "claude-2"],
            "creative": ["claude-2", "gpt-4"],
            "reasoning": ["gpt-4", "claude-2"],
            "default": ["gpt-3.5-turbo", "claude-instant"],
        }

        # Get preferred models for the category
        preferred_models = category_models.get(
            dominant_category, category_models["default"]
        )

        # Find the first available preferred model
        for model in preferred_models:
            if await self.gateway.model_registry.get_model(model):
                self.logger.info(f"Selected {model} for {dominant_category} content")
                return model

        # Fall back to any available model
        capabilities = ModelCapability.CHAT
        model_ids = await self.gateway.model_registry.get_models_by_capability(
            capabilities
        )

        if model_ids:
            return model_ids[0]

        return None


class EnsembleSelector(RouteSelector):
    """Use multiple models and combine results."""

    async def select_model(self, request: GatewayRequest) -> list[str]:
        """Select multiple models for ensemble.

        Args:
            request: The gateway request

        Returns:
            List of selected model IDs
        """
        # Note: This actually returns a list, but the interface expects a string
        # In practice, you would modify the orchestrator to handle ensemble requests

        # Extract the required capability from the request
        operation = request.operation
        capability = None

        if operation == "chat":
            capability = ModelCapability.CHAT
        elif operation == "completion":
            capability = ModelCapability.COMPLETION
        elif operation == "embedding":
            capability = ModelCapability.EMBEDDING
        else:
            # Default to chat for unknown operations
            capability = ModelCapability.CHAT

        # Get all models supporting this capability
        model_ids = await self.gateway.model_registry.get_models_by_capability(
            capability
        )

        # Predefined model groups for different ensembles
        ensembles = {
            "diverse": ["gpt-4", "claude-2"],
            "fast": ["gpt-3.5-turbo", "claude-instant"],
            "balanced": ["gpt-4", "gpt-3.5-turbo", "claude-instant"],
            "comprehensive": ["gpt-4", "gpt-3.5-turbo", "claude-2", "claude-instant"],
        }

        # Get the requested ensemble type
        ensemble_type = request.parameters.get("ensemble", "balanced")

        # Get the models for the requested ensemble
        ensemble_models = ensembles.get(ensemble_type, ensembles["balanced"])

        # Filter to only available models
        available_ensemble = [model for model in ensemble_models if model in model_ids]

        if not available_ensemble:
            # Fall back to any available models (up to 2)
            return model_ids[:2] if len(model_ids) >= 2 else model_ids

        return available_ensemble


class ModelOrchestrator:
    """Orchestrate requests between multiple AI models."""

    def __init__(self, gateway: AIGateway):
        """Initialize the orchestrator.

        Args:
            gateway: The AI Gateway instance
        """
        self.gateway = gateway
        self.selectors: dict[RoutingStrategy, RouteSelector] = {
            RoutingStrategy.COST: CostOptimizedSelector(gateway),
            RoutingStrategy.LATENCY: LatencyOptimizedSelector(gateway),
            RoutingStrategy.FALLBACK: FallbackSelector(gateway),
            RoutingStrategy.CONTEXTUAL: ContextualSelector(gateway),
            # Ensemble is handled specially
        }
        self.logger = logging.getLogger("ModelOrchestrator")

    async def route_request(self, request: GatewayRequest) -> GatewayResponse:
        """Route a request to the appropriate model.

        Args:
            request: The gateway request

        Returns:
            Gateway response
        """
        # Extract strategy from request parameters
        strategy_name = request.parameters.get("routing_strategy", "contextual")
        try:
            strategy = RoutingStrategy(strategy_name)
        except ValueError:
            strategy = RoutingStrategy.CONTEXTUAL

        start_time = time.time()

        # Handle ensemble strategy specially
        if strategy == RoutingStrategy.ENSEMBLE:
            return await self._handle_ensemble_request(request)

        # Get the selector for the strategy
        selector = self.selectors.get(strategy)
        if not selector:
            return GatewayResponse.error(
                request.request_id, f"Unsupported routing strategy: {strategy}"
            )

        # Select a model
        model_id = await selector.select_model(request)
        if not model_id:
            return GatewayResponse.error(
                request.request_id, "No suitable model found for the request"
            )

        # Get the model provider
        model_provider = await self.gateway.model_registry.get_model(model_id)
        if not model_provider:
            return GatewayResponse.error(
                request.request_id, f"Selected model {model_id} not available"
            )

        # Update request with selected model
        request.parameters["selected_model"] = model_id

        # Execute the request
        try:
            response = await model_provider.execute(request)

            # Record latency for latency-optimized selector
            if strategy == RoutingStrategy.LATENCY and isinstance(
                selector, LatencyOptimizedSelector
            ):
                latency = time.time() - start_time
                await selector.record_latency(model_id, request.request_id, latency)

            # Add orchestration metadata
            if not response.metadata:
                response.metadata = {}

            response.metadata["orchestration"] = {
                "strategy": strategy.value,
                "selected_model": model_id,
                "latency": time.time() - start_time,
            }

            return response
        except Exception as e:
            self.logger.error(f"Error executing request with model {model_id}: {e}")

            # If using fallback strategy, retry with fallback model
            if strategy == RoutingStrategy.FALLBACK:
                request.parameters["is_retry"] = True
                request.parameters["failed_model"] = model_id
                return await self.route_request(request)

            return GatewayResponse.error(
                request.request_id,
                f"Error executing request with model {model_id}: {e!s}",
            )

    async def _handle_ensemble_request(
        self, request: GatewayRequest
    ) -> GatewayResponse:
        """Handle an ensemble request using multiple models.

        Args:
            request: The gateway request

        Returns:
            Gateway response with combined results
        """
        # Create an ensemble selector
        selector = EnsembleSelector(self.gateway)

        # Get models for the ensemble
        model_ids = await selector.select_model(request)
        if not model_ids:
            return GatewayResponse.error(
                request.request_id, "No models available for ensemble"
            )

        # Execute requests in parallel
        tasks = []
        for model_id in model_ids:
            model_provider = await self.gateway.model_registry.get_model(model_id)
            if model_provider:
                # Create a copy of the request for each model
                model_request = GatewayRequest.from_dict(request.to_dict())
                model_request.parameters["selected_model"] = model_id

                # Add task
                tasks.append(
                    self._execute_model_request(model_provider, model_request, model_id)
                )

        # Wait for all requests to complete
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        valid_responses = []
        errors = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"{model_ids[i]}: {result!s}")
            elif isinstance(result, tuple) and len(result) == 2:
                model_id, response = result
                if response.status == GatewayStatus.SUCCESS:
                    valid_responses.append((model_id, response))
                else:
                    errors.append(f"{model_id}: {response.error}")

        # If no valid responses, return error
        if not valid_responses:
            return GatewayResponse.error(
                request.request_id, f"All ensemble models failed: {', '.join(errors)}"
            )

        # Combine responses based on the ensemble method
        ensemble_method = request.parameters.get("ensemble_method", "first")

        if ensemble_method == "first":
            # Return the first successful response
            model_id, response = valid_responses[0]
            response.metadata["orchestration"] = {
                "strategy": RoutingStrategy.ENSEMBLE.value,
                "ensemble_method": ensemble_method,
                "selected_models": model_ids,
                "successful_models": [m for m, _ in valid_responses],
                "latency": time.time() - start_time,
            }
            return response
        elif ensemble_method == "majority":
            # Implement majority voting (simplified version)
            # In practice, this would require parsing and comparing the responses
            # Here we just return the first response with metadata
            model_id, response = valid_responses[0]
            response.metadata["orchestration"] = {
                "strategy": RoutingStrategy.ENSEMBLE.value,
                "ensemble_method": ensemble_method,
                "selected_models": model_ids,
                "successful_models": [m for m, _ in valid_responses],
                "latency": time.time() - start_time,
            }
            return response
        elif ensemble_method == "all":
            # Return all responses
            combined_outputs = {
                "responses": {
                    model_id: response.outputs for model_id, response in valid_responses
                }
            }

            return GatewayResponse.success(
                request.request_id,
                combined_outputs,
                {
                    "orchestration": {
                        "strategy": RoutingStrategy.ENSEMBLE.value,
                        "ensemble_method": ensemble_method,
                        "selected_models": model_ids,
                        "successful_models": [m for m, _ in valid_responses],
                        "latency": time.time() - start_time,
                    }
                },
            )
        else:
            # Default to first method
            model_id, response = valid_responses[0]
            response.metadata["orchestration"] = {
                "strategy": RoutingStrategy.ENSEMBLE.value,
                "ensemble_method": "first",
                "selected_models": model_ids,
                "successful_models": [m for m, _ in valid_responses],
                "latency": time.time() - start_time,
            }
            return response

    async def _execute_model_request(
        self, model_provider: ModelProvider, request: GatewayRequest, model_id: str
    ) -> tuple[str, GatewayResponse]:
        """Execute a request with a specific model provider.

        Args:
            model_provider: The model provider
            request: The gateway request
            model_id: The model ID

        Returns:
            Tuple of model ID and response
        """
        try:
            response = await model_provider.execute(request)
            return (model_id, response)
        except Exception as e:
            self.logger.error(f"Error executing request with model {model_id}: {e}")
            return (model_id, GatewayResponse.error(request.request_id, str(e)))


# Factory function to create an orchestrator
def create_orchestrator(gateway: AIGateway) -> ModelOrchestrator:
    """Create a model orchestrator.

    Args:
        gateway: The AI Gateway instance

    Returns:
        Model orchestrator
    """
    return ModelOrchestrator(gateway)
