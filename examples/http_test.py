#!/usr/bin/env python
"""
HTTP Core Test Example for PepperPy.

This simple example demonstrates the usage of HTTP utilities 
from pepperpy.core.http after the migration from pepperpy.http.
"""

from pepperpy.core.http import (
    ResponseError,
    check_status_code,
    format_headers,
    get_content_type,
    is_json_content,
    parse_json,
    parse_query_params,
)


def main():
    """Run a simple demonstration of the HTTP utilities."""
    print("=== PepperPy HTTP Utilities Example ===")

    # 1. Parse JSON
    print("\n1. Parsing JSON:")
    json_str = '{"name": "pepperpy", "version": "0.1.0"}'
    data = parse_json(json_str)
    print(f"Parsed data: {data}")

    # 2. Format headers
    print("\n2. Formatting headers:")
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "test-key",
        "Accept": "application/json",
    }
    formatted_headers = format_headers(headers)
    print(f"Original headers: {headers}")
    print(f"Formatted headers: {formatted_headers}")

    # 3. Check content type
    print("\n3. Content type detection:")
    content_type = get_content_type({"content-type": "application/json; charset=utf-8"})
    print(f"Content type: {content_type}")

    # 4. Check if content is JSON
    print("\n4. JSON content detection:")
    json_headers = {"content-type": "application/json"}
    non_json_headers = {"content-type": "text/plain"}

    print(f"Is application/json a JSON content? {is_json_content(json_headers)}")
    print(f"Is text/plain a JSON content? {is_json_content(non_json_headers)}")

    # 5. Parse query params
    print("\n5. Parsing query parameters:")
    query_string = "name=pepperpy&version=0.1.0"
    params = parse_query_params(query_string)
    print(f"Parsed query parameters: {params}")

    # 6. Status code checking
    print("\n6. Status code checking:")
    try:
        # Should not raise an error
        check_status_code(200)
        print("Status code 200 is OK")

        # Use expected_codes parameter
        check_status_code(201, expected_codes=(200, 201, 204))
        print("Status code 201 is OK when expected_codes includes it")

        # Should raise an error
        check_status_code(404)
    except ResponseError as e:
        print(f"Caught expected error: {e}")

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
