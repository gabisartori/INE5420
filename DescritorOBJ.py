# Crie uma classe DescritorOBJ capaz de transcrever um objeto gráfico para o 
# formato .obj, tomando seu nome, seu tipo, seus vértices e suas arestas.

from wireframe import *

class DescritorOBJ:
    def __init__(self, objects: list[Wireframe], output_file):
        self.objects = objects
        self.output_file = output_file
        
    def save_to_file(self):
        with open(self.output_file, "w") as file:
          for obj in self.objects:
            name = obj.name
            if isinstance(obj, PointObject):
              obj_type = "Point"
            elif isinstance(obj, LineObject):
              obj_type = "Line"
            elif isinstance(obj, PolygonObject):
              obj_type = "Polygon"
            else:
                obj_type = "unknown"
                
            vertices = obj.points
            edges = []
            if isinstance(obj, LineObject):
              edges.append((obj.points[0], obj.points[1]))
            elif isinstance(obj, PolygonObject):
              for i in range(len(obj.points)):
                edges.append((obj.points[i], obj.points[(i + 1) % len(obj.points)]))
                
            descriptor = f"# Object: {name}, Type: {obj_type}\n"
            file.write(f"# Object: {name}, Type: {obj_type}\n")
            file.write(f"v {vertices[0].x} {vertices[0].y} {vertices[0].z}\n")
            for edge in edges:
                file.write(f"l {edge[0].id} {edge[1].id}\n")
            file.write("\n")
            
            print()