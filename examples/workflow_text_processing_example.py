#!/usr/bin/env python3
"""Example demonstrating the Text Processing Workflow plugin.

This example shows how to use the Text Processing Workflow plugin
to process text using NLP tools.
"""

import asyncio
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TextProcessingResult:
    """Result of text processing."""

    text: str
    tokens: List[str] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    pos_tags: List[str] = field(default_factory=list)
    sentiment: float = 0.0
    language: str = "en"


class MockTextProcessingWorkflow:
    """Mock implementation of a text processing workflow."""

    def __init__(self, processor: str = "spacy"):
        self.processor = processor
        self.initialized = False
        self.nlp_models = {
            "spacy": "en_core_web_sm (mock)",
            "nltk": "nltk standard (mock)",
            "custom": "custom processor (mock)",
        }

    async def initialize(self) -> None:
        """Initialize the workflow."""
        print(f"[Text Processing] Initializing with processor: {self.processor}")

        # Simulate loading NLP model
        model_name = self.nlp_models.get(self.processor, "unknown")
        print(f"[Text Processing] Loading language model: {model_name}")

        self.initialized = True

    async def process_text(
        self, text: str, options: Optional[Dict[str, Any]] = None
    ) -> TextProcessingResult:
        """Process a single text."""
        if not self.initialized:
            await self.initialize()

        print(f"[Text Processing] Processing text with {self.processor}")

        # Mock text processing with different processors
        if self.processor == "spacy":
            return self._mock_spacy_processing(text, options)
        elif self.processor == "nltk":
            return self._mock_nltk_processing(text, options)
        else:
            return self._mock_custom_processing(text, options)

    async def process_batch(
        self, texts: List[str], options: Optional[Dict[str, Any]] = None
    ) -> List[TextProcessingResult]:
        """Process multiple texts."""
        if not self.initialized:
            await self.initialize()

        print(
            f"[Text Processing] Batch processing {len(texts)} texts with {self.processor}"
        )

        results = []
        for text in texts:
            result = await self.process_text(text, options)
            results.append(result)

        return results

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the text processing workflow with different inputs."""
        if not self.initialized:
            await self.initialize()

        options = input_data.get("options", {})
        processing_options = options.get("processing_options", {})

        # Process based on input type
        if "text" in input_data:
            result = await self.process_text(input_data["text"], processing_options)
            return {"result": result}
        elif "texts" in input_data:
            results = await self.process_batch(input_data["texts"], processing_options)
            return {"results": results}
        else:
            return {"error": "Invalid input: Must provide 'text' or 'texts'"}

    def _mock_spacy_processing(
        self, text: str, options: Optional[Dict[str, Any]] = None
    ) -> TextProcessingResult:
        """Mock spaCy processing."""
        options = options or {}

        # Create mock tokens
        tokens = text.split()

        # Generate mock entities based on text content
        entities = []
        entity_types = ["PERSON", "ORG", "PRODUCT", "GPE", "DATE"]

        if "PepperPy" in text:
            entities.append(
                {
                    "text": "PepperPy",
                    "start": text.find("PepperPy"),
                    "end": text.find("PepperPy") + len("PepperPy"),
                    "label": "PRODUCT",
                }
            )

        if "Python" in text:
            entities.append(
                {
                    "text": "Python",
                    "start": text.find("Python"),
                    "end": text.find("Python") + len("Python"),
                    "label": "LANGUAGE",
                }
            )

        if "AI" in text or "artificial intelligence" in text.lower():
            ai_term = "AI" if "AI" in text else "artificial intelligence"
            entities.append(
                {
                    "text": ai_term,
                    "start": text.find(ai_term),
                    "end": text.find(ai_term) + len(ai_term),
                    "label": "CONCEPT",
                }
            )

        # Add random entities for longer texts
        if len(tokens) > 5:
            for _ in range(min(2, len(tokens) // 5)):
                token_idx = random.randint(0, len(tokens) - 1)
                token = tokens[token_idx]
                if len(token) > 3 and not any(e["text"] == token for e in entities):
                    entities.append(
                        {
                            "text": token,
                            "start": text.find(token),
                            "end": text.find(token) + len(token),
                            "label": random.choice(entity_types),
                        }
                    )

        # Generate mock POS tags if requested
        pos_tags = []
        if options.get("include_pos", False):
            possible_tags = ["NOUN", "VERB", "ADJ", "ADV", "PREP", "DET"]
            pos_tags = [random.choice(possible_tags) for _ in tokens]

        # Calculate sentiment score based on positive/negative words
        positive_words = ["good", "great", "excellent", "efficient", "easy", "helpful"]
        negative_words = ["bad", "difficult", "complex", "hard", "problematic", "error"]

        sentiment = 0.0
        lower_text = text.lower()
        for word in positive_words:
            if word in lower_text:
                sentiment += 0.2
        for word in negative_words:
            if word in lower_text:
                sentiment -= 0.2

        # Clamp sentiment between -1.0 and 1.0
        sentiment = max(-1.0, min(1.0, sentiment))

        return TextProcessingResult(
            text=text,
            tokens=tokens,
            entities=entities,
            pos_tags=pos_tags,
            sentiment=sentiment,
        )

    def _mock_nltk_processing(
        self, text: str, options: Optional[Dict[str, Any]] = None
    ) -> TextProcessingResult:
        """Mock NLTK processing."""
        # NLTK processing is similar but with different entity recognition patterns
        base_result = self._mock_spacy_processing(text, options)

        # Adjust entities slightly to simulate different NER algorithms
        for entity in base_result.entities:
            # Random chance to change entity label
            if random.random() < 0.3:
                entity["label"] = random.choice(
                    ["NNP", "NP", "NN", "ORGANIZATION", "LOCATION"]
                )

        return base_result

    def _mock_custom_processing(
        self, text: str, options: Optional[Dict[str, Any]] = None
    ) -> TextProcessingResult:
        """Mock custom processing."""
        # Custom processing with minimal functionality
        tokens = text.split()

        return TextProcessingResult(
            text=text,
            tokens=tokens,
            entities=[],  # No entity recognition
            sentiment=0.0,  # Neutral sentiment
        )

    async def cleanup(self) -> None:
        """Clean up resources."""
        print(f"[Text Processing] Cleaning up {self.processor} processor")
        self.initialized = False


class MockPluginManager:
    """Mock implementation of the PluginManager."""

    @staticmethod
    def create_provider(provider_type: str, provider_name: str, **kwargs) -> Any:
        """Create a provider instance."""
        if provider_type == "workflow" and provider_name == "text_processing":
            return MockTextProcessingWorkflow(**kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider_type}/{provider_name}")


class MockPepperPy:
    """Mock implementation of the PepperPy class."""

    def __init__(self):
        self.initialized = False

    async def __aenter__(self):
        """Context manager entry."""
        print("[PepperPy] Initializing framework")
        self.initialized = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        print("[PepperPy] Cleaning up framework")
        self.initialized = False


# Setup paths
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main() -> None:
    """Run the example."""
    print("Text Processing Workflow Example")
    print("=" * 50)

    # Initialize PepperPy
    async with MockPepperPy() as pepper:
        # Get workflow using plugin_manager
        workflow_provider = MockPluginManager.create_provider(
            "workflow", "text_processing", processor="spacy"
        )

        # Initialize workflow
        await workflow_provider.initialize()

        # Process a single text
        print("\nProcessing single text...")
        text = "PepperPy is a Python framework for building AI applications."
        result = await workflow_provider.process_text(text)

        print(f"\nInput: {text}")
        print(f"Entities: {result.entities}")
        print(f"Tokens: {result.tokens}")

        # Process multiple texts
        print("\nProcessing multiple texts...")
        texts = [
            "Machine learning models can analyze data efficiently.",
            "Natural language processing helps computers understand human language.",
            "Vector databases store embeddings for semantic search.",
        ]

        results = await workflow_provider.process_batch(texts)

        for i, (input_text, processed) in enumerate(zip(texts, results), 1):
            print(f"\n{i}. Input: {input_text}")
            print(f"   Entities: {processed.entities}")

        # Try with a different processor if available
        print("\nProcessing with NLTK processor...")
        try:
            nltk_workflow = MockPluginManager.create_provider(
                "workflow", "text_processing", processor="nltk"
            )
            await nltk_workflow.initialize()

            result = await nltk_workflow.process_text(
                "PepperPy makes AI integration easy and efficient."
            )
            print(f"Entities: {result.entities}")

            # Clean up
            await nltk_workflow.cleanup()
        except Exception as e:
            print(f"Error with NLTK processor: {e}")

        # Use the execute method directly
        print("\nUsing execute method...")
        result = await workflow_provider.execute(
            {
                "text": "This is a direct execution example.",
                "options": {"processing_options": {"include_pos": True}},
            }
        )

        processed = result["result"]
        print(f"Processed text has {len(processed.tokens)} tokens")

        # Clean up
        await workflow_provider.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
