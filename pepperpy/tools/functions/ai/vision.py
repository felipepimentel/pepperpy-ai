"""Tool for analyzing images using OpenAI's Vision API."""

import base64
import os
from dataclasses import dataclass
from typing import Optional

import aiohttp

from pepperpy.tools.base_tool import BaseTool, ToolResult


@dataclass
class VisionAnalysisResult:
    """Result from vision analysis."""
    
    description: str


class VisionTool(BaseTool):
    """Tool for analyzing images using OpenAI's Vision API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the tool.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required")
        self.session = None

    async def initialize(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
    async def cleanup(self):
        if self.session:
            await self.session.close()
            self.session = None

    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def execute(
        self,
        image_path: str,
        prompt: str = "Describe this character in detail, including appearance, personality traits that can be inferred from the image, and any notable features."
    ) -> ToolResult[VisionAnalysisResult]:
        """Execute vision analysis on an image.
        
        Args:
            image_path: Path to image file
            prompt: Prompt describing what to analyze in the image
            
        Returns:
            Analysis result
        """
        if not self.session:
            return ToolResult(success=False, error="Tool not initialized", data=None)
            
        try:
            # Encode image
            base64_image = self._encode_image(image_path)
            
            # Prepare payload for GPT-4 Vision
            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }
            
            # Make API request
            async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return ToolResult(
                        success=False,
                        error=f"API request failed: {error_text}",
                        data=None
                    )
                    
                response_data = await response.json()
                description = response_data["choices"][0]["message"]["content"]
                
                return ToolResult(
                    success=True,
                    error=None,
                    data=VisionAnalysisResult(description=description)
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to analyze image: {str(e)}",
                data=None
            ) 