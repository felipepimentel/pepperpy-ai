#!/usr/bin/env python
"""Example demonstrating the use of RAG document utility functions.

This example shows how to use the document utility functions from the PepperPy framework
to process and prepare text for RAG (Retrieval Augmented Generation) systems.
"""

from pepperpy.rag.document.utils import (
    clean_markdown_formatting,
    clean_text,
    remove_html_tags,
)


def example_clean_text() -> None:
    """Demonstrate text cleaning functionality."""
    print("\n=== Text Cleaning Example ===")

    # Example with extra whitespace
    text_with_whitespace = "  This   text  has   extra   whitespace.  "
    cleaned = clean_text(text_with_whitespace)
    print("Original text with whitespace:")
    print(f"'{text_with_whitespace}'")
    print("Cleaned text:")
    print(f"'{cleaned}'")

    # Example with unicode characters
    unicode_text = "Café Français with accents: éèêë"
    cleaned_unicode = clean_text(unicode_text, normalize_unicode=True)
    print("\nOriginal unicode text:")
    print(f"'{unicode_text}'")
    print("Cleaned unicode text:")
    print(f"'{cleaned_unicode}'")

    # Example with case conversion
    mixed_case = "This Text Has Mixed CASE"
    lowercase = clean_text(mixed_case, lowercase=True)
    print("\nOriginal mixed case text:")
    print(f"'{mixed_case}'")
    print("Lowercase text:")
    print(f"'{lowercase}'")

    # Combined example
    combined = "  Café   FRANÇAIS  with  EXTRA  whitespace  "
    cleaned_combined = clean_text(
        combined,
        remove_extra_whitespace=True,
        normalize_unicode=True,
        lowercase=True,
    )
    print("\nOriginal combined example:")
    print(f"'{combined}'")
    print("Fully cleaned text:")
    print(f"'{cleaned_combined}'")


def example_html_removal() -> None:
    """Demonstrate HTML tag removal."""
    print("\n=== HTML Tag Removal Example ===")

    # Simple HTML example
    simple_html = "<p>This is a <b>paragraph</b> with <i>formatting</i>.</p>"
    cleaned = remove_html_tags(simple_html)
    print("Original HTML:")
    print(simple_html)
    print("Cleaned text:")
    print(cleaned)

    # More complex HTML
    complex_html = """
    <div class="content">
        <h1>Article Title</h1>
        <p>This is the first paragraph with <a href="https://example.com">a link</a>.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        <p>Another paragraph with <span style="color:red">colored text</span>.</p>
    </div>
    """
    cleaned_complex = remove_html_tags(complex_html)
    print("\nOriginal complex HTML:")
    print(complex_html)
    print("Cleaned text:")
    print(cleaned_complex)


def example_markdown_cleaning() -> None:
    """Demonstrate Markdown formatting removal."""
    print("\n=== Markdown Cleaning Example ===")

    # Simple Markdown example
    simple_md = """# Heading

This is a paragraph with **bold** and *italic* text.

## Subheading

- List item 1
- List item 2

[Link text](https://example.com)
"""
    cleaned = clean_markdown_formatting(simple_md)
    print("Original Markdown:")
    print(simple_md)
    print("Cleaned text:")
    print(cleaned)

    # Code blocks example
    code_md = """## Code Example

Here's a code example:

```python
def hello_world():
    print("Hello, world!")
```

And an inline code: `print("Hello")`.
"""
    cleaned_code = clean_markdown_formatting(code_md)
    print("\nOriginal Markdown with code:")
    print(code_md)
    print("Cleaned text:")
    print(cleaned_code)


def main() -> None:
    """Run all examples."""
    print("RAG Document Utilities Examples")
    print("==============================")

    example_clean_text()
    example_html_removal()
    example_markdown_cleaning()


if __name__ == "__main__":
    main()
