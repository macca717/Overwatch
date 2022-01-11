from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import time
from typing import List, Optional, TypedDict, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator
from app.helpers import to_lower_camel
from .config_data import AppConfig

__all__ = [
    "MetricsData",
    "State",
    "SystemStatus",
    "DetectionData",
    "CaptureUpdate",
    "CaptureMetrics",
    "AlertData",
    "CommandRequest",
    "SystemCommand",
    "SilenceCmdData",
    "TestCmdData",
    "ConfigUpdateData",
    "ShutdownData",
]


class MetricsData(BaseModel):

    time_stamp: float
    sys_cpu_percent: float
    sys_mem_percent: float
    cap_cpu_percent: float
    cap_mem_percent: float
    socket_connections: int
    loop_avg_s: float
    loop_max_s: float
    loop_min_s: float

    class Config:
        alias_generator = to_lower_camel
        allow_population_by_field_name = True


@dataclass(frozen=True)
class CaptureMetrics:
    pid: int | None
    frame_processing_times: List[float]


class State(Enum):
    ON = "on"
    OFF = "off"
    ALARM = "alarm"
    SILENCED = "silenced"
    ERROR = "error"


class SystemStatus(BaseModel):
    time_stamp: float = Field(default_factory=time.time)
    state: State = Field(default=State.ON)
    initial_alarm: float = Field(default=0.0)
    silenced_till: Optional[float] = Field(default=None)

    @staticmethod
    def update(status: SystemStatus, **kwargs):
        """Update an existing SystemStatus

        Raises:
            ValueError: If key is invalid

        Returns:
            SystemStatus: Updated SystemStatus
        """
        values = status.dict()
        values.update(kwargs)
        return SystemStatus(**values)

    class Config:
        alias_generator = to_lower_camel
        allow_population_by_field_name = True


@dataclass()
class DetectionData:
    pid: int | None
    running: bool
    motion_detected: bool
    frame_processing_times: List[float]


class CaptureUpdate(TypedDict):
    stop_processing: bool
    sensitivity: int


@dataclass(frozen=True)
class AlertData:
    msg: str
    is_test: bool
    exclusion_list: List[str]


class SystemCommand(Enum):
    SILENCE = "silence"
    TEST = "test"
    CONFIG_UPDATE = "config_update"
    SHUTDOWN = "shutdown"

    def __str__(self) -> str:
        return self.value


class SilenceCmdData(BaseModel):
    silence_for: float

    class Config:
        alias_generator = to_lower_camel
        allow_population_by_field_name = True


class TestCmdData(BaseModel):
    excluded: List[str]

    class Config:
        alias_generator = to_lower_camel
        allow_population_by_field_name = True


class ConfigUpdateData(BaseModel):
    config: AppConfig

    class Config:
        alias_generator = to_lower_camel
        allow_population_by_field_name = True


class ShutdownData(BaseModel):
    shutdown_in: int

    class Config:
        alias_generator = to_lower_camel
        allow_population_by_field_name = True


class CommandRequest(BaseModel, frozen=True):
    sender_uuid: Optional[UUID]
    command: SystemCommand
    data: Union[SilenceCmdData, TestCmdData, ConfigUpdateData, ShutdownData]

    @validator("data")
    @classmethod
    def data_must_match_command(cls, data, values):
        command = values["command"]
        if command == SystemCommand.TEST:
            if not isinstance(data, TestCmdData):
                raise TypeError("Data must contain test data.")
        elif command == SystemCommand.SILENCE:
            if not isinstance(data, SilenceCmdData):
                raise TypeError("Data must contain silence data.")
        elif command == SystemCommand.CONFIG_UPDATE:
            if not isinstance(data, ConfigUpdateData):
                raise TypeError("Data must contain config update data.")
        elif command == SystemCommand.SHUTDOWN:
            if not isinstance(data, ShutdownData):
                raise TypeError("Data must contain shutdown data.")
        else:
            raise ValueError("The data type is invalid.")
        return data
