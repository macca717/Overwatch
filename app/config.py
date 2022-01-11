from __future__ import annotations
from typing import Any, Dict, Protocol
from loguru import logger
import toml
from app.datastructures import AppConfig, Flags
from app.exceptions import ConfigFileNotFound, ConfigFileInvalidError


__all__ = ["save_config_to_file", "load_config_from_file", "TomlConfigSerializer"]


class ConfigSerializer(Protocol):
    """Config Serializer Interface"""

    def loads(self, location: str) -> Dict[str, Any]:  # type: ignore
        """Load the config as a dictionary

        Args:
            location (str): File to load path

        Returns:
            Dict[str, Any]: A loaded config dictionary
        """

    def dumps(self, destination: str, data: Dict[str, Any]):
        """Save the data dictionary to disk

        Args:
            destination (str): File path location
            data (Dict[str, Any]): Config data dictionary

        Raises:
            ConfigFileNotFound: On not found
            ConfigFileInvalidError: On invalid data
        """


class TomlConfigSerializer(ConfigSerializer):
    """TOML Config serializer"""

    def loads(self, location: str) -> Dict[str, Any]:
        try:
            with open(location, "r", encoding="utf-8") as file_handle:
                return dict(toml.loads(file_handle.read()))
        except (FileNotFoundError, IsADirectoryError) as ex:
            raise ConfigFileNotFound(f"Config File Error: {ex}") from ex
        except (TypeError, toml.TomlDecodeError) as ex:
            raise ConfigFileInvalidError(f"Config File Error: {ex}") from ex

    def dumps(self, destination: str, data: Dict[str, Any]):
        with open(destination, "w", encoding="utf-8") as file_handle:
            file_handle.write(toml.dumps(data))
            logger.debug(f"Config written to toml file {destination}")


def save_config_to_file(
    config: AppConfig,
    serializer: ConfigSerializer,
    path: str | None = None,
) -> None:
    """Save the config to file

    Args:
        config (AppConfig): Application config.
        serializer (ConfigSerializer): Serializer to use.
        path (str | None, optional): Save path. Defaults to None.
    """
    filepath = path or config.flags.config_path
    config_dict = config.dict(exclude={"flags"})  # Don't persist the commandline flags
    serializer.dumps(filepath, config_dict)


def load_config_from_file(flags: Flags, serializer: ConfigSerializer) -> AppConfig:
    """Load the config file

    Args:
        flags (Flags): Command line flags.
        serializer (ConfigSerializer): Serializer to use.

    Raises:
        ConfigFileNotFound
        ConfigFileInvalidError

    Returns:
        AppConfig: Parsed config
    """
    # TODO: Exception wrapper (pydantic error?, maybe encapsualate the error at the source dataclass)
    config_dict = serializer.loads(flags.config_path)
    config = AppConfig(**config_dict, flags=flags)
    return config
