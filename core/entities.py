from typing import List, Dict, Optional
import uuid
import random

class Role:
    SECT_LEADER = "Tông Chủ"
    ELDER = "Trưởng Lão"
    DISCIPLE = "Đệ Tử"
    OUTSIDER = "Ngoại Nhân"

class Division:
    FORGE_HALL = "Luyện Khí Các"
    PHARMACY_HALL = "Dược Vương Điện"
    SHADOW_HALL = "Ám Ảnh Các"
    LAW_HALL = "Chấp Pháp Đường"
    DEFENSE_HALL = "Hộ Sơn Đường"
    SCOUT = "Trinh Sát"
    GUARD = "Cảnh Giới"
    LOGISTICS = "Tổng Quản"
    WORKER = "Công Tượng"

DEFAULT_MAP_W = 64
DEFAULT_MAP_H = 48

class SectMember:
    def __init__(self, name: str, role: str = Role.DISCIPLE, division: str = "", is_founder: bool = False, x: Optional[int]=None, y: Optional[int]=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.division = division
        self.is_founder = is_founder
        self.alive = True
        self.loyalty = 100
        self.skills: Dict[str, int] = {}
        self.memory: List[str] = []
        self.current_task: Optional[str] = None
        self.state = "idle"
        self.build_target = None
        # Vị trí trên bản đồ, random hoặc truyền vào
        self.x = x if x is not None else random.randint(0, DEFAULT_MAP_W-1)
        self.y = y if y is not None else random.randint(0, DEFAULT_MAP_H-1)

    def receive_command(self, command: str):
        if self.alive:
            self.memory.append(command)

    def assign_task(self, task: str):
        self.current_task = task

    def __repr__(self):
        alive_str = " [Đã chết]" if not self.alive else ""
        return f"{self.name} ({self.role}) [{self.division}]{' [Khai Sơn Đệ Tử]' if self.is_founder else ''}{alive_str}"

class Sect:
    def __init__(self, name: str, founder: str):
        self.name = name
        self.members: Dict[str, SectMember] = {}
        self.founder_id = None
        self.timeline_stage = 1
        self.history: List[str] = []
        self.sect_commands: List[str] = []
        self.resources: Dict[str, int] = {"water": 10, "food": 10, "farm_land": 1, "tools": 2, "money": 5}
        self.famous = False
        self.holy_site = False
        self.add_member(founder, Role.SECT_LEADER, "", is_founder=True)

    def add_member(self, name, role, division, is_founder=False, x=None, y=None):
        member = SectMember(name, role, division, is_founder, x, y)
        self.members[member.id] = member
        if is_founder and not self.founder_id:
            self.founder_id = member.id
        self.history.append(f"Đưa {name} ({role}) vào tông môn ở {division}.")
        return member.id

    def remove_member(self, member_id):
        if member_id in self.members:
            self.members[member_id].alive = False
            self.history.append(f"{self.members[member_id].name} đã rời khỏi tông môn hoặc đã chết.")

    def get_leader(self) -> Optional[SectMember]:
        for m in self.members.values():
            if m.role == Role.SECT_LEADER and m.alive:
                return m
        return None

    def issue_command(self, command: str):
        leader = self.get_leader()
        if leader:
            leader.receive_command(command)
            self.sect_commands.append(command)
            self.history.append(f"Tông Chủ ban lệnh: {command}")

    def leader_assign(self, task: str):
        leader = self.get_leader()
        if leader:
            leader.assign_task(task)
            self.history.append(f"Tông Chủ nhận nhiệm vụ: {task}")

    def get_resource(self, resource: str) -> int:
        return self.resources.get(resource, 0)

    def set_resource(self, resource: str, value: int):
        self.resources[resource] = value

    def get_population(self) -> int:
        return sum(1 for m in self.members.values() if m.alive)

    def is_famous(self) -> bool:
        return self.famous

    def set_famous(self, val: bool):
        self.famous = val

    def has_holy_site(self) -> bool:
        return self.holy_site

    def set_holy_site(self, val: bool):
        self.holy_site = val

    def __repr__(self):
        leader = self.get_leader()
        return (f"Tông môn {self.name} do {leader.name if leader else 'Không rõ'} lãnh đạo\n"
                f"Số thành viên: {self.get_population()}\n"
                f"Giai đoạn phát triển: {self.timeline_stage}/5")