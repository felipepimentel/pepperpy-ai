"""
Federation Topology.

Implements a federation pattern where multiple agent systems can work together
across organizational boundaries while maintaining separation of concerns.
"""

from typing import Any

from pepperpy.agent.base import BaseAgentProvider
from pepperpy.core.logging import get_logger

from .base import AgentTopologyProvider, TopologyError

logger = get_logger(__name__)


class FederationTopology(AgentTopologyProvider):
    """Federation topology implementation.

    This topology implements a federation pattern where multiple autonomous agent
    systems (domains) can collaborate while maintaining their boundaries. Each
    domain operates with its own policies, agents, and possibly internal topology.

    Useful for:
    - Cross-organization agent collaboration
    - Systems with strong domain separation requirements
    - Building scalable and distributed agent ecosystems
    - Implementing organizational isolation with selective sharing

    Configuration:
        domains: Dict of domain configurations
        federation_policies: Dict of cross-domain communication policies
        shared_resources: List of resources available across domains
        authentication_required: Whether cross-domain calls require authentication
        agents: Dict of agent configurations by ID (for non-domain agents)
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize federation topology.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Federation configuration
        self.domains = self.config.get("domains", {})
        self.federation_policies = self.config.get("federation_policies", {})
        self.shared_resources = self.config.get("shared_resources", [])
        self.authentication_required = self.config.get("authentication_required", True)

        # Internal state
        self.domain_agents: dict[str, dict[str, BaseAgentProvider]] = {}
        self.domain_topologies: dict[str, AgentTopologyProvider] = {}
        self.federated_queries: list[dict[str, Any]] = []
        self.access_tokens: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize federation topology resources."""
        if self.initialized:
            return

        try:
            # Initialize each domain
            for domain_name, domain_config in self.domains.items():
                await self._initialize_domain(domain_name, domain_config)

            # Initialize non-domain agents (federation-level agents)
            for agent_id, agent_config in self.agent_configs.items():
                from pepperpy.agent import create_agent

                agent = create_agent(**agent_config)
                await self.add_agent(agent_id, agent)
                logger.debug(f"Initialized federation-level agent: {agent_id}")

            # Set up cross-domain communication policies
            await self._setup_federation_policies()

            self.initialized = True
            logger.info(
                f"Initialized federation topology with {len(self.domains)} domains"
            )

        except Exception as e:
            logger.error(f"Failed to initialize federation topology: {e}")
            await self.cleanup()
            raise TopologyError(f"Initialization failed: {e}") from e

    async def _initialize_domain(
        self, domain_name: str, domain_config: dict[str, Any]
    ) -> None:
        """Initialize a domain within the federation.

        Args:
            domain_name: Name of the domain
            domain_config: Domain configuration
        """
        logger.info(f"Initializing domain: {domain_name}")

        # Extract domain configuration
        topology_type = domain_config.get("topology_type", "orchestrator")
        topology_config = domain_config.get("topology_config", {})
        domain_agents = domain_config.get("agents", {})

        # Create the domain's topology
        from pepperpy.agent.topology.base import create_topology

        topology = create_topology(topology_type, **topology_config)
        await topology.initialize()

        # Store the domain topology
        self.domain_topologies[domain_name] = topology

        # Store domain's agents for reference
        self.domain_agents[domain_name] = {}
        for agent_id in domain_agents.keys():
            self.domain_agents[domain_name][agent_id] = topology.agents.get(agent_id)

        logger.debug(f"Domain {domain_name} initialized with topology {topology_type}")

    async def _setup_federation_policies(self) -> None:
        """Set up cross-domain communication policies."""
        logger.debug("Setting up federation policies")

        # Default policy (if not specified) is to disallow cross-domain communication
        default_policy = self.federation_policies.get("default", {"allow": False})

        # Process specific domain-to-domain policies
        domain_policies = self.federation_policies.get("domain_policies", {})

        for (source_domain, target_domain), policy in domain_policies.items():
            logger.debug(f"Policy {source_domain} -> {target_domain}: {policy}")

        # Setup authentication if required
        if self.authentication_required:
            await self._setup_authentication()

    async def _setup_authentication(self) -> None:
        """Set up cross-domain authentication."""
        logger.debug("Setting up cross-domain authentication")

        # Generate access tokens for each domain
        import secrets
        import time

        for domain_name in self.domains.keys():
            token = secrets.token_hex(16)
            expiry = time.time() + 86400  # 24 hours

            self.access_tokens[domain_name] = {"token": token, "expiry": expiry}

            logger.debug(f"Generated access token for domain: {domain_name}")

    async def cleanup(self) -> None:
        """Clean up federation topology resources."""
        logger.info("Cleaning up federation topology")

        # Clean up each domain topology
        for domain_name, topology in self.domain_topologies.items():
            try:
                await topology.cleanup()
                logger.debug(f"Cleaned up domain topology: {domain_name}")
            except Exception as e:
                logger.error(f"Error cleaning up domain {domain_name}: {e}")

        # Clear internal state
        self.domain_topologies = {}
        self.domain_agents = {}
        self.federated_queries = []
        self.access_tokens = {}

        # Clean up federation-level agents
        await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the federation topology with input data.

        Args:
            input_data: Input containing task, target domain/agent, and authentication

        Returns:
            Execution results
        """
        if not self.initialized:
            await self.initialize()

        # Extract execution parameters
        task = input_data.get("task", "")
        if not task:
            raise TopologyError("No task provided in input data")

        # Check if this is a federated query (cross-domain) or direct query
        if "domain" in input_data:
            # This is a domain-targeted query
            domain = input_data.get("domain")
            return await self._execute_domain_task(domain, input_data)
        elif "source_domain" in input_data and "target_domain" in input_data:
            # This is a cross-domain (federated) query
            return await self._execute_federated_task(input_data)
        elif "agent_id" in input_data:
            # This is a direct agent query (federation-level agent)
            agent_id = input_data.get("agent_id")
            return await self._execute_agent_task(agent_id, input_data)
        else:
            # Process federation-level task
            return await self._process_federation_task(input_data)

    async def _execute_domain_task(
        self, domain: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a task within a specific domain.

        Args:
            domain: Domain name
            input_data: Task input data

        Returns:
            Task result
        """
        if domain not in self.domain_topologies:
            raise TopologyError(f"Domain not found: {domain}")

        # Execute task using the domain's topology
        topology = self.domain_topologies[domain]

        # Prepare domain-specific input by removing federation-level keys
        domain_input = input_data.copy()
        domain_input.pop("domain", None)

        logger.info(
            f"Executing task in domain {domain}: {task[:50] if (task := domain_input.get('task')) else ''}"
        )
        result = await topology.execute(domain_input)

        # Add federation metadata
        result["federation_metadata"] = {
            "domain": domain,
            "timestamp": self._get_timestamp(),
            "query_id": f"dom_{len(self.federated_queries)}",
        }

        # Record the query
        self.federated_queries.append({
            "type": "domain_task",
            "domain": domain,
            "input": input_data,
            "timestamp": self._get_timestamp(),
            "result_status": result.get("status", "unknown"),
        })

        return result

    async def _execute_federated_task(
        self, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a cross-domain (federated) task.

        Args:
            input_data: Task input with source and target domains

        Returns:
            Task result with federation metadata
        """
        source_domain = input_data.get("source_domain")
        target_domain = input_data.get("target_domain")

        if not source_domain or not target_domain:
            raise TopologyError(
                "Source and target domains required for federated tasks"
            )

        if source_domain not in self.domains:
            raise TopologyError(f"Source domain not found: {source_domain}")

        if target_domain not in self.domains:
            raise TopologyError(f"Target domain not found: {target_domain}")

        # Check if this cross-domain communication is allowed by policy
        if not self._check_federation_policy(source_domain, target_domain, input_data):
            raise TopologyError(
                f"Federation policy denied communication from {source_domain} to {target_domain}"
            )

        # Authenticate the request if required
        if self.authentication_required:
            auth_token = input_data.get("auth_token")
            if not self._authenticate(source_domain, auth_token):
                raise TopologyError(f"Authentication failed for domain {source_domain}")

        # Prepare the task for the target domain
        target_input = input_data.copy()
        target_input.pop("source_domain", None)
        target_input.pop("target_domain", None)
        target_input.pop("auth_token", None)
        target_input["domain"] = target_domain
        target_input["federated_request"] = True
        target_input["request_source"] = source_domain

        # Execute the task in the target domain
        logger.info(f"Executing federated task from {source_domain} to {target_domain}")
        result = await self._execute_domain_task(target_domain, target_input)

        # Add federation metadata
        result["federation_metadata"]["source_domain"] = source_domain
        result["federation_metadata"]["target_domain"] = target_domain
        result["federation_metadata"]["federated"] = True
        result["federation_metadata"]["query_id"] = f"fed_{len(self.federated_queries)}"

        # Record the query
        self.federated_queries.append({
            "type": "federated_task",
            "source_domain": source_domain,
            "target_domain": target_domain,
            "input": input_data,
            "timestamp": self._get_timestamp(),
            "result_status": result.get("status", "unknown"),
        })

        return result

    async def _execute_agent_task(
        self, agent_id: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a task with a specific federation-level agent.

        Args:
            agent_id: Agent ID
            input_data: Task input data

        Returns:
            Task result
        """
        if agent_id not in self.agents:
            raise TopologyError(f"Federation-level agent not found: {agent_id}")

        agent = self.agents[agent_id]
        task = input_data.get("task", "")

        logger.info(
            f"Executing task with federation-level agent {agent_id}: {task[:50]}"
        )

        # Process the task with the agent
        try:
            result = await agent.process_message(task)

            # Format the result
            return {
                "status": "success",
                "result": result,
                "agent_id": agent_id,
                "federation_metadata": {
                    "level": "federation",
                    "timestamp": self._get_timestamp(),
                    "query_id": f"agent_{len(self.federated_queries)}",
                },
            }
        except Exception as e:
            logger.error(f"Error executing task with agent {agent_id}: {e}")
            raise TopologyError(
                f"Failed to execute task with agent {agent_id}: {e}"
            ) from e

    async def _process_federation_task(
        self, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a federation-level task.

        Args:
            input_data: Task input data

        Returns:
            Task result
        """
        task = input_data.get("task", "")
        task_type = input_data.get("task_type", "")

        logger.info(f"Processing federation-level task: {task_type or task[:50]}")

        # Check for special federation tasks
        if task_type == "get_domains":
            return {
                "status": "success",
                "domains": list(self.domains.keys()),
                "domain_count": len(self.domains),
                "federation_metadata": {
                    "level": "federation",
                    "timestamp": self._get_timestamp(),
                },
            }
        elif task_type == "get_federation_status":
            return await self._get_federation_status()
        elif task_type == "get_shared_resources":
            return {
                "status": "success",
                "shared_resources": self.shared_resources,
                "federation_metadata": {
                    "level": "federation",
                    "timestamp": self._get_timestamp(),
                },
            }
        elif task_type == "get_domain_info":
            domain = input_data.get("domain")
            if not domain:
                raise TopologyError(
                    "Domain parameter required for get_domain_info task"
                )
            return await self._get_domain_info(domain)
        elif task_type == "get_auth_token":
            domain = input_data.get("domain")
            if not domain:
                raise TopologyError("Domain parameter required for get_auth_token task")
            if not self._check_federation_policy("federation", domain, input_data):
                raise TopologyError(
                    f"Federation policy denied auth token request for {domain}"
                )
            return await self._get_auth_token(domain)
        # For generic tasks, try to determine the appropriate handler
        elif "broadcast_to_domains" in input_data:
            return await self._broadcast_task(input_data)
        else:
            # Default: use a federation-level agent if specified, or return error
            default_agent = input_data.get("default_agent")
            if default_agent and default_agent in self.agents:
                input_data["agent_id"] = default_agent
                return await self._execute_agent_task(default_agent, input_data)
            else:
                raise TopologyError(
                    "Unrecognized federation task and no default agent specified"
                )

    async def _broadcast_task(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Broadcast a task to multiple domains.

        Args:
            input_data: Task input data with broadcast_to_domains field

        Returns:
            Combined results from all domains
        """
        domains = input_data.get("broadcast_to_domains", [])
        if not domains:
            raise TopologyError("No domains specified for broadcast task")

        # Validate that all domains exist
        for domain in domains:
            if domain not in self.domains:
                raise TopologyError(f"Domain not found for broadcast task: {domain}")

        # Create a copy of the input for domain-specific execution
        domain_input = input_data.copy()
        domain_input.pop("broadcast_to_domains", None)

        # Execute task in each domain
        results = {}
        errors = {}

        for domain in domains:
            try:
                domain_input["domain"] = domain
                result = await self._execute_domain_task(domain, domain_input)
                results[domain] = result
            except Exception as e:
                logger.error(f"Error broadcasting task to domain {domain}: {e}")
                errors[domain] = str(e)

        # Compile results
        return {
            "status": "success",
            "broadcast_results": results,
            "broadcast_errors": errors,
            "successful_domains": list(results.keys()),
            "failed_domains": list(errors.keys()),
            "federation_metadata": {
                "broadcast": True,
                "timestamp": self._get_timestamp(),
                "query_id": f"broadcast_{len(self.federated_queries)}",
            },
        }

    async def _get_domain_info(self, domain: str) -> dict[str, Any]:
        """Get information about a specific domain.

        Args:
            domain: Domain name

        Returns:
            Domain information
        """
        if domain not in self.domain_topologies:
            raise TopologyError(f"Domain not found: {domain}")

        topology = self.domain_topologies[domain]
        domain_config = self.domains.get(domain, {})

        # Get basic information about the domain
        info = {
            "name": domain,
            "topology_type": domain_config.get("topology_type", "unknown"),
            "agent_count": len(topology.agents),
            "agent_ids": list(topology.agents.keys()),
            "initialized": topology.initialized,
            "features": domain_config.get("features", []),
            "description": domain_config.get("description", ""),
        }

        return {
            "status": "success",
            "domain_info": info,
            "federation_metadata": {
                "level": "federation",
                "timestamp": self._get_timestamp(),
            },
        }

    async def _get_federation_status(self) -> dict[str, Any]:
        """Get the overall status of the federation.

        Returns:
            Federation status information
        """
        # Collect status from each domain
        domain_statuses = {}
        for domain, topology in self.domain_topologies.items():
            domain_statuses[domain] = {
                "initialized": topology.initialized,
                "agent_count": len(topology.agents),
                "topology_type": self.domains.get(domain, {}).get(
                    "topology_type", "unknown"
                ),
            }

        return {
            "status": "success",
            "federation_status": {
                "domain_count": len(self.domains),
                "domains": list(self.domains.keys()),
                "domain_statuses": domain_statuses,
                "initialized": self.initialized,
                "federation_agent_count": len(self.agents),
                "federation_agents": list(self.agents.keys()),
                "shared_resource_count": len(self.shared_resources),
                "query_count": len(self.federated_queries),
            },
            "federation_metadata": {
                "level": "federation",
                "timestamp": self._get_timestamp(),
            },
        }

    async def _get_auth_token(self, domain: str) -> dict[str, Any]:
        """Get authentication token for a domain.

        Args:
            domain: Domain name

        Returns:
            Authentication token
        """
        if not self.authentication_required:
            return {
                "status": "error",
                "message": "Authentication is not enabled for this federation",
            }

        if domain not in self.access_tokens:
            # Generate a new token
            import secrets
            import time

            token = secrets.token_hex(16)
            expiry = time.time() + 86400  # 24 hours

            self.access_tokens[domain] = {"token": token, "expiry": expiry}

        token_info = self.access_tokens[domain]

        # Check if token has expired
        if time.time() > token_info["expiry"]:
            # Refresh token
            import secrets
            import time

            token = secrets.token_hex(16)
            expiry = time.time() + 86400  # 24 hours

            self.access_tokens[domain] = {"token": token, "expiry": expiry}

            token_info = self.access_tokens[domain]

        return {
            "status": "success",
            "auth_token": token_info["token"],
            "expiry": token_info["expiry"],
            "federation_metadata": {
                "level": "federation",
                "timestamp": self._get_timestamp(),
            },
        }

    def _check_federation_policy(
        self, source_domain: str, target_domain: str, request_data: dict[str, Any]
    ) -> bool:
        """Check if a cross-domain request is allowed by federation policy.

        Args:
            source_domain: Source domain name
            target_domain: Target domain name
            request_data: Request data

        Returns:
            True if allowed, False otherwise
        """
        # Get the specific policy for this domain pair
        domain_policies = self.federation_policies.get("domain_policies", {})
        default_policy = self.federation_policies.get("default", {"allow": False})

        # Check for specific policy
        policy = domain_policies.get((source_domain, target_domain))
        if not policy:
            # Check for wildcard policies
            policy = (
                domain_policies.get((source_domain, "*"))
                or domain_policies.get(("*", target_domain))
                or domain_policies.get(("*", "*"))
                or default_policy
            )

        # Check if the policy allows this request
        if not policy.get("allow", False):
            return False

        # Check for additional policy constraints
        if "allowed_tasks" in policy:
            task = request_data.get("task", "")
            task_type = request_data.get("task_type", "")

            allowed_tasks = policy["allowed_tasks"]
            if (
                task_type
                and task_type not in allowed_tasks
                and "*" not in allowed_tasks
            ):
                return False

        if "denied_tasks" in policy:
            task = request_data.get("task", "")
            task_type = request_data.get("task_type", "")

            denied_tasks = policy["denied_tasks"]
            if task_type and (task_type in denied_tasks or "*" in denied_tasks):
                return False

        return True

    def _authenticate(self, domain: str, token: str) -> bool:
        """Authenticate a domain using its access token.

        Args:
            domain: Domain name
            token: Access token

        Returns:
            True if authenticated, False otherwise
        """
        if not self.authentication_required:
            return True

        if domain not in self.access_tokens:
            return False

        token_info = self.access_tokens[domain]

        # Check if token has expired
        if time.time() > token_info["expiry"]:
            return False

        # Check if token matches
        return token_info["token"] == token

    def _get_timestamp(self) -> float:
        """Get current timestamp.

        Returns:
            Current timestamp
        """
        import time

        return time.time()

    async def add_domain(self, domain_name: str, domain_config: dict[str, Any]) -> None:
        """Add a new domain to the federation.

        Args:
            domain_name: Name of the domain
            domain_config: Domain configuration

        Raises:
            TopologyError: If domain already exists
        """
        if domain_name in self.domains:
            raise TopologyError(f"Domain already exists: {domain_name}")

        # Add domain to configuration
        self.domains[domain_name] = domain_config

        # Initialize the new domain
        await self._initialize_domain(domain_name, domain_config)

        logger.info(f"Added new domain to federation: {domain_name}")

    async def remove_domain(self, domain_name: str) -> None:
        """Remove a domain from the federation.

        Args:
            domain_name: Name of the domain

        Raises:
            TopologyError: If domain not found
        """
        if domain_name not in self.domains:
            raise TopologyError(f"Domain not found: {domain_name}")

        # Clean up the domain topology
        if domain_name in self.domain_topologies:
            await self.domain_topologies[domain_name].cleanup()
            del self.domain_topologies[domain_name]

        # Remove from domain agents
        if domain_name in self.domain_agents:
            del self.domain_agents[domain_name]

        # Remove from domains
        del self.domains[domain_name]

        logger.info(f"Removed domain from federation: {domain_name}")

    async def add_federation_policy(
        self, source_domain: str, target_domain: str, policy: dict[str, Any]
    ) -> None:
        """Add or update a federation policy.

        Args:
            source_domain: Source domain name
            target_domain: Target domain name
            policy: Policy configuration
        """
        # Update the domain policies
        domain_policies = self.federation_policies.get("domain_policies", {})
        domain_policies[source_domain, target_domain] = policy

        self.federation_policies["domain_policies"] = domain_policies

        logger.info(f"Added federation policy: {source_domain} -> {target_domain}")

    async def get_domain_topology(
        self, domain_name: str
    ) -> AgentTopologyProvider | None:
        """Get the topology provider for a specific domain.

        Args:
            domain_name: Name of the domain

        Returns:
            Domain's topology provider or None if not found

        Raises:
            TopologyError: If domain not found
        """
        if domain_name not in self.domain_topologies:
            raise TopologyError(f"Domain not found: {domain_name}")

        return self.domain_topologies[domain_name]

    async def get_domain_agent(
        self, domain_name: str, agent_id: str
    ) -> BaseAgentProvider | None:
        """Get an agent from a specific domain.

        Args:
            domain_name: Name of the domain
            agent_id: Agent ID

        Returns:
            Agent provider or None if not found

        Raises:
            TopologyError: If domain or agent not found
        """
        if domain_name not in self.domain_agents:
            raise TopologyError(f"Domain not found: {domain_name}")

        if agent_id not in self.domain_agents[domain_name]:
            raise TopologyError(f"Agent not found in domain {domain_name}: {agent_id}")

        return self.domain_agents[domain_name].get(agent_id)

    async def get_queries(self, query_type: str | None = None) -> list[dict[str, Any]]:
        """Get federation queries.

        Args:
            query_type: Filter by query type (optional)

        Returns:
            List of queries
        """
        if query_type:
            return [q for q in self.federated_queries if q.get("type") == query_type]
        else:
            return self.federated_queries
