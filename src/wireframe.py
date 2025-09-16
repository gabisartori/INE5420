from dataclasses import dataclass, field
from screen import ScreenWireframe
from components.my_types import Point
import numpy as np

@dataclass
class Wireframe:
  name: str
  points: list[Point]
  color: str = "black"
  fill_color: str = "white"
  id: int = 0
  radius: float = field(default=0.0, repr=False)

  def figures(self) -> list[ScreenWireframe]: raise NotImplementedError("Subclasses should implement this method")

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
  def __init__(self, name: str, center: Point, id: int = 0, radius: float = 2):
    super().__init__(name, [center], id=id, radius=radius)

  def figures(self) -> list[ScreenWireframe]:
    return [ScreenWireframe(self.points[0])] if self.points else []
  
  def copy(self) -> 'PointObject':
    return PointObject(self.name, self.points[0].copy(), id=self.id, radius=self.radius)

  def __str__(self) -> str:
    return f"o {self.name}\nv {' '.join(map(str, self.points[0]))}\np 1"

class LineObject(Wireframe):
  def __init__(self, name: str, start: Point, end: Point, id: int = 0):
    super().__init__(name, [start, end], id=id)

  def figures(self) -> list[ScreenWireframe]:
    return [ScreenWireframe(self.points[0], self.points[1])] if self.points else []
  
  def copy(self) -> 'LineObject':
    return LineObject(self.name, self.points[0].copy(), self.points[1].copy(), id=self.id)

  def __str__(self) -> str:
    return f"o {self.name}\nv {' '.join(map(str, self.points[0]))}\nv {' '.join(map(str, self.points[1]))}\nl 1 2"

class PolygonObject(Wireframe):
  def __init__(self, name: str, points: list[Point], id: int = 0):
    super().__init__(name, points, id=id)

  def figures(self) -> list[ScreenWireframe]:
    edges = []
    for i in range(len(self.points)):
      start = self.points[i]
      end = self.points[(i + 1) % len(self.points)]
      edges.append(ScreenWireframe(start, end))
    return edges
  
  def copy(self) -> 'PolygonObject':
    return PolygonObject(self.name, [p.copy() for p in self.points], id=self.id)

  def __str__(self) -> str:
    vertices_str = '\n'.join(f"v {' '.join(map(str, p))}" for p in self.points)
    indices_str = ' '.join(str(i + 1) for i in range(len(self.points)))
    return f"o {self.name}\n{vertices_str}\nl {indices_str}"
