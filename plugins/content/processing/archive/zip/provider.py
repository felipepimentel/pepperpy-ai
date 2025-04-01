"""ZIP archive processing provider."""

import zipfile
from pathlib import Path
from typing import Any

from pepperpy.content.base import ContentProcessor, ProcessingResult
from pepperpy.core.errors import ProviderError
from pepperpy.plugins.plugin import ProviderPlugin


class ZipProvider(ContentProcessor, ProviderPlugin):
    """ZIP archive processing provider."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize provider."""
        super().__init__(**kwargs)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize provider."""
        if self._initialized:
            return

        self._initialized = True

    async def process(self, content: Path | str, **kwargs: Any) -> ProcessingResult:
        """Process ZIP archive.

        Args:
            content: Path to ZIP archive
            **kwargs: Additional arguments
                - password: Optional password for encrypted archives
                - output_dir: Directory to extract files to
                - include_extensions: List of file extensions to include
                - recursive: Whether to process nested archives

        Returns:
            Processing result with archive info and metadata

        Raises:
            ProviderError: If processing fails
        """
        try:
            # Convert content to Path
            if isinstance(content, str):
                content = Path(content)

            # Check if file exists
            if not content.exists():
                raise ProviderError(f"File not found: {content}")

            # Get optional parameters
            password = kwargs.get("password")
            if password and isinstance(password, str):
                password = password.encode()

            output_dir = kwargs.get("output_dir")
            if output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)

            include_extensions = kwargs.get("include_extensions", [])

            # Open archive
            with zipfile.ZipFile(content) as archive:
                # List files
                file_list = archive.namelist()

                # Filter by extension if specified
                if include_extensions:
                    file_list = [
                        f
                        for f in file_list
                        if any(
                            f.lower().endswith(ext.lower())
                            for ext in include_extensions
                        )
                    ]

                # Extract if output_dir specified
                if output_dir:
                    for file in file_list:
                        try:
                            archive.extract(file, output_dir, pwd=password)
                        except Exception as e:
                            print(f"Warning: Failed to extract {file}: {e}")

                # Get archive info
                info_list = [archive.getinfo(file) for file in file_list]
                total_size = sum(info.file_size for info in info_list)
                compressed_size = sum(info.compress_size for info in info_list)

                # Prepare metadata
                metadata = {
                    "filename": content.name,
                    "total_size": total_size,
                    "compressed_size": compressed_size,
                    "compression_ratio": (total_size - compressed_size) / total_size
                    if total_size > 0
                    else 0,
                    "file_count": len(file_list),
                    "files": file_list,
                }

                # Prepare text summary
                text = f"Archive: {content.name}\n"
                text += f"Total files: {len(file_list)}\n"
                text += f"Total size: {total_size:,} bytes\n"
                text += f"Compressed size: {compressed_size:,} bytes\n"
                text += f"Compression ratio: {metadata['compression_ratio']:.2%}\n"
                if output_dir:
                    text += f"Extracted to: {output_dir}\n"
                text += "\nFiles:\n" + "\n".join(f"- {f}" for f in file_list)

                return ProcessingResult(text=text, metadata=metadata)

        except Exception as e:
            raise ProviderError(f"Failed to process archive: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False
