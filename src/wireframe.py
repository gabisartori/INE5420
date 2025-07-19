import tkinter as tk

from dataclasses import dataclass, field

type Point = list[int]

@dataclass
class Wireframe:
  name: str
  center: Point
  points: list[Point]
  color: str = "black"


  def draw(self, canva: tk.Canvas): raise NotImplementedError("Subclasses should implement this method")

  def __str__(self) -> str:
    points_str = ','.join(f"({','.join(map(str, point))})" for point in self.points)
    return f"{self.name};{points_str}"

  @staticmethod
  def from_string(data: str) -> 'Wireframe':
    name, points = data.split(';')
    points = points[1:-1].split('),(')
    points = [list(map(int, point.split(','))) for point in points]
    if len(points) == 1:
      return PointObject(name, points[0])
    elif len(points) == 2:
      return LineObject(name, points[0], points[1])
    else:
      return PolygonObject(name, points)


class PointObject(Wireframe):
  def __init__(self, name: str, center: Point):
    super().__init__(name, center, [center])

  def draw(self, canva: tk.Canvas):
    x, y = self.center
    canva.create_oval(x - 2, y - 2, x + 2, y + 2, fill=self.color)

class LineObject(Wireframe):
  def __init__(self, name: str, start: Point, end: Point):
    super().__init__(name, [(start[0] + end[0]) // 2, (start[1] + end[1]) // 2], [start, end])

  def draw(self, canva: tk.Canvas):
    start, end = self.points
    canva.create_line(start[0], start[1], end[0], end[1], fill=self.color)

class PolygonObject(Wireframe):
  def __init__(self, name: str, points: list[Point]):
    center = [sum(p[n] for p in points) // len(points) for n in range(len(points[0]))]
    super().__init__(name, center, points)

  def draw(self, canva: tk.Canvas):
    for i in range(len(self.points)):
      start = self.points[i]
      end = self.points[(i + 1) % len(self.points)]
      canva.create_line(start[0], start[1], end[0], end[1], fill=self.color)