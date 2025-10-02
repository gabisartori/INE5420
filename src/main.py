import argparse
from data import preferences
from sgi import SGI

# Command-line argument parsing
# -i; --input: input file path. The file must follow the wavefront .obj format and all its objects will be displayed upon start up. If no file is passed, or if the passed file doesn't exist, the program will start with no objects.
# -o; --output: output file path. Upon termination, the program will write the current state of all objects to this file in wavefront .obj format. If no file is passed, or if the passed path is invalid (i.e. the folder doesn't exist), the program will not write any output file.
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="Path to the input file", type=str, default=None, dest="input_file")
parser.add_argument("-o", "--output", help="Path to the output file", type=str, default=None, dest="output_file")
args = parser.parse_args()

# Initialize and run the viewport with the fixed dimensions of 1400x900 pixels (the default values in the config file)
sgi = SGI(input=args.input_file, output=args.output_file, debug=True)
sgi.run()