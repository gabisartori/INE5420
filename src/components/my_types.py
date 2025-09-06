import numpy as np
from typing import TypeAlias
from enum import Enum

Point: TypeAlias = np.ndarray

class CursorTypes(Enum):
    NORMAL = 1
    DRAG = 2
    ROTATE_WINDOW = 3