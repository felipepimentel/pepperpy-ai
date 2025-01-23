"""Tree of Thoughts reasoning framework implementation."""

import heapq
from collections.abc import AsyncGenerator, AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.agents.types import AgentConfig, AgentResponse


@dataclass
class ThoughtNode:
    """Node in the thought tree."""

    thought: str
    score: float
    parent: "ThoughtNode | None" = None
    children: list["ThoughtNode"] = field(default_factory=list)
    depth: int = 0

    def __lt__(self, other: "ThoughtNode") -> bool:
        """Compare nodes by score for priority queue."""
        return self.score > other.score  # Higher scores have priority


class TreeOfThoughtsAgent(BaseAgent):
    """Tree of Thoughts reasoning agent.

    Implements breadth-first exploration of thought paths by:
    1. Generating multiple thoughts at each step
    2. Evaluating thought quality
    3. Expanding promising paths
    4. Backtracking when needed
    5. Finding optimal solution path
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize Tree of Thoughts agent.

        Args:
            config: Agent configuration
        """
        super().__init__(config)
        if config.model_kwargs:
            self.max_depth = config.model_kwargs.get("max_depth", 5)
            self.beam_width = config.model_kwargs.get("beam_width", 3)
            self.min_score = config.model_kwargs.get("min_score", 0.5)
        else:
            self.max_depth = 5
            self.beam_width = 3
            self.min_score = 0.5
        self.root: ThoughtNode | None = None
        self.best_path: list[str] = []

    async def process(
        self, input_data: dict[str, Any], context: dict[str, Any] | None = None
    ) -> AgentResponse:
        """Process input using Tree of Thoughts reasoning.

        Args:
            input_data: Input data to process
            context: Optional context information

        Returns:
            Agent's response with metadata
        """
        context = context or {}
        self.best_path = []

        try:
            # Initialize root thought
            message = input_data["message"]
            root = ThoughtNode(thought="Initial problem: " + message, score=1.0)
            self.root = root

            # Explore thought tree
            best_node = await self._explore_thoughts(root, context)

            # Extract best path
            current: ThoughtNode | None = best_node
            while current:
                self.best_path.insert(0, current.thought)
                current = current.parent

            return AgentResponse(
                text=best_node.thought,
                metadata={
                    "thought_path": self.best_path,
                    "final_score": best_node.score,
                    "tree_depth": best_node.depth,
                    "paths_explored": len(self.best_path),
                },
            )

        except Exception as e:
            return AgentResponse(
                text=f"Error in Tree of Thoughts processing: {e!s}",
                metadata={"thought_path": self.best_path, "error": str(e)},
            )

    async def process_stream(
        self, input_data: dict[str, Any], context: dict[str, Any] | None = None
    ) -> AsyncIterator[str]:
        """Process input and stream responses.

        Args:
            input_data: Input data to process
            context: Optional context information

        Returns:
            Async iterator of response chunks
        """
        context = context or {}
        self.best_path = []

        try:
            # Initialize root thought
            message = input_data["message"]
            yield "Initializing thought tree...\n"
            root = ThoughtNode(thought="Initial problem: " + message, score=1.0)
            self.root = root

            # Explore thought tree
            yield "Exploring possible solution paths...\n"

            async def stream_progress(msg: str) -> AsyncGenerator[str, None]:
                yield msg

            best_node = await self._explore_thoughts(root, context, stream_progress)

            # Extract best path
            yield "\nBest solution path found:\n"
            current: ThoughtNode | None = best_node
            while current:
                self.best_path.insert(0, current.thought)
                yield f"- {current.thought} (score: {current.score:.2f})\n"
                current = current.parent

        except Exception as e:
            yield f"Error in Tree of Thoughts processing: {e!s}"

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.root = None
        self.best_path = []

    async def _explore_thoughts(
        self,
        root: ThoughtNode,
        context: dict[str, Any],
        stream_handler: Callable[[str], AsyncGenerator[str, None]] | None = None,
    ) -> ThoughtNode:
        """Explore thought tree using beam search.

        Args:
            root: Root thought node
            context: Current context
            stream_handler: Optional handler for streaming progress

        Returns:
            Best leaf node found
        """
        # Priority queue for beam search
        beam: list[tuple[float, ThoughtNode]] = [(root.score, root)]
        heapq.heapify(beam)

        # Track visited thoughts to avoid cycles
        visited: set[str] = {root.thought}

        # Track best node seen
        best_node = root

        while beam and len(beam) <= self.beam_width * self.max_depth:
            # Get most promising node
            score, node = heapq.heappop(beam)

            if stream_handler:
                message = f"Exploring: {node.thought} (score: {score:.2f})\n"
                async for _ in stream_handler(message):
                    pass

            # Stop if we've reached max depth
            if node.depth >= self.max_depth:
                continue

            # Generate new thoughts
            new_thoughts = await self._generate_thoughts(node.thought, context)

            # Evaluate and add valid thoughts
            for thought in new_thoughts:
                if thought in visited:
                    continue

                visited.add(thought)
                score = await self._evaluate_thought(thought, context)

                if score >= self.min_score:
                    child = ThoughtNode(
                        thought=thought, score=score, parent=node, depth=node.depth + 1
                    )
                    node.children.append(child)
                    heapq.heappush(beam, (score, child))

                    if score > best_node.score:
                        best_node = child
                        if stream_handler:
                            message = f"New best: {thought} (score: {score:.2f})\n"
                            async for _ in stream_handler(message):
                                pass

        return best_node

    async def _generate_thoughts(
        self, current_thought: str, context: dict[str, Any]
    ) -> list[str]:
        """Generate next possible thoughts.

        Args:
            current_thought: Current thought to expand from
            context: Current context

        Returns:
            List of possible next thoughts
        """
        # TODO: Implement more sophisticated thought generation
        # For now, return simple variations
        thoughts = [
            f"Consider alternative: {current_thought}",
            f"What if we try: {current_thought}",
            f"Another approach: {current_thought}",
        ]
        return thoughts

    async def _evaluate_thought(self, thought: str, context: dict[str, Any]) -> float:
        """Evaluate quality of a thought.

        Args:
            thought: Thought to evaluate
            context: Current context

        Returns:
            Score between 0 and 1
        """
        # TODO: Implement more sophisticated evaluation
        # For now, use simple heuristic based on length and keywords
        score = 0.5  # Base score

        # Longer thoughts might be more detailed
        score += min(len(thought) / 200, 0.2)  # Up to 0.2 for length

        # Analytical keywords suggest better reasoning
        keywords = ["because", "therefore", "however", "consider", "analyze"]
        score += sum(
            0.1 for word in keywords if word in thought.lower()
        )  # Up to 0.5 for keywords

        return min(score, 1.0)  # Cap at 1.0
