import tkinter as tk
from tkinter import ttk, colorchooser, scrolledtext

import json

from viewport import *
from logger import logging
from config import USER_PREFERENCES_PATH

class SGI:
  def __init__(
    self,
    title: str,
    input_file: str,
    output_file: str,
    width: int,
    height: int,
    curve_type: int,
    curve_coefficient: int,
    debug: bool,
    window_zoom: float,
    window_position: list[float],
    window_normal: list[float],
    window_focus: list[float],
    window_up: list[float],
    window_movement_speed: int,
    window_rotation_speed: int,
    window_padding: int,
    line_clipping_algorithm: int,
    projection_type: int
  ):
    self.width: int = width
    self.height: int = height
    self.input_file: str | None = input_file
    self.output_file: str | None = output_file
    self.debug: bool = debug
    self.window_position: list[float] = window_position
    self.window_normal: list[float] = window_normal
    self.window_focus: list[float] = window_focus
    self.projection_type: int = projection_type
    self.window_up: list[float] = window_up
    self.window_movement_speed: int = window_movement_speed
    self.window_rotation_speed: int = window_rotation_speed
    self.window_padding: int = window_padding
    self.window_zoom: float = window_zoom

    # GUI
    self.root = tk.Tk()
    self.set_up_root(title)

    ## The *line_clipping_algorithm* and *curve_type* variables will be also passed to the Viewport class
    ## This means that changing them here will change them in the Viewport class too
    self.line_clipping_algorithm = tk.IntVar(value=line_clipping_algorithm)
    self.curve_type = tk.IntVar(value=curve_type)
    self.curve_coefficient = tk.IntVar(value=curve_coefficient)

    self.create_components()
    self.create_navbar()
    self.position_components()
    self.controls()
  
