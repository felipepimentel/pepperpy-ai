"""Example demonstrating the Document Processing Workflow plugin.

This example shows how to use the Document Processing Workflow plugin
to extract text and metadata from documents.
"""

import asyncio
import os
from pathlib import Path

# Import plugin_manager
from pepperpy.plugin_manager import plugin_manager

# Setup paths
EXAMPLES_DIR = Path(__file__).parent
DATA_DIR = EXAMPLES_DIR / "data"
OUTPUT_DIR = EXAMPLES_DIR / "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main() -> None:
    """Run the example."""
    print("Document Processing Workflow Example")
    print("=" * 50)

    # Create the document processor using plugin_manager
    # O linter vai alertar sobre o método execute(), mas isso é esperado
    # já que ele não consegue inferir o tipo exato retornado pelo plugin_manager
    workflow = plugin_manager.create_provider(
        "workflow",
        "document_processor",
        extract_metadata=True,
        extract_images=False,
        extract_tables=False,
    )

    # Inicializar o workflow
    await workflow.initialize()

    # Find sample PDF files
    pdf_files = list(DATA_DIR.glob("**/*.pdf"))
    if not pdf_files:
        print(
            "No PDF files found in the data directory. Creating a sample text file instead."
        )
        # Create a sample text file
        sample_file = OUTPUT_DIR / "sample.txt"
        with open(sample_file, "w") as f:
            f.write(
                "This is a sample document for testing the document processor workflow."
            )

        # Process the sample file usando método execute()
        # (ignorar warning do linter)
        input_data = {"document_path": str(sample_file), "options": {}}
        result = await workflow.execute(input_data)  # type: ignore

        print(f"\nProcessed: {sample_file}")
        print(f"Text content: {result['text']}")
    else:
        # Process a single document
        pdf_file = pdf_files[0]
        print(f"\nProcessing document: {pdf_file}")

        # (ignorar warning do linter)
        input_data = {"document_path": str(pdf_file), "options": {}}
        result = await workflow.execute(input_data)  # type: ignore

        print(f"Extracted text (first 100 chars): {result['text'][:100]}...")
        print(f"Metadata: {result['metadata']}")

        # Process a batch of documents if available
        if len(pdf_files) > 1:
            print(f"\nProcessing batch of {min(3, len(pdf_files))} documents...")

            # Convert Path objects to strings
            doc_paths = [str(path) for path in pdf_files[:3]]

            # (ignorar warning do linter)
            input_data = {"document_paths": doc_paths, "options": {}}
            batch_results = await workflow.execute(input_data)  # type: ignore

            for path, doc_result in batch_results["results"].items():
                if "error" in doc_result:
                    print(f"Error processing {path}: {doc_result['error']}")
                else:
                    text_preview = (
                        doc_result["text"][:50] + "..."
                        if doc_result["text"]
                        else "No text"
                    )
                    print(f"- {Path(path).name}: {text_preview}")

        # Process a directory
        print(f"\nProcessing all documents in {DATA_DIR}")

        # (ignorar warning do linter)
        input_data = {"directory_path": str(DATA_DIR), "options": {}}
        dir_results = await workflow.execute(input_data)  # type: ignore

        print(f"Processed {dir_results['num_files']} files in directory")
        print(f"Found {len(dir_results['results'])} documents")

    # Clean up
    await workflow.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
