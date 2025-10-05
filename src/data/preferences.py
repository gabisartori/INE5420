import json
import my_logging
import numpy as np

class Preferences:
  def __init__(self, application_name="INE5420 - SGI", debug=True, 
               input_file="example.obj", output_file="output.obj", 
               mode="3D", height=900, width=1400, zoom=1, 
               window_normal={"x": 0, "y": 0, "z": -1}, 
               window_position={"x": 0, "y": 0, "z": 100}, 
               theme="light", show_onboarding=True, 
               curve_algorithm="bezier", curve_coefficient=100, 
               clipping_algorithm="sutherland-hodgman", max_depth=1000):
    self.application_name = application_name
    self.debug = debug
    self.input_file = input_file
    self.output_file = output_file
    self.height = height
    self.width = width
    self.zoom = zoom
    self.window_normal = window_normal
    self.window_position = window_position
    self.theme = theme
    self.show_onboarding = show_onboarding
    self.curve_algorithm = curve_algorithm
    self.curve_coefficient = curve_coefficient
    self.clipping_algorithm = clipping_algorithm
    self.mode = mode
    self.max_depth = max_depth

  def load_user_preferences(self, path="src/data/usr_data.json"):
    try:
      with open(path, "r") as file:
        data = json.load(file)
        pref = data.get("user_preferences", {})
        # Set default values if keys are missing
        self.theme = pref.get("theme", "light")
        self.show_onboarding = pref.get("show_onboarding", True)
        self.curve_algorithm = pref.get("curve_algorithm", "bezier")
        self.curve_coefficient = pref.get("curve_coefficient", 100)
        self.clipping_algorithm = pref.get("clipping_algorithm", "sutherland_hodgman")
        self.window_normal = np.array([pref.get("window_normal", {}).get("x", 0), pref.get("window_normal", {}).get("y", 0), pref.get("window_normal", {}).get("z", -1)])
        self.window_position = np.array([pref.get("window_position", {}).get("x", 0), pref.get("window_position", {}).get("y", 0), pref.get("window_position", {}).get("z", 100)])
        self.application_name = pref.get("application_name", "INE5420 - SGI")
        self.debug = pref.get("debug", True)
        self.input_file = pref.get("input_file", "example.obj")
        self.output_file = pref.get("output_file", "output.obj")
        self.height = pref.get("height", 900)
        self.width = pref.get("width", 1400)
        self.zoom = pref.get("zoom", 1)
        self.mode = pref.get("mode", "2D")
        self.max_depth = pref.get("max_depth", 1000)
        
        return Preferences(
          theme=self.theme,
          show_onboarding=self.show_onboarding,
          curve_algorithm=self.curve_algorithm,
          curve_coefficient=self.curve_coefficient,
          clipping_algorithm=self.clipping_algorithm,
          window_normal=self.window_normal,
          window_position=self.window_position,
          application_name=self.application_name,
          debug=self.debug,
          input_file=self.input_file,
          output_file=self.output_file,
          height=self.height,
          width=self.width,
          zoom=self.zoom,
          mode=self.mode,
          max_depth=self.max_depth
        )
        
    except FileNotFoundError:
      my_logging.default_log("User preferences file not found")
      return {}
    except json.JSONDecodeError:
      my_logging.default_log("Error decoding JSON")
      return {}

  def save_user_preferences(self, path="src/data/usr_data.json"):
    data = {}

    data["user_preferences"] = {
      "theme": self.theme,
      "show_onboarding": self.show_onboarding,
      "curve_algorithm": self.curve_algorithm,
      "curve_coefficient": self.curve_coefficient,
      "clipping_algorithm": self.clipping_algorithm,
      "window_normal": {"x": int(self.window_normal[0]), "y": int(self.window_normal[1]), "z": int(self.window_normal[2])},
      "window_position": {"x": int(self.window_position[0]), "y": int(self.window_position[1]), "z": int(self.window_position[2])},
      "application_name": self.application_name,
      "debug": self.debug,
      "input_file": self.input_file,
      "output_file": self.output_file,
      "height": self.height,
      "width": self.width,
      "zoom": self.zoom,
      "mode": self.mode,
      "max_depth": self.max_depth
    }

    try:
      with open(path, "w") as file:
        json.dump(data, file, indent=2)
    except IOError:
      my_logging.default_log("Error writing to user preferences file")
    
    