class Job:
    def __init__(self, key, data):
        self.key = key
        self.name = data.get("name", key)
        self.desc = data.get("desc", "")
        self.base_skill = data.get("base_skill", [])
        self.unlock_level = data.get("unlock_level", 1)