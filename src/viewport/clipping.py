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
      obj = x
      # Clip polygon
      if isinstance(obj, PolygonObject):
        clipped = self.sutherland_hodgman_clip(obj)
        print('clipping sutherland_hodgman', obj.points, '->', clipped.points if clipped else None)
        
      # Clip line
      elif len(obj.points) == 2:
        p1, p2 = obj.points
        if algorithm == ClippingAlgorithm.COHEN_SUTHERLAND:
          clipped = self.cohen_sutherland_clip(p1[0], p1[1], p2[0], p2[1])
        elif algorithm == ClippingAlgorithm.LIANG_BARSKY:
          clipped = self.liang_barsky_clip(p1[0], p1[1], p2[0], p2[1])
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
        if not self.point_in_window(p[0], p[1]):
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
    out_code0 = self.compute_out_code(x0, y0)
    out_code1 = self.compute_out_code(x1, y1)
    
    accept = False
    # print('clipping cohen_sutherland', x0, y0, x1, y1, out_code0, out_code1)
    while not accept:
      if not (out_code0 | out_code1):
        # print('Points: ', (x0, y0), (x1, y1))
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
          print("Error: Shouldn't reach here")
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

    if t_enter > t_exit:
        return None 

    x1_clip = x1 + t_enter * dx
    y1_clip = y1 + t_enter * dy
    x2_clip = x1 + t_exit * dx
    y2_clip = y1 + t_exit * dy

    return x1_clip, y1_clip, x2_clip, y2_clip
  
  def sutherland_hodgman_clip(self, polygon: PolygonObject) -> PolygonObject | None:
    """Sutherland-Hodgman polygon clipping algorithm for polygons"""
    # Para cada lado da janela:
    # Para cada aresta (v1, v2) do polígono:
    #     Se v1 e v2 estão dentro:
    #         adicionar v2 ao novo polígono
    #     Se v1 está fora e v2 está dentro:
    #         adicionar interseção e v2
    #     Se v1 está dentro e v2 está fora:
    #         adicionar interseção
    #     Se ambos estão fora:
    #         não faz nada
    pass
    
    # def is_inside(p: Point, edge: str) -> bool:
    #   x, y = p[0], p[1]
    #   if edge == 'LEFT':
    #     return x >= self.xmin
    #   elif edge == 'RIGHT':
    #     return x <= self.xmax
    #   elif edge == 'BOTTOM':
    #     return y >= self.ymin
    #   elif edge == 'TOP':
    #     return y <= self.ymax
    #   return False
    
    
    # for window_edge in ['LEFT', 'RIGHT', 'BOTTOM', 'TOP']:
    #   input_list = polygon.points
    #   if not input_list:
    #     return None
    #   output_list = []
      
    #   for polygon_edge in range(len(input_list)):
        