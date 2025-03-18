"""Pipeline composition module.

This module provides utilities for composing pipelines together into more complex
workflows. It leverages the unified pipeline framework from `pepperpy.core.pipeline`
to enable flexible composition patterns.

The composition patterns supported include:
- Sequential composition (chaining pipelines)
- Parallel composition (running pipelines concurrently)
- Conditional branching (dynamic pipeline selection)
- Error handling and recovery
- Pipeline state sharing via contexts

Note:
    This module is fully integrated with the unified pipeline framework.
    All composition patterns use the framework's core components.

Example:
    Sequential composition:
    >>> from pepperpy.core.pipeline.base import Pipeline, PipelineContext
    >>> from pepperpy.core.pipeline.stages import FunctionStage
    >>>
    >>> # Create component pipelines
    >>> p1 = Pipeline[str, str]("tokenize")
    >>> p1.add_stage(FunctionStage("split", lambda x, ctx: x.split()))
    >>>
    >>> p2 = Pipeline[List[str], str]("join")
    >>> p2.add_stage(FunctionStage("merge", lambda x, ctx: " ".join(x)))
    >>>
    >>> # Compose pipelines
    >>> composed = compose_sequential([p1, p2])
    >>> context = PipelineContext()
    >>> result = await composed.execute("hello world", context)
    >>> assert result == "hello world"

    Parallel composition:
    >>> from pepperpy.core.pipeline.base import Pipeline, PipelineContext
    >>> from pepperpy.core.pipeline.stages import FunctionStage
    >>>
    >>> # Create component pipelines
    >>> p1 = Pipeline[str, str]("upper")
    >>> p1.add_stage(FunctionStage("to_upper", lambda x, ctx: x.upper()))
    >>>
    >>> p2 = Pipeline[str, str]("lower")
    >>> p2.add_stage(FunctionStage("to_lower", lambda x, ctx: x.lower()))
    >>>
    >>> # Compose pipelines to run in parallel
    >>> composed = compose_parallel([p1, p2])
    >>> context = PipelineContext()
    >>> results = await composed.execute("Hello", context)
    >>> assert results == ["HELLO", "hello"]

    Conditional branching:
    >>> from pepperpy.core.pipeline.base import Pipeline, PipelineContext
    >>> from pepperpy.core.pipeline.stages import FunctionStage
    >>>
    >>> # Create component pipelines
    >>> p1 = Pipeline[str, str]("short")
    >>> p1.add_stage(FunctionStage("truncate", lambda x, ctx: x[:5]))
    >>>
    >>> p2 = Pipeline[str, str]("long")
    >>> p2.add_stage(FunctionStage("pad", lambda x, ctx: x.ljust(10)))
    >>>
    >>> # Create condition
    >>> def select_pipeline(data: str, context: PipelineContext) -> Pipeline:
    ...     return p1 if len(data) > 5 else p2
    >>>
    >>> # Compose with condition
    >>> composed = compose_conditional(select_pipeline)
    >>> context = PipelineContext()
    >>> result1 = await composed.execute("hello world", context)
    >>> result2 = await composed.execute("hi", context)
    >>> assert result1 == "hello"  # Truncated
    >>> assert result2 == "hi        "  # Padded

Key Components:
    - Sources: Factory methods for creating data sources
    - Processors: Factory methods for data transformations
    - Outputs: Factory methods for handling pipeline output
    - Pipeline: High-level pipeline composition interface

Example:
    >>> from pepperpy.core.composition import compose, Sources, Processors, Outputs
    >>> pipeline = compose("example")
    >>> pipeline.source(Sources.text("hello"))
    >>> pipeline.process(Processors.transform(str.upper))
    >>> pipeline.output(Outputs.console())
    >>> context = PipelineContext()
    >>> await pipeline.execute(context)
    HELLO

Note:
    This module is built on top of the unified pipeline framework.
    For more advanced use cases, consider using the framework in
    `pepperpy.core.pipeline` directly.

See Also:
    pepperpy.core.pipeline: The unified pipeline framework
    pepperpy.core.pipeline.stages: Pipeline stage implementations
    pepperpy.core.pipeline.registry: Pipeline and component registry
    pepperpy.core.intent: Intent recognition and processing
"""

from typing import Any, Callable, Generic, Optional, TypeVar

from pepperpy.core.pipeline.base import Pipeline as CorePipeline
from pepperpy.core.pipeline.base import PipelineContext
from pepperpy.core.pipeline.stages import FunctionStage

# Type variables for generic pipeline components
Input = TypeVar("Input")
Output = TypeVar("Output")
Intermediate = TypeVar("Intermediate")


