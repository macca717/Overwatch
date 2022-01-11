from typing import Callable, Dict, List
from .topics import Topic
from .events import Event

__all__ = ["Publisher"]

EventCallback = Callable[[Event], None]


CallbackRegister = Dict[Topic, List[EventCallback]]


class Publisher:
    def __init__(self):
        """Publisher/Subscriber Class"""
        self._register: CallbackRegister = dict()

    def send_message(self, topic: Topic, evt: Event):
        """Publish an event

        Args:
            topic (Topic): Topic to publish to.
            evt (Event): Event to publish.
        """
        if subscribers := self._register.get(topic):
            for listener in subscribers:
                listener(evt)

    def subscribe(self, topic: Topic, callback: EventCallback):
        """Subscribe to a topic

        Args:
            topic (Topic): Topic to subscribe to.
            callback (EventCallback): On event callback

        Returns:
            (EventCallback): Original callback

        Raises:
            Exception: Raised on duplicate subscribes
        """
        try:
            evt_list = self._register[topic]
        except KeyError:
            evt_list = []
            self._register[topic] = evt_list
            evt_list.append(callback)
        else:
            if callback not in evt_list:
                evt_list.append(callback)
            else:
                raise Exception("Already subscribed")
        return callback

    def unsubscribe(self, callback: EventCallback):
        """Unsubscribe a prevoiusly registered callback

        Args:
            callback (EventCallback): Callback to unsubcribe

        Raises:
            Exception: If callback is not subscribed
        """
        found = False
        for cb_list in self._register.values():
            if callback in cb_list:
                cb_list.remove(callback)
                found = True
                break
        if not found:
            raise Exception("Not subscribed")
