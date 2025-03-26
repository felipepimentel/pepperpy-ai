"""Workflow recipes module.

This module provides ready-to-use workflow recipes for common use cases.
Each recipe is a complete, tested solution that combines workflow components
to achieve desired outcomes.

Available recipes:
- Code recipes: Repository analysis, code generation, etc.
- Document recipes: Document analysis, summarization, etc.
- Data recipes: Data analysis, transformation, etc.
- Conversation recipes: Chat, Q&A, etc.
"""

from pepperpy.workflow.recipes.code.repository import RepositoryAnalysisRecipe

__all__ = ["RepositoryAnalysisRecipe"]
