from tkinter import Canvas, Event, IntVar, ttk

from enum import Enum

from wireframe import *
from window import *
from clipping import Clipping, ClippingAlgorithm
from components.my_types import Point

class Viewport:
  def __init__(
      self,
      canva: Canvas,
      clipping_algorithm: IntVar,
      curve_type: IntVar,
      log_function,
      object_list: ttk.Treeview,
      debug: bool=False,
      input_file: str | None = None
    ):
    self.canva = canva
    self.window = Window()
    self.clipper = Clipping(clipping_algorithm, self.window.padding, self.window.padding, self.window.width-self.window.padding, self.window.height-self.window.padding)

    self.id_counter: int
    self.objects: list[Wireframe]
    self.id_counter, self.objects = self.load_objects(input_file, curve_type=0)
    self.building_buffer: list[Point] = []
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

  def load_objects(self, filepath: str | None, curve_type: int=0) -> tuple[int, list[Wireframe]]:
    if not filepath: return 0, []
    try:
      with open(filepath, "r") as file:
        lines = [line for line in file if line.strip() and not line.startswith("#")]
        self.placed_objects_counter = len(lines)
        objects: list[Wireframe] = []
        current_name = ""
        current_points: list[Point] = []

        for line in lines:
          header, *args = line.split()
          match header:
            case "o":
              current_name = args[0]
              current_points = []
            case "v":
              vertex = np.array([float(coord) for coord in args])
              current_points.append(vertex)
            case "p":
              if len(current_points) == 1:
                objects.append(PointObject(current_name, current_points[0], id=len(objects), thickness=int(args[0]) if args[0].isnumeric() else 2))
              current_points = []
            case "l":
              if len(current_points) == 2:
                objects.append(LineObject(current_name, current_points[0], current_points[1], id=len(objects)))
              else:
                objects.append(PolygonObject(current_name, current_points.copy(), id=len(objects)))
              current_points = []
            case "c":
              indices = [int(i) - 1 for i in args]
              control_points = [current_points[i] for i in indices if 0 <= i < len(current_points)]
              if len(control_points) >= 2:
                # TODO: get the chosen steps number from idk where
                new_curve = CurveObject_2D(current_name, control_points, steps=100, id=len(objects))
                if curve_type == 1:
                  new_curve.generate_b_spline_points()
                else:
                  new_curve.generate_bezier_points()
                objects.append(new_curve)
              else:
                raise Exception(f"Aviso: Curva '{current_name}' ignorada por ter menos de 2 pontos válidos.")
              current_points = []

            case _:
              raise Exception(f"Aviso: Cabeçalho desconhecido '{header}' ignorado.")

      return len(objects), objects
    except FileNotFoundError:
      self.log(f"Arquivo {filepath} não encontrado.")
      return 0, []
    except Exception as e:
      self.log(f"Erro: Erro ao carregar objetos: {e}")
      return 0, []

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
      self.objects.append(PointObject("Clique", world_point, id=self.id_counter))
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
      # TODO: I still feel like these lines are not perfectly centered ffs
      self.canva.create_line(x0, (y1+self.window.padding)/2, x1, (y1+self.window.padding)/2, fill="blue")
      self.canva.create_line((x1+self.window.padding)/2, y0, (x1+self.window.padding)/2, y1, fill="blue")
      self.draw_viewport_border()

    # Project all objects to the viewport and clip them
    for obj in all_objects:
      obj.points = [np.array(self.window.world_to_viewport(point)) for point in obj.points]
    all_objects = self.clipper.clip_all(all_objects)
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
          self.canva.create_oval(p[0]-obj.thickness, p[1]-obj.thickness, p[0]+obj.thickness, p[1]+obj.thickness, fill=obj.fill_color, outline=obj.line_color)

        case _: 
          # self.log(f"Erro: Tipo de objeto desconhecido: {type(obj)}")
          continue  # Unsupported object type

    # Redraw the building lines if in building mode
    # TODO: Clip these lines too
    prev = None
    for point in self.building_buffer:
      point = self.window.world_to_viewport(point)
      self.canva.create_oval(point[0] - 2, point[1] - 2, point[0] + 2, point[1] + 2, fill="red")
      if prev is not None: self.canva.create_line(prev[0], prev[1], point[0], point[1], fill="red")
      prev = point

  def update_object_list(self):
    for item in self.object_list.get_children(): self.object_list.delete(item)
    for obj in self.objects: 
      self.object_list.insert(
        "",
        "end",
        values=(
          obj.name,
          ", ".join(f"({', '.join(f'{coord:.2f}' for coord in point)})" for point in obj.points)),
          tags=(str(obj.id),
        )
      )

  # TODO: For some goddamn reason rowspan and columnspan are being ignored by most components
  # Must make it so that the components respect the grid layout
  def build_debug_grid(self):
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
      self.undo()

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
        self.objects.append(PolygonObject("Polígono", self.building_buffer.copy(), id=self.id_counter))
        self.id_counter += 1
        self.cancel_building()
    # Open polygon insertion window
    else: return

    self.update()

  def add_polygon(
    self,
    points: list[Point],
    name: str="Polygon",
    line_color: str="#000000",
    fill_color: str="#ffffff",
    thickness: int=1
  ):
    if len(points) < 3:
      raise Exception("Polígono precisa de ao menos 3 pontos.")
    self.objects.append(PolygonObject(name, points, line_color=line_color, fill_color=fill_color, thickness=thickness, id=self.id_counter))
    self.id_counter += 1
    self.update()

  def finish_building(self):
    """Adds the stored points to the viewport
    If a single point is stored, add a point object.
    If multiple points are stored, add line segments between each pair of consecutive points.
    """
    if len(self.building_buffer) == 1:
      self.objects.append(PointObject("Clique", self.building_buffer[0], id=self.id_counter))
      self.id_counter += 1

    for i in range(len(self.building_buffer) - 1):
      start, end = self.building_buffer[i:i+2]
      self.objects.append(LineObject("Linha", start, end, id=self.id_counter))
      self.id_counter += 1

    # Clear buffer and reset building state
    self.cancel_building()

  def add_curve(
    self,
    control_points: list[Point],
    name: str="Curve",
    line_color: str="#000000",
  ):
    if len(control_points) < 4:
      raise Exception("Curva precisa de ao menos 4 pontos de controle.")
    new_curve = CurveObject_2D(name, control_points, steps=100, line_color=line_color, thickness=1, id=self.id_counter, curve_type=self.curve_type)
    self.objects.append(new_curve)
    self.id_counter += 1
    self.update()

  def finish_curve(self):
    if len(self.building_buffer) < 4: 
      raise Exception("Erro: Pelo menos quatro pontos são necessários para formar uma curva de Bézier cúbica.")
    self.objects.append(CurveObject_2D("Curva", self.building_buffer.copy(), steps=100, id=self.id_counter, curve_type=self.curve_type))
    self.id_counter += 1
    self.cancel_building()

