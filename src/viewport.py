import tkinter as tk
from wireframe import *
from screen import *

class Viewport:
  def __init__(self, width, height, title="INE5420", input: str="", output: str="", debug: bool=False):
    self.output: str = output
    
    self.width: int = width
    self.height: int = height
    self.objects: list[Wireframe] = self.load_objects(input)
    self.build: list[Point] = []
    self.building: bool = False
    self.debug: bool = debug

    self.camera = Camera(np.array([0, -1, 0]), np.array([0, 0, 0]), width*0.8, height*0.8)

    # Ui Componentes
    self.root: tk.Tk = tk.Tk()
    self.root.geometry(f"{width}x{height}")
    self.root.title(title)
    self.canva = tk.Canvas(self.root, background="white", width=0.8 * self.width, height=0.8 * self.height)
    self.build_button = tk.Button(self.root, text="Build", command=self.set_building)
    self.lines_button = tk.Button(self.root, text="Lines", command=self.finish_lines)
    self.polygon_button = tk.Button(self.root, text="Polygon", command=self.finish_polygon)
    self.clear_button = tk.Button(self.root, text="Clear", command=self.clear)

    self.controls()
    self.build_ui()
    self.update()

  def set_building(self): self.building = True

  def clear(self):
    self.objects.clear()
    self.build.clear()
    self.building = False
    self.update()

  def controls(self):
    self.canva.bind("<ButtonRelease-1>", self.canva_click)
    self.root.bind("<Button-4>", lambda e: self.camera.zoom_in(e.x, e.y) or self.update())
    self.root.bind("<Button-5>", lambda e: self.camera.zoom_out(e.x, e.y) or self.update())
    self.root.bind("<KeyPress-w>", lambda e: self.camera.move_up() or self.update())
    self.root.bind("<KeyPress-s>", lambda e: self.camera.move_down() or self.update())
    self.root.bind("<KeyPress-a>", lambda e: self.camera.move_left() or self.update())
    self.root.bind("<KeyPress-d>", lambda e: self.camera.move_right() or self.update())
    self.root.bind("<KeyPress-q>", lambda e: self.camera.move_below() or self.update())
    self.root.bind("<KeyPress-e>", lambda e: self.camera.move_above() or self.update())

  def build_ui(self):
    self.canva.grid(row=0, column=0)
    self.build_button.grid(row=0, column=1)
    self.lines_button.grid(row=1, column=1)
    self.polygon_button.grid(row=2, column=1)
    self.clear_button.grid(row=3, column=1)

  def canva_click(self, event):
    if self.building: self.build.append(self.camera.get_clicked_point(event.x, event.y))
    else: self.objects.append(PointObject("Clicked Point", self.camera.get_clicked_point(event.x, event.y)))
    self.update()

  def finish_lines(self):
    if len(self.build) < 2: print("Erro: Pelo menos dois pontos são necessários para formar uma linha."); return
    for i in range(len(self.build) - 1):
      start, end = self.build[i:i+2]
      self.objects.append(LineObject(f"Line {i+1}", start, end))
    self.build.clear()
    self.building = False
    self.update()

  def finish_polygon(self):
    if len(self.build) < 3: print("Erro: Pelo menos três pontos são necessários para formar um polígono."); return
    self.objects.append(PolygonObject("Polygon", self.build.copy()))
    self.build.clear()
    self.building = False
    self.update()

  def update(self):
    self.canva.delete("all")
    for obj in self.objects:
      for edge in obj.figures():
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
    return self.objects

  def load_objects(self, objects: str) -> list[Wireframe]:
    if not objects: return []
    try:
      with open(objects, "r") as file:
        return [Wireframe.from_string(line.strip()) for line in file if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
      print(f"Arquivo {objects} não encontrado.")
      return []
    except Exception as e:
      print(f"Erro ao carregar objetos: {e}")
      return []
    