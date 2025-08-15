import random

class Quest:
    def __init__(self, key, data):
        self.key = key
        self.name = data.get("name", key)
        self.desc = data.get("desc", "")
        self.require = data.get("require", {})
        self.reward = data.get("reward", {"gold": 50, "exp": 10})
        self.status = "open"

class QuestBoard:
    def __init__(self, quest_data):
        self.quests = {k: Quest(k, v) for k,v in quest_data.items()}
        self.active_quests = []

    def add_quest(self, key):
        q = self.quests.get(key)
        if q and q.status == "open":
            self.active_quests.append(q)
            q.status = "active"

    def add_random_quest(self):
        available = [k for k,q in self.quests.items() if q.status == "open"]
        if available:
            key = random.choice(available)
            self.add_quest(key)
        elif not available:
            from core.autogen import AutoGen
            nq = AutoGen.gen_quest()
            self.quests[nq.key] = nq
            self.add_quest(nq.key)

    def complete_quest(self, key):
        q = self.quests.get(key)
        if q and q.status == "active":
            q.status = "done"
            return q.reward
        return None

    def get_active_quests(self):
        return [q for q in self.quests.values() if q.status == "active"]

    def get(self, key):
        return self.quests.get(key)