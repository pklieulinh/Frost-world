class Progression:
    def __init__(self, npc):
        self.npc = npc

    def gain_exp(self, amount):
        self.npc.exp += amount
        if self.npc.exp >= 100:
            self.npc.level += 1
            self.npc.exp -= 100
            return True
        return False

    def change_job(self, new_job):
        self.npc.job = new_job