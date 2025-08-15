import pygame
import random

MAP_W = 64
MAP_H = 48
TILE_SIZE = 16

TILE_TYPES = [
    ("village", (240,220,170)),
    ("field", (170,220,120)),
    ("forest", (60,120,60)),
    ("dungeon", (80,80,120)),
    ("road", (180,180,140)),
    ("river", (80,180,240)),
    ("building", (220,200,100)),
    ("danger", (220,100,80)),
    ("pending_build", (250,230,64))
]

class Tile:
    def __init__(self, x, y, ttype="field"):
        self.x = x
        self.y = y
        self.type = ttype
        self.occupants = []
        self.zone = ttype
        self.pending_build = False
        self.building_name = None

class WorldMap:
    def __init__(self):
        self.w = MAP_W
        self.h = MAP_H
        self.tiles = [[Tile(x, y, self.gen_tiletype(x, y)) for y in range(self.h)] for x in range(self.w)]
        self.view_x = 0
        self.view_y = 0
        self.view_w = 32
        self.view_h = 24

    def gen_tiletype(self, x, y):
        # Làng ở giữa, rừng/dungeon ở rìa, river cắt dọc, road cắt ngang
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

    def update_npc_positions(self, npcs):
        for col in self.tiles:
            for tile in col:
                tile.occupants = []
        for n in npcs:
            tx, ty = int(n.x), int(n.y)
            tile = self.get_tile(tx, ty)
            if tile:
                tile.occupants.append(n)

    def npc_move_tick(self, npcs, build_queue):
        for n in npcs:
            # Nếu đang có lệnh xây thì đi theo lệnh
            cmd = next((cmd for cmd in build_queue if cmd["npc"]==n), None)
            if cmd and not cmd.get("pending_materials",False):
                tx, ty = cmd["x"], cmd["y"]
                if (n.x, n.y) != (tx, ty):
                    n.state = "moving"
                    n.build_target = (tx, ty)
                    if n.x < tx: n.x += 1
                    elif n.x > tx: n.x -= 1
                    if n.y < ty: n.y += 1
                    elif n.y > ty: n.y -= 1
                else:
                    n.state = "building"
            else:
                for _ in range(3):
                    dx, dy = random.choice([-1,0,1]), random.choice([-1,0,1])
                    tx, ty = max(0,min(self.w-1,n.x+dx)), max(0,min(self.h-1,n.y+dy))
                    t = self.get_tile(tx, ty)
                    if t and t.type!="river" and not t.pending_build:
                        n.x, n.y = tx, ty
                        break

    def draw(self, screen, ox, oy, npcs, kingdom, build_queue):
        for x in range(self.view_x, min(self.view_x+self.view_w, self.w)):
            for y in range(self.view_y, min(self.view_y+self.view_h, self.h)):
                tile = self.tiles[x][y]
                color = dict(TILE_TYPES).get(tile.type, (200,200,200))
                if tile.pending_build:
                    color = dict(TILE_TYPES).get("pending_build",(250,230,64))
                rect = pygame.Rect(ox+(x-self.view_x)*TILE_SIZE, oy+(y-self.view_y)*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (50,50,60), rect, 1)
                if tile.type == "building":
                    pygame.draw.rect(screen, (120,80,10), rect.inflate(-4,-4))
                if tile.pending_build:
                    pygame.draw.rect(screen, (250,200,40), rect.inflate(-8,-8), border_radius=2)
        # NPC
        for n in npcs:
            tx, ty = int(n.x), int(n.y)
            if not (self.view_x <= tx < self.view_x+self.view_w and self.view_y <= ty < self.view_y+self.view_h): continue
            px, py = ox+(tx-self.view_x)*TILE_SIZE, oy+(ty-self.view_y)*TILE_SIZE
            color = (250,210,40) if getattr(n,"is_hero",False) else (90,180,255)
            border = (255,120,40) if kingdom.leader_id==n.id else (50,60,70)
            if getattr(n,"state","")== "building":
                color = (220,140,50)
            pygame.draw.rect(screen, color, (px+2,py+2,TILE_SIZE-4,TILE_SIZE-4))
            pygame.draw.rect(screen, border, (px,py,TILE_SIZE,TILE_SIZE), 1)
            label = n.name[0].upper()
            font = pygame.font.SysFont("consolas", 12)
            screen.blit(font.render(label, True, (10,30,40)), (px+TILE_SIZE//2-5, py+TILE_SIZE//2-7))
            # Trạng thái
            if getattr(n,"state","") == "building":
                screen.blit(font.render("X",True,(130,30,0)), (px+TILE_SIZE//2-2, py+TILE_SIZE//2+1))
            if getattr(n,"state","") == "moving":
                screen.blit(font.render("D",True,(40,80,130)), (px+TILE_SIZE//2-2, py+TILE_SIZE//2+1))