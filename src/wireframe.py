from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from tkinter import Canvas

from my_types import WorldPoint, WindowPoint

class WindowObject:
  def draw(self, canva: Canvas) -> None: pass

@dataclass
class WindowPointObject(WindowObject):
  p: WindowPoint

  def draw(self, canva: Canvas) -> None:
    canva.create_oval(self.x.x-2, self.x.y-2, self.x.x+2, self.x.y+2, fill="black")

@dataclass
class WindowLineObject(WindowObject):
  start: WindowPoint
  end: WindowPoint

  def draw(self, canva: Canvas) -> None:
    canva.create_line(self.start.x, self.start.y, self.end.x, self.end.y, fill="black")

@dataclass
class WindowPolygonObject(WindowObject):
  points: list[WindowPoint]
  texture: str | None = None

  def draw(self, canva: Canvas) -> None:
    coords = []
    for point in self.points:
      coords.extend([point.x, point.y])
    canva.create_polygon(*coords, outline="black", fill=self.texture if self.texture else "")

class CurveType(Enum):
  BEZIER = 0
  B_SPLINE = 1

  def __str__(self) -> str:
    if self == CurveType.BEZIER: return "Bézier"
    elif self == CurveType.B_SPLINE: return "B-Spline"
    return "Unknown"

@dataclass
class Curve:
  curve_type: CurveType
  # TODO: This is unnecessarily messy, the curve has its control points as indices of the wireframe's vertices
  # But it needs the actual points to generate the curve points, so the wireframe has to give them to the curve every time the curve points are generated.
  # This should be fixed, either by making the curve store the actual points, or something else
  control_points: list[int]
  steps: int

  @staticmethod
  def bezier_algorithm(t, P0: WindowPoint, P1: WindowPoint, P2: WindowPoint, P3: WindowPoint) -> WindowPoint:
    """Calculate points on a cubic Bezier curve defined by four control points."""
    t = np.array([(1 - t)**3, 3 * (1 - t)**2 * t, 3 * (1 - t) * t**2, t**3])
    return np.dot(t, np.array([P0, P1, P2, P3]))

  def generate_bezier_points(self, control_points: list[WindowPoint]) -> list[WindowPoint]:
    """Generate points on the Bezier curve defined by the control points."""
    if len(control_points) < 4:
      raise ValueError("Cubic Bezier curve requires at least 4 control points.")

    curve_points = []
    for i in range(0, len(control_points) - 3, 3):
      P0, P1, P2, P3 = control_points[i:i+4]
      curve_segment = [self.bezier_algorithm(step / self.steps, P0, P1, P2, P3) for step in range(self.steps + 1)]

      # Avoid duplicating points at segment joins
      if curve_points:
        curve_segment = curve_segment[1:]

      curve_points.extend(curve_segment)
    self.points = curve_points
    return curve_points

  def generate_b_spline_points(self, control_points: list[WindowPoint]) -> list[WindowPoint]:
    """Generate points on a B-Spline curve defined by the control points using the forward difference method."""
    if len(control_points) < 4:
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

    for i in range(0, len(control_points) - 3):
      P0, P1, P2, P3 = control_points[i:i+4]
      Gx = np.array([P0.x, P1.x, P2.x, P3.x])
      Gy = np.array([P0.y, P1.y, P2.y, P3.y])
      # Gz = np.array([P0[2], P1[2], P2[2], P3[2]])

      # Coeficientes da curva
      Cx = M @ Gx
      Cy = M @ Gy
      # Cz = M @ Gz

      # Valores iniciais
      x = Cx[3]
      y = Cy[3]
      # z = Cz[3]

      # Primeiras diferenças
      dx = Cx[2] * h + Cx[1] * h**2 + Cx[0] * h**3
      dy = Cy[2] * h + Cy[1] * h**2 + Cy[0] * h**3
      # dz = Cz[2] * h + Cz[1] * h**2 + Cz[0] * h**3
      # Segundas diferenças
      d2x = 2 * Cx[1] * h**2 + 6 * Cx[0] * h**3
      d2y = 2 * Cy[1] * h**2 + 6 * Cy[0] * h**3
      # d2z = 2 * Cz[1] * h**2 + 6 * Cz[0] * h**3
      # Terceiras diferenças
      d3x = 6 * Cx[0] * h**3
      d3y = 6 * Cy[0] * h**3
      # d3z = 6 * Cz[0] * h**3

      for _ in range(self.steps + 1):
        new_point = WindowPoint(x, y)
        curve_points.append(new_point)

        x += dx
        dx += d2x
        d2x += d3x

        y += dy
        dy += d2y
        d2y += d3y

        # z += dz
        # dz += d2z
        # d2z += d3z

    self.points = curve_points
    return curve_points

  def get_lines(self, control_points: list[WindowPoint]) -> list[tuple[WindowPoint, WindowPoint]]:
    match self.curve_type:
      case CurveType.BEZIER:
        points = self.generate_bezier_points(control_points)
      case CurveType.B_SPLINE:
        points = self.generate_b_spline_points(control_points)
      case _:
        points = []
    return [(points[i], points[i+1]) for i in range(len(points)-1)]

  def line_objects(self, control_points: list[WindowPoint]) -> list[WindowLineObject]:
    return [WindowLineObject(line[0], line[1]) for line in self.get_lines(control_points)]

@dataclass
class Surface:
  @property
  def window_objects(self) -> list[WindowObject]: return []

