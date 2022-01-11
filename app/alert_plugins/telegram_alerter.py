from typing import Any, Dict
import apprise
from loguru import logger
from app.helpers import feature_enabled
from .base import AlerterPlugin, retry


class TelegramAlerter(AlerterPlugin):
    """Telegram Alerter

    Sends an alert via the Telegram messaging service
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self._name = "telegram"
        self._test_grp = config[self._name]["test_grp"]
        self._enabled = config[self._name]["enabled"]
        self._api_key = config[self._name]["api_key"]
        self._chat_ids = config[self._name]["chat_ids"]

    @property
    def name(self) -> str:
        return self._name

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def in_test_grp(self) -> bool:
        return self._test_grp

    @retry(Exception, tries=3, logger=logger)
    def run(self, msg: str) -> None:
        if feature_enabled("FF_TELEGRAM"):
            apobj = apprise.Apprise()
            chat_ids_str = ""
            for _id in self._chat_ids:
                chat_ids_str += f"{_id}/"
            apobj.add(f"tgram://{self._api_key}/{chat_ids_str}")
            if not apobj.notify(body=msg, title="Seizure App"):
                raise Exception("Telegram alerter failed to send")
            logger.info("Telegram alert sent")
        else:
            logger.debug("Telegram feature flag not enabled")
