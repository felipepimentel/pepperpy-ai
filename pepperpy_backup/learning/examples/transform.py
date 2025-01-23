"""Example transformation implementation."""

import logging
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class ExampleTransformError(PepperpyError):
    """Example transform error."""
    pass


@runtime_checkable
class ExampleTransform(Protocol):
    """Example transform protocol."""
    
    def transform(self, example: Any) -> Any:
        """Transform example.
        
        Args:
            example: Example to transform
            
        Returns:
            Transformed example
        """
        ...


class DictTransform(ExampleTransform):
    """Dictionary example transform implementation."""
    
    def __init__(
        self,
        field_transforms: Dict[str, ExampleTransform],
    ) -> None:
        """Initialize dictionary transform.
        
        Args:
            field_transforms: Mapping of field names to transforms
        """
        self.field_transforms = field_transforms
        
    def transform(self, example: Any) -> Dict[str, Any]:
        """Transform example.
        
        Args:
            example: Example to transform
            
        Returns:
            Transformed example
            
        Raises:
            ValueError: If example is not a dictionary
        """
        if not isinstance(example, dict):
            raise ValueError("Example must be a dictionary")
            
        try:
            result = {}
            
            # Apply field transforms
            for field, transform in self.field_transforms.items():
                if field in example:
                    result[field] = transform.transform(example[field])
                else:
                    result[field] = None
                    
            # Copy untransformed fields
            for field, value in example.items():
                if field not in self.field_transforms:
                    result[field] = value
                    
            return result
            
        except Exception as e:
            raise ValueError(f"Failed to transform example: {e}")


class ListTransform(ExampleTransform):
    """List example transform implementation."""
    
    def __init__(
        self,
        item_transform: ExampleTransform,
    ) -> None:
        """Initialize list transform.
        
        Args:
            item_transform: Transform for list items
        """
        self.item_transform = item_transform
        
    def transform(self, example: Any) -> List[Any]:
        """Transform example.
        
        Args:
            example: Example to transform
            
        Returns:
            Transformed example
            
        Raises:
            ValueError: If example is not a list
        """
        if not isinstance(example, list):
            raise ValueError("Example must be a list")
            
        try:
            return [
                self.item_transform.transform(item)
                for item in example
            ]
            
        except Exception as e:
            raise ValueError(f"Failed to transform example: {e}")


class CompositeTransform(ExampleTransform):
    """Composite example transform implementation."""
    
    def __init__(
        self,
        transforms: List[ExampleTransform],
    ) -> None:
        """Initialize composite transform.
        
        Args:
            transforms: List of transforms to apply
        """
        self.transforms = transforms
        
    def transform(self, example: Any) -> Any:
        """Transform example.
        
        Args:
            example: Example to transform
            
        Returns:
            Transformed example
        """
        try:
            result = example
            
            # Apply transforms in sequence
            for transform in self.transforms:
                result = transform.transform(result)
                
            return result
            
        except Exception as e:
            raise ValueError(f"Failed to transform example: {e}")


class FilterTransform(ExampleTransform):
    """Filter example transform implementation."""
    
    def __init__(
        self,
        field_filters: Dict[str, Any],
    ) -> None:
        """Initialize filter transform.
        
        Args:
            field_filters: Mapping of field names to filter values
        """
        self.field_filters = field_filters
        
    def transform(self, example: Any) -> Dict[str, Any]:
        """Transform example.
        
        Args:
            example: Example to transform
            
        Returns:
            Transformed example
            
        Raises:
            ValueError: If example is not a dictionary
        """
        if not isinstance(example, dict):
            raise ValueError("Example must be a dictionary")
            
        try:
            result = {}
            
            # Copy fields that match filters
            for field, value in example.items():
                if field in self.field_filters:
                    if value == self.field_filters[field]:
                        result[field] = value
                else:
                    result[field] = value
                    
            return result
            
        except Exception as e:
            raise ValueError(f"Failed to transform example: {e}")


class MapTransform(ExampleTransform):
    """Map example transform implementation."""
    
    def __init__(
        self,
        field_map: Dict[str, str],
    ) -> None:
        """Initialize map transform.
        
        Args:
            field_map: Mapping of source field names to target field names
        """
        self.field_map = field_map
        
    def transform(self, example: Any) -> Dict[str, Any]:
        """Transform example.
        
        Args:
            example: Example to transform
            
        Returns:
            Transformed example
            
        Raises:
            ValueError: If example is not a dictionary
        """
        if not isinstance(example, dict):
            raise ValueError("Example must be a dictionary")
            
        try:
            result = {}
            
            # Map fields to new names
            for src_field, dst_field in self.field_map.items():
                if src_field in example:
                    result[dst_field] = example[src_field]
                    
            # Copy unmapped fields
            for field, value in example.items():
                if field not in self.field_map:
                    result[field] = value
                    
            return result
            
        except Exception as e:
            raise ValueError(f"Failed to transform example: {e}") 