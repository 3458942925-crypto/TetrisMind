import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HEADLESS_ENV_SET = False


def ensure_headless():
    global HEADLESS_ENV_SET
    if not HEADLESS_ENV_SET:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        HEADLESS_ENV_SET = True


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m ui", description="TetrisMind P2 UI")
    p.add_argument("--mode", default="render", choices=["render", "input", "replay", "all"])
    p.add_argument("--headless", action="store_true")
    p.add_argument("--frames", type=int, default=60)
    p.add_argument("--speed", type=int, default=1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--replay-file", type=str, default=None)
    return p


def _setup_pygame(headless: bool, caption: str):
    import pygame
    pygame.init()
    from ui.render import Renderer, WIN_W, WIN_H
    display = pygame.display.set_mode((WIN_W, WIN_H)) if not headless else pygame.display.set_mode((1, 1))
    pygame.display.set_caption(caption)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 18)
    return pygame, display, clock, font, Renderer


def run_render_mode(headless: bool, frames: int, seed: int) -> int:
    if headless:
        ensure_headless()
    import pygame
    from contracts import Engine

    pygame, display, clock, font, Renderer = _setup_pygame(headless, "TetrisMind - Render")

    engine = Engine(seed=seed)
    state = engine.reset()
    renderer = Renderer(display, font)

    if headless:
        for _ in range(frames):
            dt = clock.tick(60) / 1000.0
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            pygame.display.flip()
    else:
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            pygame.display.flip()

    pygame.quit()
    return 0


def run_input_mode(headless: bool, frames: int, seed: int) -> int:
    if headless:
        ensure_headless()
    import pygame
    from contracts import Engine, Action
    from ui.input import InputHandler, InputMode

    pygame, display, clock, font, Renderer = _setup_pygame(headless, "TetrisMind - Input")

    engine = Engine(seed=seed)
    state = engine.reset()
    renderer = Renderer(display, font)
    handler = InputHandler(InputMode.HUMAN)
    last_action_label: str = "NOOP"

    def _draw_hud():
        label = font.render(f"ACTION: {last_action_label}", True, (255, 255, 100))
        display.blit(label, (20, 20))

    if headless:
        for _ in range(frames):
            dt = clock.tick(60) / 1000.0
            events = pygame.event.get()
            action = handler.get_action(state, events)
            if action != Action.NOOP:
                print(f">>> Action Triggered: {action.name}")
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            pygame.display.flip()
    else:
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            action = handler.get_action(state, events)
            if action != Action.NOOP:
                last_action_label = action.name
                print(f">>> Action Triggered: {action.name}")
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            _draw_hud()
            pygame.display.flip()

    pygame.quit()
    return 0


def run_replay_mode(headless: bool, frames: int, speed: int, seed: int, replay_file: str | None) -> int:
    if headless:
        ensure_headless()
    import pygame
    from contracts import Engine
    from ui.replay import ReplayPlayer

    pygame, display, clock, font, Renderer = _setup_pygame(headless, f"TetrisMind - Replay x{speed}")

    engine = Engine(seed=seed)
    player = ReplayPlayer(engine, speed=speed, seed=seed)
    if replay_file:
        player.load_file(replay_file)
    state = player.reset()
    renderer = Renderer(display, font)

    if headless:
        for _ in range(frames):
            dt = clock.tick(60) / 1000.0
            if not player.finished:
                state = player.step_frame()
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            pygame.display.flip()
    else:
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            if not player.finished:
                state = player.step_frame()
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            pygame.display.flip()

    pygame.quit()
    return 0


def run_all(headless: bool, frames: int, seed: int) -> int:
    ret = 0
    ret |= run_render_mode(headless, frames, seed)
    ret |= run_input_mode(headless, frames, seed)
    ret |= run_replay_mode(headless, frames, speed=1, seed=seed, replay_file=None)
    return ret


def main() -> int:
    args = build_parser().parse_args()
    if args.mode == "render":
        return run_render_mode(args.headless, args.frames, args.seed)
    if args.mode == "input":
        return run_input_mode(args.headless, args.frames, args.seed)
    if args.mode == "replay":
        return run_replay_mode(args.headless, args.frames, args.speed, args.seed, args.replay_file)
    if args.mode == "all":
        return run_all(args.headless, args.frames, args.seed)
    return 1


if __name__ == "__main__":
    sys.exit(main())