import numpy as np

import tkinter as tk
from dataclasses import dataclass
from my_types import Point

def normalize(v: Point) -> Point:
    """Normalize a vector."""
    norm = np.linalg.norm(v)
    return v / norm if norm != 0 else v

class Camera:
  def __init__(self, normal: Point, position: Point, viewport_width:int, viewport_height: int):
    self.normal: Point = normalize(normal)
    self.position: Point = position
    self.speed: int = 5
    self.zoom: float = 1.0
    self.viewport_width: int = viewport_width
    self.viewport_height: int = viewport_height

    UP = np.array([0, 1, 0])
    if np.array_equal(normal, UP) or np.array_equal(normal, -UP):
      self.right = np.array([1, 0, 0])
      self.up = np.array([0, 0, 1])
    else:
      self.right = normalize(np.cross(self.normal, UP))
      self.up = normalize(np.cross(self.right, self.normal))

  def move_up(self): self.position[2] -= self.speed/self.zoom

  def move_down(self): self.position[2] += self.speed/self.zoom

  def move_left(self): self.position[0] -= self.speed/self.zoom

  def move_right(self): self.position[0] += self.speed/self.zoom

  def move_below(self): self.position[1] -= self.speed/self.zoom

  def move_above(self): self.position[1] += self.speed/self.zoom

  def zoom_in(self, x, y):
    self.position = self.get_clicked_point(x, y)
    self.zoom *= 1.1

  def zoom_out(self, x, y):
    self.position = self.get_clicked_point(x, y)
    self.zoom /= 1.1

  def project(self, point: Point) -> Point:
    # Ignore points behind camera
    # if np.dot(self.normal, point - self.position) < 0: point = self.position - self.normal
    
    # Project the point onto the camera view plane
    t = sum(self.normal[i] * (self.position[i] - point[i]) for i in range(len(point)))
    t /= sum(self.normal[i] * self.normal[i] for i in range(len(point)))
    c = np.array([int(point[i] + t * self.normal[i]) for i in range(len(point))])
    
    v = c - self.position
    x = np.dot(v, self.right)
    y = np.dot(v, self.up)

    # Convert the camera view plane coordinates to viewport coordinates
    # - Centering the camera plane origin at the center of the viewport
    # - Scaling the coordinates by the zoom factor
    # - Adjusting the y-coordinate to match the canvas coordinate system
    x = (x + self.viewport_width / 2)
    y = (y + self.viewport_height / 2)
    x = int(x * self.zoom)
    y = int(y * self.zoom)
    y = self.viewport_height - y

    return np.array([x, y])
  
  def get_clicked_point(self, x: int, y: int) -> Point:
    # Reverse the projection to get the 3D point from the 2D click coordinates
    # Convert the viewport coordinates to camera view plane coordinates
    y = self.viewport_height - y
    x = int(x / self.zoom - self.viewport_width / 2)
    y = int(y / self.zoom - self.viewport_height / 2)

    # Return a 3D point based on the camera's position and orientation
    # TODO: This creates a point at the exact position of the camera
    # It would be more useful if the user could control a distance from the camera to which clicks are applied
    # This is quite simple to implement, but it would mess with how zoom is behaving
    return x*self.right + y*self.up + self.position


@dataclass
class ScreenWireframe:
  start: Point
  end: Point | None = None
