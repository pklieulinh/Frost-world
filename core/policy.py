from core.utils import load_json

class Policy:
    def __init__(self, key, definition):
        self.key = key
        self.name = definition.get("name", key)
        self.desc = definition.get("desc", "")
        self.effects = definition.get("effects", {})
        self.active = False

class PolicyManager:
    def __init__(self, json_path):
        self.json_path = json_path
        self.policies_data = load_json(json_path)
        self.policies = []
        self.init_policies()
        self.proposals = []
        self.log = []

    def init_policies(self):
        self.policies = []
        for k, v in self.policies_data.items():
            self.policies.append(Policy(k, v))

    def reload(self):
        self.policies_data = load_json(self.json_path)
        self.init_policies()

    def propose_policy(self, npc, key):
        pol = self.get_policy(key)
        if pol:
            self.proposals.append({"npc": npc, "policy": pol})
            self.log.append(f"{npc.name} đề xuất chính sách '{pol.name}'.")

    def get_policy(self, key):
        for pol in self.policies:
            if pol.key == key:
                return pol
        return None

    def enact_policy(self, key):
        pol = self.get_policy(key)
        if pol:
            pol.active = True
            self.log.append(f"Chính sách '{pol.name}' đã được áp dụng!")

    def update(self):
        pass

    def get_active_policies(self):
        return [p for p in self.policies if p.active]