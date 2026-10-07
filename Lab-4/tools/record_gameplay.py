"""Headless gameplay recorder for the Marble Tilt Maze lab.

Runs the game's own loop (handle_event -> handle_input -> update -> render)
with a simulated clock and a scripted mouse, pipes every frame to ffmpeg,
and (if the game has a SoundBank) mixes the sound effects it plays into the
video's audio track.

usage: python record.py <code_dir> <scenario: before|after> <out.mp4>
"""
import io
import math
import os
import subprocess
import sys
import wave
import array
import contextlib

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

code_dir, scenario, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, code_dir)

import pygame  # noqa: E402

FPS = 60
SIM = {"frame": 0}
MOUSE = [300, 250]

pygame.time.get_ticks = lambda: int(SIM["frame"] * 1000 / FPS)
pygame.mouse.get_pos = lambda: (int(MOUSE[0]), int(MOUSE[1]))

console = io.StringIO()
with contextlib.redirect_stdout(console):
    import main as game_main  # creates window + engine (uses patched clock)

engine = game_main.engine
screen = game_main.SCREEN
W, H = screen.get_size()
BAR = 70
canvas = pygame.Surface((W, H + BAR))
small = pygame.font.SysFont("dejavusansmono,monospace", 15)
label_font = pygame.font.SysFont("dejavusans,arial", 16, bold=True)

# ---------- sound logging -------------------------------------------------
sound_log = []  # (frame, name, volume)
bank = getattr(engine, "sounds", None)
if bank is not None:
    real_play = bank.play

    def logged_play(name, volume=1.0):
        sound_log.append((SIM["frame"], name, volume))
        return real_play(name, volume)

    bank.play = logged_play

# ---------- phantom-bounce detector (annotation only) ---------------------
phantoms = []  # (frame, x, y)


def circle_touches(rect, cx, cy, r):
    nx = min(max(cx, rect.left), rect.right)
    ny = min(max(cy, rect.top), rect.bottom)
    return (cx - nx) ** 2 + (cy - ny) ** 2 < r * r


real_resolve = engine._resolve_wall_collisions


def watched_resolve():
    m = engine.marble
    x0, y0, vx0, vy0 = m.x, m.y, m.vx, m.vy
    touching = any(circle_touches(w.rect(), x0, y0, m.radius) for w in engine.walls)
    out = real_resolve()
    bounced = (m.vx != vx0) or (m.vy != vy0) or (m.x != x0) or (m.y != y0)
    if bounced and not touching:
        phantoms.append((SIM["frame"], x0, y0))
    return out


engine._resolve_wall_collisions = watched_resolve

# ---------- autopilot -----------------------------------------------------
import json
PATH = json.loads(os.environ.get("MAZE_PATH", "null")) or [(522, 78), (522, 208), (78, 208), (78, 328), (522, 328), (522, 440), (540, 440)]
wp = {"i": 0}


def autopilot():
    m = engine.marble
    i = min(wp["i"], len(PATH) - 1)
    tx, ty = PATH[i]
    dx, dy = tx - m.x, ty - m.y
    d = math.hypot(dx, dy)
    if d < 28 and wp["i"] < len(PATH) - 1:
        wp["i"] += 1
    vmax = getattr(engine, "max_speed", 9)
    want = min(vmax, 0.09 * d + 1.0)
    dvx = (dx / max(d, 1e-6)) * want - m.vx
    dvy = (dy / max(d, 1e-6)) * want - m.vy
    n = math.hypot(dvx, dvy) or 1
    goal_mx = W / 2 + dvx / n * 160
    goal_my = H / 2 + dvy / n * 160
    # move the "hand" smoothly like a real mouse
    MOUSE[0] += (goal_mx - MOUSE[0]) * 0.35
    MOUSE[1] += (goal_my - MOUSE[1]) * 0.35


def move_mouse_to(x, y, k=0.18):
    MOUSE[0] += (x - MOUSE[0]) * k
    MOUSE[1] += (y - MOUSE[1]) * k


def key(k, uni=""):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode=uni, scancode=0))


def click(x, y):
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(int(x), int(y)), button=1))


# ---------- scenario scripts ----------------------------------------------
TOTAL = 600
state = {"phase": "play", "t0": 0, "menu_target": None}


def script_before(f):
    autopilot()


def find_button(label_start):
    for b in getattr(engine, "buttons", lambda: [])():
        if b[0].lower().startswith(label_start):
            return b[1]
    return None


