#!/usr/bin/env python
"""
Example demonstrating the provider capability discovery and feature negotiation systems.

This example shows how to:
1. Register provider capabilities
2. Query provider capabilities
3. Use the feature negotiation system to find the best provider for a set of features
4. Require specific features from providers

Note: Set your API keys in a .env file before running this example.
"""

import logging
import os

from pepperpy.core.capabilities import (
    Capability,
    CapabilityRegistry,
    CapabilitySet,
)
from pepperpy.core.negotiation import (
    FeatureLevel,
    FeatureNegotiator,
    FeatureRegistry,
    get_best_provider_for_features,
    require_feature,
)
from pepperpy.llm import LLMProvider
from pepperpy.rag import RAGProvider

# Import utility functions for environment setup
try:
    from utils import check_api_keys, load_env, setup_logging
except ImportError:
    # Fallback if utils.py is not available
    def load_env():
        """Load environment variables from .env file."""
        if os.path.exists(".env"):
            with open(".env") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value
            print("Loaded environment variables from .env file")
        else:
            print("No .env file found")

    def setup_logging():
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def check_api_keys(keys):
        """Check if required API keys are set."""
        missing = [key for key in keys if not os.environ.get(key)]
        if missing:
            print(f"Warning: Missing API keys: {', '.join(missing)}")
            print("Some examples may not work without these keys")
        else:
            print(f"All required API keys are set: {', '.join(keys)}")


