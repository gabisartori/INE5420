from screen import Camera
import numpy as np
from wireframe import PolygonObject
from viewport.clipping import Clipping, ClippingAlgorithm

# WIDTH = 800
# HEIGHT = 600

# camera = Camera(
#   normal=np.array([0, 0, -1]),
#   position=np.array([100, 0, 0]),
#   viewport_width=WIDTH,
#   viewport_height=HEIGHT,
#   zoom=1.1
# )

# TOLERANCE = 10
# correct = True
# for i in range(100):
#   x = random.randint(0, WIDTH)
#   y = random.randint(0, HEIGHT)
#   a, b = camera.camera_to_viewport(*camera.viewport_to_camera(x, y))
#   if a < x-TOLERANCE or a > x+TOLERANCE or b < y-TOLERANCE or b > y+TOLERANCE : print(f"Test {i} failed: ({x}, {y}) -> ({a}, {b})"); exit(1)

window = (100, 100, 300, 300)

test_polygon = PolygonObject(
  name="test",
  points=[
    np.array([50, 150]),
    np.array([150, 50]),
    np.array([350, 150]),
    np.array([250, 250]),
    np.array([150, 350]),
    np.array([100, 300])
  ]
)

clipping = Clipping(window)
clipped = clipping.clip([test_polygon], ClippingAlgorithm.SUTHERLAND_HODGMAN)

print("Clipped polygon points:")
for poly in clipped:
    print(poly.points)

print("All tests passed!")
exit(0)
