#!/usr/bin/env python
"""Example demonstrating the use of HTTP utility functions.

This example shows how to use the HTTP utility functions from the PepperPy framework
to handle common HTTP operations like parsing JSON, checking status codes, and
working with headers.
"""

from pepperpy.http.errors import ResponseError
from pepperpy.http.utils import (
    check_status_code,
    format_headers,
    get_content_type,
    is_json_content,
    parse_json,
    parse_query_params,
)


def example_parse_json() -> None:
    """Demonstrate JSON parsing with error handling."""
    print("\n=== JSON Parsing Example ===")

    # Valid JSON
    valid_json = '{"name": "John", "age": 30, "city": "New York"}'
    try:
        result = parse_json(valid_json)
        print(f"Parsed JSON: {result}")
        print(f"Name: {result['name']}, Age: {result['age']}")
    except ResponseError as e:
        print(f"Error parsing JSON: {e}")

    # Invalid JSON
    invalid_json = '{"name": "John", "age": 30, city: "New York"}'
    try:
        result = parse_json(invalid_json)
        print(f"Parsed JSON: {result}")
    except ResponseError as e:
        print(f"Error parsing JSON: {e}")

    # JSON as bytes
    json_bytes = b'{"name": "Jane", "age": 25}'
    try:
        result = parse_json(json_bytes)
        print(f"Parsed JSON from bytes: {result}")
    except ResponseError as e:
        print(f"Error parsing JSON: {e}")


def example_status_code() -> None:
    """Demonstrate status code checking."""
    print("\n=== Status Code Example ===")

    # Success status codes
    for code in [200, 201, 204]:
        try:
            check_status_code(code)
            print(f"Status code {code} is OK")
        except ResponseError as e:
            print(f"Error with status code {code}: {e}")

    # Client error status codes
    for code in [400, 401, 404]:
        try:
            check_status_code(code)
            print(f"Status code {code} is OK")
        except ResponseError as e:
            print(f"Error with status code {code}: {e}")

    # Server error status codes
    for code in [500, 502, 503]:
        try:
            check_status_code(code)
            print(f"Status code {code} is OK")
        except ResponseError as e:
            print(f"Error with status code {code}: {e}")


def example_content_type() -> None:
    """Demonstrate content type handling."""
    print("\n=== Content Type Example ===")

    # Different header formats
    headers_examples = [
        {"Content-Type": "application/json"},
        {"content-type": "application/json; charset=utf-8"},
        {"CONTENT-TYPE": "text/html"},
        {"Content-Type": "application/xml"},
        {"X-Custom-Header": "value"},  # No content type
    ]

    for i, headers in enumerate(headers_examples):
        content_type = get_content_type(headers)
        is_json = is_json_content(headers)

        print(f"Example {i + 1}:")
        print(f"  Headers: {headers}")
        print(f"  Content Type: '{content_type}'")
        print(f"  Is JSON: {is_json}")


def example_format_headers() -> None:
    """Demonstrate header formatting."""
    print("\n=== Header Formatting Example ===")

    # Mixed case headers
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": "abc123",
        "Authorization": "Bearer token",
        "ACCEPT": "application/json",
    }

    formatted = format_headers(headers)

    print("Original headers:")
    for key, value in headers.items():
        print(f"  {key}: {value}")

    print("\nFormatted headers:")
    for key, value in formatted.items():
        print(f"  {key}: {value}")


def example_query_params() -> None:
    """Demonstrate query parameter parsing."""
    print("\n=== Query Parameter Example ===")

    # Different query strings
    query_examples = [
        "name=John&age=30&city=New%20York",
        "product=laptop&price=999.99&in_stock=true",
        "q=python%20programming&page=1&limit=10",
        "",  # Empty query string
    ]

    for i, query in enumerate(query_examples):
        params = parse_query_params(query)

        print(f"Example {i + 1}:")
        print(f"  Query: '{query}'")
        print(f"  Parsed Parameters: {params}")


def main() -> None:
    """Run all examples."""
    print("HTTP Utilities Examples")
    print("======================")

    example_parse_json()
    example_status_code()
    example_content_type()
    example_format_headers()
    example_query_params()


if __name__ == "__main__":
    main()
