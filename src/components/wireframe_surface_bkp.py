   
  # def generate_bezier_surface_points(self, control_points: list[WindowPoint]) -> list[WindowPoint]:
  #   '''Gera uma lista de pontos sobre uma superfície'''
  #   pass
  #   surface_points = []
    
  #   for i in range(self.surface_steps + 1):
  #       u = i / self.surface_steps
  #       row = []
  #       for j in range(self.surface_steps + 1):
  #           v = j / self.surface_steps
  #           point = Surface.bezier_surface_point(control_points, u, v, self.degrees[0], self.degrees[1])
  #           row.append(point)
  #       surface_points.append(row)
  #   self.points = [pt for row in surface_points for pt in row]
  #   return surface_points

  # def bezier_surface_point(control_points: list[WindowPoint], u: float, v: float, degree_u: int, degree_v: int) -> WindowPoint:
  #   """Calcula um ponto na superfície de Bézier para dados valores de u e v (0 <= u, v <= 1) e uma lista de pontos de controle."""
  #   pass
  #   n = degree_u - 1
  #   m = degree_v - 1

  #   Bu = Surface.bernstein_poly(n, u)
  #   Bv = Surface.bernstein_poly(m, v)

  #   x = y = 0
  #   for i in range(n + 1):
  #       for j in range(m + 1):
  #           b = Bu[i] * Bv[j]
  #           px, py = control_points[i * (m + 1) + j].x, control_points[i * (m + 1) + j].y
  #           x += b * px
  #           y += b * py
  #   return WindowPoint(x, y)

  # def bernstein_poly(n: int, t: float) -> float:
  #   pass
    
  #   """Retorna lista [B_0^n(t), B_1^n(t), ..., B_n^n(t)]"""
  #   return [math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i)) for i in range(n + 1)]
  
  # def generate_b_spline_v2(self, control_points: list[WindowPoint]) -> list[WindowPoint]:
  #   pass
  #   if self.degrees[0] < 2 or self.degrees[1] < 2:
  #     raise ValueError("B-Spline surface requires at least degree 2 in both u and v directions.")
    
  #   num_points_per_direction_x, num_points_per_direction_y = self.degrees[0], self.degrees[1]
    
  #   M_b_spline = np.array([
  #     [-1/6,  3/6, -3/6, 1/6],
  #     [ 3/6, -6/6,  3/6, 0],
  #     [-3/6,  0,    3/6, 0],
  #     [ 1/6,  4/6,  1/6, 0]
  #   ])

  #   M_b_spline_T = M_b_spline.T
    
  #   # reorganize control points into 2D grid
  #   G_all_xy = np.array([[cp.x, cp.y] for cp in control_points]).reshape(num_points_per_direction_x, num_points_per_direction_y, 2)

  #   #separate G into Gx and Gy
  #   GX_all = G_all_xy[:, :, 0]
  #   GY_all = G_all_xy[:, :, 1]
  
  #   surface_points: list[WindowPoint] = []
  #   step_size = 1 / self.surface_steps

  #   num_patches_u = num_points_per_direction_x - 3
  #   num_patches_v = num_points_per_direction_y - 3

  #   for patch_u_idx in range(num_patches_u):
  #     for patch_v_idx in range(num_patches_v):
  #       # selects the 4x4 control points for the current patch
  #       GX = GX_all[patch_u_idx:patch_u_idx + 4, patch_v_idx:patch_v_idx + 4]
  #       GY = GY_all[patch_u_idx:patch_u_idx + 4, patch_v_idx:patch_v_idx + 4]
        
  #       # coefficients X and Y
  #       temp_X = np.matmul(M_b_spline, GX)
  #       CX = np.matmul(temp_X, M_b_spline_T)

  #       temp_Y = np.matmul(M_b_spline, GY)
  #       CY = np.matmul(temp_Y, M_b_spline_T)
        
  #       # iterates on patch points
  #       for i in range(self.surface_steps + 1):
  #         row_points = []
  #         u = i * step_size
  #         u_vec = np.array([u**3, u**2, u, 1])
  #         for j in range(self.surface_steps + 1):
  #           v = j * step_size
  #           v_vec = np.array([v**3, v**2, v, 1])
            
  #           temp_x = np.matmul(u_vec, CX)
  #           x = np.matmul(temp_x, v_vec)
            
  #           temp_y = np.matmul(u_vec, CY)
  #           y = np.matmul(temp_y, v_vec)
  #           row_points.append(WindowPoint(x, y))
  #         surface_points.append(row_points)         
  #   return surface_points

  # def generate_b_spline_surface_points(self, control_points: list[WindowPoint]) -> list[WindowPoint]:
  #   pass
  #   """Gera uma lista de pontos sobre uma superfície B-Spline."""
  #   generated_surface_points = self.generate_b_spline_v2(control_points)
  #   self.points = generated_surface_points
  #   return generated_surface_points

  
