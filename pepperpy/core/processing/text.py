"""@file: text.py
@purpose: Text content processor implementation
@component: Core > Processors
@created: 2024-03-21
@task: TASK-007-R060
@status: active
"""

import time
from typing import Any, Dict, List

from .base import ContentProcessor, ProcessingContext, ProcessingResult

class TextProcessor(ContentProcessor[str, str]):
    """Process text content."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        
    async def process(
        self,
        content: str,
        context: ProcessingContext
    ) -> ProcessingResult[str]:
        """Process text content."""
        start_time = time.time()
        
        try:
            # Process text content
            processed = await self._process_text(content, context)
            duration = time.time() - start_time
            
            await self._record_metrics(
                "process",
                True,
                duration,
                content_type="text"
            )
            
            return ProcessingResult(
                content=processed,
                metadata={"config": self.config},
                errors=[],
                warnings=[],
                processing_time=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            await self._record_metrics(
                "process",
                False,
                duration,
                content_type="text",
                error=str(e)
            )
            
            return ProcessingResult(
                content=content,
                metadata={"error": str(e)},
                errors=[str(e)],
                warnings=[],
                processing_time=duration
            )
            
    async def validate(
        self,
        content: str,
        context: ProcessingContext
    ) -> List[str]:
        """Validate text content."""
        errors = []
        
        if not content:
            errors.append("Empty content")
            
        if len(content) > self.config.get("max_length", 1000000):
            errors.append("Content too long")
            
        return errors
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass
        
    async def _process_text(
        self,
        content: str,
        context: ProcessingContext
    ) -> str:
        """Process text content."""
        # Apply text transformations based on context
        if context.options.get("normalize", True):
            content = content.strip()
            
        if context.options.get("lowercase", False):
            content = content.lower()
            
        if context.options.get("uppercase", False):
            content = content.upper()
            
        if max_length := context.options.get("max_length"):
            content = content[:max_length]
            
        return content 