@dataclass 
class Wireframe:
  wireframe_id: int
  name: str
  vertices: list[WorldPoint] = field(default_factory=list)  # List of vertices, each vertex is a numpy array of 4 elements (x, y, z, 1)
  projected_vertices: list[WindowPoint] = field(default_factory=list)  # List of projected vertices in window coordinates
  edges: list[tuple[int, int]] = field(default_factory=list)  # (start vertex index, end vertex index)
  faces: list[tuple[list[int], str | None]] = field(default_factory=list)  # (vertex indices, fill color)
  curves: list[Curve] = field(default_factory=list)
  surfaces: list[Surface] = field(default_factory=list)  # Placeholder for future surface implementations

  def copy(self) -> 'Wireframe':
    return Wireframe(
      self.wireframe_id,
      self.name,
      [v.copy() for v in self.vertices],
      [v.copy() for v in self.projected_vertices],
      [edge[:] for edge in self.edges],
      [(face[0][:], face[1]) for face in self.faces],
      [Curve(c.curve_type, c.control_points[:], c.steps) for c in self.curves],
      []
    )
  
  def __str__(self) -> str:
    vertices_str = '\n'.join(f"v {' '.join(map(str, v[:-1]))}" for v in self.vertices)
    edges_str = '\n'.join(f"l {start} {end}" for start, end in self.edges)
    faces_str = '\n'.join(f"f {' '.join(str(idx) for idx in face[0])}" + (f" {face[1]}" if face[1] else "") for face in self.faces)
    curves_str = '\n'.join(f"c {' '.join(str(idx) for idx in curve.control_points)} {curve.steps} {curve.curve_type.name.lower()}" for curve in self.curves)
    return f"o {self.name}\n{vertices_str}\n{edges_str}\n{faces_str}\n{curves_str}"

  @property
  def window_objects(self) -> list[WindowObject]:
    objects: list[WindowObject] = []
    for start_idx, end_idx in self.edges: objects.append(WindowLineObject(self.projected_vertices[start_idx], self.projected_vertices[end_idx]))
    for face in self.faces:
      face_vertices = [self.projected_vertices[idx] for idx in face[0]]
      objects.append(WindowPolygonObject(face_vertices, texture=face[1]))
    for curve in self.curves: objects.extend(curve.line_objects([self.projected_vertices[x] for x in curve.control_points]))
    for surface in self.surfaces: objects.extend(surface.window_objects)  # Not implemented yet, should be an empty list
    if objects == []:  # If there are no edges, faces or curves, draw the vertices as points
      for v in self.projected_vertices: objects.append(WindowPointObject(v))

    return objects

  @classmethod
  def load_file(cls, file_path: str, wireframe_id: int) -> list['Wireframe']: return []

  def rotate(self, degrees: int=5, point: WorldPoint | None=None, a1: int=0, a2: int=1) -> None:
    """Rotates the object around a given point in the XY plane.
    If no point is given, rotate around the center of the object.

    The XY plane is chosen as the default plane for the 2D implementation of the program. This will then be replaced by the specific XY rotation for the 3D implementation.
    """

    point = point if point is not None else self.center

    # Move the object to be centered around the rotation point.
    self.translate(*-point[:3])
    # TODO: When needing to specify which plane the rotation is in, all that needs to change is which matrix is being used.
    # Apply the rotation matrix.
    M = np.eye(4)
    M[a1, a1] = np.cos(np.radians(degrees))
    M[a1, a2] = -np.sin(np.radians(degrees))
    M[a2, a1] = np.sin(np.radians(degrees))
    M[a2, a2] = np.cos(np.radians(degrees))
    self.transform(M)
    # Move the object back to its original position.
    self.translate(*point[:3])

  def translate(self, dx: float, dy: float, dz: float) -> None:
    """Translate the object in the XY plane.
    
    Everything that was said about the XY plane in the rotate() method also applies here.
    """
    self.transform(np.array([
      [1, 0, 0, dx],
      [0, 1, 0, dy],
      [0, 0, 1, dz],
      [0, 0, 0, 1]
    ]))

  def scale(self, factor: float) -> None:
    """Scale the object in the XY plane."""
    self.translate(*-self.center[:3])
    self.transform(np.array([
      [factor, 0, 0, 0],
      [0, factor, 0, 0],
      [0, 0, factor, 0],
      [0, 0, 0, 1]
    ]))
    self.translate(*self.center[:3])

  def transform(self, M: np.ndarray) -> None:
    """Applies the given matrix to all of the object's vertices."""
    self.vertices = [M @ v for v in self.vertices]

  @property
  def center(self) -> WorldPoint:
    return np.mean(self.vertices, axis=0).astype(int)

@dataclass
class PastWireframe:
  """Parent class for all PastWireframe objects.
  Each subclass will implement its own way of manipulating the *points* attribute.

  Attributes:
  - name: Name of the object, to be displayed in object lists.
  TODO: the definition of *points* may not match what's actually built in the code.
  - points: List of points that define the object. Each point is a numpy array of 3 or 4 elements, which will be treated as 2D (x, y, 1) or 3D (x, y, z, 1) homogeneous coordinates.
  - fill_color: Color used to fill the object when rendering (if applicable).
  - line_color: Color used to draw the object's edges.
  - thickness: Thickness of the lines used to draw the object.
  - id: Unique identifier for the object. The main program class will keep count of the last used ID and assign a new one when creating a new object.
  """
  name: str
  points: list[WorldPoint]
  fill_color: str = "white"
  line_color: str = "black"
  thickness: float = 1
  id: int = 0

  def copy(self) -> 'PastWireframe': raise NotImplementedError("Subclasses should implement this method")

  def __str__(self) -> str: raise NotImplementedError("Subclasses should implement this method")
