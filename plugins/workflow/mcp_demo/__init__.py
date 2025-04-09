"""MCP Demo workflow package."""

# Re-export SimpleLLMAdapter to make it available at package level
try:
    from .workflow import SimpleLLMAdapter
except ImportError:
    pass
