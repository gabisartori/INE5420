import sys
sys.path.append("..")

from enum import Enum
import numpy as np
from wireframe import *

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
  def __init__(self, xmin, ymin, xmax, ymax):
    self.xmin = xmin
    self.ymin = ymin
    self.xmax = xmax
    self.ymax = ymax

  def clip(self, all_objects: list[Wireframe], algorithm: ClippingAlgorithm) -> list[Wireframe]:
    """Clip all wireframe objects using the specified algorithm."""
    
    clipped_objects = []
    for x in all_objects:
      obj = x.copy()
      match obj:
        case CurveObject_2D():
          pass
          obj.points = self.clip_curve(obj, algorithm) or []

        case PolygonObject():
          obj.points = self.sutherland_hodgman_clip(obj) or []
        
        case LineObject():
          p1, p2 = obj.points
          if algorithm == ClippingAlgorithm.COHEN_SUTHERLAND:
            clipped = self.cohen_sutherland_clip(p1[0], p1[1], p2[0], p2[1])
          elif algorithm == ClippingAlgorithm.LIANG_BARSKY:
            clipped = self.liang_barsky_clip(p1[0], p1[1], p2[0], p2[1])
          else:
            continue
          if clipped is not None:
            x0, y0, x1, y1 = clipped
            obj.points = [np.array([x0, y0]), np.array([x1, y1])]
          else:
            obj.points = []
        
        case PointObject():
          p = obj.points[0]
          if not self.point_in_window(p[0], p[1]):
            obj.points = []
        
        case _:
          continue
        
      clipped_objects.append(obj) if obj.points else None
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
    out_code0 = self.compute_out_code(x0, y0)
    out_code1 = self.compute_out_code(x1, y1)
    
    accept = False
    while not accept:
      if not (out_code0 | out_code1):
        accept = True
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
    dx = x1 - x0
    dy = y1 - y0

    p = [-dx, dx, -dy, dy]
    q = [x0 - self.xmin, self.xmax - x0, y0 - self.ymin, self.ymax - y0]

    t_enter = 0.0
    t_exit = 1.0

    for i in range(4):
      if p[i] == 0:  
        if q[i] < 0:
          return None  
      else:
        t = q[i] / p[i]
        if p[i] < 0:
          if t > t_enter:
            t_enter = t
        else:
          if t < t_exit:
            t_exit = t

    if t_enter > t_exit: return None 

    x0_clip = x0 + t_enter * dx
    y0_clip = y0 + t_enter * dy
    x1_clip = x0 + t_exit * dx
    y1_clip = y0 + t_exit * dy
    return x0_clip, y0_clip, x1_clip, y1_clip

  def sutherland_hodgman_clip(self, polygon: PolygonObject) -> list[np.ndarray] | None:
    """Sutherland-Hodgman polygon clipping algorithm for polygons"""
    new_points = []
    current_points = polygon.points.copy()
    # Left clipping
    for i in range(0, len(current_points)+1):
      prev = current_points[i - 1]
      curr = current_points[i % len(current_points)]

      # Edge completely to the left, ignore it
      if prev[0] < self.xmin and curr[0] < self.xmin:
        pass
      # Edge completely to the right, add it to the output
      elif prev[0] >= self.xmin and curr[0] >= self.xmin:
        new_points.append(prev)
      # Edge going out to the left, clip it
      elif prev[0] >= self.xmin and curr[0] < self.xmin:
        x = self.xmin
        y = prev[1] + (curr[1] - prev[1]) * (self.xmin - prev[0]) / (curr[0] - prev[0])
        new_points.append(prev)
        new_points.append(np.array([x, y]))
      # Edge coming in from the left, clip it and add the current point
      elif prev[0] < self.xmin and curr[0] >= self.xmin:
        x = self.xmin
        y = prev[1] + (curr[1] - prev[1]) * (self.xmin - prev[0]) / (curr[0] - prev[0])
        new_points.append(np.array([x, y]))
        new_points.append(curr)

    if len(new_points) == 0: return None
    elif len(new_points) < 3:
      print("How tf'd u get here")
      return None
    current_points = new_points.copy()
    new_points = []

    # Top clipping
    for i in range(0, len(current_points)+1):
      prev = current_points[i - 1]
      curr = current_points[i % len(current_points)]

      # Edge completely above, ignore it
      if prev[1] > self.ymax and curr[1] > self.ymax:
        pass
      # Edge completely below, add it to the output
      elif prev[1] <= self.ymax and curr[1] <= self.ymax:
        new_points.append(prev)
      # Edge going out above, clip it
      elif prev[1] <= self.ymax and curr[1] > self.ymax:
        y = self.ymax
        x = prev[0] + (curr[0] - prev[0]) * (self.ymax - prev[1]) / (curr[1] - prev[1])
        new_points.append(prev)
        new_points.append(np.array([x, y]))
      # Edge coming in from above, clip it and add the current point
      elif prev[1] > self.ymax and curr[1] <= self.ymax:
        y = self.ymax
        x = prev[0] + (curr[0] - prev[0]) * (self.ymax - prev[1]) / (curr[1] - prev[1])
        new_points.append(np.array([x, y]))
        new_points.append(curr)
    if len(new_points) == 0: return None
    elif len(new_points) < 3:
      print("How tf'd u get here")
      return None    
    current_points = new_points.copy()
    new_points = []

    # Right clipping
    for i in range(0, len(current_points)+1):
      prev = current_points[i - 1]
      curr = current_points[i % len(current_points)]

      # Edge completely to the right, ignore it
      if prev[0] > self.xmax and curr[0] > self.xmax:
        pass
      # Edge completely to the left, add it to the output
      elif prev[0] <= self.xmax and curr[0] <= self.xmax:
        new_points.append(prev)
      # Edge going out to the right, clip it
      elif prev[0] <= self.xmax and curr[0] > self.xmax:
        x = self.xmax
        y = prev[1] + (curr[1] - prev[1]) * (self.xmax - prev[0]) / (curr[0] - prev[0])
        new_points.append(prev)
        new_points.append(np.array([x, y]))
      # Edge coming in from the right, clip it and add the current point
      elif prev[0] > self.xmax and curr[0] <= self.xmax:
        x = self.xmax
        y = prev[1] + (curr[1] - prev[1]) * (self.xmax - prev[0]) / (curr[0] - prev[0])
        new_points.append(np.array([x, y]))
        new_points.append(curr)
    if len(new_points) == 0: return None
    elif len(new_points) < 3:
      print("How tf'd u get here")
      return None
    current_points = new_points.copy()
    new_points = []

    # Bottom clipping
    for i in range(0, len(current_points)+1):
      prev = current_points[i - 1]
      curr = current_points[i % len(current_points)]

      # Edge completely below, ignore it
      if prev[1] < self.ymin and curr[1] < self.ymin:
        pass
      # Edge completely above, add it to the output
      elif prev[1] >= self.ymin and curr[1] >= self.ymin:
        new_points.append(prev)
      # Edge going out below, clip it
      elif prev[1] >= self.ymin and curr[1] < self.ymin:
        y = self.ymin
        x = prev[0] + (curr[0] - prev[0]) * (self.ymin - prev[1]) / (curr[1] - prev[1])
        new_points.append(prev)
        new_points.append(np.array([x, y]))
      # Edge coming in from below, clip it and add the current point
      elif prev[1] < self.ymin and curr[1] >= self.ymin:
        y = self.ymin
        x = prev[0] + (curr[0] - prev[0]) * (self.ymin - prev[1]) / (curr[1] - prev[1])
        new_points.append(np.array([x, y]))
        new_points.append(curr)
    if len(new_points) == 0: return None
    elif len(new_points) < 3:
      print("How tf'd u get here")
      return None
    return new_points

  def clip_curve(self, curve: CurveObject_2D, algorithm: str) -> list[np.ndarray] | None:
    """Clip a cubic Bezier curve by approximating it with line segments and clipping each segment."""
    clipped_points = []
    
    if len(curve.points) < 2: 
      return None
    
    if algorithm == ClippingAlgorithm.COHEN_SUTHERLAND:
      clip_func = self.cohen_sutherland_clip
    elif algorithm == ClippingAlgorithm.LIANG_BARSKY:
      clip_func = self.liang_barsky_clip
    else:
      return None
    
    for i in range(1, len(curve.points)):
      p1 = curve.points[i - 1]
      p2 = curve.points[i]
      clipped_segment = clip_func(p1[0], p1[1], p2[0], p2[1])
      
      if clipped_segment is not None:
        x0, y0, x1, y1 = clipped_segment
        point0 = np.array([int(x0), int(y0)])
        point1 = np.array([int(x1), int(y1)])
        
        if len(clipped_points) == 0 or not np.array_equal(clipped_points[-1], point0):
          clipped_points.append(point0)
        clipped_points.append(point1)
      # else:
      #   print(f"Segment from {p1} to {p2} is not visible.")
    return clipped_points if clipped_points else None


