from enum import Enum, auto


class Topic(Enum):
    """Event Topic Class"""

    SYSTEM_TICK = auto()
    SYSTEM_SHUTDOWN = auto()
    SYSTEM_STATUS_UPDATE = auto()
    SYSTEM_ALARM = auto()
    SYSTEM_METRICS_READY = auto()
    SYSTEM_CONFIG_UPDATE = auto()
    CAPTURE_METRICS_UPDATE = auto()
    CAPTURE_DETECTION_UPDATE = auto()
    VIDEO_RAW_UPDATE = auto()
    SCHEDULER_CAPTURE_STOP = auto()
    COMMAND_REQUEST = auto()
    COMMAND_PROCESSED = auto()
