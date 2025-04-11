"""Decision-making agent implementation.

This module implements a sophisticated decision-making agent that can weigh options,
make decisions, and adjust strategies dynamically based on feedback.
"""

from typing import Dict, List, Any, Optional, Tuple, Set, Union, cast
import asyncio
import json
import logging
from datetime import datetime
import random
from dataclasses import dataclass, field

from .base import (
    BaseAgent, Agent, AgentId, TaskId, AgentStatus, AgentConfig,
    AgentContext, AgentMemory, Task, TaskResult, DecisionStrategy,
    AgentCapability, AgentRole
)

logger = logging.getLogger(__name__)

@dataclass
class DecisionCriteria:
    """Criteria for making decisions."""
    name: str
    weight: float
    description: str


@dataclass
class Option:
    """Option for a decision."""
    id: str
    name: str
    description: str
    scores: Dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0


@dataclass
class Decision:
    """Decision made by the agent."""
    task_id: str
    options: List[Option]
    selected_option: Option
    criteria: List[DecisionCriteria]
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DecisionResult(TaskResult):
    """Result of a decision task."""
    success: bool
    output: Any
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    alternatives: List[Option] = field(default_factory=list)


class DecisionAgent(BaseAgent):
    """Agent specialized in making sophisticated decisions."""
    
    def __init__(
        self,
        agent_id: AgentId,
        config: AgentConfig,
        context: AgentContext,
        memory: AgentMemory,
        tools: Optional[Dict[str, Any]] = None,
        model_providers: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a decision agent.
        
        Args:
            agent_id: Unique identifier for the agent
            config: Configuration for the agent
            context: Context in which the agent operates
            memory: Memory for the agent
            tools: Tools available to the agent
            model_providers: Model providers available to the agent
        """
        super().__init__(
            agent_id=agent_id,
            config=config,
            context=context,
            memory=memory,
            tools=tools,
            model_providers=model_providers,
        )
        
        # Decision-specific attributes
        self.decision_history: List[Decision] = []
        self.feedback_history: Dict[str, Any] = {}
        self.default_criteria: List[DecisionCriteria] = [
            DecisionCriteria(
                name="feasibility",
                weight=1.0,
                description="How feasible is this option to implement"
            ),
            DecisionCriteria(
                name="impact",
                weight=1.0,
                description="What impact would this option have"
            ),
            DecisionCriteria(
                name="cost",
                weight=1.0,
                description="What is the cost of this option"
            ),
            DecisionCriteria(
                name="risk",
                weight=1.0,
                description="What risks are associated with this option"
            ),
        ]
    
    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a decision-making task.
        
        Args:
            task: Task to execute
            
        Returns:
            Result of executing the task
        """
        async with self._lock:
            self.status = AgentStatus.BUSY
            start_time = datetime.now()
            
            try:
                # Parse task parameters
                parameters = task.metadata.get("parameters", {})
                options = parameters.get("options", [])
                criteria = parameters.get("criteria", None)
                
                if not options:
                    raise ValueError("No options provided for decision task")
                
                # Use provided criteria or defaults
                decision_criteria = await self._load_criteria(criteria)
                
                # Make the decision
                decision = await self._make_decision(
                    task_id=task.task_id,
                    options=options,
                    criteria=decision_criteria
                )
                
                # Store the decision in memory and history
                await self.memory.add(f"decision_{task.task_id}", decision)
                self.decision_history.append(decision)
                
                # Create result
                result = DecisionResult(
                    success=True,
                    output=decision.selected_option,
                    confidence=decision.confidence,
                    alternatives=[o for o in decision.options if o != decision.selected_option],
                    metrics={
                        "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                        "options_evaluated": len(options),
                        "confidence": decision.confidence,
                    }
                )
                
                # Update metrics
                self._update_metrics(start_time, True)
                
                return result
            except Exception as e:
                logger.error(f"Error executing decision task: {e}")
                self._update_metrics(start_time, False)
                return DecisionResult(
                    success=False,
                    output=None,
                    error=str(e),
                    metrics={
                        "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    }
                )
            finally:
                self.status = AgentStatus.IDLE
    
    async def plan_tasks(self, objective: str) -> List[Task]:
        """Plan tasks to achieve an objective.
        
        Args:
            objective: Objective to achieve
            
        Returns:
            List of tasks to achieve the objective
        """
        # This would typically involve breaking down an objective into sub-tasks
        # For simplicity, we return a single task here
        task_id = f"task_{len(self.task_history) + 1}"
        return [Task(task_id=task_id, description=objective)]
    
    async def collaborate(self, agent_id: AgentId, message: Any) -> Any:
        """Collaborate with another agent.
        
        Args:
            agent_id: ID of the agent to collaborate with
            message: Message to send to the agent
            
        Returns:
            Response from the agent
        """
        # This would involve passing messages between agents
        # For simplicity, we echo the message
        return {
            "status": "received",
            "from": self.agent_id,
            "to": agent_id,
            "response": f"Received message: {message}"
        }
    
    async def learn_from_feedback(self, feedback: Any) -> None:
        """Learn from user feedback to improve decision making.
        
        Args:
            feedback: User feedback, including decision_id and rating
        """
        if not isinstance(feedback, dict):
            raise ValueError("Feedback must be a dictionary")
        
        decision_id = feedback.get("decision_id")
        rating = feedback.get("rating")
        comments = feedback.get("comments", "")
        
        if not decision_id or rating is None:
            raise ValueError("Feedback must include decision_id and rating")
        
        # Store feedback
        self.feedback_history[decision_id] = {
            "rating": rating,
            "comments": comments,
            "timestamp": datetime.now().isoformat()
        }
        
        # Adjust criteria weights based on feedback
        await self._adjust_criteria_weights(decision_id, rating, comments)
    
    async def _load_criteria(
        self,
        criteria: Optional[List[Dict[str, Any]]] = None
    ) -> List[DecisionCriteria]:
        """Load decision criteria.
        
        Args:
            criteria: Criteria to load, or None to use defaults
            
        Returns:
            Loaded criteria
        """
        if not criteria:
            # Use default criteria
            return self.default_criteria.copy()
        
        # Convert to DecisionCriteria objects
        return [
            DecisionCriteria(
                name=c.get("name", f"criterion_{i}"),
                weight=float(c.get("weight", 1.0)),
                description=c.get("description", "")
            )
            for i, c in enumerate(criteria)
        ]
    
    async def _make_decision(
        self,
        task_id: str,
        options: List[Dict[str, Any]],
        criteria: List[DecisionCriteria]
    ) -> Decision:
        """Make a decision.
        
        Args:
            task_id: ID of the task
            options: Options to choose from
            criteria: Criteria to use for evaluation
            
        Returns:
            Decision made
        """
        # Convert options to Option objects
        option_objects = [
            Option(
                id=str(i),
                name=o.get("name", f"option_{i}"),
                description=o.get("description", "")
            )
            for i, o in enumerate(options)
        ]
        
        # Compute scores for each option based on the decision strategy
        if self.config.decision_strategy == DecisionStrategy.RULE_BASED:
            await self._evaluate_rule_based(option_objects, criteria)
        elif self.config.decision_strategy == DecisionStrategy.UTILITY_BASED:
            await self._evaluate_utility_based(option_objects, criteria)
        elif self.config.decision_strategy == DecisionStrategy.GOAL_ORIENTED:
            await self._evaluate_goal_oriented(option_objects, criteria)
        elif self.config.decision_strategy == DecisionStrategy.MULTI_MODEL_CONSENSUS:
            await self._evaluate_multi_model_consensus(option_objects, criteria)
        else:
            # Fallback to utility-based
            await self._evaluate_utility_based(option_objects, criteria)
        
        # Select the option with the highest score
        selected_option = max(option_objects, key=lambda o: o.total_score)
        
        # Compute confidence based on the difference between the top scores
        if len(option_objects) > 1:
            sorted_options = sorted(option_objects, key=lambda o: o.total_score, reverse=True)
            top_score = sorted_options[0].total_score
            second_score = sorted_options[1].total_score
            score_diff = top_score - second_score
            confidence = min(1.0, max(0.5, 0.5 + score_diff))
        else:
            confidence = 1.0
        
        # Generate reasoning
        reasoning = self._generate_reasoning(selected_option, option_objects, criteria)
        
        return Decision(
            task_id=task_id,
            options=option_objects,
            selected_option=selected_option,
            criteria=criteria,
            confidence=confidence,
            reasoning=reasoning
        )
    
    async def _evaluate_rule_based(
        self,
        options: List[Option],
        criteria: List[DecisionCriteria]
    ) -> None:
        """Evaluate options using rule-based decision making.
        
        Args:
            options: Options to evaluate
            criteria: Criteria to use for evaluation
        """
        # In a real implementation, this would apply predefined rules
        # For simplicity, we use random scores
        for option in options:
            for criterion in criteria:
                # In a real implementation, this would be determined by rules
                option.scores[criterion.name] = random.uniform(0.0, 1.0)
            
            # Compute total score
            option.total_score = sum(
                option.scores[c.name] * c.weight for c in criteria
            ) / sum(c.weight for c in criteria)
    
    async def _evaluate_utility_based(
        self,
        options: List[Option],
        criteria: List[DecisionCriteria]
    ) -> None:
        """Evaluate options using utility-based decision making.
        
        Args:
            options: Options to evaluate
            criteria: Criteria to use for evaluation
        """
        # In a real implementation, this would compute utility scores
        # For simplicity, we use random scores
        for option in options:
            for criterion in criteria:
                # In a real implementation, this would be determined by utility functions
                option.scores[criterion.name] = random.uniform(0.0, 1.0)
            
            # Compute total score
            option.total_score = sum(
                option.scores[c.name] * c.weight for c in criteria
            ) / sum(c.weight for c in criteria)
    
    async def _evaluate_goal_oriented(
        self,
        options: List[Option],
        criteria: List[DecisionCriteria]
    ) -> None:
        """Evaluate options using goal-oriented decision making.
        
        Args:
            options: Options to evaluate
            criteria: Criteria to use for evaluation
        """
        # In a real implementation, this would evaluate options against goals
        # For simplicity, we use random scores
        for option in options:
            for criterion in criteria:
                # In a real implementation, this would be determined by goal alignment
                option.scores[criterion.name] = random.uniform(0.0, 1.0)
            
            # Compute total score
            option.total_score = sum(
                option.scores[c.name] * c.weight for c in criteria
            ) / sum(c.weight for c in criteria)
    
    async def _evaluate_multi_model_consensus(
        self,
        options: List[Option],
        criteria: List[DecisionCriteria]
    ) -> None:
        """Evaluate options using multi-model consensus.
        
        Args:
            options: Options to evaluate
            criteria: Criteria to use for evaluation
        """
        # In a real implementation, this would query multiple models
        # For simplicity, we use random scores
        
        # Simulate results from multiple models
        model_results = []
        for _ in range(3):  # Simulate 3 models
            model_scores = {}
            for option in options:
                option_scores = {}
                for criterion in criteria:
                    option_scores[criterion.name] = random.uniform(0.0, 1.0)
                model_scores[option.id] = option_scores
            model_results.append(model_scores)
        
        # Aggregate scores
        for option in options:
            for criterion in criteria:
                # Average scores across models
                scores = [model[option.id][criterion.name] for model in model_results]
                option.scores[criterion.name] = sum(scores) / len(scores)
            
            # Compute total score
            option.total_score = sum(
                option.scores[c.name] * c.weight for c in criteria
            ) / sum(c.weight for c in criteria)
    
    def _generate_reasoning(
        self,
        selected_option: Option,
        options: List[Option],
        criteria: List[DecisionCriteria]
    ) -> str:
        """Generate reasoning for a decision.
        
        Args:
            selected_option: Selected option
            options: All options
            criteria: Criteria used for evaluation
            
        Returns:
            Reasoning for the decision
        """
        # In a real implementation, this would generate natural language reasoning
        # For simplicity, we use a template
        reasons = []
        for criterion in criteria:
            score = selected_option.scores.get(criterion.name, 0.0)
            reason = f"{criterion.name.capitalize()}: {score:.2f}"
            reasons.append(reason)
        
        return f"Selected {selected_option.name} based on the following scores: {', '.join(reasons)}"
    
    async def _adjust_criteria_weights(
        self,
        decision_id: str,
        rating: float,
        comments: str
    ) -> None:
        """Adjust criteria weights based on feedback.
        
        Args:
            decision_id: ID of the decision
            rating: Rating (0-1)
            comments: Comments
        """
        # Find the decision
        decision = next((d for d in self.decision_history if d.task_id == decision_id), None)
        if not decision:
            logger.warning(f"Decision {decision_id} not found")
            return
        
        # Adjust weights based on rating
        # In a real implementation, this would use more sophisticated learning
        adjustment = (rating - 0.5) * 0.1  # Small adjustment
        for criterion in self.default_criteria:
            # Find corresponding criterion in the decision
            decision_criterion = next((c for c in decision.criteria if c.name == criterion.name), None)
            if decision_criterion:
                criterion.weight = max(0.1, min(2.0, criterion.weight + adjustment))
        
        logger.info(f"Adjusted criteria weights: {self.default_criteria}")


def create_decision_agent(
    agent_id: str,
    decision_strategy: DecisionStrategy = DecisionStrategy.UTILITY_BASED,
    **kwargs: Any
) -> DecisionAgent:
    """Create a decision agent.
    
    Args:
        agent_id: ID for the agent
        decision_strategy: Strategy for decision making
        **kwargs: Additional arguments
        
    Returns:
        Created agent
    """
    # Create configuration
    config = AgentConfig(
        name="decision_agent",
        capabilities=[
            AgentCapability.DECISION_MAKING,
            AgentCapability.TASK_PLANNING
        ],
        role=AgentRole.SPECIALIST,
        decision_strategy=decision_strategy,
        model_providers=kwargs.get("model_providers", ["default"]),
        tools=kwargs.get("tools", []),
        max_tokens=kwargs.get("max_tokens", 4000),
        temperature=kwargs.get("temperature", 0.7),
        custom_settings=kwargs.get("custom_settings", {})
    )
    
    # Create context
    context = AgentContext(
        session_id=kwargs.get("session_id", "default"),
        user_id=kwargs.get("user_id", None),
        environment_variables=kwargs.get("environment_variables", {}),
        metadata=kwargs.get("metadata", {})
    )
    
    # Create memory
    from .memory import SimpleMemory
    memory = SimpleMemory()
    
    # Create agent
    return DecisionAgent(
        agent_id=agent_id,
        config=config,
        context=context,
        memory=memory,
        tools=kwargs.get("tools", {}),
        model_providers=kwargs.get("model_providers", {})
    ) 