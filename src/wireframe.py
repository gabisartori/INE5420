from dataclasses import dataclass, field
from screen import ScreenWireframe
from components.my_types import Point
import numpy as np

@dataclass
class Wireframe:
  name: str
  center: Point
  points: list[Point]
  color: str = "black"
  fill_color: str = "white"
  id: int = 0
  radius: float = field(default=0.0, repr=False)
  transform_matrix: np.ndarray = field(default_factory=lambda: np.identity(3), repr=False)

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
    
  def apply_matrix(self):
    new_pts = []
    for p in self.points:
      x, z = float(p[0]), float(p[2])
      x2, z2, _ = self.transform_matrix @ np.array([x, z, 1.0])
      q = p.astype(float).copy()
      q[0], q[2] = x2, z2
      new_pts.append(q)
    self.points = new_pts
    self.center = np.mean(np.stack(self.points), axis=0)
    self.transform_matrix = np.identity(3)  # Reset após aplicar

  def apply_transform(self, M: np.ndarray):
    self.transform_matrix = M @ self.transform_matrix
  
  def apply_point(M, p):
    x, z = float(p[0]), float(p[2])
    x2, z2, _ = M @ np.array([x, z, 1])
    q = p.astype(float).copy()
    q[0], q[2] = x2, z2
    return q

  def transform2d_xz(self, M: np.ndarray) -> None:
      """Aplica M (3x3 homogênea) aos pontos no plano XZ, mantendo Y."""
      new_pts = []
      for p in self.points:
        x, z = float(p[0]), float(p[2])
        x2, z2, _ = M @ np.array([x, z, 1.0])
        q = p.astype(float).copy()
        q[0], q[2] = x2, z2
        new_pts.append(q)
      self.points = new_pts
      self.center = np.mean(np.stack(self.points), axis=0)

class PointObject(Wireframe):
  def __init__(self, name: str, center: Point, id: int = 0, radius: float = 2):
    super().__init__(name, center, [center], id=id, radius=radius)

  def figures(self) -> list[ScreenWireframe]:
    return [ScreenWireframe(self.center)]
  
class LineObject(Wireframe):
  def __init__(self, name: str, start: Point, end: Point, id: int = 0):
    super().__init__(name, np.array([(start[0] + end[0]) // 2, (start[2] + end[2]) // 2]), [start, end], id=id)

  def figures(self) -> list[ScreenWireframe]:
    return [ScreenWireframe(self.points[0], self.points[1])]

class PolygonObject(Wireframe):
  def __init__(self, name: str, points: list[Point], id: int = 0):
    center = np.array([sum(p[n] for p in points) // len(points) for n in range(len(points[0]))])
    super().__init__(name, center, points, id=id)

  def figures(self) -> list[ScreenWireframe]:
    edges = []
    for i in range(len(self.points)):
      start = self.points[i]
      end = self.points[(i + 1) % len(self.points)]
      edges.append(ScreenWireframe(start, end))
    return edges