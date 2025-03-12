"""Provider feature negotiation system for PepperPy.

This module provides a feature negotiation system for PepperPy providers,
allowing clients to negotiate features with providers at runtime. This helps
ensure that clients can use the best available features for their needs,
even if different providers support different feature sets.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional

from pepperpy.core.capabilities import Capability, CapabilityRegistry

logger = logging.getLogger(__name__)


class FeatureLevel(Enum):
    """Enumeration of feature levels.

    This enumeration defines the levels of feature support that providers
    can offer. Each level represents a different degree of support for
    a feature, from NONE (not supported) to FULL (fully supported).
    """

    NONE = 0  # Feature is not supported
    BASIC = 1  # Basic support for the feature
    STANDARD = 2  # Standard support for the feature
    ADVANCED = 3  # Advanced support for the feature
    FULL = 4  # Full support for the feature

    def __lt__(self, other: "FeatureLevel") -> bool:
        """Compare if this level is less than another level.

        Args:
            other: The other level to compare with.

        Returns:
            True if this level is less than the other level, False otherwise.
        """
        if not isinstance(other, FeatureLevel):
            return NotImplemented
        return self.value < other.value

    def __gt__(self, other: "FeatureLevel") -> bool:
        """Compare if this level is greater than another level.

        Args:
            other: The other level to compare with.

        Returns:
            True if this level is greater than the other level, False otherwise.
        """
        if not isinstance(other, FeatureLevel):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: "FeatureLevel") -> bool:
        """Compare if this level is greater than or equal to another level.

        Args:
            other: The other level to compare with.

        Returns:
            True if this level is greater than or equal to the other level, False otherwise.
        """
        if not isinstance(other, FeatureLevel):
            return NotImplemented
        return self.value >= other.value

    def __le__(self, other: "FeatureLevel") -> bool:
        """Compare if this level is less than or equal to another level.

        Args:
            other: The other level to compare with.

        Returns:
            True if this level is less than or equal to the other level, False otherwise.
        """
        if not isinstance(other, FeatureLevel):
            return NotImplemented
        return self.value <= other.value


class Feature:
    """Feature descriptor for provider negotiation.

    This class represents a feature that can be negotiated with providers.
    It includes information about the feature, such as its name, description,
    required capabilities, and the minimum level of support required.

    Example:
        ```python
        # Define a feature
        streaming = Feature(
            name="streaming",
            description="Streaming text generation",
            required_capabilities=[Capability.STREAMING],
            min_level=FeatureLevel.BASIC,
        )

        # Check if a provider supports the feature
        if streaming.is_supported_by("openai"):
            # Use streaming with OpenAI
            pass
        ```
    """

    def __init__(
        self,
        name: str,
        description: str,
        required_capabilities: List[Capability],
        min_level: FeatureLevel = FeatureLevel.BASIC,
    ):
        """Initialize the feature.

        Args:
            name: The name of the feature.
            description: A description of the feature.
            required_capabilities: The capabilities required for the feature.
            min_level: The minimum level of support required for the feature.
        """
        self.name = name
        self.description = description
        self.required_capabilities = required_capabilities
        self.min_level = min_level

    def is_supported_by(self, provider_id: str) -> bool:
        """Check if a provider supports this feature.

        Args:
            provider_id: The ID of the provider to check.

        Returns:
            True if the provider supports this feature, False otherwise.
        """
        # Check if the provider supports all required capabilities
        return CapabilityRegistry.provider_supports_all(
            provider_id, self.required_capabilities
        )

    def get_level_for(self, provider_id: str) -> FeatureLevel:
        """Get the level of support for this feature from a provider.

        Args:
            provider_id: The ID of the provider to check.

        Returns:
            The level of support for this feature from the provider.
        """
        # If the provider doesn't support the feature, return NONE
        if not self.is_supported_by(provider_id):
            return FeatureLevel.NONE

        # Get the provider's feature levels
        provider_levels = FeatureRegistry.get_provider_feature_levels(provider_id)

        # If the provider has a specific level for this feature, return it
        if self.name in provider_levels:
            return provider_levels[self.name]

        # Otherwise, return the minimum level
        return self.min_level

    def __str__(self) -> str:
        """Get a string representation of the feature.

        Returns:
            A string representation of the feature.
        """
        return f"Feature({self.name}, {self.description}, {self.required_capabilities}, {self.min_level})"

    def __repr__(self) -> str:
        """Get a string representation of the feature.

        Returns:
            A string representation of the feature.
        """
        return self.__str__()


class FeatureRegistry:
    """Registry for features and provider feature levels.

    This class provides a registry for features and provider feature levels,
    allowing clients to discover and negotiate features with providers at runtime.

    Example:
        ```python
        # Register a feature
        FeatureRegistry.register_feature(
            Feature(
                name="streaming",
                description="Streaming text generation",
                required_capabilities=[Capability.STREAMING],
                min_level=FeatureLevel.BASIC,
            )
        )

        # Register provider feature levels
        FeatureRegistry.register_provider_feature_levels(
            "openai",
            {
                "streaming": FeatureLevel.FULL,
                "function_calling": FeatureLevel.ADVANCED,
            }
        )

        # Get a feature
        streaming = FeatureRegistry.get_feature("streaming")

        # Check if a provider supports a feature
        if FeatureRegistry.provider_supports_feature("openai", "streaming"):
            # Use streaming with OpenAI
            pass

        # Get the level of support for a feature from a provider
        level = FeatureRegistry.get_provider_feature_level("openai", "streaming")
        if level >= FeatureLevel.STANDARD:
            # Use standard streaming features
            pass
        ```
    """

    _features: Dict[str, Feature] = {}
    _provider_levels: Dict[str, Dict[str, FeatureLevel]] = {}

    @classmethod
    def register_feature(cls, feature: Feature) -> None:
        """Register a feature.

        Args:
            feature: The feature to register.
        """
        cls._features[feature.name] = feature

    @classmethod
    def get_feature(cls, feature_name: str) -> Feature:
        """Get a feature.

        Args:
            feature_name: The name of the feature to get.

        Returns:
            The feature.

        Raises:
            KeyError: If the feature is not registered.
        """
        if feature_name not in cls._features:
            raise KeyError(f"Feature '{feature_name}' is not registered")
        return cls._features[feature_name]

    @classmethod
    def get_all_features(cls) -> List[Feature]:
        """Get all registered features.

        Returns:
            A list of all registered features.
        """
        return list(cls._features.values())

    @classmethod
    def register_provider_feature_levels(
        cls, provider_id: str, feature_levels: Dict[str, FeatureLevel]
    ) -> None:
        """Register a provider's feature levels.

        Args:
            provider_id: The ID of the provider.
            feature_levels: A dictionary mapping feature names to feature levels.
        """
        cls._provider_levels[provider_id] = feature_levels

    @classmethod
    def get_provider_feature_levels(cls, provider_id: str) -> Dict[str, FeatureLevel]:
        """Get a provider's feature levels.

        Args:
            provider_id: The ID of the provider.

        Returns:
            A dictionary mapping feature names to feature levels.
        """
        return cls._provider_levels.get(provider_id, {})

    @classmethod
    def get_provider_feature_level(
        cls, provider_id: str, feature_name: str
    ) -> FeatureLevel:
        """Get a provider's level of support for a feature.

        Args:
            provider_id: The ID of the provider.
            feature_name: The name of the feature.

        Returns:
            The provider's level of support for the feature.
        """
        # Get the feature
        try:
            feature = cls.get_feature(feature_name)
        except KeyError:
            return FeatureLevel.NONE

        # Get the provider's level of support for the feature
        return feature.get_level_for(provider_id)

    @classmethod
    def provider_supports_feature(cls, provider_id: str, feature_name: str) -> bool:
        """Check if a provider supports a feature.

        Args:
            provider_id: The ID of the provider.
            feature_name: The name of the feature.

        Returns:
            True if the provider supports the feature, False otherwise.
        """
        # Get the feature
        try:
            feature = cls.get_feature(feature_name)
        except KeyError:
            return False

        # Check if the provider supports the feature
        return feature.is_supported_by(provider_id)

    @classmethod
    def get_providers_supporting_feature(cls, feature_name: str) -> List[str]:
        """Get all providers that support a feature.

        Args:
            feature_name: The name of the feature.

        Returns:
            A list of provider IDs that support the feature.
        """
        # Get the feature
        try:
            feature = cls.get_feature(feature_name)
        except KeyError:
            return []

        # Get all providers
        providers = set(cls._provider_levels.keys())

        # Add all providers from the capability registry
        for capability in feature.required_capabilities:
            providers.update(
                CapabilityRegistry.get_providers_with_capability(capability)
            )

        # Filter providers that support the feature
        return [
            provider_id
            for provider_id in providers
            if feature.is_supported_by(provider_id)
        ]

    @classmethod
    def get_best_provider_for_feature(
        cls, feature_name: str, min_level: FeatureLevel = FeatureLevel.BASIC
    ) -> Optional[str]:
        """Get the best provider for a feature.

        Args:
            feature_name: The name of the feature.
            min_level: The minimum level of support required.

        Returns:
            The ID of the best provider for the feature, or None if no provider
            supports the feature at the required level.
        """
        # Get all providers that support the feature
        providers = cls.get_providers_supporting_feature(feature_name)

        # If no providers support the feature, return None
        if not providers:
            return None

        # Get the feature
        try:
            feature = cls.get_feature(feature_name)
        except KeyError:
            return None

        # Find the provider with the highest level of support
        best_provider = None
        best_level = FeatureLevel.NONE

        for provider_id in providers:
            level = feature.get_level_for(provider_id)
            if level >= min_level and level > best_level:
                best_provider = provider_id
                best_level = level

        return best_provider

    @classmethod
    def clear(cls) -> None:
        """Clear the registry."""
        cls._features.clear()
        cls._provider_levels.clear()


class FeatureNegotiator:
    """Negotiator for provider features.

    This class provides a negotiator for provider features, allowing clients
    to negotiate features with providers at runtime. It helps clients find
    the best provider for their needs based on the features they require.

    Example:
        ```python
        # Create a negotiator
        negotiator = FeatureNegotiator()

        # Add required features
        negotiator.require_feature("streaming")
        negotiator.require_feature("function_calling", min_level=FeatureLevel.ADVANCED)

        # Find the best provider
        provider_id = negotiator.get_best_provider()

        # Check if a specific provider meets the requirements
        if negotiator.provider_meets_requirements("openai"):
            # Use OpenAI
            pass
        ```
    """

    def __init__(self):
        """Initialize the feature negotiator."""
        self._required_features: Dict[str, FeatureLevel] = {}

    def require_feature(
        self, feature_name: str, min_level: FeatureLevel = FeatureLevel.BASIC
    ) -> None:
        """Require a feature.

        Args:
            feature_name: The name of the feature to require.
            min_level: The minimum level of support required for the feature.

        Raises:
            KeyError: If the feature is not registered.
        """
        # Check if the feature exists
        FeatureRegistry.get_feature(feature_name)

        # Add the feature to the required features
        self._required_features[feature_name] = min_level

    def provider_meets_requirements(self, provider_id: str) -> bool:
        """Check if a provider meets the requirements.

        Args:
            provider_id: The ID of the provider to check.

        Returns:
            True if the provider meets the requirements, False otherwise.
        """
        for feature_name, min_level in self._required_features.items():
            # Check if the provider supports the feature at the required level
            level = FeatureRegistry.get_provider_feature_level(
                provider_id, feature_name
            )
            if level < min_level:
                return False
        return True

    def get_providers_meeting_requirements(self) -> List[str]:
        """Get all providers that meet the requirements.

        Returns:
            A list of provider IDs that meet the requirements.
        """
        # Get all providers that support the first feature
        if not self._required_features:
            return []

        first_feature = next(iter(self._required_features))
        providers = set(FeatureRegistry.get_providers_supporting_feature(first_feature))

        # Filter providers that support all required features
        return [
            provider_id
            for provider_id in providers
            if self.provider_meets_requirements(provider_id)
        ]

    def get_best_provider(self) -> Optional[str]:
        """Get the best provider that meets the requirements.

        Returns:
            The ID of the best provider that meets the requirements,
            or None if no provider meets the requirements.
        """
        # Get all providers that meet the requirements
        providers = self.get_providers_meeting_requirements()

        # If no providers meet the requirements, return None
        if not providers:
            return None

        # If only one provider meets the requirements, return it
        if len(providers) == 1:
            return providers[0]

        # Calculate a score for each provider based on feature levels
        scores = {}
        for provider_id in providers:
            score = 0
            for feature_name, min_level in self._required_features.items():
                level = FeatureRegistry.get_provider_feature_level(
                    provider_id, feature_name
                )
                score += level.value
            scores[provider_id] = score

        # Return the provider with the highest score
        return max(scores.items(), key=lambda x: x[1])[0]

    def clear(self) -> None:
        """Clear the negotiator."""
        self._required_features.clear()


# Common features

# LLM features
TEXT_GENERATION = Feature(
    name="text_generation",
    description="Text generation",
    required_capabilities=[Capability.TEXT_GENERATION],
    min_level=FeatureLevel.BASIC,
)

TEXT_EMBEDDING = Feature(
    name="text_embedding",
    description="Text embedding",
    required_capabilities=[Capability.TEXT_EMBEDDING],
    min_level=FeatureLevel.BASIC,
)

STREAMING = Feature(
    name="streaming",
    description="Streaming text generation",
    required_capabilities=[Capability.STREAMING],
    min_level=FeatureLevel.BASIC,
)

FUNCTION_CALLING = Feature(
    name="function_calling",
    description="Function calling",
    required_capabilities=[Capability.FUNCTION_CALLING],
    min_level=FeatureLevel.BASIC,
)

TOOL_CALLING = Feature(
    name="tool_calling",
    description="Tool calling",
    required_capabilities=[Capability.TOOL_CALLING],
    min_level=FeatureLevel.BASIC,
)

VISION = Feature(
    name="vision",
    description="Vision capabilities",
    required_capabilities=[Capability.VISION],
    min_level=FeatureLevel.BASIC,
)

AUDIO = Feature(
    name="audio",
    description="Audio capabilities",
    required_capabilities=[Capability.AUDIO],
    min_level=FeatureLevel.BASIC,
)

MULTI_MODAL = Feature(
    name="multi_modal",
    description="Multi-modal capabilities",
    required_capabilities=[Capability.MULTI_MODAL],
    min_level=FeatureLevel.BASIC,
)

# RAG features
DOCUMENT_STORAGE = Feature(
    name="document_storage",
    description="Document storage",
    required_capabilities=[Capability.DOCUMENT_STORAGE],
    min_level=FeatureLevel.BASIC,
)

DOCUMENT_RETRIEVAL = Feature(
    name="document_retrieval",
    description="Document retrieval",
    required_capabilities=[Capability.DOCUMENT_RETRIEVAL],
    min_level=FeatureLevel.BASIC,
)

DOCUMENT_SEARCH = Feature(
    name="document_search",
    description="Document search",
    required_capabilities=[Capability.DOCUMENT_SEARCH],
    min_level=FeatureLevel.BASIC,
)

METADATA_FILTERING = Feature(
    name="metadata_filtering",
    description="Metadata filtering",
    required_capabilities=[Capability.METADATA_FILTERING],
    min_level=FeatureLevel.BASIC,
)

HYBRID_SEARCH = Feature(
    name="hybrid_search",
    description="Hybrid search",
    required_capabilities=[Capability.HYBRID_SEARCH],
    min_level=FeatureLevel.BASIC,
)

# Data features
KEY_VALUE_STORAGE = Feature(
    name="key_value_storage",
    description="Key-value storage",
    required_capabilities=[Capability.KEY_VALUE_STORAGE],
    min_level=FeatureLevel.BASIC,
)

BATCH_OPERATIONS = Feature(
    name="batch_operations",
    description="Batch operations",
    required_capabilities=[Capability.BATCH_OPERATIONS],
    min_level=FeatureLevel.BASIC,
)

TTL_SUPPORT = Feature(
    name="ttl_support",
    description="Time-to-live support",
    required_capabilities=[Capability.TTL_SUPPORT],
    min_level=FeatureLevel.BASIC,
)

METADATA_SUPPORT = Feature(
    name="metadata_support",
    description="Metadata support",
    required_capabilities=[Capability.METADATA_SUPPORT],
    min_level=FeatureLevel.BASIC,
)

# Register common features
FeatureRegistry.register_feature(TEXT_GENERATION)
FeatureRegistry.register_feature(TEXT_EMBEDDING)
FeatureRegistry.register_feature(STREAMING)
FeatureRegistry.register_feature(FUNCTION_CALLING)
FeatureRegistry.register_feature(TOOL_CALLING)
FeatureRegistry.register_feature(VISION)
FeatureRegistry.register_feature(AUDIO)
FeatureRegistry.register_feature(MULTI_MODAL)
FeatureRegistry.register_feature(DOCUMENT_STORAGE)
FeatureRegistry.register_feature(DOCUMENT_RETRIEVAL)
FeatureRegistry.register_feature(DOCUMENT_SEARCH)
FeatureRegistry.register_feature(METADATA_FILTERING)
FeatureRegistry.register_feature(HYBRID_SEARCH)
FeatureRegistry.register_feature(KEY_VALUE_STORAGE)
FeatureRegistry.register_feature(BATCH_OPERATIONS)
FeatureRegistry.register_feature(TTL_SUPPORT)
FeatureRegistry.register_feature(METADATA_SUPPORT)


# Convenience functions


def require_feature(
    provider_id: str, feature_name: str, min_level: FeatureLevel = FeatureLevel.BASIC
) -> None:
    """Require that a provider supports a feature at a minimum level.

    Args:
        provider_id: The ID of the provider.
        feature_name: The name of the feature to require.
        min_level: The minimum level of support required for the feature.

    Raises:
        ValueError: If the provider does not support the feature at the required level.
    """
    level = FeatureRegistry.get_provider_feature_level(provider_id, feature_name)
    if level < min_level:
        raise ValueError(
            f"Provider '{provider_id}' does not support feature '{feature_name}' at level '{min_level.name}'"
        )


def get_best_provider_for_features(
    feature_names: List[str], min_level: FeatureLevel = FeatureLevel.BASIC
) -> Optional[str]:
    """Get the best provider for a set of features.

    Args:
        feature_names: The names of the features to require.
        min_level: The minimum level of support required for the features.

    Returns:
        The ID of the best provider for the features, or None if no provider
        supports all the features at the required level.
    """
    negotiator = FeatureNegotiator()
    for feature_name in feature_names:
        negotiator.require_feature(feature_name, min_level)
    return negotiator.get_best_provider()


def get_providers_supporting_features(
    feature_names: List[str], min_level: FeatureLevel = FeatureLevel.BASIC
) -> List[str]:
    """Get all providers that support a set of features.

    Args:
        feature_names: The names of the features to require.
        min_level: The minimum level of support required for the features.

    Returns:
        A list of provider IDs that support all the features at the required level.
    """
    negotiator = FeatureNegotiator()
    for feature_name in feature_names:
        negotiator.require_feature(feature_name, min_level)
    return negotiator.get_providers_meeting_requirements()
