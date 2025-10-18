from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import math
from tkinter import Canvas

from my_types import WorldPoint, WindowPoint

class WindowObject:
  '''Representa a projeção de um objeto do mundo no plano da janela.
  Cada objeto do mundo pode ser representado por um ou vários WindowObjects.
  Cada WindowObject se desenha no canvas a partir de seu(s) ponto(s) (x, y) na janela.
  '''
  def draw(self, canva: Canvas, color: str="black") -> None: pass

@dataclass
class WindowPointObject(WindowObject):
  '''Representa um ponto na janela.'''
  p: WindowPoint

  def draw(self, canva: Canvas, color: str="black") -> None:
    canva.create_oval(self.p.x-2, self.p.y-2, self.p.x+2, self.p.y+2, fill=color)

@dataclass
class WindowLineObject(WindowObject):
  '''Linha na janela, definida por dois pontos.'''
  start: WindowPoint
  end: WindowPoint

  def draw(self, canva: Canvas, color: str="black") -> None:
    canva.create_line(self.start.x, self.start.y, self.end.x, self.end.y, fill=color)

@dataclass
class WindowPolygonObject(WindowObject):
  '''Polígono na janela, definido por uma lista de pontos para os vértices.

  Por requisito da matéria, esta classe só deve ser utilizada para preenchimento das faces **que possuem textura**.
  '''
  points: list[WindowPoint]
  texture: str | None = None

  def draw(self, canva: Canvas, color: str="black") -> None:
    coords = []
    for p in self.points: coords.extend([p.x, p.y])
    canva.create_polygon(*coords, outline="black", fill=self.texture if self.texture else "")

@dataclass
class WindowSurfaceObject(WindowObject):
  '''Superfície na janela, definida por uma lista de pontos para os vértices.
  
  Por requisito da matéria, esta classe só deve ser utilizada para preenchimento das faces **que possuem textura**.
  '''
  points: list[WindowPoint]
  texture: str | None = None
  steps: int = 10

  def draw(self, canva: Canvas, color: str="black") -> None:
    coords = []
    for p in self.points: coords.extend([p.x, p.y])
    for i in range(self.steps+1):
      for j in range(self.steps+1):
        idx = i * (self.steps + 1) + j
        if j < self.steps:
          canva.create_line(self.points[idx].x, self.points[idx].y,
                            self.points[idx + 1].x, self.points[idx + 1].y, fill=color)
        if i < self.steps:
          canva.create_line(self.points[idx].x, self.points[idx].y,
                            self.points[idx + self.steps + 1].x, self.points[idx + self.steps + 1].y, fill=color)
          
