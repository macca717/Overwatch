import subprocess
from typing import Any, Dict
from loguru import logger
from app.helpers import feature_enabled
from .base import AlerterPlugin, retry


class SirenAlerter(AlerterPlugin):
    """Siren Alerter

    Plays a alarm sound file via SSH
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self._name = "siren"
        self._test_grp = config[self._name]["test_grp"]
        self._enabled = config[self._name]["enabled"]
        self._key_path = config[self._name]["ssh_key_path"]
        self._ssh_user = config[self._name]["ssh_user"]
        self._ssh_host = config[self._name]["ssh_host"]

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
    def run(self, *_) -> None:
        if feature_enabled("FF_SIREN"):
            cmd = [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-i",
                self._key_path,
                f"{self._ssh_user}@{self._ssh_host}",
                "aplay",
                "siren.wav",
                "-d",
                "21",
            ]
            try:
                subprocess.check_call(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                logger.info("Sent speaker alert")
            except subprocess.CalledProcessError as err:
                logger.error(err)
                raise err
        else:
            logger.debug("Siren feature flag not enabled")