def main():
    """Run the provider capabilities example."""
    # Load environment variables and set up logging
    load_env()
    setup_logging()
    check_api_keys(["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "PINECONE_API_KEY"])

    # Register provider capabilities
    register_provider_capabilities()

    # Demonstrate capability discovery
    demonstrate_capability_discovery()

    # Demonstrate feature negotiation
    demonstrate_feature_negotiation()

    # Demonstrate finding the best provider for a set of features
    demonstrate_best_provider_selection()

    # Demonstrate requiring specific features from providers
    demonstrate_feature_requirements()


def register_provider_capabilities():
    """Register capabilities for various providers."""
    logging.info("Registering provider capabilities...")

    # Register OpenAI capabilities
    openai_capabilities = CapabilitySet()
    openai_capabilities.add(Capability.TEXT_GENERATION)
    openai_capabilities.add(Capability.TEXT_EMBEDDING)
    openai_capabilities.add(Capability.STREAMING)
    openai_capabilities.add(Capability.FUNCTION_CALLING)
    openai_capabilities.add(Capability.TOOL_CALLING)
    openai_capabilities.add(Capability.VISION)
    CapabilityRegistry.register_capabilities("openai", openai_capabilities)

    # Register Anthropic capabilities
    anthropic_capabilities = CapabilitySet()
    anthropic_capabilities.add(Capability.TEXT_GENERATION)
    anthropic_capabilities.add(Capability.STREAMING)
    anthropic_capabilities.add(Capability.TOOL_CALLING)
    anthropic_capabilities.add(Capability.VISION)
    CapabilityRegistry.register_capabilities("anthropic", anthropic_capabilities)

    # Register Pinecone capabilities
    pinecone_capabilities = CapabilitySet()
    pinecone_capabilities.add(Capability.DOCUMENT_STORAGE)
    pinecone_capabilities.add(Capability.DOCUMENT_RETRIEVAL)
    pinecone_capabilities.add(Capability.DOCUMENT_SEARCH)
    pinecone_capabilities.add(Capability.METADATA_FILTERING)
    CapabilityRegistry.register_capabilities("pinecone", pinecone_capabilities)

    # Register provider feature levels
    FeatureRegistry.register_provider_feature_levels(
        "openai",
        {
            "text_generation": FeatureLevel.FULL,
            "text_embedding": FeatureLevel.ADVANCED,
            "streaming": FeatureLevel.FULL,
            "function_calling": FeatureLevel.ADVANCED,
            "tool_calling": FeatureLevel.STANDARD,
            "vision": FeatureLevel.STANDARD,
        },
    )

    FeatureRegistry.register_provider_feature_levels(
        "anthropic",
        {
            "text_generation": FeatureLevel.FULL,
            "streaming": FeatureLevel.FULL,
            "tool_calling": FeatureLevel.BASIC,
            "vision": FeatureLevel.BASIC,
        },
    )

    FeatureRegistry.register_provider_feature_levels(
        "pinecone",
        {
            "document_storage": FeatureLevel.FULL,
            "document_retrieval": FeatureLevel.FULL,
            "document_search": FeatureLevel.ADVANCED,
            "metadata_filtering": FeatureLevel.STANDARD,
        },
    )

    logging.info("Provider capabilities registered successfully.")


def demonstrate_capability_discovery():
    """Demonstrate how to discover provider capabilities."""
    logging.info("\n=== Capability Discovery ===")

    # Get all providers with a specific capability
    text_gen_providers = CapabilityRegistry.get_providers_with_capability(
        Capability.TEXT_GENERATION
    )
    logging.info(f"Providers with text generation capability: {text_gen_providers}")

    # Check if a provider has a specific capability
    openai_has_vision = CapabilityRegistry.has_capability("openai", Capability.VISION)
    logging.info(f"OpenAI has vision capability: {openai_has_vision}")

    # Check if a provider has multiple capabilities
    anthropic_has_embedding = CapabilityRegistry.has_capability(
        "anthropic", Capability.TEXT_EMBEDDING
    )
    logging.info(f"Anthropic has embedding capability: {anthropic_has_embedding}")

    # Get all capabilities for a provider
    openai_capabilities = CapabilityRegistry.get_provider_capabilities("openai")
    logging.info(
        f"OpenAI capabilities: {[c.name for c in openai_capabilities.get_all()]}"
    )

    # Check if a provider supports all required capabilities
    required_capabilities = [
        Capability.TEXT_GENERATION,
        Capability.STREAMING,
        Capability.TOOL_CALLING,
    ]
    anthropic_supports_all = CapabilityRegistry.provider_supports_all(
        "anthropic", required_capabilities
    )
    logging.info(
        f"Anthropic supports all required capabilities {[c.name for c in required_capabilities]}: "
        f"{anthropic_supports_all}"
    )


def demonstrate_feature_negotiation():
    """Demonstrate how to use the feature negotiation system."""
    logging.info("\n=== Feature Negotiation ===")

    # Create a feature negotiator
    negotiator = FeatureNegotiator()

    # Add required features
    negotiator.require_feature("text_generation")
    negotiator.require_feature("streaming")
    negotiator.require_feature("tool_calling", min_level=FeatureLevel.BASIC)

    # Get all providers that meet the requirements
    providers = negotiator.get_providers_meeting_requirements()
    logging.info(f"Providers meeting all requirements: {providers}")

    # Check if a specific provider meets the requirements
    openai_meets = negotiator.provider_meets_requirements("openai")
    logging.info(f"OpenAI meets all requirements: {openai_meets}")

    anthropic_meets = negotiator.provider_meets_requirements("anthropic")
    logging.info(f"Anthropic meets all requirements: {anthropic_meets}")

    # Get the best provider
    best_provider = negotiator.get_best_provider()
    logging.info(f"Best provider for the requirements: {best_provider}")

    # Create a new negotiator with more stringent requirements
    advanced_negotiator = FeatureNegotiator()
    advanced_negotiator.require_feature("text_generation", min_level=FeatureLevel.FULL)
    advanced_negotiator.require_feature(
        "function_calling", min_level=FeatureLevel.ADVANCED
    )
    advanced_negotiator.require_feature("tool_calling", min_level=FeatureLevel.STANDARD)

    # Get providers meeting advanced requirements
    advanced_providers = advanced_negotiator.get_providers_meeting_requirements()
    logging.info(f"Providers meeting advanced requirements: {advanced_providers}")


def demonstrate_best_provider_selection():
    """Demonstrate how to find the best provider for a set of features."""
    logging.info("\n=== Best Provider Selection ===")

    # Find the best provider for a single feature
    best_for_text_gen = FeatureRegistry.get_best_provider_for_feature("text_generation")
    logging.info(f"Best provider for text generation: {best_for_text_gen}")

    # Find the best provider for a set of features
    features = ["text_generation", "streaming", "tool_calling"]
    best_provider = get_best_provider_for_features(features)
    logging.info(f"Best provider for {features}: {best_provider}")

    # Find the best provider with a minimum level requirement
    advanced_features = ["text_generation", "function_calling"]
    best_advanced_provider = get_best_provider_for_features(
        advanced_features, min_level=FeatureLevel.ADVANCED
    )
    logging.info(
        f"Best provider for {advanced_features} at ADVANCED level: {best_advanced_provider}"
    )

    # Find the best RAG provider
    rag_features = ["document_storage", "document_retrieval", "metadata_filtering"]
    best_rag_provider = get_best_provider_for_features(rag_features)
    logging.info(f"Best provider for RAG features {rag_features}: {best_rag_provider}")


def demonstrate_feature_requirements():
    """Demonstrate how to require specific features from providers."""
    logging.info("\n=== Feature Requirements ===")

    # Require a feature from a provider
    try:
        require_feature("openai", "text_generation", min_level=FeatureLevel.FULL)
        logging.info("OpenAI supports text generation at FULL level")
    except ValueError as e:
        logging.error(f"Error: {e}")

    # Try to require a feature that a provider doesn't support at the required level
    try:
        require_feature("anthropic", "function_calling", min_level=FeatureLevel.BASIC)
        logging.info("Anthropic supports function calling at BASIC level")
    except ValueError as e:
        logging.error(f"Error: {e}")

    # Create an LLM provider based on capabilities
    best_llm_provider = get_best_provider_for_features([
        "text_generation",
        "streaming",
        "tool_calling",
    ])
    if best_llm_provider:
        logging.info(f"Creating LLM provider: {best_llm_provider}")
        # In a real application, you would use the provider ID to create a provider
        llm = LLMProvider(provider_id=best_llm_provider)
        logging.info(f"Created LLM provider: {llm}")

    # Create a RAG provider based on capabilities
    best_rag_provider = get_best_provider_for_features([
        "document_storage",
        "document_retrieval",
    ])
    if best_rag_provider:
        logging.info(f"Creating RAG provider: {best_rag_provider}")
        # In a real application, you would use the provider ID to create a provider
        rag = RAGProvider(provider_id=best_rag_provider)
        logging.info(f"Created RAG provider: {rag}")


if __name__ == "__main__":
    main()
