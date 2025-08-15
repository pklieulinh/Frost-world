import pygame
from core.worldmap import WorldMap

class PopupEvent:
    def __init__(self):
        self.active = False
        self.text = ""
        self.timer = 0

    def show(self, text, duration=120):
        self.text = text
        self.active = True
        self.timer = duration

    def update(self):
        if self.active and self.timer > 0:
            self.timer -= 1
        if self.timer <= 0:
            self.active = False

    def render(self, screen, bigfont):
        if self.active:
            surf = bigfont.render(self.text, True, (180,30,30),(255,255,210))
            rect = surf.get_rect(center=(640,100))
            pygame.draw.rect(screen, (255,255,210), rect, border_radius=8)
            screen.blit(surf, rect.topleft)

class UIManager:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("consolas", 16)
        self.bigfont = pygame.font.SysFont("consolas", 22)
        self.worldmap = WorldMap()
        self.selected_npc_id = None
        self.tooltip = ""
        self.tooltip_visible = False
        self.tooltip_pos = (0,0)
        self.popup = PopupEvent()
        self.build_filter = "all"
        self.build_sort = "priority"
        self.build_history = []

    def show_tooltip(self, text, pos):
        self.tooltip = text
        self.tooltip_visible = True
        self.tooltip_pos = pos

    def hide_tooltip(self):
        self.tooltip_visible = False

    def handle_mouse(self, pos, npcs, heroes, parties, questboard, event_mgr, kingdom, build_queue):
        ox, oy = 900, 60
        mx, my = pos
        self.hide_tooltip()
        # Map hover
        if ox <= mx < ox+self.worldmap.view_w*16 and oy <= my < oy+self.worldmap.view_h*16:
            gx = self.worldmap.view_x + (mx-ox)//16
            gy = self.worldmap.view_y + (my-oy)//16
            tile = self.worldmap.get_tile(gx, gy)
            if tile:
                npclist = [n for n in tile.occupants]
                txt = f"Tile ({gx},{gy}) [{tile.type}]\n"
                if tile.type == "building":
                    txt += f"Công trình: {getattr(tile,'building_name','Chưa rõ')}\n"
                if tile.pending_build:
                    txt += "Đang xây dựng (pending)\n"
                if npclist:
                    for n in npclist:
                        txt += f"- {n.name}: {getattr(n,'state','idle')} ({n.job})\n"
                self.show_tooltip(txt, pos)
                for n in npclist:
                    if pygame.mouse.get_pressed()[0]:
                        self.selected_npc_id = n.id
                        return

    def render_tooltip(self):
        if self.tooltip_visible:
            font = self.font
            lines = self.tooltip.split('\n')
            w = max([font.size(l)[0] for l in lines]+[150]) + 12
            h = len(lines)*20 + 10
            surf = pygame.Surface((w,h), pygame.SRCALPHA)
            pygame.draw.rect(surf, (255,255,220,235), (0,0,w,h), border_radius=8)
            for i,line in enumerate(lines):
                surf.blit(font.render(line,True,(40,40,40)), (6,6+i*20))
            x,y = self.tooltip_pos
            if x+w>1280: x = 1280-w-12
            if y+h>720: y = 720-h-8
            self.screen.blit(surf, (x,y))

    def render_build_queue_panel(self, build_queue):
        bx, by = 10, 600
        pygame.draw.rect(self.screen, (40,40,60), (bx, by, 880, 110), border_radius=12)
        self.screen.blit(self.bigfont.render("Lệnh Xây Dựng", True, (200,220,255)), (bx+8, by+4))
        y = by+28
        # Filter/sort
        shown = build_queue
        if self.build_filter != "all":
            shown = [c for c in build_queue if (c.get("type","house")==self.build_filter)]
        if self.build_sort == "status":
            shown = sorted(shown, key=lambda c: c.get("pending_materials",False))
        elif self.build_sort == "priority":
            shown = shown  # Mặc định: theo thứ tự vào queue
        if not shown:
            self.screen.blit(self.font.render("Không có lệnh xây nào.", True, (180,180,180)), (bx+12, y))
        for i, cmd in enumerate(shown[:6]):
            n = cmd["npc"]
            status = ""
            if getattr(n,"house",None):
                status = "✓ Đã hoàn thành"
            elif cmd.get("progress",0)>0:
                status = f"Đang xây ({cmd['progress']}/120)"
            elif cmd.get("pending_materials",False):
                status = "Chờ vật liệu"
            else:
                status = "Đang di chuyển"
            mat = cmd.get("required_materials",{})
            mat_str = " | ".join(f"{k}:{v}" for k,v in mat.items())
            msg = f"{n.name} → ({cmd['x']},{cmd['y']}) | {status} | VL:{mat_str}"
            self.screen.blit(self.font.render(msg, True, (255,255,200)), (bx+8, y))
            # Progress bar
            if status.startswith("Đang xây"):
                prog = min(1.0, cmd['progress']/120)
                pygame.draw.rect(self.screen, (60,180,60), (bx+700, y+4, int(120*prog), 10), border_radius=6)
                pygame.draw.rect(self.screen, (80,80,80), (bx+700, y+4, 120, 10), 1, border_radius=6)
            y += 22
        # Lịch sử xây dựng
        self.screen.blit(self.font.render("Lịch sử xây:", True, (160,210,255)), (bx+400, by+4))
        for j, log in enumerate(self.build_history[-5:]):
            self.screen.blit(self.font.render(log, True, (180,255,180)), (bx+400, by+28+j*18))

    def render(self, state, parties, questboard, event_mgr, jobs, build_queue):
        self.worldmap.draw(self.screen, 900, 60, state.npcs, state, build_queue)
        self.render_build_queue_panel(build_queue)
        self.render_tooltip()
        self.popup.render(self.screen, self.bigfont)