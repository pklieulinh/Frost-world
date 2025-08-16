class ResourceManager:
    def __init__(self, worldmap):
        self.worldmap = worldmap
        self.resources = {"food": 10, "water": 10, "wood": 10, "stone": 10}
        self.occupancy = {}  # (x,y): member
        self.farm_workers = set()
        self.home_occupants = dict()  # (x,y): list of member ids

    def update(self, members):
        # Farm: food tăng nếu có người làm tại farm
        farm_tiles = [(x, y) for x in range(self.worldmap.w) for y in range(self.worldmap.h) if self.worldmap.get_tile(x, y).type == "farm"]
        for fx, fy in farm_tiles:
            if (fx, fy) in self.occupancy:
                self.resources["food"] += 1
        # Home: morale tăng nếu có người ở
        # Workshop, water, wood, stone... có thể mở rộng thêm

    def assign(self, member, x, y):
        # Đánh dấu member đang làm tại (x,y)
        self.occupancy[(x, y)] = member

    def leave(self, member):
        # Xóa occupancy khi member rời
        for k, v in list(self.occupancy.items()):
            if v == member:
                del self.occupancy[k]

    def get(self, res):
        return self.resources.get(res, 0)

    def set(self, res, val):
        self.resources[res] = val