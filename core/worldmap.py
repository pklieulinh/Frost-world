import pygame
import random

MAP_W, MAP_H, TILE_SIZE = 64, 58, 16
RESOURCE_TYPES = [
    ("wood", (120, 80, 40)),
    ("stone", (180, 180, 180)),
    ("water", (80, 180, 240)),
    ("soil", (170, 210, 120)),
    ("none", (0,0,0)),
]
TILE_TYPES = [
    ("village", (240,220,170)), ("field", (170,220,120)),
    ("forest", (60,120,60)), ("dungeon", (80,80,120)),
    ("road", (180,180,140)), ("river", (80,180,240)),
    ("building", (220,200,100)), ("danger", (220,100,80)),
    ("farm", (170,210,120)), ("home", (255,210,170)),
    ("workshop", (180,180,100)), ("pending_build", (250,230,64))
]

RESOURCE_INIT = {
    "wood": 20,
    "stone": 15,
    "water": 10,
    "soil": 20,
    "none": 0,
}

class Tile:
    def __init__(self, x, y, ttype="field"):
        self.x, self.y = x, y
        self.type = ttype
        self.occupants = []
        self.zone = ttype
        self.pending_build = False
        self.building_name = None
        self.resource = self.gen_resource()
        self.resource_amt = RESOURCE_INIT[self.resource]

    def gen_resource(self):
        r = random.random()
        if r < 0.13: return "wood"
        if r < 0.22: return "stone"
        if r < 0.27: return "water"
        if r < 0.40: return "soil"
        return "none"

    def is_passable(self):
        return self.type not in ["river", "danger", "dungeon"] and not self.pending_build

    def is_resource(self):
        return self.resource != "none" and self.resource_amt > 0

    def deplete_resource(self, amt):
        self.resource_amt = max(0, self.resource_amt - amt)
        if self.resource_amt == 0:
            self.type = "field"
            self.resource = "none"

