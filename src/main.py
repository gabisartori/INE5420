import viewport


screen = viewport.Viewport(1200, 800, input="../example.obj", output="../output.obj")
objects = screen.run()
