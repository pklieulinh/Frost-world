from core.npc import NPC

class Hero(NPC):
    def __init__(self, eid, name, data):
        super().__init__(eid, name, data)
        self.is_hero = True
        self.rank = data.get("rank", "C")
        self.title = data.get("title", "")
        self.special = data.get("special", [])
        self.reputation = data.get("reputation", 0)