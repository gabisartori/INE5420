import viewport


screen = viewport.Viewport(800, 600, input="../example.obj", output="../output.obj")
objects = screen.run()
