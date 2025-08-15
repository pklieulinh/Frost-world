class MapTile:
    def __init__(self, x, y, terrain="grass", building=None):
        self.x = x
        self.y = y
        self.terrain = terrain
        self.building = building

class KingdomMap:
    def __init__(self, w, h):
        self.width = w
        self.height = h
        self.grid = [[MapTile(x, y) for y in range(h)] for x in range(w)]