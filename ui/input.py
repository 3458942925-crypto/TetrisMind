import sys
from enum import Enum
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contracts import Action, State


class InputMode(Enum):
    HUMAN = "human"
    AI = "ai"
    REPLAY = "replay"


KEY_MAP = {
    pygame.K_LEFT: Action.LEFT,
    pygame.K_RIGHT: Action.RIGHT,
    pygame.K_DOWN: Action.DOWN,
    pygame.K_UP: Action.ROTATE,
    pygame.K_x: Action.ROTATE,
    pygame.K_SPACE: Action.HARD_DROP,
    pygame.K_c: Action.HOLD,
    pygame.K_LSHIFT: Action.HOLD,
}


def _load_ai_policy():
    try:
        from ai.policy import policy
        print("[input] AI policy loaded successfully.")
        return policy
    except Exception as exc:
        print(f"[input] AI policy import failed ({exc}), degraded to NOOP.")
        return lambda state, weights=None: Action.NOOP


class InputHandler:
    def __init__(self, mode: InputMode):
        self.mode = mode
        self._ai_policy = _load_ai_policy() if mode == InputMode.AI else None
        self._held_keys: dict[int, bool] = {}

    def get_action(self, state: State | None = None, events: list | None = None) -> Action:
        if self.mode == InputMode.HUMAN:
            return self._human_action(events or [])
        if self.mode == InputMode.AI:
            return self._ai_action(state)
        return Action.NOOP

    def _human_action(self, events: list) -> Action:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in KEY_MAP:
                return KEY_MAP[event.key]
        return Action.NOOP

    def _ai_action(self, state: State | None) -> Action:
        if state is None:
            return Action.NOOP
        try:
            action = self._ai_policy(state)
            if isinstance(action, Action):
                return action
        except Exception as exc:
            print(f"[input] AI policy error: {exc}")
        return Action.NOOP