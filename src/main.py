import viewport
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="Path to the input file", type=str, default=None, dest="input_file")
parser.add_argument("-o", "--output", help="Path to the output file", type=str, default=None, dest="output_file")
args = parser.parse_args()

if args.output_file == "output.obj":
  print("Warning: Name 'output.obj' reserved")
  args.output_file = "output_1.obj"

screen = viewport.Viewport(1400, 900, input=args.input_file, output=args.output_file)
objects = screen.run()
