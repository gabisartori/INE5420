from dataclasses import dataclass, field
from components.my_types import Point
import numpy as np

@dataclass
class Wireframe:
  name: str
  points: list[Point]
  fill_color: str = "white"
  line_color: str = "black"
  thickness: float = 1
  id: int = 0

  def copy(self) -> 'Wireframe': raise NotImplementedError("Subclasses should implement this method")

  def __str__(self) -> str: raise NotImplementedError("Subclasses should implement this method")

  def rotate(self, degrees: int=5, point: Point | None=None) -> None:
    """Rotate the object around a given point in the XY plane."""
    """If no point is given, rotate around the center of the object."""
    if point is not None:
      px = point[0]
      py = point[1]
    else:
      px = self.center[0]
      py = self.center[1]
    self.translate(-px, -py)
    self.transform2d(np.array([
      [np.cos(np.radians(degrees)), -np.sin(np.radians(degrees)), 0],
      [np.sin(np.radians(degrees)),  np.cos(np.radians(degrees)), 0],
      [0, 0, 1]
    ]))
    self.translate(px, py)

  def translate(self, dx: float, dy: float) -> None:
    """Translate the object in the XY plane."""
    self.transform2d(np.array([
      [1, 0, dx],
      [0, 1, dy],
      [0, 0, 1]
    ]))

  def scale(self, factor: float) -> None:
    """Scale the object in the XY plane."""
    px = self.center[0]
    py = self.center[1]
    self.translate(-px, -py)
    self.transform2d(np.array([
      [factor, 0, 0],
      [0, factor, 0],
      [0, 0, 1]
    ]))
    self.translate(px, py)

  def transform2d(self, M: np.ndarray) -> None:
    """Aplica M (3x3 homogênea) aos pontos no plano XZ, mantendo Y."""
    self.points = [M @ p for p in self.points]

  @property
  def center(self) -> Point:
    return np.mean(self.points, axis=0).astype(int)

class PointObject(Wireframe):
  def __init__(self, name: str, center: Point, **kwargs):
    super().__init__(name, [center], **kwargs)

  def copy(self) -> 'PointObject':
    return PointObject(
      self.name,
      self.points[0].copy(),
      id=self.id,
      thickness=self.thickness,
      line_color=self.line_color,
      fill_color=self.fill_color
    )

  def __str__(self) -> str:
    return f"o {self.name}\nv {' '.join(map(str, self.points[0]))}\np 1"

class LineObject(Wireframe):
  def __init__(self, name: str, start: Point, end: Point, **kwargs):
    super().__init__(name, [start, end], **kwargs)
  def copy(self) -> 'LineObject':
    return LineObject(
      self.name,
      self.points[0].copy(),
      self.points[1].copy(),
      id=self.id,
      thickness=self.thickness,
      line_color=self.line_color,
      fill_color=self.fill_color
    )

  def __str__(self) -> str:
    return f"o {self.name}\nv {' '.join(map(str, self.points[0]))}\nv {' '.join(map(str, self.points[1]))}\nl 1 2"

class PolygonObject(Wireframe):
  def __init__(self, name: str, points: list[Point], **kwargs):
    super().__init__(name, points, **kwargs)

  def copy(self) -> 'PolygonObject':
    return PolygonObject(
      self.name,
      [p.copy() for p in self.points],
      id=self.id,
      thickness=self.thickness,
      line_color=self.line_color,
      fill_color=self.fill_color
    )

  def __str__(self) -> str:
    vertices_str = '\n'.join(f"v {' '.join(map(str, p))}" for p in self.points)
    indices_str = ' '.join(str(i + 1) for i in range(len(self.points)))
    return f"o {self.name}\n{vertices_str}\nl {indices_str}"

