import random
from typing import List, Optional, Dict, Any, Tuple

class WorldTile:
    __slots__ = ("x", "y", "type", "data")

    def __init__(self, x: int, y: int, tile_type: str = "grass", data: Optional[Dict[str, Any]] = None):
        self.x = x
        self.y = y
        self.type = tile_type
        self.data = data or {}

    def is_buildable(self) -> bool:
        if self.type in ("water", "mountain"):
            return False
        return not self.data.get("blocked", False)

    def has_resource_stock(self) -> bool:
        stock = self.data.get("resource_stock")
        return isinstance(stock, int) and stock > 0

    def harvest(self) -> Optional[str]:
        stock = self.data.get("resource_stock")
        if not isinstance(stock, int) or stock <= 0:
            return None
        rtype = self.data.get("resource_type")
        if rtype not in ("wood", "stone"):
            return None
        self.data["resource_stock"] = stock - 1
        if self.data["resource_stock"] <= 0:
            # Deplete -> becomes grass
            if self.type in ("forest", "mountain"):
                self.type = "grass"
            self.data.pop("resource_type", None)
            self.data.pop("resource_stock", None)
        return rtype


class WorldMap:
    MAX_SIZE = 77

    def __init__(self, width: int = 77, height: int = 77, seed: Optional[int] = None, view_w: int = 48, view_h: int = 27):
        width = max(4, min(self.MAX_SIZE, width))
        height = max(4, min(self.MAX_SIZE, height))
        self.width = width
        self.height = height
        self._seed = seed if seed is not None else random.randint(0, 10_000_000)
        self.tiles: List[List[WorldTile]] = []
        # Camera view window
        self.view_w = min(view_w, self.width)
        self.view_h = min(view_h, self.height)
        self.view_x = 0
        self.view_y = 0
        self._generate()

    def _rng(self) -> random.Random:
        return random.Random(self._seed)

    def _generate(self):
        rnd = self._rng()
        self.tiles = []
        for y in range(self.height):
            row: List[WorldTile] = []
            for x in range(self.width):
                r = rnd.random()
                if r < 0.045:
                    t = "water"
                elif r < 0.085:
                    t = "mountain"
                elif r < 0.15:
                    t = "forest"
                else:
                    t = "grass"
                tile = WorldTile(x, y, t)
                if t == "forest":
                    tile.data["resource_type"] = "wood"
                    tile.data["resource_stock"] = rnd.randint(4, 9)
                elif t == "mountain":
                    tile.data["resource_type"] = "stone"
                    tile.data["resource_stock"] = rnd.randint(5, 12)
                row.append(tile)
            self.tiles.append(row)

    def get_tile(self, x: int, y: int) -> Optional[WorldTile]:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return None
        return self.tiles[y][x]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def all_positions_of_type(self, tile_type: str) -> List[Tuple[int, int]]:
        out: List[Tuple[int, int]] = []
        for y in range(self.height):
            row = self.tiles[y]
            for x in range(self.width):
                if row[x].type == tile_type:
                    out.append((x, y))
        return out

    def find_build_spot_near(self, targets: List[Tuple[int, int]], max_scan: int = 4000) -> Optional[Tuple[int, int]]:
        if not targets:
            return None
        best: Optional[Tuple[int, int]] = None
        best_dist = 10**9
        scanned = 0
        for y in range(self.height):
            for x in range(self.width):
                if scanned >= max_scan:
                    return best
                tile = self.tiles[y][x]
                if tile.is_buildable() and tile.type != "house":
                    md = min(abs(x - tx) + abs(y - ty) for (tx, ty) in targets)
                    if md < best_dist:
                        best_dist = md
                        best = (x, y)
                        if best_dist <= 1:
                            return best
                scanned += 1
        return best

    def clamp_camera(self):
        if self.view_w > self.width:
            self.view_w = self.width
        if self.view_h > self.height:
            self.view_h = self.height
        self.view_x = max(0, min(self.view_x, self.width - self.view_w))
        self.view_y = max(0, min(self.view_y, self.height - self.view_h))

    def move_camera(self, dx: int, dy: int):
        self.view_x += dx
        self.view_y += dy
        self.clamp_camera()

    def center_on(self, x: int, y: int):
        # Center view on (x,y)
        cx = max(0, min(x, self.width - 1))
        cy = max(0, min(y, self.height - 1))
        self.view_x = cx - self.view_w // 2
        self.view_y = cy - self.view_h // 2
        self.clamp_camera()