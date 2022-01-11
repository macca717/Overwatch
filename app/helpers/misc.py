import os


def feature_enabled(flag: str) -> bool:
    """Checks whether a feature is enabled

    Args:
        flag (str): Flag name

    Returns:
        bool: True if flag is enabled, False otherwise
    """
    if os.getenv(flag):
        return True
    return False
