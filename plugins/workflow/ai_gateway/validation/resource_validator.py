"""Resource validation for AI Gateway workflows."""

from dataclasses import dataclass
from typing import Any

from .validator import ValidationError, ValidationResult


@dataclass
class ResourceLimits:
    """Resource limits configuration."""

    max_memory_mb: int = 1024  # 1GB default
    max_tokens_per_request: int = 4096
    max_parallel_requests: int = 5
    max_retries: int = 3
    request_timeout_sec: int = 30
    max_context_size_mb: int = 100
    max_batch_size: int = 50


class ResourceValidator:
    """Validates resource usage and limits."""

    # Token estimation constants
    CHARS_PER_TOKEN = 4  # Average chars per token
    VISION_BASE_TOKENS = 85  # Base tokens for vision API
    IMAGE_TOKENS = {  # Tokens per image resolution
        "low": 85,
        "medium": 170,
        "high": 340,
        "ultra": 680,
    }

    def __init__(self, limits: ResourceLimits | None = None):
        self.limits = limits or ResourceLimits()
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []

        # Track resource usage
        self._total_memory = 0
        self._active_requests = 0
        self._context_size = 0
        self._batch_sizes: dict[str, int] = {}

    def validate_memory(self, estimated_mb: int, path: str) -> None:
        """Validate memory usage."""
        self._total_memory += estimated_mb

        if estimated_mb > self.limits.max_memory_mb:
            self.errors.append(
                ValidationError(
                    path=path,
                    message=f"Memory usage ({estimated_mb}MB) exceeds limit ({self.limits.max_memory_mb}MB)",
                    details={
                        "estimated_mb": estimated_mb,
                        "limit_mb": self.limits.max_memory_mb,
                    },
                )
            )
        elif estimated_mb > (self.limits.max_memory_mb * 0.8):  # 80% warning threshold
            self.warnings.append(
                ValidationError(
                    path=path,
                    message=f"High memory usage: {estimated_mb}MB (limit: {self.limits.max_memory_mb}MB)",
                    severity="warning",
                    details={
                        "estimated_mb": estimated_mb,
                        "limit_mb": self.limits.max_memory_mb,
                    },
                )
            )

    def validate_tokens(
        self, text: str, path: str, include_images: list[dict[str, Any]] | None = None
    ) -> None:
        """Validate token usage including text and images."""
        # Estimate text tokens
        estimated_tokens = len(text) // self.CHARS_PER_TOKEN

        # Add image tokens if any
        if include_images is not None:
            for img in include_images:
                quality = img.get("quality", "low")
                estimated_tokens += self.VISION_BASE_TOKENS + self.IMAGE_TOKENS.get(
                    quality, self.IMAGE_TOKENS["low"]
                )

        if estimated_tokens > self.limits.max_tokens_per_request:
            self.errors.append(
                ValidationError(
                    path=path,
                    message=f"Token count ({estimated_tokens}) exceeds limit ({self.limits.max_tokens_per_request})",
                    details={
                        "estimated_tokens": estimated_tokens,
                        "limit_tokens": self.limits.max_tokens_per_request,
                    },
                )
            )

    def validate_parallel_requests(self, num_requests: int, path: str) -> None:
        """Validate number of parallel requests."""
        self._active_requests += num_requests

        if self._active_requests > self.limits.max_parallel_requests:
            self.errors.append(
                ValidationError(
                    path=path,
                    message=f"Too many parallel requests ({self._active_requests}), max allowed: {self.limits.max_parallel_requests}",
                    details={
                        "current": self._active_requests,
                        "limit": self.limits.max_parallel_requests,
                    },
                )
            )

    def validate_context_size(self, size_mb: float, path: str) -> None:
        """Validate context size for RAG operations."""
        self._context_size += size_mb

        if size_mb > self.limits.max_context_size_mb:
            self.errors.append(
                ValidationError(
                    path=path,
                    message=f"Context size ({size_mb}MB) exceeds limit ({self.limits.max_context_size_mb}MB)",
                    details={
                        "size_mb": size_mb,
                        "limit_mb": self.limits.max_context_size_mb,
                    },
                )
            )

    def validate_batch_operation(
        self, operation_type: str, batch_size: int, path: str
    ) -> None:
        """Validate batch operation size."""
        current = self._batch_sizes.get(operation_type, 0) + batch_size
        self._batch_sizes[operation_type] = current

        if batch_size > self.limits.max_batch_size:
            self.errors.append(
                ValidationError(
                    path=path,
                    message=f"Batch size ({batch_size}) exceeds limit ({self.limits.max_batch_size}) for {operation_type}",
                    details={
                        "batch_size": batch_size,
                        "limit": self.limits.max_batch_size,
                    },
                )
            )

    def validate_step_resources(self, step: dict[str, Any], path: str) -> None:
        """Validate resources for a workflow step."""
        step_type = step.get("type")

        if step_type == "chat":
            # Validate chat message tokens
            messages = step.get("messages", [])
            total_text = ""
            images = []

            for msg in messages:
                if isinstance(msg.get("content"), str):
                    total_text += msg["content"]
                elif (
                    isinstance(msg.get("content"), dict)
                    and "image_url" in msg["content"]
                ):
                    images.append(msg["content"])

            self.validate_tokens(total_text, f"{path}.messages", images)

        elif step_type == "rag":
            # Validate RAG context size
            context_text = step.get("context_text", "")
            if context_text:
                # Rough estimation: 1MB = 1 million chars
                size_mb = len(context_text) / 1_000_000
                self.validate_context_size(size_mb, f"{path}.context_text")

            # Validate query tokens
            query = step.get("query", "")
            self.validate_tokens(query, f"{path}.query")

        elif step_type == "vision":
            # Validate vision prompt
            prompt = step.get("prompt", "")
            image_config = {"quality": step.get("image_quality", "low")}
            self.validate_tokens(prompt, f"{path}.prompt", [image_config])

        elif step_type == "parallel":
            # Validate parallel operations
            operations = step.get("operations", [])
            self.validate_parallel_requests(len(operations), f"{path}.operations")

            # Validate batch operations
            if operations:
                self.validate_batch_operation("parallel_ops", len(operations), path)

    def get_result(self) -> ValidationResult:
        """Get validation result with resource usage summary."""
        is_valid = len(self.errors) == 0

        # Add resource usage summary
        if self._total_memory > 0 or self._context_size > 0:
            self.warnings.append(
                ValidationError(
                    path="",
                    message="Resource usage summary",
                    severity="warning",
                    details={
                        "total_memory_mb": self._total_memory,
                        "context_size_mb": self._context_size,
                        "active_requests": self._active_requests,
                        "batch_operations": dict(self._batch_sizes),
                    },
                )
            )

        return ValidationResult(
            is_valid=is_valid, errors=self.errors, warnings=self.warnings
        )
