from typing import List
import numpy as np
import numpy.typing as npt
import pytest
from app.datastructures import AppConfig
from app.detection import BasicDetectionAlgorithm
from app.capture.filter import GuassianBlurFilter
from app.capture.device import FileCaptureDevice
from app.capture.helpers import preprocess_mat


pytestmark = pytest.mark.system


def load_video_data(path: str) -> List[npt.NDArray[np.uint8]]:
    file_cap = FileCaptureDevice(path, loop=False, fps=-1)
    video = list(file_cap.capture())
    processed = []
    for mat in video:
        mat = preprocess_mat(mat)
        processed.append(mat)
    return processed


@pytest.mark.slow
@pytest.mark.parametrize(
    "video_path, expected",
    [("tests/data/no_motion.avi", False), ("tests/data/motion.avi", True)],
)
def test_movement_detection(video_path: str, expected: bool, test_config: AppConfig):
    algo = BasicDetectionAlgorithm(test_config)
    filter_ = GuassianBlurFilter(test_config.processing.gauss_ksize)
    video_data = load_video_data(video_path)
    motion_detected = False
    for mat in video_data:
        filtered = filter_.apply(mat)
        mat_as_float = np.array(filtered, dtype=np.float32)
        motion_detected = algo.update(mat_as_float)
        if motion_detected:
            motion_detected = True
            break
    assert motion_detected == expected
