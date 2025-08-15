import pygame
from core.utils import load_json
from core.npc import NPC
from core.hero import Hero
from core.building import Building
from core.job import Job
from core.skill import Skill
from core.event import EventManager
from core.quest import QuestBoard
from core.party import Party
from core.kingdom import KingdomState
from core.ui import UIManager

def load_entities(npc_path, hero_path, building_path, job_path, skill_path, event_path, quest_path, party_path, kingdom_path):
    npc_data = load_json(npc_path)
    hero_data = load_json(hero_path)
    build_data = load_json(building_path)
    job_data = load_json(job_path)
    skill_data = load_json(skill_path)
    event_data = load_json(event_path)
    quest_data = load_json(quest_path)
    party_data = load_json(party_path)
    kingdom_data = load_json(kingdom_path)
    npcs = {k: NPC(k, v["name"], v) for k,v in npc_data.items()}
    heroes = {k: Hero(k, v["name"], v) for k,v in hero_data.items()}
    buildings = [Building(k, v["name"], v) for k,v in build_data.items()]
    jobs = {k: Job(k, v) for k,v in job_data.items()}
    skills = {k: Skill(k, v) for k,v in skill_data.items()}
    questboard = QuestBoard(quest_data)
    parties = [Party(pid, pdata, npcs, heroes) for pid, pdata in party_data.items()]
    kingdom = KingdomState(kingdom_data)
    kingdom.npcs = list(npcs.values())
    kingdom.heroes = list(heroes.values())
    kingdom.buildings = buildings
    kingdom.parties = parties
    return npcs, heroes, buildings, jobs, skills, event_data, questboard, parties, kingdom

def can_build_here(wm, x, y, kingdom, build_queue):
    tile = wm.get_tile(x, y)
    if not tile or tile.type in ["river","building","danger","dungeon"]: return False
    if tile.pending_build: return False
    for b in kingdom.buildings:
        if b.data.get("x")==x and b.data.get("y")==y:
            return False
    for cmd in build_queue:
        if cmd["x"]==x and cmd["y"]==y:
            return False
    return True

BUILD_MATERIALS = {
    "house": {"wood": 10, "stone": 5},
    "upgrade": {"wood": 8, "stone": 8}
}

def enough_materials(materials, need):
    for k,v in need.items():
        if materials.get(k,0)<v:
            return False
    return True

def sub_materials(materials, need):
    for k,v in need.items():
        if materials.get(k,0)>=v:
            materials[k] -= v

