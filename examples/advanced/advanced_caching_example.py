#!/usr/bin/env python
"""Example demonstrating advanced caching strategies in PepperPy.

This example demonstrates various caching strategies available in PepperPy:
- TTL-based caching
- Tag-based invalidation
- Metadata support
- Async operations
- Memory management

Each strategy is demonstrated with practical examples and explanations.
"""

import asyncio
import time
from typing import Dict, List, Set, Union

from pepperpy.cache.providers.memory import MemoryCacheProvider
from pepperpy.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)


class UserCache:
    """Example cache manager for user-related data."""

    def __init__(self) -> None:
        """Initialize the user cache manager."""
        self.cache = MemoryCacheProvider()
        self.setup_cache()

    def setup_cache(self) -> None:
        """Set up cache configuration."""
        # Configure cache provider
        self.cache.configure({
            "max_size": 1000,
            "default_ttl": 300,  # 5 minutes
        })

    async def get_user_data(self, user_id: str) -> Dict[str, Union[str, float]]:
        """Fetch user data with TTL caching.

        Args:
            user_id: The unique identifier of the user

        Returns:
            Dictionary containing user data
        """
        cache_key = f"user:{user_id}"
        cached_data = await self.cache.get(cache_key)

        if cached_data is not None:
            logger.debug(f"Cache hit for user {user_id}")
            return cached_data

        logger.info(f"Fetching user data for {user_id}")
        await asyncio.sleep(0.5)  # Simulate DB query

        user_data = {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "created_at": time.time(),
        }

        await self.cache.set(
            key=cache_key,
            value=user_data,
            ttl=60,  # 1 minute TTL
            tags={"user", f"user:{user_id}"},
        )

        return user_data

    async def get_user_profile(
        self, user_id: str, include_premium: bool = False
    ) -> Dict[str, Union[str, bool, List[str]]]:
        """Fetch user profile with tag-based caching.

        Args:
            user_id: The unique identifier of the user
            include_premium: Whether to include premium features

        Returns:
            Dictionary containing user profile data
        """
        cache_key = f"profile:{user_id}"
        if include_premium:
            cache_key += ":premium"

        cached_data = await self.cache.get(cache_key)

        if cached_data is not None:
            logger.debug(f"Cache hit for profile {user_id}")
            return cached_data

        logger.info(f"Fetching profile for user {user_id}")
        await asyncio.sleep(0.5)  # Simulate DB query

        profile = {
            "id": user_id,
            "name": f"User {user_id}",
            "bio": f"Bio for user {user_id}",
            "avatar_url": f"https://example.com/avatars/{user_id}.jpg",
            "is_premium": include_premium,
        }

        if include_premium:
            profile["premium_features"] = [
                "advanced_analytics",
                "priority_support",
                "custom_themes",
            ]

        # Cache with appropriate tags
        tags: Set[str] = {"profile", f"user:{user_id}"}
        if include_premium:
            tags.add("premium")

        await self.cache.set(
            key=cache_key,
            value=profile,
            ttl=3600
            if include_premium
            else 300,  # 1 hour for premium, 5 min for regular
            tags=tags,
        )

        return profile

    async def get_user_posts(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Union[str, float]]]:
        """Fetch user posts with metadata support.

        Args:
            user_id: The unique identifier of the user
            limit: Maximum number of posts to return

        Returns:
            List of user posts
        """
        cache_key = f"posts:{user_id}:{limit}"
        cached_data = await self.cache.get(cache_key)

        if cached_data is not None:
            logger.debug(f"Cache hit for posts {user_id}")
            return cached_data

        logger.info(f"Fetching {limit} posts for user {user_id}")
        await asyncio.sleep(0.5)  # Simulate DB query

        posts = [
            {
                "id": f"post_{i}",
                "user_id": user_id,
                "title": f"Post {i} by User {user_id}",
                "content": f"Content of post {i}",
                "created_at": time.time() - (i * 3600),
            }
            for i in range(limit)
        ]

        await self.cache.set(
            key=cache_key,
            value=posts,
            ttl=300,  # 5 minutes
            tags={f"user:{user_id}", "posts"},
            metadata={
                "count": len(posts),
                "last_updated": time.time(),
            },
        )

        return posts

    async def update_user(
        self, user_id: str, data: Dict[str, str]
    ) -> Dict[str, Union[str, float]]:
        """Update user data and invalidate related caches.

        Args:
            user_id: The unique identifier of the user
            data: New user data to update

        Returns:
            Updated user data
        """
        logger.info(f"Updating user {user_id}")
        await asyncio.sleep(0.5)  # Simulate DB update

        # Invalidate all caches related to this user
        await self.cache.invalidate_tag(f"user:{user_id}")

        return {
            "id": user_id,
            "name": data.get("name", f"User {user_id}"),
            "email": data.get("email", f"user{user_id}@example.com"),
            "updated_at": time.time(),
        }


async def main() -> None:
    """Run the caching examples."""
    try:
        logger.info("Starting PepperPy Advanced Caching Example")

        # Initialize cache manager
        user_cache = UserCache()

        # Example 1: Basic TTL caching
        user_id = "123"
        logger.info("\n1. Basic TTL Caching Example:")
        user_data = await user_cache.get_user_data(user_id)
        logger.info(f"First call (cache miss): {user_data}")

        cached_data = await user_cache.get_user_data(user_id)
        logger.info(f"Second call (cache hit): {cached_data}")

        # Example 2: Tag-based caching with different TTLs
        logger.info("\n2. Tag-based Caching Example:")
        regular_profile = await user_cache.get_user_profile(user_id)
        logger.info(f"Regular user profile (5min TTL): {regular_profile}")

        premium_profile = await user_cache.get_user_profile(
            user_id, include_premium=True
        )
        logger.info(f"Premium user profile (1h TTL): {premium_profile}")

        # Example 3: Caching with metadata
        logger.info("\n3. Caching with Metadata Example:")
        posts = await user_cache.get_user_posts(user_id, limit=5)
        logger.info(f"User posts: {len(posts)} posts")

        # Example 4: Cache invalidation
        logger.info("\n4. Cache Invalidation Example:")
        update_data = {"name": "Updated User 123"}
        updated_user = await user_cache.update_user(user_id, update_data)
        logger.info(f"Updated user data: {updated_user}")

        # Verify cache invalidation
        new_data = await user_cache.get_user_data(user_id)
        logger.info(f"Fresh data after invalidation: {new_data}")

    except Exception as e:
        logger.error(f"Error in caching example: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
