# Helper function to load json file into python object
import json

def open_json(name):
    with open(name, 'r') as json_file:
        object_data = json.load(json_file)
    return object_data
    