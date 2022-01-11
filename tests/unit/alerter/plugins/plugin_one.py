from typing import Any, Dict
from app.alert_plugins import AlerterPlugin


class PluginOne(AlerterPlugin):
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self._in_test_grp = config[self.name]["test_grp"]
        self._enabled = config[self.name]["enabled"]

    @property
    def name(self) -> str:
        return "test_alerter_one"

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def in_test_grp(self) -> bool:
        return self._in_test_grp

    def run(self, msg: str) -> None:
        print(f"{self.name} ran")


class PluginTwo(AlerterPlugin):
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self._in_test_grp = config[self.name]["test_grp"]
        self._enabled = config[self.name]["enabled"]

    @property
    def name(self) -> str:
        return "test_alerter_two"

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def in_test_grp(self) -> bool:
        return self._in_test_grp

    def run(self, msg: str) -> None:
        print(f"{self.name} ran")
