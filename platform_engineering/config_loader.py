import json
import os


def load_config(filename='config.json'):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} not found.")

    with open(filename, 'r') as file:
        return json.load(file)


config = load_config()
