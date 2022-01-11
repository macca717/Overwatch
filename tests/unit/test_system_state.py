from unittest.mock import Mock, patch
import pytest
import pytest_check as check
from app.datastructures import AlertData
from app.events import Publisher
from app.system.system import State, SystemState
from app.system.state_machine import ConditionsNotMet, InvalidStartState

# pylint: disable=unused-argument,redefined-outer-name,protected-access

MOCK_TIME = 99999.9


@pytest.fixture
def machine(test_config):
    return SystemState(
        publisher=Publisher(),
        config=test_config,
    )


@patch("time.time", return_value=MOCK_TIME)
def test_alarm_times(mock_time: Mock, machine: SystemState, test_config):
    machine = SystemState(
        publisher=Publisher(),
        config=test_config,
    )
    machine.alarm(AlertData(msg="Test", is_test=True, exclusion_list=[]))
    check.equal(machine.initial_alarm, MOCK_TIME)
    check.equal(machine.last_alarm, MOCK_TIME)
    check.equal(machine.state, State.ALARM)


@patch("time.time", return_value=MOCK_TIME)
def test_initial_alarm_time_valid_before_interval_exceeded(
    mock_time: Mock, machine: SystemState
):
    machine.alarm(AlertData(msg="Test", is_test=True, exclusion_list=[]))
    mock_time.return_value = MOCK_TIME + 180
    machine.alarm(AlertData(msg="Test", is_test=True, exclusion_list=[]))
    assert machine.initial_alarm == MOCK_TIME


@patch("time.time", return_value=MOCK_TIME)
def test_initial_alarm_time_valid_after_interval_exceeded(
    mock_time: Mock, machine: SystemState
):
    interval = MOCK_TIME + machine._initial_alarm_duration_s + 1
    machine.alarm(AlertData(msg="Test", is_test=True, exclusion_list=[]))
    mock_time.return_value = interval
    machine.alarm(AlertData(msg="Test", is_test=True, exclusion_list=[]))
    assert machine.initial_alarm == interval


@patch("time.time", return_value=MOCK_TIME)
def test_alarm_hysteresis_not_met(mock_time: Mock, machine: SystemState):
    machine.alarm(AlertData(msg="Test", is_test=True, exclusion_list=[]))
    mock_time.return_value = MOCK_TIME + 15
    with pytest.raises(ConditionsNotMet):
        machine.alarm(AlertData(msg="Test", is_test=True, exclusion_list=[]))


@patch("time.time", return_value=MOCK_TIME)
def test_alarm_hysteresis_met(mock_time: Mock, machine: SystemState):
    machine.alarm(AlertData(msg="Test", is_test=True, exclusion_list=[]))
    mock_time.return_value = MOCK_TIME + 31
    machine.alarm(AlertData(msg="Test", is_test=True, exclusion_list=[]))


def test_on_to_alarm_transition_valid(machine: SystemState):
    machine.alarm(AlertData(msg="Test", is_test=True, exclusion_list=[]))


def test_on_to_silence_transition(machine: SystemState):
    machine.silence(silenced_for=10)


def test_off_to_alarm_transition_invalid(machine: SystemState):
    machine.turn_off()
    with pytest.raises(InvalidStartState):
        machine.alarm(AlertData(msg="Test", is_test=True, exclusion_list=[]))


def test_off_to_silence_transition_invalid(machine: SystemState):
    machine.turn_off()
    with pytest.raises(InvalidStartState):
        machine.silence(silenced_for=30)