class CurveType(Enum):
  '''Tipos de curvas suportados.

  - Bézier: Curvas definidas por pontos de controle, onde a curva é tangente aos segmentos que ligam os pontos de controle.
  - B-Spline: Curvas definidas por pontos de controle, onde a curva não necessariamente passa pelos pontos de controle, mas é influenciada por eles.
  '''
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
  '''Armazena informações de uma curva necessárias para construir sua representação na janela.

  Os pontos de controle são índices para uma lista de pontos no mundo, armazenada no Wireframe que contém a curva.
  A partir desses pontos de controle, a curva constrói um conjunto de linhas utilizando o algoritmo definido pelo seu tipo (*curve_type*).

  *start*, *end* e *degree* estão presentes para manter compatibilidade com o formato Wavefront OBJ, mas não estão sendo 100% utilizados.
  '''
  curve_type: CurveType
  control_points: list[int]
  start: float = 0.0
  end: float = 1.0
  degree: int = 4

  @staticmethod
  def bezier_algorithm(t, *points: WindowPoint) -> WindowPoint:
    '''Calcula um ponto na curva de Bézier para um dado valor de t (0 <= t <= 1) e uma lista de pontos de controle.

    Calculo generalizado para qualquer número de pontos de controle >= 2. (para n = 2, é apenas uma linha reta)
    '''
    n = len(points)
    tv = np.array([(1-t)**(n-1-i) * t**i * math.comb(n-1, i) for i in range(n)], dtype=float)
    return WindowPoint(*(np.dot(tv, np.array(points))[:2]))

  def generate_bezier_points(self, control_points: list[WindowPoint], curve_coefficient: int) -> list[WindowPoint]:
    '''Utiliza *bezier_algorithm* para criar a lista de pontos que formam a curva de Bézier.'''
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
    '''Gera pontos em uma curva B-Spline definida pelos pontos de controle usando o método de diferenças progressivas.'''
    if len(control_points) < 4:
      raise ValueError("Cubic B-Spline curve requires at least 4 control points.")

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
    '''Gera uma lista de pontos sobre a curva a partir do algoritmo definido por *curve_type*.

    Então, constrói pares de pontos consecutivos para formar as linhas que representam a curva.
    '''
    match self.curve_type:
      case CurveType.BEZIER: points = self.generate_bezier_points(control_points, curve_coefficient)
      case CurveType.B_SPLINE: points = self.generate_b_spline_points(control_points, curve_coefficient)
      case _: points = []
    return [(points[i], points[i+1]) for i in range(len(points)-1)]

  def window_objects(self, control_points: list[WindowPoint], curve_coefficient: int) -> list[WindowLineObject]:
    '''Gera os objetos de linha que representam a curva na janela.'''
    return [WindowLineObject(line[0], line[1]) for line in self.get_lines(control_points, curve_coefficient)]

  def __str__(self) -> str:
    output = f"cstype {self.curve_type.obj_name()}\n"
    output += f"deg {self.degree}\n"
    output += f"curv {self.start} {self.end} {' '.join(str(idx+1) for idx in self.control_points)}\n"
    output += "parm u 0 1"
    return output

  def copy(self) -> 'Curve':
    return Curve(self.curve_type, self.control_points[:], self.degree)

class SurfaceType(Enum):
  '''Tipos de superfícies suportados.

  - Bézier: Superfícies definidas por uma grade de pontos de controle, onde a superfície é tangente aos segmentos que ligam os pontos de controle.
  - B-Spline: Superfícies definidas por uma grade de pontos de controle, onde a superfície não necessariamente passa pelos pontos de controle, mas é influenciada por eles.
  '''
  BEZIER = 0
  B_SPLINE = 1

  @classmethod
  def from_obj_name(cls, name: str) -> 'SurfaceType | None':
    name = name.lower()
    if name == "bezier": return SurfaceType.BEZIER
    elif name == "bspline": return SurfaceType.B_SPLINE
    return None

  def obj_name(self) -> str:
    if self == SurfaceType.BEZIER: return "bezier"
    elif self == SurfaceType.B_SPLINE: return "bspline"
    return "unknown"

  def __str__(self) -> str:
    if self == SurfaceType.BEZIER: return "Bézier"
    elif self == SurfaceType.B_SPLINE: return "B-Spline"
    return "Unknown"

@dataclass
class Surface:
  '''Armazena informações de uma superfície necessárias para construir sua representação na janela.

  Os pontos de controle são índices para uma lista de pontos no mundo, armazenada no Wireframe que contém a superfície.
  A partir desses pontos de controle, a superfície constrói um conjunto de linhas utilizando o algoritmo definido pelo seu tipo (*surface_type*).

  *start_u*, *end_u*, *start_v*, *end_v* e *degrees* estão presentes para manter compatibilidade com o formato Wavefront OBJ, mas não estão sendo 100% utilizados.  
  '''
  surface_type: SurfaceType = SurfaceType.BEZIER
  control_points: list[int] = field(default_factory=list)
  degrees: tuple[int, int] = (4, 4)
  start_u: float = 0.0
  end_u: float = 1.0
  start_v: float = 0.0
  end_v: float = 1.0

  def window_objects(self, control_points: list[WindowPoint], surface_degree: int | None) -> list[WindowObject]:
    '''Gera os objetos de linha que representam a superfície na janela.'''
    return [WindowLineObject(line[0], line[1]) for line in self.get_surface_points(control_points, surface_degree=10)]

  def get_surface_points(self, control_points: list[WindowPoint], surface_degree: int | None) -> list[tuple[WindowPoint, WindowPoint]]:
    '''Gera uma lista de pontos sobre a superfície a partir do algoritmo definido por *surface_type*.

    Então, constrói pares de pontos consecutivos para formar as linhas que representam a superfície.
    '''
    match self.surface_type:
      case SurfaceType.BEZIER: points = self.generate_bezier_surface_points(control_points, surface_degree)
      case SurfaceType.B_SPLINE: points = self.generate_b_spline_surface_points(control_points, surface_degree)
      case _: points = []
    
    # flatten points into list
    lines = []
    
    rows = len(points)
    cols = len(points[0]) if rows > 0 else 0

    for i in range(rows):
        for j in range(cols - 1):
            lines.append((points[i][j], points[i][j + 1]))
    for j in range(cols):
        for i in range(rows - 1):
            lines.append((points[i][j], points[i + 1][j]))

    return lines

  def generate_bezier_surface_points(self, control_points: list[WindowPoint], steps: int) -> list[WindowPoint]:
    '''Gera uma lista de pontos sobre uma superfície'''
    surface_points = []
    
    for i in range(steps + 1):
        u = i / steps
        row = []
        for j in range(steps + 1):
            v = j / steps
            point = Surface.bezier_surface_point(control_points, u, v)
            row.append(point)
        surface_points.append(row)
    self.points = [pt for row in surface_points for pt in row]
    return surface_points
  
  def bezier_surface_point(control_points: list[WindowPoint], u: float, v: float) -> WindowPoint:
    """Calcula um ponto na superfície de Bézier para dados valores de u e v (0 <= u, v <= 1) e uma lista de pontos de controle."""
    n = m = int(math.sqrt(len(control_points))) - 1
    
    Bu = Surface.bernstein_poly(n, u)
    Bv = Surface.bernstein_poly(m, v)

    x = y = 0
    for i in range(n + 1):
        for j in range(m + 1):
            b = Bu[i] * Bv[j]
            px, py = control_points[i * (m + 1) + j].x, control_points[i * (m + 1) + j].y
            x += b * px
            y += b * py
    return WindowPoint(x, y)

  def bernstein_poly(n: int, t: float) -> float:
    """Retorna lista [B_0^n(t), B_1^n(t), ..., B_n^n(t)]"""
    return [math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i)) for i in range(n + 1)]


  def generate_b_spline_surface_points(self, control_points: list[WindowPoint], resolution: int, 
                               degree_u: int, degree_v: int, knots_u: list[float], 
                               knots_v: list[float]) -> list[WindowPoint]:
    '''Gera uma lista de pontos sobre uma superfície'''
    m = len(control_points[0]) - 1
    n = len(control_points) - 1
    surface_points = []
    
    for iu in range(resolution + 1):
        u = knots_u[degree_u] + (knots_u[-degree_u - 1] - knots_u[degree_u]) * (iu / resolution)
        for iv in range(resolution + 1):
            v = knots_v[degree_v] + (knots_v[-degree_v - 1] - knots_v[degree_v]) * (iv / resolution)
            x = y = z = 0.0
            for i in range(n + 1):
                Nu = self.basis_function(i, degree_u, u, knots_u)
                for j in range(m + 1):
                    Nv = self.basis_function(j, degree_v, v, knots_v)
                    x += Nu * Nv * control_points[i * (m + 1) + j].x
                    y += Nu * Nv * control_points[i * (m + 1) + j].y
            surface_points.append(WindowPoint(x, y))
    self.points = surface_points
    return surface_points

  def basis_function(self, i: int, k: int, t: float, knots: list[float]) -> float:
    '''Calcula a função base B-Spline N(i, k) em t'''
    if k == 0:
        return 1.0 if knots[i] <= t < knots[i + 1] else 0.0
    denom1 = knots[i + k] - knots[i]
    denom2 = knots[i + k + 1] - knots[i + 1]
    term1 = ((t - knots[i]) / denom1 * self.basis_function(i, k - 1, t, knots)) if denom1 != 0 else 0.0
    term2 = ((knots[i + k + 1] - t) / denom2 * self.basis_function(i + 1, k - 1, t, knots)) if denom2 != 0 else 0.0
    return term1 + term2

  def copy(self) -> 'Surface':
    return Surface(
      self.surface_type,
      self.control_points[:],
      self.degrees,
      self.start_u,
      self.end_u,
      self.start_v,
      self.end_v
    )

  def __str__(self) -> str:
    output = f"cstype {self.surface_type.obj_name()}\n"
    output += f"deg {self.degrees[0]} {self.degrees[1]}\n"
    output += f"surf {self.start_u} {self.end_u} {self.start_v} {self.end_v} {' '.join(str(idx+1) for idx in self.control_points)}\n"
    output += "parm u 0 1\nparm v 0 1"
    return output

