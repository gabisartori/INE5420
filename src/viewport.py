import tkinter as tk
from tkinter import ttk, messagebox, font, colorchooser
from wireframe import *
from screen import *

class Viewport:
  def __init__(self, width, height, title="INE5420", input: str="", output: str="", debug: bool=False):
    self.output: str = output
    
    self.width: int = width
    self.height: int = height
    self.objects: list[Wireframe] = self.load_objects(input)
    self.build: list[Point] = []
    self._building: bool = False

    self.debug: bool = debug
    self.debug_objects: list[Wireframe] = [PointObject("World Origin", np.array([0, 0, 0]), id=0)]
    self.camera = Camera(np.array([0, -1, 0]), np.array([0, 100, 0]), width*0.8, height*0.8)

    # Ui Componentes
    self.root: tk.Tk = tk.Tk()
    #self.root.geometry(f"{width}x{height}")
    self.root.title(title)
    self.canva = tk.Canvas(self.root, background="white", width=0.8 * self.width, height=0.8 * self.height)
    
    self.build_button = tk.Button(self.root, text="Build", command=self.set_building)
    self.lines_button = tk.Button(self.root, text="Lines", command=self.finish_lines)
    self.polygon_button = tk.Button(self.root, text="Polygon", command=self.finish_polygon)
    self.clear_button = tk.Button(self.root, text="Clear", command=self.clear)
    self.recenter_button = tk.Button(self.root, text="Recenter", command=lambda: self.camera.recenter() or self.update())
    self.m00_value = tk.StringVar()
    self.m01_value = tk.StringVar()
    self.m10_value = tk.StringVar()
    self.m11_value = tk.StringVar()
    self.m00_input = tk.Entry(self.root, textvariable=self.m00_value, width=5)
    self.m01_input = tk.Entry(self.root, textvariable=self.m01_value, width=5)
    self.m10_input = tk.Entry(self.root, textvariable=self.m10_value, width=5)
    self.m11_input = tk.Entry(self.root, textvariable=self.m11_value, width=5)
    self.apply_transform_button = tk.Button(self.root, text="Apply Transform", command=self.apply_transform)
    
    self.change_line_color_button = tk.Button(self.root, text="Line Color", command=self.change_line_color)
    self.change_fill_color_button = tk.Button(self.root, text="Fill Color", command=self.change_fill_color)
    self.change_point_color_button = tk.Button(self.root, text="Point Color", command=self.change_point_color)
    self.change_point_radius_button = tk.Button(self.root, text="Point Radius", command=self.change_point_radius)

    self.build_forms_table()
    self.controls()
    self.build_ui()
    self.setup_grid()
    self.update()

  def setup_grid(self):
    for i in range(10):
      self.root.grid_rowconfigure(i, weight=1)
      self.root.grid_columnconfigure(i, weight=1)

    self.root.resizable(False, False) # redimensionar travado

  def apply_transform(self):
    try:
      m00 = float(self.m00_value.get())
      m01 = float(self.m01_value.get())
      m10 = float(self.m10_value.get())
      m11 = float(self.m11_value.get())
      self.camera.transform_matrix = np.array([[m00, m01], [m10, m11]])
      self.update()
    except ValueError:
      print("Erro: Valores inválidos para a matriz de transformação.")

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
    self.canva.grid(row=0, column=0, columnspan=4, rowspan=10, sticky="nsew")
    
    self.build_button.grid(row=11, column=0, sticky="ew")
    self.lines_button.grid(row=11, column=1, sticky="ew")
    self.polygon_button.grid(row=11, column=2, sticky="ew")
    self.clear_button.grid(row=11, column=3, sticky="ew")
    self.recenter_button.grid(row=0, column=5, columnspan=3)

    self.m00_input.grid(row=1, column=5, sticky="ew")
    self.m01_input.grid(row=1, column=6, sticky="ew")
    self.m10_input.grid(row=2, column=5, sticky="ew")
    self.m11_input.grid(row=2, column=6, sticky="ew")
    self.apply_transform_button.grid(row=3, column=5, columnspan=2, sticky="ew")
    
    self.change_fill_color_button.grid(row=4, column=5, sticky="ew")
    self.change_line_color_button.grid(row=4, column=6, sticky="ew")
    self.change_point_color_button.grid(row=5, column=5, sticky="ew")
    self.change_point_radius_button.grid(row=5, column=6, sticky="ew")

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
    else: 
      self.objects.append(PointObject("Clicked Point", self.camera.viewport_to_world(event.x, event.y), id=10*len(self.objects)+1))
      self.add_object_to_table(self.objects[-1])
    self.update()

  def finish_lines(self):
    if len(self.build) < 2: 
      print("Erro: Pelo menos dois pontos são necessários para formar uma linha.")
      messagebox.showerror("Erro", "Pelo menos dois pontos são necessários para formar uma linha.")
      return
    for i in range(len(self.build) - 1):
      start, end = self.build[i:i+2]
      self.objects.append(LineObject(f"Line {i+1}", start, end, id=10*len(self.objects)+1))
    self.add_object_to_table(self.objects[-1])
    self.build.clear()
    self.building = False
    self.update()

  def finish_polygon(self):
    if len(self.build) < 3: 
      print("Erro: Pelo menos três pontos são necessários para formar um polígono.")
      messagebox.showerror("Erro", "Pelo menos três pontos são necessários para formar um polígono.")
      return
    
    self.objects.append(PolygonObject("Polygon", self.build.copy(), id=10*len(self.objects)+1))
    self.add_object_to_table(self.objects[-1])
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
          start, end = self.camera.project(edge.start), self.camera.project(edge.end)
          self.canva.create_line(start[0], start[1], end[0], end[1], fill=obj.color)
        # Fill polygon
        if obj.fill_color:
          projected_points = [self.camera.project(edge.start) for edge in figures]
          # fecha o poligono se necessario
          if not np.array_equal(projected_points[0], projected_points[-1]):
              projected_points.append(projected_points[0])

          points = [coord for point in projected_points for coord in point]
          if len(points) >= 6:  # Verifica se há pelo menos 3 pontos
            # Desenha o polígono preenchido
            self.canva.create_polygon(points, fill=obj.fill_color, outline=obj.color)

      else:
        for edge in figures:
          # Draw line
          if edge.end is not None:
            start, end = self.camera.project(edge.start), self.camera.project(edge.end)
            self.canva.create_line(start[0], start[1], end[0], end[1], fill=obj.color)
          # Draw point
          else:
            point = self.camera.project(edge.start)
            self.canva.create_oval(point[0] - 2, point[1] - 2, point[0] + 2, point[1] + 2, fill=obj.color)
    prev = None
    for point in self.build:
      point = self.camera.project(point)
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
    pass

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
