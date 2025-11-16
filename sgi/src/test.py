from window import Window
from my_types import WindowPoint

window = Window(500, 500, [0,0,0], [0,0,-1], [0,0,-2], [0,1,0], 1,10,1.0,0)

for i in range(360):
  window.move_forward()
  window.rotate(1, 0,2)
  for x, y in zip(range(0, 500), range(0, 500)):
    p = window.world_to_viewport(window.viewport_to_world(x, y))
    if (p.x-x)**2 + (p.y-y)**2 > 0.0001:
      print(f"Error: {p} != {WindowPoint(x, y)}")
      # break
