import numpy as np

import tkinter as tk
from dataclasses import dataclass
from my_types import Point

def normalize(v: Point) -> Point:
    """Normalize a vector."""
    norm = np.linalg.norm(v)
    return v / norm if norm != 0 else v

class Camera:
  def __init__(self, normal: Point, position: Point):
    self.normal: Point = normalize(normal)
    self.position: Point = position
    self.speed = 5

    UP = np.array([0, 1, 0])
    if np.array_equal(normal, UP) or np.array_equal(normal, -UP):
      self.right = np.array([1, 0, 0])
      self.up = np.array([0, 0, 1])
    else:
      self.right = normalize(np.cross(self.normal, UP))
      self.up = normalize(np.cross(self.right, self.normal))

  def move_up(self): self.position[2] -= self.speed

  def move_down(self): self.position[2] += self.speed

  def move_left(self): self.position[0] -= self.speed

  def move_right(self): self.position[0] += self.speed

  def move_below(self): self.position[1] -= self.speed

  def move_above(self): self.position[1] += self.speed

  def project(self, point: Point) -> Point:
    # Ignore points behind camera
    # if np.dot(self.normal, point - self.position) < 0: point = self.position - self.normal
    
    t = sum(self.normal[i] * (self.position[i] - point[i]) for i in range(len(point)))
    t /= sum(self.normal[i] * self.normal[i] for i in range(len(point)))
    c = np.array([int(point[i] + t * self.normal[i]) for i in range(len(point))])
    
    v = c - self.position
    x = np.dot(v, self.right)
    y = np.dot(v, self.up)
    return np.array([x, y])
  
  def get_clicked_point(self, x: int, y: int) -> Point:
    """Get the point in 3D space corresponding to a click on the viewport."""
    point = x*self.right + y*self.up + self.position
    print(point)
    return point


@dataclass
class ScreenWireframe:
  start: Point
  end: Point | None = None
