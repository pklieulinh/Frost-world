import random
from core.utils import load_json

class TraitManager:
    def __init__(self, json_path):
        self.json_path = json_path
        self.traits_data = load_json(json_path)
        self.trait_keys = list(self.traits_data.keys())

    def random_traits(self):
        return random.sample(self.trait_keys, 2)

    def reload(self):
        self.traits_data = load_json(self.json_path)
        self.trait_keys = list(self.traits_data.keys())