import numpy as np
from my_types import WorldPoint, WindowPoint

from wireframe import Wireframe, WindowObject


def normalize(v: WorldPoint | list[float]) -> WorldPoint:
  """Normalize a vector."""
  v = np.array(v)
  norm = np.linalg.norm(v)
  return v / norm if norm != 0 else v

class Window:
  def __init__(
    self,
    width: int,
    height: int,
    position: list[float],
    normal: list[float],
    focus: list[float],
    up: list[float],
    movement_speed: int,
    rotation_speed: int,
    zoom: float,
    projection_type: int,
  ):
    self.position: WorldPoint = np.array(position)
    self.normal: WorldPoint = normalize(normal)
    self.focus: WorldPoint = np.array(focus)
    self.movement_speed: int = movement_speed
    self.rotation_speed: int = rotation_speed
    self.zoom: float = zoom
    self.width: int = width
    self.height: int = height
    self.window_focus_1: WindowPoint = WindowPoint(self.width // 2, self.height // 2)
    self.window_focus: WindowPoint = WindowPoint(0, 0)
    self.max_zoom = 100.0
    self.min_zoom = 0.1
    self.padding = 15

    self.chosen_projection = self.perspective_projection if projection_type == 1 else self.paralel_projection

    # Calculate the right and up vectors based on the normal vector and the given up vector
    if np.array_equal(self.normal, up) or np.array_equal(self.normal, -normalize(up)):
      self.right = np.array([1, 0, 0])
      self.up = np.array([0, 0, 1])
    else:
      self.right = normalize(np.cross(self.normal, up))
      self.up = normalize(np.cross(self.right, self.normal))

  def move_up(self): self.position[1] += max(self.movement_speed/self.zoom, 1)

  def move_down(self): self.position[1] -= max(self.movement_speed/self.zoom, 1)

  def move_left(self): self.position[0] -= max(self.movement_speed/self.zoom, 1)

  def move_right(self): self.position[0] += max(self.movement_speed/self.zoom, 1)

  def move_below(self): self.position[2] -= max(self.movement_speed/self.zoom, 1)

  def move_above(self): self.position[2] += max(self.movement_speed/self.zoom, 1)

  def rotate(self, angle: int | None = None, a1: int=0, a2: int=1):
    """Rotate the window around the normal vector."""
    angle = angle if angle is not None else self.rotation_speed
    M = np.eye(3)
    c = np.cos(np.radians(angle))
    s = np.sin(np.radians(angle))
    M[a1, a1] = c
    M[a1, a2] = -s
    M[a2, a1] = s
    M[a2, a2] = c
    self.right = M @ self.right
    self.up = M @ self.up
    self.normal = np.cross(self.up, self.right)
    # self.focus = M @ self.focus

  def zoom_in(self, x, y):
    if self.zoom <= self.max_zoom: self.zoom *= 1.1

  def zoom_out(self, x, y):
    if self.zoom >= self.min_zoom: self.zoom /= 1.1

  def recenter(self):
    self.position = np.array([0, 0, 100])
    self.normal = np.array([0, 0, -1])
    self.focus = self.position + self.normal*100
    self.right = np.array([1, 0, 0])
    self.up = np.array([0, 1, 0])
    self.zoom = 1.0
    self.window_focus = WindowPoint(0, 0)
    self.window_focus_1 = WindowPoint(self.width // 2, self.height // 2)

  def project(self, object: Wireframe) -> list[WindowObject]:
    object.projected_vertices = [self.world_to_viewport(v) for v in object.vertices]
    return object.window_objects

  def world_to_viewport(self, point: WorldPoint) -> WindowPoint:
    window_point = self.world_to_window(point)

    # Convert the window view plane coordinates to viewport coordinates
    # - Centering the window plane origin at the center of the viewport
    # - Scaling the coordinates by the zoom factor
    # - Adjusting the y-coordinate to match the canvas coordinate system
    return self.window_to_viewport(window_point)

  def world_to_window(self, point: WorldPoint) -> WindowPoint:
    return self.chosen_projection(point)

  def perspective_projection(self, point: WorldPoint) -> WindowPoint:
    return WindowPoint(0, 0)

  def _perspective_projection(self, point: WorldPoint) -> WindowPoint:
    point = point[:3]  # Ignore the homogeneous coordinate if present

    # Translate COP to the origin
    point = point - self.focus

    # Rotate world so VPN is aligned with z axis
    angle_x = np.arctan(self.normal[0]/self.normal[2])
    angle_y = np.arctan(self.normal[1]/self.normal[2])

    M1 = np.eye(3)
    M2 = np.eye(3)
    M1[1, 1] = np.cos(angle_x) #yz
    M1[1, 2] = -np.sin(angle_x)
    M1[2, 1] = np.sin(angle_x)
    M1[2, 2] = np.cos(angle_x)

    M2[0, 0] = np.cos(angle_y) # xz
    M2[0, 2] = np.sin(angle_y)
    M2[2, 0] = -np.sin(angle_y)
    M2[2, 2] = np.cos(angle_y)

    rotation = np.dot(M2, M1)
    point = np.dot(rotation, point)


    D = (M2 @ M1 @ self.position)[2]
    x, y = point[0]*D/point[2], point[1]*D/point[2]


    return WindowPoint(x, y)

  def paralel_projection(self, point: WorldPoint) -> WindowPoint:
    point = point[:3]  # Ignore the homogeneous coordinate if present
    point -= self.position
    z = self.normal
    x = np.cross(self.up, z)
    y = np.cross(z, x)
    M = np.array([
      [x[0], y[0], z[0], 0],
      [x[1], y[1], z[1], 0],
      [x[2], y[2], z[2], 0],
      [-np.dot(x, self.focus), -np.dot(y, self.focus), -np.dot(z, self.focus), 1.0]
    ])

    point_h = np.append(point[:3], 1.0)  # Ensure the point is in homogeneous coordinates
    transformed_point = M @ point_h

    return WindowPoint(transformed_point[0], transformed_point[1])

  def window_to_world(self, x: float, y: float) -> WorldPoint:
    # Return a 3D point based on the window's position and orientation
    # TODO: This creates a point at the exact position of the window
    # It would be more useful if the user could control a distance from the window to which clicks are applied
    # This is quite simple to implement, but it would mess with how zoom is behaving
    return np.append(-x*self.right + y*self.up + self.position, 1.0)

  def window_to_viewport(self, point: WindowPoint) -> WindowPoint:
    point = point*self.zoom + self.window_focus_1
    point.y = self.height - point.y
    return point

  def viewport_to_window(self, x: float, y: float) -> tuple[float, float]:
    y = self.height - y
    x = (x-self.window_focus_1.x)/self.zoom
    y = (y-self.window_focus_1.y)/self.zoom
    return x, y

  def viewport_to_world(self, x: float, y: float) -> WorldPoint:
    return self.window_to_world(*self.viewport_to_window(x, y))
    
  def click_in_window(self, x: float, y: float) -> bool:
    xmin, ymin, xmax, ymax = self.get_corners()
    return xmin <= x <= xmax and ymin <= y <= ymax

  def get_corners(self) -> tuple[float, float, float, float]:
    return self.padding, self.padding, self.width - self.padding, self.height - self.padding
