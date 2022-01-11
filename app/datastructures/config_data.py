from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
import arrow
import pydantic
from app.helpers import to_lower_camel


class Flags(pydantic.BaseModel):
    """Commandline Flags

    Args:
        config_path (str): Path to the config toml file
        silent (bool): Suppress all alerts flag
        test (bool): True if the application is running in test mode
        log_level (str): Logging level string (debug, info, warning etc..)
        file (Optional[str]): If set loads a video file instead of a camera
    """

    config_path: str = pydantic.Field(...)
    silent: bool = pydantic.Field(...)
    test: bool = pydantic.Field(...)
    log_level: str = pydantic.Field(...)
    file: Optional[str] = pydantic.Field(...)


class CameraOptions(pydantic.BaseModel, frozen=True):
    """Camera Config Options

    Args:
        fps (int): Camera frames per second
        height (int): Frame image height in pixels
        width (int): Frame image width in pixels
        url (str): Camera url
    """

    url: str = pydantic.Field(...)


class ServerOptions(pydantic.BaseModel):
    """Server Config Options

    Args:
        host_name (str): Server hostname
        video_save_dir (str): Directory where captured video is saved
        websocket_port (int): Web socket port
        webserver_port (int): Web server port
    """

    host_name: str = pydantic.Field(...)
    video_save_dir: str = pydantic.Field(...)
    websocket_port: int = pydantic.Field(...)
    webserver_port: int = pydantic.Field(...)


class AlertingOptions(pydantic.BaseModel, frozen=True):
    """Alerting Options

    Args:
        start_time (Tuple[int, int]): Start hour and minute
        end_time (Tuple[int, int]): End hour and minute
        alert_time_s (int): Total time for alert to be raised
        min_movement_s (int): Window of time in which movement must occur
        initial_alarm_duration_m (int): Number of minutes for the initial alarm timer to be displayed
        alarm_hysteresis_s (int): Minimum time in seconds for an alarm to be re-raised
    """

    start_time: str = pydantic.Field(...)
    end_time: str = pydantic.Field(...)
    alert_time_s: int = pydantic.Field(...)
    min_movement_s: int = pydantic.Field(...)
    initial_alarm_duration_m: int = pydantic.Field(...)
    alarm_hysteresis_s: int = pydantic.Field(...)

    @pydantic.validator("start_time", "end_time")
    @classmethod
    def check_time_valid(cls, value: str):
        hours, minutes = cls.parse_time_str(value)
        cls._check_valid_hour(hours)
        cls._check_valid_minute(minutes)
        return value

    @staticmethod
    def _check_valid_hour(value: int):
        if value < 0 or value > 23:
            raise ValueError("The start hour must be between 0 and 23")

    @staticmethod
    def _check_valid_minute(value: int):
        if value < 0 or value > 59:
            raise ValueError("The minute value must be between 0 and 59")

    @staticmethod
    def parse_time_str(value: str) -> Tuple[int, int]:
        hours, minutes = [int(x) for x in value.split(":")]
        return (hours, minutes)


class ProcessingOptions(pydantic.BaseModel, frozen=True):
    # TODO: Docstring
    fps: int = pydantic.Field(...)
    avg_weighting: float = pydantic.Field(...)
    dilation_iterations: int = pydantic.Field(...)
    fixed_lvl_threshold: int = pydantic.Field(...)
    gauss_ksize: int = pydantic.Field(...)
    pixel_threshold_hi: int = pydantic.Field(...)
    pixel_threshold_lo: int = pydantic.Field(...)

    @pydantic.validator("fps")
    @classmethod
    def validate_camera_data(cls, value):
        if value <= 0:
            raise ValueError("The value must be greater than zero")
        return value

    @pydantic.validator("gauss_ksize")
    @classmethod
    def guass_ksize_must_be_odd(cls, value):
        if value % 2 == 0:
            raise ValueError("The guassian ksize option must be odd")
        return value


class AppConfig(pydantic.BaseModel):
    """Application Configuration

    Args:
        server (ServerOptions): Server options
        camera (CameraOptions): Camera options
        flag (Flags): Command line flags
        processing (ProcessingOptions): Processing options
        alerting (AlertingOptions): Alerting options
        alerters (Dict[str, Any]): Dictionary containing dynamically loaded alerter configurations
        monitoring [Dict[str, Any], optional): Optional dictionary containing monitoring options
    """

    server: ServerOptions = pydantic.Field(...)
    camera: CameraOptions = pydantic.Field(...)
    flags: Flags = pydantic.Field(...)
    processing: ProcessingOptions = pydantic.Field(...)
    alerting: AlertingOptions = pydantic.Field(...)
    alerters: Optional[Dict[str, Any]]
    monitoring: Optional[Dict[str, Any]]

    class Config:
        alias_generator = to_lower_camel
        allow_population_by_field_name = True
