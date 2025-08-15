import pygame
from typing import List, Optional
from core.entities import NPC
from core.worldmap import WorldMap

NPC_DOT_COLOR = (240, 225, 90)
NPC_LEADER_COLOR = (255, 80, 80)
NPC_NAME_COLOR = (230, 230, 230)
PANEL_BG = (25, 25, 30)
PANEL_BORDER = (70, 70, 80)
PANEL_HILITE = (80, 120, 200)
PANEL_LEADER = (200, 60, 60)
TEXT_NORMAL = (210, 210, 210)
TEXT_DIM = (140, 140, 150)
ROLE_COLOR = {
    "leader": (255,80,80),
    "builder": (200,180,120),
    "gatherer": (150,220,150),
    "scout": (150,180,240),
    "guard": (240,140,140),
    "idle": (180,180,180),
    "patrol": (240,140,140)
}
HP_BAR_BG = (40,40,40)
HP_BAR_FG = (40,200,60)

class WorldRenderer:
    def __init__(self, tile_size: int, font_small: pygame.font.Font = None):
        self.tile_size = tile_size
        self.font_small = font_small or pygame.font.SysFont("arial", 11)

    def render_world(self, surface: pygame.Surface, world: WorldMap):
        for y in range(world.view_y, world.view_y + world.view_h):
            for x in range(world.view_x, world.view_x + world.view_w):
                tile = world.get_tile(x, y)
                if tile is None:
                    continue
                rx = (x - world.view_x) * self.tile_size
                ry = (y - world.view_y) * self.tile_size
                color = self._color_for(tile.type)
                pygame.draw.rect(surface, color, (rx, ry, self.tile_size, self.tile_size))

    def _color_for(self, tile_type: str):
        return {
            "water": (40, 90, 170),
            "mountain": (100, 100, 105),
            "forest": (35, 130, 45),
            "house": (185, 145, 105),
            "grass": (60, 165, 60)
        }.get(tile_type, (100, 100, 100))

    def render_npcs(self, surface: pygame.Surface, world: WorldMap, npcs: List[NPC]):
        for npc in npcs:
            if not npc.alive:
                continue
            if not (world.view_x <= npc.x < world.view_x + world.view_w and world.view_y <= npc.y < world.view_y + world.view_h):
                continue
            sx = (npc.x - world.view_x) * self.tile_size + self.tile_size // 2
            sy = (npc.y - world.view_y) * self.tile_size + self.tile_size // 2
            if npc.role == "leader":
                pygame.draw.circle(surface, NPC_LEADER_COLOR, (sx, sy), 5)
            else:
                pygame.draw.rect(surface, NPC_DOT_COLOR, (sx, sy, 2, 2))
            name_surface = self.font_small.render(npc.name, True, NPC_NAME_COLOR)
            surface.blit(name_surface, (sx + 3, sy - 6))
            ratio = max(0.0, min(1.0, npc.hp / npc.hp_max))
            pygame.draw.rect(surface, HP_BAR_BG, (sx, sy+3, 16, 3))
            pygame.draw.rect(surface, HP_BAR_FG, (sx, sy+3, int(16*ratio), 3))

class NPCPanel:
    def __init__(self, x: int, y: int, width: int, height: int, line_height: int = 18):
        self.rect = pygame.Rect(x, y, width, height)
        self.line_height = line_height
        self.scroll = 0
        self.font = pygame.font.SysFont("consolas", 14)
        self.small = pygame.font.SysFont("consolas", 12)
        self.selected_id: int = -1
        self.follow_enabled = True

    def handle_event(self, event, npcs: List[NPC]):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if event.button == 1:
                    local_y = event.pos[1] - self.rect.y
                    idx = local_y // self.line_height + self.scroll
                    if 0 <= idx < len(npcs):
                        self.selected_id = npcs[idx].npc_id if self.selected_id != npcs[idx].npc_id else self.selected_id
                elif event.button == 4:
                    self.scroll = max(0, self.scroll - 1)
                elif event.button == 5:
                    max_scroll = max(0, len(npcs) - self.visible_lines())
                    self.scroll = min(max_scroll, self.scroll + 1)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                self.follow_enabled = not self.follow_enabled

    def visible_lines(self) -> int:
        return max(1, self.rect.height // self.line_height)

    def get_selected(self, npcs: List[NPC]) -> Optional[NPC]:
        for n in npcs:
            if n.npc_id == self.selected_id:
                return n
        return None

    def render(self, surface: pygame.Surface, npcs: List[NPC]):
        pygame.draw.rect(surface, PANEL_BG, self.rect)
        pygame.draw.rect(surface, PANEL_BORDER, self.rect, 1)
        # Leader on top
        npcs_sorted = sorted(npcs, key=lambda n: (0 if n.role=="leader" else 1, n.npc_id))
        # Title
        title = self.font.render("NPCs", True, TEXT_NORMAL)
        surface.blit(title, (self.rect.x + 6, self.rect.y + 4))
        y_start = self.rect.y + 4 + self.line_height
        visible = self.visible_lines() - 1
        slice_start = self.scroll
        slice_end = min(len(npcs_sorted), slice_start + visible)
        for i, npc in enumerate(npcs_sorted[slice_start:slice_end], start=0):
            real_index = slice_start + i
            ly = y_start + i * self.line_height
            selected = (npc.npc_id == self.selected_id)
            if npc.role == "leader":
                pygame.draw.rect(surface, PANEL_LEADER, (self.rect.x+2, ly, self.rect.width-4, self.line_height-1))
            elif selected:
                pygame.draw.rect(surface, PANEL_HILITE, (self.rect.x+2, ly, self.rect.width-4, self.line_height-1))
            role_color = ROLE_COLOR.get(npc.role, TEXT_NORMAL)
            task_type = npc.task["type"] if npc.task else "idle"
            leader_tag = " [LEADER]" if npc.role == "leader" else ""
            text = f"{npc.npc_id:02d} {npc.name} [{npc.role[:3]}]{leader_tag} {task_type}"
            ts = self.small.render(text, True, (0,0,0) if (selected or npc.role=="leader") else role_color)
            surface.blit(ts, (self.rect.x + 6, ly + 1))
        # Scroll indicator
        if len(npcs_sorted) > visible:
            ratio = (self.scroll / max(1, len(npcs_sorted)-visible))
            bar_h = max(12, int(self.rect.height * visible / max(visible, len(npcs_sorted))))
            bar_y = self.rect.y + int((self.rect.height - bar_h) * ratio)
            pygame.draw.rect(surface, (60,60,70), (self.rect.right - 10, self.rect.y+2, 8, self.rect.height-4))
            pygame.draw.rect(surface, (140,140,160), (self.rect.right - 10, bar_y, 8, bar_h))
        footer = self.small.render(f"Follow: {'ON' if self.follow_enabled else 'OFF'} (F)", True, TEXT_DIM)
        surface.blit(footer, (self.rect.x + 6, self.rect.bottom - self.line_height + 2))