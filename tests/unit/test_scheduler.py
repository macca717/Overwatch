from datetime import datetime
import pytest
import arrow
from app.scheduler import check_if_scheduled


@pytest.mark.parametrize(
    "now, start, end, expected",
    [
        (
            arrow.get(datetime.now().replace(hour=17, minute=0)),
            (17, 30),
            (8, 00),
            False,
        ),
        (arrow.get(datetime.now().replace(hour=22, minute=0)), (17, 30), (8, 00), True),
        (arrow.get(datetime.now().replace(hour=4, minute=0)), (17, 30), (8, 00), True),
        (arrow.get(datetime.now().replace(hour=9, minute=0)), (17, 30), (8, 00), False),
    ],
)
def test_scheduler(now, start, end, expected):
    assert check_if_scheduled(now, start, end) == expected
