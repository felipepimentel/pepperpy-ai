"""Lifecycle manager module for Pepperpy framework."""

import asyncio
import logging
from typing import Dict, List, Optional, Set

from ...common.errors import PepperpyError
from .lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class LifecycleManagerError(PepperpyError):
    """Lifecycle manager error class."""
    pass


class PepperpyLifecycleManager:
    """Manages component lifecycle with optimized initialization."""
    
    def __init__(self) -> None:
        """Initialize the lifecycle manager."""
        self._components: Dict[str, Lifecycle] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._initialized: Set[str] = set()
        self._state = "created"
    
    def register(
        self,
        name: str,
        component: Lifecycle,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """Register a component.
        
        Args:
            name: Component name.
            component: Component instance.
            dependencies: Optional list of dependency component names.
            
        Raises:
            LifecycleManagerError: If component registration fails.
        """
        if name in self._components:
            raise LifecycleManagerError(f"Component {name} is already registered")
        
        if not isinstance(component, Lifecycle):
            raise LifecycleManagerError(
                f"Component {name} must be a Lifecycle instance"
            )
        
        self._components[name] = component
        self._dependencies[name] = set(dependencies or [])
    
    async def initialize(self) -> None:
        """Initialize all components in dependency order.
        
        This method uses a topological sort to initialize components
        in the correct order, with parallel initialization where possible.
        
        Raises:
            LifecycleManagerError: If initialization fails.
        """
        if self._state != "created":
            return
            
        try:
            # Find initialization order
            init_order = self._topological_sort()
            
            # Group components that can be initialized in parallel
            parallel_groups = self._group_parallel_components(init_order)
            
            # Initialize each group in parallel
            for group in parallel_groups:
                tasks = [
                    self._initialize_component(name)
                    for name in group
                ]
                await asyncio.gather(*tasks)
                
            self._state = "initialized"
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            await self.terminate()
            raise LifecycleManagerError(f"Initialization failed: {e}")
    
    async def terminate(self) -> None:
        """Terminate all components in reverse dependency order.
        
        Raises:
            LifecycleManagerError: If termination fails.
        """
        if self._state != "initialized":
            return
            
        try:
            # Reverse the initialization order
            term_order = list(reversed(self._topological_sort()))
            
            # Group components that can be terminated in parallel
            parallel_groups = self._group_parallel_components(term_order)
            
            # Terminate each group in parallel
            for group in parallel_groups:
                tasks = [
                    self._terminate_component(name)
                    for name in group
                ]
                await asyncio.gather(*tasks)
                
            self._initialized.clear()
            self._state = "terminated"
            
        except Exception as e:
            logger.error(f"Termination failed: {e}")
            raise LifecycleManagerError(f"Termination failed: {e}")
    
    def get_state(self) -> str:
        """Get the current lifecycle state."""
        return self._state
    
    def _topological_sort(self) -> List[str]:
        """Perform topological sort of components.
        
        Returns:
            List of component names in dependency order.
            
        Raises:
            LifecycleManagerError: If there are circular dependencies.
        """
        result: List[str] = []
        visited: Set[str] = set()
        temp: Set[str] = set()
        
        def visit(name: str) -> None:
            if name in temp:
                raise LifecycleManagerError(
                    f"Circular dependency detected involving {name}"
                )
            if name in visited:
                return
                
            temp.add(name)
            for dep in self._dependencies[name]:
                if dep not in self._components:
                    raise LifecycleManagerError(
                        f"Missing dependency {dep} for component {name}"
                    )
                visit(dep)
            temp.remove(name)
            visited.add(name)
            result.append(name)
        
        for name in self._components:
            if name not in visited:
                visit(name)
                
        return result
    
    def _group_parallel_components(self, ordered: List[str]) -> List[List[str]]:
        """Group components that can be initialized in parallel.
        
        Args:
            ordered: List of component names in dependency order.
            
        Returns:
            List of component groups that can be initialized in parallel.
        """
        result: List[List[str]] = []
        current_group: List[str] = []
        seen_deps: Set[str] = set()
        
        for name in ordered:
            # If component has unseen dependencies, start new group
            if any(dep not in seen_deps for dep in self._dependencies[name]):
                if current_group:
                    result.append(current_group)
                current_group = []
            
            current_group.append(name)
            seen_deps.add(name)
        
        if current_group:
            result.append(current_group)
            
        return result
    
    async def _initialize_component(self, name: str) -> None:
        """Initialize a single component.
        
        Args:
            name: Component name.
            
        Raises:
            LifecycleManagerError: If component initialization fails.
        """
        if name in self._initialized:
            return
            
        try:
            component = self._components[name]
            await component.initialize()
            self._initialized.add(name)
        except Exception as e:
            raise LifecycleManagerError(
                f"Failed to initialize component {name}: {e}"
            )
    
    async def _terminate_component(self, name: str) -> None:
        """Terminate a single component.
        
        Args:
            name: Component name.
            
        Raises:
            LifecycleManagerError: If component termination fails.
        """
        if name not in self._initialized:
            return
            
        try:
            component = self._components[name]
            await component.cleanup()
            self._initialized.remove(name)
        except Exception as e:
            raise LifecycleManagerError(
                f"Failed to terminate component {name}: {e}"
            ) 