from typing import Dict, Optional, Set

from .errors import InvalidStateTransitionError, StateValidationError
from .machine.base import StateMachine
from .monitoring.base import LoggingMonitor, MetricsMonitor, MonitoringSystem
from .types import State, StateMetadata, Transition, TransitionHooks
from .validation.base import OrderedStateValidator, RequiredStateValidator, StateValidator


class StateManager:
    def __init__(self, initial_state: State = State.UNREGISTERED):
        self.machine = StateMachine(initial_state)
        self.monitor = MonitoringSystem()
        self.monitor.add_monitor(MetricsMonitor())
        self.monitor.add_monitor(LoggingMonitor())
        self.validators: Dict[State, Set[StateValidator]] = {}
        self.global_validators: Set[StateValidator] = set()

    @property
    def current_state(self) -> State:
        return self.machine.current_state

    def add_transition(
        self,
        from_state: State,
        to_state: State,
        hooks: Optional[TransitionHooks] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        self.machine.add_transition(
            Transition(
                from_state=from_state,
                to_state=to_state,
                hooks=hooks,
                metadata=metadata,
            )
        )

    def add_validator(self, state: State, validator: StateValidator) -> None:
        if state not in self.validators:
            self.validators[state] = set()
        self.validators[state].add(validator)

    def add_global_validator(self, validator: StateValidator) -> None:
        self.global_validators.add(validator)

    def transition_to(self, target_state: State, metadata: Optional[Dict] = None) -> None:
        # Run global validators
        for validator in self.global_validators:
            validator.validate(target_state)

        # Run state-specific validators
        if target_state in self.validators:
            for validator in self.validators[target_state]:
                validator.validate(target_state)

        # Record transition start
        self.monitor.record_transition(self.current_state, target_state, metadata)

        # Perform transition
        self.machine.transition_to(target_state, metadata)

    def get_history(self) -> list[StateMetadata]:
        return self.machine.get_history()

    def get_metrics(self) -> dict:
        metrics_monitor = next(
            m for m in self.monitor.monitors if isinstance(m, MetricsMonitor)
        )
        return metrics_monitor.get_metrics()


__all__ = [
    "InvalidStateTransitionError",
    "OrderedStateValidator",
    "RequiredStateValidator",
    "State",
    "StateManager",
    "StateMetadata",
    "StateValidationError",
    "TransitionHooks",
]
