import argparse
import config
import json

from sgi import SGI

# Command-line argument parsing
# -i; --input: input file path. The file must follow the wavefront .obj format and all its objects will be displayed upon start up. If no file is passed, or if the passed file doesn't exist, the program will start with no objects.
# -o; --output: output file path. Upon termination, the program will write the current state of all objects to this file in wavefront .obj format. If no file is passed, or if the passed path is invalid (i.e. the folder doesn't exist), the program will not write any output file.
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="Path to the input file", type=str, default=None, dest="input_file")
parser.add_argument("-o", "--output", help="Path to the output file", type=str, default=None, dest="output_file")

# Make sure that all output files are saved inside the data folder
args = parser.parse_args()
if args.output_file is not None and not args.output_file.strip().startswith(config.DATA_PATH):
  args.output_file = f"{config.DATA_PATH}/{args.output_file.strip()}"

preferences = json.load(open(config.USER_PREFERENCES_PATH))

sgi = SGI(
  # Application configuration
  width=config.WIDTH,
  height=config.HEIGHT,
  title=config.TITLE,
  window_padding=config.WINDOW_PADDING,
  window_movement_speed=config.WINDOW_MOVEMENT_SPEED,
  window_rotation_speed=config.WINDOW_ROTATION_SPEED,
  projection_type=config.PROJECTION_TYPE,
  # User data, storing the current state of the application
  **preferences,
  # Arguments passed by the user in the command line
  **args.__dict__
)
sgi.run()