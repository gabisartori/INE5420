from tkinter import IntVar

from enum import Enum
from wireframe import *

from logger import logging

class Code(Enum):
  INSIDE  = 0b0000
  LEFT    = 0b0001
  RIGHT   = 0b0010
  BOTTOM  = 0b0100
  TOP     = 0b1000

class ClippingAlgorithm(Enum):
  COHEN_SUTHERLAND = 0
  LIANG_BARSKY = 1

  def __str__(self) -> str:
    if self == ClippingAlgorithm.COHEN_SUTHERLAND:
      return "Cohen-Sutherland"
    elif self == ClippingAlgorithm.LIANG_BARSKY:
      return "Liang-Barsky"
    return "Unknown"

class Clipping:
  """This class implements various 2D clipping algorithms.
  It holds the clipping window defined by (xmin, ymin) and (xmax, ymax).
  Tipically these values would just match the viewport size. But since we'd like to prove that the clipping is actually working, we add a padding value to create a smaller clipping window inside the viewport.

  3D objects can be projected to the 2D clipping window using orthographic or perspective projection. To then be clipped by this class.

  Implemented algorithms:
  - Point clipping by checking if the point lies within the clipping window
  - Line clipping Cohen-Sutherland
  - Line clipping Liang-Barsky
  - Polygon clipping Sutherland-Hodgman
  - Cubic Bezier curve clipping by approximating it with line segments and clipping each segment
  """

  def __init__(self, width: int, height: int, padding: int, line_clipping_algorithm: IntVar):
    self._line_clipping_algorithm: IntVar = line_clipping_algorithm
    self.xmin: int = padding
    self.ymin: int = padding
    self.xmax: int = width - padding
    self.ymax: int = height - padding

  @property
  def line_clipping_algorithm(self) -> ClippingAlgorithm:
    return ClippingAlgorithm(self._line_clipping_algorithm.get())

  def clip(self, object: WindowObject) -> WindowObject | None:
    """Clips an WindowObject, altering its points accordingly and returning it. If the object is completely outside the clipping window, returns None.
    
    "Line" is the only type of object that can be clipped by more than one algorithm. So the algorithm parameter is used to select which one to use for lines. Curves will also be affected, since they're approximated with lines for clipping.
    """
    match object:
      case WindowPointObject():
        if self.point_in_window(object.p.x, object.p.y): return object
        else: return None

      case WindowLineObject():
        p1, p2 = object.start, object.end
        if self.line_clipping_algorithm == ClippingAlgorithm.COHEN_SUTHERLAND: clipped = self.cohen_sutherland_clip(p1.x, p1.y, p2.x, p2.y)
        elif self.line_clipping_algorithm == ClippingAlgorithm.LIANG_BARSKY: clipped = self.liang_barsky_clip(p1.x, p1.y, p2.x, p2.y)
        else: return None

        if clipped is not None:
          x0, y0, x1, y1 = clipped
          object.start = WindowPoint(x0, y0)
          object.end = WindowPoint(x1, y1)
          return object

      case WindowPolygonObject():
        new_points = self.sutherland_hodgman_clip(object.points)
        if new_points is not None and len(new_points) >= 3:
          object.points = new_points
          return object
        else: return None

      case _:
        logging.error(f"Unknown object type: {type(object)}")
        return None

  def compute_out_code(self, x: float, y: float) -> int:
    """Used in the Cohen-Sutherland algorithm to compute the outcode of a point.
    
    Each point will be represented by a 4-bit code, each bit representing one of the regions outside the clipping window. From most to least significant bit:
    1st bit: Top
    2nd bit: Bottom
    3rd bit: Right
    4th bit: Left

    If all bits are 0, the point is inside the clipping window.
    """
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
    return self.compute_out_code(x, y) == Code.INSIDE.value

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

  def sutherland_hodgman_clip(self, current_points: list[WindowPoint]) -> list[WindowPoint] | None:
    """Sutherland-Hodgman polygon clipping algorithm for polygons"""
    new_points = []
    # Left clipping
    for i in range(0, len(current_points)+1):
      prev = current_points[i - 1]
      curr = current_points[i % len(current_points)]

      # Edge completely to the left, ignore it
      if prev.x < self.xmin and curr.x < self.xmin:
        pass
      # Edge completely to the right, add it to the output
      elif prev.x >= self.xmin and curr.x >= self.xmin:
        new_points.append(prev)
      # Edge going out to the left, clip it
      elif prev.x >= self.xmin and curr.x < self.xmin:
        x = self.xmin
        y = prev.y + (curr.y - prev.y) * (self.xmin - prev.x) / (curr.x - prev.x)
        new_points.append(prev)
        new_points.append(WindowPoint(x, y))
      # Edge coming in from the left, clip it and add the current point
      elif prev.x < self.xmin and curr.x >= self.xmin:
        x = self.xmin
        y = prev.y + (curr.y - prev.y) * (self.xmin - prev.x) / (curr.x - prev.x)
        new_points.append(WindowPoint(x, y))
        new_points.append(curr)

    if len(new_points) == 0: return None
    elif len(new_points) < 3:
      logging.warning(f"This point should not be reachable. {new_points=}")
      return None
    current_points = new_points.copy()
    new_points = []

    # Top clipping
    for i in range(0, len(current_points)+1):
      prev = current_points[i - 1]
      curr = current_points[i % len(current_points)]

      # Edge completely above, ignore it
      if prev.y > self.ymax and curr.y > self.ymax:
        pass
      # Edge completely below, add it to the output
      elif prev.y <= self.ymax and curr.y <= self.ymax:
        new_points.append(prev)
      # Edge going out above, clip it
      elif prev.y <= self.ymax and curr.y > self.ymax:
        y = self.ymax
        x = prev.x + (curr.x - prev.x) * (self.ymax - prev.y) / (curr.y - prev.y)
        new_points.append(prev)
        new_points.append(WindowPoint(x, y))
      # Edge coming in from above, clip it and add the current point
      elif prev.y > self.ymax and curr.y <= self.ymax:
        y = self.ymax
        x = prev.x + (curr.x - prev.x) * (self.ymax - prev.y) / (curr.y - prev.y)
        new_points.append(WindowPoint(x, y))
        new_points.append(curr)
    if len(new_points) == 0: return None
    elif len(new_points) < 3:
      logging.warning(f"This point should not be reachable. {new_points=}")
      return None
    current_points = new_points.copy()
    new_points = []

    # Right clipping
    for i in range(0, len(current_points)+1):
      prev = current_points[i - 1]
      curr = current_points[i % len(current_points)]

      # Edge completely to the right, ignore it
      if prev.x > self.xmax and curr.x > self.xmax:
        pass
      # Edge completely to the left, add it to the output
      elif prev.x <= self.xmax and curr.x <= self.xmax:
        new_points.append(prev)
      # Edge going out to the right, clip it
      elif prev.x <= self.xmax and curr.x > self.xmax:
        x = self.xmax
        y = prev.y + (curr.y - prev.y) * (self.xmax - prev.x) / (curr.x - prev.x)
        new_points.append(prev)
        new_points.append(WindowPoint(x, y))
      # Edge coming in from the right, clip it and add the current point
      elif prev.x > self.xmax and curr.x <= self.xmax:
        x = self.xmax
        y = prev.y + (curr.y - prev.y) * (self.xmax - prev.x) / (curr.x - prev.x)
        new_points.append(WindowPoint(x, y))
        new_points.append(curr)
    if len(new_points) == 0: return None
    elif len(new_points) < 3:
      logging.warning(f"This point should not be reachable. {new_points=}")
      return None
    current_points = new_points.copy()
    new_points = []

    # Bottom clipping
    for i in range(0, len(current_points)+1):
      prev = current_points[i - 1]
      curr = current_points[i % len(current_points)]

      # Edge completely below, ignore it
      if prev.y < self.ymin and curr.y < self.ymin:
        pass
      # Edge completely above, add it to the output
      elif prev.y >= self.ymin and curr.y >= self.ymin:
        new_points.append(prev)
      # Edge going out below, clip it
      elif prev.y >= self.ymin and curr.y < self.ymin:
        y = self.ymin
        x = prev.x + (curr.x - prev.x) * (self.ymin - prev.y) / (curr.y - prev.y)
        new_points.append(prev)
        new_points.append(WindowPoint(x, y))
      # Edge coming in from below, clip it and add the current point
      elif prev.y < self.ymin and curr.y >= self.ymin:
        y = self.ymin
        x = prev.x + (curr.x - prev.x) * (self.ymin - prev.y) / (curr.y - prev.y)
        new_points.append(WindowPoint(x, y))
        new_points.append(curr)
    if len(new_points) == 0: return None
    elif len(new_points) < 3:
      logging.warning(f"This point should note be reachable. {new_points=}")
      return None

    return new_points if len(new_points) >= 3 else None
