"""
Teamwork Topology Provider.

Implements a collaborative agent topology where agents work together
as a team to solve complex problems through deliberation and consensus.
"""

from typing import Any

from pepperpy.agent.topology.base import AgentTopologyProvider, TopologyError
from pepperpy.core.logging import get_logger
from pepperpy.plugin import ProviderPlugin

logger = get_logger(__name__)


class TeamworkTopologyProvider(AgentTopologyProvider, ProviderPlugin):
    """Teamwork topology provider.

    Implements a collaborative approach to agent coordination where agents
    function as a team, sharing insights and building consensus through
    deliberation and voting.

    This topology is suitable for:
    - Tasks requiring multiple perspectives
    - Complex decision-making processes
    - Avoiding individual agent biases
    - Solving problems through deliberation

    Configuration:
        team_leader: ID of the agent serving as team leader
        voting_threshold: Threshold for consensus (0.0-1.0)
        max_iterations: Maximum iterations for deliberation
        consensus_required: Whether full consensus is needed
        agent_roles: Role definitions for each agent
    """

    # Type-annotated config attributes
    team_leader: str | None = None
    voting_threshold: float = 0.6
    max_iterations: int = 10
    consensus_required: bool = True

    async def initialize(self) -> None:
        """Initialize topology resources."""
        if self.initialized:
            return

        try:
            # Create and initialize configured agents
            for agent_id, agent_config in self.agent_configs.items():
                from pepperpy.agent import create_agent

                # Inject role information if available
                if hasattr(self, "agent_roles") and agent_id in self.agent_roles:
                    role_info = self.agent_roles[agent_id]
                    if isinstance(agent_config, dict):
                        agent_config["role"] = role_info

                agent = create_agent(**agent_config)
                await self.add_agent(agent_id, agent)

            self.initialized = True
            logger.info(f"Initialized teamwork topology with {len(self.agents)} agents")

            # Auto-assign team leader if not specified
            if not self.team_leader and self.agents:
                self.team_leader = next(iter(self.agents.keys()))
                logger.info(f"Auto-assigned team leader: {self.team_leader}")

        except Exception as e:
            logger.error(f"Failed to initialize teamwork topology: {e}")
            await self.cleanup()
            raise TopologyError(f"Initialization failed: {e}") from e

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the teamwork topology with input data.

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

        # Validate team configuration
        if not self.agents:
            raise TopologyError("No agents configured for teamwork")

        if self.team_leader and self.team_leader not in self.agents:
            raise TopologyError(f"Team leader {self.team_leader} not found in agents")

        # Execute teamwork process
        try:
            return await self._execute_teamwork_process(task, input_data)
        except Exception as e:
            logger.error(f"Error in teamwork process: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to complete teamwork process",
            }

    async def _execute_teamwork_process(
        self, task: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute the teamwork process for the given task.

        Args:
            task: Task description
            input_data: Full input data

        Returns:
            Process results
        """
        # Track deliberation details
        deliberation: list[dict[str, Any]] = []

        # Stage 1: Initial task analysis by team leader
        analysis = await self._get_leader_analysis(task)
        deliberation.append({
            "stage": "analysis",
            "agent": self.team_leader,
            "content": analysis,
        })

        # Stage in 2: Individual perspectives from team members
        perspectives = await self._get_team_perspectives(task, analysis)
        for agent_id, perspective in perspectives.items():
            deliberation.append({
                "stage": "perspective",
                "agent": agent_id,
                "content": perspective,
            })

        # Stage 3: Iterative deliberation
        proposal = analysis
        consensus = False
        iteration = 0

        while iteration < self.max_iterations and not consensus:
            iteration += 1

            # Generate new proposal
            proposal = await self._generate_proposal(proposal, perspectives)
            deliberation.append({
                "stage": f"proposal_{iteration}",
                "agent": self.team_leader,
                "content": proposal,
            })

            # Collect votes on proposal
            votes, comments = await self._collect_votes(proposal)
            vote_result = sum(votes.values()) / len(votes) if votes else 0

            for agent_id, comment in comments.items():
                deliberation.append({
                    "stage": f"feedback_{iteration}",
                    "agent": agent_id,
                    "vote": votes.get(agent_id, 0),
                    "content": comment,
                })

            # Check for consensus
            consensus = vote_result >= self.voting_threshold

            if self.consensus_required:
                # Full consensus requires all votes to be affirmative
                consensus = all(vote > 0 for vote in votes.values())

            # Break if we have consensus
            if consensus:
                break

            # Update perspectives based on comments
            perspectives = comments

        # Stage 4: Final solution
        status = "complete" if consensus else "partial"
        if iteration >= self.max_iterations and not consensus:
            status = "timeout"

        # Build result
        result = {
            "status": status,
            "iterations": iteration,
            "consensus_level": sum(votes.values()) / len(votes) if votes else 0,
            "solution": proposal,
            "deliberation": deliberation,
        }

        if status == "timeout":
            result["message"] = (
                f"Reached maximum iterations ({self.max_iterations}) without consensus"
            )

        return result

    async def _get_leader_analysis(self, task: str) -> str:
        """Get initial task analysis from team leader.

        Args:
            task: Task description

        Returns:
            Analysis text
        """
        if not self.team_leader or self.team_leader not in self.agents:
            # If no leader, use first agent
            leader_id = next(iter(self.agents.keys()))
        else:
            leader_id = self.team_leader

        leader = self.agents[leader_id]

        # Prepare leader prompt
        leader_prompt = (
            f"You are the team leader. Analyze this task thoroughly:\n\n"
            f"{task}\n\n"
            f"Provide a structured analysis with:\n"
            f"1. Task breakdown\n"
            f"2. Key challenges\n"
            f"3. Approach recommendation"
        )

        try:
            return await leader.process_message(leader_prompt)
        except Exception as e:
            logger.error(f"Error getting analysis from leader: {e}")
            return f"Error in analysis: {e}"

    async def _get_team_perspectives(self, task: str, analysis: str) -> dict[str, str]:
        """Get individual perspectives from team members.

        Args:
            task: Task description
            analysis: Leader's analysis

        Returns:
            Dict mapping agent IDs to their perspectives
        """
        perspectives: dict[str, str] = {}

        for agent_id, agent in self.agents.items():
            # Skip leader, we already have their analysis
            if agent_id == self.team_leader:
                continue

            # Get agent role if available
            role = "team member"
            if hasattr(self, "agent_roles") and agent_id in self.agent_roles:
                role = self.agent_roles[agent_id]

            # Prepare agent prompt
            prompt = (
                f"You are a {role} in the team.\n"
                f"TASK: {task}\n\n"
                f"LEADER ANALYSIS:\n{analysis}\n\n"
                f"Provide your perspective on this task based on your expertise. "
                f"Include:\n"
                f"1. Points you agree with\n"
                f"2. Additional insights\n"
                f"3. Any concerns or alternative approaches"
            )

            try:
                perspective = await agent.process_message(prompt)
                perspectives[agent_id] = perspective
            except Exception as e:
                logger.error(f"Error getting perspective from {agent_id}: {e}")
                perspectives[agent_id] = f"Error: {e}"

        return perspectives

    async def _generate_proposal(
        self, previous_proposal: str, perspectives: dict[str, str]
    ) -> str:
        """Generate a new proposal based on perspectives.

        Args:
            previous_proposal: Previous proposal text
            perspectives: Team member perspectives

        Returns:
            New proposal text
        """
        if not self.team_leader or self.team_leader not in self.agents:
            # If no leader, use first agent
            leader_id = next(iter(self.agents.keys()))
        else:
            leader_id = self.team_leader

        leader = self.agents[leader_id]

        # Format perspectives
        perspectives_text = "\n\n".join([
            f"AGENT {agent_id}:\n{perspective}"
            for agent_id, perspective in perspectives.items()
        ])

        # Prepare proposal prompt
        proposal_prompt = (
            f"You are synthesizing team input into a proposal.\n\n"
            f"PREVIOUS PROPOSAL:\n{previous_proposal}\n\n"
            f"TEAM FEEDBACK:\n{perspectives_text}\n\n"
            f"Synthesize this feedback into an improved proposal that "
            f"addresses the concerns and incorporates the insights from the team. "
            f"Create a clear, actionable proposal that the team can vote on."
        )

        try:
            return await leader.process_message(proposal_prompt)
        except Exception as e:
            logger.error(f"Error generating proposal: {e}")
            return f"Error in proposal: {e}"

    async def _collect_votes(
        self, proposal: str
    ) -> tuple[dict[str, float], dict[str, str]]:
        """Collect votes and comments on a proposal.

        Args:
            proposal: Proposal text

        Returns:
            Tuple of (votes, comments) where votes maps agent IDs to
            vote values (0.0-1.0) and comments maps agent IDs to feedback
        """
        votes: dict[str, float] = {}
        comments: dict[str, str] = {}

        for agent_id, agent in self.agents.items():
            # Get agent role if available
            role = "team member"
            if hasattr(self, "agent_roles") and agent_id in self.agent_roles:
                role = self.agent_roles[agent_id]

            # Prepare voting prompt
            vote_prompt = (
                f"You are a {role} in the team.\n\n"
                f"PROPOSAL:\n{proposal}\n\n"
                f"Evaluate this proposal and vote on it:\n"
                f"1. Give a score from 0.0 (reject) to 1.0 (fully approve)\n"
                f"2. Explain your vote with specific feedback\n\n"
                f"Start your response with 'VOTE: X.X' where X.X is your score."
            )

            try:
                response = await agent.process_message(vote_prompt)

                # Extract vote score
                vote_score = 0.0
                if "VOTE:" in response:
                    vote_parts = response.split("VOTE:", 1)[1].strip().split(None, 1)
                    if vote_parts:
                        try:
                            vote_score = float(vote_parts[0])
                            vote_score = max(0.0, min(1.0, vote_score))  # Clamp to 0-1
                        except ValueError:
                            pass

                # Store vote and comment
                votes[agent_id] = vote_score
                comments[agent_id] = response
            except Exception as e:
                logger.error(f"Error collecting vote from {agent_id}: {e}")
                votes[agent_id] = 0.0
                comments[agent_id] = f"Error: {e}"

        return votes, comments
