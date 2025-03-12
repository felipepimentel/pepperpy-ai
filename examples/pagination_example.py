#!/usr/bin/env python
"""Example demonstrating standardized pagination and iteration patterns.

This example shows how to use the pagination and iteration patterns provided by
the PepperPy framework. It demonstrates different pagination strategies, page
iterators, and item iterators.
"""

import asyncio
import logging
from dataclasses import dataclass

from pepperpy.core.pagination import (
    Page,
    PaginationConfig,
    PaginationStrategy,
    create_async_item_iterator,
    create_async_page_iterator,
    create_item_iterator,
    create_page_iterator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class Product:
    """Example product class."""

    id: str
    name: str
    price: float
    category: str
    timestamp: float


class ProductRepository:
    """Example repository implementing the Pageable protocol."""

    def __init__(self):
        """Initialize the repository with sample data."""
        self.products = [
            Product("p1", "Laptop", 1200.0, "Electronics", 1609459200.0),
            Product("p2", "Smartphone", 800.0, "Electronics", 1609545600.0),
            Product("p3", "Headphones", 150.0, "Electronics", 1609632000.0),
            Product("p4", "Monitor", 300.0, "Electronics", 1609718400.0),
            Product("p5", "Keyboard", 80.0, "Electronics", 1609804800.0),
            Product("p6", "Mouse", 50.0, "Electronics", 1609891200.0),
            Product("p7", "Tablet", 500.0, "Electronics", 1609977600.0),
            Product("p8", "Printer", 200.0, "Electronics", 1610064000.0),
            Product("p9", "Scanner", 150.0, "Electronics", 1610150400.0),
            Product("p10", "Speaker", 100.0, "Electronics", 1610236800.0),
            Product("p11", "Camera", 600.0, "Electronics", 1610323200.0),
            Product("p12", "Microphone", 120.0, "Electronics", 1610409600.0),
            Product("p13", "Router", 80.0, "Electronics", 1610496000.0),
            Product("p14", "External Hard Drive", 150.0, "Electronics", 1610582400.0),
            Product("p15", "USB Drive", 30.0, "Electronics", 1610668800.0),
            Product("p16", "Webcam", 70.0, "Electronics", 1610755200.0),
            Product("p17", "Gaming Console", 400.0, "Electronics", 1610841600.0),
            Product("p18", "Smart Watch", 250.0, "Electronics", 1610928000.0),
            Product("p19", "Bluetooth Speaker", 80.0, "Electronics", 1611014400.0),
            Product("p20", "Wireless Earbuds", 120.0, "Electronics", 1611100800.0),
        ]

    def get_page(self, config: PaginationConfig) -> Page[Product]:
        """Get a page of products.

        Args:
            config: The pagination configuration

        Returns:
            A page of products
        """
        # Apply filters from config
        filtered_products = self.products.copy()

        # Apply sorting
        if config.sort_by:
            reverse = config.sort_order.lower() == "desc"
            if config.sort_by == "price":
                filtered_products.sort(key=lambda p: p.price, reverse=reverse)
            elif config.sort_by == "name":
                filtered_products.sort(key=lambda p: p.name, reverse=reverse)
            elif config.sort_by == "timestamp":
                filtered_products.sort(key=lambda p: p.timestamp, reverse=reverse)

        # Apply pagination based on strategy
        if config.strategy == PaginationStrategy.OFFSET:
            offset = config.offset
            limit = config.limit or config.page_size
            paginated = filtered_products[offset : offset + limit]
            return Page(
                items=paginated,
                total=len(filtered_products),
                page_size=limit,
                has_next=offset + limit < len(filtered_products),
                has_previous=offset > 0,
            )
        elif config.strategy == PaginationStrategy.PAGE:
            page = config.page
            page_size = config.page_size
            start = (page - 1) * page_size
            end = start + page_size
            paginated = filtered_products[start:end]
            return Page(
                items=paginated,
                total=len(filtered_products),
                page_size=page_size,
                page_number=page,
                has_next=end < len(filtered_products),
                has_previous=page > 1,
            )
        elif config.strategy == PaginationStrategy.CURSOR:
            # Simple cursor-based implementation
            cursor = config.cursor
            direction = config.direction
            page_size = config.page_size

            if cursor is None:
                # First page
                paginated = filtered_products[:page_size]
                next_cursor = paginated[-1].id if paginated else None
                return Page(
                    items=paginated,
                    total=len(filtered_products),
                    page_size=page_size,
                    has_next=len(paginated) == page_size,
                    has_previous=False,
                    next_cursor=next_cursor,
                )
            else:
                # Find the cursor position
                cursor_index = next(
                    (i for i, p in enumerate(filtered_products) if p.id == cursor), -1
                )
                if cursor_index == -1:
                    return Page(
                        items=[],
                        total=len(filtered_products),
                        page_size=page_size,
                        has_next=False,
                        has_previous=False,
                    )

                if direction == "forward":
                    start = cursor_index + 1
                    end = start + page_size
                    paginated = filtered_products[start:end]
                    next_cursor = paginated[-1].id if paginated else None
                    return Page(
                        items=paginated,
                        total=len(filtered_products),
                        page_size=page_size,
                        has_next=end < len(filtered_products),
                        has_previous=True,
                        next_cursor=next_cursor,
                        previous_cursor=cursor,
                    )
                else:  # backward
                    end = cursor_index
                    start = max(0, end - page_size)
                    paginated = filtered_products[start:end]
                    previous_cursor = paginated[0].id if paginated else None
                    return Page(
                        items=paginated,
                        total=len(filtered_products),
                        page_size=page_size,
                        has_next=True,
                        has_previous=start > 0,
                        next_cursor=cursor,
                        previous_cursor=previous_cursor,
                    )
        elif config.strategy == PaginationStrategy.TIME:
            # Time-based pagination
            before = config.before
            after = config.after
            page_size = config.page_size

            if before is not None:
                filtered_products = [
                    p for p in filtered_products if p.timestamp < before
                ]
            if after is not None:
                filtered_products = [
                    p for p in filtered_products if p.timestamp > after
                ]

            # Sort by timestamp
            reverse = config.sort_order.lower() == "desc"
            filtered_products.sort(key=lambda p: p.timestamp, reverse=reverse)

            # Get page
            paginated = filtered_products[:page_size]

            # Determine next/previous timestamps
            next_timestamp = None
            previous_timestamp = None

            if paginated:
                if reverse:  # descending order
                    next_timestamp = (
                        paginated[-1].timestamp if len(paginated) == page_size else None
                    )
                    previous_timestamp = paginated[0].timestamp
                else:  # ascending order
                    next_timestamp = (
                        paginated[-1].timestamp if len(paginated) == page_size else None
                    )
                    previous_timestamp = paginated[0].timestamp

            return Page(
                items=paginated,
                total=len(self.products),  # Total count of all products
                page_size=page_size,
                has_next=len(paginated) == page_size,
                has_previous=before is not None or after is not None,
                next_timestamp=next_timestamp,
                previous_timestamp=previous_timestamp,
            )

        # Default simple pagination
        return Page(
            items=filtered_products[: config.page_size],
            total=len(filtered_products),
            page_size=config.page_size,
        )


class AsyncProductRepository:
    """Example repository implementing the AsyncPageable protocol."""

    def __init__(self):
        """Initialize the repository with sample data."""
        self.products = [
            Product("p1", "Laptop", 1200.0, "Electronics", 1609459200.0),
            Product("p2", "Smartphone", 800.0, "Electronics", 1609545600.0),
            Product("p3", "Headphones", 150.0, "Electronics", 1609632000.0),
            Product("p4", "Monitor", 300.0, "Electronics", 1609718400.0),
            Product("p5", "Keyboard", 80.0, "Electronics", 1609804800.0),
            Product("p6", "Mouse", 50.0, "Electronics", 1609891200.0),
            Product("p7", "Tablet", 500.0, "Electronics", 1609977600.0),
            Product("p8", "Printer", 200.0, "Electronics", 1610064000.0),
            Product("p9", "Scanner", 150.0, "Electronics", 1610150400.0),
            Product("p10", "Speaker", 100.0, "Electronics", 1610236800.0),
            Product("p11", "Camera", 600.0, "Electronics", 1610323200.0),
            Product("p12", "Microphone", 120.0, "Electronics", 1610409600.0),
            Product("p13", "Router", 80.0, "Electronics", 1610496000.0),
            Product("p14", "External Hard Drive", 150.0, "Electronics", 1610582400.0),
            Product("p15", "USB Drive", 30.0, "Electronics", 1610668800.0),
            Product("p16", "Webcam", 70.0, "Electronics", 1610755200.0),
            Product("p17", "Gaming Console", 400.0, "Electronics", 1610841600.0),
            Product("p18", "Smart Watch", 250.0, "Electronics", 1610928000.0),
            Product("p19", "Bluetooth Speaker", 80.0, "Electronics", 1611014400.0),
            Product("p20", "Wireless Earbuds", 120.0, "Electronics", 1611100800.0),
        ]

    async def get_page_async(self, config: PaginationConfig) -> Page[Product]:
        """Get a page of products asynchronously.

        Args:
            config: The pagination configuration

        Returns:
            A page of products
        """
        # Simulate async operation
        await asyncio.sleep(0.1)

        # Apply filters from config
        filtered_products = self.products.copy()

        # Apply sorting
        if config.sort_by:
            reverse = config.sort_order.lower() == "desc"
            if config.sort_by == "price":
                filtered_products.sort(key=lambda p: p.price, reverse=reverse)
            elif config.sort_by == "name":
                filtered_products.sort(key=lambda p: p.name, reverse=reverse)
            elif config.sort_by == "timestamp":
                filtered_products.sort(key=lambda p: p.timestamp, reverse=reverse)

        # Apply pagination based on strategy
        if config.strategy == PaginationStrategy.OFFSET:
            offset = config.offset
            limit = config.limit or config.page_size
            paginated = filtered_products[offset : offset + limit]
            return Page(
                items=paginated,
                total=len(filtered_products),
                page_size=limit,
                has_next=offset + limit < len(filtered_products),
                has_previous=offset > 0,
            )
        elif config.strategy == PaginationStrategy.PAGE:
            page = config.page
            page_size = config.page_size
            start = (page - 1) * page_size
            end = start + page_size
            paginated = filtered_products[start:end]
            return Page(
                items=paginated,
                total=len(filtered_products),
                page_size=page_size,
                page_number=page,
                has_next=end < len(filtered_products),
                has_previous=page > 1,
            )
        elif config.strategy == PaginationStrategy.CURSOR:
            # Simple cursor-based implementation
            cursor = config.cursor
            direction = config.direction
            page_size = config.page_size

            if cursor is None:
                # First page
                paginated = filtered_products[:page_size]
                next_cursor = paginated[-1].id if paginated else None
                return Page(
                    items=paginated,
                    total=len(filtered_products),
                    page_size=page_size,
                    has_next=len(paginated) == page_size,
                    has_previous=False,
                    next_cursor=next_cursor,
                )
            else:
                # Find the cursor position
                cursor_index = next(
                    (i for i, p in enumerate(filtered_products) if p.id == cursor), -1
                )
                if cursor_index == -1:
                    return Page(
                        items=[],
                        total=len(filtered_products),
                        page_size=page_size,
                        has_next=False,
                        has_previous=False,
                    )

                if direction == "forward":
                    start = cursor_index + 1
                    end = start + page_size
                    paginated = filtered_products[start:end]
                    next_cursor = paginated[-1].id if paginated else None
                    return Page(
                        items=paginated,
                        total=len(filtered_products),
                        page_size=page_size,
                        has_next=end < len(filtered_products),
                        has_previous=True,
                        next_cursor=next_cursor,
                        previous_cursor=cursor,
                    )
                else:  # backward
                    end = cursor_index
                    start = max(0, end - page_size)
                    paginated = filtered_products[start:end]
                    previous_cursor = paginated[0].id if paginated else None
                    return Page(
                        items=paginated,
                        total=len(filtered_products),
                        page_size=page_size,
                        has_next=True,
                        has_previous=start > 0,
                        next_cursor=cursor,
                        previous_cursor=previous_cursor,
                    )
        elif config.strategy == PaginationStrategy.TIME:
            # Time-based pagination
            before = config.before
            after = config.after
            page_size = config.page_size

            if before is not None:
                filtered_products = [
                    p for p in filtered_products if p.timestamp < before
                ]
            if after is not None:
                filtered_products = [
                    p for p in filtered_products if p.timestamp > after
                ]

            # Sort by timestamp
            reverse = config.sort_order.lower() == "desc"
            filtered_products.sort(key=lambda p: p.timestamp, reverse=reverse)

            # Get page
            paginated = filtered_products[:page_size]

            # Determine next/previous timestamps
            next_timestamp = None
            previous_timestamp = None

            if paginated:
                if reverse:  # descending order
                    next_timestamp = (
                        paginated[-1].timestamp if len(paginated) == page_size else None
                    )
                    previous_timestamp = paginated[0].timestamp
                else:  # ascending order
                    next_timestamp = (
                        paginated[-1].timestamp if len(paginated) == page_size else None
                    )
                    previous_timestamp = paginated[0].timestamp

            return Page(
                items=paginated,
                total=len(self.products),  # Total count of all products
                page_size=page_size,
                has_next=len(paginated) == page_size,
                has_previous=before is not None or after is not None,
                next_timestamp=next_timestamp,
                previous_timestamp=previous_timestamp,
            )

        # Default simple pagination
        return Page(
            items=filtered_products[: config.page_size],
            total=len(filtered_products),
            page_size=config.page_size,
        )


def example_offset_pagination():
    """Example of offset-based pagination."""
    logger.info("=== Offset-based Pagination Example ===")

    # Create repository
    repo = ProductRepository()

    # Create pagination configuration
    config = PaginationConfig(
        strategy=PaginationStrategy.OFFSET,
        page_size=5,
        offset=0,
        sort_by="price",
        sort_order="desc",
    )

    # Get first page
    page = repo.get_page(config)

    logger.info(f"Page 1 - Items: {len(page.items)}, Total: {page.total}")
    for item in page:
        logger.info(f"  {item.name}: ${item.price}")

    # Get next page
    if page.has_next:
        config.offset += config.page_size
        page = repo.get_page(config)

        logger.info(f"Page 2 - Items: {len(page.items)}, Total: {page.total}")
        for item in page:
            logger.info(f"  {item.name}: ${item.price}")


def example_page_pagination():
    """Example of page-based pagination."""
    logger.info("=== Page-based Pagination Example ===")

    # Create repository
    repo = ProductRepository()

    # Create pagination configuration
    config = PaginationConfig(
        strategy=PaginationStrategy.PAGE,
        page_size=5,
        page=1,
        sort_by="name",
        sort_order="asc",
    )

    # Get first page
    page = repo.get_page(config)

    logger.info(
        f"Page {page.page_number} - Items: {len(page.items)}, Total: {page.total}"
    )
    for item in page:
        logger.info(f"  {item.name}: ${item.price}")

    # Get next page
    if page.has_next:
        config.page += 1
        page = repo.get_page(config)

        logger.info(
            f"Page {page.page_number} - Items: {len(page.items)}, Total: {page.total}"
        )
        for item in page:
            logger.info(f"  {item.name}: ${item.price}")


def example_cursor_pagination():
    """Example of cursor-based pagination."""
    logger.info("=== Cursor-based Pagination Example ===")

    # Create repository
    repo = ProductRepository()

    # Create pagination configuration
    config = PaginationConfig(
        strategy=PaginationStrategy.CURSOR,
        page_size=5,
        cursor=None,  # Start with no cursor
        sort_by="price",
        sort_order="asc",
    )

    # Get first page
    page = repo.get_page(config)

    logger.info(f"First Page - Items: {len(page.items)}, Total: {page.total}")
    for item in page:
        logger.info(f"  {item.name}: ${item.price}")

    # Get next page
    if page.has_next and page.next_cursor:
        config.cursor = page.next_cursor
        config.direction = "forward"
        page = repo.get_page(config)

        logger.info(f"Next Page - Items: {len(page.items)}, Total: {page.total}")
        for item in page:
            logger.info(f"  {item.name}: ${item.price}")


def example_time_pagination():
    """Example of time-based pagination."""
    logger.info("=== Time-based Pagination Example ===")

    # Create repository
    repo = ProductRepository()

    # Create pagination configuration
    config = PaginationConfig(
        strategy=PaginationStrategy.TIME,
        page_size=5,
        sort_by="timestamp",
        sort_order="desc",  # Most recent first
    )

    # Get first page
    page = repo.get_page(config)

    logger.info(f"First Page - Items: {len(page.items)}, Total: {page.total}")
    for item in page:
        logger.info(f"  {item.name}: Timestamp {item.timestamp}")

    # Get next page
    if page.has_next and page.next_timestamp:
        config.before = page.next_timestamp
        page = repo.get_page(config)

        logger.info(f"Next Page - Items: {len(page.items)}, Total: {page.total}")
        for item in page:
            logger.info(f"  {item.name}: Timestamp {item.timestamp}")


def example_page_iterator():
    """Example of using a page iterator."""
    logger.info("=== Page Iterator Example ===")

    # Create repository
    repo = ProductRepository()

    # Create pagination configuration
    config = PaginationConfig(
        strategy=PaginationStrategy.OFFSET,
        page_size=5,
        sort_by="price",
        sort_order="desc",
    )

    # Create page iterator
    iterator = create_page_iterator(repo, config, max_pages=3)

    # Iterate over pages
    for i, page in enumerate(iterator, 1):
        logger.info(f"Page {i} - Items: {len(page.items)}, Total: {page.total}")
        for item in page:
            logger.info(f"  {item.name}: ${item.price}")


def example_item_iterator():
    """Example of using an item iterator."""
    logger.info("=== Item Iterator Example ===")

    # Create repository
    repo = ProductRepository()

    # Create pagination configuration
    config = PaginationConfig(
        strategy=PaginationStrategy.OFFSET,
        page_size=5,
        sort_by="name",
        sort_order="asc",
    )

    # Create item iterator
    iterator = create_item_iterator(repo, config, max_items=8)

    # Iterate over items
    for i, item in enumerate(iterator, 1):
        logger.info(f"Item {i}: {item.name} - ${item.price}")


async def example_async_pagination():
    """Example of asynchronous pagination."""
    logger.info("=== Asynchronous Pagination Example ===")

    # Create repository
    repo = AsyncProductRepository()

    # Create pagination configuration
    config = PaginationConfig(
        strategy=PaginationStrategy.OFFSET,
        page_size=5,
        sort_by="price",
        sort_order="desc",
    )

    # Get first page
    page = await repo.get_page_async(config)

    logger.info(f"Async Page 1 - Items: {len(page.items)}, Total: {page.total}")
    for item in page:
        logger.info(f"  {item.name}: ${item.price}")

    # Get next page
    if page.has_next:
        config.offset += config.page_size
        page = await repo.get_page_async(config)

        logger.info(f"Async Page 2 - Items: {len(page.items)}, Total: {page.total}")
        for item in page:
            logger.info(f"  {item.name}: ${item.price}")


async def example_async_page_iterator():
    """Example of using an asynchronous page iterator."""
    logger.info("=== Asynchronous Page Iterator Example ===")

    # Create repository
    repo = AsyncProductRepository()

    # Create pagination configuration
    config = PaginationConfig(
        strategy=PaginationStrategy.OFFSET,
        page_size=5,
        sort_by="price",
        sort_order="desc",
    )

    # Create page iterator
    iterator = create_async_page_iterator(repo, config, max_pages=2)

    # Iterate over pages
    page_num = 1
    async for page in iterator:
        logger.info(
            f"Async Page {page_num} - Items: {len(page.items)}, Total: {page.total}"
        )
        for item in page:
            logger.info(f"  {item.name}: ${item.price}")
        page_num += 1


async def example_async_item_iterator():
    """Example of using an asynchronous item iterator."""
    logger.info("=== Asynchronous Item Iterator Example ===")

    # Create repository
    repo = AsyncProductRepository()

    # Create pagination configuration
    config = PaginationConfig(
        strategy=PaginationStrategy.OFFSET,
        page_size=5,
        sort_by="name",
        sort_order="asc",
    )

    # Create item iterator
    iterator = create_async_item_iterator(repo, config, max_items=8)

    # Iterate over items
    item_num = 1
    async for item in iterator:
        logger.info(f"Async Item {item_num}: {item.name} - ${item.price}")
        item_num += 1


async def run_async_examples():
    """Run all asynchronous examples."""
    await example_async_pagination()
    await example_async_page_iterator()
    await example_async_item_iterator()


def main():
    """Run all examples."""
    # Run synchronous examples
    example_offset_pagination()
    example_page_pagination()
    example_cursor_pagination()
    example_time_pagination()
    example_page_iterator()
    example_item_iterator()

    # Run asynchronous examples
    asyncio.run(run_async_examples())


if __name__ == "__main__":
    main()
