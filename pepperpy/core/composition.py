"""Composition module for PepperPy.

This module provides utilities for composing components in a pipeline.
"""

from typing import Any, Callable


class Sources:
    """Source factories for composition pipelines."""

    @staticmethod
    def text(content: str):
        """Create a text source."""
        return lambda: content

    @staticmethod
    def file(path: str):
        """Create a file source."""

        def source():
            with open(path, "r") as f:
                return f.read()

        return source

    @staticmethod
    def json(path: str):
        """Create a JSON source."""
        import json

        def source():
            with open(path, "r") as f:
                return json.load(f)

        return source


class Processors:
    """Processor factories for composition pipelines."""

    @staticmethod
    def transform(func: Callable[[Any], Any]):
        """Create a transformation processor."""
        return lambda data: func(data)

    @staticmethod
    def filter(predicate: Callable[[Any], bool]):
        """Create a filter processor."""
        return lambda data: data if predicate(data) else None

    @staticmethod
    def map(func: Callable[[Any], Any]):
        """Create a mapping processor for collections."""
        return lambda data: [func(item) for item in data]


class Outputs:
    """Output factories for composition pipelines."""

    @staticmethod
    def console():
        """Create a console output."""
        return lambda data: print(data)

    @staticmethod
    def file(path: str):
        """Create a file output."""

        def output(data):
            with open(path, "w") as f:
                f.write(str(data))
            return data

        return output

    @staticmethod
    def json(path: str):
        """Create a JSON output."""
        import json

        def output(data):
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            return data

        return output


class Pipeline:
    """A composition pipeline."""

    def __init__(self, name: str):
        """Initialize the pipeline."""
        self.name = name
        self._source = None
        self._processors = []
        self._output = None

    def source(self, source_factory: Callable[[], Any]):
        """Set the source for the pipeline."""
        self._source = source_factory
        return self

    def process(self, processor_factory: Callable[[Any], Any]):
        """Add a processor to the pipeline."""
        self._processors.append(processor_factory)
        return self

    def output(self, output_factory: Callable[[Any], Any]):
        """Set the output for the pipeline."""
        self._output = output_factory
        return self

    async def execute(self) -> Any:
        """Execute the pipeline."""
        if not self._source:
            raise ValueError("No source defined for pipeline")

        # Get data from source
        data = self._source()

        # Apply processors
        for processor in self._processors:
            data = processor(data)
            if data is None:
                return None

        # Apply output
        if self._output:
            return self._output(data)

        return data


def compose(name: str) -> Pipeline:
    """Create a new composition pipeline."""
    return Pipeline(name)


async def recognize_intent(text: str):
    """Recognize intent from text.

    This is a simplified implementation for the example.
    """
    # Simplified intent recognition
    intent_type = "query"
    confidence = 0.85
    entities = {}

    if "resumir" in text.lower():
        intent_name = "summarize"
        entities["url"] = text.split("em ")[-1] if "em " in text else None
    elif "traduzir" in text.lower():
        intent_name = "translate"
        entities["text"] = text.split("traduzir ")[-1] if "traduzir " in text else text
    elif "buscar" in text.lower() or "pesquisar" in text.lower():
        intent_name = "search"
        entities["query"] = (
            text.split("buscar ")[-1]
            if "buscar " in text
            else text.split("pesquisar ")[-1]
            if "pesquisar " in text
            else text
        )
    else:
        intent_name = "unknown"
        confidence = 0.3

    # Create intent object
    class Intent:
        def __init__(self, name, type, confidence, entities):
            self.name = name
            self.type = type
            self.confidence = confidence
            self.entities = entities

    class IntentType:
        QUERY = "query"
        COMMAND = "command"
        CONVERSATION = "conversation"

        def __init__(self, value):
            self.value = value

    return Intent(
        name=intent_name,
        type=IntentType(intent_type),
        confidence=confidence,
        entities=entities,
    )
