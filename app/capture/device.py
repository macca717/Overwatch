from __future__ import annotations
import time
from typing import Generator, Protocol
import cv2 as cv
import numpy as np
from app.exceptions import CaptureError


class CaptureDevice(Protocol):
    """Capture Device Interface"""

    def capture(self) -> Generator[np.ndarray, None, None]:
        """Capture Generator

        Raises:
            ConnectionError: On failed connection.
            CaptureError: On frame capture error

        Yields:
            Generator[np.ndarray, None, None]: An image matrix
        """


class CameraCaptureDevice:
    def __init__(self, url: str) -> None:
        """Standard camera capture device

        Args:
            url (str): Url of video resource
        """
        self.url = url
        self.cap: cv.VideoCapture | None = None

    def capture(self) -> Generator[np.ndarray, None, None]:
        try:
            self.cap = cv.VideoCapture(self.url)
            while True:
                if not self.cap.isOpened():
                    raise ConnectionError(f"Couldn't open camera at {self.url}")
                ret, mat = self.cap.read()
                if not ret:
                    raise CaptureError()
                yield mat
        finally:
            if self.cap:
                self.cap.release()


class FileCaptureDevice:
    def __init__(self, path: str, loop: bool = True, fps: int = 15) -> None:
        """Video file capture device

        Args:
            path (str): Path to file
            loop (bool, optional): Continous looping of video file. Defaults to True.
            fps (int, optional): Required frame rate. Defaults to 15. -1 is no frame delay
        """
        self.path = path
        self.cap: cv.VideoCapture | None = None
        self.loop = loop
        if fps == -1:
            self.frame_wait = 0.0
        else:
            self.frame_wait = 1 / fps

    def capture(self) -> Generator[np.ndarray, None, None]:
        try:
            self.cap = cv.VideoCapture(self.path)
            while True:
                if not self.cap.isOpened():
                    raise ConnectionError(f"Couldn't open file at {self.path}")
                ret, mat = self.cap.read()
                if not ret:
                    if self.loop:
                        raise CaptureError("End of file")  # TODO: New exception???
                    break
                yield mat
                time.sleep(self.frame_wait)
        finally:
            if self.cap:
                self.cap.release()
