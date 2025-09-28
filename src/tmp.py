import tkinter as tk
from tkinter import ttk, messagebox, font, colorchooser, simpledialog, scrolledtext
from wireframe import *
from window import *
from components.toggle_switch import *
from components.my_types import *
from data.usr_preferences import *
from clipping import Clipping, ClippingAlgorithm

class Viewport:
  def __init__(self, width, height, title="INE5420", input: str | None=None, output: str | None=None, debug: bool=False):
    self.objects: list[Wireframe] = self.load_objects(input) if input else []
    self.update()

  # TODO: For some goddamn reason rowspan and columnspan are being ignored by most components
  # Must make it so that the components respect the grid layout
  def build_debug_grid(self):
    step = 75
    min_zoom = self.window.min_zoom 

    width = self.width
    height = self.height

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
        fill=ColorScheme.LIGHT_DEBUG_GRID.value if self.theme == "light" else ColorScheme.DARK_DEBUG_GRID.value
      )

      start_v = self.window.world_to_viewport(np.array([i, -max_range, 0]))
      end_v = self.window.world_to_viewport(np.array([i, max_range, 0]))
      self.canva.create_line(
        start_v[0], start_v[1], end_v[0], end_v[1],
        fill=ColorScheme.LIGHT_DEBUG_GRID.value if self.theme == "light" else ColorScheme.DARK_DEBUG_GRID.value
      )

    origin = self.window.world_to_viewport(np.array([0, 0, 0]))
    self.canva.create_text(origin[0] + 15, origin[1] - 10, text="(0,0)", fill=ColorScheme.LIGHT_TEXT.value if self.theme == "light" else ColorScheme.DARK_TEXT.value, font=("Arial", 10, "bold"))

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

  def rotate(self):
    '''Rotates something according to the inputs passed'''
    '''If no object is selected, it'll rotate the window'''
    '''If there's a selected object, it'll rotate it around the specified point'''
    '''If there are no specified points, it'll rotate the object around its center'''
    try: angle = int(self.ui_degree_input.get())
    except ValueError: angle = 15

    # Check if there's a selected item
    target = self.get_selected_object()
    # Object selected, check if it'll be rotated around its center or a specified point
    if target:
      rx = self.ui_point_x_input.get()
      ry = self.ui_point_y_input.get()
      # Valid point, rotate around it
      try:
        rx = float(rx)
        ry = float(ry)
        target.rotate(angle, np.array([rx, ry, 1]))
      # No valid point, rotate around the object's center
      except ValueError:
        target.rotate(angle)

    # No object selected, rotate window
    else:
      self.window.rotate(angle)

    self.update()

  def translate(self):
    target = self.get_selected_object()
    if target is None:
      self.log("Aviso: Nenhum objeto selecionado.")
      return
    try:
      dx = float(self.ui_point_x_input.get())
      dy = float(self.ui_point_y_input.get())
    except ValueError:
      self.log("Erro: Coordenadas inválidas.")
      return
    target.translate(dx, dy)
    self.update()

  def scale_selected_object(self):
    target = self.get_selected_object()
    if target is None:
      self.log("Aviso: Nenhum objeto selecionado.")
      return
    try: factor = float(self.ui_scale_factor_input.get())
    except ValueError: factor = 1.5
    if factor <= 0:
      self.log("Erro: Fator de escala deve ser maior que zero.")
      return
    target.scale(factor)
    self.update()

  def object_list_menu(self, event):
    selected_item = self.ui_object_list.identify_row(event.y)
    if selected_item:
      self.ui_object_list.selection_set(selected_item)
      menu = tk.Menu(self.root, tearoff=0)
      menu.add_command(label="Propriedades", command=self.properties_window)
      menu.add_command(label="Remover", command=self.remove_selected_object)

      # Show the menu and close it if a click outside happens
      def close_menu_on_click(event2):
        menu.unpost()
        self.root.unbind("<Button-1>", close_menu_binding)
      close_menu_binding = self.root.bind("<Button-1>", close_menu_on_click, add="+")
      menu.post(event.x_root, event.y_root)      

  def remove_selected_object(self):
    target = self.get_selected_object()
    if target:
      self.objects.remove(target)
      self.update()
    else:
      self.log("Aviso: Nenhum objeto selecionado.")

  def set_debug(self):
    self.debug = not self.debug
    self.update()

  def move_window(self, event):
    self.window.position = self.window.viewport_to_world(event.x, event.y)
    self.update()

  def clear(self):
    self.objects.clear()
    self.ui_object_list.delete(*self.ui_object_list.get_children())
    self.build.clear()
    self.building = False
    self.update()

  def set_curve_config(self):
    steps = simpledialog.askinteger("Configuração de Curvas", "Número de passos para desenhar curvas de Bézier (padrão 100):", initialvalue=self.window.bezier_steps, minvalue=10, maxvalue=1000)
    if steps:
      self.window.bezier_steps = steps
      self.log(f"Número de passos para desenhar curvas de Bézier alterado para {steps}.")
      self.update() 

  def set_clipping_algorithm(self, algorithm: str):
    self.log(f"Algoritmo de clipagem alterado para {algorithm.title()}")
    self.update()

  def set_curve_type(self, curve_type: str):
    self.log(f"Tipo de curva alterado para {curve_type.title()}")
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

  def is_click_inside_viewport(self, x, y) -> bool:
    x0, y0, x1, y1 = self.window.get_corners()
    return x0 <= x <= x1 and y0 <= y <= y1

  def finish_curve(self):
    if self.building:
      if len(self.build) < 4: 
        self.log("Erro: Pelo menos quatro pontos são necessários para formar uma curva de Bézier cúbica.")
        return

      new_curve = CurveObject_2D("Curve", self.build.copy(), self.window.bezier_steps, id=self.placed_objects_counter)
      if self.curve_type.get() == "b_spline":
        new_curve.generate_b_spline_points()
      else:
        new_curve.generate_bezier_points()

      self.objects.append(new_curve)
      self.placed_objects_counter += 1
      self.cancel_building()
    else:
      self.add_curve()

  def load_objects(self, filepath: str) -> list[Wireframe]:
    if not filepath: return []
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
                new_curve = CurveObject_2D(current_name, control_points, steps=steps, id=len(objects))
                if self.curve_type.get() == "b_spline":
                  new_curve.generate_b_spline_points()
                else:
                  new_curve.generate_bezier_points()
                objects.append(new_curve)

              else:
                  self.log(f"Aviso: Curva '{current_name}' ignorada por ter menos de 2 pontos válidos.")
              current_points = []

            case _:
              self.log(f"Aviso: Cabeçalho desconhecido '{header}' ignorado.")

      return objects
    except FileNotFoundError:
      self.log(f"Arquivo {filepath} não encontrado.")
      return []
    except Exception as e:
      self.log(f"Erro: Erro ao carregar objetos: {e}")
      return []

  def add_curve(self, target: CurveObject_2D | None=None, prompt_window: tk.Toplevel | None=None):
    popup = tk.Toplevel(self.root)
    title = "Adicionar Curva de Bézier Cúbica" if self.curve_type.get() == "bezier" else "Adicionar Curva B-Spline Cúbica"
    popup.title(title)
    popup.geometry("300x200")
    popup.resizable(False, False)
    popup.grab_set()

    instructions_control_points = tk.Label(popup, text="Pontos de controle (x0,y0,x1,y1,...,xN,yN)")
    instructions_control_points.pack(pady=10)
    control_points = tk.Entry(popup, textvariable=tk.StringVar(value=", ".join(f"{p[0]},{p[1]}" for p in target.control_points) if target else ""), justify="center")
    control_points.pack(pady=5, padx=10, fill=tk.X, expand=True)



    def finish_curve_callback(target=target):
      try:
        # delete previous curve if editing
        if target: self.objects.remove(target)

        # Remove spaces and parentheses from input text before parsing it as a list of floats split by commas
        control_points_str = control_points.get().strip("(").strip(")").replace(" ", "")
        control_values = list(map(float, control_points_str.split(',')))

        input_points = [np.array([control_values[i], control_values[i+1], 1]) for i in range(0, len(control_values), 2)]
        if len(input_points) < 4:
          self.log("Erro: insira ao menos 4 pontos de controle.")
          return

        self.build = input_points           
        popup.destroy()            
        target = CurveObject_2D("Curve", self.build.copy(), self.window.bezier_steps, id=self.placed_objects_counter)
        if self.curve_type.get() == "b_spline":
          target.generate_b_spline_points()
        else:
          target.generate_bezier_points()

        if target:
          target.line_color = target.line_color
          target.fill_color = target.fill_color
          target.thickness = target.thickness

        self.objects.append(target)
        self.placed_objects_counter += 1

        self.cancel_building()
        prompt_window.destroy() if prompt_window else None

      except Exception as e:
        self.log(f"Erro: {e}")
        raise e

    create_button = tk.Button(popup, text="Criar/Alterar Curva", command=finish_curve_callback)
    create_button.pack(pady=10)          

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
    x0, y0, x1, y1 = self.window.get_corners()
    self.canva.create_rectangle(x0, y0, x1, y1, outline="red", width=1)

  def change_thickness(self, target: Wireframe, thickness: str, window: tk.Toplevel):
    try:
      target.thickness = int(thickness)
      self.update()
    except ValueError:
      self.log("Erro: Espessura inválida. Deve ser um número inteiro.")
    window.destroy()

  def change_line_color(self, target: Wireframe, window: tk.Toplevel):
    color = colorchooser.askcolor(title="Escolha a cor da linha")
    if color[1]:
      target.line_color = color[1]
      self.update()
    window.destroy()

  def change_fill_color(self, target: Wireframe, window: tk.Toplevel):    
    color = colorchooser.askcolor(title="Escolha a cor de preenchimento")
    if color[1]:
      target.fill_color = color[1]
      self.update()
    window.destroy()

  def properties_window(self):
    target = self.get_selected_object()
    if not target:
      self.log("Aviso: Nenhum objeto selecionado.")
      return
    match target:
      case PointObject():
        thickness_prompt = "Raio do ponto"
        line_prompt = "Cor do contorno"
        fill_prompt = "Cor do ponto"
        control_points_prompt = ""
      case LineObject():
        thickness_prompt = "Espessura da linha"
        line_prompt = "Cor da linha"
        fill_prompt = ""
        control_points_prompt = ""
      case PolygonObject():
        thickness_prompt = "Espessura da linha"
        line_prompt = "Cor do contorno"
        fill_prompt = "Cor de preenchimento"
        control_points_prompt = ""
      case CurveObject_2D():
        thickness_prompt = "Espessura da linha"
        line_prompt = "Cor da linha"
        fill_prompt = ""
        control_points_prompt = "Pontos de controle"

      case _:
        return
    prompt_window = tk.Toplevel(self.root)
    prompt_window.title("Propriedades do Objeto")
    prompt_window.resizable(False, False)
    name_label = tk.Label(prompt_window, text="Nome do objeto:")
    name_input = tk.Entry(prompt_window)
    name_input.insert(0, target.name)
    name_button = tk.Button(prompt_window, text="Alterar", command=lambda: (setattr(target, 'name', name_input.get()), prompt_window.destroy(), self.update()))

    fill_color_label = tk.Label(prompt_window, text=fill_prompt)
    line_color_label = tk.Label(prompt_window, text=line_prompt)
    thickness_label = tk.Label(prompt_window, text=thickness_prompt)
    fill_color_button = tk.Button(prompt_window, text="Alterar", command=lambda: self.change_fill_color(target, prompt_window))
    line_color_button = tk.Button(prompt_window, text="Alterar", command=lambda: self.change_line_color(target, prompt_window))
    thickness_input = tk.Entry(prompt_window)
    thickness_button = tk.Button(prompt_window, text="Alterar", command=lambda: self.change_thickness(target, thickness_input.get(), prompt_window))
    name_label.grid(row=0, column=0)
    name_input.grid(row=0, column=1)
    name_button.grid(row=0, column=2)
    line_color_label.grid(row=1, column=0, columnspan=2)
    line_color_button.grid(row=1, column=2)
    thickness_label.grid(row=2, column=0)
    thickness_input.grid(row=2, column=1)
    thickness_button.grid(row=2, column=2)
    if fill_prompt:
      fill_color_label.grid(row=3, column=0, columnspan=2)
      fill_color_button.grid(row=3, column=2)

    if isinstance(target, CurveObject_2D):
      control_points_label = tk.Label(prompt_window, text=control_points_prompt + ": " + ", ".join(f"({p[0]:.2f}, {p[1]:.2f})" for p in target.control_points), wraplength=300, justify="left")
      control_points_label.grid(row=5, column=0, columnspan=2)
      alter_control_points_button = tk.Button(prompt_window, text="Alterar", command=lambda: self.add_curve(target, prompt_window))
      alter_control_points_button.grid(row=5, column=2)

  def get_selected_object(self) -> Wireframe | None:
    selected = self.ui_object_list.selection()
    selected_id = self.ui_object_list.item(selected[0], "tags")[0] if selected else None
    return self.get_object_by_id(int(selected_id)) if selected_id else None

  def get_object_by_id(self, id: int) -> Wireframe | None:
    return next((o for o in self.objects if o.id == id), None)

  @property
  def building(self) -> bool: return self._building

  @building.setter
  def building(self, value: bool):
    self._building = value
