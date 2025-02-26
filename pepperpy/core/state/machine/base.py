"""Base state machine implementation.

This module provides the core state machine functionality, including state
transitions, validation, hooks, and history tracking.
"""

from datetime import datetime

from ..errors import InvalidStateTransitionError, StateHookError
from ..types import State, StateMetadata, Transition


class StateMachine:
    """Core state machine implementation.

    The StateMachine class provides functionality for managing state transitions
    with validation, hooks, and history tracking.

    Args:
        initial_state (State, optional): Initial state. Defaults to UNREGISTERED.

    Example:
        >>> machine = StateMachine()
        >>> machine.add_transition(Transition(
        ...     from_state=State.UNREGISTERED,
        ...     to_state=State.REGISTERED
        ... ))
        >>> machine.transition_to(State.REGISTERED)
        >>> assert machine.current_state == State.REGISTERED
    """

    def __init__(self, initial_state: State = State.UNREGISTERED):
        """Initialize the state machine."""
        self.current_state = initial_state
        self.transitions: dict[State, dict[State, Transition]] = {}
        self.history: list[StateMetadata] = []
        self._add_to_history(initial_state, "Initial state")

    def add_transition(self, transition: Transition) -> None:
        """Add a valid state transition.

        Args:
            transition (Transition): The transition to add.

        Example:
            >>> machine = StateMachine()
            >>> machine.add_transition(Transition(
            ...     from_state=State.REGISTERED,
            ...     to_state=State.READY
            ... ))
        """
        if transition.from_state not in self.transitions:
            self.transitions[transition.from_state] = {}
        self.transitions[transition.from_state][transition.to_state] = transition

    def can_transition_to(self, target_state: State) -> bool:
        """Check if transition to target state is valid.

        Args:
            target_state (State): The state to check transition to.

        Returns:
            bool: True if transition is valid, False otherwise.

        Example:
            >>> machine = StateMachine()
            >>> machine.add_transition(Transition(
            ...     from_state=State.UNREGISTERED,
            ...     to_state=State.REGISTERED
            ... ))
            >>> assert machine.can_transition_to(State.REGISTERED)
        """
        if self.current_state not in self.transitions:
            return False
        return target_state in self.transitions[self.current_state]

    def get_valid_transitions(self) -> set[State]:
        """Get all valid states that can be transitioned to.

        Returns:
            Set[State]: Set of valid target states.

        Example:
            >>> machine = StateMachine()
            >>> machine.add_transition(Transition(
            ...     from_state=State.UNREGISTERED,
            ...     to_state=State.REGISTERED
            ... ))
            >>> valid = machine.get_valid_transitions()
            >>> assert State.REGISTERED in valid
        """
        if self.current_state not in self.transitions:
            return set()
        return set(self.transitions[self.current_state].keys())

    def transition_to(self, target_state: State, metadata: dict | None = None) -> None:
        """Perform state transition with validation and hooks.

        Args:
            target_state (State): The target state to transition to.
            metadata (Optional[Dict]): Additional metadata for the transition.

        Raises:
            InvalidStateTransitionError: If transition is not valid.
            StateValidationError: If state validation fails.
            StateHookError: If a transition hook fails.

        Example:
            >>> machine = StateMachine()
            >>> machine.add_transition(Transition(
            ...     from_state=State.UNREGISTERED,
            ...     to_state=State.REGISTERED,
            ...     metadata={"reason": "registration complete"}
            ... ))
            >>> machine.transition_to(State.REGISTERED)
        """
        if not self.can_transition_to(target_state):
            raise InvalidStateTransitionError(self.current_state, target_state)

        transition = self.transitions[self.current_state][target_state]

        try:
            if transition.hooks and transition.hooks.pre_transition:
                transition.hooks.pre_transition(self)
        except Exception as e:
            if transition.hooks and transition.hooks.on_error:
                transition.hooks.on_error(self)
            raise StateHookError("pre_transition", target_state, e)

        old_state = self.current_state
        self.current_state = target_state

        description = f"Transitioned from {old_state.name} to {target_state.name}"
        self._add_to_history(target_state, description, metadata)

        try:
            if transition.hooks and transition.hooks.post_transition:
                transition.hooks.post_transition(self)
        except Exception as e:
            if transition.hooks and transition.hooks.on_error:
                transition.hooks.on_error(self)
            raise StateHookError("post_transition", target_state, e)

    def get_history(self) -> list[StateMetadata]:
        """Get the history of state transitions.

        Returns:
            List[StateMetadata]: List of state transitions in chronological order.

        Example:
            >>> machine = StateMachine()
            >>> machine.transition_to(State.REGISTERED)
            >>> history = machine.get_history()
            >>> assert len(history) >= 2  # Initial + transition
        """
        return self.history.copy()

    def _add_to_history(
        self, state: State, description: str, metadata: dict | None = None
    ) -> None:
        """Add a state transition to history.

        Args:
            state (State): The new state.
            description (str): Description of the transition.
            metadata (Optional[Dict]): Additional metadata.
        """
        self.history.append(
            StateMetadata(
                description=description,
                timestamp=datetime.now().timestamp(),
                metadata=metadata,
            )
        )


__all__ = ["StateMachine"]
