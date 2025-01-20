"""Tree of thought reasoner implementation."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from ..common.errors import PepperpyError
from ..models.llm import LLMModel
from ..models.types import Message
from .base import Reasoner, ReasoningError


logger = logging.getLogger(__name__)


@dataclass
class ThoughtNode:
    """Thought node implementation."""
    
    id: str
    parent_id: Optional[str]
    content: str
    score: float
    children: List["ThoughtNode"]


class TreeOfThoughtReasoner(Reasoner):
    """Tree of thought reasoner implementation."""
    
    def __init__(
        self,
        name: str,
        model: LLMModel,
        max_depth: int = 3,
        max_branches: int = 3,
        min_score: float = 0.5,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize tree of thought reasoner.
        
        Args:
            name: Reasoner name
            model: Language model
            max_depth: Maximum tree depth
            max_branches: Maximum number of branches per node
            min_score: Minimum score for valid thoughts
            config: Optional reasoner configuration
        """
        super().__init__(name, config)
        self._model = model
        self._max_depth = max_depth
        self._max_branches = max_branches
        self._min_score = min_score
        
    @property
    def model(self) -> LLMModel:
        """Return language model."""
        return self._model
        
    @property
    def max_depth(self) -> int:
        """Return maximum tree depth."""
        return self._max_depth
        
    @property
    def max_branches(self) -> int:
        """Return maximum number of branches per node."""
        return self._max_branches
        
    @property
    def min_score(self) -> float:
        """Return minimum score for valid thoughts."""
        return self._min_score
        
    async def _initialize(self) -> None:
        """Initialize reasoner."""
        await super()._initialize()
        await self._model.initialize()
        
    async def _cleanup(self) -> None:
        """Clean up reasoner."""
        await super()._cleanup()
        await self._model.cleanup()
        
    async def reason(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Reason about input data using tree of thought.
        
        Args:
            input_data: Input data
            context: Optional reasoning context
            
        Returns:
            Reasoning result
            
        Raises:
            ReasoningError: If reasoning fails
        """
        context = context or {}
        
        try:
            # Generate initial thoughts
            root_thoughts = await self._generate_thoughts(
                input_data=input_data,
                parent_id=None,
                depth=0,
                context=context,
            )
            
            # Build thought tree
            thought_tree = []
            for thought in root_thoughts:
                node = await self._build_thought_tree(
                    input_data=input_data,
                    parent_id=thought.id,
                    parent_content=thought.content,
                    depth=1,
                    context=context,
                )
                thought.children = node
                thought_tree.append(thought)
                
            # Find best path
            best_path = self._find_best_path(thought_tree)
            
            # Generate conclusion
            conclusion = await self._get_conclusion(
                input_data=input_data,
                path=best_path,
                context=context,
            )
            
            return {
                "tree": thought_tree,
                "best_path": best_path,
                "conclusion": conclusion,
            }
            
        except Exception as e:
            raise ReasoningError(f"Tree of thought reasoning failed: {e}")
            
    async def _generate_thoughts(
        self,
        input_data: Any,
        parent_id: Optional[str],
        depth: int,
        context: Dict[str, Any],
    ) -> List[ThoughtNode]:
        """Generate thoughts.
        
        Args:
            input_data: Input data
            parent_id: Optional parent thought ID
            depth: Current tree depth
            context: Reasoning context
            
        Returns:
            List of thought nodes
        """
        prompt = self._build_thought_prompt(input_data, parent_id, depth, context)
        message = Message(role="user", content=prompt)
        response = await self._model.generate([message])
        
        thoughts = []
        for line in response.content.split("\n"):
            line = line.strip()
            if not line:
                continue
                
            # Extract thought and score
            parts = line.split(" | ")
            if len(parts) != 2:
                continue
                
            thought, score = parts
            try:
                score = float(score)
            except ValueError:
                continue
                
            if score < self._min_score:
                continue
                
            thoughts.append(
                ThoughtNode(
                    id=f"{depth}-{len(thoughts)}",
                    parent_id=parent_id,
                    content=thought,
                    score=score,
                    children=[],
                )
            )
            
            if len(thoughts) >= self._max_branches:
                break
                
        return thoughts
        
    async def _build_thought_tree(
        self,
        input_data: Any,
        parent_id: str,
        parent_content: str,
        depth: int,
        context: Dict[str, Any],
    ) -> List[ThoughtNode]:
        """Build thought tree.
        
        Args:
            input_data: Input data
            parent_id: Parent thought ID
            parent_content: Parent thought content
            depth: Current tree depth
            context: Reasoning context
            
        Returns:
            List of thought nodes
        """
        if depth >= self._max_depth:
            return []
            
        thoughts = await self._generate_thoughts(
            input_data=input_data,
            parent_id=parent_id,
            depth=depth,
            context=context,
        )
        
        for thought in thoughts:
            children = await self._build_thought_tree(
                input_data=input_data,
                parent_id=thought.id,
                parent_content=thought.content,
                depth=depth + 1,
                context=context,
            )
            thought.children = children
            
        return thoughts
        
    def _find_best_path(self, tree: List[ThoughtNode]) -> List[str]:
        """Find best path in thought tree.
        
        Args:
            tree: Thought tree
            
        Returns:
            List of thoughts in best path
        """
        def _get_path_score(path: List[ThoughtNode]) -> float:
            return sum(node.score for node in path) / len(path)
            
        def _find_paths(node: ThoughtNode, current_path: List[ThoughtNode]) -> List[List[ThoughtNode]]:
            path = current_path + [node]
            
            if not node.children:
                return [path]
                
            paths = []
            for child in node.children:
                paths.extend(_find_paths(child, path))
                
            return paths
            
        # Find all paths
        all_paths = []
        for root in tree:
            all_paths.extend(_find_paths(root, []))
            
        # Find path with highest average score
        best_path = max(all_paths, key=_get_path_score)
        return [node.content for node in best_path]
        
    async def _get_conclusion(
        self,
        input_data: Any,
        path: List[str],
        context: Dict[str, Any],
    ) -> str:
        """Get conclusion.
        
        Args:
            input_data: Input data
            path: Best thought path
            context: Reasoning context
            
        Returns:
            Conclusion
        """
        prompt = self._build_conclusion_prompt(input_data, path, context)
        message = Message(role="user", content=prompt)
        response = await self._model.generate([message])
        return response.content
        
    def _build_thought_prompt(
        self,
        input_data: Any,
        parent_id: Optional[str],
        depth: int,
        context: Dict[str, Any],
    ) -> str:
        """Build thought prompt.
        
        Args:
            input_data: Input data
            parent_id: Optional parent thought ID
            depth: Current tree depth
            context: Reasoning context
            
        Returns:
            Thought prompt
        """
        prompt = f"Input: {input_data}\n\n"
        
        if parent_id is not None:
            prompt += f"Parent thought: {parent_id}\n\n"
            
        prompt += f"Generate {self._max_branches} thoughts at depth {depth}.\n"
        prompt += "Format: <thought> | <score>\n"
        prompt += f"Score must be between 0 and 1. Only thoughts with score >= {self._min_score} will be considered.\n\n"
        prompt += "Thoughts:"
        return prompt
        
    def _build_conclusion_prompt(
        self,
        input_data: Any,
        path: List[str],
        context: Dict[str, Any],
    ) -> str:
        """Build conclusion prompt.
        
        Args:
            input_data: Input data
            path: Best thought path
            context: Reasoning context
            
        Returns:
            Conclusion prompt
        """
        prompt = f"Input: {input_data}\n\n"
        
        if path:
            prompt += "Thought path:\n"
            for i, thought in enumerate(path, 1):
                prompt += f"{i}. {thought}\n"
            prompt += "\n"
            
        prompt += "Conclusion:"
        return prompt
        
    def validate(self) -> None:
        """Validate reasoner state."""
        super().validate()
        
        if not self._model:
            raise ValueError("Language model not provided")
            
        if self._max_depth < 1:
            raise ValueError("Maximum depth must be greater than 0")
            
        if self._max_branches < 1:
            raise ValueError("Maximum branches must be greater than 0")
            
        if not 0 <= self._min_score <= 1:
            raise ValueError("Minimum score must be between 0 and 1") 