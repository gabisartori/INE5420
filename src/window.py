import numpy as np

from components.my_types import Point
from config import PREFERENCES
from data.matrices import rotation_matrix

def normalize(v: Point) -> Point:
  """Normalize a vector."""
  norm = np.linalg.norm(v)
  return v / norm if norm != 0 else v

class Window:
  def __init__(self, normal: Point, position: Point, viewport_width: int, viewport_height: int, zoom: float=1.0):
    self.normal: Point = normalize(normal)
    self.position: Point = position
    self.speed: int = 5
    self.zoom: float = zoom
    self.viewport_width: int = viewport_width
    self.viewport_height: int = viewport_height
    self.viewport_focus: tuple[float, float] = (self.viewport_width // 2, self.viewport_height // 2)
    self.window_focus: tuple[float, float] = (0, 0)
    self.max_zoom = 100.0
    self.min_zoom = 0.1
    self.padding = 15
    self.coeff = PREFERENCES.curve_coefficient # coefficient only for curves
        
    self.vrp = np.array([0, 0, 0])  # View Reference Point
    self.vpn = np.array([0, 0, -1]) # View Plane Normal
    self.vup = np.array([0, 1, 0])  # View Up Vector

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

  def rotate(self, angle: int=5, axis: str="z"):
    """Rotate the window around the normal vector."""
    M = rotation_matrix(angle, axis)
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
    self.window_focus = (0, 0)
    self.viewport_focus = (self.viewport_width // 2, self.viewport_height // 2)

  def world_to_viewport(self, point: Point) -> tuple[float, float]:
    # Ignore points behind window
    # if np.dot(self.normal, point - self.position) < 0: point = self.position - self.normal
    if PREFERENCES.mode == "2D":
      x, y = self.world_to_window(point)
      x_vp, y_vp = self.window_to_viewport(x, y)
      return x_vp, y_vp
    else: # 3D
      if point.shape[0] == 3:
        point = np.append(point, 1)

      transformed = self.view_matrix @ point
      x, y, z, w = transformed
      x_vp, y_vp = self.window_to_viewport(x, y)

      return x_vp, y_vp, z, 1

    # Convert the window view plane coordinates to viewport coordinates
    # - Centering the window plane origin at the center of the viewport
    # - Scaling the coordinates by the zoom factor
    # - Adjusting the y-coordinate to match the canvas coordinate system
    # position = self.window_to_viewport(x, y)

    # return position

  def world_to_window(self, point: Point) -> tuple[float, float]:
    # Project the point onto the window view plane
    t = sum(self.normal[i] * (self.position[i] - point[i]) for i in range(len(point)))
    t /= sum(self.normal[i] * self.normal[i] for i in range(len(point)))
    c = np.array([point[i] + t * self.normal[i] for i in range(len(point))])

    v = c - self.position
    return np.dot(v, self.right), np.dot(v, self.up)

  def window_to_world(self, x: float, y: float, z: float | None) -> Point:
    # Return a 3D point based on the window's position and orientation
    # TODO: This creates a point at the exact position of the window
    # It would be more useful if the user could control a distance from the window to which clicks are applied
    # This is quite simple to implement, but it would mess with how zoom is behaving

    return self.position + x * self.right + y * self.up + (z * self.normal if z is not None else 0)

  def window_to_viewport(self, x: float, y: float, z: float = None) -> tuple[float, float, float | None]:
    x = x*self.zoom + self.viewport_focus[0]
    y = y*self.zoom + self.viewport_focus[1]
    y = self.viewport_height - y
    return x, y

  def viewport_to_window(self, x: float, y: float) -> tuple[float, float]:
    y = self.viewport_height - y
    x = (x-self.viewport_focus[0])/self.zoom
    y = (y-self.viewport_focus[1])/self.zoom
    return x, y

  def viewport_to_world(self, x: float, y: float, z: float | None) -> Point:
    x, y = self.viewport_to_window(x, y)
    return self.window_to_world(x, y, z)

  def is_point_in_viewport(self, point: Point) -> bool:
    x, y = self.world_to_window(point)
    half_width = (self.viewport_width / self.zoom) / 2
    half_height = (self.viewport_height / self.zoom) / 2
    center_x, center_y = self.window_focus
    return center_x - half_width <= x <= center_x + half_width and center_y - half_height <= y <= center_y + half_height

  def get_corners(self) -> tuple[float, float, float, float]:
    return self.padding, self.padding, self.viewport_width - self.padding, self.viewport_height - self.padding

  def update_view_matrix(self):
    # Cria a base da câmera
    n = self.vpn / np.linalg.norm(self.vpn)
    u = np.cross(self.vup, n)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)

    # Guarda os vetores caso precise
    self.u = u
    self.v = v
    self.n = n

    # Matriz de rotação (orienta a câmera)
    rot = np.array([
        [u[0], u[1], u[2], 0],
        [v[0], v[1], v[2], 0],
        [n[0], n[1], n[2], 0],
        [0,    0,    0,    1]
    ])

    # Matriz de translação (leva VRP para origem)
    trans = np.identity(4)
    trans[:3, 3] = -self.vrp

    # Matriz de visualização final
    self.view_matrix = rot @ trans

