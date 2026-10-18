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


_HUMAN_AI_CYCLE = [InputMode.HUMAN, InputMode.AI]


def _load_ai_policy():
    try:
        from ai.policy import policy
        print("[input] AI policy loaded.")
        return policy
    except Exception as exc:
        print(f"[input] AI policy import failed ({exc}), degraded to NOOP.")
        return lambda state, weights=None: Action.NOOP


class InputHandler:
    def __init__(self, mode: InputMode):
        self._mode = mode
        self._ai_policy = _load_ai_policy()
        self._prev_tab = False

    @property
    def mode(self) -> InputMode:
        return self._mode

    @property
    def mode_name(self) -> str:
        return self._mode.value.upper()

    def poll_events(self, events: list | None = None) -> None:
        events = events or []
        tab_pressed = any(
            e.type == pygame.KEYDOWN and e.key == pygame.K_TAB for e in events
        )
        if tab_pressed and not self._prev_tab:
            self._cycle_mode()
        self._prev_tab = tab_pressed

    def _cycle_mode(self) -> None:
        idx = _HUMAN_AI_CYCLE.index(self._mode) if self._mode in _HUMAN_AI_CYCLE else 0
        self._mode = _HUMAN_AI_CYCLE[(idx + 1) % len(_HUMAN_AI_CYCLE)]

    def get_action(self, state: State | None = None, events: list | None = None) -> Action:
        self.poll_events(events)
        if self._mode == InputMode.HUMAN:
            return self._human_action(events or [])
        if self._mode == InputMode.AI:
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
        except Exception:
            pass
        return Action.NOOP