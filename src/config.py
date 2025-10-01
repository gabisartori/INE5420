import numpy as np

HEIGHT: int = 900
WIDTH: int = 1400
ZOOM: float = 1.0

WINDOW_NORMAL: np.ndarray = np.array([0, 0, -1])
WINDOW_POSITION: np.ndarray = np.array([0, 0, 100])

APPLICATION_NAME: str = "INE5420 - SGI"
INPUT_FILE: str | None = "example.obj"
OUTPUT_FILE: str | None = None
DEBUG: bool = True
DEFAULT_CLIPPING_ALGORITHM = 0  # Cohen-Sutherland
DEFAULT_CURVE_TYPE = 0  # Bezier