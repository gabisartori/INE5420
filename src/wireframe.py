from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import math
from tkinter import Canvas

from my_types import WorldPoint, WindowPoint

class WindowObject:
  def draw(self, canva: Canvas, color: str="black") -> None: pass

@dataclass
class WindowPointObject(WindowObject):
  p: WindowPoint

  def draw(self, canva: Canvas, color: str="black") -> None:
    canva.create_oval(self.p.x-2, self.p.y-2, self.p.x+2, self.p.y+2, fill=color)

@dataclass
class WindowLineObject(WindowObject):
  start: WindowPoint
  end: WindowPoint

  def draw(self, canva: Canvas, color: str="black") -> None:
    canva.create_line(self.start.x, self.start.y, self.end.x, self.end.y, fill=color)

@dataclass
class WindowPolygonObject(WindowObject):
  points: list[WindowPoint]
  texture: str | None = None

  def draw(self, canva: Canvas, color: str="black") -> None:
    coords = []
    for p in self.points: coords.extend([p.x, p.y])
    canva.create_polygon(*coords, outline="black", fill=self.texture if self.texture else "")

class CurveType(Enum):
  BEZIER = 0
  B_SPLINE = 1

  @classmethod
  def from_obj_name(cls, name: str) -> 'CurveType | None':
    name = name.lower()
    if name == "bezier": return CurveType.BEZIER
    elif name == "bspline": return CurveType.B_SPLINE
    return None

  def obj_name(self) -> str:
    if self == CurveType.BEZIER: return "bezier"
    elif self == CurveType.B_SPLINE: return "bspline"
    return "unknown"

  def __str__(self) -> str:
    if self == CurveType.BEZIER: return "Bézier"
    elif self == CurveType.B_SPLINE: return "B-Spline"
    return "Unknown"

@dataclass
class Curve:
  curve_type: CurveType
  control_points: list[int]
  start: float = 0.0
  end: float = 1.0
  degree: int = 4

  @staticmethod
  def bezier_algorithm(t, *points: WindowPoint) -> WindowPoint:
    """Calculate points on a cubic Bezier curve defined by four control points."""
    n = len(points)
    tv = np.array([(1-t)**(n-1-i) * t**i * math.comb(n-1, i) for i in range(n)], dtype=float)
    return WindowPoint(*(np.dot(tv, np.array(points))[:2]))

  def generate_bezier_points(self, control_points: list[WindowPoint], curve_coefficient: int) -> list[WindowPoint]:
    """Generate points on the Bezier curve defined by the control points."""
    curve_points = []
    for points in zip(*(control_points[i::self.degree-1] for i in range(self.degree))):
      curve_segment = [self.bezier_algorithm(step / curve_coefficient, *points) for step in range(curve_coefficient + 1)]

      # Avoid duplicating points at segment joins
      if curve_points:
        curve_segment = curve_segment[1:]

      curve_points.extend(curve_segment)
    self.points = curve_points
    return curve_points

  def generate_b_spline_points(self, control_points: list[WindowPoint], curve_coefficient: int) -> list[WindowPoint]:
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
    h = 1 / curve_coefficient

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

      for _ in range(curve_coefficient + 1):
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

  def get_lines(self, control_points: list[WindowPoint], curve_coefficient: int) -> list[tuple[WindowPoint, WindowPoint]]:
    match self.curve_type:
      case CurveType.BEZIER: points = self.generate_bezier_points(control_points, curve_coefficient)
      case CurveType.B_SPLINE: points = self.generate_b_spline_points(control_points, curve_coefficient)
      case _: points = []
    return [(points[i], points[i+1]) for i in range(len(points)-1)]

  def line_objects(self, control_points: list[WindowPoint], curve_coefficient: int) -> list[WindowLineObject]:
    return [WindowLineObject(line[0], line[1]) for line in self.get_lines(control_points, curve_coefficient)]

  def __str__(self) -> str:
    output = f"cstype {self.curve_type.obj_name()}\n"
    output += f"deg {self.degree}\n"
    output += f"curv {self.start} {self.end} {' '.join(str(idx+1) for idx in self.control_points)}\n"
    output += "parm u 0 1"
    return output

  def copy(self) -> 'Curve':
    return Curve(self.curve_type, self.control_points[:], self.degree)

