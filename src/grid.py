import numpy as np
from config import PREFERENCES
from window import Window

class Grid:
    def __init__(self, window: Window, step: int=75, width: int=800, height: int=600):
        self.window = window
        self.lines = []
        
        self.step = step
        self.min_zoom = window.min_zoom

        self.width = width
        self.height = height

        self.max_world_width = self.width / self.min_zoom
        self.max_world_height = self.height / self.min_zoom
        self.max_range = int(max(self.max_world_width, self.max_world_height) / 2)  # /2 para ter metade pra cada lado do centro

        self.start = ( -self.max_range // self.step ) * self.step
        self.end = ( self.max_range // self.step + 1 ) * self.step

    def draw(self, canva):
        color = "lightgray"
        if PREFERENCES.mode == "2D":
            for i in range(self.start, self.end, self.step):
                start_h = self.window.world_to_viewport(np.array([-self.max_range, i, 0]))
                end_h = self.window.world_to_viewport(np.array([self.max_range, i, 0]))
                self.canva.create_line(
                start_h[0], start_h[1], end_h[0], end_h[1],
                fill=color
                )

                start_v = self.window.world_to_viewport(np.array([i, -self.max_range, 0]))
                end_v = self.window.world_to_viewport(np.array([i, self.max_range, 0]))
                self.canva.create_line(
                start_v[0], start_v[1], end_v[0], end_v[1],
                fill=color
                )
            else: # 3D
                lines = []
                for i in range(-self.max_range, self.max_range + 1, self.step):
                    lines.append((np.array([-self.max_range, i, 0]), np.array([self.max_range, i, 0])))
                    lines.append((np.array([i, -self.max_range, 0]), np.array([i, self.max_range, 0])))
                    lines.append((np.array([-self.max_range, 0, i]), np.array([self.max_range, 0, i])))
                self.lines = lines
                
                for line in lines:
                    v1 = self.window.world_to_viewport(line[0])
                    v2 = self.window.world_to_viewport(line[1])
                    canva.create_line(
                    v1[0], v1[1], v2[0], v2[1],
                    fill=color
                    )

                origin = self.window.world_to_viewport(np.array([0, 0, 0]))
                canva.create_text(origin[0] + 15, origin[1] - 10, text="(0,0)", 
                    fill=color)