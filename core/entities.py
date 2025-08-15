from typing import Optional, Dict, Any, Tuple, List
import random

def clamp_int(v: int, lo: int, hi: int) -> int:
    return lo if v < lo else hi if v > hi else v

class NPC:
    __slots__ = (
        "npc_id","name","x","y","hp","hp_max","role","state","task","task_progress",
        "speed","alive","destination","task_target","pending_resources"
    )

    def __init__(self, npc_id: int, name: str, x: int, y: int, is_leader=False):
        self.npc_id = npc_id
        self.name = name or f"NPC{npc_id}"
        self.x = x
        self.y = y
        self.hp_max = 100
        self.hp = self.hp_max
        self.role = "leader" if is_leader else "idle"
        self.state = "idle"
        self.task: Optional[Dict[str, Any]] = None
        self.task_progress = 0.0
        self.speed = 3.0
        self.alive = True
        self.destination: Optional[Tuple[int,int]] = None
        self.task_target: Optional[Tuple[int,int]] = None
        self.pending_resources: List[Tuple[str,int]] = []

    def assign_role(self, new_role: str):
        # Leader không bị đổi role
        if self.role == "leader":
            return
        self.role = new_role

    def start_task(self, task: Dict[str, Any]):
        self.task = task
        self.state = "working"
        self.task_progress = 0.0
        pos = task.get("data", {}).get("pos")
        if pos and isinstance(pos,(tuple,list)) and len(pos)==2:
            self.task_target = (int(pos[0]), int(pos[1]))
            self.destination = self.task_target
        else:
            self.task_target = None
            self.destination = None

    def complete_task(self):
        self.task = None
        self.state = "idle"
        self.task_progress = 0.0
        self.destination = None
        self.task_target = None

    def fail_task(self):
        self.task = None
        self.state = "idle"
        self.task_progress = 0.0
        self.destination = None
        self.task_target = None

    def update(self, dt: float, world):
        if not self.alive or dt <= 0:
            return
        self._update_position(world)
        if self.task:
            ttype = self.task.get("type")
            if ttype in ("gather","build_house","scout_explore","patrol"):
                self._process_task(dt, world)

    def _update_position(self, world):
        if not self.destination:
            return
        tx, ty = self.destination
        if self.x == tx and self.y == ty:
            self.destination = None
            return
        dx = tx - self.x
        dy = ty - self.y
        if abs(dx) + abs(dy) == 0:
            self.destination = None
            return
        # Step (simple 4-dir)
        if random.random() < 0.5:
            step = (1 if dx > 0 else -1, 0) if dx != 0 else (0, 1 if dy > 0 else -1)
        else:
            step = (0, 1 if dy > 0 else -1) if dy != 0 else (1 if dx > 0 else -1, 0)
        nx = clamp_int(self.x + step[0], 0, world.width - 1)
        ny = clamp_int(self.y + step[1], 0, world.height - 1)
        tile = world.get_tile(nx, ny)
        if tile and tile.type not in ("water","mountain"):
            self.x, self.y = nx, ny
        else:
            # Try alternate
            alt = (step[1], step[0])
            nx2 = clamp_int(self.x + alt[0], 0, world.width - 1)
            ny2 = clamp_int(self.y + alt[1], 0, world.height - 1)
            tile2 = world.get_tile(nx2, ny2)
            if tile2 and tile2.type not in ("water","mountain"):
                self.x, self.y = nx2, ny2
            else:
                self.destination = None  # stuck

    def _process_task(self, dt: float, world):
        if self.task_target:
            if self.x != self.task_target[0] or self.y != self.task_target[1]:
                return
        diff = self.task.get("difficulty", 1.0)
        if diff <= 0:
            diff = 1.0
        self.task_progress += (dt * self.speed) / diff
        if self.task_progress < 1.0:
            return
        ttype = self.task.get("type")
        data = self.task.get("data", {})
        if ttype == "build_house":
            tile = world.get_tile(self.x, self.y)
            if tile and tile.is_buildable():
                tile.type = "house"
                tile.data.pop("resource_type", None)
                tile.data.pop("resource_stock", None)
        elif ttype == "gather":
            tile = world.get_tile(self.x, self.y)
            # gather fail nếu tile không còn resource
            if not tile or not tile.has_resource_stock():
                self.fail_task()
                return
            harvested = tile.harvest()
            if harvested:
                self.pending_resources.append((harvested, 1))
        # scout_explore / patrol: nothing special
        self.complete_task()