class Sources:
    """Source factories for composition pipelines.

    This class provides factory methods for creating pipeline sources.
    Each factory returns a callable that produces data for the pipeline.

    Example:
        >>> pipeline = compose("example")
        >>> pipeline.source(Sources.text("hello"))
        >>> context = PipelineContext()
        >>> await pipeline.execute(context)
        'hello'
    """

    @staticmethod
    def text(content: str) -> Callable[[], str]:
        """Create a text source.

        Args:
            content: The text content to use as source.

        Returns:
            A callable that returns the text content.

        Example:
            >>> source = Sources.text("hello")
            >>> source()
            'hello'
        """
        return lambda: content

    @staticmethod
    def file(path: str) -> Callable[[], str]:
        """Create a file source.

        Args:
            path: The path to the file to read.

        Returns:
            A callable that reads and returns the file content.

        Example:
            >>> source = Sources.file("data.txt")
            >>> content = source()  # Reads data.txt
        """

        def source() -> str:
            with open(path, "r") as f:
                return f.read()

        return source

    @staticmethod
    def json(path: str) -> Callable[[], Any]:
        """Create a JSON source.

        Args:
            path: The path to the JSON file to read.

        Returns:
            A callable that reads and returns the parsed JSON content.

        Example:
            >>> source = Sources.json("data.json")
            >>> data = source()  # Reads and parses data.json
        """
        import json

        def source() -> Any:
            with open(path, "r") as f:
                return json.load(f)

        return source


class Processors:
    """Processor factories for composition pipelines.

    This class provides factory methods for creating pipeline processors.
    Each factory returns a callable that transforms data in the pipeline.

    Example:
        >>> pipeline = compose("example")
        >>> pipeline.process(Processors.transform(str.upper))
        >>> context = PipelineContext()
        >>> await pipeline.execute(context)
    """

    @staticmethod
    def transform(func: Callable[[Any], Any]) -> Callable[[Any, PipelineContext], Any]:
        """Create a transformation processor.

        Args:
            func: The function to use for transformation.

        Returns:
            A callable that applies the transformation function.

        Example:
            >>> processor = Processors.transform(str.upper)
            >>> context = PipelineContext()
            >>> processor("hello", context)
            'HELLO'
        """

        def wrapper(data: Any, context: PipelineContext) -> Any:
            result = func(data)
            context.set_metadata("transform_result", result)
            return result

        return wrapper

    @staticmethod
    def filter(
        predicate: Callable[[Any], bool],
    ) -> Callable[[Any, PipelineContext], Any]:
        """Create a filter processor.

        Args:
            predicate: The function to use for filtering.

        Returns:
            A callable that filters data based on the predicate.

        Example:
            >>> processor = Processors.filter(lambda x: len(x) > 3)
            >>> context = PipelineContext()
            >>> processor("hello", context)
            'hello'
            >>> processor("hi", context)
            None
        """

        def wrapper(data: Any, context: PipelineContext) -> Any:
            result = data if predicate(data) else None
            context.set_metadata("filter_result", bool(result))
            return result

        return wrapper

    @staticmethod
    def map(func: Callable[[Any], Any]) -> Callable[[Any, PipelineContext], Any]:
        """Create a mapping processor for collections.

        Args:
            func: The function to apply to each item.

        Returns:
            A callable that maps the function over a collection.

        Example:
            >>> processor = Processors.map(str.upper)
            >>> context = PipelineContext()
            >>> processor(["hello", "world"], context)
            ['HELLO', 'WORLD']
        """

        def wrapper(data: Any, context: PipelineContext) -> Any:
            result = [func(item) for item in data]
            context.set_metadata("map_result", result)
            return result

        return wrapper


class Outputs:
    """Output factories for composition pipelines.

    This class provides factory methods for creating pipeline outputs.
    Each factory returns a callable that handles the pipeline output.

    Example:
        >>> pipeline = compose("example")
        >>> pipeline.output(Outputs.console())
        >>> context = PipelineContext()
        >>> await pipeline.execute(context)
    """

    @staticmethod
    def console() -> Callable[[Any, PipelineContext], Any]:
        """Create a console output.

        Returns:
            A callable that prints data to the console.

        Example:
            >>> output = Outputs.console()
            >>> context = PipelineContext()
            >>> output("hello", context)  # Prints: hello
            hello
        """

        def wrapper(data: Any, context: PipelineContext) -> Any:
            print(data)
            context.set_metadata("console_output", str(data))
            return data

        return wrapper

    @staticmethod
    def file(path: str) -> Callable[[Any, PipelineContext], Any]:
        """Create a file output.

        Args:
            path: The path to write the output to.

        Returns:
            A callable that writes data to a file.

        Example:
            >>> output = Outputs.file("output.txt")
            >>> context = PipelineContext()
            >>> output("hello", context)  # Writes to output.txt
        """

        def wrapper(data: Any, context: PipelineContext) -> Any:
            with open(path, "w") as f:
                f.write(str(data))
            context.set_metadata("file_output", path)
            return data

        return wrapper

    @staticmethod
    def json(path: str) -> Callable[[Any, PipelineContext], Any]:
        """Create a JSON output.

        Args:
            path: The path to write the JSON output to.

        Returns:
            A callable that writes data as JSON.

        Example:
            >>> output = Outputs.json("output.json")
            >>> context = PipelineContext()
            >>> output({"key": "value"}, context)  # Writes to output.json
        """
        import json

        def wrapper(data: Any, context: PipelineContext) -> Any:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            context.set_metadata("json_output", path)
            return data

        return wrapper


