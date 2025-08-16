class Camera:
    def __init__(self, map_w, map_h, screen_w, screen_h, tile_size):
        self.map_w = map_w
        self.map_h = map_h
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.tile_size = tile_size
        self.x = max(0, map_w // 2 - screen_w // (2 * tile_size))
        self.y = max(0, map_h // 2 - screen_h // (2 * tile_size))
        self.following_member = None
        self.zoom = 1
        self._last_pos = None  # Track last NPC pos to auto update

    def move(self, dx, dy):
        self.x = max(0, min(self.x + dx, self.map_w - self.screen_w // (self.tile_size*self.zoom)))
        self.y = max(0, min(self.y + dy, self.map_h - self.screen_h // (self.tile_size*self.zoom)))
        self.following_member = None

    def update(self):
        if self.following_member:
            tx = int(self.following_member.x)
            ty = int(self.following_member.y)
            # Only update if NPC moved
            if self._last_pos != (tx, ty):
                new_x = max(0, tx - self.screen_w // (2 * self.tile_size * self.zoom))
                new_y = max(0, ty - self.screen_h // (2 * self.tile_size * self.zoom))
                self.x = min(max(new_x, 0), self.map_w - self.screen_w // (self.tile_size*self.zoom))
                self.y = min(max(new_y, 0), self.map_h - self.screen_h // (self.tile_size*self.zoom))
                self._last_pos = (tx, ty)

    def follow_member(self, member):
        self.following_member = member
        self._last_pos = (int(member.x), int(member.y))
        self.update()

    def set_zoom(self, zoom):
        self.zoom = max(1, min(zoom, 4))

    def world_to_screen(self, wx, wy):
        px = (wx - self.x) * self.tile_size * self.zoom
        py = (wy - self.y) * self.tile_size * self.zoom
        return px, py