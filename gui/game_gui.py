import pygame
from pygame import Rect
from core.entities import Sect, SectMember
from core.camera import Camera

class GameGUI:
    def __init__(self, screen, sect: Sect, leader_ai, manager, worldmap, camera):
        self.screen = screen
        self.sect = sect
        self.leader_ai = leader_ai
        self.manager = manager
        self.worldmap = worldmap
        self.camera = camera
        self.font = pygame.font.SysFont("consolas", 12)
        self.large_font = pygame.font.SysFont("consolas", 16)
        self.panel_color = (48, 64, 56)
        self.bg_color = (32, 48, 32)
        self.text_color = (240, 240, 210)
        self.info_color = (180, 230, 140)
        self.header_color = (40, 80, 50)
        self.npc_panel_rects = []
        self.selected_member = None
        self.zoom = 1
        self.history_offset = 0
        self.speed = 1  # x1, x3, x10
        self.highlight_tile = None
        self.tile_info = ""

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Click map tile: lấy thông tin tile
            map_ox = 192
            map_oy = 54
            tile_sz = int(16 * self.zoom)
            map_w_px = self.worldmap.view_w * tile_sz
            map_h_px = self.worldmap.view_h * tile_sz
            if map_ox <= mx < map_ox + map_w_px and map_oy <= my < map_oy + map_h_px:
                tx, ty = self.worldmap.screen_to_tile(mx, my, map_ox, map_oy, tile_sz)
                if tx is not None and ty is not None:
                    self.highlight_tile = (tx, ty)
                    self.tile_info = self.worldmap.get_tile_info(tx, ty)
            # Side left panel click: NPC select
            for idx, rect in enumerate(self.npc_panel_rects):
                if rect.collidepoint(mx, my):
                    members = [m for m in self.sect.members.values() if m.alive]
                    if 0 <= idx < len(members):
                        self.selected_member = members[idx]
                        self.camera.follow_member(members[idx])
                        break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                self.zoom = min(4, self.zoom + 1)
                self.camera.set_zoom(self.zoom)
            elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                self.zoom = max(1, self.zoom - 1)
                self.camera.set_zoom(self.zoom)
            elif event.key == pygame.K_PAGEUP:
                self.history_offset = max(0, self.history_offset-1)
            elif event.key == pygame.K_PAGEDOWN:
                self.history_offset = min(max(0, len(self.sect.history)-12), self.history_offset+1)
            elif event.key == pygame.K_1:
                self.speed = 1
            elif event.key == pygame.K_3:
                self.speed = 3
            elif event.key == pygame.K_0:
                self.speed = 10

    def update(self):
        self.camera.update()

    def render(self):
        self.screen.fill(self.bg_color)
        self.draw_header()
        self.draw_member_side_panel()
        self.draw_map()
        self.draw_member_detail_panel()
        self.draw_history_panel()
        self.draw_tile_tooltip()

    def draw_header(self):
        s = self.sect
        surf = pygame.Surface((self.screen.get_width(), 48))
        surf.fill(self.header_color)
        lines = [
            f"{s.name} | Giai đoạn: {s.timeline_stage}/5 | Tông Chủ: {s.get_leader().name if s.get_leader() else 'Không rõ'} | Thành viên: {s.get_population()} | Tốc độ: x{self.speed}",
            f"Tài nguyên: Nước {s.get_resource('water')} | Thức ăn {s.get_resource('food')} | Đất NN {s.get_resource('farm_land')} | Dụng cụ {s.get_resource('tools')} | Tiền {s.get_resource('money')} | Nổi tiếng: {'Có' if s.is_famous() else 'Chưa'} | Thánh địa: {'Có' if s.has_holy_site() else 'Chưa'}"
        ]
        for i, line in enumerate(lines):
            text = self.large_font.render(line, True, self.info_color)
            surf.blit(text, (10, 3 + i*22))
        self.screen.blit(surf, (0, 0))

    def draw_member_side_panel(self):
        s = self.sect
        members = [m for m in s.members.values() if m.alive]
        panel_x, panel_y = 0, 48
        panel_w, panel_h = 180, self.screen.get_height() - 98
        pygame.draw.rect(self.screen, self.panel_color, Rect(panel_x, panel_y, panel_w, panel_h), border_radius=8)
        text = self.font.render("Đệ tử:", True, self.info_color)
        self.screen.blit(text, (panel_x + 10, panel_y + 6))
        self.npc_panel_rects = []
        for i, m in enumerate(members):
            y = panel_y + 30 + i * 18
            label = f"{m.name} [{m.role}]"
            rect = pygame.Rect(panel_x + 8, y, panel_w-16, 16)
            self.screen.blit(self.font.render(label, True, self.text_color), (panel_x + 14, y+1))
            self.npc_panel_rects.append(rect)
            if self.selected_member == m:
                pygame.draw.rect(self.screen, (200,180,80), rect, 2)

    def draw_map(self):
        map_w, map_h = self.worldmap.view_w, self.worldmap.view_h
        tile_sz = int(16 * self.zoom)
        ox = 192
        oy = 54
        surf_w = map_w * tile_sz
        surf_h = map_h * tile_sz
        map_surf = pygame.Surface((surf_w, surf_h))
        self.worldmap.render(map_surf, 0, 0, [m for m in self.sect.members.values() if m.alive], self.sect, self.leader_ai.build_queue, self.camera, tile_size=tile_sz, highlight_tile=self.highlight_tile)
        self.screen.blit(map_surf, (ox, oy))

    def draw_member_detail_panel(self):
        panel_w, panel_h = 200, self.screen.get_height() - 98
        panel_x, panel_y = self.screen.get_width() - panel_w, 48
        pygame.draw.rect(self.screen, self.panel_color, Rect(panel_x, panel_y, panel_w, panel_h), border_radius=8)
        if not self.selected_member:
            self.screen.blit(self.font.render("Chọn 1 đệ tử để xem", True, self.info_color), (panel_x+10, panel_y+12))
            return
        m = self.selected_member
        lines = [
            f"Tên: {m.name}",
            f"Vai trò: {m.role}",
            f"Phòng ban: {m.division}",
            f"Trung thành: {m.loyalty}",
            f"Trạng thái: {getattr(m,'state','idle')}",
            f"Nhiệm vụ: {m.current_task if m.current_task else 'Không'}",
            f"Vị trí: ({m.x},{m.y})",
            f"Kỹ năng: {', '.join(m.skills.keys()) if m.skills else 'Không'}",
        ]
        for i, line in enumerate(lines):
            self.screen.blit(self.font.render(line, True, self.text_color), (panel_x+12, panel_y+12 + i*15))

    def draw_history_panel(self):
        x, y = 0, self.screen.get_height() - 70
        panel_width = self.screen.get_width()
        panel_height = 70
        pygame.draw.rect(self.screen, self.panel_color, Rect(x, y, panel_width, panel_height), border_radius=8)
        self.screen.blit(self.font.render("Lịch sử tông môn:", True, self.info_color), (x + 10, y + 6))
        visible_lines = 3 + (panel_height-24)//13
        history = self.sect.history
        offset = self.history_offset
        lines = history[-visible_lines-offset:len(history)-offset] if len(history)-offset > 0 else []
        for i, line in enumerate(lines):
            self.screen.blit(self.font.render(line, True, self.text_color), (x + 12, y + 24 + i * 13))

    def draw_tile_tooltip(self):
        # Hiển thị thông tin tile khi click
        if self.highlight_tile and self.tile_info:
            panel_w, panel_h = 240, 138
            panel_x, panel_y = (self.screen.get_width() // 2) - 120, 60
            pygame.draw.rect(self.screen, (60,60,40), Rect(panel_x, panel_y, panel_w, panel_h), border_radius=8)
            lines = self.tile_info.split("\n")
            for i, line in enumerate(lines):
                self.screen.blit(self.font.render(line, True, (240,240,200)), (panel_x+12, panel_y+8 + i*15))