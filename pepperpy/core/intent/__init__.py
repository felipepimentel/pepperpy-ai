"""Módulo de abstração de intenções.

Este módulo fornece a API para abstração de intenções, permitindo
definir operações de alto nível que são traduzidas para pipelines
de composição.

Example:
    ```python
    from pepperpy.core.intent import create_podcast, summarize_document, translate_content

    # Criar um podcast a partir de um feed RSS
    podcast_path = await create_podcast(
        source_url="https://news.google.com/rss",
        output_path="podcast.mp3",
        voice="pt",
        max_length=150,
    )

    # Resumir um documento
    summary = await summarize_document(
        document_path="document.txt",
        max_length=200,
    )

    # Traduzir conteúdo
    translated = await translate_content(
        content="Hello, world!",
        target_language="pt",
    )
    ```
"""

from pepperpy.core.intent.creators import (
    create_podcast,
    summarize_document,
    translate_content,
)

__all__ = ["create_podcast", "summarize_document", "translate_content"]
