import numpy as np
from typing import TypeAlias
from enum import Enum

Point: TypeAlias = np.ndarray

class CursorTypes(Enum):
  NORMAL = 1
  DRAG = 2
  ROTATE_WINDOW = 3

class ColorScheme(Enum):
  LIGHT_CANVAS = "#fff"
  LIGHT_BG = "#f0f0f0"
  LIGHT_TEXT = "#000"
  LIGHT_BUTTON = "#f0f0f0"
  LIGHT_HIGH_CONTRAST_BUTTON = "#555"
  LIGHT_HIGH_CONTRAST_TEXT = "#fff"
  LIGHT_DEBUG_GRID = "#ddd"

  DARK_CANVAS = "#555"
  DARK_BG = "#333"
  DARK_TEXT = "#fff"
  DARK_BUTTON = "#555"
  DARK_HIGH_CONTRAST_BUTTON = "#f0f0f0"
  DARK_HIGH_CONTRAST_TEXT = "#000"
  DARK_BUTTON_INPUT = "#afaeae"
  DARK_DEBUG_GRID = "#777"

  DEFAULT_BUTTON_COLOR = "#f0f0f0"
