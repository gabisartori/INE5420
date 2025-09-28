from datetime import datetime

# TODO: Either replace this with a proper logging library or decide where this would better fit in the code.
def default_log(message: str, filename="DEFAULT_LOG_FILE.txt"):
  """Writes the message to the specified log file with a timestamp.

  It also prints the message to the console for immediate feedback.
  """
  with open(filename, "a") as file:
    file.write(f"[{datetime.now()}] {message}\n")
  print(f'Message "{message}" logged to {filename}')