from dataclasses import dataclass, field
from screen import ScreenWireframe
from components.my_types import Point
import numpy as np

@dataclass
class Wireframe:
  name: str
  points: list[Point]
  center: Point = field(init=False, repr=False)
  color: str = "black"
  fill_color: str = "white"
  id: int = 0
  radius: float = field(default=0.0, repr=False)
  
  def __post_init__(self): self.center = self.get_center()

  def get_center(self) -> Point: return np.mean(self.points, axis=0).astype(int)

  def figures(self) -> list[ScreenWireframe]: raise NotImplementedError("Subclasses should implement this method")

  def __str__(self) -> str:
    points_str = ','.join(f"({','.join(map(str, point))})" for point in self.points)
    return f"{self.name};{points_str}"

  @staticmethod
  def from_string(data: str) -> 'Wireframe':
    name, points = data.split(';')
    points = points[1:-1].split('),(')
    points = [np.array(list(map(int, point.split(',')))) for point in points]
    if len(points) == 1:
      return PointObject(name, points[0])
    elif len(points) == 2:
      return LineObject(name, points[0], points[1])
    else:
      return PolygonObject(name, points)

  def rotate(self, degrees: int=5, point: Point | None=None) -> None:
    """Rotate the object around a given point in the XY plane."""
    M = np.array([
      [np.cos(np.radians(degrees)), -np.sin(np.radians(degrees)), 0],
      [np.sin(np.radians(degrees)),  np.cos(np.radians(degrees)), 0],
      [0, 0, 1]
    ])
    if point is not None:
      px = point[0]
      py = point[1]
    else:
      px = self.center[0]
      py = self.center[1]
    T1 = np.array([
      [1, 0, -px],
      [0, 1, -py],
      [0, 0, 1]
    ])
    T2 = np.array([
      [1, 0, px],
      [0, 1, py],
      [0, 0, 1]
    ])
    M = T2 @ M @ T1
    self.transform2d(M)

  def transform2d(self, M: np.ndarray) -> None:
    """Aplica M (3x3 homogênea) aos pontos no plano XZ, mantendo Y."""
    self.points = [np.dot(M, p) for p in self.points]

class PointObject(Wireframe):
  def __init__(self, name: str, center: Point, id: int = 0, radius: float = 2):
    super().__init__(name, [center], id=id, radius=radius)

  def figures(self) -> list[ScreenWireframe]:
    return [ScreenWireframe(self.center)]
  
class LineObject(Wireframe):
  def __init__(self, name: str, start: Point, end: Point, id: int = 0):
    super().__init__(name, [start, end], id=id)

  def figures(self) -> list[ScreenWireframe]:
    return [ScreenWireframe(self.points[0], self.points[1])]

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