import numpy as np
from typing import TypeAlias
from dataclasses import dataclass

WorldPoint: TypeAlias = np.ndarray

@dataclass
class WindowPoint:
  x: int
  y: int

  def copy(self) -> 'WindowPoint':
    return WindowPoint(self.x, self.y)

  def __add__(self, other: 'WindowPoint | int') -> 'WindowPoint':
    match other:
      case int():
        return WindowPoint(self.x + other, self.y + other)
      case WindowPoint():
        return WindowPoint(self.x + other.x, self.y + other.y)
    raise TypeError(f"Unsupported type for addition: {type(other)}")

  def __sub__(self, other: 'WindowPoint | int') -> 'WindowPoint':
    match other:
      case int():
        return WindowPoint(self.x - other, self.y - other)
      case WindowPoint():
        return WindowPoint(self.x - other.x, self.y - other.y)
    raise TypeError(f"Unsupported type for subtraction: {type(other)}")
  
  def __mul__(self, other: 'WindowPoint | int | float ') -> 'WindowPoint':
    match other:
      case int():
        return WindowPoint(self.x * other, self.y * other)
      case float():
        return WindowPoint(int(self.x * other), int(self.y * other))
      case WindowPoint():
        return WindowPoint(self.x * other.x, self.y * other.y)
    raise TypeError(f"Unsupported type for multiplication: {type(other)}")
