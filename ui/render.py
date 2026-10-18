import sys
from pathlib import Path

from contracts import Action, State

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame

BASE_W = 600
BASE_H = 800


def _sf(families: list[str], size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont(families, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)

CELL = 30
COLS = 10
ROWS = 20
HUD_LEFT_W = 130
SIDEBAR_W = 170
TOP_BAR_H = 70
MARGIN = 16
PANEL_GAP = 8

COLOR_BG = (20, 24, 34)
COLOR_BOARD_BG = (10, 10, 15)
COLOR_GRID = (40, 45, 60)
COLOR_PANEL = (30, 35, 48)
COLOR_PANEL_SHADOW = (8, 10, 18)
COLOR_PANEL_BORDER = (80, 90, 120)
COLOR_BOARD_BORDER = (0, 255, 255)
COLOR_TEXT = (220, 225, 240)
COLOR_TEXT_DIM = (100, 100, 110)
COLOR_ACCENT = (255, 230, 0)
COLOR_ACCENT2 = (0, 255, 255)
COLOR_VALUE = (255, 255, 255)
COLOR_NEON_INNER = (255, 255, 255)

PIECE_COLORS = {
    0: (15, 15, 22),
    1: (0, 240, 255),
    2: (80, 120, 255),
    3: (255, 220, 40),
    4: (255, 60, 80),
    5: (60, 240, 120),
    6: (200, 100, 255),
    7: (255, 160, 40),
}

HUD_LEFT_X = MARGIN
HUD_LEFT_Y = TOP_BAR_H + MARGIN
HUD_LEFT_H = ROWS * CELL
BOARD_X = HUD_LEFT_X + HUD_LEFT_W + PANEL_GAP
BOARD_Y = TOP_BAR_H + MARGIN
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
SIDEBAR_X = BOARD_X + BOARD_W + PANEL_GAP
SIDEBAR_Y = TOP_BAR_H + MARGIN
SIDEBAR_H = BOARD_H

CLEAR_SCORE_TABLE = [0, 100, 300, 500, 800]


class LineClearAnimation:
    def __init__(self, row_indices: list[int], duration: float = 0.3):
        self.rows = list(row_indices)
        self.duration = duration
        self.elapsed = 0.0

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        return self.elapsed < self.duration

    @property
    def phase(self) -> int:
        if self.elapsed < 0.12:
            return 0
        if self.elapsed < 0.22:
            return 1
        return 2

    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 1.0
        return min(1.0, self.elapsed / self.duration)

    @property
    def flash_visible(self) -> bool:
        if self.phase != 0:
            return False
        cycle = int(self.elapsed * 20) % 2
        return cycle == 0


class FloatTextAnimation:
    def __init__(self, text: str, center: tuple[int, int], duration: float = 1.0):
        self.text = text
        self.center_x = float(center[0])
        self.center_y = float(center[1])
        self.duration = duration
        self.elapsed = 0.0

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        return self.elapsed < self.duration

    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 1.0
        return min(1.0, self.elapsed / self.duration)

    @property
    def alpha(self) -> int:
        return int(255 * (1.0 - self.progress))

    @property
    def current_y(self) -> float:
        return self.center_y - 80.0 * self.progress


class Renderer:
    def __init__(self, surface: pygame.Surface,
                 font: pygame.font.Font | None = None,
                 big_font: pygame.font.Font | None = None,
                 value_font: pygame.font.Font | None = None,
                 clock: pygame.time.Clock | None = None):
        self.surface = surface
        _sys = ['Microsoft YaHei', 'Segoe UI', 'Arial']
        self.font = font or _sf(_sys, 18)
        self.big_font = big_font or _sf(_sys, 42, bold=True)
        self.value_font = value_font or _sf(_sys, 48, bold=True)
        self.mode_font = _sf(_sys, 52, bold=True)
        self.clock = clock
        self.mode_label: str = "HUMAN"
        self.mode_name_full: str = "human"
        self.replay_speed: int = 1
        self.replay_progress: tuple[int, int] = (0, 0)
        self.is_replay: bool = False
        self.is_paused: bool = False
        self.replay_finished: bool = False
        self._prev_mode: str | None = None
        self._mode_transition: float = 0.0
        self.line_animations: list[LineClearAnimation] = []
        self.float_texts: list[FloatTextAnimation] = []

    def set_mode(self, label: str, name_full: str, is_replay: bool = False) -> None:
        if self.mode_label != label:
            self._prev_mode = self.mode_label
            self.mode_label = label
            self.mode_name_full = name_full
            self._mode_transition = 0.0
        self.is_replay = is_replay

    def record_clears(self, cleared_rows: list[int]) -> None:
        if cleared_rows:
            n = len(cleared_rows)
            score = CLEAR_SCORE_TABLE[min(n, 4)]
            self.line_animations.append(LineClearAnimation(cleared_rows))
            cx = BOARD_X + BOARD_W // 2
            cy = BOARD_Y + BOARD_H // 2
            self.float_texts.append(FloatTextAnimation(f"+{score}", (cx, cy)))

    def update_animations(self, dt: float) -> None:
        self.line_animations = [a for a in self.line_animations if a.update(dt)]
        self.float_texts = [t for t in self.float_texts if t.update(dt)]
        if self._mode_transition < 0.2:
            self._mode_transition = min(0.2, self._mode_transition + dt)

    def draw(self, state: State) -> None:
        self.surface.fill(COLOR_BG)
        self._draw_top_bar()
        self._draw_hud_left(state)
        self._draw_board(state)
        self._draw_sidebar(state)
        self._draw_line_animations()
        self._draw_float_texts()
        self._draw_overlay_texts()

    def _draw_top_bar(self) -> None:
        fps = int(self.clock.get_fps()) if self.clock else 0
        fps_surf = self.font.render(f"FPS {fps}", True, COLOR_TEXT_DIM)
        self.surface.blit(fps_surf, (MARGIN, MARGIN))

        mode_alpha = 255
        if self._mode_transition < 0.2 and self._prev_mode is not None:
            mode_alpha = int(255 * (self._mode_transition / 0.2))
        mode_surf = self.mode_font.render(f"MODE: {self.mode_label}", True, COLOR_ACCENT)
        if mode_alpha < 255:
            mode_surf.set_alpha(mode_alpha)
        self.surface.blit(mode_surf, (MARGIN, MARGIN + 18))

        if self.is_replay:
            prog = self.replay_progress
            info = self.font.render(
                f"SPEED {self.replay_speed}x   {prog[0]}/{prog[1]}", True, COLOR_ACCENT2)
            self.surface.blit(info, (BASE_W - info.get_width() - MARGIN, MARGIN + 28))

    def _draw_panel_with_shadow(self, rect: pygame.Rect, radius: int = 12) -> None:
        shadow = rect.copy()
        shadow.x += 4
        shadow.y += 6
        shadow_surf = pygame.Surface((shadow.w, shadow.h), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 90))
        self.surface.blit(shadow_surf, shadow.topleft)
        pygame.draw.rect(self.surface, COLOR_PANEL, rect, border_radius=radius)
        pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, rect, 1, border_radius=radius)
        inner = rect.inflate(-3, -3)
        pygame.draw.rect(self.surface, (50, 56, 74), inner, 1, border_radius=radius - 2)

    def _draw_hud_left(self, state: State) -> None:
        panel = pygame.Rect(HUD_LEFT_X, HUD_LEFT_Y, HUD_LEFT_W, HUD_LEFT_H)
        self._draw_panel_with_shadow(panel, radius=12)

        score = int(getattr(state, 'score', 0) or 0)
        level = int(getattr(state, 'level', 0) or 0)
        lines = int(getattr(state, 'total_lines', 0) or 0)

        y = HUD_LEFT_Y + 18
        for label, val in [("SCORE", score), ("LEVEL", level), ("LINES", lines)]:
            title = self.font.render(label, True, COLOR_TEXT_DIM)
            self.surface.blit(title, (HUD_LEFT_X + 12, y))
            val_surf = self.value_font.render(f"{val}", True, COLOR_VALUE)
            self.surface.blit(val_surf, (HUD_LEFT_X + 12, y + 18))
            y += 74

        human_mode = self.mode_label == "HUMAN"
        interactive = human_mode
        legend_alpha = 255 if interactive else 90
        legend_color = COLOR_TEXT_DIM

        header = self.font.render("CONTROLS", True, legend_color)
        header.set_alpha(legend_alpha)
        self.surface.blit(header, (HUD_LEFT_X + 12, HUD_LEFT_H - 128))

        if self.is_replay:
            hints = ["P       pause", "R       restart", "1/2/4/8 speed"]
            yy = HUD_LEFT_H - 108
        elif interactive:
            hints = ["LEFT/RIGHT move", "UP/X      rotate", "SPACE     hard",
                     "C/SHIFT   hold", "TAB       AI/HU", "ESC       quit"]
            yy = HUD_LEFT_H - 108
        else:
            hints = ["LEFT/RIGHT move", "UP/X      rotate", "SPACE     hard",
                     "C/SHIFT   hold", "TAB       AI/HU", "ESC       quit"]
            yy = HUD_LEFT_H - 108

        for line in hints:
            surf = self.font.render(line, True, legend_color)
            surf.set_alpha(legend_alpha)
            self.surface.blit(surf, (HUD_LEFT_X + 12, yy))
            yy += 18

        if not interactive and not self.is_replay:
            note = self.font.render("(KEYS DISABLED)", True, (80, 80, 95))
            note.set_alpha(130)
            self.surface.blit(note, (HUD_LEFT_X + 12, HUD_LEFT_H - 16))

    def _draw_board(self, state: State) -> None:
        board_bg = pygame.Rect(BOARD_X, BOARD_Y, BOARD_W, BOARD_H)
        pygame.draw.rect(self.surface, COLOR_BOARD_BG, board_bg)

        for c in range(COLS + 1):
            x = BOARD_X + c * CELL
            pygame.draw.line(self.surface, COLOR_GRID, (x, BOARD_Y), (x, BOARD_Y + BOARD_H), 1)
        for r in range(ROWS + 1):
            y = BOARD_Y + r * CELL
            pygame.draw.line(self.surface, COLOR_GRID, (BOARD_X, y), (BOARD_X + BOARD_W, y), 1)

        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(BOARD_X + c * CELL + 1, BOARD_Y + r * CELL + 1, CELL - 2, CELL - 2)
                cell_val = state.board[r][c] if r < len(state.board) and c < len(state.board[r]) else 0
                if cell_val:
                    self._draw_block(rect, PIECE_COLORS.get(cell_val, (200, 200, 200)))

        pygame.draw.rect(self.surface, COLOR_BOARD_BORDER, board_bg, 3)

    def _draw_block(self, rect: pygame.Rect, base_color: tuple[int, int, int]) -> None:
        fill = rect.inflate(-2, -2)
        pygame.draw.rect(self.surface, base_color, fill)

        inner_glow = fill.inflate(-2, -2)
        if inner_glow.w > 0 and inner_glow.h > 0:
            glow_surf = pygame.Surface((inner_glow.w, inner_glow.h), pygame.SRCALPHA)
            glow_surf.fill((255, 255, 255, 55))
            self.surface.blit(glow_surf, inner_glow.topleft)
        pygame.draw.rect(self.surface, (255, 255, 255), fill, 1)

        hl_rect = pygame.Rect(rect.x + 3, rect.y + 3, max(2, rect.w // 5), max(2, rect.h // 7))
        hl = pygame.Surface((hl_rect.w, hl_rect.h), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 165))
        self.surface.blit(hl, hl_rect.topleft)

        sh_rect = pygame.Rect(rect.right - rect.w // 5 - 3, rect.bottom - rect.h // 7 - 3,
                              max(2, rect.w // 5), max(2, rect.h // 7))
        sh = pygame.Surface((sh_rect.w, sh_rect.h), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 130))
        self.surface.blit(sh, sh_rect.topleft)

    def _draw_sidebar(self, state: State) -> None:
        panel = pygame.Rect(SIDEBAR_X, SIDEBAR_Y, SIDEBAR_W, SIDEBAR_H)
        self._draw_panel_with_shadow(panel, radius=12)

        title = self.font.render("HOLD", True, COLOR_TEXT_DIM)
        self.surface.blit(title, (SIDEBAR_X + 12, SIDEBAR_Y + 10))
        hold_rect = pygame.Rect(SIDEBAR_X + 12, SIDEBAR_Y + 34, 80, 70)
        pygame.draw.rect(self.surface, COLOR_BOARD_BG, hold_rect, border_radius=8)
        pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, hold_rect, 1, border_radius=8)
        hold_val = getattr(state, 'hold_piece', None)
        if hold_val is not None and hold_val != 0:
            self._draw_block(hold_rect.inflate(-4, -4), PIECE_COLORS.get(hold_val, (200, 200, 200)))
        elif hold_val == 0:
            hint = self.font.render("empty", True, (70, 70, 85))
            hint.set_alpha(120)
            self.surface.blit(hint, hint.get_rect(center=hold_rect.center))

        title2 = self.font.render("NEXT", True, COLOR_TEXT_DIM)
        self.surface.blit(title2, (SIDEBAR_X + 12, SIDEBAR_Y + 124))
        queue = getattr(state, 'next_queue', []) or []
        for i in range(5):
            slot_rect = pygame.Rect(SIDEBAR_X + 12, SIDEBAR_Y + 148 + i * 36, 60, 30)
            pygame.draw.rect(self.surface, (16, 18, 26), slot_rect, border_radius=5)
            pygame.draw.rect(self.surface, (55, 62, 78), slot_rect, 1, border_radius=5)
            piece = queue[i] if i < len(queue) else 0
            if piece:
                self._draw_block(slot_rect.inflate(-4, -4), PIECE_COLORS.get(piece, (200, 200, 200)))

    def _draw_line_animations(self) -> None:
        for anim in self.line_animations:
            t = anim.progress
            for row in anim.rows:
                base_rect = pygame.Rect(BOARD_X + 1, BOARD_Y + row * CELL + 1, BOARD_W - 2, CELL - 2)
                if anim.phase == 0:
                    if anim.flash_visible:
                        flash = pygame.Surface((base_rect.w, base_rect.h), pygame.SRCALPHA)
                        flash.fill((255, 255, 255, 210))
                        self.surface.blit(flash, base_rect.topleft)
                elif anim.phase == 1:
                    fade_t = (t - 0.12) / 0.10 if t > 0.12 else 0
                    shrink = int(BOARD_W * fade_t)
                    new_w = max(1, BOARD_W - 2 - shrink)
                    new_x = BOARD_X + 1 + shrink // 2
                    rect = pygame.Rect(new_x, BOARD_Y + row * CELL + 1, new_w, CELL - 2)
                    flash = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                    flash.fill((255, 255, 255, 180))
                    self.surface.blit(flash, rect.topleft)
                else:
                    fade_t = (t - 0.22) / 0.08 if t > 0.22 else 0
                    shrink = int(BOARD_W)
                    new_w = max(1, BOARD_W - 2 - shrink)
                    new_x = BOARD_X + 1 + shrink // 2
                    rect = pygame.Rect(new_x, BOARD_Y + row * CELL + 1, new_w, CELL - 2)
                    alpha = int(180 * (1 - fade_t))
                    flash = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                    flash.fill((255, 255, 255, alpha))
                    self.surface.blit(flash, rect.topleft)

    def _draw_float_texts(self) -> None:
        for ft in self.float_texts:
            alpha = ft.alpha
            surf = self.big_font.render(ft.text, True, COLOR_ACCENT)
            surf.set_alpha(alpha)
            rect = surf.get_rect(center=(int(ft.center_x), int(ft.current_y)))
            self.surface.blit(surf, rect.topleft)

    def _draw_overlay_texts(self) -> None:
        center = pygame.Rect(0, 0, BASE_W, BASE_H).center
        _sys = ['Microsoft YaHei', 'Segoe UI', 'Arial']
        big_font = _sf(_sys, 72, bold=True)

        if self.is_paused:
            big = big_font.render("PAUSED", True, COLOR_ACCENT)
            sub = self.font.render("Press P to resume", True, COLOR_TEXT_DIM)
            self.surface.blit(big, big.get_rect(center=(center[0], center[1] - 20)))
            self.surface.blit(sub, sub.get_rect(center=(center[0], center[1] + 30)))

        if self.replay_finished and self.is_replay:
            big = _sf(_sys, 54, bold=True).render("REPLAY FINISHED", True, COLOR_ACCENT2)
            sub = self.font.render("Press R to restart", True, COLOR_TEXT_DIM)
            self.surface.blit(big, big.get_rect(center=(center[0], center[1] + 80)))
            self.surface.blit(sub, sub.get_rect(center=(center[0], center[1] + 120)))