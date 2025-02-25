def test_state_manager():
    from pepperpy.state import State, StateManager
    manager = StateManager()
    assert manager.current_state == State.UNREGISTERED
    manager.add_transition(State.UNREGISTERED, State.REGISTERED)
    manager.transition_to(State.REGISTERED)
    assert manager.current_state == State.REGISTERED