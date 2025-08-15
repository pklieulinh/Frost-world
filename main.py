import pygame
import sys
from typing import List

from core.worldmap import WorldMap
from core.entities import NPC
from core.leader import LeaderAI
from ui.render import WorldRenderer, NPCPanel

SCREEN_W = 1280
SCREEN_H = 720
TARGET_FPS = 60

VIEW_W = 48
VIEW_H = 27

WORLD_SCREEN_W = SCREEN_W - 300
TILE_SIZE = min(WORLD_SCREEN_W // VIEW_W, SCREEN_H // VIEW_H)
if TILE_SIZE < 8:
    TILE_SIZE = 8

PANEL_WIDTH = 300

def init_pygame():
    pygame.init()
    flags = pygame.HWSURFACE | pygame.DOUBLEBUF
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
    pygame.display.set_caption("Frost World - Leader Core (Steps 2 & 3)")
    return screen

def create_initial_npcs(count: int, world: WorldMap) -> List[NPC]:
    npcs: List[NPC] = []
    midx, midy = world.width // 2, world.height // 2
    npcs.append(NPC(0, "LEADER", midx, midy, is_leader=True))
    for i in range(1, count):
        npcs.append(NPC(i, f"N{i}", midx, midy))
    return npcs

def accumulate_resource_yields(npcs: List[NPC], leader: LeaderAI):
    for npc in npcs:
        if not npc.pending_resources:
            continue
        for res, amount in npc.pending_resources:
            leader.materials[res] = leader.materials.get(res, 0) + amount
        npc.pending_resources.clear()

def handle_events(running_flag: List[bool], panel: NPCPanel, npcs: List[NPC], speed_state: dict):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running_flag[0] = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running_flag[0] = False
            elif event.key == pygame.K_1:
                speed_state["game_speed"] = 1
            elif event.key == pygame.K_3:
                speed_state["game_speed"] = 3
            elif event.key == pygame.K_0:
                speed_state["game_speed"] = 10
        panel.handle_event(event, npcs)

def update_npcs(npcs: List[NPC], world: WorldMap, dt: float):
    for npc in npcs:
        npc.update(dt, world)

def follow_camera(world: WorldMap, panel: NPCPanel, npcs: List[NPC]):
    if not panel.follow_enabled or panel.selected_id < 0:
        return
    target = panel.get_selected(npcs)
    if not target or not target.alive:
        return
    world.center_on(target.x, target.y)

def draw(screen, world, npcs, leader, tick, renderer: WorldRenderer, panel: NPCPanel, game_speed: int):
    screen.fill((15,15,20))
    renderer.render_world(screen, world)
    renderer.render_npcs(screen, world, npcs)
    font = pygame.font.SysFont("arial", 16)
    hud_lines = [
        f"Tick: {tick}",
        f"Speed: x{game_speed}   (1,3,0 to change)",
        f"Leader: {npcs[0].name} ({leader.profile.archetype})",
        f"Pop: {len(npcs)} Housing: {leader.population_housing}",
        f"Materials: {leader.materials}",
        f"Tasks: {len(leader.task_queue)}",
        f"Profile: {leader.profile.describe()}",
        "LMB: chọn NPC | F: toggle follow | Wheel: scroll NPC list"
    ]
    y = 4
    for line in hud_lines:
        ts = font.render(line, True, (235,235,235))
        screen.blit(ts, (6, y))
        y += 20
    panel.render(screen, sorted(npcs, key=lambda n: (0 if n.role=="leader" else 1, n.npc_id)))
    pygame.display.flip()

def main():
    screen = init_pygame()
    clock = pygame.time.Clock()
    world = WorldMap(77, 77, view_w=VIEW_W, view_h=VIEW_H)
    world.center_on(world.width//2, world.height//2)
    materials = {"wood": 40, "stone": 18}
    leader = LeaderAI(materials)
    print(">>> Leader Profile:", leader.profile.describe())
    renderer = WorldRenderer(TILE_SIZE)
    panel = NPCPanel(SCREEN_W - PANEL_WIDTH, 0, PANEL_WIDTH, SCREEN_H)
    npcs = create_initial_npcs(14, world)
    running = [True]
    tick = 0
    speed_state = {"game_speed": 1}

    while running[0]:
        dt_ms = clock.tick(TARGET_FPS)
        if dt_ms > 250:
            dt_ms = 250
        dt = dt_ms / 1000.0
        handle_events(running, panel, npcs, speed_state)
        tick += 1
        dt_logic = dt * speed_state["game_speed"]
        leader.update(tick, npcs, world)
        update_npcs(npcs, world, dt_logic)
        accumulate_resource_yields(npcs, leader)
        follow_camera(world, panel, npcs)
        draw(screen, world, npcs, leader, tick, renderer, panel, speed_state["game_speed"])
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()