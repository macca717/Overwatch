# Application Exceptions


class OverwatchException(Exception):
    """Base Application Exception"""


class CommandParserException(OverwatchException):
    """Exception for invalid command line arguement input"""


class ConfigFileNotFound(OverwatchException):
    """Exception for missing config file"""


class ConfigFileInvalidError(OverwatchException):
    """Exception for invalid config file"""


class CaptureError(OverwatchException):
    """Video Capture Exception"""


class CaptureConnectionError(CaptureError):
    """Video Connection Exception"""
