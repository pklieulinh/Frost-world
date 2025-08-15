class Skill:
    def __init__(self, key, data):
        self.key = key
        self.name = data.get("name", key)
        self.effect = data.get("effect", "")