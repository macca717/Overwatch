from abc import ABC, abstractmethod
from typing import Protocol
import numpy as np
import numpy.typing as npt
from app.datastructures import ProcessingOptions


class DetectionAlgorithm(ABC):
    """Abstract detection algorithm

    Basis for all derived detection algorithms.
    """

    @abstractmethod
    def update(self, img: npt.NDArray[np.float32]) -> bool:
        """Update the algorithm with the latest image frame

        Args:
            img (npt.NDArray[np.float32]): Image array.

        Returns:
            bool: True if detection observed
        """


class MotionProcessor(Protocol):
    """Processor Interface"""

    def detect_motion(
        self, img: npt.NDArray[np.float32], options: ProcessingOptions
    ) -> int:
        """Process the image frame

        Args:
            img (npt.NDArray[np.float32]): Image array
            options (ProcessingOptions): Processing options

        Returns:
            int: Number of changed pixels
        """
