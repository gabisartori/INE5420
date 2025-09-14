import json

def load_user_preferences(path="src/data/usr_data.json"):
  try:
    with open(path, "r") as file:
      data = json.load(file)
      return data.get("user_preferences", {})
  except FileNotFoundError:
    print("User preferences file not found")
    return {}
  except json.JSONDecodeError:
    print("Error decoding JSON")
    return {}
  
def save_user_preferences(preferences, path="src/data/usr_data.json"):
  try:
    with open(path, "r") as file:
      data = json.load(file)
  except (FileNotFoundError, json.JSONDecodeError):
    data = {}
  
  data["user_preferences"] = preferences
  
  try:
    with open(path, "w") as file:
      json.dump(data, file, indent=2)
  except IOError:
    print("Error writing to user preferences file")