import logging

class NPC:
    def __init__(self, npc_id, role, profile, is_leader=False):
        self.npc_id = npc_id
        self.role = role
        self.profile = profile
        self.state = 'idle'
        self.is_leader = is_leader
        self.current_task = None

    def can_gather(self):
        # Defensive: Leader phải được phép gather nếu không bị block bởi điều kiện đặc biệt
        if self.is_leader:
            return True  # Leader luôn có thể gather nếu không có task khác ưu tiên
        # Các NPC thường kiểm tra thêm điều kiện, nếu có
        return self.role in ['gat', 'gua', 'bui']

    def assign_task(self, task):
        self.current_task = task
        if task is None:
            self.state = 'idle'
        else:
            self.state = task.type

    def __repr__(self):
        leader_str = "[LEADER]" if self.is_leader else ""
        return f"{self.npc_id} {self.role} {leader_str} {self.state}"

class Task:
    def __init__(self, task_type):
        self.type = task_type  # e.g., 'gather', 'build', etc.

class NPCManager:
    def __init__(self):
        self.npcs = []
        self.tasks = []

    def add_npc(self, npc):
        self.npcs.append(npc)

    def add_task(self, task):
        self.tasks.append(task)

    def assign_tasks(self):
        # Defensive: Nếu không còn task gather, không ai được gather
        gather_tasks = [t for t in self.tasks if t.type == 'gather']
        if not gather_tasks:
            logging.info("No gather tasks available.")
            for npc in self.npcs:
                if npc.state == 'gather':
                    npc.assign_task(None)
            return

        # Xác định danh sách NPC có thể gather, bao gồm cả Leader nếu đủ điều kiện
        for npc in self.npcs:
            if npc.can_gather():
                # Nếu chưa có task hoặc task trước đã xong, gán task mới
                if npc.current_task is None or npc.current_task.type != 'gather':
                    npc.assign_task(gather_tasks[0])
                    logging.info(f"Assigned gather to {npc}")
            else:
                # Defensive: Log lý do tại sao không được giao nhiệm vụ
                logging.warning(f"{npc} cannot gather due to role restrictions or explicit conditions.")

    def debug_states(self):
        # Xuất trạng thái tất cả NPC, log riêng Leader
        for npc in self.npcs:
            leader_tag = "[LEADER]" if npc.is_leader else ""
            print(f"{npc.npc_id} {npc.role} {leader_tag} {npc.state}")
            if npc.is_leader and npc.state == 'idle':
                print(f"DEBUG: Leader {npc.npc_id} is idle. Reason: current_task={npc.current_task}. Profile={npc.profile}")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = NPCManager()

    # Tạo Leader và một số NPC thường
    leader = NPC('LEADER', 'lea', {'Explorer': True}, is_leader=True)
    n1 = NPC('N1', 'gua', {}, is_leader=False)
    n2 = NPC('N2', 'bui', {}, is_leader=False)
    n3 = NPC('N3', 'gat', {}, is_leader=False)

    manager.add_npc(leader)
    manager.add_npc(n1)
    manager.add_npc(n2)
    manager.add_npc(n3)

    # Thêm task gather
    manager.add_task(Task('gather'))

    # Phân task
    manager.assign_tasks()
    manager.debug_states()