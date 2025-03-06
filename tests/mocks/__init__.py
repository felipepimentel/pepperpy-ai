"""Pacote de mocks para testes.

Este pacote fornece implementações de mock para componentes do framework,
permitindo testes sem dependências externas.
"""

from tests.mocks.pipeline_mocks import (
    MockAPIOutput,
    MockAPISource,
    MockClassificationProcessor,
    MockFileOutput,
    MockFileSource,
    MockPodcastGenerator,
    MockRSSSource,
    MockSummarizationProcessor,
    MockTranslationProcessor,
)

__all__ = [
    "MockAPIOutput",
    "MockAPISource",
    "MockClassificationProcessor",
    "MockFileOutput",
    "MockFileSource",
    "MockPodcastGenerator",
    "MockRSSSource",
    "MockSummarizationProcessor",
    "MockTranslationProcessor",
]
