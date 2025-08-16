import pygame
from core.entities import Sect, Role, Division
from core.sect_manager import SectManager
from core.sect_leader_ai import SectLeaderAI
from core.worldmap import WorldMap
from core.camera import Camera
from gui.game_gui import GameGUI

def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 864))  # H tăng 20%
    pygame.display.set_caption("Frost World - Tông Chủ Quyết")
    clock = pygame.time.Clock()

    manager = SectManager()
    sect = manager.create_sect("Vô Cực Môn", "Vô Cực Tông Chủ")
    leader = sect.get_leader()
    leader_ai = SectLeaderAI(sect, leader.id)

    # Khởi tạo đệ tử
    manager.add_member("Vô Cực Môn", "A Nhị", Role.DISCIPLE, Division.WORKER, True)
    manager.add_member("Vô Cực Môn", "A Tam", Role.DISCIPLE, Division.WORKER, True)
    manager.add_member("Vô Cực Môn", "A Tứ", Role.DISCIPLE, Division.SCOUT, True)
    manager.add_member("Vô Cực Môn", "A Ngũ", Role.DISCIPLE, Division.LOGISTICS, True)
    manager.add_member("Vô Cực Môn", "A Đại", Role.DISCIPLE, Division.GUARD, True)

    worldmap = WorldMap()
    camera = Camera(worldmap.w, worldmap.h, 640, 500, 16)
    gui = GameGUI(screen, sect, leader_ai, manager, worldmap, camera)

    # Resource tổng: bổ sung các loại
    materials = {"wood": 20, "stone": 20, "food": 10, "water": 10, "soil": 20}
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            gui.handle_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    camera.move(-4, 0)
                elif event.key == pygame.K_d:
                    camera.move(4, 0)
                elif event.key == pygame.K_w:
                    camera.move(0, -4)
                elif event.key == pygame.K_s:
                    camera.move(0, 4)

        # AI leader quyết định blueprint, clear, build, task
        leader_ai.decide_action(worldmap, materials)
        leader_ai.sync_build_queue(worldmap, materials)

        # NPC di chuyển, collect, build, resource tăng đúng
        worldmap.member_move_tick([m for m in sect.members.values() if m.alive], leader_ai.build_queue, leader_ai.collect_queue, resources=materials)
        worldmap.update_member_positions([m for m in sect.members.values() if m.alive])

        for _ in range(gui.speed-1):  # Speed x3, x10...
            leader_ai.decide_action(worldmap, materials)
            leader_ai.sync_build_queue(worldmap, materials)
            worldmap.member_move_tick([m for m in sect.members.values() if m.alive], leader_ai.build_queue, leader_ai.collect_queue, resources=materials)
            worldmap.update_member_positions([m for m in sect.members.values() if m.alive])

        gui.update()
        gui.render()
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()