from core.entities import Sect, Role, Division
from typing import List, Optional

class SectManager:
    def __init__(self):
        self.sects: dict = {}

    def create_sect(self, name: str, founder: str) -> Sect:
        sect = Sect(name, founder)
        self.sects[sect.name] = sect
        return sect

    def add_member(self, sect_name: str, name: str, role: str, division: str, is_founder: bool = False):
        if sect_name not in self.sects:
            return None
        return self.sects[sect_name].add_member(name, role, division, is_founder)

    def remove_member(self, sect_name: str, member_id: str):
        if sect_name in self.sects:
            self.sects[sect_name].remove_member(member_id)

    def issue_command(self, sect_name: str, command: str):
        if sect_name in self.sects:
            self.sects[sect_name].issue_command(command)

    def advance_stage(self, sect_name: str):
        if sect_name in self.sects:
            self.sects[sect_name].timeline_stage = min(5, self.sects[sect_name].timeline_stage + 1)

    def get_sect_info(self, sect_name: str) -> Optional[str]:
        if sect_name in self.sects:
            return repr(self.sects[sect_name])
        return None

    def get_member_list(self, sect_name: str) -> List[str]:
        if sect_name in self.sects:
            return [repr(m) for m in self.sects[sect_name].members.values()]
        return []

    def get_timeline_stage(self, sect_name: str) -> int:
        if sect_name in self.sects:
            return self.sects[sect_name].timeline_stage
        return 0

    def get_leader(self, sect_name: str) -> Optional[str]:
        if sect_name in self.sects:
            leader = self.sects[sect_name].get_leader()
            if leader:
                return leader.name
        return None