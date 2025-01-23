"""Lifecycle manager implementation.

This module provides functionality for managing multiple component lifecycles,
including dependency resolution and parallel initialization/cleanup.
"""

import asyncio
from typing import Any, Dict, List, Optional, Set

from pepperpy.common.errors import PepperpyError
from .lifecycle import Lifecycle, LifecycleError


class ManagerError(PepperpyError):
    """Manager error."""
    pass


class LifecycleManager(Lifecycle):
    """Lifecycle manager implementation."""
    
    def __init__(
        self,
        name: str,
        components: Optional[List[Lifecycle]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize manager.
        
        Args:
            name: Manager name
            components: Optional components to manage
            config: Optional configuration
        """
        super().__init__()
        self.name = name
        self._components = components or []
        self._config = config or {}
        self._dependencies: Dict[Lifecycle, Set[Lifecycle]] = {}
        
    def add_component(self, component: Lifecycle) -> None:
        """Add component.
        
        Args:
            component: Component to add
            
        Raises:
            ManagerError: If component already exists
        """
        if component in self._components:
            raise ManagerError("Component already exists")
            
        self._components.append(component)
        
    def remove_component(self, component: Lifecycle) -> None:
        """Remove component.
        
        Args:
            component: Component to remove
            
        Raises:
            ManagerError: If component not found
        """
        if component not in self._components:
            raise ManagerError("Component not found")
            
        self._components.remove(component)
        
        if component in self._dependencies:
            del self._dependencies[component]
            
        for deps in self._dependencies.values():
            deps.discard(component)
            
    def add_dependency(
        self,
        component: Lifecycle,
        dependency: Lifecycle,
    ) -> None:
        """Add component dependency.
        
        Args:
            component: Component
            dependency: Component dependency
            
        Raises:
            ManagerError: If components not found or cycle detected
        """
        if component not in self._components:
            raise ManagerError("Component not found")
            
        if dependency not in self._components:
            raise ManagerError("Dependency not found")
            
        if component == dependency:
            raise ManagerError("Self dependency not allowed")
            
        if component not in self._dependencies:
            self._dependencies[component] = set()
            
        self._dependencies[component].add(dependency)
        
        # Check for cycles
        visited = set()
        stack = set()
        
        def has_cycle(node: Lifecycle) -> bool:
            visited.add(node)
            stack.add(node)
            
            for dep in self._dependencies.get(node, set()):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in stack:
                    return True
                    
            stack.remove(node)
            return False
            
        if has_cycle(component):
            self._dependencies[component].remove(dependency)
            raise ManagerError("Dependency cycle detected")
            
    async def _initialize(self) -> None:
        """Initialize manager.
        
        Raises:
            ManagerError: If initialization fails
        """
        # Initialize components in dependency order
        initialized = set()
        tasks = []
        
        async def init_component(component: Lifecycle) -> None:
            # Wait for dependencies
            deps = self._dependencies.get(component, set())
            for dep in deps:
                if dep not in initialized:
                    await asyncio.Event().wait()
                    
            try:
                await component.initialize()
                initialized.add(component)
            except Exception as e:
                raise ManagerError(f"Component initialization failed: {e}")
                
        for component in self._components:
            task = asyncio.create_task(init_component(component))
            tasks.append(task)
            
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            raise ManagerError(f"Manager initialization failed: {e}")
            
    async def _cleanup(self) -> None:
        """Clean up manager.
        
        Raises:
            ManagerError: If cleanup fails
        """
        # Clean up components in reverse dependency order
        cleaned = set()
        tasks = []
        
        async def cleanup_component(component: Lifecycle) -> None:
            # Wait for dependents
            for dep, deps in self._dependencies.items():
                if component in deps and dep not in cleaned:
                    await asyncio.Event().wait()
                    
            try:
                await component.cleanup()
                cleaned.add(component)
            except Exception as e:
                raise ManagerError(f"Component cleanup failed: {e}")
                
        for component in reversed(self._components):
            task = asyncio.create_task(cleanup_component(component))
            tasks.append(task)
            
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            raise ManagerError(f"Manager cleanup failed: {e}")
            
    def validate(self) -> None:
        """Validate manager state.
        
        Raises:
            ManagerError: If validation fails
        """
        super().validate()
        
        if not self.name:
            raise ManagerError("Empty manager name")
            
        # Validate components
        for component in self._components:
            try:
                component.validate()
            except Exception as e:
                raise ManagerError(f"Component validation failed: {e}") 