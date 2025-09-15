import numpy as np

from dataclasses import dataclass
from components.my_types import Point

def normalize(v: Point) -> Point:
  """Normalize a vector."""
  norm = np.linalg.norm(v)
  return v / norm if norm != 0 else v

class Camera:
  def __init__(self, normal: Point, position: Point, viewport_width: int, viewport_height: int, zoom: float=1.0):
    self.normal: Point = normalize(normal)
    self.position: Point = position
    self.speed: int = 5
    self.zoom: float = zoom
    self.viewport_width: int = viewport_width
    self.viewport_height: int = viewport_height
    self.viewport_focus: tuple[float, float] = (self.viewport_width // 2, self.viewport_height // 2)
    self.camera_focus: tuple[float, float] = (0, 0)
    self.max_zoom = 100.0
    self.min_zoom = 0.1
    self.h_viewport_margin = int(0.1 * self.viewport_height)
    self.v_viewport_margin = int(0.02 * self.viewport_width)
    
    UP = np.array([0, 1, 0])
    if np.array_equal(normal, UP) or np.array_equal(normal, -UP):
      self.right = np.array([1, 0, 0])
      self.up = np.array([0, 0, 1])
    else:
      self.right = normalize(np.cross(self.normal, UP))
      self.up = normalize(np.cross(self.right, self.normal))

  def move_up(self): self.position[1] += max(self.speed/self.zoom, 1)

  def move_down(self): self.position[1] -= max(self.speed/self.zoom, 1)

  def move_left(self): self.position[0] -= max(self.speed/self.zoom, 1)

  def move_right(self): self.position[0] += max(self.speed/self.zoom, 1)

  def move_below(self): self.position[2] -= max(self.speed/self.zoom, 1)

  def move_above(self): self.position[2] += max(self.speed/self.zoom, 1)
  
  def rotate(self, angle: int=5):
    """Rotate the camera around the normal vector."""
    M = np.array([
      [np.cos(np.radians(angle)), -np.sin(np.radians(angle)), 0],
      [np.sin(np.radians(angle)),  np.cos(np.radians(angle)), 0],
      [0, 0, 1]
    ])
    self.right = normalize(M @ self.right)
    self.up = normalize(M @ self.up)
    self.normal = normalize(np.cross(self.right, self.up))

  def zoom_in(self, x, y):
    if self.zoom <= self.max_zoom: self.zoom *= 1.1

  def zoom_out(self, x, y):
    if self.zoom >= self.min_zoom: self.zoom /= 1.1

  # TODO: Add a way for the user to call this function
  def recenter(self):
    self.position = np.array([0, 0, 100])
    self.normal = np.array([0, 0, -1])
    self.zoom = 1.0
    self.camera_focus = (0, 0)
    self.viewport_focus = (self.viewport_width // 2, self.viewport_height // 2)

  def world_to_viewport(self, point: Point) -> tuple[float, float]:
    # Ignore points behind camera
    # if np.dot(self.normal, point - self.position) < 0: point = self.position - self.normal
    x, y = self.world_to_camera(point)


    # Convert the camera view plane coordinates to viewport coordinates
    # - Centering the camera plane origin at the center of the viewport
    # - Scaling the coordinates by the zoom factor
    # - Adjusting the y-coordinate to match the canvas coordinate system
    position = self.camera_to_viewport(x, y)

    return position

  def world_to_camera(self, point: Point) -> tuple[float, float]:
    # Project the point onto the camera view plane
    t = sum(self.normal[i] * (self.position[i] - point[i]) for i in range(len(point)))
    t /= sum(self.normal[i] * self.normal[i] for i in range(len(point)))
    c = np.array([point[i] + t * self.normal[i] for i in range(len(point))])

    v = c - self.position
    return np.dot(v, self.right), np.dot(v, self.up)

  def camera_to_world(self, x: float, y: float) -> Point:
    # Return a 3D point based on the camera's position and orientation
    # TODO: This creates a point at the exact position of the camera
    # It would be more useful if the user could control a distance from the camera to which clicks are applied
    # This is quite simple to implement, but it would mess with how zoom is behaving
    return x*self.right + y*self.up + self.position

  def camera_to_viewport(self, x: float, y: float) -> tuple[float, float]:
    x = x*self.zoom + self.viewport_focus[0]
    y = y*self.zoom + self.viewport_focus[1]
    y = self.viewport_height - y
    return x, y

  def viewport_to_camera(self, x: float, y: float) -> tuple[float, float]:
    y = self.viewport_height - y
    x = (x-self.viewport_focus[0])/self.zoom
    y = (y-self.viewport_focus[1])/self.zoom
    return x, y

  def viewport_to_world(self, x: float, y: float) -> Point:
    return self.camera_to_world(*self.viewport_to_camera(x, y))
    
  def is_point_in_viewport(self, point: Point) -> bool:
    x, y = self.world_to_camera(point)
    half_width = (self.viewport_width / self.zoom) / 2
    half_height = (self.viewport_height / self.zoom) / 2
    center_x, center_y = self.camera_focus
    return center_x - half_width <= x <= center_x + half_width and center_y - half_height <= y <= center_y + half_height

@dataclass
class ScreenWireframe:
  start: Point
  end: Point | None = None
