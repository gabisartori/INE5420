import tkinter as tk
from tkinter import ttk, messagebox, font, colorchooser, simpledialog, scrolledtext
from wireframe import *
from window import *
from components.toggle_switch import *
from components.my_types import *
from data.usr_preferences import *
from clipping import Clipping, ClippingAlgorithm

class Viewport:
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

  def set_curve_config(self):
    steps = simpledialog.askinteger("Configuração de Curvas", "Número de passos para desenhar curvas de Bézier (padrão 100):", initialvalue=self.window.bezier_steps, minvalue=10, maxvalue=1000)
    if steps:
      self.window.bezier_steps = steps
      self.log(f"Número de passos para desenhar curvas de Bézier alterado para {steps}.")
      self.update() 
          
  def add_object_to_table(self, obj: Wireframe):
    formatted_coordinates = [f"({', '.join(f'{coord:.2f}' for coord in point)})" for point in obj.points]
    self.ui_object_list.insert("", "end", values=(obj.name, ", ".join(formatted_coordinates)), tags=(str(obj.id),))

    font_style = font.nametofont("TkDefaultFont")
    font_size = font_style.measure("".join(formatted_coordinates)) + 20

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
