#!/usr/bin/env python
"""Example demonstrating the schema migration and versioning system.

This example shows how to create and use schema versions, define migrations
between versions, and migrate data between schema versions.
"""

import json
from typing import Any, Dict

from pepperpy.data.schema_migration import (
    migrate_data,
    register_field_migration,
    register_function_migration,
    register_schema_version,
    validate_data,
)


def main() -> None:
    """Run the example."""
    print("Schema Migration and Versioning Example")
    print("=======================================\n")

    # Define schema versions
    print("Defining schema versions...")

    # User schema v1.0
    user_schema_v1 = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "User",
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "age": {"type": "integer", "minimum": 0},
        },
        "required": ["id", "name", "email"],
    }

    # User schema v1.1 (adds address field)
    user_schema_v1_1 = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "User",
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "age": {"type": "integer", "minimum": 0},
            "address": {"type": "string"},
        },
        "required": ["id", "name", "email"],
    }

    # User schema v2.0 (splits name into first_name and last_name)
    user_schema_v2 = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "User",
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "age": {"type": "integer", "minimum": 0},
            "address": {"type": "string"},
        },
        "required": ["id", "first_name", "last_name", "email"],
    }

    # Register schema versions
    register_schema_version(
        schema_name="user",
        version="1.0",
        schema_definition=user_schema_v1,
        description="Initial user schema",
    )

    register_schema_version(
        schema_name="user",
        version="1.1",
        schema_definition=user_schema_v1_1,
        description="User schema with address field",
    )

    register_schema_version(
        schema_name="user",
        version="2.0",
        schema_definition=user_schema_v2,
        description="User schema with split name fields",
    )

    print("  Registered schema versions: user v1.0, v1.1, v2.0")

    # Define migrations
    print("\nDefining migrations...")

    # Migration from v1.0 to v1.1 (simple field addition)
    def forward_v1_to_v1_1(data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate user data from v1.0 to v1.1."""
        result = data.copy()
        if "address" not in result:
            result["address"] = ""
        return result

    def backward_v1_1_to_v1(data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate user data from v1.1 to v1.0."""
        result = data.copy()
        if "address" in result:
            del result["address"]
        return result

    register_function_migration(
        schema_name="user",
        source_version="1.0",
        target_version="1.1",
        forward_func=forward_v1_to_v1_1,
        backward_func=backward_v1_1_to_v1,
        description="Add address field",
    )

    print("  Registered function migration: user v1.0 -> v1.1")

    # Migration from v1.1 to v2.0 (split name field)
    name_mappings = {
        "name": {
            "field": "first_name",
            "transform": lambda name: name.split()[0] if name and " " in name else name,
            "reverse_transform": lambda first_name: f"{first_name} ",
        }
    }

    register_field_migration(
        schema_name="user",
        source_version="1.1",
        target_version="2.0",
        field_mappings=name_mappings,  # type: ignore
        description="Split name into first_name and last_name",
    )

    # We need to add last_name separately since it's not a direct mapping
    def add_last_name_v1_1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
        """Add last_name field from name."""
        result = data.copy()
        if "name" in result and " " in result["name"]:
            result["last_name"] = " ".join(result["name"].split()[1:])
        else:
            result["last_name"] = ""
        return result

    def combine_name_v2_to_v1_1(data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine first_name and last_name into name."""
        result = data.copy()
        if "first_name" in result and "last_name" in result:
            result["name"] = f"{result['first_name']} {result['last_name']}".strip()
            del result["first_name"]
            del result["last_name"]
        elif "first_name" in result:
            result["name"] = result["first_name"]
            del result["first_name"]
            if "last_name" in result:
                del result["last_name"]
        return result

    register_function_migration(
        schema_name="user",
        source_version="1.1",
        target_version="2.0",
        forward_func=add_last_name_v1_1_to_v2,
        backward_func=combine_name_v2_to_v1_1,
        description="Add last_name field",
    )

    print("  Registered field migration: user v1.1 -> v2.0")
    print("  Registered function migration: user v1.1 -> v2.0 (for last_name)")

    # Create sample data
    print("\nCreating sample data...")

    user_v1 = {
        "id": "user123",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 30,
    }

    print(f"  User v1.0: {json.dumps(user_v1, indent=2)}")

    # Validate against v1.0 schema
    print("\nValidating against v1.0 schema...")
    validated_v1 = validate_data("user", user_v1, "1.0")
    print(f"  Validation successful: {json.dumps(validated_v1, indent=2)}")

    # Migrate from v1.0 to v1.1
    print("\nMigrating from v1.0 to v1.1...")
    user_v1_1 = migrate_data("user", user_v1, "1.0", "1.1")
    print(f"  User v1.1: {json.dumps(user_v1_1, indent=2)}")

    # Validate against v1.1 schema
    print("\nValidating against v1.1 schema...")
    validated_v1_1 = validate_data("user", user_v1_1, "1.1")
    print(f"  Validation successful: {json.dumps(validated_v1_1, indent=2)}")

    # Migrate from v1.1 to v2.0
    print("\nMigrating from v1.1 to v2.0...")
    user_v2 = migrate_data("user", user_v1_1, "1.1", "2.0")
    print(f"  User v2.0: {json.dumps(user_v2, indent=2)}")

    # Validate against v2.0 schema
    print("\nValidating against v2.0 schema...")
    validated_v2 = validate_data("user", user_v2, "2.0")
    print(f"  Validation successful: {json.dumps(validated_v2, indent=2)}")

    # Migrate directly from v1.0 to v2.0
    print("\nMigrating directly from v1.0 to v2.0...")
    user_v2_direct = migrate_data("user", user_v1, "1.0", "2.0")
    print(f"  User v2.0 (direct migration): {json.dumps(user_v2_direct, indent=2)}")

    # Migrate backward from v2.0 to v1.0
    print("\nMigrating backward from v2.0 to v1.0...")
    user_v1_backward = migrate_data("user", user_v2, "2.0", "1.0")
    print(f"  User v1.0 (backward migration): {json.dumps(user_v1_backward, indent=2)}")

    # Try with invalid data
    print("\nTrying with invalid data...")
    invalid_user = {
        "id": "user456",
        "name": "Jane Smith",
        # Missing required email field
        "age": -5,  # Invalid age (negative)
    }

    print(f"  Invalid user: {json.dumps(invalid_user, indent=2)}")

    try:
        validate_data("user", invalid_user, "1.0")
        print("  Validation successful (unexpected!)")
    except Exception as e:
        print(f"  Validation failed as expected: {e}")


if __name__ == "__main__":
    main()