class Pipeline(Generic[Input, Output]):
    """High-level pipeline composition interface.

    This class provides a fluent interface for composing pipelines using
    source, processor, and output components. It uses the unified pipeline
    framework internally while providing a simpler API for common use cases.

    Example:
        >>> pipeline = Pipeline("example")
        >>> pipeline.source(Sources.text("hello"))
        >>> pipeline.process(Processors.transform(str.upper))
        >>> pipeline.output(Outputs.console())
        >>> context = PipelineContext()
        >>> await pipeline.execute(context)
        HELLO

    Note:
        For more advanced use cases, consider using the unified pipeline
        framework directly via `pepperpy.core.pipeline`.
    """

    def __init__(self, name: str):
        """Initialize a pipeline.

        Args:
            name: The name of the pipeline.

        Example:
            >>> pipeline = Pipeline("example")
            >>> assert pipeline.name == "example"
        """
        self.name = name
        self._pipeline = CorePipeline[Input, Output](name)
        self._source: Optional[Callable[[], Any]] = None

    def source(self, source_factory: Callable[[], Input]) -> "Pipeline[Input, Output]":
        """Set the pipeline's data source.

        Args:
            source_factory: A callable that produces input data.

        Returns:
            self for method chaining.

        Example:
            >>> pipeline = Pipeline("example")
            >>> pipeline.source(Sources.text("hello"))
        """
        self._source = source_factory
        return self

    def process(
        self, processor_factory: Callable[[Input, PipelineContext], Intermediate]
    ) -> "Pipeline[Input, Intermediate]":
        """Add a processing stage to the pipeline.

        Args:
            processor_factory: A callable that transforms data.

        Returns:
            A new pipeline with updated output type.

        Example:
            >>> pipeline = Pipeline("example")
            >>> pipeline.process(Processors.transform(str.upper))
        """
        stage = FunctionStage(
            f"process_{len(self._pipeline.stages)}",
            processor_factory,
            description="Processing stage",
        )
        new_pipeline = Pipeline[Input, Intermediate](self.name)
        new_pipeline._pipeline = CorePipeline[Input, Intermediate](self.name)
        new_pipeline._source = self._source
        for existing_stage in self._pipeline.stages:
            new_pipeline._pipeline.add_stage(existing_stage)
        new_pipeline._pipeline.add_stage(stage)
        return new_pipeline

    def output(
        self, output_factory: Callable[[Output, PipelineContext], Any]
    ) -> "Pipeline[Input, Output]":
        """Add an output stage to the pipeline.

        Args:
            output_factory: A callable that handles output data.

        Returns:
            self for method chaining.

        Example:
            >>> pipeline = Pipeline("example")
            >>> pipeline.output(Outputs.console())
        """
        stage = FunctionStage(
            f"output_{len(self._pipeline.stages)}",
            output_factory,
            description="Output stage",
        )
        self._pipeline.add_stage(stage)
        return self

    async def execute(self, context: Optional[PipelineContext] = None) -> Any:
        """Execute the pipeline.

        Args:
            context: Optional pipeline context. If not provided,
                a new context will be created.

        Returns:
            The pipeline's output after processing.

        Example:
            >>> pipeline = Pipeline("example")
            >>> pipeline.source(Sources.text("hello"))
            >>> pipeline.process(Processors.transform(str.upper))
            >>> context = PipelineContext()
            >>> await pipeline.execute(context)
            'HELLO'
        """
        if not self._source:
            raise ValueError("No source configured for pipeline")

        if context is None:
            context = PipelineContext()

        # Get input from source
        data = self._source()
        context.set_metadata("source_data", data)

        # Execute pipeline
        result = await self._pipeline.execute(data, context)
        context.set_metadata("final_result", result)

        return result


def compose(name: str) -> Pipeline:
    """Create a new pipeline composition.

    This is the main entry point for creating pipelines using the
    composition API.

    Args:
        name: The name of the pipeline.

    Returns:
        A new pipeline instance.

    Example:
        >>> pipeline = compose("example")
        >>> pipeline.source(Sources.text("hello"))
        >>> pipeline.process(Processors.transform(str.upper))
        >>> pipeline.output(Outputs.console())
        >>> context = PipelineContext()
        >>> await pipeline.execute(context)
        HELLO
    """
    return Pipeline(name)


async def recognize_intent(text: str):
    """Recognize intent from text.

    This is a simplified implementation for the example.

    Args:
        text: The text to recognize intent from

    Returns:
        An Intent object containing the recognized intent

    Example:
        >>> intent = await recognize_intent("traduzir hello world")
        >>> assert intent.name == "translate"
        >>> assert intent.entities["text"] == "hello world"
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
