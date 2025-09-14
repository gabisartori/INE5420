import tkinter as tk
from .color_scheme import ColorScheme

class ToggleSwitch(tk.Canvas):
  def __init__(self, master=None, width=60, height=30, on_toggle=None, **kwargs):
    super().__init__(master, width=width, height=height, bg=ColorScheme.LIGHT_BG.value, highlightthickness=0)
    self.on_toggle = on_toggle
    self.width = width
    self.height = height
    self.is_on = False

    self.bg_rect = self.create_oval(6, 6, width-8, height-8, fill="#ccc", outline="")
    self.knob = self.create_oval(6, 6, height-6, height-6, fill="#fff", outline="")
    self.configure(background=kwargs.get("bg", ColorScheme.LIGHT_BG.value))
    self.bind("<Button-1>", self.toggle)

  def toggle(self, event=None):
    self.is_on = not self.is_on
    if self.is_on: #dark mode
      self.itemconfig(self.bg_rect, fill="#4cd137")  # Cor de fundo ON
      self.move(self.knob, self.width - self.height, 0)
      self.configure(bg=ColorScheme.DARK_BG.value)
    else:
      self.itemconfig(self.bg_rect, fill="#ccc")    # Cor de fundo OFF
      self.move(self.knob, -(self.width - self.height), 0)
      self.configure(bg=ColorScheme.LIGHT_BG.value)
    if self.on_toggle:
      self.on_toggle(self.is_on)
