#!/usr/bin/env python
"""Example demonstrating the data consistency and integrity validation system.

This example shows how to create and use integrity checks, validators, and
validation hooks to ensure data consistency and integrity.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Union

from pepperpy.data.integrity import (
    create_completeness_check,
    create_format_check,
    create_range_check,
    create_referential_integrity_check,
    create_temporal_check,
    create_uniqueness_check,
    register_integrity_validator,
)
from pepperpy.data.validation import (
    ValidationLevel,
    ValidationStage,
    create_validation_hook,
    validate_with,
)

# Mock database for referential integrity checks
USERS_DB = {
    "user1": {"id": "user1", "name": "John Doe", "email": "john@example.com"},
    "user2": {"id": "user2", "name": "Jane Smith", "email": "jane@example.com"},
}

PRODUCTS_DB = {
    "prod1": {"id": "prod1", "name": "Product 1", "price": 10.99},
    "prod2": {"id": "prod2", "name": "Product 2", "price": 20.99},
}


# Mock uniqueness resolver
def check_unique_email(data: Dict[str, Any], fields: Union[str, List[str]]) -> bool:
    """Check if an email is unique.

    Args:
        data: The data to check
        fields: The field or fields to check

    Returns:
        True if the email is unique, False otherwise
    """
    if isinstance(fields, str):
        fields = [fields]

    # For this example, we'll just check if the email is not in the database
    for field in fields:
        if field == "email" and data.get(field):
            for user in USERS_DB.values():
                if user["email"] == data["email"] and user["id"] != data.get("id", ""):
                    return False

    return True


# Mock reference resolver
def check_reference_exists(reference_value: Any, target_entity: str) -> bool:
    """Check if a reference exists.

    Args:
        reference_value: The reference value to check
        target_entity: The name of the target entity

    Returns:
        True if the reference exists, False otherwise
    """
    if target_entity == "users":
        return reference_value in USERS_DB
    elif target_entity == "products":
        return reference_value in PRODUCTS_DB

    return False


# Email format validator
def is_valid_email(value: Any) -> bool:
    """Check if a value is a valid email address.

    Args:
        value: The value to check

    Returns:
        True if the value is a valid email address, False otherwise
    """
    if not isinstance(value, str):
        return False

    # Simple email validation regex
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, value))


def main() -> None:
    """Run the example."""
    print("Data Consistency and Integrity Validation Example")
    print("================================================\n")

    # Create integrity checks
    print("Creating integrity checks...")

    # Completeness check
    create_completeness_check(
        name="order_required_fields",
        required_fields=["id", "user_id", "product_ids", "total_amount", "created_at"],
        allow_empty=False,
    )
    print("  Created completeness check: order_required_fields")

    # Referential integrity checks
    create_referential_integrity_check(
        name="order_user_reference",
        source_field="user_id",
        target_entity="users",
        target_field="id",
        resolver=check_reference_exists,
    )
    print("  Created referential integrity check: order_user_reference")

    # Range check
    create_range_check(
        name="order_amount_range",
        field="total_amount",
        min_value=0.01,
        max_value=10000.00,
        inclusive_min=True,
        inclusive_max=True,
    )
    print("  Created range check: order_amount_range")

    # Format check
    create_format_check(
        name="user_email_format",
        field="email",
        format_validator=is_valid_email,
        error_message="Invalid email format",
    )
    print("  Created format check: user_email_format")

    # Temporal check
    create_temporal_check(
        name="order_date_sequence",
        start_field="created_at",
        end_field="updated_at",
        allow_equal=True,
    )
    print("  Created temporal check: order_date_sequence")

    # Uniqueness check
    create_uniqueness_check(
        name="user_email_uniqueness",
        fields="email",
        resolver=check_unique_email,
    )
    print("  Created uniqueness check: user_email_uniqueness")

    # Register integrity validators
    print("\nRegistering integrity validators...")

    # Order validator
    register_integrity_validator(
        name="order_validator",
        checks=[
            "order_required_fields",
            "order_user_reference",
            "order_amount_range",
            "order_date_sequence",
        ],
    )
    print("  Registered validator: order_validator")

    # User validator
    register_integrity_validator(
        name="user_validator",
        checks=[
            "user_email_format",
            "user_email_uniqueness",
        ],
    )
    print("  Registered validator: user_validator")

    # Create validation hooks
    print("\nCreating validation hooks...")

    # Order validation hook
    order_hook = create_validation_hook(
        validator="order_validator",
        stage=ValidationStage.PRE_TRANSFORM,
        level=ValidationLevel.STRICT,
    )
    print("  Created validation hook for order_validator")

    # User validation hook
    user_hook = create_validation_hook(
        validator="user_validator",
        stage=ValidationStage.PRE_TRANSFORM,
        level=ValidationLevel.STANDARD,
    )
    print("  Created validation hook for user_validator")

    # Test with valid data
    print("\nTesting with valid data...")

    # Valid order
    valid_order = {
        "id": "order1",
        "user_id": "user1",
        "product_ids": ["prod1", "prod2"],
        "total_amount": 31.98,
        "created_at": datetime(2023, 1, 1, 10, 0, 0),
        "updated_at": datetime(2023, 1, 1, 10, 30, 0),
    }

    print(f"  Valid order: {valid_order}")

    try:
        result = validate_with("order_validator", valid_order)
        print(f"  Validation result: {result.is_valid}")
        if result.is_valid:
            print("  Order is valid!")
        else:
            print(f"  Validation errors: {result.errors}")
    except Exception as e:
        print(f"  Error: {e}")

    # Valid user
    valid_user = {
        "id": "user3",
        "name": "Bob Johnson",
        "email": "bob@example.com",
    }

    print(f"\n  Valid user: {valid_user}")

    try:
        result = validate_with("user_validator", valid_user)
        print(f"  Validation result: {result.is_valid}")
        if result.is_valid:
            print("  User is valid!")
        else:
            print(f"  Validation errors: {result.errors}")
    except Exception as e:
        print(f"  Error: {e}")

    # Test with invalid data
    print("\nTesting with invalid data...")

    # Invalid order (missing required field)
    invalid_order_1 = {
        "id": "order2",
        "user_id": "user1",
        # Missing product_ids
        "total_amount": 15.99,
        "created_at": datetime(2023, 1, 2, 10, 0, 0),
        "updated_at": datetime(2023, 1, 2, 10, 30, 0),
    }

    print(f"  Invalid order (missing field): {invalid_order_1}")

    try:
        result = validate_with("order_validator", invalid_order_1)
        print(f"  Validation result: {result.is_valid}")
        if result.is_valid:
            print("  Order is valid!")
        else:
            print(f"  Validation errors: {result.errors}")
    except Exception as e:
        print(f"  Error: {e}")

    # Invalid order (invalid reference)
    invalid_order_2 = {
        "id": "order3",
        "user_id": "user999",  # Non-existent user
        "product_ids": ["prod1"],
        "total_amount": 10.99,
        "created_at": datetime(2023, 1, 3, 10, 0, 0),
        "updated_at": datetime(2023, 1, 3, 10, 30, 0),
    }

    print(f"\n  Invalid order (invalid reference): {invalid_order_2}")

    try:
        result = validate_with("order_validator", invalid_order_2)
        print(f"  Validation result: {result.is_valid}")
        if result.is_valid:
            print("  Order is valid!")
        else:
            print(f"  Validation errors: {result.errors}")
    except Exception as e:
        print(f"  Error: {e}")

    # Invalid order (invalid amount)
    invalid_order_3 = {
        "id": "order4",
        "user_id": "user1",
        "product_ids": ["prod1"],
        "total_amount": -5.00,  # Negative amount
        "created_at": datetime(2023, 1, 4, 10, 0, 0),
        "updated_at": datetime(2023, 1, 4, 10, 30, 0),
    }

    print(f"\n  Invalid order (invalid amount): {invalid_order_3}")

    try:
        result = validate_with("order_validator", invalid_order_3)
        print(f"  Validation result: {result.is_valid}")
        if result.is_valid:
            print("  Order is valid!")
        else:
            print(f"  Validation errors: {result.errors}")
    except Exception as e:
        print(f"  Error: {e}")

    # Invalid order (invalid date sequence)
    invalid_order_4 = {
        "id": "order5",
        "user_id": "user1",
        "product_ids": ["prod1"],
        "total_amount": 10.99,
        "created_at": datetime(2023, 1, 5, 10, 30, 0),
        "updated_at": datetime(2023, 1, 5, 10, 0, 0),  # Before created_at
    }

    print(f"\n  Invalid order (invalid date sequence): {invalid_order_4}")

    try:
        result = validate_with("order_validator", invalid_order_4)
        print(f"  Validation result: {result.is_valid}")
        if result.is_valid:
            print("  Order is valid!")
        else:
            print(f"  Validation errors: {result.errors}")
    except Exception as e:
        print(f"  Error: {e}")

    # Invalid user (invalid email format)
    invalid_user_1 = {
        "id": "user4",
        "name": "Invalid User",
        "email": "not-an-email",  # Invalid email format
    }

    print(f"\n  Invalid user (invalid email format): {invalid_user_1}")

    try:
        result = validate_with("user_validator", invalid_user_1)
        print(f"  Validation result: {result.is_valid}")
        if result.is_valid:
            print("  User is valid!")
        else:
            print(f"  Validation errors: {result.errors}")
    except Exception as e:
        print(f"  Error: {e}")

    # Invalid user (non-unique email)
    invalid_user_2 = {
        "id": "user5",
        "name": "Duplicate User",
        "email": "john@example.com",  # Already used by user1
    }

    print(f"\n  Invalid user (non-unique email): {invalid_user_2}")

    try:
        result = validate_with("user_validator", invalid_user_2)
        print(f"  Validation result: {result.is_valid}")
        if result.is_valid:
            print("  User is valid!")
        else:
            print(f"  Validation errors: {result.errors}")
    except Exception as e:
        print(f"  Error: {e}")

    # Demonstrate validation hooks
    print("\nDemonstrating validation hooks...")

    # Create a mock pipeline context
    context = {
        "validation_levels": [
            ValidationLevel.BASIC,
            ValidationLevel.STANDARD,
            ValidationLevel.STRICT,
        ],
        "operation": "create",
    }

    # Validate with hooks
    print("  Validating order with hook...")
    order_result = order_hook.validate(valid_order, context)
    print(f"  Order validation result: {order_result.is_valid}")

    print("\n  Validating user with hook...")
    user_result = user_hook.validate(valid_user, context)
    print(f"  User validation result: {user_result.is_valid}")

    # Demonstrate conditional validation
    print("\nDemonstrating conditional validation...")

    # Create a condition that only validates on create operations
    def validate_on_create(data: Any, context: Dict[str, Any]) -> bool:
        return context.get("operation") == "create"

    # Create a conditional validation hook
    conditional_hook = create_validation_hook(
        validator="user_validator",
        stage=ValidationStage.PRE_TRANSFORM,
        level=ValidationLevel.STANDARD,
        condition=validate_on_create,
    )

    # Test with create operation
    create_context = {
        "operation": "create",
        "validation_levels": [ValidationLevel.STANDARD],
    }
    print("  Validating with create operation...")
    create_result = conditional_hook.validate(valid_user, create_context)
    print(f"  Validation result: {create_result.is_valid}")

    # Test with update operation
    update_context = {
        "operation": "update",
        "validation_levels": [ValidationLevel.STANDARD],
    }
    print("  Validating with update operation...")
    update_result = conditional_hook.validate(valid_user, update_context)
    print(f"  Validation result: {update_result.is_valid}")
    print("  (Validation was skipped due to condition)")


if __name__ == "__main__":
    main()
