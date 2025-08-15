from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import random
import math

from .tasks import TaskQueue
from .entities import NPC
from .worldmap import WorldMap

PERSONALITY_ARCHETYPES = {
    "Expansionist": {"build_bias":1.4,"gather_bias":1.0,"scout_bias":1.0,"guard_bias":1.0,"reserve_ratio":0.5,"reassign_factor":1.0},
    "Defensive":    {"build_bias":1.0,"gather_bias":1.0,"scout_bias":0.8,"guard_bias":1.4,"reserve_ratio":0.9,"reassign_factor":0.9},
    "Economist":    {"build_bias":0.9,"gather_bias":1.5,"scout_bias":0.9,"guard_bias":1.0,"reserve_ratio":1.2,"reassign_factor":1.1},
    "Explorer":     {"build_bias":1.0,"gather_bias":1.0,"scout_bias":1.6,"guard_bias":0.9,"reserve_ratio":0.7,"reassign_factor":1.0},
}

class LeaderProfile:
    def __init__(self):
        self.archetype = random.choice(list(PERSONALITY_ARCHETYPES.keys()))
        base = PERSONALITY_ARCHETYPES[self.archetype]
        def jitter(k): return base[k] * random.uniform(0.9,1.1)
        self.build_bias = jitter("build_bias")
        self.gather_bias = jitter("gather_bias")
        self.scout_bias = jitter("scout_bias")
        self.guard_bias = jitter("guard_bias")
        self.reserve_ratio = jitter("reserve_ratio")
        self.reassign_factor = jitter("reassign_factor")
    def describe(self) -> str:
        return f"{self.archetype} B:{self.build_bias:.2f} G:{self.gather_bias:.2f} S:{self.scout_bias:.2f} Guard:{self.guard_bias:.2f} Rsv:{self.reserve_ratio:.2f}"

class LeaderAIConfig:
    def __init__(self):
        self.evaluate_interval = 180
        self.reassign_interval = 240
        self.house_capacity = 4
        self.house_cost = {"wood":6,"stone":2}
        self.base_builder_ratio = 0.20
        self.base_guard_ratio = 0.15
        self.base_scout_ratio = 0.10
        self.min_gatherers = 4
        self.max_build_tasks = 3
        self.max_scout_tasks = 8
        self.max_gather_tasks = 40
        self.max_guard_patrol_tasks = 6
        self.resource_scan_limit = 6000

