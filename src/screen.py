import numpy as np
import math

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
    self.center_x = viewport_width // 2
    self.center_y = viewport_height // 2
    self.viewport_angle = 0

    UP = np.array([0, 1, 0])
    if np.array_equal(normal, UP) or np.array_equal(normal, -UP):
      self.right = np.array([1, 0, 0])
      self.up = np.array([0, 0, 1])
    else:
      self.right = normalize(np.cross(self.normal, UP))
      self.up = normalize(np.cross(self.right, self.normal))

  def move_up(self): self.position[2] += max(self.speed/self.zoom, 1)

  def move_down(self): self.position[2] -= max(self.speed/self.zoom, 1)

  def move_left(self): self.position[0] -= max(self.speed/self.zoom, 1)

  def move_right(self): self.position[0] += max(self.speed/self.zoom, 1)

  def move_below(self): self.position[1] -= max(self.speed/self.zoom, 1)

  def move_above(self): self.position[1] += max(self.speed/self.zoom, 1)

  # def rotate_left(self):
  #   rotation_matrix = np.array([
  #     [math.cos(math.radians(5)), 0, -math.sin(math.radians(5))],
  #     [0, 1, 0],
  #     [math.sin(math.radians(5)), 0, math.cos(math.radians(5))]
  #   ])
  #   self.right = np.dot(rotation_matrix, self.right)

  def zoom_in(self, x, y):
    # self.position = self.get_clicked_point(x, y)
    self.zoom *= 1.1

  def zoom_out(self, x, y):
    # self.position = self.get_clicked_point(x, y)
    self.zoom /= 1.1

  def recenter(self): self.position = np.array([0, 100, 0]); self.normal = np.array([0, -1, 0]); self.zoom = 1.0

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
    x = (x + self.center_x)
    y = (y + self.center_y)
    x = int(self.center_x + self.zoom*(x-self.center_x))
    y = int(self.center_y + self.zoom*(y-self.center_y))
    y = self.viewport_height - y

    return np.array([x, y])
  
  def viewport_to_camera(self, x: int, y: int) -> tuple[int, int]:
    # Convert viewport coordinates to camera view plane coordinates
    y = self.viewport_height - y
    x = int((x - self.center_x) / self.zoom)
    y = int((y - self.center_y) / self.zoom)
    return x, y

  def get_clicked_point(self, x: int, y: int) -> Point:
    # Reverse the projection to get the 3D point from the 2D click coordinates
    x, y = self.viewport_to_camera(x, y)

    # Return a 3D point based on the camera's position and orientation
    # TODO: This creates a point at the exact position of the camera
    # It would be more useful if the user could control a distance from the camera to which clicks are applied
    # This is quite simple to implement, but it would mess with how zoom is behaving
    return x*self.right + y*self.up + self.position


@dataclass
class ScreenWireframe:
  start: Point
  end: Point | None = None
