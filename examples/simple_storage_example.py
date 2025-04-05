#!/usr/bin/env python
"""
Simple Storage Example.

This example demonstrates basic file storage using the framework's API without
relying on complex models.
"""

import asyncio
import json
import os
from pathlib import Path
from tempfile import gettempdir


async def main():
    """Run the simple storage example."""
    print("PepperPy Simple Storage Example")
    print("===============================")

    # Setup storage paths
    temp_dir = Path(gettempdir()) / "pepperpy_examples"
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / "simple_storage.json"

    # Create a simple in-memory storage
    data_store = {}

    # Store some data
    print("\nStoring data...")
    data_store["user1"] = {
        "id": "user1",
        "name": "John Doe",
        "email": "john@example.com",
        "created_at": "2023-01-01T12:00:00Z",
    }

    data_store["user2"] = {
        "id": "user2",
        "name": "Jane Smith",
        "email": "jane@example.com",
        "created_at": "2023-01-02T14:30:00Z",
    }

    # Save to file
    with open(db_path, "w") as f:
        json.dump(data_store, f, indent=2)

    print(f"Data stored to {db_path}")

    # Retrieve data
    print("\nRetrieving data...")
    with open(db_path) as f:
        loaded_data = json.load(f)

    # Display data
    for user_id, user_data in loaded_data.items():
        print(f"User: {user_data['name']} ({user_id})")
        print(f"  Email: {user_data['email']}")
        print(f"  Created: {user_data['created_at']}")

    print("\nExample complete!")

    # Clean up
    clean = input("\nRemove example database? (y/n): ").lower() == "y"
    if clean and os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed {db_path}")


if __name__ == "__main__":
    asyncio.run(main())
