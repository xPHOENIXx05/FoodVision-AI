import json


def load_json(path):
    """
    Load a JSON file and return its contents.

    The JSON file should contain either:
      - A list of food objects
      - A dictionary containing a list
    """

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data
