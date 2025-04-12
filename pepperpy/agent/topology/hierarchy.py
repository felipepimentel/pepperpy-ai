"""
Hierarchy Topology.

Implements a hierarchical agent topology where agents are organized in a
tree-like structure with managers overseeing workers.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from pepperpy.agent.base import BaseAgentProvider
from pepperpy.core.logging import get_logger

from .base import AgentTopologyProvider, TopologyError

logger = get_logger(__name__)


class HierarchyTopology(AgentTopologyProvider):
    """Hierarchy topology implementation.
    
    This topology follows a tree-like structure where agents are organized
    in a management hierarchy, with higher-level agents delegating work to
    and synthesizing results from lower-level agents.
    
    Hierarchy topologies are suitable for:
    - Complex tasks requiring decomposition
    - Multi-step reasoning processes
    - Management of specialized worker agents
    - Division of labor across expertise domains
    
    Configuration:
        hierarchy_structure: Dict mapping agent IDs to their reports
        root_agent: ID of the agent at the top of the hierarchy
        max_iterations: Maximum number of task delegation iterations
        agents: Dict of agent configurations by ID
    """

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        """Initialize hierarchy topology.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.max_iterations = self.config.get("max_iterations", 10)
        self.hierarchy_structure: Dict[str, List[str]] = self.config.get("hierarchy_structure", {})
        self.root_agent = self.config.get("root_agent", None)
        
        # Initialize internal state
        self.parent_map: Dict[str, str] = {}  # child_id -> parent_id
        self.level_map: Dict[str, int] = {}  # agent_id -> hierarchy level
        
    async def initialize(self) -> None:
        """Initialize topology resources."""
        if self.initialized:
            return
        
        try:
            # Create and initialize configured agents
            for agent_id, agent_config in self.agent_configs.items():
                from pepperpy.agent import create_agent
                
                agent = create_agent(**agent_config)
                await self.add_agent(agent_id, agent)
            
            # Build hierarchy maps
            await self._build_hierarchy_maps()
            
            self.initialized = True
            logger.info(f"Initialized hierarchy topology with {len(self.agents)} agents")
        except Exception as e:
            logger.error(f"Failed to initialize hierarchy topology: {e}")
            await self.cleanup()
            raise TopologyError(f"Initialization failed: {e}") from e

    async def _build_hierarchy_maps(self) -> None:
        """Build parent and level maps from hierarchy structure."""
        self.parent_map = {}
        self.level_map = {}
        
        # Find root agent if not specified
        if not self.root_agent:
            all_children = set()
            for children in self.hierarchy_structure.values():
                all_children.update(children)
            
            possible_roots = set(self.agents.keys()) - all_children
            if not possible_roots:
                if self.agents:
                    # If no clear root, use first agent
                    self.root_agent = next(iter(self.agents.keys()))
                    logger.warning(f"No root agent found, using {self.root_agent} as root")
                else:
                    raise TopologyError("No agents configured")
            else:
                self.root_agent = next(iter(possible_roots))
                logger.info(f"Found root agent: {self.root_agent}")
        
        # Start with root at level 0
        if self.root_agent:
            self.level_map[self.root_agent] = 0
            
        # Build parent map and assign levels
        for parent_id, children in self.hierarchy_structure.items():
            parent_level = self.level_map.get(parent_id, 0)
            
            for child_id in children:
                if child_id in self.agents:
                    self.parent_map[child_id] = parent_id
                    self.level_map[child_id] = parent_level + 1

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.parent_map = {}
        self.level_map = {}
        await super().cleanup()

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the hierarchy topology with input data.
        
        Args:
            input_data: Input containing task details
            
        Returns:
            Execution results
        """
        if not self.initialized:
            await self.initialize()
            
        # Extract input task
        task = input_data.get("task", "")
        if not task:
            raise TopologyError("No task provided in input data")
            
        # Validate hierarchy
        if not self.root_agent or self.root_agent not in self.agents:
            raise TopologyError(f"Root agent {self.root_agent} not available")
            
        # Execute hierarchical process
        try:
            return await self._execute_hierarchical_process(task, input_data)
        except Exception as e:
            logger.error(f"Error in hierarchical process: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to complete hierarchical process"
            }

    async def _execute_hierarchical_process(
        self, task: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the hierarchical process for the given task.
        
        Args:
            task: Task description
            input_data: Full input data
            
        Returns:
            Process results
        """
        # Track delegation and results
        delegation_chain: List[Dict[str, Any]] = []
        agent_results: Dict[str, str] = {}
        
        # Start with root agent
        current_task = task
        current_agent_id = self.root_agent
        current_level = 0
        max_level = max(self.level_map.values()) if self.level_map else 0
        
        # Delegation phase - move down the hierarchy
        while current_level < max_level:
            # Get the current agent and its direct reports
            current_agent = self.agents[current_agent_id]
            direct_reports = self.hierarchy_structure.get(current_agent_id, [])
            
            if not direct_reports:
                # This is a leaf agent, process task directly
                break
                
            # Create delegation prompt
            delegation_prompt = (
                f"You are a manager with these direct reports: {', '.join(direct_reports)}\n\n"
                f"TASK: {current_task}\n\n"
                f"Break down this task for delegation. For each subtask, specify:\n"
                f"1. ASSIGNEE: [agent_id] (choose from your direct reports)\n"
                f"2. SUBTASK: [description]\n\n"
                f"Provide one or more subtask assignments."
            )
            
            # Process delegation
            try:
                delegation_response = await current_agent.process_message(delegation_prompt)
                
                # Record delegation
                delegation_chain.append({
                    "agent_id": current_agent_id,
                    "level": current_level,
                    "task": current_task,
                    "response": delegation_response
                })
                
                # Extract delegations
                delegations = self._parse_delegations(delegation_response, direct_reports)
                
                # If no valid delegations, treat as leaf agent
                if not delegations:
                    break
                    
                # Process delegations in parallel
                for assignee_id, subtask in delegations:
                    # Record delegation
                    delegation_chain.append({
                        "agent_id": current_agent_id,
                        "delegated_to": assignee_id,
                        "subtask": subtask
                    })
                    
                    # Process subtask
                    subtask_result = await self._process_leaf_task(assignee_id, subtask)
                    agent_results[assignee_id] = subtask_result
                
                # Prepare for next level - aggregation
                current_task = self._format_results_for_aggregation(
                    current_task, delegations, agent_results
                )
                current_level = max_level  # Jump to aggregation phase
            except Exception as e:
                logger.error(f"Error in delegation by {current_agent_id}: {e}")
                current_level = max_level  # Skip to aggregation
                delegation_chain.append({
                    "agent_id": current_agent_id,
                    "error": str(e)
                })
        
        # If reached a leaf node directly
        if current_level < max_level:
            try:
                # Process task directly
                leaf_result = await self._process_leaf_task(current_agent_id, current_task)
                agent_results[current_agent_id] = leaf_result
                
                delegation_chain.append({
                    "agent_id": current_agent_id,
                    "level": current_level,
                    "task": current_task,
                    "result": leaf_result
                })
                
                # Set the current task to this result for any aggregation
                current_task = leaf_result
            except Exception as e:
                logger.error(f"Error processing leaf task by {current_agent_id}: {e}")
                delegation_chain.append({
                    "agent_id": current_agent_id,
                    "error": str(e)
                })
        
        # Aggregation phase - move up the hierarchy
        current_agent_id = self.root_agent
        aggregation_result = await self._aggregate_results(
            current_agent_id, task, agent_results
        )
        
        # Return final result
        return {
            "status": "complete",
            "result": aggregation_result,
            "delegation_chain": delegation_chain,
            "agent_results": agent_results
        }

    def _parse_delegations(
        self, delegation_text: str, valid_assignees: List[str]
    ) -> List[Tuple[str, str]]:
        """Parse delegations from text.
        
        Args:
            delegation_text: Delegation response text
            valid_assignees: List of valid assignee IDs
            
        Returns:
            List of (assignee_id, subtask) tuples
        """
        delegations = []
        lines = delegation_text.split("\n")
        
        current_assignee = None
        current_subtask = ""
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
                
            # Look for assignee marker
            if "ASSIGNEE:" in line:
                # Save previous delegation if exists
                if current_assignee and current_subtask:
                    delegations.append((current_assignee, current_subtask.strip()))
                
                # Extract new assignee
                parts = line.split("ASSIGNEE:", 1)[1].strip()
                for assignee in valid_assignees:
                    if assignee in parts:
                        current_assignee = assignee
                        current_subtask = ""
                        break
                else:
                    current_assignee = None
                    
            # Look for subtask marker
            elif "SUBTASK:" in line and current_assignee:
                current_subtask = line.split("SUBTASK:", 1)[1].strip()
                
            # Continue building subtask
            elif current_assignee and current_subtask:
                current_subtask += "\n" + line
        
        # Add final delegation if exists
        if current_assignee and current_subtask:
            delegations.append((current_assignee, current_subtask.strip()))
            
        return delegations

    async def _process_leaf_task(self, agent_id: str, task: str) -> str:
        """Process a task at a leaf node.
        
        Args:
            agent_id: Agent ID to process the task
            task: Task description
            
        Returns:
            Task result
        """
        if agent_id not in self.agents:
            raise TopologyError(f"Agent {agent_id} not found")
            
        agent = self.agents[agent_id]
        
        # Create leaf task prompt
        leaf_prompt = (
            f"You are a specialist assigned this task directly:\n\n"
            f"{task}\n\n"
            f"Complete this task in detail. Your response will be used "
            f"as part of a larger solution."
        )
        
        return await agent.process_message(leaf_prompt)

    def _format_results_for_aggregation(
        self, original_task: str, delegations: List[Tuple[str, str]], 
        results: Dict[str, str]
    ) -> str:
        """Format results for aggregation.
        
        Args:
            original_task: Original task description
            delegations: List of delegations
            results: Dict mapping agent IDs to results
            
        Returns:
            Formatted results text
        """
        formatted = [
            f"ORIGINAL TASK: {original_task}\n",
            "SUBTASK RESULTS:"
        ]
        
        for assignee_id, subtask in delegations:
            result = results.get(assignee_id, "No result")
            formatted.append(
                f"AGENT {assignee_id}:\n"
                f"SUBTASK: {subtask}\n"
                f"RESULT: {result}\n"
            )
            
        return "\n\n".join(formatted)

    async def _aggregate_results(
        self, agent_id: str, original_task: str, results: Dict[str, str]
    ) -> str:
        """Aggregate results at manager level.
        
        Args:
            agent_id: Agent ID to perform aggregation
            original_task: Original task description
            results: Dict mapping agent IDs to results
            
        Returns:
            Aggregated result
        """
        if agent_id not in self.agents:
            raise TopologyError(f"Agent {agent_id} not found")
            
        agent = self.agents[agent_id]
        
        # Get direct reports and their results
        direct_reports = self.hierarchy_structure.get(agent_id, [])
        report_results = []
        
        for report_id in direct_reports:
            if report_id in results:
                report_results.append(
                    f"AGENT {report_id}:\n{results[report_id]}"
                )
        
        # Create aggregation prompt
        if report_results:
            aggregation_prompt = (
                f"You are synthesizing results from your team.\n\n"
                f"ORIGINAL TASK: {original_task}\n\n"
                f"TEAM RESULTS:\n\n" + 
                "\n\n".join(report_results) + 
                "\n\nSynthesize these results into a coherent, comprehensive solution."
            )
        else:
            # If no report results, process task directly
            aggregation_prompt = (
                f"Complete this task directly:\n\n{original_task}"
            )
        
        return await agent.process_message(aggregation_prompt)

    async def add_reporting_relationship(
        self, manager_id: str, report_id: str
    ) -> None:
        """Add a reporting relationship.
        
        Args:
            manager_id: Manager agent ID
            report_id: Direct report agent ID
            
        Raises:
            TopologyError: If agents don't exist
        """
        if manager_id not in self.agents:
            raise TopologyError(f"Manager agent {manager_id} does not exist")
            
        if report_id not in self.agents:
            raise TopologyError(f"Report agent {report_id} does not exist")
            
        # Add to hierarchy structure
        if manager_id in self.hierarchy_structure:
            if report_id not in self.hierarchy_structure[manager_id]:
                self.hierarchy_structure[manager_id].append(report_id)
        else:
            self.hierarchy_structure[manager_id] = [report_id]
            
        # Update parent and level maps
        self.parent_map[report_id] = manager_id
        manager_level = self.level_map.get(manager_id, 0)
        self.level_map[report_id] = manager_level + 1
        
        logger.debug(f"Added reporting relationship: {report_id} -> {manager_id}")

    async def remove_reporting_relationship(
        self, manager_id: str, report_id: str
    ) -> None:
        """Remove a reporting relationship.
        
        Args:
            manager_id: Manager agent ID
            report_id: Direct report agent ID
        """
        if (manager_id in self.hierarchy_structure and 
            report_id in self.hierarchy_structure[manager_id]):
            self.hierarchy_structure[manager_id].remove(report_id)
            
            # Remove empty lists
            if not self.hierarchy_structure[manager_id]:
                del self.hierarchy_structure[manager_id]
                
            # Update parent and level maps
            if self.parent_map.get(report_id) == manager_id:
                del self.parent_map[report_id]
                if report_id in self.level_map:
                    del self.level_map[report_id]
                    
            logger.debug(f"Removed reporting relationship: {report_id} -> {manager_id}")

    async def get_hierarchy(self) -> Dict[str, Any]:
        """Get the current hierarchy structure.
        
        Returns:
            Dict containing hierarchy information
        """
        return {
            "structure": self.hierarchy_structure,
            "root": self.root_agent,
            "levels": self.level_map
        } 