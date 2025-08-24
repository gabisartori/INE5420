import viewport
import sys

input_file = sys.argv[1] if len(sys.argv) > 1 else None


screen = viewport.Viewport(1200, 800, input=input_file, output="../output.obj")
objects = screen.run()
