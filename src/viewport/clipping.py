import sys
sys.path.append("..")

from enum import Enum
import numpy as np
from wireframe import PolygonObject, Wireframe
from components.my_types import Point

class Code(Enum):
  INSIDE = 0  # 0000
  LEFT = 1  # 0001
  RIGHT = 2   # 0010
  BOTTOM = 4  # 0100
  TOP = 8   # 1000

class ClippingAlgorithm(Enum):
  COHEN_SUTHERLAND = 1
  LIANG_BARSKY = 2
  SUTHERLAND_HODGMAN = 3

  def __str__(self) -> str:
    if self == ClippingAlgorithm.COHEN_SUTHERLAND:
      return "Cohen-Sutherland"
    elif self == ClippingAlgorithm.LIANG_BARSKY:
      return "Liang-Barsky"
    elif self == ClippingAlgorithm.SUTHERLAND_HODGMAN:
      return "Sutherland-Hodgman"
    return "Unknown"

class Clipping:
  #def __init__(self, camera: Camera):
  def __init__(self, window: tuple[float, float, float, float]):
    self.window = window
    self.xmin, self.ymin, self.xmax, self.ymax = window

  def clip(self, all_objects: list[Wireframe], algorithm: ClippingAlgorithm) -> list[Wireframe]:
    """Clip all wireframe objects using the specified algorithm."""
    clipped_objects = []
    for x in all_objects:
      obj = x.copy()
      # Clip polygon
      if isinstance(obj, PolygonObject) and algorithm == ClippingAlgorithm.SUTHERLAND_HODGMAN:
        clipped = self.sutherland_hodgman_clip(obj)
      # Clip line
      elif len(obj.points) == 2:
        p1, p2 = obj.points
        if algorithm == ClippingAlgorithm.COHEN_SUTHERLAND:
          clipped = self.cohen_sutherland_clip(p1[0], p1[2], p2[0], p2[2])
        elif algorithm == ClippingAlgorithm.LIANG_BARSKY:
          clipped = self.liang_barsky_clip(p1[0], p1[2], p2[0], p2[2])
        else:
          continue
        if clipped is not None:
          x0, y0, x1, y1 = clipped
          obj.points = [np.array([x0, p1[1], y0]), np.array([x1, p2[1], y1])]
        else:
          obj.points = []
      # Clip point
      elif len(obj.points) == 1:
        p = obj.points[0]
        if not self.point_in_window(p[0], p[2]):
          obj.points = []

      clipped_objects.append(obj)
    return clipped_objects

  def compute_out_code(self, x: float, y: float) -> int:
    code = Code.INSIDE.value
    if x < self.xmin:    # to the left of clip window
      code |= Code.LEFT.value
    elif x > self.xmax:  # to the right of clip window
      code |= Code.RIGHT.value
    if y < self.ymin:    # below the clip window
      code |= Code.BOTTOM.value
    elif y > self.ymax:  # above the clip window
      code |= Code.TOP.value
    return code

  def point_in_window(self, x: float, y: float) -> bool:
    return self.xmin <= x <= self.xmax and self.ymin <= y <= self.ymax

  def cohen_sutherland_clip(self, x0: float, y0: float, x1: float, y1: float) -> tuple[float, float, float, float] | None:
    """Cohen-Sutherland clipping algorithm for a line"""
    xmin, ymin, xmax, ymax = self.window
    out_code0 = self.compute_out_code(x0, y0)
    out_code1 = self.compute_out_code(x1, y1)
    accept = False

    while True:
      if not (out_code0 | out_code1):
        return x0, y0, x1, y1  # Both points inside
      elif out_code0 & out_code1:
        return None  # Both points outside
      else:
        out_code_out = out_code0 if out_code0 else out_code1
        if out_code_out & Code.TOP.value:
          x = x0 + (x1 - x0) * (self.ymax - y0) / (y1 - y0)
          y = self.ymax
        elif out_code_out & Code.BOTTOM.value:
          x = x0 + (x1 - x0) * (self.ymin - y0) / (y1 - y0)
          y = self.ymin
        elif out_code_out & Code.RIGHT.value:
          y = y0 + (y1 - y0) * (self.xmax - x0) / (x1 - x0)
          x = self.xmax
        elif out_code_out & Code.LEFT.value:
          y = y0 + (y1 - y0) * (self.xmin - x0) / (x1 - x0)
          x = self.xmin
        else:
          # TODO: Fix these non exhaustive checks throughout the code
          raise RuntimeError("Shouldn't reach here")

        if out_code_out == out_code0:
          x0, y0 = x, y
          out_code0 = self.compute_out_code(x0, y0)
        else:
          x1, y1 = x, y
          out_code1 = self.compute_out_code(x1, y1)

  def liang_barsky_clip(self, x0: float, y0: float, x1: float, y1: float) -> tuple[float, float, float, float] | None:
    """Liang-Barsky clipping algorithm for a line"""
    self.xmin, self.ymin, self.xmax, self.ymax = self.window
    dx = x1 - x0
    dy = y1 - y0

    p = [-dx, dx, -dy, dy]
    q = [x0 - self.xmin, self.xmax - x0, y0 - self.ymin, self.ymax - y0]

    t0, t1 = 0.0, 1.0

    u1, u2 = t0, t1
    for i in range(4):
      if p[i] == 0 or q[i] < 0:
        return None
      else:
        t = q[i] / p[i]
        if p[i] < 0: u1 = max(t0, t)
        else: u2 = min(t1, t)
    # if u1 > u2:
    #   return None

    return x0 + u1 * dx, y0 + u1 * dy, x0 + u2 * dx, y0 + u2 * dy

  def sutherland_hodgman_clip(self, polygon: PolygonObject) -> PolygonObject | None:
    """Sutherland-Hodgman polygon clipping algorithm for polygons"""
    def inside(p: np.ndarray, edge: str) -> bool:
      x, y = p[0], p[1]
      if edge == "left": return x >= self.xmin
      if edge == "right": return x <= self.xmax
      if edge == "bottom": return y >= self.ymin
      if edge == "top": return y <= self.ymax
      raise ValueError("Invalid edge")

    def compute_intersection(p1: np.ndarray, p2: np.ndarray, edge: str) -> np.ndarray:
      x1, y1 = p1[0], p1[1]
      x2, y2 = p2[0], p2[1]

      dx, dy = x2 - x1, y2 - y1
      if dx == 0: dx = 1e-10  # Prevent division by zero
      if dy == 0: dy = 1e-10
      x, y = 0, 0
      if edge == "left":
        x = self.xmin
        y = y1 + dy * (self.xmin - x1) / dx
      elif edge == "right":
        x = self.xmax
        y = y1 + dy * (self.xmax - x1) / dx
      elif edge == "bottom":
        y = self.ymin
        x = x1 + dx * (self.ymin - y1) / dy
      elif edge == "top":
        y = self.ymax
        x = x1 + dx * (self.ymax - y1) / dy
      return np.array([x, y])
    # Clip the polygon against the current edge
    clipped = []
    for edge in ["left", "right", "bottom", "top"]:
      input_list = polygon.points

      if not input_list: break

      S = input_list[-1]
      for E in input_list:
        if inside(E, edge):
          if not inside(S, edge):
            intersection = compute_intersection(S, E, edge)
            clipped.append(intersection)
          clipped.append(E)
        elif inside(S, edge):
          intersection = compute_intersection(S, E, edge)
          clipped.append(intersection)
        S = E
      clipped = [np.array(pt) for pt in clipped]
    if len(clipped) < 3: return None
    return PolygonObject(polygon.name, clipped, id=polygon.id)