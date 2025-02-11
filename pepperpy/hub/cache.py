"""Caching system for workflow results.

This module provides functionality to cache and retrieve workflow results,
helping to optimize performance by avoiding redundant computations.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
from pydantic import BaseModel

from pepperpy.core.errors import CacheError
from pepperpy.monitoring import logger

log = logger.bind(module="cache")


class CacheEntry(BaseModel):
    """Model for a cached workflow result."""

    workflow_name: str
    workflow_version: str
    inputs_hash: str
    result: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class WorkflowCache:
    """Cache manager for workflow results."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the workflow cache.

        Args:
        ----
            cache_dir: Optional path to the cache directory. If not provided,
                      will use PEPPERPY_CACHE_DIR env var or default to ~/.pepper_hub/cache

        """
        self.cache_dir = cache_dir or Path(
            os.getenv(
                "PEPPERPY_CACHE_DIR",
                str(Path.home() / ".pepper_hub" / "cache" / "workflows"),
            )
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_inputs_hash(self, inputs: Dict[str, Any]) -> str:
        """Compute a deterministic hash of workflow inputs.

        Args:
        ----
            inputs: Workflow input parameters

        Returns:
        -------
            Hash string of the inputs

        """
        # Sort dictionary to ensure deterministic serialization
        sorted_inputs = dict(sorted(inputs.items()))
        inputs_json = json.dumps(sorted_inputs, sort_keys=True)
        return hashlib.sha256(inputs_json.encode()).hexdigest()

    def _get_cache_path(
        self, workflow_name: str, workflow_version: str, inputs_hash: str
    ) -> Path:
        """Get the path where a cache entry should be stored.

        Args:
        ----
            workflow_name: Name of the workflow
            workflow_version: Version of the workflow
            inputs_hash: Hash of the workflow inputs

        Returns:
        -------
            Path where the cache entry should be stored

        """
        return self.cache_dir / workflow_name / workflow_version / f"{inputs_hash}.json"

    async def get(
        self,
        workflow_name: str,
        workflow_version: str,
        inputs: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Get cached results for a workflow execution.

        Args:
        ----
            workflow_name: Name of the workflow
            workflow_version: Version of the workflow
            inputs: Workflow input parameters

        Returns:
        -------
            Cached results if found and valid, None otherwise

        Raises:
        ------
            CacheError: If there's an error reading from cache

        """
        inputs_hash = self._compute_inputs_hash(inputs)
        cache_path = self._get_cache_path(workflow_name, workflow_version, inputs_hash)

        if not cache_path.exists():
            return None

        try:
            async with aiofiles.open(cache_path) as f:
                data = json.loads(await f.read())
                entry = CacheEntry(**data)

                # Check if cache has expired
                if entry.expires_at and entry.expires_at < datetime.now():
                    await self.invalidate(workflow_name, workflow_version, inputs)
                    return None

                return entry.result

        except Exception as e:
            log.error(
                "Failed to read cache",
                workflow=workflow_name,
                version=workflow_version,
                error=str(e),
            )
            raise CacheError(f"Failed to read cache: {e}")

    async def set(
        self,
        workflow_name: str,
        workflow_version: str,
        inputs: Dict[str, Any],
        result: Dict[str, Any],
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Cache the results of a workflow execution.

        Args:
        ----
            workflow_name: Name of the workflow
            workflow_version: Version of the workflow
            inputs: Workflow input parameters
            result: Workflow execution results
            ttl: Optional time-to-live in seconds
            metadata: Optional metadata to store with the cache entry

        Raises:
        ------
            CacheError: If there's an error writing to cache

        """
        inputs_hash = self._compute_inputs_hash(inputs)
        cache_path = self._get_cache_path(workflow_name, workflow_version, inputs_hash)

        # Create parent directories if they don't exist
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            entry = CacheEntry(
                workflow_name=workflow_name,
                workflow_version=workflow_version,
                inputs_hash=inputs_hash,
                result=result,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl) if ttl else None,
                metadata=metadata or {},
            )

            async with aiofiles.open(cache_path, "w") as f:
                await f.write(entry.model_dump_json(indent=2))

        except Exception as e:
            log.error(
                "Failed to write cache",
                workflow=workflow_name,
                version=workflow_version,
                error=str(e),
            )
            raise CacheError(f"Failed to write cache: {e}")

    async def invalidate(
        self,
        workflow_name: str,
        workflow_version: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Invalidate cached results.

        Args:
        ----
            workflow_name: Name of the workflow
            workflow_version: Version of the workflow
            inputs: Optional specific input parameters to invalidate.
                   If None, invalidates all cached results for the workflow version.

        Raises:
        ------
            CacheError: If there's an error invalidating cache

        """
        try:
            if inputs:
                # Invalidate specific cache entry
                inputs_hash = self._compute_inputs_hash(inputs)
                cache_path = self._get_cache_path(
                    workflow_name, workflow_version, inputs_hash
                )
                if cache_path.exists():
                    cache_path.unlink()
            else:
                # Invalidate all cached results for the workflow version
                version_dir = self.cache_dir / workflow_name / workflow_version
                if version_dir.exists():
                    for cache_file in version_dir.glob("*.json"):
                        cache_file.unlink()
                    version_dir.rmdir()

        except Exception as e:
            log.error(
                "Failed to invalidate cache",
                workflow=workflow_name,
                version=workflow_version,
                error=str(e),
            )
            raise CacheError(f"Failed to invalidate cache: {e}")

    async def clear(self) -> None:
        """Clear all cached results.

        Raises
        ------
            CacheError: If there's an error clearing cache

        """
        try:
            if self.cache_dir.exists():
                for workflow_dir in self.cache_dir.glob("*"):
                    if workflow_dir.is_dir():
                        for version_dir in workflow_dir.glob("*"):
                            if version_dir.is_dir():
                                for cache_file in version_dir.glob("*.json"):
                                    cache_file.unlink()
                                version_dir.rmdir()
                        workflow_dir.rmdir()

        except Exception as e:
            log.error("Failed to clear cache", error=str(e))
            raise CacheError(f"Failed to clear cache: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns
        -------
            Dictionary containing cache statistics

        Raises
        ------
            CacheError: If there's an error getting statistics

        """
        try:
            stats = {
                "total_entries": 0,
                "total_size": 0,
                "workflows": {},
            }

            if not self.cache_dir.exists():
                return stats

            for workflow_dir in self.cache_dir.glob("*"):
                if not workflow_dir.is_dir():
                    continue

                workflow_name = workflow_dir.name
                stats["workflows"][workflow_name] = {
                    "versions": {},
                    "total_entries": 0,
                }

                for version_dir in workflow_dir.glob("*"):
                    if not version_dir.is_dir():
                        continue

                    version = version_dir.name
                    version_stats = {
                        "entries": 0,
                        "size": 0,
                        "oldest_entry": None,
                        "newest_entry": None,
                    }

                    for cache_file in version_dir.glob("*.json"):
                        version_stats["entries"] += 1
                        version_stats["size"] += cache_file.stat().st_size

                        try:
                            async with aiofiles.open(cache_file) as f:
                                data = json.loads(await f.read())
                                entry = CacheEntry(**data)
                                created_at = entry.created_at

                                if (
                                    version_stats["oldest_entry"] is None
                                    or created_at < version_stats["oldest_entry"]
                                ):
                                    version_stats["oldest_entry"] = created_at

                                if (
                                    version_stats["newest_entry"] is None
                                    or created_at > version_stats["newest_entry"]
                                ):
                                    version_stats["newest_entry"] = created_at

                        except Exception as e:
                            log.warning(
                                "Failed to read cache entry",
                                file=str(cache_file),
                                error=str(e),
                            )

                    stats["workflows"][workflow_name]["versions"][version] = (
                        version_stats
                    )
                    stats["workflows"][workflow_name]["total_entries"] += version_stats[
                        "entries"
                    ]
                    stats["total_entries"] += version_stats["entries"]
                    stats["total_size"] += version_stats["size"]

            return stats

        except Exception as e:
            log.error("Failed to get cache stats", error=str(e))
            raise CacheError(f"Failed to get cache statistics: {e}")
