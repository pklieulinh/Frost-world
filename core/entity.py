class Entity:
    def __init__(self, eid, name, entity_type, data):
        self.id = eid
        self.name = name
        self.entity_type = entity_type
        self.data = data
        self.state = "idle"
        self.x = data.get("x", 0)
        self.y = data.get("y", 0)