from app.config import load_config_from_file, TomlConfigSerializer
from app.datastructures import AppConfig
from .cmd_parser import process_cmd_args
from .logger import set_log_level
from .welcome import print_welcome

__all__ = ["initialise"]


def initialise() -> AppConfig:
    """Initialise the application

    Loads external data (cmd line, config file)

    Returns:
        AppConfig: Application Config
    """
    flags = process_cmd_args()
    set_log_level(flags.log_level)
    loaded_config = load_config_from_file(flags, serializer=TomlConfigSerializer())
    print_welcome(loaded_config)
    return loaded_config
