from collections import deque
import numpy as np
import pytest
from app.detection.basic_detection.basic import (
    is_in_alarm,
    bandpass_filter,
    raise_alert,
)


@pytest.mark.parametrize(
    "data, low_value, hi_value, expected",
    [
        (np.array([0]), 0, 0, np.array([0])),
        (np.array([1]), 0, 0, np.array([-1])),
        (np.array([0]), 10, 100, np.array([-1])),
        (np.array([10]), 10, 100, np.array([10])),
        (np.array([10]), 0, 1e10, np.array([10])),
        (np.array([10, 10, 10]), 0, 9, np.array([-1, -1, -1])),
        (np.array([1, 10, 10]), 0, 9, np.array([1, -1, -1])),
        (np.array([]), 0, 9, np.array([])),
    ],
)
def test_bandpass_filter(data, low_value, hi_value, expected):
    actual = bandpass_filter(data, low_value, hi_value)
    assert (actual == expected).all()


@pytest.mark.parametrize(
    "data, min_move_s, expected",
    [
        (deque([0] * 10), 10, False),
        (deque([1] * 10), 10, True),
        (deque([0] * 100), 10, False),
        (deque([0, 1, 1, 0] * 25), 10, True),
    ],
)
def test_is_in_alarm(data, min_move_s, expected):
    actual = is_in_alarm(data, min_move_s)
    assert actual == expected


@pytest.mark.skip
def test_raise_alert():
    ...
