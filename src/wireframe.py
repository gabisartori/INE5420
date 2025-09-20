from dataclasses import dataclass, field
from components.my_types import Point
import numpy as np

@dataclass
class Wireframe:
  name: str
  points: list[Point]
  fill_color: str = "white"
  line_color: str = "black"
  thickness: float = 1
  id: int = 0

  def copy(self) -> 'Wireframe': raise NotImplementedError("Subclasses should implement this method")

  def __str__(self) -> str: raise NotImplementedError("Subclasses should implement this method")

  def rotate(self, degrees: int=5, point: Point | None=None) -> None:
    """Rotate the object around a given point in the XY plane."""
    """If no point is given, rotate around the center of the object."""
    if point is not None:
      px = point[0]
      py = point[1]
    else:
      px = self.center[0]
      py = self.center[1]
    self.translate(-px, -py)
    self.transform2d(np.array([
      [np.cos(np.radians(degrees)), -np.sin(np.radians(degrees)), 0],
      [np.sin(np.radians(degrees)),  np.cos(np.radians(degrees)), 0],
      [0, 0, 1]
    ]))
    self.translate(px, py)

  def translate(self, dx: float, dy: float) -> None:
    """Translate the object in the XY plane."""
    self.transform2d(np.array([
      [1, 0, dx],
      [0, 1, dy],
      [0, 0, 1]
    ]))

  def scale(self, factor: float) -> None:
    """Scale the object in the XY plane."""
    px = self.center[0]
    py = self.center[1]
    self.translate(-px, -py)
    self.transform2d(np.array([
      [factor, 0, 0],
      [0, factor, 0],
      [0, 0, 1]
    ]))
    self.translate(px, py)

  def transform2d(self, M: np.ndarray) -> None:
    """Aplica M (3x3 homogênea) aos pontos no plano XZ, mantendo Y."""
    self.points = [M @ p for p in self.points]

  @property
  def center(self) -> Point:
    return np.mean(self.points, axis=0).astype(int)

class PointObject(Wireframe):
  def __init__(self, name: str, center: Point, **kwargs):
    super().__init__(name, [center], **kwargs)

  def copy(self) -> 'PointObject':
    return PointObject(
      self.name,
      self.points[0].copy(),
      id=self.id,
      thickness=self.thickness,
      line_color=self.line_color,
      fill_color=self.fill_color
    )

  def __str__(self) -> str:
    return f"o {self.name}\nv {' '.join(map(str, self.points[0]))}\np 1"

class LineObject(Wireframe):
  def __init__(self, name: str, start: Point, end: Point, **kwargs):
    super().__init__(name, [start, end], **kwargs)
  def copy(self) -> 'LineObject':
    return LineObject(
      self.name, self.points[0].copy(),
      self.points[1].copy(),
      id=self.id,
      thickness=self.thickness,
      line_color=self.line_color,
      fill_color=self.fill_color
    )

  def __str__(self) -> str:
    return f"o {self.name}\nv {' '.join(map(str, self.points[0]))}\nv {' '.join(map(str, self.points[1]))}\nl 1 2"

class PolygonObject(Wireframe):
  def __init__(self, name: str, points: list[Point], **kwargs):
    super().__init__(name, points, **kwargs)

  def copy(self) -> 'PolygonObject':
    return PolygonObject(
      self.name,
      [p.copy() for p in self.points],
      id=self.id,
      thickness=self.thickness,
      line_color=self.line_color,
      fill_color=self.fill_color
    )

  def __str__(self) -> str:
    vertices_str = '\n'.join(f"v {' '.join(map(str, p))}" for p in self.points)
    indices_str = ' '.join(str(i + 1) for i in range(len(self.points)))
    return f"o {self.name}\n{vertices_str}\nl {indices_str}"

class CurveObject_2D(Wireframe):
  def __init__(self, name: str, points: list[Point], steps: int, **kwargs):
    super().__init__(name, points, **kwargs)
    self.steps = steps
    self.control_points = points[1:-1]
    self.begin_end_points = [points[0], points[-1]]

  def copy(self) -> 'CurveObject_2D':
    if len(self.points) == 4: 
      self.points = self.generate_bezier_points()
    return CurveObject_2D(
      name=self.name,
      points=[self.points[i].copy() for i in range(len(self.points))],
      steps=self.steps,
      id=self.id,
      thickness=self.thickness,
      line_color=self.line_color,
      fill_color=self.fill_color
    )
        
  def bezier_cubic(self, t, P0, P1, P2, P3) -> Point:
    """Calculate points on a cubic Bezier curve defined by four control points."""
    x = (1 - t)**3 * P0[0] + 3 * (1 - t)**2 * t * P1[0] + 3 * (1 - t) * t**2 * P2[0] + t**3 * P3[0]
    y = (1 - t)**3 * P0[1] + 3 * (1 - t)**2 * t * P1[1] + 3 * (1 - t) * t**2 * P2[1] + t**3 * P3[1]
    new_point = np.array([x, y, 1])
    return new_point

  def generate_bezier_points(self) -> list[Point]:
    """Generate points on the Bezier curve defined by the control points."""
    if len(self.points) != 4:
      raise ValueError("Cubic Bezier curve requires exactly 4 control points.")
    P0, P1, P2, P3 = self.points
    curve_points = [self.bezier_cubic(step / self.steps, P0, P1, P2, P3) for step in range(self.steps + 1)]
    return curve_points
    
    
    
    # P0, P1, P2, P3 = self.points
    # curve_points = []
    # for step in range(self.steps + 1):
    #   t = step / self.steps
    #   x = (1 - t)**3 * P0[0] + 3 * (1 - t)**2 * t * P1[0] + 3 * (1 - t) * t**2 * P2[0] + t**3 * P3[0]
    #   y = (1 - t)**3 * P0[1] + 3 * (1 - t)**2 * t * P1[1] + 3 * (1 - t) * t**2 * P2[1] + t**3 * P3[1]
    #   curve_points.append(np.array([x, y]))
    # return curve_points
        

  def __str__(self) -> str:
    vertices_str = '\n'.join(f"v {' '.join(map(str, p))}" for p in self.points)
    indices_str = ' '.join(str(i + 1) for i in range(len(self.points)))
    return f"o {self.name}\n{vertices_str}\nc {indices_str}"

