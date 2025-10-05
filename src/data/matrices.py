import numpy as np
from config import PREFERENCES

def rotation_matrix(angle: int, axis: str="z") -> np.ndarray:
    """Create a rotation matrix for a given angle (in degrees) around a specified axis."""
    rad = np.radians(angle)

    if PREFERENCES.mode == "2D":
        axis = "z"

    if axis == "x":
        return np.array([
        [1, 0, 0],
        [0, np.cos(rad), -np.sin(rad)],
        [0, np.sin(rad),  np.cos(rad)]
        ])
    elif axis == "y":
        return np.array([
        [ np.cos(rad), 0, np.sin(rad)],
        [0, 1, 0],
        [-np.sin(rad), 0, np.cos(rad)]
        ])
    elif axis == "z":
        return np.array([
        [np.cos(rad), -np.sin(rad), 0],
        [np.sin(rad),  np.cos(rad), 0],
        [0, 0, 1]
        ])
    else:
        raise ValueError(f"Unknown axis: {axis}")
    