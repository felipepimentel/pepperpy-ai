#!/usr/bin/env python
"""Example demonstrating advanced caching strategies in PepperPy.

This example demonstrates the usage of advanced caching strategies with TTL
and invalidation mechanisms in PepperPy.
"""

import asyncio
import time
from typing import Dict, List, Optional

from pepperpy.utils.caching import (
    CacheInvalidationRule,
    DynamicTTLCachePolicy,
    InvalidationStrategy,
    SizeLimitedCachePolicy,
    async_cached,
    cached,
    get_cache_invalidator,
)
from pepperpy.utils.logging import get_logger

# Logger for this example
logger = get_logger(__name__)


# Example 1: Basic caching with TTL
@cached(ttl=60)
def fetch_user_data(user_id: str) -> Dict:
    """Fetch user data from a simulated database.

    Args:
        user_id: The ID of the user to fetch

    Returns:
        The user data
    """
    logger.info(f"Fetching user data for {user_id} from database")
    # Simulate a database query
    time.sleep(0.5)
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "created_at": time.time(),
    }


# Example 2: Caching with dynamic TTL
def calculate_ttl(key: str, value: Dict) -> Optional[int]:
    """Calculate TTL based on the value.

    Args:
        key: The cache key
        value: The value to cache

    Returns:
        The TTL in seconds, or None for no expiration
    """
    # Use a longer TTL for premium users
    if value.get("is_premium", False):
        return 3600  # 1 hour
    else:
        return 300  # 5 minutes


@cached(policy=DynamicTTLCachePolicy(calculate_ttl))
def fetch_user_profile(user_id: str, include_premium: bool = False) -> Dict:
    """Fetch user profile from a simulated database.

    Args:
        user_id: The ID of the user to fetch
        include_premium: Whether to include premium information

    Returns:
        The user profile
    """
    logger.info(f"Fetching user profile for {user_id} from database")
    # Simulate a database query
    time.sleep(0.5)
    profile = {
        "id": user_id,
        "name": f"User {user_id}",
        "bio": f"This is the bio for user {user_id}",
        "avatar_url": f"https://example.com/avatars/{user_id}.jpg",
        "is_premium": include_premium,
    }
    if include_premium:
        profile["premium_features"] = ["feature1", "feature2", "feature3"]
    return profile


# Example 3: Caching with size limits
@cached(policy=SizeLimitedCachePolicy(max_size=1000, ttl=300))
def fetch_user_posts(user_id: str, limit: int = 10) -> List[Dict]:
    """Fetch user posts from a simulated database.

    Args:
        user_id: The ID of the user to fetch posts for
        limit: The maximum number of posts to fetch

    Returns:
        The user posts
    """
    logger.info(f"Fetching {limit} posts for user {user_id} from database")
    # Simulate a database query
    time.sleep(0.5)
    return [
        {
            "id": f"post{i}",
            "user_id": user_id,
            "title": f"Post {i} by User {user_id}",
            "content": f"This is the content of post {i} by user {user_id}",
            "created_at": time.time() - i * 3600,
        }
        for i in range(limit)
    ]


# Example 4: Caching with dependency invalidation
def setup_dependency_invalidation():
    """Set up dependency invalidation rules."""
    # Get the cache invalidator
    invalidator = get_cache_invalidator()

    # Add a rule for user data
    invalidator.add_rule(
        "fetch_user_data",
        CacheInvalidationRule(
            strategy=InvalidationStrategy.DEPENDENCY,
            dependencies=["user"],
        ),
    )

    # Add a rule for user profile
    invalidator.add_rule(
        "fetch_user_profile",
        CacheInvalidationRule(
            strategy=InvalidationStrategy.DEPENDENCY,
            dependencies=["user"],
        ),
    )

    # Add a rule for user posts
    invalidator.add_rule(
        "fetch_user_posts",
        CacheInvalidationRule(
            strategy=InvalidationStrategy.DEPENDENCY,
            dependencies=["user", "post"],
        ),
    )


@cached(invalidator=get_cache_invalidator())
def update_user(user_id: str, data: Dict) -> Dict:
    """Update user data in a simulated database.

    Args:
        user_id: The ID of the user to update
        data: The data to update

    Returns:
        The updated user data
    """
    logger.info(f"Updating user {user_id} in database")
    # Simulate a database update
    time.sleep(0.5)
    # Invalidate user-related caches
    invalidator = get_cache_invalidator()
    invalidator.invalidate_by_dependency(f"user:{user_id}")
    return {
        "id": user_id,
        "name": data.get("name", f"User {user_id}"),
        "email": data.get("email", f"user{user_id}@example.com"),
        "updated_at": time.time(),
    }


# Example 5: Asynchronous caching
@async_cached(ttl=60)
async def fetch_user_data_async(user_id: str) -> Dict:
    """Fetch user data asynchronously from a simulated database.

    Args:
        user_id: The ID of the user to fetch

    Returns:
        The user data
    """
    logger.info(f"Fetching user data for {user_id} from database (async)")
    # Simulate an asynchronous database query
    await asyncio.sleep(0.5)
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "created_at": time.time(),
    }


# Example 6: Version-based invalidation
def setup_version_invalidation():
    """Set up version-based invalidation rules."""
    # Get the cache invalidator
    invalidator = get_cache_invalidator()

    # Add a rule for API responses
    invalidator.add_rule(
        "fetch_api_data",
        CacheInvalidationRule(
            strategy=InvalidationStrategy.VERSION,
            version="1.0",
        ),
    )


