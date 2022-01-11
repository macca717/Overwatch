from pathlib import Path
import platform
import signal
from subprocess import run, Popen, TimeoutExpired
import time
import pytest

pytestmark = pytest.mark.integration

python_path = Path(".venv/bin/python3")

if platform.uname().system == "Windows":
    python_path = Path().cwd() / ".venv" / "Scripts" / "python"

BASE_CMD = [str(python_path), "-O", "-m", "app"]


@pytest.mark.parametrize("sig", (signal.SIGINT, signal.SIGTERM))
def test_clean_start_and_shutdown(sig):
    cmd = BASE_CMD + [
        "-c",
        "sample-config.toml",
        "--log-level",
        "warning",
        "--file",
        "tests/data/test.avi",
    ]
    process = None
    try:
        process = Popen(cmd, text=True)
        time.sleep(10.0)
        process.send_signal(sig)
        code = process.wait(10)
        assert code == 0
    except TimeoutExpired as ex:
        if process is not None:
            process.terminate()
            raise


def test_config_not_found():
    result = run(BASE_CMD + ["-c", "notfound.toml"], check=False)
    assert result.returncode == 2


def test_check_invalid_cmd():
    result = run(BASE_CMD + ["--invalid-flag", "notfound.toml"], check=False)
    assert result.returncode == 2
