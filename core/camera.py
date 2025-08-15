class Camera:
    def __init__(self, map_w, map_h, screen_w, screen_h, tile_size):
        self.map_w = map_w
        self.map_h = map_h
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.tile_size = tile_size
        self.x = max(0, map_w // 2 - screen_w // (2 * tile_size))
        self.y = max(0, map_h // 2 - screen_h // (2 * tile_size))
        self.following_npc = None

    def move(self, dx, dy):
        self.x = max(0, min(self.x + dx, self.map_w - self.screen_w // self.tile_size))
        self.y = max(0, min(self.y + dy, self.map_h - self.screen_h // self.tile_size))
        self.following_npc = None

    def update(self):
        if self.following_npc:
            tx = max(0, self.following_npc.x - self.screen_w // (2 * self.tile_size))
            ty = max(0, self.following_npc.y - self.screen_h // (2 * self.tile_size))
            self.x = min(tx, self.map_w - self.screen_w // self.tile_size)
            self.y = min(ty, self.map_h - self.screen_h // self.tile_size)

    def follow_npc(self, npc):
        self.following_npc = npc

    def world_to_screen(self, wx, wy):
        px = (wx - self.x) * self.tile_size
        py = (wy - self.y) * self.tile_size
        return px, py