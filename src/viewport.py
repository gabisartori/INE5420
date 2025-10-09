from typing import Callable

from tkinter import Canvas, Event, IntVar, ttk

from wireframe import *
from window import *
from clipping import Clipping
from my_types import WorldPoint

class Viewport:
  def __init__(
    self,
    canva: Canvas,
    log_function: Callable[[str], None],
    object_list: ttk.Treeview,
    input_file: str | None,
    output_file: str | None,
    width: int,
    height: int,
    curve_type: IntVar,
    curve_coefficient: IntVar,
    debug: bool,
    window_position: list[float],
    window_normal: list[float],
    window_focus: list[float],
    window_up: list[float],
    window_movement_speed: int,
    window_rotation_speed: int,
    window_padding: int,
    window_zoom: float,
    line_clipping_algorithm: IntVar,
    projection_type: int,
  ):
    self.canva = canva
    self.window = Window(
      width,
      height,
      window_position,
      window_normal,
      window_focus,
      window_up,
      window_movement_speed,
      window_rotation_speed,
      window_zoom,
      projection_type
    )
    self.clipper = Clipping(
      width,
      height,
      window_padding,
      line_clipping_algorithm,
    )
    self.curve_coefficient = curve_coefficient

    self.id_counter: int
    self.objects: list[Wireframe]
    self.objects = Wireframe.load_file(input_file)
    self.id_counter = len(self.objects)
    self.building_buffer: list[WorldPoint] = []
    self.building: bool = False
    self.debug: bool = debug
    self._curve_type: IntVar = curve_type

    self.log = log_function
    self.object_list: ttk.Treeview = object_list

    self.update()
    self.update_object_list()

  @property
  def curve_type(self) -> CurveType:
    return CurveType(self._curve_type.get())

  def save_objects(self, path: str):
    with open(path, "w") as f:
      for obj in self.objects:
        f.write(f"{obj}\n")

  def is_click_inside_window(self, x: int, y: int) -> bool:
    return self.window.click_in_window(x, y)

  def canva_click(self, event: Event):
    if not self.is_click_inside_window(event.x, event.y): return

    world_point = self.window.viewport_to_world(event.x, event.y)
    if self.building: self.building_buffer.append(world_point)
    else:
      self.objects.append(Wireframe(self.id_counter, "Clique", [world_point]))
      self.id_counter += 1

    self.update()

  def move_window(self, event: Event):
    self.window.position = self.window.viewport_to_world(event.x, event.y)
    self.update()

  def clear(self):
    self.objects.clear()
    self.building = False
    self.building_buffer.clear()
    self.update()
  
  def recenter(self):
    self.window.recenter()
    self.update()

  def update(self):
    # TODO: Only update the object list when something changes, not every frame
    self.update_object_list()
    self.canva.delete("all")
    all_objects = [obj.copy() for obj in self.objects]
    # Add debug objects to the list of objects to be drawn if debug mode is on
    if self.debug:
      self.build_debug_grid()
      x0, y0, x1, y1 = self.window.get_corners()
      self.canva.create_line(x0, (y1+self.window.padding)/2, x1, (y1+self.window.padding)/2, fill="blue")
      self.canva.create_line((x1+self.window.padding)/2, y0, (x1+self.window.padding)/2, y1, fill="blue")
      self.draw_viewport_border()
      self.canva.create_text(x1 - 100, y1 - 10, fill="black", font=("Arial", 10, "bold"), text=str(self.window.position))

    for object in sorted(all_objects, key=lambda obj: obj.distance(self.window.position), reverse=True):
      for window_object in self.window.project(object):
        clipped = self.clipper.clip(window_object)
        if clipped is not None: clipped.draw(self.canva)

    # Redraw the building lines if in building mode
    prev = None
    for point in self.building_buffer:
      point = self.window.world_to_viewport(point)
      clipped_point = self.clipper.clip(WindowPointObject(point))
      if clipped_point: clipped_point.draw(self.canva, 'red')
      if prev is not None:
        line = self.clipper.clip(WindowLineObject(prev, point))
        if line: line.draw(self.canva, 'red')
      prev = point

  def update_object_list(self):
    for item in self.object_list.get_children(): self.object_list.delete(item)
    for obj in self.objects: 
      self.object_list.insert(
        "",
        "end",
        values=(
          obj.name,
          ", ".join(f"({', '.join(f'{coord:.2f}' for coord in point)})" for point in obj.vertices)),
          tags=(str(obj.wireframe_id),
        )
      )

  # TODO: Optimize this function to only draw lines instead of creating world elements to be the lines
  def build_debug_grid(self):
    return
    step = 75
    min_zoom = self.window.min_zoom 

    width = self.window.width
    height = self.window.height

    max_world_width = width / min_zoom
    max_world_height = height / min_zoom
    max_range = int(max(max_world_width, max_world_height) / 2)  # /2 para ter metade pra cada lado do centro

    start = ( -max_range // step ) * step
    end = ( max_range // step + 1 ) * step

    for i in range(start, end, step):
      start_h = self.window.world_to_viewport(np.array([-max_range, i, 0]))
      end_h = self.window.world_to_viewport(np.array([max_range, i, 0]))
      self.canva.create_line(
        start_h[0], start_h[1], end_h[0], end_h[1],
        fill="lightgray"
      )

      start_v = self.window.world_to_viewport(np.array([i, -max_range, 0]))
      end_v = self.window.world_to_viewport(np.array([i, max_range, 0]))
      self.canva.create_line(
        start_v[0], start_v[1], end_v[0], end_v[1],
        fill="lightgray"
      )

    origin = self.window.world_to_viewport(np.array([0, 0, 0]))
    self.canva.create_text(origin[0] + 15, origin[1] - 10, text="(0,0)", fill="black", font=("Arial", 10, "bold"))

  def draw_viewport_border(self):
    x0, y0, x1, y1 = self.window.get_corners()
    self.canva.create_rectangle(x0, y0, x1, y1, outline="red", width=1)

  def undo(self):
    """Undoes the last action. If the SGI is in building mode, remove the last added point or exit building mode if no points are left.
    If not in building mode, then the viewport must remove the last added object.
    """
    if self.building_buffer:
      if self.building_buffer: self.building_buffer.pop()
      else: self.cancel_building()
      self.update()
    else:
      self.objects.pop()
      self.update()

  def toggle_building(self):
    self.building = not self.building
    if not self.building: self.finish_building()
  
  def toggle_debug(self):
    self.debug = not self.debug
    self.update()

  def cancel_building(self):
    self.building_buffer.clear()
    self.building = False
    self.update()

  def finish_polygon(self):
    if self.building:
      if len(self.building_buffer) < 3:
        raise Exception("Polígono precisa de ao menos 3 pontos.")
      else:
        self.objects.append(Wireframe(
          self.id_counter,
          "Polígono",
          vertices=self.building_buffer.copy(),
          edges=[(i, (i+1) % len(self.building_buffer)) for i in range(len(self.building_buffer))],
          faces=[([i for i in range(len(self.building_buffer))], None)]
        ))
        self.id_counter += 1
        self.cancel_building()
    # Open polygon insertion window
    else: return

    self.update()

  def add_polygon(
    self,
    points: list[WorldPoint],
    name: str="Polygon",
    line_color: str="#000000",
    fill_color: str="#ffffff",
    thickness: int=1
  ):
    if len(points) < 3:
      raise Exception("Polígono precisa de ao menos 3 pontos.")
    self.objects.append(Wireframe(
      self.id_counter,
      name,
      vertices=points,
      edges=[(i, (i+1) % len(points)) for i in range(len(points))],
      faces=[([i], fill_color) for i in range(len(points))]
    ))
    
    self.id_counter += 1
    self.update()

  def finish_building(self):
    """Adds the stored points to the viewport
    If a single point is stored, add a point object.
    If multiple points are stored, add line segments between each pair of consecutive points.
    """
    if len(self.building_buffer) == 1:
      self.objects.append(Wireframe(
        self.id_counter,
        "Clique",
        vertices=[self.building_buffer[0]]
      ))
      self.id_counter += 1

    for i in range(len(self.building_buffer) - 1):
      start, end = self.building_buffer[i:i+2]
      self.objects.append(Wireframe(
        self.id_counter,
        "Linha",
        vertices=[start, end],
        edges=[(0, 1)],
      ))
      self.id_counter += 1

    # Clear buffer and reset building state
    self.cancel_building()

  def add_curve(
    self,
    control_points: list[WorldPoint],
    name: str="Curve",
    line_color: str="#000000",
  ):
    if len(control_points) < 4:
      raise Exception("Curva precisa de ao menos 4 pontos de controle.")

    new_curve = Wireframe(
      self.id_counter,
      name,
      vertices=control_points,
      curves=[Curve(self.curve_type, list(range(len(control_points))), self.curve_coefficient.get())]
    )
    self.objects.append(new_curve)
    self.id_counter += 1
    self.update()

  def finish_curve(self):
    if len(self.building_buffer) < 4: 
      raise Exception("Erro: Pelo menos quatro pontos são necessários para formar uma curva de Bézier cúbica.")
    self.objects.append(Wireframe(
      self.id_counter,
      "Curva",
      vertices=self.building_buffer.copy(),
      curves=[
        Curve(self.curve_type, list(range(len(self.building_buffer))), self.curve_coefficient.get())
      ]
    ))
    self.id_counter += 1
    self.cancel_building()
