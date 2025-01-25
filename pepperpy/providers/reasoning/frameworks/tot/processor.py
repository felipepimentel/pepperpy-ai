"""Tree of Thought reasoning processor."""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from pepperpy.reasoning.base import Reasoner
from pepperpy.core.utils.errors import PepperpyError


logger = logging.getLogger(__name__)


@dataclass
class ThoughtNode:
    """Node in thought tree."""
    
    id: str
    content: Any
    score: float
    children: List["ThoughtNode"]


class TreeOfThoughtProcessor(Reasoner):
    """Tree of Thought reasoning processor."""
    
    def __init__(self, max_depth: int = 3, max_branches: int = 3):
        """Initialize processor.
        
        Args:
            max_depth: Maximum tree depth
            max_branches: Maximum branches per node
        """
        self.max_depth = max_depth
        self.max_branches = max_branches
        
    async def reason(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute tree of thought reasoning.
        
        Args:
            input_data: Input data to reason about
            context: Optional reasoning context
            
        Returns:
            Reasoning result containing:
                - thoughts: List of thoughts in best path
                - tree: Full thought tree
                - confidence: Confidence score
                
        Raises:
            PepperpyError: If reasoning fails
        """
        try:
            # Build thought tree
            tree = await self._build_thought_tree(
                input_data=input_data,
                parent_id="root",
                parent_content=input_data,
                depth=0,
                context=context,
            )
            
            # Find best path
            best_path = self._find_best_path(tree)
            
            return {
                "thoughts": best_path,
                "tree": tree,
                "confidence": self._calculate_confidence(best_path),
            }
            
        except Exception as e:
            logger.error(f"Tree of thought reasoning failed: {e}")
            raise PepperpyError(str(e))
            
    async def _build_thought_tree(
        self,
        input_data: Any,
        parent_id: str,
        parent_content: str,
        depth: int,
        context: Optional[Dict[str, Any]],
    ) -> List[ThoughtNode]:
        """Build thought tree.
        
        Args:
            input_data: Input data
            parent_id: Parent thought ID
            parent_content: Parent thought content
            depth: Current tree depth
            context: Optional reasoning context
            
        Returns:
            List of thought nodes
        """
        if depth >= self.max_depth:
            return []
            
        thoughts = await self._generate_thoughts(
            input_data=input_data,
            parent_id=parent_id,
            depth=depth,
            context=context or {},
        )
        
        for thought in thoughts:
            children = await self._build_thought_tree(
                input_data=input_data,
                parent_id=thought.id,
                parent_content=thought.content,
                depth=depth + 1,
                context=context or {},
            )
            thought.children = children
            
        return thoughts
        
    async def _generate_thoughts(
        self,
        input_data: Any,
        parent_id: str,
        depth: int,
        context: Dict[str, Any],
    ) -> List[ThoughtNode]:
        """Generate thoughts for tree node.
        
        Args:
            input_data: Input data
            parent_id: Parent thought ID
            depth: Current tree depth
            context: Reasoning context
            
        Returns:
            List of thought nodes
            
        Raises:
            NotImplementedError: Must be implemented by concrete class
        """
        raise NotImplementedError
        
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
        
    def _calculate_confidence(self, path: List[str]) -> float:
        """Calculate confidence score for reasoning path.
        
        Args:
            path: List of thoughts in path
            
        Returns:
            Confidence score between 0 and 1
            
        Raises:
            NotImplementedError: Must be implemented by concrete class
        """
        raise NotImplementedError