class LeaderAI:
    def __init__(self, materials: Dict[str,int]):
        self.cfg = LeaderAIConfig()
        self.profile = LeaderProfile()
        self.materials = materials
        self.task_queue = TaskQueue()
        self.last_eval_tick = 0
        self.last_reassign_tick = 0
        self.population_housing = 0
        self.stats = {"build_created":0,"gather_created":0,"scout_created":0,"guard_created":0}
        self.cached_resource_tiles: List[Tuple[int,int,int,str]] = []

    def update(self, tick: int, npcs: List[NPC], world: WorldMap):
        if tick - self.last_eval_tick >= self.cfg.evaluate_interval:
            self._evaluate_world_state(npcs, world)
            self._update_resource_cache(world)
            self._generate_tasks(npcs, world)
            self.last_eval_tick = tick
        if tick - self.last_reassign_tick >= int(self.cfg.reassign_interval * self.profile.reassign_factor):
            self._rebalance_roles(npcs)
            self.last_reassign_tick = tick
        self._assign_tasks(npcs)

    def _evaluate_world_state(self, npcs: List[NPC], world: WorldMap):
        houses = world.all_positions_of_type("house")
        self.population_housing = len(houses) * self.cfg.house_capacity

    def _update_resource_cache(self, world: WorldMap):
        result: List[Tuple[int,int,int,str]] = []
        for y in range(world.height):
            row = world.tiles[y]
            for x in range(world.width):
                tile = row[x]
                if tile.has_resource_stock():
                    if len(result) < self.cfg.resource_scan_limit:
                        result.append((tile.data.get("resource_stock",0), x, y, tile.data.get("resource_type","")))
        result.sort(key=lambda t: t[0], reverse=True)
        self.cached_resource_tiles = result[:200]

    def _rebalance_roles(self, npcs: List[NPC]):
        total = len(npcs)
        if total <= 0:
            return
        # leader giữ nguyên vai trò
        builders_desired = max(1, int((total-1) * self.cfg.base_builder_ratio * self.profile.build_bias))
        scouts_desired = max(1, int((total-1) * self.cfg.base_scout_ratio * self.profile.scout_bias))
        guards_desired = max(1, int((total-1) * self.cfg.base_guard_ratio * self.profile.guard_bias))
        gather_min = max(self.cfg.min_gatherers, (total-1) // 3)

        counts = {"builder":0,"scout":0,"guard":0,"gatherer":0}
        for n in npcs:
            if n.role in counts:
                counts[n.role] += 1

        def promote(from_roles, target_role, needed):
            if needed <= 0:
                return
            for n in npcs:
                if n.npc_id == 0:  # leader không đổi role
                    continue
                if needed <= 0:
                    break
                if n.role in from_roles:
                    n.assign_role(target_role)
                    needed -= 1

        if counts["gatherer"] < gather_min:
            promote(["idle","builder","scout","guard"], "gatherer", gather_min - counts["gatherer"])
            counts = {"builder":0,"scout":0,"guard":0,"gatherer":0}
            for n in npcs:
                if n.role in counts:
                    counts[n.role] += 1

        if counts["builder"] < builders_desired:
            promote(["idle","gatherer","scout","guard"], "builder", builders_desired - counts["builder"])
        counts = {"builder":0,"scout":0,"guard":0,"gatherer":0}
        for n in npcs:
            if n.role in counts:
                counts[n.role] += 1
        if counts["scout"] < scouts_desired:
            promote(["idle","gatherer","builder","guard"], "scout", scouts_desired - counts["scout"])
        counts = {"builder":0,"scout":0,"guard":0,"gatherer":0}
        for n in npcs:
            if n.role in counts:
                counts[n.role] += 1
        if counts["guard"] < guards_desired:
            promote(["idle","gatherer","builder","scout"], "guard", guards_desired - counts["guard"])

        for n in npcs:
            if n.npc_id == 0:
                continue
            if n.role == "idle":
                n.assign_role("gatherer")

    def _generate_tasks(self, npcs: List[NPC], world: WorldMap):
        total = len(npcs)
        if total <= 0:
            return
        existing = self.task_queue.to_list()
        cnt_build = sum(1 for t in existing if t["type"] == "build_house")
        cnt_gather = sum(1 for t in existing if t["type"] == "gather")
        cnt_scout = sum(1 for t in existing if t["type"] == "scout_explore")
        cnt_guard = sum(1 for t in existing if t["type"] == "patrol")
        # BUILD
        housing_need = 0.0
        if total >= self.population_housing:
            deficit = total - self.population_housing
            housing_need = (1.0 + deficit / max(1,total)) * self.profile.build_bias
        if housing_need > 0.5 and cnt_build < self.cfg.max_build_tasks:
            if self._materials_available(self.cfg.house_cost):
                pos = self._pick_house_site(world)
                if pos:
                    self.task_queue.push({
                        "type":"build_house",
                        "priority":1,
                        "data":{"pos":pos,"cost":dict(self.cfg.house_cost)},
                        "difficulty":2.0
                    })
                    self.stats["build_created"] += 1
        # GATHER
        desired_gather = min(int(self.profile.gather_bias * 10) + 5, self.cfg.max_gather_tasks)
        res_idx = 0
        while cnt_gather < desired_gather and res_idx < len(self.cached_resource_tiles):
            stock,x,y,rtype = self.cached_resource_tiles[res_idx]
            res_idx += 1
            if stock <= 0:
                continue
            # Chỉ tạo gather task nếu chưa có NPC nào đang gather tại cùng (x,y)
            if not any(npc.task and npc.task.get("type")=="gather" and npc.task.get("data",{}).get("pos")==(x,y) for npc in npcs):
                self.task_queue.push({
                    "type":"gather",
                    "priority":4,
                    "data":{"pos":(x,y),"rtype":rtype},
                    "difficulty":1.0
                })
                cnt_gather += 1
                self.stats["gather_created"] += 1
        # SCOUT
        desired_scout = min(int(self.profile.scout_bias * 5) + 1, self.cfg.max_scout_tasks)
        while cnt_scout < desired_scout:
            pos = (random.randint(0, world.width-1), random.randint(0, world.height-1))
            self.task_queue.push({
                "type":"scout_explore",
                "priority":6,
                "data":{"pos":pos},
                "difficulty":1.2
            })
            cnt_scout += 1
            self.stats["scout_created"] += 1
        # GUARD
        desired_guard = min(int(self.profile.guard_bias * 5) + 1, self.cfg.max_guard_patrol_tasks)
        while cnt_guard < desired_guard:
            pos = (random.randint(0, world.width-1), random.randint(0, world.height-1))
            self.task_queue.push({
                "type":"patrol",
                "priority":7,
                "data":{"pos":pos},
                "difficulty":1.0
            })
            cnt_guard += 1
            self.stats["guard_created"] += 1

    def _assign_tasks(self, npcs: List[NPC]):
        if len(self.task_queue) == 0:
            return
        snapshot = sorted(self.task_queue.to_list(), key=lambda t: t["priority"])
        for npc in npcs:
            if npc.npc_id == 0 or npc.task is not None or not npc.alive or npc.state != "idle":
                continue
            task = self._pick_task_for_role(snapshot, npc.role)
            if not task:
                continue
            if task["type"] == "build_house":
                if not self._consume_materials(task["data"]["cost"]):
                    continue
            tid = task["id"]
            self.task_queue.remove_where(lambda tt: tt["id"] == tid)
            npc.start_task(task)
            snapshot = sorted(self.task_queue.to_list(), key=lambda t: t["priority"])
            if len(snapshot) == 0:
                break

    def _pick_task_for_role(self, tasks: List[Dict[str,Any]], role: str) -> Optional[Dict[str,Any]]:
        prefer = {
            "builder": ("build_house","gather"),
            "gatherer": ("gather","build_house"),
            "scout": ("scout_explore","gather"),
            "guard": ("patrol","gather"),
            "idle": ("gather","build_house")
        }.get(role, ("gather",))
        for p in prefer:
            for t in tasks:
                if t["type"] == p:
                    return t
        return tasks[0] if tasks else None

    def _pick_house_site(self, world: WorldMap) -> Optional[Tuple[int,int]]:
        houses = world.all_positions_of_type("house")
        targets = houses if houses else [(world.width//2, world.height//2)]
        return world.find_build_spot_near(targets)

    def _materials_available(self, cost: Dict[str,int]) -> bool:
        for k,v in cost.items():
            if self.materials.get(k,0) < v:
                return False
        return True

    def _consume_materials(self, cost: Dict[str,int]) -> bool:
        if not self._materials_available(cost):
            return False
        for k,v in cost.items():
            self.materials[k] -= v
        return True