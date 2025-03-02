"""Example demonstrating the component metadata system.

This example shows how to:
1. Create a component with metadata
2. Register components with the registry
3. Discover components in a module
4. Query components by name, category, and tag
"""

from typing import Any

from pepperpy.core.base.common import BaseComponent
from pepperpy.core.common.metadata import (
    ComponentCategory,
    component,
    get_component,
    get_components_by_category,
    get_components_by_tag,
    get_metadata,
    register_component,
)


# Define a simple component with metadata
@component(
    name="example_text_processor",
    description="A simple text processor for demonstration purposes",
    category=ComponentCategory.TEXT,
    input=["text"],
    output=["text"],
    parameters={
        "uppercase": "Convert text to uppercase",
        "remove_spaces": "Remove spaces from text",
    },
    dependencies=["pepperpy>=0.1.0"],
    tags=["example", "text", "processor"],
    version="0.1.0",
    author="PepperPy Team",
    homepage="https://github.com/pepperpy/pepperpy",
    license="MIT",
    example_usage="See documentation for usage examples",
)
class ExampleTextProcessor(BaseComponent):
    """A simple text processor for demonstration purposes."""

    def __init__(
        self,
        name: str = "text_processor",
        uppercase: bool = False,
        remove_spaces: bool = False,
    ) -> None:
        """Initialize the text processor.

        Args:
            name: Component name
            uppercase: Whether to convert text to uppercase
            remove_spaces: Whether to remove spaces from text
        """
        super().__init__(name=name)
        self.uppercase = uppercase
        self.remove_spaces = remove_spaces

    def process_text(self, text: str) -> str:
        """Process the input text.

        Args:
            text: Input text to process

        Returns:
            Processed text
        """
        result = text
        if self.uppercase:
            result = result.upper()
        if self.remove_spaces:
            result = result.replace(" ", "")
        return result


# Define another component with different metadata
@component(
    name="example_image_processor",
    description="A simple image processor for demonstration purposes",
    category=ComponentCategory.IMAGE,
    input=["image"],
    output=["image"],
    tags=["example", "image", "processor"],
)
class ExampleImageProcessor(BaseComponent):
    """A simple image processor for demonstration purposes."""

    def __init__(self, name: str = "image_processor") -> None:
        """Initialize the image processor.

        Args:
            name: Component name
        """
        super().__init__(name=name)

    def process_image(self, image: Any) -> Any:
        """Process the input image.

        Args:
            image: Input image to process

        Returns:
            Processed image
        """
        # Placeholder for image processing
        return image


def main() -> None:
    """Run the metadata example."""
    # Register components manually
    register_component(ExampleTextProcessor)
    register_component(ExampleImageProcessor)

    # Or discover components in a module
    # discover_components(__name__)

    # Get component by name
    text_processor_class = get_component("example_text_processor")
    if text_processor_class:
        print(f"Found component: {text_processor_class.__name__}")

        # Get metadata for the component
        metadata = get_metadata(text_processor_class)
        if metadata:
            print(f"Component description: {metadata.description}")
            print(f"Component category: {metadata.category.value}")
            print(f"Component tags: {metadata.tags}")

            # Convert metadata to dictionary
            metadata_dict = metadata.to_dict()
            print(f"Metadata as dict: {metadata_dict}")

            # Create an instance directly instead of using the class from registry
            # This avoids type checking issues
            processor = ExampleTextProcessor(name="my_text_processor", uppercase=True)
            result = processor.process_text("Hello, world!")
            print(f"Processing result: {result}")

            # Get metadata from instance using the method added by the decorator
            instance_metadata = getattr(
                processor, "get_component_metadata", lambda: None
            )()
            if instance_metadata:
                print(f"Instance metadata name: {instance_metadata.name}")

    # Get components by category
    image_components = get_components_by_category(ComponentCategory.IMAGE)
    print(f"Found {len(image_components)} image components")

    # Get components by tag
    example_components = get_components_by_tag("example")
    print(f"Found {len(example_components)} components with 'example' tag")

    # Print names of all example components
    for comp in example_components:
        metadata = get_metadata(comp)
        if metadata:
            print(f"- {metadata.name} ({metadata.category.value})")


if __name__ == "__main__":
    main()
