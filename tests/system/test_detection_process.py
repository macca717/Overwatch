import time
import pytest
from app.capture.detection_process import DetectionProcess


pytestmark = pytest.mark.system


def test_detection_process_shutdown(test_config):
    process = DetectionProcess(test_config)
    process.start()
    time.sleep(5)
    process.shutdown()
