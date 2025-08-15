import random
from core.npc import NPC
from core.quest import Quest

NAMES = ["Alex", "Bryn", "Cara", "Dax", "Eva", "Finn", "Gia", "Hugo", "Ira", "Jin", "Kai", "Luz", "Mila", "Nico", "Oda", "Pax", "Quin", "Rex", "Sia", "Tara"]
JOBS = ["farmer", "soldier", "merchant", "mage", "healer", "hunter", "miner", "blacksmith", "explorer", "trainer"]
SKILLS = ["gather", "farm", "combat", "defend", "trade", "negotiation", "magic", "cast", "heal", "medicine", "hunt", "track", "mine", "forge", "lead", "special", "explore", "research", "train"]

class AutoGen:
    @staticmethod
    def gen_npc(npcid=None):
        name = random.choice(NAMES)
        job = random.choice(JOBS)
        level = random.randint(1, 7)
        exp = random.randint(0, 90)
        skills = random.sample(SKILLS, k=2)
        return NPC(npcid or f"npc_auto_{random.randint(1000,9999)}", name, {
            "name": name, "job": job, "level": level, "exp": exp, "skills": skills, 
            "house": None, "party": None, "morale": 1.0, "loyalty": 1.0
        })
    
    @staticmethod
    def gen_quest():
        key = f"quest_auto_{random.randint(1000,9999)}"
        name = random.choice(["Thám hiểm rừng sâu", "Tiêu diệt boss", "Khám phá kho báu", "Hộ tống thương nhân", "Xây dựng công trình"])
        desc = f"Nhiệm vụ tự động sinh: {name}"
        reward = {"gold": random.randint(50,300), "exp": random.randint(10,40)}
        require = {"party": 1, "job": random.choice(JOBS)}
        return Quest(key, {"name": name, "desc": desc, "reward": reward, "require": require})
