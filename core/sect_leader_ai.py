from enum import Enum
from typing import Dict, List, Optional
import math
import random

HOUSE_CAPACITY = 4  # Số người mỗi nhà ở tối đa

class Stage(Enum):
    SHADOW = 1
    ROOT = 2
    EMERGENCE = 3
    RENOWN = 4
    HOLYLAND = 5

class SectPolicy:
    def __init__(self, name: str, priorities: Dict, commands: List[str], description: str):
        self.name = name
        self.priorities = priorities
        self.commands = commands
        self.description = description

class SectLeaderAI:
    def __init__(self, sect, leader_id):
        self.sect = sect
        self.leader_id = leader_id
        self.stage = Stage.SHADOW
        self.stages_policy = self._build_stages_policy()
        self.memory: List[str] = []
        self.stage_years = 0
        self.build_queue = []
        self.collect_queue = []
        self.ml_history: List[Dict] = []
        self.blueprint_region = None

    def _build_stages_policy(self) -> Dict[Stage, SectPolicy]:
        return {
            Stage.SHADOW: SectPolicy(
                "Sinh Tồn Tuyệt Đối",
                priorities={"discipline": 1, "food": 1, "water": 1, "hide": 2, "recruit": 2, "medicine": 2, "shelter": 3, "defense": 3},
                commands=[
                    "Tuyệt đối giữ im lặng, tuân thủ mệnh lệnh.",
                    "Ưu tiên nước sạch, thức ăn an toàn, không được ăn linh tinh.",
                    "Chỉ nhóm lửa để đun nước, không dùng để sưởi.",
                    "Phân vai rõ ràng, kỷ luật sắt đá.",
                    "Xây dựng nơi trú ẩn kín đáo, ngụy trang tối đa.",
                    "Thiết lập hệ thống cảnh báo thô sơ, ưu tiên phòng thủ bị động.",
                    "Xây hố xí, đảm bảo vệ sinh chung nghiêm ngặt.",
                ],
                description="Tồn tại trong bóng tối, không để ai phát hiện."
            ),
        }

    def get_current_policy(self):
        return self.stages_policy.get(self.stage) or list(self.stages_policy.values())[0]

    def choose_base_region(self, worldmap, population):
        best_score = -1
        best_rect = None
        for _ in range(20):
            x1 = random.randint(2, worldmap.w-9)
            y1 = random.randint(2, worldmap.h-9)
            x2, y2 = x1+6, y1+6
            score = 0
            for xx in range(x1, x2+1):
                for yy in range(y1, y2+1):
                    t = worldmap.get_tile(xx, yy)
                    if t and t.resource in ["soil", "wood"] and t.resource_amt > 0: score += 2
                    elif t and t.resource == "stone" and t.resource_amt > 0: score += 1
            if score > best_score:
                best_score = score
                best_rect = (x1,y1,x2,y2)
        self.blueprint_region = best_rect
        return best_rect

    def is_tile_in_queue(self, queue, x, y):
        return any(cmd.get("x")==x and cmd.get("y")==y for cmd in queue)

    def get_idle_npc(self, members, exclude_ids=None):
        if exclude_ids is None:
            exclude_ids = set()
        return [m for m in members if getattr(m, "state", "idle") == "idle" and m.id not in exclude_ids]

    def assign_collect_task(self, worldmap, members):
        if not self.blueprint_region: return
        (x1,y1,x2,y2) = self.blueprint_region
        task_tiles = []
        for x in range(x1, x2+1):
            for y in range(y1, y2+1):
                tile = worldmap.get_tile(x, y)
                if tile and tile.is_resource() and not self.is_tile_in_queue(self.collect_queue, x, y):
                    task_tiles.append((x, y))
        idle_members = self.get_idle_npc(members)
        for tilepos, m in zip(task_tiles, idle_members):
            self.collect_queue.append({"member": m, "x": tilepos[0], "y": tilepos[1], "progress": 0})
            m.state = "moving"

    def assign_build_task(self, worldmap, members, type_name):
        if not self.blueprint_region: return
        (x1,y1,x2,y2) = self.blueprint_region
        for x in range(x1, x2+1):
            for y in range(y1, y2+1):
                tile = worldmap.get_tile(x, y)
                if tile and tile.resource=="none" and not tile.pending_build and tile.type=="field" and not self.is_tile_in_queue(self.build_queue, x, y):
                    idle = next((m for m in members if getattr(m, "state", "idle") == "idle"), None)
                    if idle:
                        self.build_queue.append({"member": idle, "x": x, "y": y, "progress": 0, "type": type_name, "pending_materials": False})
                        idle.state = "moving"
                        worldmap.set_pending_build(x, y, True, f"{type_name.title()}")
                        break

    def decide_action(self, worldmap, materials):
        leader = self.sect.get_leader()
        if not leader: return
        members = [m for m in self.sect.members.values() if m.alive]
        population = len(members)
        # Nếu chưa có blueprint thì chọn vùng
        if not self.blueprint_region:
            region = self.choose_base_region(worldmap, population)
            if region:
                x = (region[0] + region[2]) // 2
                y = (region[1] + region[3]) // 2
                leader.x, leader.y = x, y
        # Giao collect task cho các tile còn resource (ưu tiên farm đầu tiên)
        self.assign_collect_task(worldmap, members)
        if self.collect_queue: return
        # Khi vùng đã clear, xây farm trước, sau đó nhà, rồi mới tới các công trình khác
        num_farm = sum(1 for x in range(worldmap.w) for y in range(worldmap.h) if worldmap.get_tile(x, y).type == "farm")
        num_home = sum(1 for x in range(worldmap.w) for y in range(worldmap.h) if worldmap.get_tile(x, y).type == "home")
        required_farm = max(1, population // 2)
        required_home = max(1, math.ceil(population / HOUSE_CAPACITY))
        # Ưu tiên farm, rồi home, rồi mới đến các công trình khác
        if num_farm < required_farm:
            self.assign_build_task(worldmap, members, "farm")
        elif num_home < required_home:
            self.assign_build_task(worldmap, members, "home")
        # TODO: phát triển các công trình tiếp theo (workshop, defense...)

    def sync_build_queue(self, worldmap, materials):
        for cmd in self.collect_queue[:]:
            member = cmd.get("member")
            tx, ty = cmd.get("x"), cmd.get("y")
            tile = worldmap.get_tile(tx, ty)
            if not tile:
                self.collect_queue.remove(cmd)
                continue
            if getattr(member, "state", "") == "collecting":
                cmd["progress"] += 1
                if tile.resource_amt == 0 or cmd["progress"] > 8:
                    member.state = "idle"
                    self.collect_queue.remove(cmd)
        for cmd in self.build_queue[:]:
            member = cmd.get("member")
            tx, ty = cmd.get("x"), cmd.get("y")
            tile = worldmap.get_tile(tx, ty)
            if not tile:
                self.build_queue.remove(cmd)
                continue
            if getattr(member, "state", "") == "building":
                cmd["progress"] += 1
                if cmd["progress"] >= 60:
                    worldmap.set_pending_build(tx, ty, False, "Xây xong")
                    if cmd["type"] == "farm":
                        tile.type = "farm"
                    elif cmd["type"] == "home":
                        tile.type = "home"
                    member.state = "idle"
                    self.build_queue.remove(cmd)
                    self.ml_record_reward(member, f"build_{cmd['type']}", (tx, ty), reward=1.0)

    def ml_record_state_action(self, member, action, target):
        state = self._ml_get_state_snapshot()
        self.ml_history.append({
            "t": "state_action",
            "member_id": member.id,
            "action": action,
            "target": target,
            "state": state
        })

    def ml_record_reward(self, member, action, target, reward):
        self.ml_history.append({
            "t": "reward",
            "member_id": member.id,
            "action": action,
            "target": target,
            "reward": reward
        })

    def _ml_get_state_snapshot(self):
        return {
            "members_alive": sum(1 for m in self.sect.members.values() if m.alive),
            "resources": dict(self.sect.resources),
            "stage": self.stage.name
        }