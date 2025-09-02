import tkinter as tk
from tkinter import ttk, messagebox, font, colorchooser, simpledialog
from wireframe import *
from screen import *
from components.toggle_switch import *
from components.color_scheme import ColorScheme

#from .ui_builder import build_ui

class Viewport:
  def __init__(self, width, height, title="INE5420", input: str | None=None, output: str | None=None, debug: bool=False):
    self.output: str | None = output 
    
    self.width: int = width
    self.height: int = height
    self.objects: list[Wireframe] = self.load_objects(input) if input else []
    self.build: list[Point] = []
    self._building: bool = False
    self.rotation_angle: float = 0.0
    self.scale: float = 1.0
    self.transform_matrix = np.identity(2)

    self.debug: bool = debug
    self.debug_objects: list[Wireframe] = [PointObject("World Origin", np.array([0, 0, 0]), id=0)]
    self.camera = Camera(np.array([0, -1, 0]), np.array([0, 100, 0]), width*0.8, height*0.8)
    self.original_points: list[Point] = [Point(p.x, p.y, p.z) for p in self.objects]

    # Ui components
    self.root: tk.Tk = tk.Tk()
    self.root.geometry(f"{width}x{height}")
    self.root.resizable(True, True)
    self.root.title(title)

    self.canva = tk.Canvas(self.root, background=ColorScheme.LIGHT_BG.value, width=0.8 * self.width, height=0.8 * self.height)
    
    # creates elements on the right
    self.right_panel = tk.Frame(self.root)
    self.right_panel.grid(row=0, column=4, rowspan=10, columnspan=7, sticky="nsew", padx=5, pady=5)
    self.right_panel.grid_columnconfigure(0, weight=1)
    
    self.exit_button = tk.Button(self.right_panel, text="Exit", command=self.root.quit, bg="red", fg="white")
    self.toggle_light_dark = ToggleSwitch(self.right_panel, width=80, height=40, on_toggle=self.toggle_light_dark_mode)
    
    # colors
    self.color_button_frame = tk.Frame(self.root)
    self.color_button_frame.grid(row=4, column=5, rowspan=8, sticky="ns")

    self.change_line_color_button = tk.Button(self.color_button_frame, text="Line Color", command=self.change_line_color)
    self.change_fill_color_button = tk.Button(self.color_button_frame, text="Fill Color", command=self.change_fill_color)
    self.change_point_color_button = tk.Button(self.color_button_frame, text="Point Color", command=self.change_point_color)
    self.change_point_radius_button = tk.Button(self.color_button_frame, text="Point Radius", command=self.change_point_radius)

    # camera controls
    self.recenter_button = tk.Button(self.right_panel, text="Recenter", command=lambda: self.camera.recenter() or self.update())

    self.build_button = tk.Button(self.root, text="Build", command=self.set_building)
    self.lines_button = tk.Button(self.root, text="Lines", command=self.finish_lines)
    self.polygon_button = tk.Button(self.root, text="Polygon", command=self.finish_polygon)
    self.clear_button = tk.Button(self.root, text="Clear", command=self.clear)

    # transform frame
    self.transform_widget_frame = tk.Frame(self.root)
    self.transform_widget_frame.grid(row=1, column=5, columnspan=2, sticky="nsew")
    self.transform_widget_frame.grid_columnconfigure(0, weight=1)
    self.transform_widget_frame.grid_columnconfigure(1, weight=1)
    self.transform_widget_frame.config(width=100, height=100)

    self.m00_value = tk.StringVar()
    self.m01_value = tk.StringVar()
    self.m10_value = tk.StringVar()
    self.m11_value = tk.StringVar()
    self.m00_input = tk.Entry(self.transform_widget_frame, textvariable=self.m00_value, width=6)
    self.m01_input = tk.Entry(self.transform_widget_frame, textvariable=self.m01_value, width=6)
    self.m10_input = tk.Entry(self.transform_widget_frame, textvariable=self.m10_value, width=6)
    self.m11_input = tk.Entry(self.transform_widget_frame, textvariable=self.m11_value, width=6)
    self.apply_transform_button = tk.Button(self.transform_widget_frame, text="Apply Transform", command=self.apply_transform)

    # translate frame
    self.translate_frame = tk.Frame(self.root)
    self.translate_frame.grid(row=2, column=5, columnspan=1, sticky="nsew")

    insert_x_label = tk.Label(self.translate_frame, text="X:")
    insert_x_label.grid(row=0, column=1, sticky="ew")
    self.translate_x = tk.StringVar()
    self.translate_x_entry = tk.Entry(self.translate_frame, textvariable=self.translate_x, width=6)

    insert_y_label = tk.Label(self.translate_frame, text="Y:")
    insert_y_label.grid(row=0, column=3, sticky="ew")
    self.translate_y = tk.StringVar()
    self.translate_y_entry = tk.Entry(self.translate_frame, textvariable=self.translate_y, width=6)

    self.translate_x_entry.grid(row=0, column=2, sticky="ew")
    self.translate_y_entry.grid(row=0, column=4, sticky="ew")
    
    self.translate_button = tk.Button(self.translate_frame, text="Translate", command=self.translate)
    self.translate_button.grid(row=0, column=0, sticky="ew")

    # rotate frame
    self.rotate_frame = tk.Frame(self.root)
    self.rotate_frame.grid(row=3, column=5, columnspan=1, sticky="nsew")

    rotate_label = tk.Label(self.rotate_frame, text="Rotate:")
    rotate_label.grid(row=0, column=0, sticky="w")

    self.rotate_left_button = tk.Button(self.rotate_frame, text="⟲", command=lambda: self.rotate("left"))
    self.rotate_left_button.grid(row=0, column=1, sticky="ew")

    self.rotate_right_button = tk.Button(self.rotate_frame, text="⟳", command=lambda: self.rotate("right"))
    self.rotate_right_button.grid(row=0, column=2, sticky="ew")

    self.rotate_degrees = tk.StringVar()
    self.rotate_degrees_entry = tk.Entry(self.rotate_frame, textvariable=self.rotate_degrees, width=6)
    self.rotate_degrees_entry.grid(row=0, column=3, sticky="ew")

    degree_symbol_label = tk.Label(self.rotate_frame, text="°")
    degree_symbol_label.grid(row=0, column=4, sticky="w")

    around_point_label = tk.Label(self.rotate_frame, text="Around Point:")
    around_point_label.grid(row=1, column=0, sticky="w")

    self.around_point_x = tk.StringVar()
    self.around_point_y = tk.StringVar()
    self.around_point_x_entry = tk.Entry(self.rotate_frame, textvariable=self.around_point_x, width=6)
    self.around_point_y_entry = tk.Entry(self.rotate_frame, textvariable=self.around_point_y, width=6)

    self.around_point_x_entry.grid(row=1, column=1, sticky="ew")
    self.around_point_y_entry.grid(row=1, column=2, sticky="ew")

    self.build_forms_table()
    self.controls()
    self.build_ui()
    self.setup_grid()
    self.update()

  def toggle_light_dark_mode(self, state):
    if state: # dark mode
      self.root.config(bg=ColorScheme.DARK_BG.value)
      self.canva.config(bg=ColorScheme.DARK_CANVAS.value)
      self.color_button_frame.config(bg=ColorScheme.DARK_BG.value)
      self.transform_widget_frame.config(bg=ColorScheme.DARK_BG.value)
      self.translate_frame.config(bg=ColorScheme.DARK_BG.value)
      self.rotate_frame.config(bg=ColorScheme.DARK_BG.value)
      self.right_panel.config(bg=ColorScheme.DARK_BG.value)
    else:
      self.root.config(bg=ColorScheme.LIGHT_BG.value)
      self.canva.config(bg=ColorScheme.LIGHT_CANVAS.value)
      self.color_button_frame.config(bg=ColorScheme.LIGHT_BG.value)
      self.transform_widget_frame.config(bg=ColorScheme.LIGHT_BG.value)
      self.translate_frame.config(bg=ColorScheme.LIGHT_BG.value)
      self.rotate_frame.config(bg=ColorScheme.LIGHT_BG.value)
      self.right_panel.config(bg=ColorScheme.LIGHT_BG.value)
      
  def setup_grid(self):
    for i in range(10):
      self.root.grid_rowconfigure(i, weight=1)
      self.root.grid_columnconfigure(i, weight=1)
      
    for i in range(11, 21):
      self.root.grid_rowconfigure(i, weight=0)

    #self.root.resizable(False, False) # redimensionar travado
    self.toggle_light_dark_mode(False)
    
  def apply_transform(self, pivot=None):
      if not self.m00_input.get(): self.m00_value.set("1.0")
      if not self.m01_input.get(): self.m01_value.set("0.0")
      if not self.m10_input.get(): self.m10_value.set("0.0")
      if not self.m11_input.get(): self.m11_value.set("1.0")

      selected_item = self.formsTable.selection()
      if not selected_item:
          messagebox.showwarning("Aviso", "Nenhum objeto selecionado.")
          return

      try:
          m00 = float(self.m00_value.get())
          m01 = float(self.m01_value.get())
          m10 = float(self.m10_value.get())
          m11 = float(self.m11_value.get())
      except ValueError:
          messagebox.showerror("Erro", "Valores inválidos para a matriz.")
          return

      item_id = self.formsTable.item(selected_item[0], "tags")[0]
      target = next((o for o in self.objects if str(o.id) == item_id), None)
      if target is None:
          messagebox.showwarning("Aviso", "Objeto não encontrado.")
          return

      A = np.array([[m00, m01, 0.0],
                    [m10, m11, 0.0],
                    [0.0, 0.0, 1.0]], dtype=float)
      
      if pivot is None:
          cx, cz = float(target.center[0]), float(target.center[2])
      else:
          cx, cz = pivot

      T = np.array([[1,0,cx],[0,1,cz],[0,0,1]])
      Ti = np.array([[1,0,-cx],[0,1,-cz],[0,0,1]])
      M = T @ A @ Ti

      target.transform_matrix = M @ target.transform_matrix
      target.apply_matrix()

      target.transform2d_xz(M)
      self.update()

  def rotate(self, direction: str):
    # only rotates if an object is selected
    # if a pivot point is specified, rotates around that point
    # if an angle is specified, rotates by that angle
    # if angle is not specified, uses the default value (15)
    rotate_degrees = self.rotate_degrees.get() if self.rotate_degrees.get() else "15"
  
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

    px_str = self.around_point_x.get()
    pz_str = self.around_point_y.get()
    
    if px_str and pz_str:
      try:
        px = float(px_str)
        pz = float(pz_str)
        
        selected_item = self.formsTable.selection()
        if not selected_item:
          messagebox.showwarning("Aviso", "Nenhum objeto selecionado.")
          return
        
        item_id = self.formsTable.item(selected_item[0], "tags")[0]
        target = next((o for o in self.objects if str(o.id) == item_id), None)

        T  = np.array([[1, 0, px], [0, 1, pz], [0, 0, 1]], dtype=float)
        Ti = np.array([[1, 0, -px], [0, 1, -pz], [0, 0, 1]], dtype=float)
        M  = T @ R @ Ti

        target.transform2d_xz(M)

        # for target in self.objects:
        #     target.transform2d_xz(M)

      except ValueError:
        messagebox.showerror("Erro", "Coordenadas do ponto inválidas.")
        return
    else:
      selected_item = self.formsTable.selection()
      if not selected_item:
        messagebox.showwarning("Aviso", "Nenhum objeto selecionado.")
        return

      item_id = self.formsTable.item(selected_item[0], "tags")[0]
      target = next((o for o in self.objects if str(o.id) == item_id), None)

      if target is None:
          messagebox.showwarning("Aviso", "Objeto não encontrado.")
          return

      cx, cz = float(target.center[0]), float(target.center[2])

      T  = np.array([[1, 0, cx], [0, 1, cz], [0, 0, 1]], dtype=float)
      Ti = np.array([[1, 0, -cx], [0, 1, -cz], [0, 0, 1]], dtype=float)
      M  = T @ R @ Ti

      target.transform2d_xz(M)
      # else:
      #   cx, cz = float(self.camera.position[0]), float(self.camera.position[2])
      #   T  = np.array([[1, 0, cx], [0, 1, cz], [0, 0, 1]], dtype=float)
      #   Ti = np.array([[1, 0, -cx], [0, 1, -cz], [0, 0, 1]], dtype=float)
      #   M  = T @ R @ Ti

      #   for target in self.objects:
      #       target.transform2d_xz(M)

    self.update()

  def translate(self):
    tx = float(self.translate_x.get()) if self.translate_x.get() else 0
    ty = float(self.translate_y.get()) if self.translate_y.get() else 0

    translation_matrix = np.array([[1, 0, tx],
                                  [0, 1, ty],
                                  [0, 0, 1]], dtype=float)

    selected_item = self.formsTable.selection()
    if not selected_item:
        messagebox.showwarning("Aviso", "Nenhum objeto selecionado.")
        return

    item_id = self.formsTable.item(selected_item[0], "tags")[0]
    target = next((o for o in self.objects if str(o.id) == item_id), None)

    if target is None:
        messagebox.showwarning("Aviso", "Objeto não encontrado.")
        return
    target.transform2d_xz(translation_matrix)
    # else:
    #     for target in self.objects:
    #         target.transform2d_xz(translation_matrix)

    self.update()

  def set_building(self): self.building = True

  def set_debug(self):
    self.debug = not self.debug
    self.update()

  def move_camera(self, event):
    self.camera.position = self.camera.viewport_to_world(event.x, event.y)
    self.update()

  def clear(self):
    self.objects.clear()
    self.formsTable.delete(*self.formsTable.get_children())
    self.build.clear()
    self.building = False
    self.update()

  def cancel_building(self):
    self.build.clear()
    self.building = False
    self.update()

  def build_ui(self):
    self.canva.grid(row=0, column=0, columnspan=4, rowspan=10, sticky="nsew", padx=5, pady=5)
    
    self.build_button.grid(row=11, column=0, sticky="ew", padx=5, pady=5)
    self.lines_button.grid(row=11, column=1, sticky="ew", padx=5, pady=5)
    self.polygon_button.grid(row=11, column=2, sticky="ew", padx=5, pady=5)
    self.clear_button.grid(row=11, column=3, sticky="ew", padx=5, pady=5)
    
    self.toggle_light_dark.grid(row=0, column=1, padx=5, pady=5)
    self.exit_button.grid(row=0, column=7, columnspan=1)
    self.recenter_button.grid(row=0, column=0, columnspan=3)

    self.m00_input.grid(row=0, column=0, sticky="ew")
    self.m01_input.grid(row=0, column=1, sticky="ew")
    self.m10_input.grid(row=1, column=0, sticky="ew")
    self.m11_input.grid(row=1, column=1, sticky="ew")
    self.apply_transform_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))

    self.change_fill_color_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    self.change_line_color_button.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
    self.change_point_color_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
    self.change_point_radius_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

  def build_forms_table(self):
    self.forms_table_frame = tk.Frame(self.root, width=400, height=200, background="white")
    self.forms_table_frame.grid(row=6, column=4, columnspan=7, rowspan=6, sticky="nsew")
    self.forms_table_frame.grid_rowconfigure(0, weight=1)
    self.forms_table_frame.grid_columnconfigure(0, weight=1)

    self.scrollbar_x = ttk.Scrollbar(self.forms_table_frame, orient="horizontal")
    self.scrollbar_y = ttk.Scrollbar(self.forms_table_frame, orient="vertical")
    
    self.formsTable = ttk.Treeview(self.forms_table_frame, columns=("Id", "Points"), show="headings", xscrollcommand=self.scrollbar_x.set, yscrollcommand=self.scrollbar_y.set)
    
    self.formsTable.heading("Id", text="Id")
    self.formsTable.heading("Points", text="Points")
    self.formsTable.column("Id", width=50, anchor="center", stretch=tk.NO)
    self.formsTable.column("Points", width=400, anchor="w", stretch=tk.YES)

    self.scrollbar_x.config(command=self.formsTable.xview)
    self.scrollbar_y.config(command=self.formsTable.yview)

    self.max_points_width = 400

    self.formsTable.grid(row=0, column=0, sticky="nsew")
    self.scrollbar_y.grid(row=0, column=1, sticky="ns")
    self.scrollbar_x.grid(row=1, column=0, sticky="ew")
    
    self.forms_table_frame.grid_propagate(False)
    self.formsTable.bind("<Button-3>", self.on_table_right_click)
    self.formsTable.pack(fill=tk.BOTH, expand=True, pady=10)

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
    # self.root.bind("<KeyPress-h>", lambda e: self.camera.rotate_left() or self.update())

  def canva_click(self, event):
    if self.building: self.build.append(self.camera.viewport_to_world(event.x, event.y))
    else:  self.objects.append(PointObject("Clicked Point", self.camera.viewport_to_world(event.x, event.y), id=10*len(self.objects)+1))
    self.update()

  def finish_lines(self):
    if len(self.build) < 2: 
      print("Erro: Pelo menos dois pontos são necessários para formar uma linha.")
      messagebox.showerror("Erro", "Pelo menos dois pontos são necessários para formar uma linha.")
      return
    for i in range(len(self.build) - 1):
      start, end = self.build[i:i+2]
      self.objects.append(LineObject(f"Line {i+1}", start, end, id=10*len(self.objects)+1))

    self.build.clear()
    self.building = False
    self.update()

  def finish_polygon(self):
    if len(self.build) < 3: 
      print("Erro: Pelo menos três pontos são necessários para formar um polígono.")
      messagebox.showerror("Erro", "Pelo menos três pontos são necessários para formar um polígono.")
      return
    
    self.objects.append(PolygonObject("Polygon", self.build.copy(), id=10*len(self.objects)+1))
    self.build.clear()
    self.building = False
    self.update()

  def update(self):        
    self.canva.delete("all")
    all_objects = self.objects.copy()
    
    if self.debug: all_objects += self.debug_objects
    
    for obj in all_objects:
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
          
          # Draw line
          if edge.end is not None:
            start, end = self.camera.world_to_viewport(edge.start), self.camera.world_to_viewport(edge.end)
            self.canva.create_line(start[0], start[1], end[0], end[1], fill=obj.color)
          
          # Draw point
          else:
            point = self.camera.world_to_viewport(edge.start)
            radius = obj.radius
            self.canva.create_oval(point[0] - radius, point[1] - radius, point[0] + radius, point[1] + radius, fill=obj.color)
    
    self.formsTable.delete(*self.formsTable.get_children())
    for obj in self.objects:
      self.add_object_to_table(obj)

    prev = None
    for point in self.build:
      point = self.camera.world_to_viewport(point)
      self.canva.create_oval(point[0] - 2, point[1] - 2, point[0] + 2, point[1] + 2, fill="red")
      if prev is not None: self.canva.create_line(prev[0], prev[1], point[0], point[1], fill="red")
      prev = point
    
    # Draw axes
    if self.debug:
      self.canva.create_line(0, self.height*0.4, self.width, self.height*0.4, fill="blue")
      self.canva.create_line(self.width*0.4, 0, self.width*0.4, self.height, fill="blue")

  def run(self) -> list[Wireframe]:
    self.root.mainloop()
    if self.output:
      try:
        with open(self.output, "w") as file:
          for obj in self.objects:
            file.write(f"{obj}\n")
      except Exception as e:
        print(f"Erro ao salvar objetos: {e}")
        messagebox.showerror("Erro", f"Erro ao salvar objetos: {e}")
    return self.objects
  
  def add_object_to_table(self, obj: Wireframe):
    formatted_coordinates = [f"({', '.join(f'{coord:.2f}' for coord in point)})" for point in obj.points]
    self.formsTable.insert("", "end", values=(obj.name, ", ".join(formatted_coordinates)), tags=(str(obj.id),))

    font_style = font.nametofont("TkDefaultFont")
    font_size = font_style.measure("".join(formatted_coordinates)) + 20
    
    if font_size > self.max_points_width:
      self.formsTable.column("Points", width=font_size+20, anchor="w", stretch=tk.NO)
      self.formsTable.update_idletasks()
      self.formsTable.xview_moveto(0) # Reset horizontal scroll position
    self.max_points_width = max(self.max_points_width, font_size) 

  def on_table_right_click(self, event):
    item = self.formsTable.identify_row(event.y)
    if not item: return
    item_id = self.formsTable.item(item, "values")[0]

    if messagebox.askyesno("Deletar objeto", f"Deletar objeto {item_id}?"):
      self.formsTable.delete(item)
      self.objects = [obj for obj in self.objects if str(obj.id) != item_id]
      self.update()
      
  def change_point_color(self):
    selected_item = self.formsTable.selection()
    
    if not selected_item:
      messagebox.showwarning("Aviso", "Nenhum objeto selecionado.")
      return
    
    item_id = self.formsTable.item(selected_item[0], "tags")[0]
    for obj in self.objects:
      if str(obj.id) == item_id:
        color = colorchooser.askcolor(title="Escolha a cor do ponto")
        if color[1]:
          obj.color = color[1]
          self.update()
        break

  def change_point_radius(self):
    selected_item = self.formsTable.selection()
    if not selected_item:
      messagebox.showwarning("Aviso", "Nenhum objeto selecionado.")
      return

    item_id = self.formsTable.item(selected_item[0], "tags")[0]
    for obj in self.objects:
      if str(obj.id) == item_id:
        obj.radius = simpledialog.askfloat("Raio do Ponto", "Digite o novo raio do ponto:", minvalue=1, maxvalue=100, initialvalue=obj.radius) or 0.0
        if obj.radius is not None:
          self.update()
          break

  def change_line_color(self):
    selected_item = self.formsTable.selection()
    if not selected_item:
      messagebox.showwarning("Aviso", "Nenhum objeto selecionado.")
      return

    item_id = self.formsTable.item(selected_item[0], "tags")[0]
    for obj in self.objects:
      if str(obj.id) == item_id:
        color = colorchooser.askcolor(title="Escolha a cor da linha")
        if color[1]:
          obj.color = color[1]
          self.update()
        break

  def change_fill_color(self):    
    selected_item = self.formsTable.selection()
 
    if not selected_item:
      messagebox.showwarning("Aviso", "Nenhum objeto selecionado.")
      return
    item_id = self.formsTable.item(selected_item[0], "tags")[0]

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
      print(f"Arquivo {objects} não encontrado.")
      messagebox.showerror("Erro", f"Arquivo {objects} não encontrado.")
      return []
    except Exception as e:
      print(f"Erro ao carregar objetos: {e}")
      messagebox.showerror("Erro", f"Erro ao carregar objetos: {e}")
      return []

  def undo(self):
    if self.building:
      if self.build: self.build.pop()
      else: self.building = False
    elif self.objects:
      self.objects.pop()
    self.update()

  @property
  def building(self) -> bool: return self._building

  @building.setter
  def building(self, value: bool):
    self._building = value
