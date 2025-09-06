from wireframe import *
import os

class DescritorOBJ:
    def __init__(self, objects: list[Wireframe], output_file: str):
        self.objects = objects
        self.output_file = output_file

    def clear_obj_files(self):
      # clears all .obj files in the current directory
      for filename in os.listdir('.'):
          if filename.endswith('.obj'):
              os.remove(filename)      

    def save_to_file(self):
      with open(self.output_file, "w") as file:
          vertex_offset = 0  

          for obj in self.objects:
              name = getattr(obj, "name", "Unnamed")
              obj_type = self._get_type(obj)
              file.write(f"# Object: {name}\n")
              file.write(f"# Type: {obj_type}\n")

              vertices = obj.points
              for vertice in vertices:
                  x, y, z = vertice[0], vertice[1], vertice[2]
                  file.write(f"v {x} {y} {z}\n")

              arestas = self._get_edges(obj)
              for i1, i2 in arestas:
                  file.write(f"l {vertex_offset + i1 + 1} {vertex_offset + i2 + 1}\n")

              file.write("\n")
              vertex_offset += len(vertices)
      
      # saves original format for compatibility                             
      with open("output.obj", "w") as file:
        for obj in self.objects:
          file.write(f"{obj}\n")

    def _get_type(self, obj) -> str:
        if isinstance(obj, PointObject):
            return "Point"
        elif isinstance(obj, LineObject):
            return "Line"
        elif isinstance(obj, PolygonObject):
            return "Polygon"
        return "Unknown"

    def _get_edges(self, obj) -> list[tuple[int, int]]:
        arestas = []
        pontos = obj.points

        if isinstance(obj, LineObject) and len(pontos) >= 2:
            arestas.append((0, 1))

        elif isinstance(obj, PolygonObject):
            for i in range(len(pontos)):
                j = (i + 1) % len(pontos)
                arestas.append((i, j))

        return arestas
