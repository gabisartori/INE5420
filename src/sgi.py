import tkinter as tk
from tkinter import ttk, font, colorchooser, simpledialog, scrolledtext

from viewport import *
from wireframe import *
from window import *
from components.my_types import *
from clipping import *
from data import preferences
from config import PREFERENCES


class SGI:
  def __init__(
    self,
    # width: int=config.WIDTH, 
    # height: int=config.HEIGHT, 
    # title: str=config.APPLICATION_NAME, 
    input: str | None, 
    output: str | None, 
    debug: bool
    #preferences: preferences.Preferences
  ):
    # Config
    #self.pr = preferences.load_user_preferences()
    self.width: int = PREFERENCES.width
    self.height: int = PREFERENCES.height
    self.input_file: str | None = input if input is not None else PREFERENCES.input_file
    self.output_file: str | None = output if output is not None else PREFERENCES.output_file
    self.debug: bool = debug

    # GUI
    self.root = tk.Tk()
    self.set_up_root(PREFERENCES.application_name)

    ## The *clipping_algorithm* and *curve_type* variables will be also passed to the Viewport class
    ## Hopefully, this means that changing them here will change them in the Viewport class too
    ## TODO: There's probably a better place to initialize these variables
    self.clipping_algorithm = tk.IntVar(value=PREFERENCES.clipping_algorithm)
    self.curve_type = tk.IntVar(value=PREFERENCES.curve_algorithm)

    self.create_components()
    self.create_navbar()
    self.position_components()
    self.controls()
  
# Main window and components setup
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

    clipping_submenu.add_radiobutton(label="Cohen-Sutherland", value=0, variable=self.clipping_algorithm)
    clipping_submenu.add_radiobutton(label="Liang-Barsky", value=1, variable=self.clipping_algorithm)
    curve_submenu.add_radiobutton(label="Bézier", value=0, variable=self.curve_type)
    curve_submenu.add_radiobutton(label="B-Spline", value=1, variable=self.curve_type)

    self.navbar.add_cascade(label="Arquivo", menu=file_menu)
    self.navbar.add_cascade(label="Configurações", menu=settings_menu)
    self.root.config(menu=self.navbar)

  def create_components(self):
    # Canva
    self.canva = tk.Canvas(self.root, background="white", width=self.width*2//3, height=self.height*5//6)
    self.viewport = Viewport(self.canva, self.clipping_algorithm, self.curve_type, self.log, debug=self.debug)

    # Log session
    self.ui_log = scrolledtext.ScrolledText(self.root, bg="white", fg="black", state="disabled", font=("Arial", 10), height=9)

    # Control buttons and input fields
    self.ui_build_button = tk.Button(self.root, text="Build", command=self.toggle_building)
    self.ui_close_polygon_button = tk.Button(self.root, text="Polígono", command=self.finish_polygon)
    self.ui_create_curve_button = tk.Button(self.root, text="Curva", command=self.finish_curve)
    self.ui_object_properties_button = tk.Button(self.root, text="Propriedades", command=None)#self.properties_window) # also on mouse right click on object at table
    self.ui_rotate_object_button = tk.Button(self.root, text="Girar", command=None)#self.viewport.rotate)
    self.ui_translate_object_button = tk.Button(self.root, text="Deslocar", command=None)#self.translate)
    self.ui_scale_button = tk.Button(self.root, text="Escalar", command=None)#self.scale_selected_object)

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
    # TODO: There's a phantom space on the right of the canvas
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
    self.canva.bind("<ButtonRelease-1>", self.viewport.canva_click)
    self.canva.bind("<Button-3>", self.viewport.move_window)
    self.root.bind("<Button-2>", lambda e: self.viewport.toggle_debug())
    self.root.bind("<Button-4>", lambda e: self.viewport.window.zoom_in(e.x, e.y) or self.viewport.update())
    self.root.bind("<Button-5>", lambda e: self.viewport.window.zoom_out(e.x, e.y) or self.viewport.update())
    self.root.bind("<KeyPress-w>", lambda e: self.viewport.window.move_up() or self.viewport.update())
    self.root.bind("<KeyPress-s>", lambda e: self.viewport.window.move_down() or self.viewport.update())
    self.root.bind("<KeyPress-a>", lambda e: self.viewport.window.move_left() or self.viewport.update())
    self.root.bind("<KeyPress-d>", lambda e: self.viewport.window.move_right() or self.viewport.update())
    self.root.bind("<KeyPress-q>", lambda e: self.viewport.window.move_below() or self.viewport.update())
    self.root.bind("<KeyPress-e>", lambda e: self.viewport.window.move_above() or self.viewport.update())
    self.root.bind("<KeyPress-Escape>", lambda e: self.cancel_building())
    self.root.bind("<Control-z>", lambda e: self.viewport.undo())

    self.ui_object_list.bind("<Button-3>", lambda e: self.object_list_menu(e))

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
    if self.output_file:
      try:
        self.viewport.save_objects(self.output_file)
      except Exception as e:
        self.log(f"Erro ao salvar objetos: {e}")
    return self.viewport.objects

  def exit(self):
    # TODO: Save user preferences and current objects to output file
    PREFERENCES.save_user_preferences()
    self.root.quit()

# Additional Windows
  def add_curve(self, prompt_window: tk.Toplevel | None=None):
    def finish_curve_callback(control_points):
      control_points = control_points.get().strip("(").strip(")").replace(" ", "")
      control_points = list(map(float, control_points.split(',')))
      control_points = [np.array([control_points[i], control_points[i+1], 1]) for i in range(0, len(control_points), 2)]
      if len(control_points) < 4:
        self.log("Erro: insira ao menos 4 pontos de controle.")
        return
      popup.destroy()
      self.viewport.add_curve_from_points(control_points)
      prompt_window.destroy() if prompt_window else None

    popup = tk.Toplevel(self.root)
    title = "Adicionar Curva"
    popup.title(title)
    popup.geometry("300x200")
    popup.resizable(False, False)
    popup.grab_set()

    instructions_control_points = tk.Label(popup, text="Pontos de controle (x0,y0,x1,y1,...,xN,yN)")
    instructions_control_points.pack(pady=10)
    control_points = tk.Entry(popup, justify="center")
    control_points.pack(pady=5, padx=10, fill=tk.X, expand=True)

    create_button = tk.Button(popup, text="Criar/Alterar Curva", command=lambda: finish_curve_callback(control_points))
    create_button.pack(pady=10)

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
    self.ui_build_button.config(relief=tk.RAISED)
    self.viewport.finish_polygon()
  
  def finish_curve(self):
    self.ui_build_button.config(relief=tk.RAISED)
    self.viewport.finish_curve()
