import tkinter as tk
from tkinter import ttk, messagebox, font, colorchooser, simpledialog, scrolledtext
from wireframe import *
from window import *
from components.toggle_switch import *
from components.my_types import *
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
