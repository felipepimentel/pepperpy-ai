"""
Agent Topology Module.

Defines various agent coordination and interaction patterns.
"""

from .base import AgentTopologyProvider, TopologyError, create_topology

__all__ = [
    "AgentTopologyProvider",
    "TopologyError",
    "create_topology",
]
