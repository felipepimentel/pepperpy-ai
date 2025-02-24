"""
Component pool manager for managing multiple lifecycle components.
"""

from typing import Dict, Optional, List, Any
from asyncio import gather

from pepperpy.core.lifecycle.base import LifecycleComponent
from pepperpy.core.lifecycle.errors import (
    ComponentNotFoundError,
    ComponentAlreadyExistsError,
    LifecycleOperationError,
)
from pepperpy.core.lifecycle.types import LifecycleState
from pepperpy.core.metrics.unified import MetricsManager

class ComponentPool:
    """Manages a pool of lifecycle components."""
    
    _instance = None
    
    def __new__(cls) -> 'ComponentPool':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._components: Dict[str, LifecycleComponent] = {}
            self._metrics = MetricsManager.get_instance()
    
    def register(self, component: LifecycleComponent) -> None:
        """Register a component with the pool."""
        if component.name in self._components:
            raise ComponentAlreadyExistsError(component.name)
        
        self._components[component.name] = component
        self._metrics.record_metric(
            "component_registered",
            1,
            {"component": component.name}
        )
    
    def unregister(self, component_name: str) -> None:
        """Unregister a component from the pool."""
        if component_name not in self._components:
            raise ComponentNotFoundError(component_name)
        
        del self._components[component_name]
        self._metrics.record_metric(
            "component_unregistered",
            1,
            {"component": component_name}
        )
    
    def get_component(self, component_name: str) -> LifecycleComponent:
        """Get a component by name."""
        if component_name not in self._components:
            raise ComponentNotFoundError(component_name)
        return self._components[component_name]
    
    def get_components(self) -> List[LifecycleComponent]:
        """Get all registered components."""
        return list(self._components.values())
    
    def get_components_by_state(self, state: LifecycleState) -> List[LifecycleComponent]:
        """Get all components in a specific state."""
        return [c for c in self._components.values() if c.state == state]
    
    async def initialize_all(self) -> None:
        """Initialize all uninitialized components."""
        components = self.get_components_by_state(LifecycleState.UNINITIALIZED)
        try:
            await gather(*[c.initialize() for c in components])
            self._metrics.record_metric(
                "components_initialized",
                len(components)
            )
        except Exception as e:
            raise LifecycleOperationError("initialize_all", "pool", e)
    
    async def start_all(self) -> None:
        """Start all initialized components."""
        components = self.get_components_by_state(LifecycleState.INITIALIZED)
        try:
            await gather(*[c.start() for c in components])
            self._metrics.record_metric(
                "components_started",
                len(components)
            )
        except Exception as e:
            raise LifecycleOperationError("start_all", "pool", e)
    
    async def stop_all(self) -> None:
        """Stop all running components."""
        components = self.get_components_by_state(LifecycleState.RUNNING)
        try:
            await gather(*[c.stop() for c in components])
            self._metrics.record_metric(
                "components_stopped",
                len(components)
            )
        except Exception as e:
            raise LifecycleOperationError("stop_all", "pool", e)
    
    async def finalize_all(self) -> None:
        """Finalize all stopped components."""
        components = self.get_components_by_state(LifecycleState.STOPPED)
        try:
            await gather(*[c.finalize() for c in components])
            self._metrics.record_metric(
                "components_finalized",
                len(components)
            )
        except Exception as e:
            raise LifecycleOperationError("finalize_all", "pool", e)
    
    def get_component_stats(self) -> Dict[str, Any]:
        """Get statistics about the component pool."""
        stats = {
            "total_components": len(self._components),
            "states": {
                state.value: len(self.get_components_by_state(state))
                for state in LifecycleState
            }
        }
        return stats

def get_component_pool() -> ComponentPool:
    """Get the global ComponentPool instance."""
    return ComponentPool() 