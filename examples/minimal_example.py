#!/usr/bin/env python
"""
Minimal example demonstrating the intent analysis functionality in PepperPy.
"""
import re
import time
from typing import Any, Dict, Tuple


# Intent analysis functionality
def analyze_intent(query: str) -> Tuple[str, Dict[str, Any], float]:
    """Analyze a user query to determine the intent and extract parameters.

    Args:
        query: The user query to analyze

    Returns:
        A tuple containing (intent_type, parameters, confidence)
    """
    # Normalize query
    normalized_query = query.strip().lower()

    # Default values
    intent_type = "query"
    params = {}
    confidence = 0.5

    # Check for create intent patterns
    create_patterns = [
        r"(?:create|generate|write|make)(?:\s+a)?(?:\s+an)?(?:\s+some)?\s+(.*)",
        r"(?:produce|draft|compose|prepare)(?:\s+a)?(?:\s+an)?(?:\s+some)?\s+(.*)",
    ]

    for pattern in create_patterns:
        match = re.search(pattern, normalized_query)
        if match:
            what_to_create = match.group(1).strip()
            intent_type = "create"
            params = {"content_type": what_to_create}
            confidence = 0.7
            break

    # Check for process intent patterns
    process_patterns = [
        r"(?:process|transform|convert|summarize|analyze)\s+(.*)",
        r"(?:extract|parse|get|find)\s+(.*?)\s+(?:from|in)\s+(.*)",
    ]

    for pattern in process_patterns:
        match = re.search(pattern, normalized_query)
        if match:
            intent_type = "process"
            if len(match.groups()) == 1:
                params = {"content": match.group(1).strip()}
            else:
                params = {
                    "target": match.group(1).strip(),
                    "content": match.group(2).strip(),
                }
            confidence = 0.65
            break

    # Check for analyze intent patterns
    analyze_patterns = [
        r"(?:analyze|examine|study|investigate)\s+(.*)",
        r"(?:what|tell me about|describe)\s+(.*)",
    ]

    for pattern in analyze_patterns:
        match = re.search(pattern, normalized_query)
        if match:
            content = match.group(1).strip()
            # Only switch to analyze if we haven't matched a more specific intent
            if intent_type == "query":
                intent_type = "analyze"
                params = {"data": content}
                confidence = 0.6

    return intent_type, params, confidence


def demonstrate_intent_analysis() -> None:
    """Demonstrate the intent analysis feature."""
    print("\n=== Intent Analysis Demonstration ===")

    # Example queries to analyze
    queries = [
        "Tell me about artificial intelligence",
        "Create a blog post about climate change",
        "Summarize this article about quantum computing",
        "Process this PDF and extract the main points",
        "What's the weather like today?",
        "Analyze this dataset for trends",
    ]

    for query in queries:
        # Analyze the intent
        intent_type, parameters, confidence = analyze_intent(query)

        print(f"\nQuery: {query}")
        print(f"Intent: {intent_type}")
        print(f"Parameters: {parameters}")
        print(f"Confidence: {confidence:.2f}")
        print("-" * 50)


def simulate_caching() -> None:
    """Simulate the caching functionality."""
    print("\n=== Caching Simulation ===")

    # Function that simulates processing with and without caching
    def process_with_cache(key: str, use_cache: bool = False) -> str:
        cache = {}

        if use_cache and key in cache:
            print(f"Retrieved result from cache for '{key}'")
            return cache[key]

        print(f"Processing '{key}' (not from cache)")
        # Simulate processing time
        time.sleep(0.5)
        result = f"Processed {key}"

        # Store in cache
        cache[key] = result
        return result

    # Simulate first-time requests
    print("\nFirst requests (no cache):")
    start = time.time()
    process_with_cache("query1")
    process_with_cache("query2")
    end = time.time()
    print(f"Total execution time: {end - start:.2f}s")

    # Simulate cached requests
    print("\nCached implementation would reduce processing time for repeated requests")
    print("The @cached decorator in the full framework provides this functionality")


def main() -> None:
    """Main function to run the example."""
    print("=== PepperPy Minimal Example ===")
    print("Demonstrating Intent Analysis and Caching Simulation")

    # Demonstrate intent analysis
    demonstrate_intent_analysis()

    # Simulate caching
    simulate_caching()

    print("\nTo use the full implementation with real LLM providers:")
    print("1. Install the pepperpy package")
    print("2. Set up your API keys in environment variables")
    print("3. Use the @cached decorator for automatic result caching")
    print("4. Use the analyze_intent function for intelligent query routing")


if __name__ == "__main__":
    main()
