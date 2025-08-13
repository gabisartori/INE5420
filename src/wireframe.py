from dataclasses import dataclass, field
from screen import ScreenWireframe
from my_types import Point
import numpy as np

@dataclass
class Wireframe:
  name: str
  center: Point
  points: list[Point]
  color: str = "black"
  fill_color: str = "white"
  id: int = 0

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


class PointObject(Wireframe):
  def __init__(self, name: str, center: Point, id: int = 0):
    super().__init__(name, center, [center], id=id)

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