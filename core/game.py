import pygame
from core.map import TileMap
from core.camera import Camera
from core.npc import NPCManager
from core.resource import ResourceManager
from core.building import BuildingManager
from core.event import EventManager
from core.trait import TraitManager
from core.faction import FactionManager
from core.policy import PolicyManager
from core.ui import UIManager
from core.utils import load_json

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.tile_size = 32
        self.map_size = 77
        self.camera = Camera(self.map_size, self.map_size, self.width, self.height, self.tile_size)
        self.tilemap = TileMap(self.map_size, self.map_size, self.tile_size)
        self.trait_mgr = TraitManager("data/traits.json")
        self.res_mgr = ResourceManager("data/resources.json", self.tilemap)
        self.build_mgr = BuildingManager("data/buildings.json", self.tilemap)
        self.faction_mgr = FactionManager("data/factions.json")
        self.policy_mgr = PolicyManager("data/policies.json")
        self.npc_mgr = NPCManager(
            self.tilemap,
            self.res_mgr,
            self.build_mgr,
            self.trait_mgr,
            self.faction_mgr,
            self.policy_mgr
        )
        self.event_mgr = EventManager("data/events.json", self.npc_mgr)
        self.ui_mgr = UIManager(self.screen, self)
        self.speed = 1
        self.tick_count = 0
        self.log_list = []
        self.override_event = None

    def handle_event(self, event):
        self.ui_mgr.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.camera.move(0, -1)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.camera.move(0, 1)
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                self.camera.move(-1, 0)
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                self.camera.move(1, 0)
            elif event.key == pygame.K_1:
                self.speed = 1
            elif event.key == pygame.K_3:
                self.speed = 3
            elif event.key == pygame.K_0:
                self.speed = 10
            elif event.key == pygame.K_o:
                self.override_event = True

    def update(self):
        if self.event_mgr.pending_event and self.override_event:
            self.event_mgr.override_event()
            self.override_event = None
            self.log("God intervened in event.")
        self.tick_count += 1
        if self.tick_count % self.speed == 0:
            self.npc_mgr.update(self.event_mgr)
            self.res_mgr.update()
            self.event_mgr.update()
            self.build_mgr.update()
            self.tilemap.update()
            self.policy_mgr.update()
            self.faction_mgr.update()
            if self.event_mgr.last_log:
                self.log(self.event_mgr.last_log)
                self.event_mgr.last_log = ""
            for msg in self.policy_mgr.log:
                self.log(msg)
            self.policy_mgr.log.clear()
        self.camera.update()

    def render(self):
        self.tilemap.render(self.screen, self.camera)
        self.res_mgr.render(self.screen, self.camera)
        self.build_mgr.render(self.screen, self.camera)
        self.npc_mgr.render(self.screen, self.camera)
        self.ui_mgr.render()
        self.render_top_ui()

    def render_top_ui(self):
        font = pygame.font.SysFont("consolas", 18)
        pygame.draw.rect(self.screen, (0,0,0), (0, 0, self.width, 42))
        txt = font.render(f"Tick: {self.tick_count} | Speed: x{self.speed} | [WASD/Arrows] Cam | [1/3/0] Speed | [O] Override", True, (255,255,255))
        self.screen.blit(txt, (8, 4))

    def log(self, msg):
        self.log_list.append(msg)
        if len(self.log_list) > 100:
            self.log_list = self.log_list[-100:]

    def speed_tick(self):
        if self.speed == 1:
            return 15
        if self.speed == 3:
            return 45
        if self.speed == 10:
            return 150
        return 15