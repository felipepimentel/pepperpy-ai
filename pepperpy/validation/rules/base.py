"""Base validation rule interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, ClassVar, Union

from pepperpy.core.utils.errors import ValidationError

T = TypeVar('T', bound='BaseValidationRule')

class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(
        self,
        is_valid: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize validation result.
        
        Args:
            is_valid: Whether the validation passed
            errors: Optional list of error messages
            warnings: Optional list of warning messages
            metadata: Optional metadata about the validation
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}

class BaseValidationRule(ABC):
    """Base class for all validation rules.
    
    A validation rule defines criteria for validating data and provides
    methods to perform the validation.
    """
    
    _registry: ClassVar[Dict[str, Type['BaseValidationRule']]] = {}
    
    @classmethod
    def register(cls, name: str) -> Any:
        """Register a validation rule class.
        
        Args:
            name: Name to register the rule under.
            
        Returns:
            Decorator function.
        """
        def decorator(rule_cls: Type[T]) -> Type[T]:
            cls._registry[name] = rule_cls
            return rule_cls
        return decorator
    
    @classmethod
    def get_rule(cls, name: str) -> Type['BaseValidationRule']:
        """Get a registered validation rule class.
        
        Args:
            name: Name of the rule.
            
        Returns:
            Validation rule class.
            
        Raises:
            ValueError: If rule is not registered.
        """
        if name not in cls._registry:
            raise ValueError(f"Validation rule '{name}' not registered")
        return cls._registry[name]
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize validation rule.
        
        Args:
            name: Rule name
            config: Optional configuration
        """
        if not name:
            raise ValueError("Rule name cannot be empty")
            
        self._name = name
        self._config = config or {}
        self._initialized = False
        
    @property
    def name(self) -> str:
        """Get rule name."""
        return self._name
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get rule configuration."""
        return self._config.copy()
        
    @property
    def is_initialized(self) -> bool:
        """Get initialization status."""
        return self._initialized
        
    async def initialize(self) -> None:
        """Initialize validation rule."""
        if self.is_initialized:
            return
            
        await self._initialize_impl()
        self._initialized = True
        
    async def cleanup(self) -> None:
        """Clean up validation rule."""
        if not self.is_initialized:
            return
            
        await self._cleanup_impl()
        self._initialized = False
        
    def validate(self) -> None:
        """Validate rule state."""
        if not self.name:
            raise ValueError("Empty rule name")
            
        self._validate_impl()
        
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Initialize implementation."""
        pass
        
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Clean up implementation."""
        pass
        
    def _validate_impl(self) -> None:
        """Validate implementation."""
        pass

    @abstractmethod
    async def validate_data(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate data against the rule.
        
        Args:
            data: Data to validate
            context: Optional validation context
            
        Returns:
            Validation result
            
        Raises:
            ValidationError: If validation process fails
        """
        pass

    @abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """Get rule metadata.
        
        Returns:
            Dictionary containing rule metadata
        """
        pass

    @abstractmethod
    async def get_dependencies(self) -> List[str]:
        """Get rule dependencies.
        
        Returns:
            List of rule names that this rule depends on
        """
        pass

    @abstractmethod
    async def get_supported_types(self) -> List[str]:
        """Get supported data types.
        
        Returns:
            List of data types that this rule can validate
        """
        pass

    @abstractmethod
    async def get_validation_schema(self) -> Dict[str, Any]:
        """Get validation schema.
        
        Returns:
            Dictionary describing the validation schema
        """
        pass 