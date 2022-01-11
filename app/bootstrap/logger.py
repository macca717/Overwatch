import sys
from loguru import logger

# pylint: disable=line-too-long


def set_log_level(level_str: str) -> None:
    """Set the application wide log level

    Args:
        level_str (str): log level string
    """
    logger.remove()
    level = level_str.upper()
    logger.add(
        sys.stderr,
        format="<lvl>{level:<8}</> {time:YYYY-MM-DD at HH:mm:ss} |Proc:<c>{process.name}</> | Thread:<c>{thread}</> | {file:}, line {line} | {message}",
        level=level,
        colorize=True,
        enqueue=True,
    )
