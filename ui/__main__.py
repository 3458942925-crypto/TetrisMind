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


def _make_font(size: int, bold: bool = False):
    import pygame.font
    _sys = ['Microsoft YaHei', 'Segoe UI', 'Arial']
    try:
        return pygame.font.SysFont(_sys, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


def _setup_pygame(headless: bool, caption: str):
    import pygame
    pygame.init()
    pygame.font.init()
    from ui.render import Renderer, BASE_W, BASE_H
    game_surface = pygame.Surface((BASE_W, BASE_H))
    if headless:
        display = pygame.display.set_mode((1, 1))
    else:
        display = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
    pygame.display.set_caption(caption)
    clock = pygame.time.Clock()
    font = _make_font(18)
    big_font = _make_font(42, bold=True)
    value_font = _make_font(48, bold=True)
    pygame.key.set_repeat(200, 50)
    return pygame, display, clock, font, big_font, value_font, game_surface, Renderer


def _scale_and_blit(display, game_surface, clock):
    import pygame
    win_w, win_h = display.get_size()
    from ui.render import BASE_W, BASE_H
    scale = min(win_w / BASE_W, win_h / BASE_H)
    scale = max(0.1, scale)
    sw = max(1, int(BASE_W * scale))
    sh = max(1, int(BASE_H * scale))
    scaled = pygame.transform.scale(game_surface, (sw, sh))
    display.fill((0, 0, 0))
    display.blit(scaled, ((win_w - sw) // 2, (win_h - sh) // 2))


def _finalize_frame(pygame, display, game_surface, clock):
    _scale_and_blit(display, game_surface, clock)
    pygame.display.flip()


def run_render_mode(headless: bool, frames: int, seed: int) -> int:
    if headless:
        ensure_headless()
    import pygame
    from contracts import Engine
    from ui.render import BASE_W, BASE_H

    pygame, display, clock, font, big_font, value_font, game_surface, Renderer = \
        _setup_pygame(headless, "TetrisMind")

    engine = Engine(seed=seed)
    state = engine.reset()
    renderer = Renderer(game_surface, font, big_font, value_font, clock)
    renderer.set_mode("OBSERVE", "observe", is_replay=False)

    if headless:
        for _ in range(frames):
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.VIDEORESIZE:
                    display = pygame.display.set_mode((1, 1))
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            _finalize_frame(pygame, display, game_surface, clock)
    else:
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    if display.get_flags() & pygame.FULLSCREEN:
                        display = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
                    else:
                        display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                elif event.type == pygame.VIDEORESIZE:
                    display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            pygame.display.set_caption(
                f"TetrisMind | {renderer.mode_label}")
            _finalize_frame(pygame, display, game_surface, clock)

    pygame.quit()
    return 0


def run_input_mode(headless: bool, frames: int, seed: int) -> int:
    if headless:
        ensure_headless()
    import pygame
    from contracts import Engine, Action
    from ui.input import InputHandler, InputMode
    from ui.render import BASE_W, BASE_H

    pygame, display, clock, font, big_font, value_font, game_surface, Renderer = \
        _setup_pygame(headless, "TetrisMind")

    engine = Engine(seed=seed)
    state = engine.reset()
    renderer = Renderer(game_surface, font, big_font, value_font, clock)
    handler = InputHandler(InputMode.HUMAN)
    renderer.set_mode(handler.mode_name, handler.mode.value, is_replay=False)
    prev_key_repr = ""

    if headless:
        for _ in range(frames):
            dt = clock.tick(60) / 1000.0
            events = pygame.event.get()
            action = handler.get_action(state, events)
            renderer.set_mode(handler.mode_name, handler.mode.value, is_replay=False)
            if action != Action.NOOP:
                state = engine.step(action)
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            _finalize_frame(pygame, display, game_surface, clock)
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
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    if display.get_flags() & pygame.FULLSCREEN:
                        display = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
                    else:
                        display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                elif event.type == pygame.VIDEORESIZE:
                    display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            action = handler.get_action(state, events)
            renderer.set_mode(handler.mode_name, handler.mode.value, is_replay=False)
            if action != Action.NOOP:
                state = engine.step(action)
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            pygame.display.set_caption(
                f"TetrisMind | {renderer.mode_label}")
            _finalize_frame(pygame, display, game_surface, clock)

    pygame.quit()
    return 0


def run_replay_mode(headless: bool, frames: int, speed: int, seed: int, replay_file: str | None) -> int:
    if headless:
        ensure_headless()
    import pygame
    from contracts import Engine
    from ui.replay import ReplayPlayer
    from ui.render import BASE_W, BASE_H

    pygame, display, clock, font, big_font, value_font, game_surface, Renderer = \
        _setup_pygame(headless, "TetrisMind")

    engine = Engine(seed=seed)
    player = ReplayPlayer(engine, speed=speed, seed=seed)
    if replay_file:
        player.load_file(replay_file)
    state = player.reset()

    renderer = Renderer(game_surface, font, big_font, value_font, clock)
    renderer.set_mode("REPLAY", "replay", is_replay=True)
    renderer.replay_speed = player.speed

    if headless:
        for _ in range(frames):
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.VIDEORESIZE:
                    display = pygame.display.set_mode((1, 1))
            if not player.finished:
                state = player.step_frame()
            renderer.replay_progress = (player.current_index, player.total_actions)
            renderer.replay_finished = player.finished
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            _finalize_frame(pygame, display, game_surface, clock)
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
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    if display.get_flags() & pygame.FULLSCREEN:
                        display = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
                    else:
                        display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                elif event.type == pygame.VIDEORESIZE:
                    display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    player.toggle_pause()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    state = player.restart()
                    renderer.replay_finished = False
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_1, pygame.K_2, pygame.K_4, pygame.K_8):
                    new_speed = int(pygame.key.name(event.key))
                    player.set_speed(new_speed)
                    renderer.replay_speed = new_speed
            if not player.finished and not player.paused:
                state = player.step_frame()
            renderer.is_paused = player.paused
            renderer.replay_speed = player.speed
            renderer.replay_progress = (player.current_index, player.total_actions)
            renderer.replay_finished = player.finished
            renderer.record_clears(getattr(state, 'cleared_lines', []))
            renderer.update_animations(dt)
            renderer.draw(state)
            pygame.display.set_caption(
                f"TetrisMind | REPLAY x{player.speed}")
            _finalize_frame(pygame, display, game_surface, clock)

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