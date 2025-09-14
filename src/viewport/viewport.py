import tkinter as tk
from tkinter import ttk, messagebox, font, colorchooser, simpledialog, scrolledtext
from wireframe import *
from screen import *
from components.toggle_switch import *
from components.color_scheme import ColorScheme
from data.usr_preferences import *
from components.my_types import Point, CursorTypes
from .clipping import Clipping, ClippingAlgorithm
import math

class Viewport:
  def __init__(self, width, height, title="INE5420", input: str | None=None, output: str | None=None, debug: bool=False):
    self.output: str | None = output
    self.input: str | None = input

    self.width: int = width
    self.height: int = height
    self.objects: list[Wireframe] = self.load_objects(input) if input else []
    self.build: list[Point] = []
    self._building: bool = False
    self.rotation_angle: float = 0.0
    self.scale: float = 1.0

    self.debug: bool = debug
    self.debug_objects: list[Wireframe] = [PointObject("World Origin", np.array([0, 0, 0]), id=0)]
    self.camera = Camera(np.array([0, 0, -1]), np.array([0, 0, 100]), width*0.8, height*0.8)

    # TODO: Move all of the functions in that file to here
    # TODO: Remove the unnecessary usage of self.theme instead of self.preferences["theme"], possibly turning self.preferences into a class of its own instead of it being a dict
    self.preferences = load_user_preferences()
    self.show_onboarding = self.preferences.get("show_onboarding", True)
    self.theme = self.preferences.get("theme", "light")
    self.clipping_algorithm = ClippingAlgorithm[self.preferences.get("clipping_algorithm", "COHEN_SUTHERLAND")]

    # Tkinter setup
    self.root: tk.Tk = tk.Tk()
    self.root.geometry(f"{width}x{height}")
    self.root.resizable(False, False)
    self.root.title(title)
    self.root.protocol("WM_DELETE_WINDOW", self.exit)

    # Ui components
    # Canva
    self.canva = tk.Canvas(self.root, background="white")
    
    # Log session
    self.ui_log = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, bg="white", fg="black", state="disabled", height=5)

    # Control buttons and input fields
    self.ui_build_button = tk.Button(self.root, text="Build", command=self.set_building)
    self.ui_close_polygon_button = tk.Button(self.root, text="Polígono", command=self.finish_polygon)
    self.ui_object_properties_button = tk.Button(self.root, text="Propriedades", command=lambda: self.log("Função não implementada"))
    self.ui_rotate_object_button = tk.Button(self.root, text="Girar", command=lambda: self.rotate("left"))
    self.ui_translate_object_button = tk.Button(self.root, text="Deslocar", command=self.translate)
    self.ui_scale_button = tk.Button(self.root, text="Escalar", command=lambda: self.log("Função não implementada"))

    self.ui_point_label = tk.Label(self.root, text="Ponto (x,y):")
    self.ui_point_x_input = tk.Entry(self.root)
    self.ui_point_y_input = tk.Entry(self.root)

    self.ui_degree_label = tk.Label(self.root, text="Ângulo:")
    self.ui_degree_var = tk.StringVar(value="Ângulo")
    self.ui_degree_input = tk.Entry(self.root)
    self.ui_scale_factor_label = tk.Label(self.root, text="Fator:")
    self.ui_scale_factor_var = tk.StringVar(value="Fator")
    self.ui_scale_factor_input = tk.Entry(self.root)

    # Object List
    self.ui_object_list_frame = tk.Frame(self.root)
    self.ui_object_list_frame.rowconfigure(0, weight=1)
    self.ui_object_list_frame.columnconfigure(0, weight=1)
    scrollbar_x = ttk.Scrollbar(self.ui_object_list_frame, orient="horizontal")
    scrollbar_y = ttk.Scrollbar(self.ui_object_list_frame, orient="vertical")

    self.ui_object_list = ttk.Treeview(
      self.ui_object_list_frame,
      columns=("Id", "Points"),
      show="headings",
      xscrollcommand=scrollbar_x.set,
      yscrollcommand=scrollbar_y.set,
      style="Custom.Treeview"
    )

    scrollbar_x.config(command=self.ui_object_list.xview)
    scrollbar_y.config(command=self.ui_object_list.yview)
    self.ui_object_list.heading("Id", text="Id")
    self.ui_object_list.heading("Points", text="Points")
    self.ui_object_list.column("Id", width=100, anchor="center", stretch=tk.NO)
    self.ui_object_list.column("Points", anchor="w", stretch=tk.YES)

    self.ui_object_list.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, rowspan=2, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")


    self.build_ui()
    self.controls()
    self.update()

  # TODO: your job for today lmao
  def build_ui(self):
    for i in range(12): self.root.columnconfigure(i, weight=1)
    for i in range(120): self.root.rowconfigure(i, weight=1)
    
    self.canva.grid(row=0, column=4, columnspan=8, rowspan=100, sticky="nsew")
    self.ui_log.grid(row=100, column=4, columnspan=12, rowspan=20, sticky="nsew")

    self.ui_build_button.grid(row=60, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_close_polygon_button.grid(row=60, column=2, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_rotate_object_button.grid(row=62, column=0, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_translate_object_button.grid(row=62, column=1, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_scale_button.grid(row=62, column=2, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_object_properties_button.grid(row=62, column=3, rowspan=1, columnspan=1, sticky="nsew")

    self.ui_object_list_frame.grid(row=0, column=0, rowspan=60, columnspan=4, sticky="nsew")

    self.ui_point_label.grid(row=63, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_point_x_input.grid(row=63, column=2, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_point_y_input.grid(row=63, column=3, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_degree_label.grid(row=64, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_degree_input.grid(row=64, column=2, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_scale_factor_label.grid(row=65, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_scale_factor_input.grid(row=65, column=2, rowspan=1, columnspan=2, sticky="nsew")



  # TODO: Don't touch
  def build_debug_grid(self):
    step = 75
    min_zoom = self.camera.min_zoom 

    width = self.width
    height = self.height
  
    max_world_width = width / min_zoom
    max_world_height = height / min_zoom
    max_range = int(max(max_world_width, max_world_height) / 2)  # /2 para ter metade pra cada lado do centro
    
    start = ( -max_range // step ) * step
    end = ( max_range // step + 1 ) * step

    for i in range(start, end, step):
      start_h = self.camera.world_to_viewport(np.array([-max_range, i, 0]))
      end_h = self.camera.world_to_viewport(np.array([max_range, i, 0]))
      self.canva.create_line(
        start_h[0], start_h[1], end_h[0], end_h[1],
        fill=ColorScheme.LIGHT_DEBUG_GRID.value if self.theme == "light" else ColorScheme.DARK_DEBUG_GRID.value
      )

      start_v = self.camera.world_to_viewport(np.array([i, -max_range, 0]))
      end_v = self.camera.world_to_viewport(np.array([i, max_range, 0]))
      self.canva.create_line(
        start_v[0], start_v[1], end_v[0], end_v[1],
        fill=ColorScheme.LIGHT_DEBUG_GRID.value if self.theme == "light" else ColorScheme.DARK_DEBUG_GRID.value
      )

    origin = self.camera.world_to_viewport(np.array([0, 0, 0]))
    self.canva.create_text(origin[0] + 15, origin[1] - 10, text="(0,0)", fill=ColorScheme.LIGHT_TEXT.value if self.theme == "light" else ColorScheme.DARK_TEXT.value, font=("Arial", 10, "bold"))

  # TODO: Don't touch
  # I touched it lmao fuck this shit
  def toggle_light_dark_mode(self, state: bool):
    self.theme = "light" if not state else "dark"

    if state: # dark mode
      self.root.config(bg=ColorScheme.DARK_BG.value)
      self.canva.config(bg=ColorScheme.DARK_CANVAS.value)
    else:
      self.root.config(bg=ColorScheme.LIGHT_BG.value)
      self.canva.config(bg=ColorScheme.LIGHT_CANVAS.value)

      self.ui_object_list.config()
    
    self.update()

  # TODO: Learn this topic]
  # TODO: When rebuilding the UI, use this function
  def rotate(self, direction: str):
    # only rotates if an object is selected
    # if a pivot point is specified, rotates around that point
    # if an angle is specified, rotates by that angle
    # if angle is not specified, uses the default value (15)
    rotate_degrees = "15"
  
    if direction == "left":
      self.rotation_angle -= float(rotate_degrees)
    elif direction == "right":
      self.rotation_angle += float(rotate_degrees)
    else:
      return

    angle = -float(rotate_degrees) if direction == "left" else float(rotate_degrees)

    radians = math.radians(angle)
    cos = math.cos(radians)
    sin = math.sin(radians)
    
    R = np.array([
        [cos, sin, 0.0],
        [-sin, cos, 0.0],
        [0.0,  0.0, 1.0]
    ], dtype=float)

    # px_str = self.around_point_x.get()
    # pz_str = self.around_point_y.get()
    px_str, pz_str = None, None
    
    if px_str and pz_str:
      try:
        px = float(px_str)
        pz = float(pz_str)
        
        selected_item = self.ui_object_list.selection()
        if not selected_item:
          self.log("Aviso: Nenhum objeto selecionado.")
          return
        
        item_id = self.ui_object_list.item(selected_item[0], "tags")[0]
        target = next((o for o in self.objects if str(o.id) == item_id), None)

        T  = np.array([[1, 0, px], [0, 1, pz], [0, 0, 1]], dtype=float)
        Ti = np.array([[1, 0, -px], [0, 1, -pz], [0, 0, 1]], dtype=float)
        M  = T @ R @ Ti

        if target: target.transform2d_xz(M)

      except ValueError:
        self.log("Erro: Coordenadas do ponto inválidas.")
        return
    else:
      selected_item = self.ui_object_list.selection()
      if not selected_item:
        self.log("Aviso: Nenhum objeto selecionado.")
        return

      item_id = self.ui_object_list.item(selected_item[0], "tags")[0]
      target = next((o for o in self.objects if str(o.id) == item_id), None)

      if target is None:
        self.log("Aviso: Objeto não encontrado.")
        return

      cx, cz = float(target.center[0]), float(target.center[2])

      T  = np.array([[1, 0, cx], [0, 1, cz], [0, 0, 1]], dtype=float)
      Ti = np.array([[1, 0, -cx], [0, 1, -cz], [0, 0, 1]], dtype=float)
      M  = T @ R @ Ti

      target.transform2d_xz(M)

    self.update()

  # TODO: Resist the urge to change all of this to just x += tx and z += ty
  def translate(self):
    # tx = float(self.translate_x.get()) if self.translate_x.get() else 0
    # ty = float(self.translate_y.get()) if self.translate_y.get() else 0
    tx, ty = 100, 100

    translation_matrix = np.array([
      [1, 0, tx],
      [0, 1, ty],
      [0, 0, 1]
    ], dtype=float)

    selected_item = self.ui_object_list.selection()
    if not selected_item:
      self.log("Aviso: Nenhum objeto selecionado.")
      return

    item_id = self.ui_object_list.item(selected_item[0], "tags")[0]
    target = next((o for o in self.objects if str(o.id) == item_id), None)

    if target is None:
      self.log("Aviso: Objeto não encontrado.")
      return
    target.transform2d_xz(translation_matrix)


    self.update()

  # TODO: Update this so the button color will indicate the current mode
  def set_building(self): 
    if not self.building:
      self.building = True

  # TODO: Update this so the button color will indicate the current mode
  def cancel_building(self):
    self.build.clear()
    self.building = False
    self.update()

  def set_debug(self):
    self.debug = not self.debug
    self.update()

  def move_camera(self, event):
    self.camera.position = self.camera.viewport_to_world(event.x, event.y)
    self.update()

  def clear(self):
    self.objects.clear()
    self.ui_object_list.delete(*self.ui_object_list.get_children())
    self.build.clear()
    self.building = False
    self.update()

  # TODO: Put this in the proper place ffs
  # def set_theme(self):
  #   style = ttk.Style()
  #   style.theme_use('default')  # usar tema padrão

  #   if self.theme == "dark":
  #     bg_color = ColorScheme.DARK_CANVAS.value
  #     text_color = ColorScheme.DARK_TEXT.value
  #     selected_bg = "#333366"
  #     selected_fg = "white"
  #   else:
  #     bg_color = ColorScheme.LIGHT_CANVAS.value
  #     text_color = ColorScheme.LIGHT_TEXT.value
  #     selected_bg = "#cce5ff"
  #     selected_fg = "black"

  #   style.configure(
  #     "Custom.Treeview",
  #     background=bg_color,
  #     foreground=text_color,
  #     fieldbackground=bg_color,
  #     bordercolor=bg_color,
  #     borderwidth=0
  #   )

  #   style.map(
  #     "Custom.Treeview",
  #     background=[('selected', selected_bg)],
  #     foreground=[('selected', selected_fg)]
  #   )

  def controls(self):
    self.canva.bind("<ButtonRelease-1>", self.canva_click)
    self.canva.bind("<Button-3>", self.move_camera)
    self.root.bind("<Button-2>", lambda e: self.set_debug())
    self.root.bind("<Button-4>", lambda e: self.camera.zoom_in(e.x, e.y) or self.update())
    self.root.bind("<Button-5>", lambda e: self.camera.zoom_out(e.x, e.y) or self.update())
    self.root.bind("<KeyPress-w>", lambda e: self.camera.move_up() or self.update())
    self.root.bind("<KeyPress-s>", lambda e: self.camera.move_down() or self.update())
    self.root.bind("<KeyPress-a>", lambda e: self.camera.move_left() or self.update())
    self.root.bind("<KeyPress-d>", lambda e: self.camera.move_right() or self.update())
    self.root.bind("<KeyPress-q>", lambda e: self.camera.move_below() or self.update())
    self.root.bind("<KeyPress-e>", lambda e: self.camera.move_above() or self.update())
    self.root.bind("<KeyPress-Escape>", lambda e: self.cancel_building())
    self.root.bind("<Control-z>", lambda e: self.undo())

  def canva_click(self, event):
    if self.building: self.build.append(self.camera.viewport_to_world(event.x, event.y))
    else:  self.objects.append(PointObject("Clicked Point", self.camera.viewport_to_world(event.x, event.y), id=10*len(self.objects)+1))
    self.update()

  def finish_polygon(self):
    if len(self.build) < 3: 
      self.log("Erro: Pelo menos três pontos são necessários para formar um polígono.")
      return
    
    self.objects.append(PolygonObject("Polygon", self.build.copy(), id=10*len(self.objects)+1))
    self.cancel_building()

  def update(self):
    self.canva.delete("all")
    all_objects = self.objects.copy()
    
    # Add debug objects to the list of objects to be drawn if debug mode is on
    if self.debug:
      all_objects += self.debug_objects
      self.build_debug_grid()
      self.canva.create_line(0, self.height*0.4, self.width, self.height*0.4, fill="blue")
      self.canva.create_line(self.width*0.4, 0, self.width*0.4, self.height, fill="blue")  

    # TODO: Clipping
    # Clip the objects if a clipping algorithm is selected, I don't think this is supposed to be here tho
    # x0 = self.camera.h_viewport_margin
    # y0 = self.camera.v_viewport_margin
    # x1 = self.camera.viewport_width - self.camera.h_viewport_margin
    # y1 = self.camera.viewport_height - self.camera.v_viewport_margin
    # window = [x0, y0, x1, y1]
    # clipping = Clipping(window)
    clipped_objects = all_objects

    # Draw all objects
    for obj in clipped_objects:
      figures = obj.figures()
      if isinstance(obj, PolygonObject):
        for edge in figures:
          # Draw polygon edges
          if edge.end is None: raise ValueError("Polygon edge has no endpoint")
          start, end = self.camera.world_to_viewport(edge.start), self.camera.world_to_viewport(edge.end)
          self.canva.create_line(start[0], start[1], end[0], end[1], fill=obj.color)
        
        # Fill polygon
        if obj.fill_color:
          projected_points = [self.camera.world_to_viewport(edge.start) for edge in figures]
          
          # fecha o poligono se necessario
          if not np.array_equal(projected_points[0], projected_points[-1]):
              projected_points.append(projected_points[0])

          points = [coord for point in projected_points for coord in point]
          if len(points) >= 6:  
            self.canva.create_polygon(points, fill=obj.fill_color, outline=obj.color)

      else:
        for edge in figures:       
          if edge.end is not None:
            start, end = self.camera.world_to_viewport(edge.start), self.camera.world_to_viewport(edge.end)
            self.canva.create_line(start[0], start[1], end[0], end[1], fill=obj.color)
          
          else:
            point = self.camera.world_to_viewport(edge.start)
            radius = obj.radius
            self.canva.create_oval(point[0] - radius, point[1] - radius, point[0] + radius, point[1] + radius, fill=obj.color)

    # Refresh the object list
    self.ui_object_list.delete(*self.ui_object_list.get_children())
    for obj in self.objects:
      self.add_object_to_table(obj)

    # Redraw the building lines if in building mode
    prev = None
    for point in self.build:
      point = self.camera.world_to_viewport(point)
      self.canva.create_oval(point[0] - 2, point[1] - 2, point[0] + 2, point[1] + 2, fill="red")
      if prev is not None: self.canva.create_line(prev[0], prev[1], point[0], point[1], fill="red")
      prev = point

    # Viewport border to visualize the clipping area
    self.draw_viewport_border()

  def run(self) -> list[Wireframe]:
    self.root.mainloop()
    if self.output:
      try:
        with open(self.output, "w") as file:
          for obj in self.objects:
            file.write(f"{obj}\n")
      except Exception as e:
        self.log(f"Erro ao salvar objetos: {e}")
    return self.objects
  
  def add_object_to_table(self, obj: Wireframe):
    formatted_coordinates = [f"({', '.join(f'{coord:.2f}' for coord in point)})" for point in obj.points]
    self.ui_object_list.insert("", "end", values=(obj.name, ", ".join(formatted_coordinates)), tags=(str(obj.id),))

    font_style = font.nametofont("TkDefaultFont")
    font_size = font_style.measure("".join(formatted_coordinates)) + 20
    
  def draw_viewport_border(self):
    x0 = self.camera.h_viewport_margin
    y0 = self.camera.v_viewport_margin
    x1 = self.camera.viewport_width - self.camera.h_viewport_margin
    y1 = self.camera.viewport_height - self.camera.v_viewport_margin

    self.canva.create_rectangle(x0, y0, x1, y1, outline="red", width=2)

  def change_point_color(self):
    selected_item = self.ui_object_list.selection()
    
    if not selected_item:
      self.log("Aviso: Nenhum objeto selecionado.")
      return
    
    item_id = self.ui_object_list.item(selected_item[0], "tags")[0]
    for obj in self.objects:
      if str(obj.id) == item_id:
        color = colorchooser.askcolor(title="Escolha a cor do ponto")
        if color[1]:
          obj.color = color[1]
          self.update()
        break

  def change_point_radius(self):
    selected_item = self.ui_object_list.selection()
    if not selected_item:
      self.log("Aviso: Nenhum objeto selecionado.")
      return

    item_id = self.ui_object_list.item(selected_item[0], "tags")[0]
    for obj in self.objects:
      if str(obj.id) == item_id:
        obj.radius = simpledialog.askfloat("Raio do Ponto", "Digite o novo raio do ponto:", minvalue=1, maxvalue=100, initialvalue=obj.radius) or 0.0
        if obj.radius is not None:
          self.update()
          break

  def change_line_color(self):
    selected_item = self.ui_object_list.selection()
    if not selected_item:
      self.log("Aviso: Nenhum objeto selecionado.")
      return

    item_id = self.ui_object_list.item(selected_item[0], "tags")[0]
    for obj in self.objects:
      if str(obj.id) == item_id:
        color = colorchooser.askcolor(title="Escolha a cor da linha")
        if color[1]:
          obj.color = color[1]
          self.update()
        break

  def change_fill_color(self):    
    selected_item = self.ui_object_list.selection()
    if not selected_item:
      self.log("Aviso: Nenhum objeto selecionado.")
      return
    item_id = self.ui_object_list.item(selected_item[0], "tags")[0]

    for obj in self.objects:
      if str(obj.id) == item_id:
        color = colorchooser.askcolor(title="Escolha a cor de preenchimento")
        if color[1]:
          obj.fill_color = color[1]
          self.update()
        break

  def load_objects(self, objects: str) -> list[Wireframe]:
    if not objects: return []
    try:
      with open(objects, "r") as file:
        return [Wireframe.from_string(line.strip()) for line in file if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
      self.log(f"Arquivo {objects} não encontrado.")
      return []
    except Exception as e:
      self.log(f"Erro: Erro ao carregar objetos: {e}")
      return []

  # TODO: Send log message to log widget
  def log(self, message: str):
    print(message)

  def undo(self):
    if self.building:
      if self.build: self.build.pop()
      else: self.building = False
    elif self.objects:
      self.objects.pop()
    self.update()

  def exit(self):
    # For the love of christ I ain't confirming exit anymore
    # if messagebox.askokcancel("Sair", "Deseja sair?"):
      usr_pref = {
        "theme": self.theme,
        "show_onboarding": self.show_onboarding
      }
      save_user_preferences(usr_pref)
      self.root.quit()

  @property
  def building(self) -> bool: return self._building

  @building.setter
  def building(self, value: bool):
    self._building = value
