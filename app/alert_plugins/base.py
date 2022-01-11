from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict
from loguru import logger
from app.helpers import retry

__all__ = ["AlerterPlugin", "retry"]


class AlerterPlugin(ABC):
    """AlerterPlugin Base Class

    Derive all user plugins from this class

    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Base Alerter Plugin

        Args:
            config (Dict[str, Any]): Config Dictionary
        """
        self.config = config
        self._common_dir = Path(__file__).parent / "common"

    @property
    @abstractmethod
    def name(self) -> str:
        """Alerter name

        Returns:
            str: Name of alerter
        """

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Enabled status

        Returns:
            bool: True if the plugin is enabled
        """

    @property
    @abstractmethod
    def in_test_grp(self) -> bool:
        """Test group check

        The test group is only run when an alerter test is run

        Returns:
            bool: Returns true if the alerter is in the test alerter group
        """

    @property
    def common_dir(self) -> Path:
        """Path to the common plugin directory

        Returns:
            Path: Common directory
        """
        return self._common_dir

    def raise_alert(self, msg: str) -> None:
        """Raise an alert

        This is a wrapper for user code

        Args:
            msg (str): Alert message
        """
        if self.enabled:
            self.run(msg)
        else:
            logger.info(f"Plugin {self.name} not run due to being disabled")

    @abstractmethod
    def run(self, msg: str) -> None:
        """Method that will run on an alert

        Dont call this method directly, call "raise_alert"

        Args:
            msg (str, optional): Alert message, if required. Defaults to None.
        """
