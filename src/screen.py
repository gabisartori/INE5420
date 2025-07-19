import numpy as np

import tkinter as tk
from dataclasses import dataclass
from my_types import Point

class Camera:
  def __init__(self, normal: Point, position: Point):
    self.normal: Point = normal
    self.position: Point = position

    UP = np.array([0, 1, 0])
    if np.array_equal(normal, UP) or np.array_equal(normal, -UP):
      self.right = np.array([1, 0, 0])
      self.up = np.array([0, 0, 1])
    else:
      self.right = np.cross(self.normal, UP)
      self.up = np.cross(self.right, self.normal)


  def project(self, point: Point) -> Point:
    # Ignore points behind camera
    # if np.dot(self.normal, point - self.position) < 0: return np.array([-1, -1])
    
    
    t = sum(self.normal[i] * (self.position[i] - point[i]) for i in range(len(point)))
    t /= sum(self.normal[i] * self.normal[i] for i in range(len(point)))
    c = np.array([int(point[i] + t * self.normal[i]) for i in range(len(point))])
    
    v = c - self.position
    x = np.dot(v, self.right)
    y = np.dot(v, self.up)
    print(point)
    print(c)
    print(v)
    print(x, y)
    print(self.right, self.up)
    print()
    return np.array([x, y])


@dataclass
class ScreenWireframe:
  start: Point
  end: Point | None = None
