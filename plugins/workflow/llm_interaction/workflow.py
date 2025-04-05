"""
LLM Interaction Workflow

This workflow provides a comprehensive interface for interacting with Large Language Models:
1. Text completion
2. Chat conversations
3. Streaming responses
4. Text embeddings
"""

import json
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from pepperpy.utils.logging import get_logger
from pepperpy.workflow.provider import WorkflowProvider


class LLMInteractionWorkflow(WorkflowProvider):
    """Workflow for LLM interaction including chat, completion, streaming, and embedding."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the LLM interaction workflow.

        Args:
            config: Configuration parameters
        """
        self.config = config or {}

        # LLM configuration
        self.provider = self.config.get("provider", "openai")
        self.model = self.config.get("model", "gpt-3.5-turbo")
        self.api_key = self.config.get(
            "api_key", os.environ.get(f"{self.provider.upper()}_API_KEY", "")
        )
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 1024)
        self.streaming = self.config.get("streaming", False)
        self.system_prompt = self.config.get(
            "system_prompt",
            "You are a helpful assistant powered by the PepperPy framework.",
        )
        self.embedding_model = self.config.get(
            "embedding_model", "text-embedding-ada-002"
        )

        # Output configuration
        self.output_dir = self.config.get("output_dir", "./output/llm")

        # Logging
        self.log_level = self.config.get("log_level", "INFO")
        self.log_to_console = self.config.get("log_to_console", True)
        self.logger = get_logger(
            __name__, level=self.log_level, console=self.log_to_console
        )

        # State
        self.pepperpy: Any = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize LLM provider and resources."""
        if self.initialized:
            return

        try:
            # Import pepperpy facade
            from pepperpy.facade import PepperPyFacade

            # Create output directory if needed
            os.makedirs(self.output_dir, exist_ok=True)

            # Initialize PepperPy facade with LLM provider
            self.pepperpy = PepperPyFacade()

            # Configure the LLM provider
            llm_config = {
                "api_key": self.api_key,
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            # Add provider-specific config
            if self.provider == "openai":
                # For OpenAI embedding model
                llm_config["embedding_model"] = self.embedding_model

            # Set up the LLM provider
            self.pepperpy.with_llm(self.provider, **llm_config)

            # Initialize the facade
            await self.pepperpy.initialize()

            self.initialized = True
            self.logger.info(
                f"Initialized LLM interaction workflow with {self.provider} provider"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM workflow: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized or self.pepperpy is None:
            return

        try:
            if hasattr(self.pepperpy, "cleanup"):
                await self.pepperpy.cleanup()
            self.pepperpy = None
            self.initialized = False
            self.logger.info("Cleaned up LLM interaction workflow resources")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    async def _text_completion(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute text completion task.

        Args:
            input_data: Input data containing prompt and options

        Returns:
            Completion result
        """
        if not self.initialized or self.pepperpy is None:
            await self.initialize()
            if not self.initialized:
                return {"error": "Failed to initialize LLM provider", "success": False}

        prompt = input_data.get("prompt", "")
        if not prompt:
            return {"error": "No prompt provided", "success": False}

        options = input_data.get("options", {})

        try:
            # Make sure we can access the LLM provider
            if not hasattr(self.pepperpy, "llm"):
                return {
                    "error": "LLM provider not properly initialized",
                    "success": False,
                }

            # Call LLM provider for completion
            if hasattr(self.pepperpy.llm, "complete"):
                result = await self.pepperpy.llm.complete(prompt, **options)
            else:
                # Fall back to chat if complete is not available
                messages = [{"role": "user", "content": prompt}]
                result = await self.pepperpy.llm.chat(messages, **options)

            return {
                "text": result,
                "success": True,
                "prompt": prompt,
                "model": self.model,
                "provider": self.provider,
            }
        except Exception as e:
            self.logger.error(f"Text completion error: {e}")
            return {"error": str(e), "success": False}

    async def _chat(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute chat task.

        Args:
            input_data: Input data containing messages and options

        Returns:
            Chat result
        """
        if not self.initialized or self.pepperpy is None:
            await self.initialize()
            if not self.initialized:
                return {"error": "Failed to initialize LLM provider", "success": False}

        # Make sure we can access the LLM provider
        if not hasattr(self.pepperpy, "llm"):
            return {"error": "LLM provider not properly initialized", "success": False}

        messages = input_data.get("messages", [])

        # Add system message if not present and system_prompt is configured
        if self.system_prompt and not any(m.get("role") == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        options = input_data.get("options", {})

        try:
            # Call LLM provider for chat
            result = await self.pepperpy.llm.chat(messages, **options)

            return {
                "text": result,
                "success": True,
                "messages": messages,
                "model": self.model,
                "provider": self.provider,
            }
        except Exception as e:
            self.logger.error(f"Chat error: {e}")
            return {"error": str(e), "success": False}

    async def _stream_chat(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute streaming chat task.

        Args:
            input_data: Input data containing messages/prompt and options

        Returns:
            Chat result with streaming output
        """
        if not self.initialized or self.pepperpy is None:
            await self.initialize()
            if not self.initialized:
                return {"error": "Failed to initialize LLM provider", "success": False}

        # Make sure we can access the LLM provider
        if not hasattr(self.pepperpy, "llm"):
            return {"error": "LLM provider not properly initialized", "success": False}

        # Messages can be provided directly or constructed from prompt
        messages = input_data.get("messages", [])
        prompt = input_data.get("prompt", "")

        if not messages and prompt:
            messages = [{"role": "user", "content": prompt}]

        # Add system message if not present and system_prompt is configured
        if self.system_prompt and not any(m.get("role") == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        options = input_data.get("options", {})

        try:
            # Get the client output callback if available
            callback = input_data.get("callback")

            # Call LLM provider for streaming chat
            full_response = ""

            if hasattr(self.pepperpy.llm, "stream_chat"):
                # Initialize an empty response
                print("Streaming response: ", end="", flush=True)

                async for chunk in self.pepperpy.llm.stream_chat(messages, **options):
                    # Print the chunk if no callback
                    if not callback:
                        print(chunk, end="", flush=True)
                    else:
                        # Call the callback with the chunk
                        await callback(chunk)

                    # Accumulate the full response
                    full_response += chunk

                # Print newline after response if no callback
                if not callback:
                    print()
            else:
                # Fall back to non-streaming chat
                self.logger.warning(
                    "Streaming not supported, falling back to regular chat"
                )
                result = await self.pepperpy.llm.chat(messages, **options)
                full_response = result

                # Print the result if no callback
                if not callback:
                    print(result)
                else:
                    await callback(result)

            return {
                "text": full_response,
                "success": True,
                "messages": messages,
                "model": self.model,
                "provider": self.provider,
            }
        except Exception as e:
            self.logger.error(f"Stream chat error: {e}")
            return {"error": str(e), "success": False}

    async def _embedding(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Generate embeddings for texts.

        Args:
            input_data: Input data containing texts to embed

        Returns:
            Embedding result
        """
        if not self.initialized or self.pepperpy is None:
            await self.initialize()
            if not self.initialized:
                return {"error": "Failed to initialize LLM provider", "success": False}

        # Make sure we can access the LLM provider
        if not hasattr(self.pepperpy, "llm"):
            return {"error": "LLM provider not properly initialized", "success": False}

        # Can handle either a single text or a list of texts
        texts = input_data.get("texts", [])
        text = input_data.get("text", "")

        if text and not texts:
            texts = [text]

        if not texts:
            return {"error": "No text provided for embedding", "success": False}

        options = input_data.get("options", {})

        try:
            # Call LLM provider for embeddings
            if hasattr(self.pepperpy.llm, "get_embeddings"):
                embeddings = await self.pepperpy.llm.get_embeddings(texts, **options)

                # Save embeddings to file if requested
                output_file = input_data.get("output_file", "")
                if output_file and self.output_dir:
                    output_path = Path(self.output_dir) / output_file
                    with open(output_path, "w") as f:
                        json.dump({"embeddings": embeddings}, f)
                    self.logger.info(f"Saved embeddings to {output_path}")

                return {
                    "embeddings": embeddings,
                    "success": True,
                    "count": len(embeddings),
                    "model": self.embedding_model,
                    "provider": self.provider,
                }
            else:
                return {
                    "error": "Embeddings not supported by provider",
                    "success": False,
                }
        except Exception as e:
            self.logger.error(f"Embedding error: {e}")
            return {"error": str(e), "success": False}

    async def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """Execute the LLM interaction workflow.

        Args:
            data: Input data with task and parameters

        Returns:
            Results of the workflow execution
        """
        try:
            # Initialize if not already initialized
            if not self.initialized:
                await self.initialize()

            # Get task and input
            task = data.get("task", "")
            input_data = data.get("input", {})

            # Handle different tasks
            if task == "text_completion":
                return await self._text_completion(input_data)
            elif task == "chat":
                return await self._chat(input_data)
            elif task == "stream_chat":
                return await self._stream_chat(input_data)
            elif task == "embedding":
                return await self._embedding(input_data)
            else:
                return {"error": f"Unsupported task: {task}", "success": False}
        except Exception as e:
            self.logger.error(f"Workflow execution error: {e}")
            return {"error": str(e), "success": False}
        finally:
            # We don't cleanup after each execution to allow for
            # stateful interactions like chat history
            pass

    async def stream(self, data: dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream results from the LLM interaction workflow.

        Args:
            data: Input data with task and parameters

        Yields:
            Chunks of the streamed response
        """
        # Initialize if not already initialized
        if not self.initialized or self.pepperpy is None:
            await self.initialize()
            if not self.initialized:
                yield "Failed to initialize LLM provider"
                return

        # Make sure we can access the LLM provider
        if not hasattr(self.pepperpy, "llm"):
            yield "LLM provider not properly initialized"
            return

        # Get task and input
        task = data.get("task", "")
        input_data = data.get("input", {})

        if task != "stream_chat":
            yield f"Streaming only supported for 'stream_chat' task, not '{task}'"
            return

        messages = input_data.get("messages", [])
        prompt = input_data.get("prompt", "")

        if not messages and prompt:
            messages = [{"role": "user", "content": prompt}]

        # Add system message if not present and system_prompt is configured
        if self.system_prompt and not any(m.get("role") == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        options = input_data.get("options", {})

        try:
            if hasattr(self.pepperpy.llm, "stream_chat"):
                async for chunk in self.pepperpy.llm.stream_chat(messages, **options):
                    yield chunk
            else:
                # Fall back to non-streaming chat
                result = await self.pepperpy.llm.chat(messages, **options)
                yield result
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
            yield f"Error: {e!s}"
