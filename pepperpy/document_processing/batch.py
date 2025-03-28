"""Batch processing for document handling.

This module provides functionality for batch processing documents,
including optional parallelization.
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from pepperpy.core.base import PepperpyError

logger = logging.getLogger(__name__)


class BatchProcessingError(PepperpyError):
    """Error raised during batch processing operations."""

    pass


class BatchResult:
    """Result of batch processing job.

    Stores information about successful and failed processing
    operations during batch job execution.
    """

    def __init__(self) -> None:
        """Initialize batch result."""
        self.successful: List[Path] = []
        self.failed: Dict[Path, str] = {}
        self.errors: List[Exception] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    @property
    def total_count(self) -> int:
        """Get total number of files processed."""
        return len(self.successful) + len(self.failed)

    @property
    def success_count(self) -> int:
        """Get number of successfully processed files."""
        return len(self.successful)

    @property
    def failure_count(self) -> int:
        """Get number of failed files."""
        return len(self.failed)

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100

    @property
    def duration(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if self.start_time is None or self.end_time is None:
            return None
        return self.end_time - self.start_time

    def add_success(self, file_path: Path) -> None:
        """Add successful file processing result."""
        self.successful.append(file_path)

    def add_failure(self, file_path: Path, reason: str) -> None:
        """Add failed file processing result."""
        self.failed[file_path] = reason

    def add_error(self, error: Exception) -> None:
        """Add processing error."""
        self.errors.append(error)

    def merge(self, other: "BatchResult") -> None:
        """Merge another batch result into this one."""
        self.successful.extend(other.successful)
        self.failed.update(other.failed)
        self.errors.extend(other.errors)

    def __str__(self) -> str:
        """Convert to string representation."""
        duration_str = f" in {self.duration:.2f}s" if self.duration is not None else ""
        return (
            f"BatchResult: {self.success_count}/{self.total_count} successful "
            f"({self.success_rate:.1f}%){duration_str}, {self.failure_count} failed, "
            f"{len(self.errors)} errors"
        )


class BatchProcessor:
    """Processor for batch document operations.

    This class provides functionality for processing documents in batches,
    with optional parallelization.
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        raise_on_error: bool = False,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize batch processor.

        Args:
            max_workers: Maximum number of worker threads
            raise_on_error: Whether to raise exception on first error
            timeout: Timeout for each processing operation (seconds)
            **kwargs: Additional configuration options
        """
        # Set configuration
        self.max_workers = max_workers or os.cpu_count() or 4
        self.raise_on_error = raise_on_error
        self.timeout = timeout
        self.config = kwargs

    def process_files(
        self,
        file_paths: List[Union[str, Path]],
        processor_func: Callable[..., Any],
        extensions: Optional[Set[str]] = None,
        batch_size: Optional[int] = None,
        parallel: bool = True,
        **kwargs: Any,
    ) -> BatchResult:
        """Process files in batches.

        Args:
            file_paths: List of file paths to process
            processor_func: Function to apply to each file
            extensions: Set of file extensions to process (if None, process all)
            batch_size: Size of each batch (if None, use single batch)
            parallel: Whether to process files in parallel
            **kwargs: Additional arguments for processor_func

        Returns:
            BatchResult with processing results

        Raises:
            BatchProcessingError: If processing fails and raise_on_error is True
        """
        import time

        # Convert all paths to Path objects
        paths = [Path(p) if isinstance(p, str) else p for p in file_paths]

        # Filter by extension if specified
        if extensions:
            paths = [p for p in paths if p.suffix.lower() in extensions]

        # Create result
        result = BatchResult()
        result.start_time = time.time()

        # Create batches
        if batch_size:
            batches = [
                paths[i : i + batch_size] for i in range(0, len(paths), batch_size)
            ]
        else:
            batches = [paths]

        try:
            # Process each batch
            for batch in batches:
                batch_result = self._process_batch(
                    batch, processor_func, parallel=parallel, **kwargs
                )
                result.merge(batch_result)

                # Raise exception if any processing failed
                if self.raise_on_error and (
                    batch_result.failure_count > 0 or batch_result.errors
                ):
                    errors = batch_result.errors or [
                        "Processing failed for one or more files"
                    ]
                    raise BatchProcessingError(str(errors[0]))
        finally:
            result.end_time = time.time()

        return result

    def _process_batch(
        self,
        file_paths: List[Path],
        processor_func: Callable[..., Any],
        parallel: bool = True,
        **kwargs: Any,
    ) -> BatchResult:
        """Process a batch of files.

        Args:
            file_paths: List of file paths to process
            processor_func: Function to apply to each file
            parallel: Whether to process files in parallel
            **kwargs: Additional arguments for processor_func

        Returns:
            BatchResult with processing results
        """
        # Create result
        result = BatchResult()

        # Create processing function with fixed kwargs
        process_func = partial(
            self._process_file, processor_func=processor_func, **kwargs
        )

        if parallel and len(file_paths) > 1:
            # Process files in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_path = {
                    executor.submit(process_func, file_path): file_path
                    for file_path in file_paths
                }

                # Process results as they complete
                for future in as_completed(future_to_path):
                    file_path = future_to_path[future]
                    try:
                        success, error_msg = future.result(timeout=self.timeout)
                        if success:
                            result.add_success(file_path)
                        else:
                            result.add_failure(file_path, error_msg)
                    except Exception as e:
                        result.add_failure(file_path, str(e))
                        result.add_error(e)
                        if self.raise_on_error:
                            raise BatchProcessingError(
                                f"Error processing {file_path}: {e}"
                            )
        else:
            # Process files sequentially
            for file_path in file_paths:
                try:
                    success, error_msg = process_func(file_path)
                    if success:
                        result.add_success(file_path)
                    else:
                        result.add_failure(file_path, error_msg)
                except Exception as e:
                    result.add_failure(file_path, str(e))
                    result.add_error(e)
                    if self.raise_on_error:
                        raise BatchProcessingError(f"Error processing {file_path}: {e}")

        return result

    def _process_file(
        self, file_path: Path, processor_func: Callable[..., Any], **kwargs: Any
    ) -> Tuple[bool, str]:
        """Process a single file.

        Args:
            file_path: Path to file
            processor_func: Function to apply to file
            **kwargs: Additional arguments for processor_func

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Check if file exists
            if not file_path.exists():
                return False, f"File not found: {file_path}"

            # Process file
            processor_func(file_path, **kwargs)
            return True, ""
        except Exception as e:
            logger.exception(f"Error processing file {file_path}")
            return False, str(e)


# Global batch processor instance
_batch_processor: Optional[BatchProcessor] = None


def get_batch_processor(
    max_workers: Optional[int] = None,
    raise_on_error: bool = False,
    timeout: Optional[float] = None,
    **kwargs: Any,
) -> BatchProcessor:
    """Get batch processor instance.

    Args:
        max_workers: Maximum number of worker threads
        raise_on_error: Whether to raise exception on first error
        timeout: Timeout for each processing operation (seconds)
        **kwargs: Additional configuration options

    Returns:
        Batch processor instance
    """
    global _batch_processor

    if _batch_processor is None:
        _batch_processor = BatchProcessor(
            max_workers=max_workers,
            raise_on_error=raise_on_error,
            timeout=timeout,
            **kwargs,
        )

    return _batch_processor
