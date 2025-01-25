"""Base lifecycle management system.

This module provides the core lifecycle management functionality for the Pepperpy framework,
including initialization, cleanup, dependency resolution, and validation.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import asyncio
import logging

from ...interfaces import Provider

logger = logging.getLogger(__name__)

class LifecycleState(Enum):
    """Component lifecycle states."""
    
    UNINITIALIZED = auto()
    """Component is uninitialized."""
    
    INITIALIZING = auto()
    """Component is initializing."""
    
    INITIALIZED = auto()
    """Component is initialized."""
    
    CLEANING_UP = auto()
    """Component is cleaning up."""
    
    CLEANED_UP = auto()
    """Component is cleaned up."""
    
    ERROR = auto()
    """Component is in error state."""

class LifecycleComponent(Provider):
    """Base class for all lifecycle-managed components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize component.
        
        Args:
            config: Optional component configuration
        """
        self._state = LifecycleState.UNINITIALIZED
        self._error: Optional[Exception] = None
        self._config = config or {}
        self._metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat()
        }
    
    @property
    def state(self) -> LifecycleState:
        """Get component state."""
        return self._state
    
    @property
    def error(self) -> Optional[Exception]:
        """Get component error if any."""
        return self._error
    
    @property
    def is_initialized(self) -> bool:
        """Check if component is initialized."""
        return self._state == LifecycleState.INITIALIZED
    
    @property
    def is_error(self) -> bool:
        """Check if component is in error state."""
        return self._state == LifecycleState.ERROR
    
    async def initialize(self) -> None:
        """Initialize component.
        
        This method handles the initialization lifecycle, including state
        management and error handling. The actual initialization logic
        should be implemented in _initialize_impl.
        """
        if self._state != LifecycleState.UNINITIALIZED:
            logger.warning(f"Component already initialized (state: {self._state})")
            return
        
        try:
            self._state = LifecycleState.INITIALIZING
            await self._initialize_impl()
            self._state = LifecycleState.INITIALIZED
            self._metadata["initialized_at"] = datetime.now().isoformat()
            logger.info("Component initialized successfully")
        except Exception as e:
            self._error = e
            self._state = LifecycleState.ERROR
            self._metadata["error"] = str(e)
            logger.error(f"Failed to initialize component: {str(e)}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up component.
        
        This method handles the cleanup lifecycle, including state
        management and error handling. The actual cleanup logic
        should be implemented in _cleanup_impl.
        """
        if self._state not in (LifecycleState.INITIALIZED, LifecycleState.ERROR):
            logger.warning(f"Component not initialized (state: {self._state})")
            return
        
        try:
            self._state = LifecycleState.CLEANING_UP
            await self._cleanup_impl()
            self._state = LifecycleState.CLEANED_UP
            self._metadata["cleaned_up_at"] = datetime.now().isoformat()
            logger.info("Component cleaned up successfully")
        except Exception as e:
            self._error = e
            self._state = LifecycleState.ERROR
            self._metadata["error"] = str(e)
            logger.error(f"Failed to clean up component: {str(e)}")
            raise
    
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Implementation-specific initialization logic.
        
        This method should be overridden by components to provide
        their specific initialization logic.
        """
        pass
    
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Implementation-specific cleanup logic.
        
        This method should be overridden by components to provide
        their specific cleanup logic.
        """
        pass
    
    def validate(self) -> None:
        """Validate component state.
        
        This method performs basic state validation. Components can
        override this method to add additional validation logic.
        """
        if self._state == LifecycleState.ERROR and self._error:
            raise ValueError(f"Component in error state: {self._error}")
        
        if self._state not in (
            LifecycleState.INITIALIZED,
            LifecycleState.CLEANED_UP,
        ):
            raise ValueError(f"Invalid component state: {self._state}")

class LifecycleManager(LifecycleComponent):
    """Manager for multiple lifecycle components."""
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize manager.
        
        Args:
            config: Optional manager configuration
        """
        super().__init__(config)
        self._components: Dict[str, LifecycleComponent] = {}
        self._dependencies: Dict[str, Set[str]] = {}
    
    def register(
        self,
        name: str,
        component: LifecycleComponent,
        dependencies: Optional[List[str]] = None,
    ) -> None:
        """Register component.
        
        Args:
            name: Component name
            component: Component instance
            dependencies: Optional list of dependency component names
        """
        self._components[name] = component
        self._dependencies[name] = set(dependencies or [])
    
    def unregister(self, name: str) -> None:
        """Unregister component.
        
        Args:
            name: Component name
        """
        if name in self._components:
            del self._components[name]
            del self._dependencies[name]
            
            # Remove from other components' dependencies
            for deps in self._dependencies.values():
                deps.discard(name)
    
    async def _initialize_impl(self) -> None:
        """Initialize all components in dependency order."""
        # Find initialization order
        init_order = self._topological_sort()
        
        # Group components that can be initialized in parallel
        parallel_groups = self._group_parallel_components(init_order)
        
        try:
            # Initialize each group in parallel
            for group in parallel_groups:
                tasks = [
                    self._initialize_component(name)
                    for name in group
                ]
                await asyncio.gather(*tasks)
                
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            await self.cleanup()
            raise
    
    async def _cleanup_impl(self) -> None:
        """Clean up all components in reverse dependency order."""
        # Clean up in reverse order
        cleanup_order = list(reversed(self._topological_sort()))
        
        # Group components that can be cleaned up in parallel
        parallel_groups = self._group_parallel_components(cleanup_order)
        
        try:
            # Clean up each group in parallel
            for group in parallel_groups:
                tasks = [
                    self._cleanup_component(name)
                    for name in group
                ]
                await asyncio.gather(*tasks)
                
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            raise
    
    def _topological_sort(self) -> List[str]:
        """Sort components by dependency order.
        
        Returns:
            List of component names in dependency order
            
        Raises:
            ValueError: If there are circular dependencies
        """
        result: List[str] = []
        visited: Set[str] = set()
        temp: Set[str] = set()
        
        def visit(name: str) -> None:
            if name in temp:
                raise ValueError(f"Circular dependency detected: {name}")
            if name in visited:
                return
                
            temp.add(name)
            
            for dep in self._dependencies[name]:
                visit(dep)
                
            temp.remove(name)
            visited.add(name)
            result.append(name)
            
        for name in self._components:
            if name not in visited:
                visit(name)
                
        return result
    
    def _group_parallel_components(self, ordered: List[str]) -> List[List[str]]:
        """Group components that can be initialized/cleaned up in parallel.
        
        Args:
            ordered: List of component names in dependency order
            
        Returns:
            List of component groups that can be processed in parallel
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
            name: Component name
        """
        component = self._components[name]
        if not component.is_initialized:
            await component.initialize()
    
    async def _cleanup_component(self, name: str) -> None:
        """Clean up a single component.
        
        Args:
            name: Component name
        """
        component = self._components[name]
        if component.is_initialized:
            await component.cleanup() 