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
    self.origin_x = self.center_x
    self.origin_y = self.center_y
    self.viewport_angle = 0
    self.transform_matrix: np.ndarray = np.eye(2)

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
    self.transform_matrix = np.dot(self.transform_matrix, np.array([[11/10, 0], [0, 11/10]]))

  def zoom_out(self, x, y):
    # self.position = self.get_clicked_point(x, y)
    self.transform_matrix = np.dot(self.transform_matrix, np.array([[10/11, 0], [0, 10/11]]))

  def recenter(self): self.position = np.array([0, 100, 0]); self.normal = np.array([0, -1, 0]); self.zoom = 1.0

  def project(self, point: Point) -> tuple[int, int]:
    # Ignore points behind camera
    # if np.dot(self.normal, point - self.position) < 0: point = self.position - self.normal
    x, y = self.world_to_camera(point)


    # Convert the camera view plane coordinates to viewport coordinates
    # - Centering the camera plane origin at the center of the viewport
    # - Scaling the coordinates by the zoom factor
    # - Adjusting the y-coordinate to match the canvas coordinate system
    position = self.camera_to_viewport(x, y)

    return position

  def world_to_camera(self, point: Point) -> tuple[int, int]:
    # Project the point onto the camera view plane
    t = sum(self.normal[i] * (self.position[i] - point[i]) for i in range(len(point)))
    t /= sum(self.normal[i] * self.normal[i] for i in range(len(point)))
    c = np.array([int(point[i] + t * self.normal[i]) for i in range(len(point))])
    
    v = c - self.position
    return np.dot(v, self.right), np.dot(v, self.up)

  def camera_to_world(self, x: int, y: int) -> Point:
    # Return a 3D point based on the camera's position and orientation
    # TODO: This creates a point at the exact position of the camera
    # It would be more useful if the user could control a distance from the camera to which clicks are applied
    # This is quite simple to implement, but it would mess with how zoom is behaving
    print(x, y)
    return x*self.right + y*self.up + self.position

  def camera_to_viewport(self, x: int, y: int) -> tuple[int, int]:
    y = self.viewport_height - y

    a = (x + self.center_x) / self.zoom - self.center_x
    b = (y + self.center_y) / self.zoom - self.center_y
    return int(a), int(b)

  def viewport_to_camera(self, x: int, y: int) -> tuple[int, int]:
    y = self.viewport_height - y
    a = (x - self.center_x) / self.zoom + self.center_x
    b = (y - self.center_y) / self.zoom + self.center_y
    print(a, b, self.center_x, self.center_y)
    return int(a), int(b)

  def viewport_to_word(self, x: int, y: int) -> Point:
    return self.camera_to_world(*self.viewport_to_camera(x, y))

@dataclass
class ScreenWireframe:
  start: Point
  end: Point | None = None
