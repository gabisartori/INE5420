import numpy as np
from typing import TypeAlias
from dataclasses import dataclass

WorldPoint: TypeAlias = np.ndarray

@dataclass
class WindowPoint:
  x: int | float
  y: int | float

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
        return WindowPoint(self.x * other, self.y * other)
      case WindowPoint():
        return WindowPoint(self.x * other.x, self.y * other.y)
    raise TypeError(f"Unsupported type for multiplication: {type(other)}")

  def __radd__(self, other: 'int') -> 'WindowPoint': return self + other
  def __rsub__(self, other: 'int') -> 'WindowPoint': return WindowPoint(other - self.x, other - self.y)
  def __rmul__(self, other: 'int | float') -> 'WindowPoint': return self * other
