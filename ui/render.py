import sys
from pathlib import Path

from contracts import Action, State

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame

CELL = 30
COLS = 10
ROWS = 20
SIDEBAR_W = 180
MARGIN = 20

COLOR_BG = (20, 20, 28)
COLOR_GRID = (40, 40, 52)
COLOR_EMPTY = (0, 0, 0)
COLOR_BORDER = (120, 120, 140)
COLOR_TEXT = (230, 230, 240)
COLOR_CLEAR = (255, 255, 255)
COLOR_CLEAR_BG = (200, 240, 255)

PIECE_COLORS = {
    0: (30, 30, 38),
    1: (80, 200, 220),
    2: (80, 120, 220),
    3: (220, 200, 80),
    4: (220, 80, 80),
    5: (120, 220, 120),
    6: (180, 120, 220),
    7: (220, 140, 60),
}

BOARD_X = MARGIN
BOARD_Y = MARGIN
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
SIDEBAR_X = BOARD_X + BOARD_W + MARGIN
SIDEBAR_Y = MARGIN
SIDEBAR_H = BOARD_H
WIN_W = SIDEBAR_X + SIDEBAR_W + MARGIN
WIN_H = BOARD_H + 2 * MARGIN


class LineClearAnimation:
    def __init__(self, row_indices: list[int], duration: float = 0.3):
        self.rows = list(row_indices)
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


class Renderer:
    def __init__(self, surface: pygame.Surface, font: pygame.font.Font | None = None):
        self.surface = surface
        self.font = font or pygame.font.Font(None, 18)
        self.line_animations: list[LineClearAnimation] = []

    def record_clears(self, cleared_rows: list[int]) -> None:
        if cleared_rows:
            self.line_animations.append(LineClearAnimation(cleared_rows))

    def update_animations(self, dt: float) -> None:
        self.line_animations = [a for a in self.line_animations if a.update(dt)]

    def draw(self, state: State) -> None:
        self.surface.fill(COLOR_BG)
        self._draw_board(state)
        self._draw_sidebar(state)
        self._draw_line_animations()

    def _draw_board(self, state: State) -> None:
        board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_W, BOARD_H)
        pygame.draw.rect(self.surface, COLOR_BORDER, board_rect, 2)
        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(BOARD_X + c * CELL, BOARD_Y + r * CELL, CELL, CELL)
                cell_val = state.board[r][c] if r < len(state.board) and c < len(state.board[r]) else 0
                color = PIECE_COLORS.get(cell_val, COLOR_EMPTY) if cell_val else COLOR_GRID
                pygame.draw.rect(self.surface, color, rect)
                pygame.draw.rect(self.surface, (50, 50, 62), rect, 1)

    def _draw_sidebar(self, state: State) -> None:
        title = self.font.render("HOLD", True, COLOR_TEXT)
        self.surface.blit(title, (SIDEBAR_X, SIDEBAR_Y))
        hold_val = getattr(state, 'hold_piece', None)
        hold_rect = pygame.Rect(SIDEBAR_X, SIDEBAR_Y + 30, 60, 60)
        pygame.draw.rect(self.surface, COLOR_BORDER, hold_rect, 1)
        if hold_val is not None and hold_val != 0:
            pygame.draw.rect(self.surface, PIECE_COLORS.get(hold_val, COLOR_EMPTY), hold_rect.inflate(-4, -4))

        next_title = self.font.render("NEXT", True, COLOR_TEXT)
        self.surface.blit(next_title, (SIDEBAR_X, SIDEBAR_Y + 120))
        queue = getattr(state, 'next_queue', []) or []
        for i, piece in enumerate(queue[:5]):
            rect = pygame.Rect(SIDEBAR_X, SIDEBAR_Y + 150 + i * 40, 40, 30)
            pygame.draw.rect(self.surface, COLOR_BORDER, rect, 1)
            if piece:
                pygame.draw.rect(self.surface, PIECE_COLORS.get(piece, COLOR_EMPTY), rect.inflate(-3, -3))

    def _draw_line_animations(self) -> None:
        for anim in self.line_animations:
            t = anim.progress
            alpha = int(255 * (1 - t))
            for row in anim.rows:
                rect = pygame.Rect(BOARD_X, BOARD_Y + row * CELL, BOARD_W, CELL)
                flash_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, alpha))
                self.surface.blit(flash_surf, rect.topleft)