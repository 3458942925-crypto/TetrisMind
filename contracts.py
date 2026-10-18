from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple, Optional


class Action(Enum):
    LEFT = auto()
    RIGHT = auto()
    DOWN = auto()
    ROTATE = auto()
    HARD_DROP = auto()
    HOLD = auto()
    NOOP = auto()


@dataclass
class State:
    board: List[List[int]]
    current_piece: Tuple[int, int]
    hold_piece: Optional[int]
    next_queue: List[int]
    cleared_lines: List[int]


class Engine:
    def __init__(self, seed: int = 0):
        self.seed = seed

    def reset(self) -> State:
        return State(
            board=[[0] * 10 for _ in range(20)],
            current_piece=(3, 0),
            hold_piece=1,
            next_queue=[2, 3, 4],
            cleared_lines=[]
        )

    def step(self, action: Action) -> State:
        return self.reset()