class WorldMap:
    def __init__(self):
        self.w, self.h = MAP_W, MAP_H
        self.tiles = [[Tile(x, y, self.gen_tiletype(x, y)) for y in range(self.h)] for x in range(self.w)]
        self.view_x = 0
        self.view_y = 0
        self.view_w = 32
        self.view_h = 34

    def gen_tiletype(self, x, y):
        cx, cy = MAP_W//2, MAP_H//2
        if abs(x-cx)<3 and abs(y-cy)<2:
            return "village"
        elif (x in [0, self.w-1] or y in [0, self.h-1]):
            return "forest" if (x+y)%2==0 else "dungeon"
        elif (x in [1, self.w-2] or y in [1, self.h-2]):
            return "danger"
        elif (x==cx and y in range(cy-8, cy+8)):
            return "river"
        elif (abs(y-cy)<2):
            return "road"
        else:
            return "field"

    def get_tile(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.tiles[x][y]
        return None

    def update_member_positions(self, members):
        for col in self.tiles:
            for tile in col:
                tile.occupants = []
        for m in members:
            if not getattr(m, "alive", True): continue
            x, y = int(getattr(m, "x", 0)), int(getattr(m, "y", 0))
            if 0 <= x < self.w and 0 <= y < self.h:
                tile = self.get_tile(x, y)
                if tile:
                    tile.occupants.append(m)

    def member_move_tick(self, members, build_queue, collect_queue, resources=None):
        for m in members:
            if not getattr(m, "alive", True): continue
            # Clamp vị trí trong map
            m.x = max(0, min(self.w - 1, int(m.x)))
            m.y = max(0, min(self.h - 1, int(m.y)))
            m._stuck_count = getattr(m, "_stuck_count", 0)
            # Collect task (ưu tiên)
            cmd = next((cmd for cmd in collect_queue if cmd.get("member") == m), None)
            if cmd:
                tx, ty = cmd["x"], cmd["y"]
                reached = (m.x, m.y) == (tx, ty)
                moved = self.smart_move(m, tx, ty)
                if reached:
                    tile = self.get_tile(tx, ty)
                    if tile and tile.is_resource():
                        # Tăng resource tổng khi thu thập
                        if resources is not None and tile.resource in resources:
                            resources[tile.resource] += 1
                        tile.deplete_resource(1)
                        m.state = "collecting"
                        cmd["progress"] += 1
                        m._stuck_count = 0
                        if tile.resource_amt == 0 or cmd["progress"] > 8:
                            m.state = "idle"
                            collect_queue.remove(cmd)
                    else:
                        m.state = "idle"
                        collect_queue.remove(cmd)
                elif moved:
                    m.state = "moving"
                    m._stuck_count = 0
                else:
                    m._stuck_count += 1
                    # Nếu stuck quá 10 lần, huỷ task
                    if m._stuck_count > 10:
                        m.state = "idle"
                        collect_queue.remove(cmd)
                continue
            # Build task
            cmd = next((cmd for cmd in build_queue if cmd.get("member") == m), None)
            if cmd and not cmd.get("pending_materials", False):
                tx, ty = cmd["x"], cmd["y"]
                reached = (m.x, m.y) == (tx, ty)
                moved = self.smart_move(m, tx, ty)
                if reached:
                    m.state = "building"
                    m._stuck_count = 0
                elif moved:
                    m.state = "moving"
                    m._stuck_count = 0
                else:
                    m._stuck_count += 1
                    if m._stuck_count > 10:
                        m.state = "idle"
                        build_queue.remove(cmd)
            else:
                m.state = "idle"
                m._stuck_count = 0

    def smart_move(self, m, tx, ty):
        # Defensive: clamp target trong map
        tx = max(0, min(self.w - 1, int(tx)))
        ty = max(0, min(self.h - 1, int(ty)))
        dx = tx - m.x
        dy = ty - m.y
        step_x = 1 if dx > 0 else -1 if dx < 0 else 0
        step_y = 1 if dy > 0 else -1 if dy < 0 else 0
        options = []
        if step_x != 0:
            options.append((m.x + step_x, m.y))
        if step_y != 0:
            options.append((m.x, m.y + step_y))
        if step_x != 0 and step_y != 0:
            options.append((m.x + step_x, m.y + step_y))
        options = [(x, y) for x, y in options if 0 <= x < self.w and 0 <= y < self.h]
        for nx, ny in options:
            tile = self.get_tile(nx, ny)
            if tile and tile.is_passable():
                m.x, m.y = nx, ny
                return True
        # fallback: random step in bound
        for _ in range(4):
            dx, dy = random.choice([-1,0,1]), random.choice([-1,0,1])
            tx2, ty2 = max(0, min(self.w-1, m.x+dx)), max(0, min(self.h-1, m.y+dy))
            t2 = self.get_tile(tx2, ty2)
            if t2 and t2.is_passable():
                m.x, m.y = tx2, ty2
                return True
        return False

    def set_pending_build(self, x, y, val=True, building_name=None):
        tile = self.get_tile(x, y)
        if tile:
            tile.pending_build = val
            tile.building_name = building_name if val else None
            if not val:
                tile.type = "building"

    def get_tile_info(self, x, y):
        tile = self.get_tile(x, y)
        if not tile:
            return "Ngoài biên bản đồ."
        s = f"Tile ({x},{y})\n"
        s += f"Loại: {tile.type}\n"
        if tile.resource and tile.resource != "none":
            s += f"Tài nguyên: {tile.resource} ({tile.resource_amt})\n"
        if tile.pending_build:
            s += "Đang chờ xây dựng\n"
        if tile.building_name:
            s += f"Công trình: {tile.building_name}\n"
        if tile.occupants:
            s += "NPC trên tile:\n"
            for o in tile.occupants:
                s += f" - {o.name} ({o.role})\n"
        return s.strip()

    def screen_to_tile(self, mx, my, ox, oy, tile_size):
        tx = (mx - ox) // tile_size + self.view_x
        ty = (my - oy) // tile_size + self.view_y
        if 0 <= tx < self.w and 0 <= ty < self.h:
            return tx, ty
        return None, None

    def render(self, screen, ox, oy, members, sect, build_queue, camera=None, tile_size=16, highlight_tile=None):
        font = pygame.font.SysFont("consolas", 10)
        for x in range(self.view_x, min(self.view_x+self.view_w, self.w)):
            for y in range(self.view_y, min(self.view_y+self.view_h, self.h)):
                tile = self.tiles[x][y]
                color = dict(TILE_TYPES).get(tile.type, (200,200,200))
                if tile.pending_build:
                    color = dict(TILE_TYPES).get("pending_build",(250,230,64))
                rect = pygame.Rect(ox+(x-self.view_x)*tile_size, oy+(y-self.view_y)*tile_size, tile_size, tile_size)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (50,50,60), rect, 1)
                if tile.resource and tile.resource != "none":
                    rcolor = dict(RESOURCE_TYPES).get(tile.resource, (100, 80, 60))
                    pygame.draw.rect(screen, rcolor, rect.inflate(-8,-8))
                if tile.type in ["building", "home", "workshop", "farm"]:
                    pygame.draw.rect(screen, (120,80,10), rect.inflate(-4,-4))
                if tile.pending_build:
                    pygame.draw.rect(screen, (250,200,40), rect.inflate(-8,-8), border_radius=2)
                if highlight_tile and (x, y) == highlight_tile:
                    pygame.draw.rect(screen, (255,255,0), rect, 2)
        for m in members:
            if not getattr(m, "alive", True): continue
            tx, ty = int(m.x), int(m.y)
            if not (self.view_x <= tx < self.view_x+self.view_w and self.view_y <= ty < self.view_y+self.view_h): continue
            px, py = ox+(tx-self.view_x)*tile_size, oy+(ty-self.view_y)*tile_size
            color = (250,210,40) if getattr(m,"role","")=="Tông Chủ" else (90,180,255)
            border = (255,120,40) if getattr(m,"role","")=="Tông Chủ" else (50,60,70)
            if getattr(m,"state","") == "building":
                color = (220,140,50)
            elif getattr(m,"state","") == "moving":
                color = (80,120,220)
            elif getattr(m,"state","") == "collecting":
                color = (120,180,140)
            pygame.draw.rect(screen, color, (px+2,py+2,tile_size-4,tile_size-4))
            pygame.draw.rect(screen, border, (px,py,tile_size,tile_size), 1)
            label = m.name[0].upper()
            screen.blit(font.render(label, True, (10,30,40)), (px+tile_size//2-5, py+tile_size//2-7))
            if getattr(m,"state","") == "building": screen.blit(font.render("X",True,(130,30,0)), (px+tile_size//2-2, py+tile_size//2+1))
            if getattr(m,"state","") == "moving": screen.blit(font.render("D",True,(40,80,130)), (px+tile_size//2-2, py+tile_size//2+1))
            if getattr(m,"state","") == "collecting": screen.blit(font.render("C",True,(20,120,60)), (px+tile_size//2-2, py+tile_size//2+1))
            if camera and camera.following_member == m:
                pygame.draw.rect(screen, (255,80,80), (px-1, py-1, tile_size+2, tile_size+2), 2)