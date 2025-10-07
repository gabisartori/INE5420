import json
import my_logging
import numpy as np

from dataclasses import dataclass, field

# TODO: Turn this into a dataclass and replace json load/save with asdict and fromdict
@dataclass
class Preferences:
  # Application data
  input_file: str
  output_file: str
  application_name: str = "INE5420 - SGI"
  debug: bool = True
  height: int = 900
  width: int = 1400
  zoom: float = 1.0

  # Viewport data
  window_normal: np.ndarray = field(default_factory=lambda: np.array([0, 0, -1]))
  window_position: np.ndarray = field(default_factory=lambda: np.array([0, 0, 0]))

  # User preferences
  curve_algorithm: int = 0  # 0: Bezier, 1: B-Spline
  curve_coefficient: int = 100  # Percentage of curve smoothness
  clipping_algorithm: int = 1  # 0: Cohen-Sutherland, 1
  
  @classmethod
  def load_user_preferences(cls, path="src/data/usr_data.json") -> 'Preferences':
    pref = json.load(open(path))
    return Preferences(input_file="./a.obj", output_file="./b.obj", **pref)

  def save_user_preferences(self, path="src/data/usr_data.json"):
    try:
      with open(path, "w") as file:
        json.dump(self.__dict__, file, indent=2)
    except IOError:
      my_logging.default_log("Error writing to user preferences file")
    
    