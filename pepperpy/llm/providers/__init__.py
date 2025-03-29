"""LLM provider implementations."""

PROVIDER_MODULES = {
    "openai": "pepperpy.llm.providers.openai.OpenAIProvider",
    "openrouter": "pepperpy.llm.providers.openrouter.OpenRouterProvider",
    "local": "pepperpy.llm.providers.local.LocalProvider",
}

__all__ = list(PROVIDER_MODULES.keys())
