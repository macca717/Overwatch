import shutil
from pathlib import Path
from subprocess import Popen
from time import sleep
import pytest
from app.datastructures import (
    AppConfig,
    Flags,
    ServerOptions,
    CameraOptions,
    ProcessingOptions,
    AlertingOptions,
)

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="module")
def app():
    cmd = [
        ".venv/bin/python3",
        "-O",
        "-m",
        "app",
        "-c",
        "tests/configs/api_test_config.toml",
        "--log-level",
        "debug",
        "--file",
        "tests/data/test.avi",
        "--test",
    ]
    process = Popen(cmd)
    sleep(10)
    yield
    process.terminate()
    process.wait(timeout=10)


@pytest.fixture(scope="function")
def app_with_handle():
    cmd = [
        ".venv/bin/python3",
        "-O",
        "-m",
        "app",
        "-c",
        "tests/configs/app_test_config.toml",
        "--log-level",
        "debug",
        "--file",
        "tests/data/test.avi",
        "--test",
    ]
    process = Popen(cmd)
    sleep(20)
    yield process
    process.terminate()
    process.wait(timeout=10)


@pytest.fixture(scope="function")
def config_path(tmp_path: Path):
    dest_path = tmp_path / "sample-config"
    src_path = Path(__file__).parent.parent / "sample-config.toml"
    shutil.copy(str(src_path), str(dest_path))
    return str(dest_path.absolute())


@pytest.fixture(scope="function")
def test_config(config_path: str) -> AppConfig:
    return AppConfig(
        server=ServerOptions(
            host_name="localhost",
            websocket_port=9999,
            webserver_port=8888,
            video_save_dir="/tmp",
        ),
        camera=CameraOptions(url="http://192.168.1.1/video.mjpeg"),
        flags=Flags(
            silent=True,
            config_path=config_path,
            log_level="error",
            test=True,
            file="tests/data/test.avi",
        ),
        processing=ProcessingOptions(
            fps=2,
            avg_weighting=0.5,
            dilation_iterations=0,
            fixed_lvl_threshold=5,
            gauss_ksize=5,
            pixel_threshold_hi=9000,
            pixel_threshold_lo=100,
        ),
        alerting=AlertingOptions(
            alert_time_s=45,
            end_time="08:15",
            min_movement_s=2,
            start_time="18:15",
            initial_alarm_duration_m=60,
            alarm_hysteresis_s=30,
        ),
        alerters={
            "test_alerter_one": {"test_grp": True, "enabled": True},
            "test_alerter_two": {"test_grp": False, "enabled": True},
            "test_alerter_three": {"test_grp": False, "enabled": True},
        },
        monitoring={"test": {"test_key": "1234456788"}},
    )
