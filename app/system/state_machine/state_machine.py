from __future__ import annotations
from enum import Enum
import functools
import types
from typing import List, Union
from finite_state_machine.state_machine import Transition
from finite_state_machine.exceptions import ConditionsNotMet, InvalidStartState

__all__ = ["StateMachine", "transition", "ConditionsNotMet", "InvalidStartState"]

State = Union[str, bool, int, Enum]


class StateMachine:
    """Reimplementation of the library's state machine."""

    def __init__(self, initial_state: State):
        self._state = initial_state

    @property
    def state(self):
        return self._state

    def __str__(self) -> str:
        if isinstance(self._state, Enum):
            return self._state.value
        return str(self._state)


def transition(source: List[State], target: State, conditions=None, on_error=None):
    """Re-implementation of https://github.com/alysivji/finite-state-machine
    Moved the wrapped function call to after the state is updated

    """
    # pylint: disable=protected-access,broad-except
    allowed_types = (str, bool, int, Enum)

    if isinstance(source, allowed_types):
        source = [source]
    if not isinstance(source, list):
        raise ValueError("Source can be a bool, int, string, Enum, or list")
    for item in source:
        if not isinstance(item, allowed_types):
            raise ValueError("Source can be a bool, int, string, Enum, or list")

    if not isinstance(target, allowed_types):
        raise ValueError("Target needs to be a bool, int or string")

    if not conditions:
        conditions = []
    if not isinstance(conditions, list):
        raise ValueError("conditions must be a list")
    for condition in conditions:
        if not isinstance(condition, types.FunctionType):
            raise ValueError("conditions list must contain functions")

    if on_error:
        if not isinstance(on_error, allowed_types):
            raise ValueError("on_error needs to be a bool, int or string")

    def transition_decorator(func):
        func.__fsm = Transition(func.__name__, source, target, conditions, on_error)

        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            self: StateMachine = args[0]

            if self.state not in source:
                exception_message = (
                    f"Current state is {self.state}. "
                    f"{func.__name__} allows transitions from {source}."
                )
                raise InvalidStartState(exception_message)

            conditions_not_met = []
            for condition in conditions:
                if not condition(*args, **kwargs):
                    conditions_not_met.append(condition)
            if conditions_not_met:
                raise ConditionsNotMet(conditions_not_met)

            try:
                self._state = target
                result = func(*args, **kwargs)
                return result
            except Exception as ex:
                if on_error:
                    self._state = on_error
                else:
                    raise ex

        return _wrapper

    return transition_decorator
