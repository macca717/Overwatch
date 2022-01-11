from typing import Protocol
import cv2
import numpy as np
import numpy.typing as npt


class Filter(Protocol):
    """Preprocessing Filter Interface"""

    def apply(
        self,
        mat: npt.NDArray[np.uint8],
    ) -> npt.NDArray[np.uint8]:
        """Apply the filter

        Args:
            mat (np.float32): Input image

        Returns:
            np.float32: Filtered ouput image
        """


class GuassianBlurFilter:
    def __init__(self, ksize: int, sigma_x: int = 0, sigma_y: int = 0) -> None:
        """Guassian Filter

        Blurs an image using a Gaussian filter.

        Args:
            ksize (int): Gaussian kernel size. ksize.width and ksize.height can differ but they both must be positive and odd.
                Or, they can be zero's and then they are computed from sigma.
            sigma_x (int, optional): Gaussian kernel standard deviation in X direction. Defaults to 0.
            sigma_y (int, optional): Gaussian kernel standard deviation in Y direction. Defaults to 0.
        """
        self.ksize = ksize
        self.sigma_x = sigma_x
        self.sigma_y = sigma_y

    def apply(
        self,
        mat: npt.NDArray[np.uint8],
    ) -> npt.NDArray[np.uint8]:
        return cv2.GaussianBlur(
            mat, (self.ksize, self.ksize), sigmaX=self.sigma_x, sigmaY=self.sigma_y
        )


class BilateralFilter:
    def __init__(self, diameter: int, sigma_color: int, sigma_space: int) -> None:
        """Bilateral filter

        Bilateral filtering can reduce unwanted noise very well while keeping edges fairly sharp.
        However, it is very slow compared to most filters.

        Sigma values: For simplicity, you can set the 2 sigma values to be the same.
        If they are small (< 10), the filter will not have much effect,
        whereas if they are large (> 150), they will have a very strong effect,
        making the image look "cartoonish".

        Large filters (d > 5) are very slow, so it is recommended to use d=5 for real-time applications,
        and perhaps d=9 for offline applications that need heavy noise filtering.

        Args:
            diameter (int): Diameter
            sigma_color (int): Filter sigma in the color space
            sigma_space (int): Filter sigma in the coordinate space
        """
        self.diameter = diameter
        self.sigma_color = sigma_color
        self.sigma_space = sigma_space

    def apply(
        self,
        mat: npt.NDArray[np.uint8],
    ) -> npt.NDArray[np.uint8]:
        return cv2.bilateralFilter(
            mat, self.diameter, self.sigma_color, self.sigma_space
        )
