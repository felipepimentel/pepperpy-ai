"""Analyzer for reasoning processes.

This module provides functionality for analyzing reasoning processes,
including step analysis, pattern detection, and quality assessment.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.common.errors import PepperpyError
from pepperpy.reasoning.frameworks.cot import CoTStep
from pepperpy.reasoning.frameworks.react import ReActStep


class AnalyzerError(PepperpyError):
    """Analyzer error."""
    pass


T = TypeVar("T")


class ReasoningAnalyzer(ABC):
    """Base class for reasoning analyzers."""
    
    def __init__(self, name: str):
        """Initialize analyzer.
        
        Args:
            name: Analyzer name
        """
        self.name = name
        self._patterns: Dict[str, Any] = {}
        
    @property
    def patterns(self) -> Dict[str, Any]:
        """Get detected patterns."""
        return self._patterns
        
    @abstractmethod
    async def analyze_cot(self, steps: List[CoTStep]) -> Dict[str, Any]:
        """Analyze Chain-of-Thought steps.
        
        Args:
            steps: CoT steps to analyze
            
        Returns:
            Analysis results
            
        Raises:
            AnalyzerError: If analysis fails
        """
        pass
        
    @abstractmethod
    async def analyze_react(self, steps: List[ReActStep]) -> Dict[str, Any]:
        """Analyze ReAct steps.
        
        Args:
            steps: ReAct steps to analyze
            
        Returns:
            Analysis results
            
        Raises:
            AnalyzerError: If analysis fails
        """
        pass
        
    def validate(self) -> None:
        """Validate analyzer state."""
        if not self.name:
            raise ValueError("Analyzer name cannot be empty")
