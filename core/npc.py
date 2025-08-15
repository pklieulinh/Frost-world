from core.entity import Entity
import random

class NPC(Entity):
    def __init__(self, eid, name, data):
        super().__init__(eid, name, "npc", data)
        self.job = data.get("job", "villager")
        self.house = data.get("house", None)
        self.level = data.get("level", 1)
        self.exp = data.get("exp", 0)
        self.skills = data.get("skills", [])
        self.relation = {}
        self.memory = []
        self.party = data.get("party", None)
        self.morale = data.get("morale", 1.0)
        self.loyalty = data.get("loyalty", 1.0)
        self.is_hero = False
        self.x = data.get("x", random.randint(0,15))
        self.y = data.get("y", random.randint(0,11))
        self.target_x = self.x
        self.target_y = self.y

    def gain_exp(self, amount):
        self.exp += amount
        if self.exp >= 100:
            self.level += 1
            self.exp -= 100

    def update_state(self):
        # Không cần random walk ở đây vì worldmap đã xử lý
        pass