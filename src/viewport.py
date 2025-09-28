from tkinter import Canvas

from wireframe import *
from window import *
from clipping import Clipping, ClippingAlgorithm
from components.my_types import Point

class Viewport:
  def __init__(self, canva: Canvas, building_buffer: list[Point]):
    self.canva = canva
    self.window = Window()

    self.id_counter: int
    self.objects: list[Wireframe]
    self.id_counter, self.objects = self.load_objects()

    self.building_buffer: list[Point] = building_buffer


  def is_click_inside_window(self, x: int, y: int) -> bool:
    return self.window.point_in_window(x, y)

  def clear(self):
    self.objects.clear()
    self.update()
  
  def recenter(self):
    self.window.recenter()
    self.update()
  
  def update(self, building_buffer: list[Point] | None = None):
    self.canva.delete("all")
    all_objects = [obj.copy() for obj in self.objects]

    # Add debug objects to the list of objects to be drawn if debug mode is on
    if self.debug:
      all_objects += [obj.copy() for obj in self.debug_objects]
      self.build_debug_grid()
      x0, y0, x1, y1 = self.window.get_corners()
      # TODO: I still feel like these lines are not perfectly centered ffs
      self.canva.create_line(x0, (y1+self.window.padding)/2, x1, (y1+self.window.padding)/2, fill="blue")
      self.canva.create_line((x1+self.window.padding)/2, y0, (x1+self.window.padding)/2, y1, fill="blue")
      self.draw_viewport_border()

    # Project all objects to the viewport and clip them
    for obj in all_objects:
      obj.points = [np.array(self.window.world_to_viewport(point)) for point in obj.points]
    all_objects = self.clipping.clip_all(all_objects, ClippingAlgorithm(self.clipping_algorithm.get()))

    # Draw all objects
    for obj in all_objects:
      match obj:
        case CurveObject_2D():
          if len(obj.points) < 2: 
            continue
          for i in range(1, len(obj.points)):
            p0 = obj.points[i - 1]
            p1 = obj.points[i]

            if p0 is None or p1 is None:
              continue

            dist = np.linalg.norm(p1 - p0)
            if dist > 100:
              continue  # Não conectar segmentos distantes

            self.canva.create_line(p0[0], p0[1], p1[0], p1[1], fill=obj.line_color, width=obj.thickness)

        case PolygonObject():
          if len(obj.points) < 3: continue
          for i in range(len(obj.points)):
            start = obj.points[i]
            end = obj.points[(i + 1) % len(obj.points)]
            self.canva.create_line(start[0], start[1], end[0], end[1], fill=obj.line_color, width=obj.thickness)
          if obj.fill_color:
            self.canva.create_polygon(*((p[0], p[1]) for p in obj.points), fill=obj.fill_color, outline=obj.line_color, width=obj.thickness)

        case LineObject():
          if len(obj.points) != 2: continue
          self.canva.create_line(obj.points[0][0], obj.points[0][1], obj.points[1][0], obj.points[1][1], fill=obj.line_color, width=obj.thickness)

        case PointObject():
          p = obj.points[0] if obj.points else None
          if p is None: continue
          if not self.is_click_inside_viewport(p[0], p[1]): continue
          self.canva.create_oval(p[0]-obj.thickness, p[1]-obj.thickness, p[0]+obj.thickness, p[1]+obj.thickness, fill=obj.fill_color, outline=obj.line_color)

        case _: 
          self.log(f"Erro: Tipo de objeto desconhecido: {type(obj)}")
          continue  # Unsupported object type

    # Refresh the object list
    self.ui_object_list.delete(*self.ui_object_list.get_children())
    for obj in self.objects:
      self.add_object_to_table(obj)

    # Redraw the building lines if in building mode
    prev = None
    for point in self.build:
      point = self.window.world_to_viewport(point)
      self.canva.create_oval(point[0] - 2, point[1] - 2, point[0] + 2, point[1] + 2, fill="red")
      if prev is not None: self.canva.create_line(prev[0], prev[1], point[0], point[1], fill="red")
      prev = point
