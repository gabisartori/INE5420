import numpy as np
import math

import tkinter as tk
from dataclasses import dataclass
from components.my_types import Point

def normalize(v: Point) -> Point:
    """Normalize a vector."""
    norm = np.linalg.norm(v)
    return v / norm if norm != 0 else v

class Camera:
  def __init__(self, normal: Point, position: Point, viewport_width: int, viewport_height: int, zoom: float=1.0):
    self.normal: Point = normalize(normal)
    self.position: Point = position
    self.speed: int = 5
    self.zoom: float = zoom
    self.viewport_width: int = viewport_width
    self.viewport_height: int = viewport_height
    self.viewport_focus: tuple[float, float] = (self.viewport_width // 2, self.viewport_height // 2)
    self.camera_focus: tuple[float, float] = (0, 0)
    self.viewport_angle = 0
    self.transform_matrix: np.ndarray = np.eye(2)
    self.max_zoom = 100.0
    self.min_zoom = 0.1

    UP = np.array([0, 1, 0])
    if np.array_equal(normal, UP) or np.array_equal(normal, -UP):
      self.right = np.array([1, 0, 0])
      self.up = np.array([0, 0, 1])
    else:
      self.right = normalize(np.cross(self.normal, UP))
      self.up = normalize(np.cross(self.right, self.normal))
      
  def move_up(self):
      direction = self.up
      self.position += direction * max(self.speed / self.zoom, 1)

  def move_right(self):
      direction = self.right
      self.position += direction * max(self.speed / self.zoom, 1)

  # def move_up(self): self.position[2] += max(self.speed/self.zoom, 1)

  # def move_down(self): self.position[2] -= max(self.speed/self.zoom, 1)

  def move_left(self): self.position[0] -= max(self.speed/self.zoom, 1)

  def move_right(self): self.position[0] += max(self.speed/self.zoom, 1)

  def move_below(self): self.position[1] -= max(self.speed/self.zoom, 1)

  def move_above(self): self.position[1] += max(self.speed/self.zoom, 1)
  
  def rotate(self, degrees=5):
    degrees = int(degrees)
    angle_rad = np.radians(degrees)

    cos_a = np.cos(angle_rad)  
    sin_a = np.sin(angle_rad)
    rotation_matrix = np.array([
        [cos_a, -sin_a],
        [sin_a,  cos_a]
    ])

    right_2d = self.right[[0, 2]]
    up_2d = self.up[[0, 2]]

    new_right_2d = rotation_matrix @ right_2d
    new_up_2d = rotation_matrix @ up_2d

    self.right = normalize(np.array([new_right_2d[0], 0, new_right_2d[1]]))
    self.up = normalize(np.array([new_up_2d[0], 0, new_up_2d[1]]))

    self.transform_matrix = rotation_matrix @ self.transform_matrix
    self.viewport_angle += degrees
    self.viewport_angle %= 360

  # def rotate(self, degrees=5):
  #   # 0: Obter o centro da câmera para translação
  #   tx, tz = -self.position[0], -self.position[2]  # negativo para transladar mundo ao redor da câmera
    
  #   # 1: Matriz de translação para levar o centro ao ponto (0,0)
  #   T = np.array([
  #       [1, 0, tx],
  #       [0, 1, tz],
  #       [0, 0, 1]
  #   ])
    
  #   # 2: Matriz de rotação em torno da origem (ângulo positivo para sentido anti-horário)
  #   theta = math.radians(degrees)
  #   c, s = math.cos(theta), math.sin(theta)
  #   R = np.array([
  #       [c, -s, 0],
  #       [s,  c, 0],
  #       [0,  0, 1]
  #   ])
    
  #   # 3: Matriz inversa da translação para voltar para a posição original
  #   Ti = np.array([
  #       [1, 0, -tx],
  #       [0, 1, -tz],
  #       [0, 0, 1]
  #   ])
    
  #   # 4: Atualizar matriz de transformação acumulada:
  #   # a ordem correta para aplicar transformações no mundo é Ti * R * T * M
  #   # Ou seja, primeiro translada o mundo para a origem, depois rotaciona, depois translada de volta
  #   M = self.transform_matrix
  #   self.transform_matrix = Ti @ R @ T @ M
    
  #   # 5: Atualizar os vetores do sistema de coordenadas da câmera (direita e up) na projeção 2D
  #   right_2d = self.right[[0, 2]]
  #   up_2d = self.up[[0, 2]]
    
  #   def normalize(v):
  #       norm = np.linalg.norm(v)
  #       return v / norm if norm != 0 else v
    
  #   right_rot = normalize(R[:2, :2] @ right_2d)
  #   up_rot = normalize(R[:2, :2] @ up_2d)
    
  #   self.right[0], self.right[2] = right_rot
  #   self.up[0], self.up[2] = up_rot
    
  #   # 6: Corrigir normal da câmera (direção da câmera)
  #   self.normal = normalize(np.cross(self.right, self.up))
    
  #   # 7: Atualizar ângulo da viewport (para controle)
  #   self.viewport_angle = (self.viewport_angle + degrees) % 360

  #   # theta = math.radians(degrees)
  #   # c, s = math.cos(theta), math.sin(theta)
  #   # R = np.array([[c, -s], [s, c]])
  #   # self.transform_matrix = R @ self.transform_matrix
  #   # self.right = normalize(R @ self.right[[0,2]])
  #   # self.up = normalize(R @ self.up[[0,2]])
  #   # self.normal = normalize(np.cross(self.right, self.up))
  #   # self.viewport_angle = (self.viewport_angle + degrees) % 360

  def zoom_in(self, x, y):
    if self.zoom <= self.max_zoom: self.zoom *= 1.1

  def zoom_out(self, x, y):
    if self.zoom >= self.min_zoom: self.zoom /= 1.1

  def recenter(self):
    self.position = np.array([0, 100, 0])
    self.normal = np.array([0, -1, 0])
    self.zoom = 1.0
    self.camera_focus = (0, 0)
    self.viewport_focus = (self.viewport_width // 2, self.viewport_height // 2)

  def world_to_viewport(self, point: Point) -> tuple[float, float]:
    # Ignore points behind camera
    # if np.dot(self.normal, point - self.position) < 0: point = self.position - self.normal
    x, y = self.world_to_camera(point)


    # Convert the camera view plane coordinates to viewport coordinates
    # - Centering the camera plane origin at the center of the viewport
    # - Scaling the coordinates by the zoom factor
    # - Adjusting the y-coordinate to match the canvas coordinate system
    position = self.camera_to_viewport(x, y)

    return position

  def world_to_camera(self, point: Point) -> tuple[float, float]:
    # Project the point onto the camera view plane
    t = sum(self.normal[i] * (self.position[i] - point[i]) for i in range(len(point)))
    t /= sum(self.normal[i] * self.normal[i] for i in range(len(point)))
    c = np.array([point[i] + t * self.normal[i] for i in range(len(point))])
    
    v = c - self.position
    return np.dot(v, self.right), np.dot(v, self.up)

  def camera_to_world(self, x: float, y: float) -> Point:
    # Return a 3D point based on the camera's position and orientation
    # TODO: This creates a point at the exact position of the camera
    # It would be more useful if the user could control a distance from the camera to which clicks are applied
    # This is quite simple to implement, but it would mess with how zoom is behaving
    return x*self.right + y*self.up + self.position

  def camera_to_viewport(self, x: float, y: float) -> tuple[float, float]:
    x = x*self.zoom + self.viewport_focus[0]
    y = y*self.zoom + self.viewport_focus[1]
    y = self.viewport_height - y
    return x, y

  def viewport_to_camera(self, x: float, y: float) -> tuple[float, float]:
    y = self.viewport_height - y
    x = (x-self.viewport_focus[0])/self.zoom
    y = (y-self.viewport_focus[1])/self.zoom
    return x, y

  def viewport_to_world(self, x: float, y: float) -> Point:
    return self.camera_to_world(*self.viewport_to_camera(x, y))

@dataclass
class ScreenWireframe:
  start: Point
  end: Point | None = None
