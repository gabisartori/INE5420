import numpy as np

import config
from components.my_types import Point
from data.matrices import rotation_matrix

def normalize(v: Point) -> Point:
  """Normalize a vector."""
  norm = np.linalg.norm(v)
  return v / norm if norm != 0 else v

class Window:
  #def __init__(self, normal: Point=config.WINDOW_NORMAL, position: Point=config.WINDOW_POSITION, width: int=config.WIDTH, height: int=config.HEIGHT, zoom: float=config.ZOOM):
  def __init__(self):
    self.preferences = config.PREFERENCES 
    self.normal: Point = normalize(self.preferences.window_normal)
    self.position: Point = self.preferences.window_position
    self.speed: int = 5
    self.zoom: float = self.preferences.zoom
    self.width: int = self.preferences.width*2//3
    self.height: int = self.preferences.height*5//6
    self.focus: tuple[float, float] = (self.width // 2, self.height // 2)
    self.window_focus: tuple[float, float] = (0, 0)
    self.max_zoom = 100.0
    self.min_zoom = 0.1
    self.padding = 15
    self.curve_coeff = self.preferences.curve_coefficient

    self.vrp = np.array([0, 0, 0])  # View Reference Point
    self.vpn = np.array([0, 0, -1]) # View Plane Normal
    self.vup = np.array([0, 1, 0])  # View Up Vector
    
    UP = np.array([0, 1, 0])
    if np.array_equal(self.normal, UP) or np.array_equal(self.normal, -UP):
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

  def rotate(self, angle: int=5, axis: str="z", clockwise: bool=True):
    """Rotate the window around the normal vector."""
    M = rotation_matrix(angle if clockwise else -angle, axis)
    self.right = normalize(M @ self.right)
    self.up = normalize(M @ self.up)
    self.normal = normalize(np.cross(self.right, self.up))
    
    # if PREFERENCES.mode == "2D": 
    #   self.right = normalize(M @ self.right)
    #   self.up = normalize(M @ self.up)
    #   self.normal = normalize(np.cross(self.right, self.up))
    # else: # 3D
    #   self.vpn = normalize(M @ self.vpn)
    #   self.vup = normalize(M @ self.vup)
    #   self.update_view_matrix()
    
  def zoom_in(self, x, y):
    if self.zoom <= self.max_zoom: self.zoom *= 1.1

  def zoom_out(self, x, y):
    if self.zoom >= self.min_zoom: self.zoom /= 1.1

  # TODO: Add a way for the user to call this function
  def recenter(self):
    self.position = np.array([0, 0, 100])
    self.normal = np.array([0, 0, -1])
    self.zoom = 1.0
    self.window_focus = (0, 0)
    self.focus = (self.width // 2, self.height // 2)

  def world_to_viewport(self, point: Point) -> tuple[float, float]:
    # Ignore points behind window
    # if np.dot(self.normal, point - self.position) < 0: point = self.position - self.normal
    x, y = self.world_to_window(point)

    # Convert the window view plane coordinates to viewport coordinates
    # - Centering the window plane origin at the center of the viewport
    # - Scaling the coordinates by the zoom factor
    # - Adjusting the y-coordinate to match the canvas coordinate system
    position = self.window_to_viewport(x, y)

    return position

  def world_to_window(self, point: Point) -> tuple[float, float]:
    # Project the point onto the window view plane
    t = sum(self.normal[i] * (self.position[i] - point[i]) for i in range(len(point)))
    t /= sum(self.normal[i] * self.normal[i] for i in range(len(point)))
    c = np.array([point[i] + t * self.normal[i] for i in range(len(point))])

    v = c - self.position
    return np.dot(v, self.right), np.dot(v, self.up)

  def window_to_world(self, x: float, y: float) -> Point:
    # Return a 3D point based on the window's position and orientation
    # TODO: This creates a point at the exact position of the window
    # It would be more useful if the user could control a distance from the window to which clicks are applied
    # This is quite simple to implement, but it would mess with how zoom is behaving
    return x*self.right + y*self.up + self.position

  def window_to_viewport(self, x: float, y: float) -> tuple[float, float]:
    x = x*self.zoom + self.focus[0]
    y = y*self.zoom + self.focus[1]
    y = self.height - y
    return x, y

  def viewport_to_window(self, x: float, y: float) -> tuple[float, float]:
    y = self.height - y
    x = (x-self.focus[0])/self.zoom
    y = (y-self.focus[1])/self.zoom
    return x, y

  def viewport_to_world(self, x: float, y: float) -> Point:
    return self.window_to_world(*self.viewport_to_window(x, y))

  def click_in_window(self, x: float, y: float) -> bool:
    xmin, ymin, xmax, ymax = self.get_corners()
    return xmin <= x <= xmax and ymin <= y <= ymax

  def get_corners(self) -> tuple[float, float, float, float]:
    return self.padding, self.padding, self.width - self.padding, self.height - self.padding
