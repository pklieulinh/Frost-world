class Building:
    def __init__(self, eid, name, data):
        self.id = eid
        self.name = name
        self.type = data.get("type", "house")
        self.level = data.get("level", 1)
        self.state = "normal"
        self.owner = data.get("owner", None)
        self.x = data.get("x", 0)
        self.y = data.get("y", 0)