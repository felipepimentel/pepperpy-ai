from abc import ABC, abstractmethod
from typing import Set

from ..errors import StateValidationError
from ..types import State


class StateValidator(ABC):
    @abstractmethod
    def validate(self, state: State) -> None:
        pass


class RequiredStateValidator(StateValidator):
    def __init__(self, required_states: Set[State]):
        self.required_states = required_states
        self.visited_states: Set[State] = set()

    def validate(self, state: State) -> None:
        if not self.required_states.issubset(self.visited_states):
            missing = self.required_states - self.visited_states
            raise StateValidationError(
                state,
                f"Required states not visited: {", ".join(s.name for s in missing)}",
            )

        self.visited_states.add(state)


class OrderedStateValidator(StateValidator):
    def __init__(self, ordered_states: list[State]):
        self.ordered_states = ordered_states
        self.current_index = 0

    def validate(self, state: State) -> None:
        if state not in self.ordered_states:
            raise StateValidationError(
                state,
                f"State {state.name} not in ordered sequence",
            )

        state_index = self.ordered_states.index(state)
        if state_index > self.current_index + 1:
            missing = self.ordered_states[self.current_index + 1:state_index]
            raise StateValidationError(
                state,
                f"States must be visited in order. Missing: {", ".join(s.name for s in missing)}",
            )

        self.current_index = state_index


__all__ = [
    "OrderedStateValidator",
    "RequiredStateValidator",
    "StateValidator",
]