@dataclass
class Surface:
  surface_type: CurveType = CurveType.BEZIER
  control_points: list[int] = field(default_factory=list)
  degrees: tuple[int, int] = (4, 4)
  start_u: float = 0.0
  end_u: float = 1.0
  start_v: float = 0.0
  end_v: float = 1.0

  @property
  def window_objects(self) -> list[WindowObject]: return []

  def copy(self) -> 'Surface': return Surface()

  def __str__(self) -> str:
    output = f"cstype {self.surface_type.obj_name()}\n"
    output += f"deg {self.degrees[0]} {self.degrees[1]}\n"
    output += f"surf {self.start_u} {self.end_u} {self.start_v} {self.end_v} {' '.join(str(idx+1) for idx in self.control_points)}\n"
    output += "parm u 0 1\nparm v 0 1"
    return output

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
      [c.copy() for c in self.curves],
      [s.copy() for s in self.surfaces]
    )
  
  def __str__(self) -> str:
    vertices_str = '\n'.join(f"v {' '.join(map(str, v[:-1]))}" for v in self.vertices)
    edges_str = '\n'.join(f"l {start+1} {end+1}" for start, end in self.edges)
    faces_str = "\n".join([self.polygon_str(face) for face in self.faces])
    curves_str = "\n".join([str(curve) for curve in self.curves])
    surfaces_str = "\n".join([str(surface) for surface in self.surfaces])
    
    parts = [f"o {self.name}"]
    if vertices_str: parts.append(vertices_str)
    if edges_str: parts.append(edges_str)
    if faces_str: parts.append(faces_str)
    if curves_str: parts.append(curves_str)
    if surfaces_str: parts.append(surfaces_str)
    return "\n\n".join(parts) + "\n"

  @staticmethod
  def polygon_str(face: tuple[list[int], str | None]) -> str:
    vertices, texture = face
    texture_str = f"usemtl {texture}\n" if texture else ""
    return f"{texture_str}f {' '.join(str(idx+1) for idx in vertices)}"

  def distance(self, window: np.ndarray) -> float:
    """Calculate the distance from the object's center to the window's position."""
    center = self.center[:3]
    window_pos = window[:3]
    return np.linalg.norm(center - window_pos).astype(float)

  def window_objects(self, curve_coefficient: int) -> list[WindowObject]:
    objects: list[WindowObject] = []
    for start_idx, end_idx in self.edges: objects.append(WindowLineObject(self.projected_vertices[start_idx], self.projected_vertices[end_idx]))
    for face in self.faces:
      face_vertices = [self.projected_vertices[idx] for idx in face[0]]
      objects.append(WindowPolygonObject(face_vertices, texture=face[1]))
    for curve in self.curves: objects.extend(curve.line_objects([self.projected_vertices[x] for x in curve.control_points], curve_coefficient))
    for surface in self.surfaces: objects.extend(surface.window_objects)  # Not implemented yet, should be an empty list
    if objects == []:  # If there are no edges, faces or curves, draw the vertices as points
      for v in self.projected_vertices: objects.append(WindowPointObject(v))

    return objects

  @classmethod
  def load_file(cls, filepath: str | None) -> list['Wireframe']:
    if filepath is None: return []
    objects: list[Wireframe] = []
    current_vertices: list[WorldPoint] = []
    current_edges: list[tuple[int, int]] = []
    current_faces: list[tuple[list[int], str | None]] = []
    current_curves: list[Curve] = []
    current_surfaces: list[Surface] = []

    current_name: str = ""
    current_texture: str | None = None
    with open(filepath, 'r') as f:
      while line := f.readline():
        if line.startswith('#') or line.strip() == '': continue  # Skip comments and empty lines
        header, *body = line.split()

        match header:
          case 'o' | 'g':
            # Save previous object if it exists
            if current_name:
              objects.append(Wireframe(
                wireframe_id=len(objects),
                name=current_name,
                vertices=current_vertices,
                edges=current_edges,
                faces=current_faces,
                curves=current_curves,
                surfaces=current_surfaces
              ))
            # Reset building variables for new object
            current_name = body[0]
            current_vertices = []
            current_edges = []
            current_faces = []
            current_curves = []
            current_surfaces = []

          case 'v':
            if len(body) < 3: raise ValueError(f"Invalid vertex line: {line.strip()}")
            x, y, z = map(float, body[:3])
            current_vertices.append(np.array([x, y, z, 1.0]))
          
          case 'l':
            if len(body) < 2: raise ValueError(f"Invalid line (edge) line: {line.strip()}")
            body = [int(i)-1 for i in body]
            for start, end in zip(body, body[1:]): current_edges.append((start, end))

          # TODO: Currently it follows the format "usemtl <color>" where color is any string accepted by tkinter
          # Real wavefront shoul define a material library and reference it here, where it material is in rgb format
          case 'usemtl':
            if len(body) < 1: raise ValueError(f"Invalid usemtl line: {line.strip()}")
            current_texture = body[0]

          case 'f':
            if len(body) < 3: raise ValueError(f"Invalid face line: {line.strip()}")
            vertices = [int(x)-1 for x in body]
            current_faces.append((
              vertices,
              current_texture
            ))
            current_texture = None
          
          case 'cstype':
            if len(body) < 1: raise ValueError(f"Invalid cstype line: {line.strip()}")
            curve_type = CurveType.from_obj_name(body[0])
            if curve_type is None: raise ValueError(f"Unknown curve type: {body[0]}")

            deg_header, *deg_values = f.readline().split()
            if deg_header != 'deg' or len(deg_values) < 1: raise ValueError(f"Invalid deg line: {' '.join([deg_header]+deg_values)}")
            deg_values = [int(x) for x in deg_values]

            t, *points = f.readline().split()
            if t == "curv":
              start, end = [float(x) for x in points[:2]]
              points = [int(x)-1 for x in points[2:]]
              if len(points) < deg_values[0]: raise ValueError(f"Number of control points {len(points)} does not match curve degree {deg_values[0]}")
              current_curves.append(Curve(curve_type, points, start, end, deg_values[0] if deg_values else len(points)))
            elif t == "surf":
              su, eu, sv, ev = [float(x) for x in points[:4]]
              points = [int(x)-1 for x in points[4:]]
              if len(deg_values) < 2: raise ValueError(f"Invalid surface degrees line: {' '.join(map(str, deg_values))}")
              if len(points) < deg_values[0]*deg_values[1]: raise ValueError(f"Number of control points {len(points)} does not match surface degrees {deg_values[0]} and {deg_values[1]} (should be {deg_values[0]*deg_values[1]})")
              current_surfaces.append(Surface(curve_type, points, (deg_values[0], deg_values[1]), su, eu, sv, ev))
            else: raise ValueError(f"Invalid curve/surface line: {line.strip()}")

          case 'parm': continue

    # Append last object since it won't be appended in the loop
    objects.append(Wireframe(
      wireframe_id=len(objects),
      name=current_name,
      vertices=current_vertices,
      edges=current_edges,
      faces=current_faces,
      curves=current_curves,
      surfaces=current_surfaces
    ))
    return objects

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
    return np.mean(self.vertices, axis=0).astype(float)