def script_after(f):
    ph = state["phase"]
    st = getattr(engine, "state", None)
    if ph == "play":
        autopilot()
        if st == "game_over":
            state.update(phase="end", t0=f)
    elif ph == "end":
        move_mouse_to(W / 2, H / 2 + 120, 0.05)
        if f - state["t0"] == 90:
            key(pygame.K_RETURN, "\r")
        if st == "menu":
            state.update(phase="menu", t0=f)
    elif ph == "menu":
        r = find_button("hard")
        if r is not None:
            move_mouse_to(r.centerx, r.centery)
            if f - state["t0"] == 55:
                click(r.centerx, r.centery)
        if st == "playing":
            wp["i"] = 0
            state.update(phase="replay", t0=f)
    elif ph == "replay":
        autopilot()


def script_timeout(f):
    if f == 0:
        engine.start_round("Hard")
        engine.start_ticks -= 18000  # begin with 7 s left on the clock
    ang = f / 30.0
    move_mouse_to(W / 2 + 170 * math.cos(ang), H / 2 + 150 * math.sin(ang * 1.3), 0.3)


script = {"before": script_before, "after": script_after, "timeout": script_timeout}[scenario]
caption = {"before": "BEFORE  -  original code",
           "after": "AFTER  -  Tasks 1-4 implemented",
           "timeout": "AFTER  -  timeout (Hard round, clip starts 7s before the end)"}[scenario]

# ---------- render + capture ----------------------------------------------
ff = subprocess.Popen(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
     "-s", f"{W}x{H + BAR}", "-r", str(FPS), "-i", "-",
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", out_path + ".noaudio.mp4"],
    stdin=subprocess.PIPE)


def draw_cursor(surf, x, y):
    pts = [(x, y), (x, y + 17), (x + 4, y + 13), (x + 8, y + 20), (x + 11, y + 19), (x + 7, y + 12), (x + 13, y + 12)]
    pygame.draw.polygon(surf, (255, 255, 255), pts)
    pygame.draw.polygon(surf, (0, 0, 0), pts, 1)


for f in range(TOTAL):
    SIM["frame"] = f
    script(f)
    with contextlib.redirect_stdout(console):
        for event in pygame.event.get():
            engine.handle_event(event)
        engine.handle_input()
        engine.update()
        engine.render(screen)

    canvas.fill((18, 18, 22))
    canvas.blit(screen, (0, 0))
    # annotate phantom bounces (recorder overlay, not part of the game)
    for (pf, px, py) in phantoms:
        age = f - pf
        if 0 <= age < 45:
            pygame.draw.circle(canvas, (255, 70, 70), (int(px), int(py)), 22, 3)
            t = small.render("phantom bounce!", True, (255, 90, 90))
            canvas.blit(t, (int(px) - t.get_width() // 2, int(py) + 24))
    draw_cursor(canvas, int(MOUSE[0]), int(MOUSE[1]))
    pygame.draw.line(canvas, (70, 70, 80), (0, H), (W, H))
    canvas.blit(label_font.render(caption, True, (230, 230, 120)), (10, H + 6))
    canvas.blit(small.render(f"t={f / FPS:4.1f}s", True, (150, 150, 160)), (W - 80, H + 8))
    lines = [ln for ln in console.getvalue().splitlines() if ln.strip() and "pygame" not in ln.lower()]
    canvas.blit(small.render("console> " + (lines[-1] if lines else ""), True, (140, 220, 140)), (10, H + 32))
    if scenario == "before":
        canvas.blit(small.render(f"phantom bounces so far: {len(phantoms)}", True, (255, 120, 120)), (330, H + 32))
    else:
        canvas.blit(small.render(f"phantom bounces so far: {len(phantoms)}", True, (120, 220, 140)), (330, H + 32))
    ff.stdin.write(pygame.image.tostring(canvas, "RGB"))

ff.stdin.close()
ff.wait()

# ---------- audio track ---------------------------------------------------
RATE = getattr(bank, "rate", 44100)
n_samples = int(TOTAL / FPS * RATE)
mix = [0.0] * n_samples
if bank is not None:
    for (fr, name, vol) in sound_log:
        samp = bank.samples.get(name, [])
        start = int(fr / FPS * RATE)
        for i, s in enumerate(samp):
            j = start + i
            if j >= n_samples:
                break
            mix[j] += s * vol
pcm = array.array("h", (int(max(-1.0, min(1.0, s)) * 30000) for s in mix))
wav_path = out_path + ".wav"
with wave.open(wav_path, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(pcm.tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out_path + ".noaudio.mp4", "-i", wav_path,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", out_path], check=True)
os.remove(out_path + ".noaudio.mp4")
os.remove(wav_path)

print("frames:", TOTAL, "phantoms:", len(phantoms), "sounds:", len(sound_log),
      "state:", getattr(engine, "state", None), "result:", engine.result, file=sys.stderr)
print("console:", [ln for ln in console.getvalue().splitlines() if ln.strip()][-3:], file=sys.stderr)