@cached(key_prefix="api", invalidator=get_cache_invalidator())
def fetch_api_data(endpoint: str) -> Dict:
    """Fetch data from a simulated API.

    Args:
        endpoint: The API endpoint to fetch data from

    Returns:
        The API response
    """
    logger.info(f"Fetching data from API endpoint {endpoint}")
    # Simulate an API request
    time.sleep(0.5)
    return {
        "endpoint": endpoint,
        "data": f"Data from {endpoint}",
        "timestamp": time.time(),
    }


def update_api_version():
    """Update the API version, invalidating all API caches."""
    # Get the cache invalidator
    invalidator = get_cache_invalidator()

    # Update the version
    invalidator.invalidate_by_version("fetch_api_data", "1.1")
    logger.info("Updated API version to 1.1, invalidating all API caches")


# Example 7: LRU-based invalidation
def setup_lru_invalidation():
    """Set up LRU-based invalidation rules."""
    # Get the cache invalidator
    invalidator = get_cache_invalidator()

    # Add a rule for search results
    invalidator.add_rule(
        "search_results",
        CacheInvalidationRule(
            strategy=InvalidationStrategy.LRU,
            max_size=5,
        ),
    )


@cached(key_prefix="search", invalidator=get_cache_invalidator())
def search(query: str) -> List[Dict]:
    """Search for items matching a query.

    Args:
        query: The search query

    Returns:
        The search results
    """
    logger.info(f"Searching for '{query}'")
    # Simulate a search
    time.sleep(0.5)
    return [
        {
            "id": f"result{i}",
            "title": f"Result {i} for '{query}'",
            "relevance": 1.0 - (i * 0.1),
        }
        for i in range(10)
    ]


async def main():
    """Run the example."""
    # Set up invalidation rules
    setup_dependency_invalidation()
    setup_version_invalidation()
    setup_lru_invalidation()

    # Example 1: Basic caching with TTL
    logger.info("Example 1: Basic caching with TTL")
    user1 = fetch_user_data("1")
    logger.info(f"User 1: {user1}")
    # This should use the cache
    user1_again = fetch_user_data("1")
    logger.info(f"User 1 (cached): {user1_again}")

    # Example 2: Caching with dynamic TTL
    logger.info("\nExample 2: Caching with dynamic TTL")
    profile1 = fetch_user_profile("1")
    logger.info(f"Profile 1: {profile1}")
    # This should use the cache
    profile1_again = fetch_user_profile("1")
    logger.info(f"Profile 1 (cached): {profile1_again}")
    # This should use a different TTL
    profile2 = fetch_user_profile("2", include_premium=True)
    logger.info(f"Profile 2 (premium): {profile2}")

    # Example 3: Caching with size limits
    logger.info("\nExample 3: Caching with size limits")
    posts1 = fetch_user_posts("1", limit=5)
    logger.info(f"Posts for user 1: {len(posts1)} posts")
    # This should use the cache
    posts1_again = fetch_user_posts("1", limit=5)
    logger.info(f"Posts for user 1 (cached): {len(posts1_again)} posts")

    # Example 4: Caching with dependency invalidation
    logger.info("\nExample 4: Caching with dependency invalidation")
    user2 = fetch_user_data("2")
    logger.info(f"User 2: {user2}")
    # Update the user, which should invalidate the cache
    updated_user2 = update_user("2", {"name": "Updated User 2"})
    logger.info(f"Updated user 2: {updated_user2}")
    # This should not use the cache
    user2_after_update = fetch_user_data("2")
    logger.info(f"User 2 after update: {user2_after_update}")

    # Example 5: Asynchronous caching
    logger.info("\nExample 5: Asynchronous caching")
    user3 = await fetch_user_data_async("3")
    logger.info(f"User 3 (async): {user3}")
    # This should use the cache
    user3_again = await fetch_user_data_async("3")
    logger.info(f"User 3 (async, cached): {user3_again}")

    # Example 6: Version-based invalidation
    logger.info("\nExample 6: Version-based invalidation")
    api_data1 = fetch_api_data("users")
    logger.info(f"API data for 'users': {api_data1}")
    # This should use the cache
    api_data1_again = fetch_api_data("users")
    logger.info(f"API data for 'users' (cached): {api_data1_again}")
    # Update the API version, which should invalidate the cache
    update_api_version()
    # This should not use the cache
    api_data1_after_update = fetch_api_data("users")
    logger.info(f"API data for 'users' after version update: {api_data1_after_update}")

    # Example 7: LRU-based invalidation
    logger.info("\nExample 7: LRU-based invalidation")
    # Perform several searches
    for query in ["apple", "banana", "cherry", "date", "elderberry", "fig"]:
        results = search(query)
        logger.info(f"Search results for '{query}': {len(results)} results")

    # The first search should have been evicted
    logger.info("Searching for 'apple' again (should not use cache):")
    apple_results = search("apple")
    logger.info(f"Search results for 'apple': {len(apple_results)} results")

    # The last search should still be in the cache
    logger.info("Searching for 'fig' again (should use cache):")
    fig_results = search("fig")
    logger.info(f"Search results for 'fig': {len(fig_results)} results")


if __name__ == "__main__":
    asyncio.run(main())
