import cv2 as cv
import numpy as np
import numpy.typing as npt


def resize_mat(mat: np.ndarray, output_width: int = 640):
    """Resize an image matrix to a specified width

    Args:
        mat (np.ndarray): Image matrix
        output_width (int, optional): Desired output width in pixels. Defaults to 640.

    Returns:
        [type]: [description]
    """
    ratio = mat.shape[1] / output_width
    output_height = int(mat.shape[0] * ratio)
    dim = (output_width, output_height)
    return cv.resize(mat, dim, cv.INTER_AREA)


def mat_to_bytes(mat: np.ndarray, img_type: str = ".jpg") -> bytes:
    """Convert an image matrix to bytes

    Args:
        mat (np.ndarray): Image matrix to convert.
        img_type (str, optional): Required output format. Defaults to ".jpg".

    Returns:
        bytes: Image encoded as bytes.
    """
    return cv.imencode(img_type, mat)[1].tobytes()


def to_gray_scale(mat: np.ndarray) -> npt.NDArray[np.uint8]:
    """Convert an image matrix to gray scale

    Args:
        mat ([np.ndarray): Image matrix to convert

    Returns:
        npt.NDArray[np.uint8]: Converted image matrix as gray scale
    """
    return cv.cvtColor(mat, cv.COLOR_BGR2GRAY)


def preprocess_mat(mat: np.ndarray) -> npt.NDArray[np.uint8]:
    """Helper to resize and grey scale matrix

    Args:
        mat (np.ndarray): Input matrix

    Returns:
        npt.NDArray[np.uint8]: Matrix resized(width of 640px) and greyscaled
    """
    resized = resize_mat(mat)
    return to_gray_scale(resized)