# Main window and components setup
  def set_up_root(self, title: str):
    self.root.title(title)
    self.root.resizable(False, False)

  def create_navbar(self):
    self.navbar = tk.Menu(self.root)

    # Arquivo menu
    file_menu = tk.Menu(self.navbar, tearoff=0)
    file_menu.add_command(label="Limpar tela", command=self.viewport.clear)
    file_menu.add_command(label="Recentralizar", command=self.viewport.recenter)
    file_menu.add_command(label="Sair", command=self.root.quit)

    # Configurações menu
    settings_menu = tk.Menu(self.navbar, tearoff=0)
    clipping_submenu = tk.Menu(settings_menu, tearoff=0)
    curve_submenu = tk.Menu(settings_menu, tearoff=0)

    clipping_submenu.add_radiobutton(label="Cohen-Sutherland", value=0, variable=self.line_clipping_algorithm)
    clipping_submenu.add_radiobutton(label="Liang-Barsky", value=1, variable=self.line_clipping_algorithm)
    curve_submenu.add_radiobutton(label="Bézier", value=0, variable=self.curve_type)
    curve_submenu.add_radiobutton(label="B-Spline", value=1, variable=self.curve_type)
    curve_submenu.add_command(label="Grau de continuidade", command=lambda: (
      popup := self.popup(250, 100, "Grau de continuidade"),
      tk.Label(popup, text="Grau de continuidade:").pack(),
      input := tk.Entry(popup),
      input.insert(0, str(self.curve_coefficient.get())),
      input.pack(),
      tk.Button(popup, text="Aplicar", command=lambda: (
        self.curve_coefficient.set(int(input.get())) if input.get().isnumeric() and int(input.get()) > 0 else None,
        popup.destroy()
      )).pack(),
    ))

    settings_menu.add_cascade(label="Algoritmo de Recorte", menu=clipping_submenu)
    settings_menu.add_cascade(label="Curvas", menu=curve_submenu)

    self.navbar.add_cascade(label="Arquivo", menu=file_menu)
    self.navbar.add_cascade(label="Configurações", menu=settings_menu)
    self.root.config(menu=self.navbar)

  # TODO: The creation of components is in a completly messy order,
  # Many elements need to be created upfront so they can be passed to other components
  # This should be at the very least better organized and hopefully simplified
  def create_components(self):
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
    # Canva
    self.canva = tk.Canvas(self.root, background="white", width=self.width, height=self.height)
    self.viewport = Viewport(
      self.canva,
      self.log,
      self.ui_object_list,
      self.input_file,
      self.output_file,
      self.width,
      self.height,
      self.curve_type,
      self.curve_coefficient,
      self.debug,
      self.window_position,
      self.window_normal,
      self.window_focus,
      self.window_up,
      self.window_movement_speed,
      self.window_rotation_speed,
      self.window_padding,
      self.window_zoom,
      self.line_clipping_algorithm,
      self.projection_type
    )

    # Log session
    # TODO: This needs to be created before the viewport so that the viewport can use the log function
    self.ui_log = scrolledtext.ScrolledText(self.root, bg="white", fg="black", state="disabled", font=("Arial", 10), height=9)

    # Control buttons and input fields
    self.ui_build_button = tk.Button(self.root, text="Build", command=self.toggle_building)
    self.ui_close_polygon_button = tk.Button(self.root, text="Polígono", command=self.finish_polygon)
    self.ui_create_curve_button = tk.Button(self.root, text="Curva", command=self.finish_curve)
    self.ui_object_properties_button = tk.Button(self.root, text="Propriedades", command=self.properties_window) # also on mouse right click on object at table
    self.ui_rotate_x_button = tk.Button(self.root, text="Girar X", command=lambda:self.rotate_selected_object(a1=1, a2=2))
    self.ui_rotate_y_button = tk.Button(self.root, text="Girar Y", command=lambda:self.rotate_selected_object(a1=0, a2=2))
    self.ui_rotate_z_button = tk.Button(self.root, text="Girar Z", command=lambda:self.rotate_selected_object(a1=0, a2=1))

    self.ui_translate_object_button = tk.Button(self.root, text="Deslocar", command=self.translate_selected_object)
    self.ui_scale_button = tk.Button(self.root, text="Escalar", command=self.scale_selected_object)

    self.ui_point_label = tk.Label(self.root, text="Ponto (x,y,z):")
    self.ui_point_x_input = tk.Entry(self.root, width=10)
    self.ui_point_y_input = tk.Entry(self.root, width=10)
    self.ui_point_z_input = tk.Entry(self.root, width=10)

    self.ui_degree_label = tk.Label(self.root, text="Ângulo:")
    self.ui_degree_var = tk.StringVar(value="Ângulo")
    self.ui_degree_input = tk.Entry(self.root)
    self.ui_scale_factor_label = tk.Label(self.root, text="Fator:")
    self.ui_scale_factor_var = tk.StringVar(value="Fator")
    self.ui_scale_factor_input = tk.Entry(self.root)

    scrollbar_x.config(command=self.ui_object_list.xview)
    scrollbar_y.config(command=self.ui_object_list.yview)
    self.ui_object_list.heading("Id", text="Id")
    self.ui_object_list.heading("Points", text="Points")
    self.ui_object_list.column("Id", width=100, anchor="center", stretch=tk.NO)
    self.ui_object_list.column("Points", anchor="w", stretch=tk.YES)

    self.ui_object_list.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, rowspan=2, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")

  def position_components(self):
    self.canva.grid(row=0, column=4, columnspan=8, rowspan=20, sticky="nsew")
    self.ui_log.grid(row=20, column=4, columnspan=12, rowspan=4, sticky="nsew")

    self.ui_object_list_frame.grid(row=0, column=0, rowspan=12, columnspan=4, sticky="nsew")

    self.ui_build_button.grid(row=12, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_close_polygon_button.grid(row=12, column=2, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_create_curve_button.grid(row=12, column=3, rowspan=1, columnspan=1, sticky="nsew")


    self.ui_translate_object_button.grid(row=13, column=0, rowspan=1, columnspan=3, sticky="nsew")
    self.ui_scale_button.grid(row=13, column=3, rowspan=1, columnspan=1, sticky="nsew")

    self.ui_rotate_x_button.grid(row=14, column=0, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_rotate_y_button.grid(row=14, column=1, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_rotate_z_button.grid(row=14, column=3, rowspan=1, columnspan=1, sticky="nsew")
    
    self.ui_object_properties_button.grid(row=18, column=0, rowspan=1, columnspan=4, sticky="nsew")

    self.ui_point_label.grid(row=15, column=0, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_point_x_input.grid(row=15, column=1, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_point_y_input.grid(row=15, column=2, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_point_z_input.grid(row=15, column=3, rowspan=1, columnspan=1, sticky="nsew")

    self.ui_degree_label.grid(row=16, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_degree_input.grid(row=16, column=2, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_scale_factor_label.grid(row=17, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_scale_factor_input.grid(row=17, column=2, rowspan=1, columnspan=2, sticky="nsew")

  def controls(self):
    self.canva.bind("<ButtonRelease-1>", self.viewport.canva_click)
    self.canva.bind("<Button-3>", self.viewport.move_window)
    self.root.bind("<Button-2>", lambda e: self.viewport.toggle_debug())
    self.root.bind("<Button-4>", lambda e: self.viewport.window.zoom_in(e.x, e.y) or self.viewport.update())
    self.root.bind("<Button-5>", lambda e: self.viewport.window.zoom_out(e.x, e.y) or self.viewport.update())
    # Camera navegation
    self.root.bind("<KeyPress-w>", lambda e: self.viewport.window.move_upward() or self.viewport.update())
    self.root.bind("<KeyPress-s>", lambda e: self.viewport.window.move_downward() or self.viewport.update())
    self.root.bind("<KeyPress-a>", lambda e: self.viewport.window.move_sideways_right() or self.viewport.update())
    self.root.bind("<KeyPress-d>", lambda e: self.viewport.window.move_sideways_left() or self.viewport.update())
    self.root.bind("<KeyPress-q>", lambda e: self.viewport.window.move_forward() or self.viewport.update())
    self.root.bind("<KeyPress-e>", lambda e: self.viewport.window.move_backward() or self.viewport.update())
    # Camera rotation
    self.root.bind("<KeyPress-r>", lambda e: self.viewport.window.rotate(a1=1, a2=2, angle=self.window_rotation_speed) or self.viewport.update())
    self.root.bind("<KeyPress-t>", lambda e: self.viewport.window.rotate(a1=1, a2=2, angle=-self.window_rotation_speed) or self.viewport.update())
    self.root.bind("<KeyPress-f>", lambda e: self.viewport.window.rotate(a1=0, a2=2, angle=self.window_rotation_speed) or self.viewport.update())
    self.root.bind("<KeyPress-g>", lambda e: self.viewport.window.rotate(a1=0, a2=2, angle=-self.window_rotation_speed) or self.viewport.update())
    self.root.bind("<KeyPress-v>", lambda e: self.viewport.window.rotate(a1=0, a2=1, angle=self.window_rotation_speed) or self.viewport.update())
    self.root.bind("<KeyPress-b>", lambda e: self.viewport.window.rotate(a1=0, a2=1, angle=-self.window_rotation_speed) or self.viewport.update())
    
    # Extras
    self.root.bind("<KeyPress-Escape>", lambda e: self.cancel_building())
    self.root.bind("<Control-z>", lambda e: self.viewport.undo())

    self.ui_object_list.bind("<Button-3>", lambda e: self.properties_window())

    # This one is not a control. It's used to remove focus from a text input when clicking outside of it
    def focus_clicked_widget(event):
      # TODO: There has to be a better way to avoid errors when clicking on certain widgets
      try: event.widget.focus_set()
      except: pass
    # TODO: Stop object list from unselecting whenever another widget is clicked
    self.root.bind_all("<Button-1>", focus_clicked_widget)    

# Main loop and exit
  def run(self) -> list[Wireframe]:
    self.root.mainloop()
    # Save current state
    with open(USER_PREFERENCES_PATH, "w") as f:
      json.dump({
        "window_position": self.viewport.window.position.tolist(),
        "window_normal": self.viewport.window.normal.tolist(),
        "window_focus": self.viewport.window.focus.tolist(),
        "window_up": self.viewport.window.up.tolist(),
        "window_zoom": self.viewport.window.zoom,
        "line_clipping_algorithm": self.line_clipping_algorithm.get(),
        "curve_type": self.curve_type.get(),
        "curve_coefficient": self.curve_coefficient.get(),
        "debug": self.viewport.debug,
      }, f, indent=2)

    # Save objects to output file if specified
    if self.output_file:
      try:
        self.viewport.save_objects(self.output_file)
      except Exception as e:
          logging.error(f"Erro ao salvar objetos: {e}")
    return self.viewport.objects

  @staticmethod
  def popup(width: int, height: int, title: str) -> tk.Toplevel:
    popup = tk.Toplevel()
    popup.title(title)
    popup.minsize(width, height)
    popup.resizable(False, False)
    return popup

# Additional Windows
  def properties_window(self):
    target = self.get_selected_object()
    if target is None: return
    popup = self.popup(0, 300, "Propriedades do Objeto")
    def apply_changes(name, texture):
      target.name = name.get().strip() if name.get().strip() != "" else target.name
      for i, face in enumerate(target.faces):
        target.faces[i] = (face[0], texture.strip() if texture.strip() != "" else face[1])

      self.viewport.update()
      popup.destroy()

    # Name
    name_label = tk.Label(popup, text="Nome do objeto:")
    name_input = tk.Entry(popup)
    name_input.insert(0, target.name)
    name_label.grid(row=0, column=0, sticky="ew")
    name_input.grid(row=0, column=1, columnspan=2, sticky="ew")

    
    # Fill Color
    texture_label = tk.Label(popup, text="Cor das faces:")
    texture_input = tk.Entry(popup)
    texture_input.insert(0, target.faces[0][1] if len(target.faces) > 0 and target.faces[0][1] else "")
    texture_button = tk.Button(popup, text="Escolher", command=lambda: (
      color := colorchooser.askcolor(title="Escolha a cor de preenchimento"),
      texture_input.delete(0, tk.END),
      texture_input.insert(0, color[1]) if color[1] else None
    ))
    texture_label.grid(row=2, column=0, sticky="ew")
    texture_input.grid(row=2, column=1, sticky="ew")
    texture_button.grid(row=2, column=2, sticky="ew")
  

    # Apply Button
    apply_button = tk.Button(popup, text="Aplicar", command=lambda: apply_changes(name_input, texture_input.get()))
    cancel_button = tk.Button(popup, text="Cancelar", command=popup.destroy)
    apply_button.grid(row=4, column=0, columnspan=4, sticky="ew")
    cancel_button.grid(row=5, column=0, columnspan=4, sticky="ew")

  def add_polygon_window(self):
    popup = self.popup(0, 300, "Adicionar Polígono")
    def finish_polygon_callback():
      name = name_input.get().strip() if name_input.get().strip() != "" else "Polygon"
      points = points_input.get().strip("(").strip(")").replace(" ", "").split("),(")
      try: points = [list(map(float, p.split(','))) for p in points]
      except ValueError:
        self.log("Erro: pontos inválidos.")
        return
      if len(points) < 3:
        self.log("Erro: insira ao menos 3 pontos.")
        return
      points = [np.append(np.array(p), 1.0) for p in points]

      try: thickness = int(thickness_input.get())
      except ValueError: thickness = 1
      line_color = line_color_input.get().strip() if line_color_input.get().strip() != "" else "#000000"
      texture = texture_input.get().strip() if texture_input.get().strip() != "" else "#ffffff"
      self.viewport.add_polygon(points, name, line_color, texture, thickness)
      popup.destroy()
    
    name_label = tk.Label(popup, text="Nome do objeto:")
    name_input = tk.Entry(popup)
    name_input.insert(0, "Polygon")
    name_label.grid(row=0, column=0, sticky="ew")
    name_input.grid(row=0, column=1, columnspan=2, sticky="ew")

    points_label = tk.Label(popup, text="Pontos (x0,y0,z0),(x1,y1,z1),...,(xN,yN,zN):")
    points_input = tk.Entry(popup)
    points_label.grid(row=1, column=0, sticky="ew")
    points_input.grid(row=1, column=1, columnspan=2, sticky="ew")

    line_color_label = tk.Label(popup, text="Cor de contorno:")
    line_color_input = tk.Entry(popup)
    line_color_input.insert(0, "#000000")
    line_color_button = tk.Button(popup, text="Escolher", command=lambda: (
      color := colorchooser.askcolor(title="Escolha a cor da linha"),
      line_color_input.delete(0, tk.END),
      line_color_input.insert(0, color[1]) if color[1] else None
    ))
    line_color_label.grid(row=2, column=0, sticky="ew")
    line_color_input.grid(row=2, column=1, sticky="ew")
    line_color_button.grid(row=2, column=2, sticky="ew")

    texture_label = tk.Label(popup, text="Cor de preenchimento:")
    texture_input = tk.Entry(popup)
    texture_input.insert(0, "#ffffff")
    texture_button = tk.Button(popup, text="Escolher", command=lambda: (
      color := colorchooser.askcolor(title="Escolha a cor de preenchimento"),
      texture_input.delete(0, tk.END),
      texture_input.insert(0, color[1]) if color[1] else None
    ))
    texture_label.grid(row=3, column=0, sticky="ew")
    texture_input.grid(row=3, column=1, sticky="ew")
    texture_button.grid(row=3, column=2, sticky="ew")

    thickness_label = tk.Label(popup, text="Espessura da linha:")
    thickness_input = tk.Entry(popup)
    thickness_input.insert(0, "1")
    thickness_label.grid(row=4, column=0, sticky="ew")
    thickness_input.grid(row=4, column=1, columnspan=2, sticky="ew")

    create_button = tk.Button(popup, text="Criar Polígono", command=finish_polygon_callback)
    create_button.grid(row=5, column=0, columnspan=3, sticky="ew")

    cancel_button = tk.Button(popup, text="Cancelar", command=popup.destroy)
    cancel_button.grid(row=6, column=0, columnspan=3, sticky="ew")

  def add_curve_window(self):
    popup = self.popup(0, 200, "Adicionar Curva")
    
    def finish_curve_callback():
      control_points = points_input.get().strip("(").strip(")").replace(" ", "").split("),(")
      try: control_points = [list(map(float, p.split(','))) for p in control_points]
      except ValueError:
        self.log("Erro: pontos inválidos.")
        return
      control_points = [np.append(np.array(p), 1.0) for p in control_points]

      if len(control_points) < 2:
        self.log("Erro: insira ao menos 2 pontos de controle.")
        return

      self.viewport.add_curve(control_points, name_input.get(), line_color_input.get().strip())
      popup.destroy()

    name_label = tk.Label(popup, text="Nome do objeto:")
    name_input = tk.Entry(popup)
    name_input.insert(0, "Curve")
    name_label.grid(row=0, column=0, sticky="ew")
    name_input.grid(row=0, column=1, columnspan=2, sticky="ew")

    points_label = tk.Label(popup, text="Pontos de controle (x0,y0),(x1,y1),...,(xN,yN):")
    points_input = tk.Entry(popup)
    points_label.grid(row=1, column=0, sticky="ew")
    points_input.grid(row=1, column=1, columnspan=2, sticky="ew")

    line_color_label = tk.Label(popup, text="Cor da linha:")
    line_color_input = tk.Entry(popup)
    line_color_input.insert(0, "#000000")
    line_color_button = tk.Button(popup, text="Escolher", command=lambda: (
      color := colorchooser.askcolor(title="Escolha a cor da linha"),
      line_color_input.delete(0, tk.END),
      line_color_input.insert(0, color[1]) if color[1] else None
    ))
    line_color_label.grid(row=2, column=0, sticky="ew")
    line_color_input.grid(row=2, column=1, sticky="ew")
    line_color_button.grid(row=2, column=2, sticky="ew")

    create_button = tk.Button(popup, text="Criar Curva", command=finish_curve_callback)
    cancel_button = tk.Button(popup, text="Cancelar", command=popup.destroy)
    create_button.grid(row=3, column=0, columnspan=3, sticky="ew")
    cancel_button.grid(row=4, column=0, columnspan=3, sticky="ew")

# Instance attributes control
  def toggle_building(self):
    self.viewport.toggle_building()
    self.ui_build_button.config(relief=tk.SUNKEN if self.viewport.building else tk.RAISED)

  def cancel_building(self):
    self.ui_build_button.config(relief=tk.RAISED)
    self.viewport.cancel_building()

# Utilities
  def log(self, *message: str):
    '''Writes *message* to the log widget'''
    '''In the future, there could be different log levels'''
    self.ui_log.config(state="normal")
    self.ui_log.insert(tk.END, f"{''.join([str(m) for m in message])}\n")
    self.ui_log.see(tk.END)
    self.ui_log.config(state="disabled")

# Wrappers for viewport methods
  def finish_polygon(self):
    if self.viewport.building:
      self.ui_build_button.config(relief=tk.RAISED)
      self.viewport.finish_polygon()
    else:
      self.add_polygon_window()

  def finish_curve(self):
    if self.viewport.building:
      self.ui_build_button.config(relief=tk.RAISED)
      self.viewport.finish_curve()
    else:
      self.add_curve_window()
  
  def get_selected_object(self, log=True) -> Wireframe | None:
    selected = self.ui_object_list.selection()
    if not selected:
      if log: self.log("Nenhum objeto selecionado.")
      return None
    item_id = int(self.ui_object_list.item(selected[0])['tags'][0])
    target = next((obj for obj in self.viewport.objects if obj.wireframe_id == item_id), None)
    if target is None:
      if log: self.log("Objeto não encontrado.")
      return None
    return target

  def rotate_selected_object(self, a1: int=0, a2: int=1):
    angle = self.ui_degree_input.get()
    # If the angle_input is invalid, rotate 15 degrees by default
    # Otherwise, rotate by the specified angle
    if angle and angle.strip("-").isnumeric():
      angle = int(angle)
    elif not angle:
      angle = 15
    else:
      self.log("Erro: Ângulo inválido. Rotacionando 15° por padrão.")
      angle = 15

    match self.get_selected_object(log=False):
      # If no target is selected, rotate window
      case None: self.viewport.window.rotate(angle, a1, a2)
      # Rotate selected object
      case target:
        # If no valid point is specified, rotate around object's center
        # Otherwise, rotate around specified point
        rx = self.ui_point_x_input.get()
        ry = self.ui_point_y_input.get()
        rz = self.ui_point_z_input.get()
        try:
          rx = float(rx)
          ry = float(ry)
          rz = float(rz)
          point = np.array([rx, ry, rz, 1.0])
          target.rotate(angle, point, a1, a2)
        except ValueError:
          target.rotate(angle, None, a1, a2)

    self.viewport.update()

  def translate_selected_object(self):
    target = self.get_selected_object()
    if target is None: return
    dx = self.ui_point_x_input.get()
    dy = self.ui_point_y_input.get()
    dz = self.ui_point_z_input.get()
    try: dx = int(dx)
    except ValueError: dx = 0
    try: dy = int(dy)
    except ValueError: dy = 0
    try: dz = int(dz)
    except ValueError: dz = 0

    if dx == 0 and dy == 0 and dz == 0: return

    target.translate(dx, dy, dz)
    self.viewport.update()

  def scale_selected_object(self):
    target = self.get_selected_object()
    if target is None: return
    s = self.ui_scale_factor_input.get()
    if s and s.replace(".", "").replace(",", "").isnumeric():
      s = float(s.replace(",", "."))
    else:
      self.log("Erro: Valores de escala inválidos.")
      return
    target.scale(s)
    self.viewport.update()
    