from typing import Callable

from tkinter import Canvas, Event, IntVar, ttk
import numpy as np
import random

from wireframe import *
from window import *
from clipping import Clipping
from my_types import WorldPoint

class Viewport:
  '''Gerencia a janela de visualização de objetos 3D, incluindo a renderização, manipulação e interação com o usuário.

  Esta classe mantém uma lista de objetos criados e uma lista de pontos de criação temporários.

  Esses objetos são então projetados por meio de uma instância da classe Window, que lida com a projeção 3D para 2D. E então, os objetos projetados são recortados usando uma instância da classe Clipping, que aplica algoritmos de recorte de linha e polígonos antes de desenhá-los na tela.
  '''
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
    surface_type: IntVar,
    surface_degree: tuple[int, int],
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
    self._surface_type: IntVar = surface_type
    self.surface_degree: tuple[int, int] = surface_degree

    self.log = log_function
    self.object_list: ttk.Treeview = object_list

    self.update()
    self.update_object_list()

  @property
  def curve_type(self) -> CurveType:
    return CurveType(self._curve_type.get())
  
  @property
  def surface_type(self) -> SurfaceType:
    return SurfaceType(self._surface_type.get())

  def save_objects(self, path: str):
    with open(path, "w") as f:
      for obj in self.objects:
        f.write(f"{obj}\n")

  def is_click_inside_window(self, x: int, y: int) -> bool:
    return self.window.click_in_window(x, y)

  def canva_click(self, event: Event):
    '''Registra o clique do usuário na tela.

    Caso o usuário esteja em modo de construção, adiciona o ponto clicado ao buffer de construção.
    Caso contrário, cria um novo objeto ponto na posição clicada.
    '''
    if not self.is_click_inside_window(event.x, event.y): return

    world_point = self.window.viewport_to_world(event.x, event.y)
    if self.building: self.building_buffer.append(world_point)
    else:
      self.objects.append(Wireframe(self.id_counter, "Clique", [world_point]))
      self.id_counter += 1

    self.update()
    
  def remove_object(self, target: Wireframe):
    self.objects = [obj for obj in self.objects if obj.wireframe_id != target.wireframe_id] 
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
    self.update_object_list()
    self.canva.delete("all")
    all_objects = [obj.copy() for obj in self.objects]
    # Se o modo debug estiver ativado, desenha elementos auxiliares na tela, como a grade e o centro da tela
    if self.debug:
      self.build_debug_grid()
      x0, y0, x1, y1 = self.window.get_corners()
      self.canva.create_line(x0, (y1+self.window.padding)/2, x1, (y1+self.window.padding)/2, fill="blue")
      self.canva.create_line((x1+self.window.padding)/2, y0, (x1+self.window.padding)/2, y1, fill="blue")
      self.draw_viewport_border()
      self.canva.create_text(x1 - 100, y1 - 10, fill="black", font=("Arial", 10, "bold"), text=str(self.window.position))

    # Ordena os objetos por distância da janela antes de desenhá-los
    # Dessa forma, objetos mais distantes são desenhados primeiro e, então, cobertos por objetos mais próximos
    for object in sorted(all_objects, key=lambda obj: obj.distance(self.window.position), reverse=True):
      # Projeta os vértices do objeto na janela de visualização
      object.projected_vertices = self.window.project(object.vertices)
      for window_object in object.window_objects(self.curve_coefficient.get(), self.surface_degree):
        # Recorta objetos cujas posições na janela estejam além dos limites da tela de exibição.
        clipped = self.clipper.clip(window_object)
        if clipped is not None: clipped.draw(self.canva)

    # Aplica o mesmo processo de projeção e recorte para os pontos que estão na lista de construção
    # A única diferença é a construção manual das linhas entre os pontos
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
        self.log("Polígono precisa de ao menos 3 pontos.")
        return
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
    thickness: int=1
  ):
    if len(control_points) < 4:
      raise Exception("Curva precisa de ao menos 4 pontos de controle.")

    new_curve = Wireframe(
      self.id_counter,
      name,
      vertices=control_points,
      curves=[Curve(self.curve_type, list(range(len(control_points))), degree=min(4, len(control_points)))],
    )
    self.objects.append(new_curve)
    self.id_counter += 1
    self.update()

  def finish_curve(self):
    if len(self.building_buffer) < 4: 
      raise Exception("Erro: Pelo menos quatro pontos são necessários para formar uma curva de Bézier.")
    elif len(self.building_buffer) == 2:
      self.log("Apenas dois pontos foram inseridos. Adicionando uma linha ao invés de uma curva.")
      start, end = self.building_buffer
      self.objects.append(Wireframe(
        self.id_counter,
        "Linha",
        vertices=[start, end],
        edges=[(0, 1)],
      ))
    else:
      if len(self.building_buffer) == 3: self.log("Apenas três pontos foram inseridos. Adicionando uma curva quadrática ao invés de uma cúbica.")
      self.objects.append(Wireframe(
        self.id_counter,
        "Curva",
        vertices=self.building_buffer.copy(),
        curves=[
          Curve(self.curve_type, 
                list(range(len(self.building_buffer))), 
                self.curve_coefficient.get(), 
                degree=min(4, len(self.building_buffer)))
        ]
      ))
    self.id_counter += 1
    self.cancel_building()

  def add_surface(
    self,
    control_points: list[WorldPoint],
    degree: tuple[int, int],
    name: str="Surface",
    surface_steps: int=10,
    line_color: str="#000000",
    texture: str="#ffffff",
  ):
    if len(control_points) < 9:
      self.log("Superfície precisa de ao menos 9 pontos de controle.")
      return
    elif len(control_points) < 16:
      self.log("Interpolação bicúbica precisa de ao menos 16 pontos de controle. Criando uma superfície bilinear.")

    degree_u, degree_v = degree
    new_surface = Wireframe(
      self.id_counter,
      name,
      vertices=control_points,
      surfaces=[Surface(
        self.surface_type,
        [i for i in range(len(control_points))],
        (degree_u, degree_v),
        surface_steps,
        0.0,
        1.0,
        0.0,
        1.0,
      )],
    )
    self.objects.append(new_surface)
    self.id_counter += 1
    self.update()
    
  def generate_default_input(self, form_type: str, target_object: Wireframe | None = None) -> dict[str, str]:
    """Generates default input values for the given form type if object hasn't been created.
    Uses a seed to give slight variations to the default values, 
    but still keeping them inside the canva area.
    """

    seed = 42  # Fixed seed for reproducibility
    random.seed(seed)

    match form_type:
      case 'point':
        if target_object:
     
          return {
            'name': target_object.name,
            'coordinates': f"({target_object.vertices[0][0]:.2f}, {target_object.vertices[0][1]:.2f}, {target_object.vertices[0][2]:.2f})",
            'texture': target_object.color,
            'thickness': target_object.thickness,
            'line_color': target_object.line_color
          }
        x = random.randint(100, self.window.width - 100)
        y = random.randint(100, self.window.height - 100)
        z = random.randint(-100, 100)
        return {
          'name': 'Ponto',
          'coordinates': f"({x}, {y}, {z})",
          'texture': f"#{random.randint(0, 0xFFFFFF):06x}",
          'thickness': random.randint(1, 5),
          'line_color': f"#{random.randint(0, 0xFFFFFF):06x}"
        }
        
      case 'edge':
        if target_object:
          start = target_object.vertices[0]
          end = target_object.vertices[1]
          return {
            'name': target_object.name,
            'start_point': f"({start[0]:.2f}, {start[1]:.2f}, {start[2]:.2f})",
            'end_point': f"({end[0]:.2f}, {end[1]:.2f}, {end[2]:.2f})",
            'line_color': target_object.line_color,
            'thickness': target_object.thickness
          }
        x1 = random.randint(100, self.window.width - 200)
        y1 = random.randint(100, self.window.height - 200)
        z1 = random.randint(-100, 100)
        x2 = x1 + random.randint(50, 150)
        y2 = y1 + random.randint(50, 150)
        z2 = z1 + random.randint(-50, 50)
        return {
          'name': 'Aresta',
          'start_point': f"({x1:.2f}, {y1:.2f}, {z1:.2f})",
          'end_point': f"({x2:.2f}, {y2:.2f}, {z2:.2f})",
          'line_color': f"#{random.randint(0, 0xFFFFFF):06x}",
          'line_width': random.randint(1, 5)
        }
      case 'face':
        points = []
        if target_object:
          for point in target_object.vertices:
            points.append(f"({point[0]:.2f}, {point[1]:.2f}, {point[2]:.2f})")
          return {
            'name': target_object.name,
            'vertices': ', '.join(points),
            'line_color': target_object.lince_color,
            'thickness': str(target_object.thickness),
            'texture': target_object.color
          }
        num_points = random.randint(3, 6)
        for _ in range(num_points):
          x = random.randint(100, self.window.width - 100)
          y = random.randint(100, self.window.height - 100)
          z = random.randint(-100, 100)
          points.append(f"({x}, {y}, {z})")
        return {
          'name': 'Face',
          'vertices': ', '.join(points),
          'line_color': f"#{random.randint(0, 0xFFFFFF):06x}",
          'thickness': random.randint(1, 5),
          'texture': f"#{random.randint(0, 0xFFFFFF):06x}",
        }
      case 'polygon':
        points = []
        if target_object:
          for point in target_object.vertices:
            points.append(f"({point[0]}, {point[1]}, {point[2]})")
          return {
            'name': target_object.name,
            'points': ', '.join(points),
            'line_color': target_object.line_color,
            'thickness': str(target_object.thickness),
            'texture': target_object.color           
          }
        num_points = random.randint(3, 6)
        for _ in range(num_points):
          x = random.randint(100, self.window.width - 100)
          y = random.randint(100, self.window.height - 100)
          z = random.randint(-100, 100)
          points.append(f"({x}, {y}, {z})")
        return {
          'name': 'Polígono',
          'points': ', '.join(points),
          'line_color': f"#{random.randint(0, 0xFFFFFF):06x}",
          'thickness': random.randint(1, 5),
          'texture': f"#{random.randint(0, 0xFFFFFF):06x}",
        }
      case 'curve':
        points = []
        if target_object:
          for point in target_object.vertices:
            points.append(f"({point[0]}, {point[1]}, {point[2]})")
          return {
            'name': target_object.name,
            'points': ', '.join(points),
            'line_color': target_object.line_color,
            'thickness': str(target_object.thickness)
          }
        num_points = random.randint(4, 6)
        for _ in range(num_points):
          x = random.randint(100, self.window.width - 100)
          y = random.randint(100, self.window.height - 100)
          z = random.randint(-100, 100)
          points.append(f"({x}, {y}, {z})")
        return {
          'name': 'Curva',
          'points': ', '.join(points),
          'line_color': f"#{random.randint(0, 0xFFFFFF):06x}",
          'thickness': random.randint(1, 5)
        }
      case 'surface':
        if target_object:
          return {
            'name': target_object.name,
            'line_color': target_object.line_color,
            'texture': target_object.color,
            'thickness': str(target_object.thickness)
          }
        return {
          'name': 'Superfície',
          'line_color': f"#{random.randint(0, 0xFFFFFF):06x}",
          'texture': f"#{random.randint(0, 0xFFFFFF):06x}",
          'thickness': str(random.randint(1, 5))
        }
      case _:
        return {} 
        