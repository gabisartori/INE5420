import tkinter as tk
from tkinter import ttk, font, colorchooser, simpledialog, scrolledtext

from viewport import *
from wireframe import *
from window import *
from components.my_types import *
from clipping import *
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
    self.mode = tk.StringVar(value=PREFERENCES.mode)
    self.coeff = PREFERENCES.curve_coefficient
    
    self.create_components()
    self.create_navbar()
    self.position_components()
    self.controls()
  
# Main window and components setup
  def set_up_root(self, title: str):
    self.root.title(title)
    # TODO: Remove this
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
    mode_submenu = tk.Menu(settings_menu, tearoff=0)
    curve_coefficient_submenu = tk.Menu(settings_menu, tearoff=0)

    clipping_submenu.add_radiobutton(label="Cohen-Sutherland", value=0, variable=self.clipping_algorithm, command=lambda: self.set_clipping_algorithm())
    clipping_submenu.add_radiobutton(label="Liang-Barsky", value=1, variable=self.clipping_algorithm, command=lambda: self.set_clipping_algorithm())

    curve_submenu.add_radiobutton(label="Bézier", value=0, variable=self.curve_type, command=lambda: self.set_curve_type())
    curve_submenu.add_radiobutton(label="B-Spline", value=1, variable=self.curve_type, command=lambda: self.set_curve_type())

    curve_coefficient_submenu.add_command(label="Coeficiente para curvas", 
                                          command=lambda: self.set_curve_coefficient())

    mode_submenu.add_radiobutton(label="2D", value="2D", variable=self.mode, command=lambda: self.set_mode())
    mode_submenu.add_radiobutton(label="3D", value="3D", variable=self.mode, command=lambda: self.set_mode())

    settings_menu.add_cascade(label="Algoritmo de Recorte", menu=clipping_submenu)
    settings_menu.add_cascade(label="Tipo de Curva", menu=curve_submenu)
    settings_menu.add_cascade(label="Coeficiente de Curva", menu=curve_coefficient_submenu)
    settings_menu.add_cascade(label="Modo", menu=mode_submenu)

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
    self.canva = tk.Canvas(self.root, background="white", width=self.width*2//3, height=self.height*5//6)
    self.viewport = Viewport(self.canva, self.clipping_algorithm, self.curve_type, self.log, self.ui_object_list, debug=self.debug)

    # Log session
    self.ui_log = scrolledtext.ScrolledText(self.root, bg="white", fg="black", state="disabled", font=("Arial", 10), height=9)

    # Control buttons and input fields
    self.ui_build_button = tk.Button(self.root, text="Build", command=self.toggle_building)
    self.ui_object_properties_button = tk.Button(self.root, text="Propriedades", command=self.properties_window) # also on mouse right click on object at table
    
    self.ui_create_point_button = tk.Button(self.root, text="Ponto", command=self.finish_point)
    self.ui_create_line_button = tk.Button(self.root, text="Linha", command=self.finish_lines)
    self.ui_close_polygon_button = tk.Button(self.root, text="Polígono", command=self.finish_polygon)
    
    self.ui_create_curve_button = tk.Button(self.root, text="Curva", command=self.finish_curve)
    self.ui_create_object_3d_button = tk.Button(self.root, text="Objeto 3D", command=self.finish_3d_object)
    
    self.ui_translate_object_button = tk.Button(self.root, text="Deslocar", command=self.translate_selected_object)
    self.ui_scale_button = tk.Button(self.root, text="Escalar", command=self.scale_selected_object)

    self.ui_rotate_x_button = tk.Button(self.root, text="Girar X", command=lambda: self.rotate_selected_object(axis="x"), state=tk.NORMAL if PREFERENCES.mode == "3D" else tk.DISABLED)
    self.ui_rotate_y_button = tk.Button(self.root, text="Girar Y", command=lambda: self.rotate_selected_object(axis="y"), state=tk.NORMAL if PREFERENCES.mode == "3D" else tk.DISABLED)
    self.ui_rotate_z_button = tk.Button(self.root, text="Girar Z", command=lambda: self.rotate_selected_object(axis="z"))

    self.ui_point_label = tk.Label(self.root, text="Ponto (x,y):" if PREFERENCES.mode == "2D" else "Ponto (x,y,z):")
    self.ui_point_x_y_input = tk.Entry(self.root)

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

  def set_curve_coefficient(self):
    coeff = simpledialog.askinteger("Configuração de Curvas", "Coeficiente para desenhar curvas de Bézier ou B-Spline(padrão 100):", initialvalue=self.window.coeff, minvalue=10, maxvalue=1000)
    if coeff:
      self.coeff = coeff
      self.log(f"Coeficiente para desenhar curvas alterado para {coeff}.")
      self.viewport.update()
   
  def set_clipping_algorithm(self):
    PREFERENCES.clipping_algorithm = self.clipping_algorithm.get()
    self.log(f"Algoritmo de recorte alterado para {'Cohen-Sutherland' if self.clipping_algorithm.get() == 0 else 'Liang-Barsky'}.")
    self.viewport.update()
    
  def set_curve_type(self):
    PREFERENCES.curve_algorithm = self.curve_type.get()
    self.log(f"Tipo de curva alterado para {'Bézier' if self.curve_type.get() == 0 else 'B-Spline'}.")
    self.viewport.update()
    
  def set_mode(self):
    PREFERENCES.mode = self.mode.get()
    self.ui_point_label.config(text="Ponto (x,y):" if PREFERENCES.mode == "2D" else "Ponto (x,y,z):")
    if PREFERENCES.mode == "2D":
      self.ui_rotate_x_button.config(state=tk.DISABLED)
      self.ui_rotate_y_button.config(state=tk.DISABLED)
    else:
      self.ui_rotate_x_button.config(state=tk.NORMAL)
      self.ui_rotate_y_button.config(state=tk.NORMAL)
    self.log(f"Modo alterado para {PREFERENCES.mode}.")
    self.viewport.set_mode(PREFERENCES.mode)
    self.viewport.update()
       
  def position_components(self):
    self.canva.grid(row=0, column=4, columnspan=8, rowspan=20, sticky="nsew")
    self.ui_log.grid(row=20, column=4, columnspan=12, rowspan=4, sticky="nsew")

    self.ui_object_list_frame.grid(row=0, column=0, rowspan=12, columnspan=4, sticky="nsew")

    #row 12:
    self.ui_build_button.grid(row=12, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_object_properties_button.grid(row=12, column=2, rowspan=1, columnspan=2, sticky="nsew")
    
    # row 13:
    self.ui_create_point_button.grid(row=13, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_create_line_button.grid(row=13, column=2, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_close_polygon_button.grid(row=13, column=3, rowspan=1, columnspan=1, sticky="nsew")
  
    # row 14:
    self.ui_create_curve_button.grid(row=14, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_create_object_3d_button.grid(row=14, column=2, rowspan=1, columnspan=2, sticky="nsew")

    # row 15:
    self.ui_rotate_x_button.grid(row=15, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_rotate_y_button.grid(row=15, column=2, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_rotate_z_button.grid(row=15, column=3, rowspan=1, columnspan=1, sticky="nsew")
    
    # row 16:
    self.ui_degree_label.grid(row=16, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_degree_input.grid(row=16, column=2, rowspan=1, columnspan=2, sticky="nsew")

    # row 17:
    self.ui_point_label.grid(row=17, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_point_x_y_input.grid(row=17, column=2, rowspan=1, columnspan=1, sticky="nsew")
    #self.ui_point_y_input.grid(row=17, column=3, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_translate_object_button.grid(row=17, column=3, rowspan=1, columnspan=1, sticky="nsew")
    
    # row 18:
    self.ui_scale_factor_label.grid(row=18, column=0, rowspan=1, columnspan=2, sticky="nsew")
    self.ui_scale_factor_input.grid(row=18, column=2, rowspan=1, columnspan=1, sticky="nsew")
    self.ui_scale_button.grid(row=18, column=3, rowspan=1, columnspan=1, sticky="nsew")

    # row 19:
    
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

  @staticmethod
  def popup(width: int, height: int, title: str) -> tk.Toplevel:
    popup = tk.Toplevel()
    popup.title(title)
    popup.minsize(width, height)
    popup.resizable(False, False)
    return popup
  
  def object_list_menu(self, event):
    selected_item = self.ui_object_list.identify_row(event.y)
    if selected_item:
      self.ui_object_list.selection_set(selected_item)
      menu = tk.Menu(self.root, tearoff=0)
      menu.add_command(label="Propriedades", command=self.properties_window)
      menu.add_command(label="Remover", command=lambda: self.viewport.remove_selected_object(selected_item))
      
      def close_menu(event2):
        menu.unpost()
        self.root.unbind("<Button-1>", close_menu_binding)
        
      close_menu_binding = self.root.bind("<Button-1>", close_menu)
      menu.post(event.x_root, event.y_root)

# Additional Windows
  def properties_window(self):
    target = self.get_selected_object()
    if target is None: return
    popup = self.popup(0, 300, "Propriedades do Objeto")
    def apply_changes(name, fill_color, line_color, thickness):
      target.name = name.get().strip() if name.get().strip() != "" else target.name
      target.fill_color = fill_color
      target.line_color = line_color
      try: target.thickness = float(thickness.get())
      except ValueError: pass

      self.viewport.update()
      popup.destroy()

    match target:
      case PointObject():
        thickness_prompt = "Raio do ponto"
        line_prompt = "Cor do contorno"
        fill_prompt = "Cor do ponto"
      case LineObject():
        thickness_prompt = "Espessura da linha"
        line_prompt = "Cor da linha"
        fill_prompt = ""
      case PolygonObject():
        thickness_prompt = "Espessura da linha"
        line_prompt = "Cor do contorno"
        fill_prompt = "Cor de preenchimento"
      case CurveObject_2D():
        thickness_prompt = "Espessura da linha"
        line_prompt = "Cor da linha"
        fill_prompt = ""
      case _:
        return

    # Name
    name_label = tk.Label(popup, text="Nome do objeto:")
    name_input = tk.Entry(popup)
    name_input.insert(0, target.name)
    name_label.grid(row=0, column=0, sticky="ew")
    name_input.grid(row=0, column=1, columnspan=2, sticky="ew")

    # Line Color
    line_color_label = tk.Label(popup, text=line_prompt)
    line_color_input = tk.Entry(popup)
    line_color_input.insert(0, target.line_color)
    line_color_button = tk.Button(popup, text="Escolher", command=lambda: (
      color := colorchooser.askcolor(title="Escolha a cor da linha"),
      line_color_input.delete(0, tk.END),
      line_color_input.insert(0, color[1]) if color[1] else None
    ))
    line_color_label.grid(row=1, column=0, sticky="ew")
    line_color_input.grid(row=1, column=1, sticky="ew")
    line_color_button.grid(row=1, column=2, sticky="ew")
    
    # Fill Color
    if fill_prompt:
      fill_color_label = tk.Label(popup, text=fill_prompt)
      fill_color_input = tk.Entry(popup)
      fill_color_input.insert(0, target.fill_color)
      fill_color_button = tk.Button(popup, text="Escolher", command=lambda: (
        color := colorchooser.askcolor(title="Escolha a cor de preenchimento"),
        fill_color_input.delete(0, tk.END),
        fill_color_input.insert(0, color[1]) if color[1] else None
      ))
      fill_color_label.grid(row=2, column=0, sticky="ew")
      fill_color_input.grid(row=2, column=1, sticky="ew")
      fill_color_button.grid(row=2, column=2, sticky="ew")
    else:
      fill_color_input = tk.StringVar(value=target.fill_color)

    # Thickness
    thickness_label = tk.Label(popup, text=thickness_prompt)
    thickness_input = tk.Entry(popup)
    thickness_input.insert(0, str(target.thickness))
    thickness_label.grid(row=3, column=0, sticky="ew")
    thickness_input.grid(row=3, column=1, columnspan=2, sticky="ew")
  

    # Apply Button
    apply_button = tk.Button(popup, text="Aplicar", command=lambda: apply_changes(name_input, fill_color_input.get(), line_color_input.get(), thickness_input))
    cancel_button = tk.Button(popup, text="Cancelar", command=popup.destroy)
    apply_button.grid(row=4, column=0, columnspan=4, sticky="ew")
    cancel_button.grid(row=5, column=0, columnspan=4, sticky="ew")

  def add_point_window(self):
    popup = self.popup(0, 200, "Adicionar Ponto")
    def finish_point_callback():
      try: point = np.array(list(map(float, point_input.get().strip().strip("()").strip(")").split(','))))
      except ValueError:
        self.log("Erro: ponto inválido.")
        return
      if (self.mode.get() == "2D" and len(point) != 2) or (self.mode.get() == "3D" and len(point) != 3):
        self.log(f"Erro: insira um ponto {'(x,y)' if self.mode.get() == '2D' else '(x,y,z)'}.")
        return

      name = name_input.get().strip() if name_input.get().strip() != "" else "Point"
      try: thickness = int(thickness_input.get())
      except ValueError: thickness = 1
      color = color_input.get().strip() if color_input.get().strip() != "" else "#000000"
      self.viewport.add_point(point, name, color, thickness)
      popup.destroy()
    
    name_label = tk.Label(popup, text="Nome do objeto:")
    name_input = tk.Entry(popup)
    name_input.insert(0, "Point")
    name_label.grid(row=0, column=0, sticky="ew")
    name_input.grid(row=0, column=1, columnspan=2, sticky="ew")

    point_label = tk.Label(popup, text="Coordenadas do ponto:")
    point_input = tk.Entry(popup)
    point_input.insert(0, "0,0,0" if self.mode.get() == "3D" else "0,0")
    point_label.grid(row=1, column=0, sticky="ew")
    point_input.grid(row=1, column=1, columnspan=2, sticky="ew")

    color_label = tk.Label(popup, text="Cor do ponto:")
    color_input = tk.Entry(popup)
    color_input.insert(0, "#000000")
    color_button = tk.Button(popup, text="Escolher", command=lambda: (
      color := colorchooser.askcolor(title="Escolha a cor do ponto"),
      color_input.delete(0, tk.END),
      color_input.insert(0, color[1]) if color[1] else None
    ))
    color_label.grid(row=4 if self.mode.get() == "3D" else 3, column=0, sticky="ew")
    color_input.grid(row=4 if self.mode.get() == "3D" else 3, column=1, sticky="ew")
    color_button.grid(row=4 if self.mode.get() == "3D" else 3, column=2, sticky="ew") 
    
    thickness_label = tk.Label(popup, text="Raio do ponto:")
    thickness_input = tk.Entry(popup)
    thickness_input.insert(0, "1")
    thickness_label.grid(row=5 if self.mode.get() == "3D" else 4, column=0, sticky="ew")
    thickness_input.grid(row=5 if self.mode.get() == "3D" else 4, column=1, columnspan=2, sticky="ew")
    
    create_button = tk.Button(popup, text="Criar Ponto", command=finish_point_callback)
    create_button.grid(row=6 if self.mode.get() == "3D" else 5, column=0, columnspan=3, sticky="ew")
    cancel_button = tk.Button(popup, text="Cancelar", command=popup.destroy)
    cancel_button.grid(row=7 if self.mode.get() == "3D" else 6, column=0, columnspan=3, sticky="ew")
  
  def add_lines_window(self):
    popup = self.popup(0, 250, "Adicionar Linha")
    def finish_lines_callback():
      points = points_input.get().strip().strip("(").strip(")").replace(" ", "").split("),(")
      try: points = [list(map(float, p.split(','))) for p in points]
      except ValueError:
        self.log("Erro: pontos inválidos.")
        return
      if len(points) < 2:
        self.log("Erro: insira ao menos 2 pontos.")
        return
      points = [np.array(p) for p in points]

      name = name_input.get().strip() if name_input.get().strip() != "" else "Line"
      try: thickness = int(thickness_input.get())
      except ValueError: thickness = 1
      color = color_input.get().strip() if color_input.get().strip() != "" else "#000000"
      self.viewport.add_lines(points, name, color, thickness)
      popup.destroy()
    
    name_label = tk.Label(popup, text="Nome do objeto:")
    name_input = tk.Entry(popup)
    name_input.insert(0, "Line")
    name_label.grid(row=0, column=0, sticky="ew")
    name_input.grid(row=0, column=1, columnspan=2, sticky="ew")

    points_label = tk.Label(popup, text="Pontos (x0,y0,z0),(x1,y1,z1):" 
                            if PREFERENCES.mode == "3D" else "Pontos (x0,y0),(x1,y1):")
    points_input = tk.Entry(popup)
    points_label.grid(row=1, column=0, sticky="ew")
    points_input.grid(row=1, column=1, columnspan=2, sticky="ew")

    color_label = tk.Label(popup, text="Cor da linha:")
    color_input = tk.Entry(popup)
    color_input.insert(0, "#000000")
    color_button = tk.Button(popup, text="Escolher", command=lambda: (
      color := colorchooser.askcolor(title="Escolha a cor da linha"),
      color_input.delete(0, tk.END),
      color_input.insert(0, color[1]) if color[1] else None
    ))
    color_label.grid(row=2, column=0, sticky="ew")
    color_input.grid(row=2, column=1, sticky="ew")
    color_button.grid(row=2, column=2, sticky="ew")
    thickness_label = tk.Label(popup, text="Espessura da linha:")
    thickness_input = tk.Entry(popup)
    thickness_input.insert(0, "1")
    thickness_label.grid(row=3, column=0, sticky="ew")
    thickness_input.grid(row=3, column=1, columnspan=2, sticky="ew")
    create_button = tk.Button(popup, text="Criar Linha", command=finish_lines_callback)
    create_button.grid(row=4, column=0, columnspan=3, sticky="ew")
    cancel_button = tk.Button(popup, text="Cancelar", command=popup.destroy)
    cancel_button.grid(row=5, column=0, columnspan=3, sticky="ew")
    

  def add_polygon_window(self):
    popup = self.popup(0, 300, "Adicionar Polígono")
    def finish_polygon_callback():
      name = name_input.get().strip() if name_input.get().strip() != "" else "Polygon"
      points = points_input.get().strip().strip("(").strip(")").replace(" ", "").split("),(")
      try: points = [list(map(float, p.split(','))) for p in points]
      except ValueError:
        self.log("Erro: pontos inválidos.")
        return
      if len(points) < 3:
        self.log("Erro: insira ao menos 3 pontos.")
        return
      points = [np.array(p) for p in points]

      try: thickness = int(thickness_input.get())
      except ValueError: thickness = 1
      line_color = line_color_input.get().strip() if line_color_input.get().strip() != "" else "#000000"
      fill_color = fill_color_input.get().strip() if fill_color_input.get().strip() != "" else "#ffffff"
      self.viewport.add_polygon(points, name, line_color, fill_color, thickness)
      popup.destroy()
    
    name_label = tk.Label(popup, text="Nome do objeto:")
    name_input = tk.Entry(popup)
    name_input.insert(0, "Polygon")
    name_label.grid(row=0, column=0, sticky="ew")
    name_input.grid(row=0, column=1, columnspan=2, sticky="ew")

    points_label = tk.Label(popup, text="Pontos (x0,y0,z0),(x1,y1,z1),...,(xN,yN,zN):"
                            if PREFERENCES.mode == "3D" else "Pontos (x0,y0),(x1,y1),...,(xN,yN):")
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

    fill_color_label = tk.Label(popup, text="Cor de preenchimento:")
    fill_color_input = tk.Entry(popup)
    fill_color_input.insert(0, "#ffffff")
    fill_color_button = tk.Button(popup, text="Escolher", command=lambda: (
      color := colorchooser.askcolor(title="Escolha a cor de preenchimento"),
      fill_color_input.delete(0, tk.END),
      fill_color_input.insert(0, color[1]) if color[1] else None
    ))
    fill_color_label.grid(row=3, column=0, sticky="ew")
    fill_color_input.grid(row=3, column=1, sticky="ew")
    fill_color_button.grid(row=3, column=2, sticky="ew")

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
      control_points = [np.array(p) for p in control_points]
      if len(control_points) < 4:
        self.log("Erro: insira ao menos 4 pontos de controle.")
        return
      popup.destroy()
      self.viewport.add_curve(control_points, name_input.get().strip(), line_color_input.get().strip())
      popup.destroy()

    name_label = tk.Label(popup, text="Nome do objeto:")
    name_input = tk.Entry(popup)
    name_input.insert(0, "Curve")
    name_label.grid(row=0, column=0, sticky="ew")
    name_input.grid(row=0, column=1, columnspan=2, sticky="ew")

    points_label = tk.Label(popup, text="Pontos de controle (x0,y0),(x1,y1),...,(xN,yN):"
                            if PREFERENCES.mode == "2D" else "Pontos de controle (x0,y0,z0),(x1,y1,z1),...,(xN,yN,zN):")
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

    create_button = tk.Button(popup, text="Criar Curva", command=lambda: finish_curve_callback)
    cancel_button = tk.Button(popup, text="Cancelar", command=popup.destroy)
    create_button.grid(row=3, column=0, columnspan=3, sticky="ew")
    cancel_button.grid(row=4, column=0, columnspan=3, sticky="ew")
  
  def add_3d_object_window(self):
    popup = self.popup(0, 250, "Adicionar Objeto 3D")

    # Variáveis vinculadas aos Entry widgets
    name_var = tk.StringVar(value="3D Object")
    points_var = tk.StringVar()
    line_color_var = tk.StringVar(value="#000000")

    def finish_3d_object_callback():
        try:
            # Obtenha os valores das variáveis (não diretamente dos widgets)
            name = name_var.get().strip()
            color = line_color_var.get().strip()
            control_points_str = points_var.get().strip().strip("(").strip(")").replace(" ", "").split("),(")

            control_points = [list(map(float, p.split(','))) for p in control_points_str]
            control_points = [np.array(p) for p in control_points]

            if len(control_points) < 4:
                self.log("Erro: insira ao menos 4 pontos de controle.")
                return

            popup.destroy()
            self.viewport.add_3d_object(control_points, name, color)

        except ValueError:
            self.log("Erro: pontos inválidos.")
        except Exception as e:
            self.log(f"Erro: {e}")

    name_label = tk.Label(popup, text="Nome do objeto:")
    name_input = tk.Entry(popup, textvariable=name_var)
    name_label.grid(row=0, column=0, sticky="ew")
    name_input.grid(row=0, column=1, columnspan=2, sticky="ew")

    points_label = tk.Label(popup, text="Linhas (x0,y0,z0),(x1,y1,z1),...,(xN,yN,zN):")
    points_input = tk.Entry(popup, textvariable=points_var)
    points_label.grid(row=1, column=0, sticky="ew")
    points_input.grid(row=1, column=1, columnspan=2, sticky="ew")

    line_color_label = tk.Label(popup, text="Cor das linhas:")
    line_color_input = tk.Entry(popup, textvariable=line_color_var)
    line_color_button = tk.Button(popup, text="Escolher", command=lambda: (
        color := colorchooser.askcolor(title="Escolha a cor da linha"),
        line_color_var.set(color[1]) if color[1] else None
    ))
    line_color_label.grid(row=2, column=0, sticky="ew")
    line_color_input.grid(row=2, column=1, sticky="ew")
    line_color_button.grid(row=2, column=2, sticky="ew")

    create_button = tk.Button(popup, text="Criar Objeto 3D", command=finish_3d_object_callback)
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
      
  def finish_point(self):
    if self.viewport.building:
      self.ui_build_button.config(relief=tk.RAISED)
      self.viewport.finish_point()
    else:
      self.add_point_window()

  def finish_lines(self):
    if self.viewport.building:
      self.ui_build_button.config(relief=tk.RAISED)
      self.viewport.finish_lines()
    else:
      self.add_lines_window()

  def finish_3d_object(self):
    if self.viewport.building:
      self.ui_build_button.config(relief=tk.RAISED)
      self.viewport.finish_3d_object()
    else:
      self.add_3d_object_window()

  def get_selected_object(self, log=True) -> Wireframe | None:
    selected = self.ui_object_list.selection()
    if not selected:
      if log: self.log("Nenhum objeto selecionado.")
      return None
    item_id = int(self.ui_object_list.item(selected[0])['tags'][0])
    target = next((obj for obj in self.viewport.objects if obj.id == item_id), None)
    if target is None:
      if log: self.log("Objeto não encontrado.")
      return None
    return target

  def rotate_selected_object(self, axis: str):
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
      case None: self.viewport.window.rotate(angle,axis)
      # Rotate selected object
      case target:
        # If no valid point is specified, rotate around object's center
        # Otherwise, rotate around specified point
        rx, ry = self.ui_point_x_y_input.get().split(",") if "," in self.ui_point_x_y_input.get() else (self.ui_point_x_y_input.get(), '1')
        rz = '1'
        try:
          rx = int(rx)
          ry = int(ry)
          rz = int(rz)
        except ValueError:
          rx, ry, rz = target.center

        target.rotate(angle, np.array([rx, ry, rz]))
    self.viewport.update()

  def translate_selected_object(self):
    target = self.get_selected_object()
    if target is None: return
    points = self.ui_point_x_y_input.get().strip("(").strip(")").replace(" ", "").split(",")
    if (self.mode.get() == "2D" and len(points) != 2) or (self.mode.get() == "3D" and len(points) != 3):
      self.log(f"Erro: insira um ponto de deslocamento {'(dx,dy)' if self.mode.get() == '2D' else '(dx,dy,dz)'}.")
      return
    
    dx, dy = points[0], points[1]
    dz = points[2] if self.mode.get() == "3D" else '1'
    
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
    