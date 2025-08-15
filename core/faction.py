import random
from core.utils import load_json

class Faction:
    def __init__(self, name, desc, color, base_loyalty=0.5):
        self.name = name
        self.desc = desc
        self.color = color
        self.base_loyalty = base_loyalty
        self.members = []

    def add_member(self, npc):
        self.members.append(npc)
        npc.faction = self

    def remove_member(self, npc):
        if npc in self.members:
            self.members.remove(npc)
            npc.faction = None

class FactionManager:
    def __init__(self, json_path):
        self.json_path = json_path
        self.factions_data = load_json(json_path)
        self.factions = []
        self.init_factions()

    def reload(self):
        self.factions_data = load_json(self.json_path)
        self.init_factions()

    def init_factions(self):
        self.factions = []
        for k, v in self.factions_data.items():
            color = tuple(v.get("color", [random.randint(100,255),random.randint(100,255),random.randint(100,255)]))
            self.factions.append(Faction(k, v.get("desc",""), color, v.get("base_loyalty",0.5)))

    def get_random_faction(self):
        return random.choice(self.factions)

    def get_by_name(self, name):
        for f in self.factions:
            if f.name == name:
                return f
        return None

    def assign_initial_factions(self, npcs):
        for npc in npcs:
            f = self.get_random_faction()
            f.add_member(npc)

    def update(self):
        pass