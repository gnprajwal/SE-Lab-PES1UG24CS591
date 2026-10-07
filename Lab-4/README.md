# Lab 4 — VibeCoding: Marble Tilt Maze

Assigned repo: SETAPESU26 / 42_marble-tilt-maze · AI tool: Claude (claude.ai)

| Deliverable | Where |
|---|---|
| Video before changes (10 s) | `videos/before.mp4` |
| Video after changes (10 s) | `videos/after.mp4` (+ `videos/after_timeout.mp4` for the time-out screen/sound) |
| Updated code | `code/` |
| Chat history | `chat_history.pdf` |

## Run

```bash
cd code
pip install -r requirements.txt
python main.py
```

Move the mouse away from the window centre to tilt the maze. **M** mutes sound.

## What changed (one commit per task)

1. **Collision detection** — circle-vs-rectangle test (closest point on the wall) replaces the
   square bounding-box check, so there are no more phantom bounces next to wall corners.
2. **Game over screen** — "Maze Solved!" with finish time or "Time's Up!", waits for
   ENTER/click (continue) or ESC (quit). Timer now freezes at the end of the round.
3. **Replay with difficulty** — "Play again?" menu: Easy (60 s), Medium (45 s, original tuning),
   Hard (25 s); each sets tilt strength, friction and top speed. Click, 1/2/3, or arrows + ENTER; Exit/ESC quits.
4. **Sound** — synthesised in code (no audio files): wall bounce (scaled by impact), goal chime,
   last-5-seconds ticks and a time-out sound.

## About the videos

Recorded with `tools/record_gameplay.py`: it runs the game's own loop headlessly with a scripted
mouse (autopilot following `tools/autopilot_path.json`), captures every frame at 60 fps and mixes
in the sounds the game plays. The red "phantom bounce!" rings and the bar under the game are
recorder overlays, not part of the game.
