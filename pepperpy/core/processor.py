"""@file: processor.py
@purpose: Core processor base class for the Pepperpy framework
@component: Core
@created: 2024-02-18
@task: TASK-004
@status: active
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Processor(ABC, Generic[T]):
    """Base class for all processors in the framework.

    Processors are responsible for transforming data from one form to another.
    They can be used for pre-processing inputs, post-processing outputs,
    or any other data transformation needs.
    """

    @abstractmethod
    async def process(self, data: T, **kwargs: Any) -> T:
        """Process the input data.

        Args:
            data: Input data to process
            **kwargs: Additional processing parameters

        Returns:
            Processed data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError
