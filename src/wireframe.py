from dataclasses import dataclass
from components.my_types import Point
import numpy as np
from config import PREFERENCES 
from enum import Enum
from data.matrices import rotation_matrix

class CurveType(Enum):
  BEZIER = 0
  B_SPLINE = 1

  def __str__(self) -> str:
    if self == CurveType.BEZIER:
      return "Bézier"
    elif self == CurveType.B_SPLINE:
      return "B-Spline"
    return "Unknown"

@dataclass
class Wireframe:
  """Parent class for all wireframe objects.
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
  points: list[Point]
  fill_color: str = "white"
  line_color: str = "black"
  thickness: float = 1
  id: int = 0

  def copy(self) -> 'Wireframe': raise NotImplementedError("Subclasses should implement this method")

  def __str__(self) -> str: raise NotImplementedError("Subclasses should implement this method")

  # TODO: For 3D objects, there must be three different rotations, one for each axis.
  # TODO: Decide whether this function should alter the original object or return a new one with the new coordinates.
  def rotate(self, degrees: int=5, point: Point | None=None) -> None:
    """Rotates the object around a given point in the XY plane.
    If no point is given, rotate around the center of the object.

    The XY plane is chosen as the default plane for the 2D implementation of the program. This will then be replaced by the specific XY rotation for the 3D implementation.
    """

    # If no point is given, set the rotation center to be the object's center.
    if point is None:
      px = self.center[0]
      py = self.center[1]
    # Otherwise, use the given point.
    else:
      px = point[0]
      py = point[1]

    # Move the object to be centered around the rotation point.
    self.translate(-px, -py)
    # TODO: When needing to specify which plane the rotation is in, all that needs to change is which matrix is being used.
    # Apply the rotation matrix.
    self.transform2d(rotation_matrix(degrees, axis="z"))
    # Move the object back to its original position.
    self.translate(px, py)

  def translate(self, dx: float, dy: float, dz: float=0) -> None:
    """Translate the object in the XY plane.
    
    Everything that was said about the XY plane in the rotate() method also applies here.
    """
    
    if PREFERENCES.mode == "3D":
      self.transform2d(np.array([
        [1, 0, 0, dx],
        [0, 1, 0, dy],
        [0, 0, 1, dz],
        [0, 0, 0, 1]
      ]))
    else:
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
    if PREFERENCES.mode == "3D":
      self.transform2d(np.array([
        [factor, 0, 0, 0],
        [0, factor, 0, 0],
        [0, 0, factor, 0],
        [0, 0, 0, 1]
      ]))
    else: # 2D
      self.transform2d(np.array([
        [factor, 0, 0],
        [0, factor, 0],
        [0, 0, 1]
      ]))
    self.translate(px, py)

  # TODO: again, decide whether this should modify the original object or return a new one.
  def transform2d(self, M: np.ndarray) -> None:
    """Applies the given matrix to all of the object's points."""
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
  def __init__(self, name: str, control_points: list[Point], steps: int, curve_type: CurveType = CurveType.BEZIER, **kwargs):
    self.steps = steps
    self.control_points = control_points
    self.curve_type = curve_type
    super().__init__(name, [], **kwargs)

    self.generate_bezier_points() if self.curve_type == CurveType.BEZIER else self.generate_b_spline_points()

  def copy(self) -> 'CurveObject_2D':
    new_obj = CurveObject_2D(
      name=self.name,
      control_points=[p.copy() for p in self.control_points],
      steps=self.steps,
      curve_type=self.curve_type,
      id=self.id,
      thickness=self.thickness,
      line_color=self.line_color,
      fill_color=self.fill_color
    )
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
      
      for _ in range(self.steps + 1):
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

class Object_3D(Wireframe):
  def __init__(self, name: str, lines: list[Point], **kwargs):
    points = [p.copy() for p in lines]
    self.lines = lines  
    super().__init__(name, points, **kwargs)
 
  def copy(self) -> 'Object_3D':
    return Object_3D(
      self.name,
      [p.copy() for p in self.lines],
      id=self.id,
      thickness=self.thickness,
      line_color=self.line_color,
      #fill_color=self.fill_color
    )
    
  def __str__(self) -> str:
    vertices_str = '\n'.join(f"v {' '.join(map(str, p))}" for p in self.lines)
    indices_str = ' '.join(str(i + 1) for i in range(len(self.lines)))
    return f"o {self.name}\n{vertices_str}\nl {indices_str}"
    