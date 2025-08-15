import random
from core.hero import Hero

class KingdomState:
    def __init__(self, data):
        self.gold = data.get("gold", 1000)
        self.population = data.get("population", 0)
        self.fame = data.get("fame", 0)
        self.morale = data.get("morale", 1.0)
        self.level = data.get("level", 1)
        self.research = data.get("research", 0)
        self.buildings = []
        self.npcs = []
        self.heroes = []
        self.parties = []
        self.leader_id = data.get("leader_id", None)  # New: leader npc/hero id
        self.event_log = []

    def get_leader(self):
        for n in self.npcs + self.heroes:
            if getattr(n, "id", None) == self.leader_id:
                return n
        return None

    def set_leader(self, npc_or_hero_id):
        self.leader_id = npc_or_hero_id

    def spawn_hero(self):
        new_hero = Hero(f"hero{len(self.heroes)+1}", f"Hero-{random.randint(100,999)}", {
            "job": "hero",
            "level": random.randint(1, 5),
            "rank": "C",
            "skills": ["lead", "combat", "special"]
        })
        self.heroes.append(new_hero)
        self.population += 1

    def add_random_quest(self, questboard):
        questboard.add_random_quest()