"""Optimizer for suggesting improvements to PepperPy components and pipelines."""

from typing import Any, Dict, List, Optional


class Optimizer:
    """Optimizer for suggesting improvements to PepperPy components and pipelines.

    This class analyzes components and pipelines to suggest optimizations
    for performance, memory usage, and other aspects.
    """

    def __init__(self) -> None:
        """Initialize the optimizer."""
        self.optimization_rules: List[Dict[str, Any]] = [
            # Performance optimizations
            {
                "name": "add_caching",
                "category": "performance",
                "impact": "high",
                "description": "Add caching to expensive operations",
                "applies_to": ["llm", "embedding_model", "retriever"],
                "check": self._check_missing_caching,
                "suggestion": "Add a caching layer to reduce redundant operations",
            },
            {
                "name": "batch_processing",
                "category": "performance",
                "impact": "medium",
                "description": "Use batch processing for multiple items",
                "applies_to": ["embedding_model", "document_processor"],
                "check": self._check_missing_batching,
                "suggestion": "Process items in batches to reduce overhead",
            },
            {
                "name": "parallel_execution",
                "category": "performance",
                "impact": "high",
                "description": "Execute independent operations in parallel",
                "applies_to": ["pipeline"],
                "check": self._check_parallelizable,
                "suggestion": "Use parallel execution for independent operations",
            },
            # Memory optimizations
            {
                "name": "streaming_processing",
                "category": "memory",
                "impact": "high",
                "description": "Use streaming for large data processing",
                "applies_to": ["document_loader", "document_processor"],
                "check": self._check_missing_streaming,
                "suggestion": "Process data as a stream to reduce memory usage",
            },
            {
                "name": "optimize_chunk_size",
                "category": "memory",
                "impact": "medium",
                "description": "Optimize text chunk size",
                "applies_to": ["text_splitter"],
                "check": self._check_suboptimal_chunk_size,
                "suggestion": "Adjust chunk size to balance context and memory usage",
            },
            # Configuration optimizations
            {
                "name": "optimize_model_selection",
                "category": "configuration",
                "impact": "high",
                "description": "Select appropriate model for the task",
                "applies_to": ["llm"],
                "check": self._check_suboptimal_model,
                "suggestion": "Use a more appropriate model for this task",
            },
            {
                "name": "optimize_temperature",
                "category": "configuration",
                "impact": "medium",
                "description": "Optimize temperature setting",
                "applies_to": ["llm"],
                "check": self._check_suboptimal_temperature,
                "suggestion": "Adjust temperature based on the task requirements",
            },
            # Architecture optimizations
            {
                "name": "simplify_pipeline",
                "category": "architecture",
                "impact": "medium",
                "description": "Simplify pipeline structure",
                "applies_to": ["pipeline"],
                "check": self._check_pipeline_complexity,
                "suggestion": "Simplify the pipeline by combining or removing components",
            },
            {
                "name": "add_error_handling",
                "category": "architecture",
                "impact": "high",
                "description": "Add robust error handling",
                "applies_to": ["pipeline", "llm", "retriever"],
                "check": self._check_missing_error_handling,
                "suggestion": "Add error handling and fallback mechanisms",
            },
        ]

    def suggest(
        self,
        component: Any,
        categories: Optional[List[str]] = None,
        min_impact: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Suggest optimizations for a component or pipeline.

        Args:
            component: The component or pipeline to optimize
            categories: Optional list of optimization categories to include
            min_impact: Optional minimum impact level (low, medium, high)
            **kwargs: Additional parameters for optimization

        Returns:
            List of optimization suggestions
        """
        # Determine the component type
        component_type = self._get_component_type(component)

        # Filter rules by component type and categories
        applicable_rules = self._filter_rules(
            component_type,
            categories,
            min_impact,
        )

        # Apply the rules to get suggestions
        suggestions = []
        for rule in applicable_rules:
            check_func = rule["check"]
            if check_func(component, **kwargs):
                suggestions.append({
                    "name": rule["name"],
                    "category": rule["category"],
                    "impact": rule["impact"],
                    "description": rule["description"],
                    "suggestion": rule["suggestion"],
                    "details": self._get_suggestion_details(rule["name"], component),
                })

        return suggestions

    def _filter_rules(
        self,
        component_type: str,
        categories: Optional[List[str]] = None,
        min_impact: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Filter optimization rules by component type and categories.

        Args:
            component_type: Type of the component
            categories: Optional list of optimization categories to include
            min_impact: Optional minimum impact level (low, medium, high)

        Returns:
            List of applicable optimization rules
        """
        # Filter by component type
        filtered_rules = [
            rule
            for rule in self.optimization_rules
            if component_type in rule["applies_to"] or "all" in rule["applies_to"]
        ]

        # Filter by categories
        if categories:
            filtered_rules = [
                rule for rule in filtered_rules if rule["category"] in categories
            ]

        # Filter by minimum impact
        if min_impact:
            impact_levels = {"low": 1, "medium": 2, "high": 3}
            min_impact_level = impact_levels.get(min_impact.lower(), 1)

            filtered_rules = [
                rule
                for rule in filtered_rules
                if impact_levels.get(rule["impact"].lower(), 1) >= min_impact_level
            ]

        return filtered_rules

    def _get_component_type(self, component: Any) -> str:
        """Get the type of a component.

        Args:
            component: The component to get the type of

        Returns:
            The component type
        """
        # Check if it's a pipeline
        if hasattr(component, "components") and hasattr(component, "connections"):
            return "pipeline"

        # Check for specific component types
        if hasattr(component, "type"):
            return component.type

        # Use the class name as a fallback
        return type(component).__name__.lower()

    def _get_suggestion_details(self, rule_name: str, component: Any) -> str:
        """Get detailed suggestions for a specific rule and component.

        Args:
            rule_name: Name of the optimization rule
            component: The component to get suggestions for

        Returns:
            Detailed suggestion text
        """
        # This would provide more specific suggestions based on the component
        # For now, we'll return a generic message
        return f"Consider applying the {rule_name} optimization to improve performance."

    # Rule check functions

    def _check_missing_caching(self, component: Any, **kwargs: Any) -> bool:
        """Check if a component is missing caching.

        Args:
            component: The component to check
            **kwargs: Additional parameters

        Returns:
            True if the component is missing caching, False otherwise
        """
        # Check if the component has caching enabled
        if hasattr(component, "config"):
            config = component.config
            return not config.get("use_cache", False)

        # For pipelines, check if any cacheable components are missing caching
        if hasattr(component, "components"):
            cacheable_types = ["llm", "embedding_model", "retriever"]
            for subcomponent in component.components:
                if subcomponent.get("type") in cacheable_types:
                    config = subcomponent.get("config", {})
                    if not config.get("use_cache", False):
                        return True

        return False

    def _check_missing_batching(self, component: Any, **kwargs: Any) -> bool:
        """Check if a component is missing batch processing.

        Args:
            component: The component to check
            **kwargs: Additional parameters

        Returns:
            True if the component is missing batch processing, False otherwise
        """
        # Check if the component has batch processing enabled
        if hasattr(component, "config"):
            config = component.config
            return not config.get("batch_size", 0) > 1

        # For pipelines, check if any batchable components are missing batching
        if hasattr(component, "components"):
            batchable_types = ["embedding_model", "document_processor"]
            for subcomponent in component.components:
                if subcomponent.get("type") in batchable_types:
                    config = subcomponent.get("config", {})
                    if not config.get("batch_size", 0) > 1:
                        return True

        return False

    def _check_parallelizable(self, component: Any, **kwargs: Any) -> bool:
        """Check if a pipeline has parallelizable operations.

        Args:
            component: The pipeline to check
            **kwargs: Additional parameters

        Returns:
            True if the pipeline has parallelizable operations, False otherwise
        """
        # This requires analyzing the pipeline structure to find independent operations
        # For now, we'll return a simple heuristic
        if hasattr(component, "connections"):
            # Count the number of connections
            connections = component.connections
            if len(connections) >= 3:
                # Check if there are multiple paths
                sources = set(conn.get("source", "") for conn in connections)
                targets = set(conn.get("target", "") for conn in connections)
                return len(sources) >= 2 and len(targets) >= 2

        return False

    def _check_missing_streaming(self, component: Any, **kwargs: Any) -> bool:
        """Check if a component is missing streaming processing.

        Args:
            component: The component to check
            **kwargs: Additional parameters

        Returns:
            True if the component is missing streaming, False otherwise
        """
        # Check if the component has streaming enabled
        if hasattr(component, "config"):
            config = component.config
            return not config.get("streaming", False)

        # For pipelines, check if any streamable components are missing streaming
        if hasattr(component, "components"):
            streamable_types = ["document_loader", "document_processor"]
            for subcomponent in component.components:
                if subcomponent.get("type") in streamable_types:
                    config = subcomponent.get("config", {})
                    if not config.get("streaming", False):
                        return True

        return False

    def _check_suboptimal_chunk_size(self, component: Any, **kwargs: Any) -> bool:
        """Check if a text splitter has a suboptimal chunk size.

        Args:
            component: The component to check
            **kwargs: Additional parameters

        Returns:
            True if the component has a suboptimal chunk size, False otherwise
        """
        # Check if the component has a chunk size configuration
        if hasattr(component, "config"):
            config = component.config
            chunk_size = config.get("chunk_size", 0)
            # Check if the chunk size is too small or too large
            return chunk_size < 100 or chunk_size > 2000

        # For pipelines, check if any text splitters have suboptimal chunk sizes
        if hasattr(component, "components"):
            for subcomponent in component.components:
                if subcomponent.get("type") == "text_splitter":
                    config = subcomponent.get("config", {})
                    chunk_size = config.get("chunk_size", 0)
                    if chunk_size < 100 or chunk_size > 2000:
                        return True

        return False

    def _check_suboptimal_model(self, component: Any, **kwargs: Any) -> bool:
        """Check if an LLM component is using a suboptimal model.

        Args:
            component: The component to check
            **kwargs: Additional parameters

        Returns:
            True if the component is using a suboptimal model, False otherwise
        """
        # Check if the component has a model configuration
        if hasattr(component, "config"):
            config = component.config
            model_name = config.get("model_name", "")

            # Check if the model is appropriate for the task
            task = kwargs.get("task", "")
            if task == "summarization" and "gpt-3.5" in model_name:
                return True
            if task == "code_generation" and not any(
                m in model_name for m in ["gpt-4", "claude-3"]
            ):
                return True

        # For pipelines, check if any LLM components are using suboptimal models
        if hasattr(component, "components"):
            for subcomponent in component.components:
                if subcomponent.get("type") == "llm":
                    config = subcomponent.get("config", {})
                    model_name = config.get("model_name", "")

                    # Check if the model is appropriate for the task
                    task = kwargs.get("task", "")
                    if task == "summarization" and "gpt-3.5" in model_name:
                        return True
                    if task == "code_generation" and not any(
                        m in model_name for m in ["gpt-4", "claude-3"]
                    ):
                        return True

        return False

    def _check_suboptimal_temperature(self, component: Any, **kwargs: Any) -> bool:
        """Check if an LLM component is using a suboptimal temperature.

        Args:
            component: The component to check
            **kwargs: Additional parameters

        Returns:
            True if the component is using a suboptimal temperature, False otherwise
        """
        # Check if the component has a temperature configuration
        if hasattr(component, "config"):
            config = component.config
            temperature = config.get("temperature", 0.7)

            # Check if the temperature is appropriate for the task
            task = kwargs.get("task", "")
            if task == "factual_qa" and temperature > 0.3:
                return True
            if task == "creative_writing" and temperature < 0.7:
                return True

        # For pipelines, check if any LLM components are using suboptimal temperatures
        if hasattr(component, "components"):
            for subcomponent in component.components:
                if subcomponent.get("type") == "llm":
                    config = subcomponent.get("config", {})
                    temperature = config.get("temperature", 0.7)

                    # Check if the temperature is appropriate for the task
                    task = kwargs.get("task", "")
                    if task == "factual_qa" and temperature > 0.3:
                        return True
                    if task == "creative_writing" and temperature < 0.7:
                        return True

        return False

    def _check_pipeline_complexity(self, component: Any, **kwargs: Any) -> bool:
        """Check if a pipeline is unnecessarily complex.

        Args:
            component: The pipeline to check
            **kwargs: Additional parameters

        Returns:
            True if the pipeline is unnecessarily complex, False otherwise
        """
        # Check if the pipeline has too many components
        if hasattr(component, "components"):
            components = component.components
            if len(components) > 10:
                return True

            # Check for redundant components
            component_types = [comp.get("type", "") for comp in components]
            if len(component_types) != len(set(component_types)):
                return True

        return False

    def _check_missing_error_handling(self, component: Any, **kwargs: Any) -> bool:
        """Check if a component is missing error handling.

        Args:
            component: The component to check
            **kwargs: Additional parameters

        Returns:
            True if the component is missing error handling, False otherwise
        """
        # Check if the component has error handling configuration
        if hasattr(component, "config"):
            config = component.config
            return not config.get("error_handling", False)

        # For pipelines, check if error handling is configured
        if hasattr(component, "error_handling"):
            return not component.error_handling

        return True
