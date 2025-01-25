"""
Unit tests for base capability functionality.
"""

import pytest
from typing import Any, Dict, List

from pepperpy.core.utils.errors import ValidationError
from pepperpy.capabilities.base.capability import (
    BaseCapability,
    DocumentProcessor,
    TextAnalyzer,
)


class TestCapability(BaseCapability[str, str]):
    """Test capability implementation."""
    
    async def initialize(self) -> None:
        """Initialize the capability."""
        await super().initialize()
    
    async def _initialize_impl(self) -> None:
        """Initialize implementation."""
        pass
    
    async def _cleanup_impl(self) -> None:
        """Clean up implementation."""
        pass
    
    async def _execute(self, input_data: str) -> str:
        """Execute the capability."""
        return input_data.upper()
    
    async def validate_input(self, input_data: str) -> None:
        """Validate input data."""
        if not isinstance(input_data, str):
            raise ValidationError("Input must be a string")
    
    async def validate_output(self, output_data: str) -> None:
        """Validate output data."""
        if not isinstance(output_data, str):
            raise ValidationError("Output must be a string")
            
    async def get_metadata(self) -> Dict[str, Any]:
        """Get capability metadata."""
        return {
            "name": self.name,
            "version": "1.0.0",
            "description": "Test capability for unit tests"
        }
        
    async def get_dependencies(self) -> List[str]:
        """Get capability dependencies."""
        return []
        
    async def get_required_providers(self) -> List[str]:
        """Get required providers."""
        return []
        
    async def get_supported_inputs(self) -> Dict[str, Any]:
        """Get supported input parameters."""
        return {"input": "string"}
        
    async def get_supported_outputs(self) -> Dict[str, Any]:
        """Get supported output parameters."""
        return {"output": "string"}


@pytest.mark.asyncio
async def test_capability_lifecycle(test_config):
    """Test capability initialization."""
    capability = TestCapability(config=test_config)
    
    assert not capability.is_initialized
    await capability.initialize()
    assert capability.is_initialized


@pytest.mark.asyncio
async def test_capability_config(test_config):
    """Test capability configuration."""
    capability = TestCapability(config=test_config)
    assert capability.config == test_config
    
    capability_no_config = TestCapability()
    assert capability_no_config.config == {}


@pytest.mark.asyncio
async def test_capability_execution():
    """Test capability execution."""
    capability = TestCapability()
    await capability.initialize()
    
    result = await capability.execute("test")
    assert result == "TEST"


@pytest.mark.asyncio
async def test_capability_validation():
    """Test capability validation."""
    capability = TestCapability()
    await capability.initialize()
    
    with pytest.raises(ValidationError):
        await capability.validate_input(123)  # type: ignore
    
    await capability.validate_input("test")  # Should not raise
    
    with pytest.raises(ValidationError):
        await capability.validate_output(123)  # type: ignore
    
    await capability.validate_output("TEST")  # Should not raise


class TestDocProcessor(DocumentProcessor):
    """Test document processor implementation."""
    
    async def initialize(self) -> None:
        """Initialize the capability."""
        await super().initialize()
    
    async def _initialize_impl(self) -> None:
        """Initialize implementation."""
        pass
    
    async def _cleanup_impl(self) -> None:
        """Clean up implementation."""
        pass
    
    async def _execute(self, input_data: str) -> dict:
        """Execute the capability."""
        return {
            "text": input_data.upper(),
            "length": len(input_data)
        }
    
    async def validate_input(self, input_data: str) -> None:
        """Validate input data."""
        if not isinstance(input_data, str):
            raise ValidationError("Input must be a string")
    
    async def validate_output(self, output_data: dict) -> None:
        """Validate output data."""
        if not isinstance(output_data, dict):
            raise ValidationError("Output must be a dictionary")
        if "text" not in output_data or "length" not in output_data:
            raise ValidationError("Output must contain 'text' and 'length' keys")
            
    async def get_metadata(self) -> Dict[str, Any]:
        """Get capability metadata."""
        return {
            "name": self.name,
            "version": "1.0.0",
            "description": "Test document processor for unit tests"
        }
        
    async def get_dependencies(self) -> List[str]:
        """Get capability dependencies."""
        return []
        
    async def get_required_providers(self) -> List[str]:
        """Get required providers."""
        return []
        
    async def get_supported_inputs(self) -> Dict[str, Any]:
        """Get supported input parameters."""
        return {"document": "string"}
        
    async def get_supported_outputs(self) -> Dict[str, Any]:
        """Get supported output parameters."""
        return {
            "text": "string",
            "length": "integer"
        }


@pytest.mark.asyncio
async def test_document_processor():
    """Test document processor functionality."""
    processor = TestDocProcessor()
    await processor.initialize()
    
    result = await processor.process("test document")
    assert result["text"] == "TEST DOCUMENT"
    assert result["length"] == 12


class TestTextAnalyzer(TextAnalyzer):
    """Test text analyzer implementation."""
    
    async def initialize(self) -> None:
        """Initialize the capability."""
        await super().initialize()
    
    async def _initialize_impl(self) -> None:
        """Initialize implementation."""
        pass
    
    async def _cleanup_impl(self) -> None:
        """Clean up implementation."""
        pass
    
    async def _execute(self, input_data: str) -> dict:
        """Execute the capability."""
        words = input_data.split()
        return {
            "word_count": len(words),
            "char_count": len(input_data)
        }
    
    async def validate_input(self, input_data: str) -> None:
        """Validate input data."""
        if not isinstance(input_data, str):
            raise ValidationError("Input must be a string")
    
    async def validate_output(self, output_data: dict) -> None:
        """Validate output data."""
        if not isinstance(output_data, dict):
            raise ValidationError("Output must be a dictionary")
        if "word_count" not in output_data or "char_count" not in output_data:
            raise ValidationError("Output must contain 'word_count' and 'char_count' keys")
            
    async def get_metadata(self) -> Dict[str, Any]:
        """Get capability metadata."""
        return {
            "name": self.name,
            "version": "1.0.0",
            "description": "Test text analyzer for unit tests"
        }
        
    async def get_dependencies(self) -> List[str]:
        """Get capability dependencies."""
        return []
        
    async def get_required_providers(self) -> List[str]:
        """Get required providers."""
        return []
        
    async def get_supported_inputs(self) -> Dict[str, Any]:
        """Get supported input parameters."""
        return {"text": "string"}
        
    async def get_supported_outputs(self) -> Dict[str, Any]:
        """Get supported output parameters."""
        return {
            "word_count": "integer",
            "char_count": "integer"
        }


@pytest.mark.asyncio
async def test_text_analyzer():
    """Test text analyzer functionality."""
    analyzer = TestTextAnalyzer()
    await analyzer.initialize()
    
    result = await analyzer.analyze("test text analysis")
    assert result["word_count"] == 3
    assert result["char_count"] == 17 