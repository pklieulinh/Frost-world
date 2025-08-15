class Party:
    def __init__(self, pid, data, npc_lookup, hero_lookup):
        self.id = pid
        self.name = data.get("name", pid)
        self.quest = data.get("quest", None)
        self.status = data.get("status", "idle")
        self.members = []
        self.leader_id = data.get("leader_id", None)
        for m in data.get("members", []):
            member = npc_lookup.get(m) or hero_lookup.get(m)
            if member is not None:
                self.members.append(member)
        self.update_leader()

    def update_leader(self):
        # Default: leader là hero trong party, nếu không có thì lấy NPC level cao nhất
        if self.leader_id and any(getattr(m, "id", None) == self.leader_id for m in self.members):
            return
        hero_members = [m for m in self.members if getattr(m, "is_hero", False)]
        if hero_members:
            self.leader_id = hero_members[0].id
        elif self.members:
            self.leader_id = max(self.members, key=lambda x: getattr(x, "level", 0)).id
        else:
            self.leader_id = None

    def get_leader(self):
        for m in self.members:
            if getattr(m, "id", None) == self.leader_id:
                return m
        return None

    def set_leader(self, npc_or_hero_id):
        if any(getattr(m, "id", None) == npc_or_hero_id for m in self.members):
            self.leader_id = npc_or_hero_id

    def is_active(self):
        return self.status == "active"

    def assign_quest(self, quest_key):
        self.quest = quest_key
        self.status = "active"

    def complete_quest(self, quest_lookup):
        q = quest_lookup.get(self.quest)
        if q:
            self.status = "idle"
            self.quest = None
            return q.reward
        return {}