def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Kingdom Adventurers Prototype - GeminiForge")
    npcs, heroes, buildings, jobs, skills, event_data, questboard, parties, kingdom = load_entities(
        "data/npcs.json", "data/heroes.json", "data/buildings.json", "data/jobs.json", "data/skills.json", "data/events.json", "data/quests.json", "data/parties.json", "data/kingdom.json"
    )
    ui_mgr = UIManager(screen)
    event_mgr = EventManager(event_data)
    running = True
    clock = pygame.time.Clock()
    popup_shown_prev = False
    build_queue = []
    build_timer = 0
    build_history = []
    # Dummy vật liệu vương quốc
    materials = {"wood": 30, "stone": 15}
    # Event/quest: tự động tăng vật liệu 1 lần mỗi 1000 tick, và khi quest thành công
    tick = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    ui_mgr.worldmap.view_x = max(0, ui_mgr.worldmap.view_x-4)
                if event.key == pygame.K_d:
                    ui_mgr.worldmap.view_x = min(ui_mgr.worldmap.w-ui_mgr.worldmap.view_w, ui_mgr.worldmap.view_x+4)
                if event.key == pygame.K_w:
                    ui_mgr.worldmap.view_y = max(0, ui_mgr.worldmap.view_y-4)
                if event.key == pygame.K_s:
                    ui_mgr.worldmap.view_y = min(ui_mgr.worldmap.h-ui_mgr.worldmap.view_h, ui_mgr.worldmap.view_y+4)
            elif event.type == pygame.MOUSEMOTION:
                ui_mgr.handle_mouse(event.pos, kingdom.npcs, kingdom.heroes, kingdom.parties, questboard, event_mgr, kingdom, build_queue)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if ui_mgr.tooltip_visible:
                    ui_mgr.hide_tooltip()
        # Tăng vật liệu qua event/quest/production
        tick += 1
        if tick % 1000 == 0:
            materials["wood"] += 10
            materials["stone"] += 5
            event_mgr.event_log.append(("PROD", "Sản xuất vật liệu: +10 wood, +5 stone"))
        # Quest hoàn thành thì tăng vật liệu
        if hasattr(questboard, "active_quests"):
            for q in questboard.active_quests:
                if getattr(q, "status", "") == "done":
                    materials["wood"] += 2
                    materials["stone"] += 2
                    event_mgr.event_log.append(("QUEST", f"Hoàn thành '{q.name}': +2 wood, +2 stone"))
                    q.status = "archived"
        # AI leader: xây nhiều loại công trình, ưu tiên nhà chưa có, upgrade khi đủ
        build_timer += 1
        if build_timer > 600:
            build_timer = 0
            leader = kingdom.get_leader()
            homeless = [n for n in kingdom.npcs if not n.house and not getattr(n,"build_target",None)]
            wm = ui_mgr.worldmap
            # Xây nhà
            while homeless and len(build_queue)<3:
                field_candidates = []
                for x in range(wm.w):
                    for y in range(wm.h):
                        if can_build_here(wm, x, y, kingdom, build_queue):
                            dist = min(abs(x-vx)+abs(y-vy) for vx in range(wm.w) for vy in range(wm.h) if wm.get_tile(vx,vy).type=="village")
                            field_candidates.append((dist,x,y))
                if not field_candidates:
                    event_mgr.event_log.append(("AI", "Không tìm thấy vị trí xây nhà hợp lệ!"))
                    break
                field_candidates.sort()
                _, tx, ty = field_candidates[0]
                n = homeless.pop(0)
                mat_need = dict(BUILD_MATERIALS["house"])
                if enough_materials(materials, mat_need):
                    sub_materials(materials, mat_need)
                    build_queue.append({"npc": n, "x": tx, "y": ty, "progress": 0, "required_materials": mat_need.copy(), "type": "house", "priority": 1})
                    n.build_target = (tx, ty)
                    wm.get_tile(tx, ty).pending_build = True
                    event_mgr.event_log.append(("AI", f"Leader ra lệnh cho {n.name} xây nhà tại ({tx},{ty}), trừ vật liệu {mat_need}"))
                else:
                    build_queue.append({"npc": n, "x": tx, "y": ty, "progress": 0, "pending_materials": True, "required_materials": mat_need.copy(), "type": "house", "priority": 1})
                    n.build_target = (tx, ty)
                    wm.get_tile(tx, ty).pending_build = True
                    event_mgr.event_log.append(("AI", f"Thiếu vật liệu khi ra lệnh cho {n.name} xây tại ({tx},{ty}), chờ bổ sung"))
            # Nâng cấp nhà khi đủ
            upgrades = [b for b in kingdom.buildings if b.data.get("level",1)<3]
            for b in upgrades:
                owner = next((n for n in kingdom.npcs if getattr(n,"house",None)==b.id), None)
                if not owner or any(cmd.get("type")=="upgrade" and cmd.get("npc")==owner for cmd in build_queue): continue
                mat_need = dict(BUILD_MATERIALS["upgrade"])
                if enough_materials(materials, mat_need):
                    sub_materials(materials, mat_need)
                    build_queue.append({"npc": owner, "x": b.data.get("x"), "y": b.data.get("y"), "progress": 0, "required_materials": mat_need.copy(), "type": "upgrade", "priority": 2, "building": b})
                    event_mgr.event_log.append(("AI", f"Nâng cấp nhà cho {owner.name} tại ({b.data.get('x')},{b.data.get('y')})"))
        # Xử lý lệnh xây nhà/nâng cấp
        for cmd in build_queue[:]:
            npc = cmd["npc"]
            tx, ty = cmd["x"], cmd["y"]
            tile = ui_mgr.worldmap.get_tile(tx, ty)
            if not tile:
                event_mgr.event_log.append(("BUILD", f"Tile ({tx},{ty}) không tồn tại, hủy lệnh xây!"))
                build_queue.remove(cmd)
                continue
            if getattr(npc,"house",None) and cmd.get("type")=="house":
                tile.pending_build = False
                build_queue.remove(cmd)
                continue
            if cmd.get("pending_materials",False):
                mat_need = cmd["required_materials"]
                if enough_materials(materials, mat_need):
                    sub_materials(materials, mat_need)
                    cmd["pending_materials"] = False
                    event_mgr.event_log.append(("AI", f"Đủ vật liệu, bắt đầu xây nhà tại ({tx},{ty}) cho {npc.name}"))
                continue
            if (npc.x, npc.y) != (tx, ty):
                npc.state = "moving"
                npc.build_target = (tx, ty)
            else:
                npc.state = "building"
                cmd["progress"] += 1
                # Defensive: NPC chết/null/rời kingdom
                if npc not in kingdom.npcs:
                    build_queue.remove(cmd)
                    tile.pending_build = False
                    event_mgr.event_log.append(("BUILD", "NPC đã rời khỏi kingdom, hủy lệnh xây!"))
                    continue
                # Xây xong
                if cmd["progress"]>=120:
                    if cmd.get("type")=="house":
                        from core.building import Building
                        home_id = f"house_auto_{npc.id}"
                        home_data = {"name":f"Nhà {npc.name}","type":"house","level":1,"owner":npc.id,"x":tx,"y":ty}
                        new_build = Building(home_id, home_data["name"], home_data)
                        kingdom.buildings.append(new_build)
                        npc.house = home_id
                        npc.state = "idle"
                        npc.build_target = None
                        tile.pending_build = False
                        build_history.append(f"{npc.name} xây nhà tại ({tx},{ty})")
                        build_queue.remove(cmd)
                        event_mgr.event_log.append(("BUILD", f"{npc.name} đã xây nhà thành công tại ({tx},{ty})"))
                    elif cmd.get("type")=="upgrade":
                        b = cmd["building"]
                        b.data["level"] = b.data.get("level",1)+1
                        build_history.append(f"{npc.name} nâng cấp nhà tại ({tx},{ty}) lên lv{b.data['level']}")
                        build_queue.remove(cmd)
                        event_mgr.event_log.append(("BUILD", f"{npc.name} đã nâng cấp nhà tại ({tx},{ty}) thành công"))
                        npc.state = "idle"
        # Update NPC movement
        ui_mgr.worldmap.npc_move_tick(kingdom.npcs, build_queue)
        ui_mgr.worldmap.update_npc_positions(kingdom.npcs)
        # Trigger event: tăng vật liệu qua event thành công
        if pygame.time.get_ticks() % 3000 < 30:
            import random
            event_mgr.check_and_trigger(kingdom, parties, season=random.choice(["spring","summer","autumn","winter"]), fame=kingdom.fame)
            if random.random()<0.3:
                materials["wood"] += 3
                materials["stone"] += 2
                event_mgr.event_log.append(("EVENT", "+3 wood, +2 stone (event)"))
        # Show popup if event just happened
        if event_mgr.event_log and not popup_shown_prev:
            last = event_mgr.event_log[-1]
            if last[0] == "EVENT":
                ui_mgr.popup.show(last[1])
                popup_shown_prev = True
        if not ui_mgr.popup.active:
            popup_shown_prev = False
        ui_mgr.popup.update()
        screen.fill((20,25,40))
        ui_mgr.render(kingdom, parties, questboard, event_mgr, jobs, build_queue)
        # Hiển thị vật liệu vương quốc
        mstr = " | ".join(f"{k}: {v}" for k,v in materials.items())
        screen.blit(ui_mgr.font.render(f"Vật liệu: {mstr}", True, (180,255,180)), (10, 710))
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()

if __name__ == "__main__":
    main()