class CurveObject_2D(Wireframe):
  def __init__(self, name: str, points: list[Point], steps: int, **kwargs):
    self.steps = steps
    self.control_points = points
    super().__init__(name, [], **kwargs)
    
    #self.generate_bezier_points() if kwargs.get("curve_type", "bezier") == "bezier" else self.generate_b_spline_points()

  def copy(self) -> 'CurveObject_2D':
    new_obj = CurveObject_2D(
      name=self.name,
      points=[p.copy() for p in self.control_points], 
      steps=self.steps,
      id=self.id,
      thickness=self.thickness,
      line_color=self.line_color,
      fill_color=self.fill_color
    )
    new_obj.points = [p.copy() for p in self.points]
    return new_obj
        
  def bezier_algorithm(self, t, P0, P1, P2, P3) -> Point:
    """Calculate points on a cubic Bezier curve defined by four control points."""
    x = (1 - t)**3 * P0[0] + 3 * (1 - t)**2 * t * P1[0] + 3 * (1 - t) * t**2 * P2[0] + t**3 * P3[0]
    y = (1 - t)**3 * P0[1] + 3 * (1 - t)**2 * t * P1[1] + 3 * (1 - t) * t**2 * P2[1] + t**3 * P3[1]
    new_point = np.array([x, y, 1])
    return new_point

  def generate_bezier_points(self) -> list[Point]:
    """Generate points on the Bezier curve defined by the control points."""
    if len(self.control_points) < 4:
      raise ValueError("Cubic Bezier curve requires at least 4 control points.")
    
    curve_points = []
    for i in range(0, len(self.control_points) - 3, 3):
      P0, P1, P2, P3 = self.control_points[i:i+4]
      curve_segment = [self.bezier_algorithm(step / self.steps, P0, P1, P2, P3) for step in range(self.steps + 1)]
      
      # Avoid duplicating points at segment joins
      if curve_points:
        curve_segment = curve_segment[1:]
      
      curve_points.extend(curve_segment)
    self.points = curve_points
    return curve_points
  
  def generate_b_spline_points(self) -> list[Point]:
    """Generate points on a B-Spline curve defined by the control points using the forward difference method."""
    if len(self.control_points) < 4:
      raise ValueError("Cubic B-Spline curve requires at least 4 control points.")
        
    # Algoritmo para Desenho de Curvas Paramétricas usando Forward Differences
    # DesenhaCurvaFwdDiff( n, x, ∆x, ∆2x, ∆3x,
    # y, ∆y, ∆2y, ∆3y,
    # z, ∆z, ∆2z, ∆3z )
    # início
    # inteiro i = 0;
    # mova(x, y, z);/* Move ao início da curva */
    # enquanto i < n faça
    # i <- i + 1;
    # x <- x + ∆x; ∆x <- ∆x + ∆2x; ∆2x <- ∆2x + ∆3x;
    # y <- y + ∆y; ∆y <- ∆y + ∆2y; ∆2y <- ∆2y + ∆3y;
    # z <- z + ∆z; ∆z <- ∆z + ∆2z; ∆2z <- ∆2z + ∆3z;
    # desenheAté(x, y, z); /* Desenha reta */
    # fim enquanto;
    # fim DesenhaCurvaFwdDiff;
    
    curve_points = []
    h = 1 / self.steps
    
    M = np.array([
      [-1/6,  3/6, -3/6, 1/6],
      [ 3/6, -6/6,  3/6, 0],
      [-3/6,  0,    3/6, 0],
      [ 1/6,  4/6,  1/6, 0]
    ])
    
    for i in range(0, len(self.control_points) - 3):
      P0, P1, P2, P3 = self.control_points[i:i+4]
      Gx = np.array([P0[0], P1[0], P2[0], P3[0]])
      Gy = np.array([P0[1], P1[1], P2[1], P3[1]])
      
      # Coeficientes da curva
      Cx = M @ Gx
      Cy = M @ Gy
      
      # Valores iniciais
      x = Cx[3]
      y = Cy[3]
      
      # Primeiras diferenças
      dx = Cx[2] * h + Cx[1] * h**2 + Cx[0] * h**3
      dy = Cy[2] * h + Cy[1] * h**2 + Cy[0] * h**3
      # Segundas diferenças
      d2x = 2 * Cx[1] * h**2 + 6 * Cx[0] * h**3
      d2y = 2 * Cy[1] * h**2 + 6 * Cy[0] * h**3
      # Terceiras diferenças
      d3x = 6 * Cx[0] * h**3
      d3y = 6 * Cy[0] * h**3
      
      for step in range(self.steps):
        new_point = np.array([x, y, 1])
        curve_points.append(new_point)
        
        x += dx
        dx += d2x
        d2x += d3x
        
        y += dy
        dy += d2y
        d2y += d3y
    self.points = curve_points
    return curve_points

  def __str__(self) -> str:
    vertices_str = '\n'.join(f"v {' '.join(map(str, p))}" for p in self.control_points)
    indices_str = ' '.join(str(i + 1) for i in range(len(self.control_points)))
    return f"o {self.name}\n{vertices_str}\nc {indices_str}"
