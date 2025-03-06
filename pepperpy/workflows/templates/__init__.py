"""Módulo de templates para workflows.

Este módulo fornece templates pré-configurados para workflows comuns,
permitindo a reutilização de configurações e padrões.

Example:
    ```python
    from pepperpy.workflows.templates import (
        PodcastTemplate,
        SummaryTemplate,
        TranslationTemplate,
    )

    # Usar template para criar um podcast
    podcast_template = PodcastTemplate(
        voice="pt",
        max_length=150,
    )
    podcast_path = await podcast_template.create_podcast(
        source_url="https://news.google.com/rss",
        output_path="podcast.mp3",
    )

    # Usar template para resumir um documento
    summary_template = SummaryTemplate(max_length=200)
    summary = await summary_template.summarize(
        document_path="document.txt",
    )

    # Usar template para traduzir conteúdo
    translation_template = TranslationTemplate(target_language="pt")
    translated = await translation_template.translate(
        content="Hello, world!",
    )
    ```
"""

from pepperpy.workflows.templates.applications import (
    PodcastTemplate,
    SummaryTemplate,
    TranslationTemplate,
)

__all__ = ["PodcastTemplate", "SummaryTemplate", "TranslationTemplate"]
