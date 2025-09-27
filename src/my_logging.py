from datetime import datetime

def default_log(message: str, filename="DEFAULT_LOG_FILE.txt"):
  with open(filename, "a") as file:
    file.write(f"[{datetime.now()}] {message}\n")
  print(f'Message "{message}" logged to {filename}')