@dataclass 
class Wireframe:
  '''Representa um objeto 3D no mundo, composto por vértices, arestas, faces, curvas e superfícies.

  Cada componente do wireframe possui sua própria representação na janela, que é gerada a partir dos vértices projetados.
  Os componentes armazenam seus pontos como índices para a lista de vértices do wireframe.

  Cada vértice é um WorldPoint, que é um array de n elementos de acordo com o número de dimensões do mundo. Esses pontos podem ser projetados para a janela, que é um plano.
  Ou seja, WorldPoint (n dimensões) pode ser convertido para WindowPoint (2 dimensões).

  A representação de cada compoenente do Wireframe é:
  - Vértices: Diretamente convertidos para WindowPointObject
  - Arestas: Cada aresta é representada por um WindowLineObject, que conecta dois vértices.
  - Faces: Cada face é representada por múltiplos WindowLineObject, que conecta múltiplos vértices de forma circular. Caso a face possua textura, também será criado um WindowPolygonObject para preenchê-la.
  - Curvas: Cada curva é representada por múltiplos WindowLineObject, criadas a partir dos pontos de controle.
  - Superfícies: Cada superfície é representada por múltiplos WindowLineObject, criadas a partir dos pontos de controle.

  Para desenhar o Wireframe na janela, primeiro é necessário converter seus vértices em WindowPoints. Então, cada componente pode usar esses valores para construir seus objetos de janela respectivos e desenhá-los.
  Os vértices do Wireframe só são desenhados como pontos se o Wireframe não possuir nenhum outro tipo de componente.
  '''
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

  def window_objects(self, curve_coefficient: int, surface_degree: int | None) -> list[WindowObject]:
    '''Gera uma lista de objetos de janela que representam o Wireframe.

    A definição da construção de objetos de janela a partir de cada componente está na docstring da classe Wireframe.
    '''
    objects: list[WindowObject] = []
    for start_idx, end_idx in self.edges: objects.append(WindowLineObject(self.projected_vertices[start_idx], self.projected_vertices[end_idx]))
    for face in self.faces:
      face_vertices = [self.projected_vertices[idx] for idx in face[0]]
      objects.append(WindowPolygonObject(face_vertices, texture=face[1]))
    for curve in self.curves: objects.extend(curve.window_objects([self.projected_vertices[x] for x in curve.control_points], curve_coefficient))
    for surface in self.surfaces: 
      objects.extend(surface.window_objects([self.projected_vertices[x] for x in surface.control_points], surface_degree))
    if objects == []:  # If there are no edges, faces or curves, draw the vertices as points
      for v in self.projected_vertices: objects.append(WindowPointObject(v))

    return objects

  @classmethod
  def load_file(cls, filepath: str | None) -> list['Wireframe']:
    '''Carrega um arquivo no formato Wavefront OBJ e retorna uma lista de Wireframes.'''
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
            current_curve_type = curve_type  # Armazena temporariamente

          case 'deg':
            deg_values = [int(x) for x in body]
            current_degrees = deg_values  # Também temporário

          case 'surf':
            su, eu, sv, ev = map(float, body[:4])
            point_indices = [int(i) - 1 for i in body[4:]]
            if len(current_degrees) < 2:
                raise ValueError(f"Invalid surface degrees: {current_degrees}")
            expected_points = current_degrees[0] * current_degrees[1]
            if len(point_indices) < expected_points:
                raise ValueError(f"Expected at least {expected_points} control points, got {len(point_indices)}")
            current_surfaces.append(Surface(
                surface_type=current_curve_type,
                control_points=point_indices,
                degrees=(current_degrees[0], current_degrees[1]),
                start_u=su, end_u=eu, start_v=sv, end_v=ev
            ))

          
          # case 'cstype':
          #   if len(body) < 1: raise ValueError(f"Invalid cstype line: {line.strip()}")
          #   curve_type = CurveType.from_obj_name(body[0])
          #   if curve_type is None: raise ValueError(f"Unknown curve type: {body[0]}")

          #   deg_header, *deg_values = f.readline().split()
          #   if deg_header != 'deg' or len(deg_values) < 1: raise ValueError(f"Invalid deg line: {' '.join([deg_header]+deg_values)}")
          #   deg_values = [int(x) for x in deg_values]

          #   t, *points = f.readline().split()
          #   if t == "curv":
          #     start, end = [float(x) for x in points[:2]]
          #     points = [int(x)-1 for x in points[2:]]
          #     if len(points) < deg_values[0]: raise ValueError(f"Number of control points {len(points)} does not match curve degree {deg_values[0]}")
          #     current_curves.append(Curve(curve_type, points, start, end, deg_values[0] if deg_values else len(points)))
          #   elif t == "surf":
          #     su, eu, sv, ev = [float(x) for x in points[:4]]
          #     points = [int(x)-1 for x in points[4:]]
          #     if len(deg_values) < 2: raise ValueError(f"Invalid surface degrees line: {' '.join(map(str, deg_values))}")
          #     if len(points) < deg_values[0]*deg_values[1]: raise ValueError(f"Number of control points {len(points)} does not match surface degrees {deg_values[0]} and {deg_values[1]} (should be {deg_values[0]*deg_values[1]})")
          #     current_surfaces.append(Surface(curve_type, points, (deg_values[0], deg_values[1]), su, eu, sv, ev))
          #   else: raise ValueError(f"Invalid curve/surface line: {line.strip()}")

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
    '''Rotaciona todos os vértices do objeto em torno de um ponto arbitrário.
    Se nenhum ponto for fornecido, o objeto será rotacionado em torno de seu próprio centro.

    O plano rotacionado é definido por a1 e a2, que são os índices das dimensões do mundo.
    Por exemplo, para rotacionar no plano XY, a1=0 e a2=1 (padrão). Ou seja, rotacionar em torno do eixo Z.
    '''
    
    point = point if point is not None else self.center

    # Move the object to be centered around the rotation point.
    self.translate(*-point[:3])
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
    '''Desloca o objeto em relação ao seu sistema de coordenadas.'''
    self.transform(np.array([
      [1, 0, 0, dx],
      [0, 1, 0, dy],
      [0, 0, 1, dz],
      [0, 0, 0, 1]
    ]))

  def scale(self, factor: float) -> None:
    '''Escala o objeto em relação ao seu centro.'''
    self.translate(*-self.center[:3])
    self.transform(np.array([
      [factor, 0, 0, 0],
      [0, factor, 0, 0],
      [0, 0, factor, 0],
      [0, 0, 0, 1]
    ]))
    self.translate(*self.center[:3])

  def transform(self, M: np.ndarray) -> None:
    '''Aplica uma transformação linear a todos os vértices do objeto.'''
    self.vertices = [M @ v for v in self.vertices]

  @property
  def center(self) -> WorldPoint:
    return np.mean(self.vertices, axis=0).astype(float)
