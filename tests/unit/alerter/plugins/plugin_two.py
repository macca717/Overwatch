from typing import Any, Dict
from app.alert_plugins import AlerterPlugin


class PluginThree(AlerterPlugin):
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self._in_test_grp = config[self.name]["test_grp"]
        self._enabled = config[self.name]["enabled"]

    @property
    def name(self) -> str:
        return "test_alerter_three"

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def in_test_grp(self) -> bool:
        return self._in_test_grp

    def run(self, msg) -> None:
        print(f"{self.name}: {msg}")
