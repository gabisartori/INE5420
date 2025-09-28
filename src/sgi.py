import tkinter as tk
from tkinter import ttk, font, colorchooser, simpledialog, scrolledtext

from viewport import *
from wireframe import *
from window import *
from components.my_types import *
from clipping import *
import config

class SGI:
  def __init__(
    self,
    width: int=config.WIDTH, 
    height: int=config.HEIGHT, 
    title: str=config.APPLICATION_NAME, 
    input: str | None=config.INPUT_FILE, 
    output: str | None=config.OUTPUT_FILE, 
    debug: bool=config.DEBUG
  ):
    # Config
    self.width: int = width
    self.height: int = height
    self.input_file: str | None = input
    self.output_file: str | None = output
    self.debug: bool = debug

    # TODO: This data must be handled by the Viewport class
    # Functionality attributes
    self.building_buffer: list[Point] = []
    self.building: bool = False
    self.id_counter: int = 0

    # GUI
    self.root = tk.Tk()
    self.set_up_root(title)
    self.create_components()
    self.create_navbar()
    self.position_components()
    self.controls()
  
  def set_up_root(self, title: str):
    self.root.title(title)
    self.root.geometry(f"{self.width}x{self.height}")
    self.root.resizable(False, False)
    self.root.protocol("WM_DELETE_WINDOW", self.exit)

  def create_navbar(self):
    self.navbar = tk.Menu(self.root)

    # Arquivo menu
    file_menu = tk.Menu(self.navbar, tearoff=0)
    file_menu.add_command(label="Limpar tela", command=self.viewport.clear)
    file_menu.add_command(label="Recentralizar", command=self.viewport.recenter)
    file_menu.add_command(label="Sair", command=self.exit)

    # Configurações menu
    settings_menu = tk.Menu(self.navbar, tearoff=0)
    clipping_submenu = tk.Menu(settings_menu, tearoff=0)
    curve_submenu = tk.Menu(settings_menu, tearoff=0)

    ## The *clipping_algorithm* and *curve_type* variables will be also passed to the Viewport class
    ## Hopefully, this means that changing them here will change them in the Viewport class too
    clipping_algorithm = tk.IntVar(value=config.DEFAULT_CLIPPING_ALGORITHM)
    curve_type = tk.IntVar(value=config.DEFAULT_CURVE_TYPE)

    clipping_submenu.add_radiobutton(label="Cohen-Sutherland", value=0, variable=clipping_algorithm)
    clipping_submenu.add_radiobutton(label="Liang-Barsky", value=1, variable=clipping_algorithm)
    curve_submenu.add_radiobutton(label="Bézier", value=0, variable=curve_type)
    curve_submenu.add_radiobutton(label="B-Spline", value=1, variable=curve_type)

    self.viewport.clipping_algorithm = clipping_algorithm
    self.viewport.curve_type = curve_type

    self.navbar.add_cascade(label="Arquivo", menu=file_menu)
    self.navbar.add_cascade(label="Configurações", menu=settings_menu)
    self.root.config(menu=self.navbar)

  def create_components(self):
    # Canva
    self.canva = tk.Canvas(self.root, background="white", width=self.width*2/3, height=self.height*5/6)
    self.viewport = Viewport(self.canva)

    # Log session
    self.ui_log = scrolledtext.ScrolledText(self.root, bg="white", fg="black", state="disabled", font=("Arial", 10), height=9)

    # Control buttons and input fields
    self.ui_build_button = tk.Button(self.root, text="Build", command=self.toggle_building)
    self.ui_close_polygon_button = tk.Button(self.root, text="Polígono", command=self.finish_polygon)
    self.ui_create_curve_button = tk.Button(self.root, text="Curva", command=self.finish_curve)
    self.ui_object_properties_button = tk.Button(self.root, text="Propriedades", command=self.properties_window) # also on mouse right click on object at table
    self.ui_rotate_object_button = tk.Button(self.root, text="Girar", command=self.rotate)
    self.ui_translate_object_button = tk.Button(self.root, text="Deslocar", command=self.translate)
    self.ui_scale_button = tk.Button(self.root, text="Escalar", command=self.scale_selected_object)

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

  def position_components(self):
    for i in range(12): self.root.columnconfigure(i, weight=1)
    for i in range(24): self.root.rowconfigure(i, weight=1)

    self.canva.grid(row=0, column=4, columnspan=8, rowspan=20, sticky="nsew")
    self.ui_log.grid(row=20, column=4, columnspan=12, rowspan=4, sticky="nsew")

    self.ui_object_list_frame.grid(row=0, column=0, rowspan=12, columnspan=4, sticky="nsew")

    self.ui_build_button.grid(row=12, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_close_polygon_button.grid(row=12, column=2, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_create_curve_button.grid(row=12, column=3, rowspan=1, columnspan=1, sticky="nsew")

    self.ui_rotate_object_button.grid(row=13, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_translate_object_button.grid(row=13, column=2, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_scale_button.grid(row=13, column=3, rowspan=1, columnspan=1, sticky="nsew")

    self.ui_object_properties_button.grid(row=14, column=0, rowspan=1, columnspan=4, sticky="nsew")

    self.ui_point_label.grid(row=15, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_point_x_input.grid(row=15, column=2, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_point_y_input.grid(row=15, column=3, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_degree_label.grid(row=16, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_degree_input.grid(row=16, column=2, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_scale_factor_label.grid(row=17, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_scale_factor_input.grid(row=17, column=2, rowspan=1, columnspan=2, sticky="nsew")

  def controls(self):
    self.canva.bind("<ButtonRelease-1>", self.canva_click)
    self.canva.bind("<Button-3>", self.move_window)
    self.root.bind("<Button-2>", lambda e: self.set_debug())
    self.root.bind("<Button-4>", lambda e: self.window.zoom_in(e.x, e.y) or self.update())
    self.root.bind("<Button-5>", lambda e: self.window.zoom_out(e.x, e.y) or self.update())
    self.root.bind("<KeyPress-w>", lambda e: self.window.move_up() or self.update())
    self.root.bind("<KeyPress-s>", lambda e: self.window.move_down() or self.update())
    self.root.bind("<KeyPress-a>", lambda e: self.window.move_left() or self.update())
    self.root.bind("<KeyPress-d>", lambda e: self.window.move_right() or self.update())
    self.root.bind("<KeyPress-q>", lambda e: self.window.move_below() or self.update())
    self.root.bind("<KeyPress-e>", lambda e: self.window.move_above() or self.update())
    self.root.bind("<KeyPress-Escape>", lambda e: self.cancel_building())
    self.root.bind("<Control-z>", lambda e: self.undo())

    self.ui_object_list.bind("<Button-3>", lambda e: self.object_list_menu(e))

    # This one is not a control. It's used to remove focus from a text input when clicking outside of it
    def focus_clicked_widget(event):
      # TODO: There has to be a better way to avoid errors when clicking on certain widgets
      try: event.widget.focus_set()
      except: pass
    # TODO: Stop object list from unselecting whenever another widget is clicked
    self.root.bind_all("<Button-1>", focus_clicked_widget)    

  def exit(self):
    # TODO: Save user preferences and current objects to output file
    self.root.quit()

  def toggle_building(self):
    self.building = not self.building
    self.ui_build_button.config(relief=tk.SUNKEN if self.building else tk.RAISED)
    if not self.building: self.finish_building()

  def cancel_building(self):
    self.building_buffer.clear()
    self.building = False
    self.ui_build_button.config(relief=tk.RAISED)
    self.viewport.update()

  def log(self, *message: str):
    '''Writes *message* to the log widget'''
    '''In the future, there could be different log levels'''
    self.ui_log.config(state="normal")
    self.ui_log.insert(tk.END, f"{''.join([str(m) for m in message])}\n")
    self.ui_log.see(tk.END)
    self.ui_log.config(state="disabled")

  def undo(self):
    """Undoes the last action. If the SGI is in building mode, remove the last added point or exit building mode if no points are left.
    If not in building mode, then the viewport must remove the last added object.
    """
    if self.building:
      if self.building_buffer: self.building_buffer.pop()
      else: self.cancel_building()
      self.viewport.update()
    else:
      self.undo()

  def canva_click(self, event: tk.Event):
    # Ignore click if it's outside the viewport area
    if not self.viewport.is_click_inside_window(event.x, event.y): return

    world_point = self.viewport.window.viewport_to_world(event.x, event.y)
    if self.building: self.building_buffer.append(world_point)
    else:
      self.viewport.add_point(world_point, self.id_counter)
      self.id_counter += 1

  # The following methods are just wrappers to the Viewport class methods
  # The added functionalities involve updating the program state, such as the building buffer and the object list
  def finish_polygon(self):
    if self.building:
      if len(self.building_buffer) < 3:
        self.log("Polígono precisa de ao menos 3 pontos.")
        return
      else:
        self.viewport.add_polygon(self.building_buffer, self.id_counter)
        self.cancel_building()

    # Open polygon insertion window
    else: return
  
  def finish_building(self):
    """Adds the stored points to the viewport
    If a single point is stored, add a point object.
    If multiple points are stored, add line segments between each pair of consecutive points.
    """
    if len(self.building_buffer) == 1:
      self.viewport.add_point(self.building_buffer[0], self.id_counter)
      self.id_counter += 1

    for i in range(len(self.building_buffer) - 1):
      start, end = self.building_buffer[i:i+2]
      self.viewport.add_line(start, end, self.id_counter)
      self.id_counter += 1

    # Clear buffer and reset building state
    self.cancel_building()