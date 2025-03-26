"""Example demonstrating document processing with PepperPy."""

import asyncio

from pepperpy import PepperPy


async def process_document(content: bytes, content_type: str) -> None:
    """Process a document using PepperPy's workflow system.

    Args:
        content: Document content in bytes
        content_type: MIME type of the document
    """
    async with PepperPy().with_workflow() as assistant:
        # Create and execute workflow
        workflow = (
            assistant.workflow("document_processing")
            .add_stage("extract", "text_extraction")
            .add_stage("classify", "document_classification")
            .add_stage("metadata", "metadata_extraction")
            .connect("extract", "classify")
            .connect("classify", "metadata")
        )

        # Execute workflow
        result = await workflow.execute({
            "content": content,
            "content_type": content_type,
        })

        # Print results
        print("\nWorkflow Results:")
        print(f"Status: {result.status}")
        print(f"Extracted Text: {len(result.get('extract'))} characters")
        print(f"Classification: {result.get('classify')}")
        print(f"Metadata: {result.get('metadata')}")


async def main() -> None:
    """Run document processing examples."""
    # Example with a PDF document
    pdf_content = b"%PDF-1.4\n..."  # Sample PDF content
    await process_document(pdf_content, "application/pdf")

    # Example with an image
    image_content = b"\x89PNG\r\n..."  # Sample PNG content
    await process_document(image_content, "image/png")


if __name__ == "__main__":
    asyncio.run(main())
