import pytest
from app.events import Event, Publisher, Topic

# pylint: disable=redefined-outer-name


@pytest.fixture
def test_pub():
    return Publisher()


@pytest.fixture
def test_event():
    return Event(data=23)


def test_no_subscribers(test_event, test_pub):
    test_pub.send_message(Topic.SYSTEM_TICK, test_event)


def test_subscribe(test_pub):
    def callback(*_):
        pass

    test_pub.subscribe(Topic.SYSTEM_TICK, callback)


def test_unsubscribe(test_pub: Publisher):
    def callback(*_):
        pass

    handle = test_pub.subscribe(Topic.SYSTEM_TICK, callback)
    test_pub.unsubscribe(handle)


def test_callback(test_event, test_pub):
    result = 0

    def callback(evt: Event):
        nonlocal result
        result = evt.data

    test_pub.subscribe(Topic.SYSTEM_TICK, callback)
    test_pub.send_message(Topic.SYSTEM_TICK, test_event)
    assert result == 23


def test_multiple_subscribes(test_pub):
    def callback(*_):
        pass

    test_pub.subscribe(Topic.SYSTEM_TICK, callback)
    with pytest.raises(Exception, match="Already subscribed"):
        test_pub.subscribe(Topic.SYSTEM_TICK, callback)
