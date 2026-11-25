# Time Loop game (repo: hyperLoop)

A 2D top-down Pygame game, built step by step. The owner designs the game and gives
instructions; **Claude writes the Python code**. The owner will write the C port of the
final game themselves, so keep the code readable and well commented.

- **Design doc (source of truth for rules and the Build plan):**
  https://claude.ai/artifact/5g33H2zLpNE8cJ8tRcAWVd
- **GitHub:** https://github.com/PurnimaM-0012/hyperLoop

## How we work

1. Before building a step, Claude explains what it adds, why, the ideas it teaches,
   the files involved, and how to test it, and asks about open design choices.
2. Once the owner says go, Claude implements it, tests it headlessly, commits and
   pushes to GitHub, and updates the design doc's Build plan.
3. After each step, Claude summarises what changed and explains the next step.
4. The owner makes all design decisions; record new ones in the design doc.

## Run it

Python: `D:\Code_projects\Py\python\myvir\Scripts\python.exe` (Pygame 2.6.1 is installed there).

```
cd d:\github\time_loop_game
D:\Code_projects\Py\python\myvir\Scripts\Activate.ps1
python main.py
```

Keys in a level: WASD/arrows move, Q drop item, C skip to the race, Y/N answer "Race?",
R race from the "cleared" screen, F5 save, Esc menu.
On the track: WASD drive, Space drift, Tab tuning panel, Esc give up, Enter leave results.
Debug keys: R reset loop, B +1 bag slot.

## Code map

| File | What it does |
|---|---|
| `main.py` | Window, `Game` object (fonts, progress, current scene), the game loop |
| `scenes.py` | `MenuScene` and `LevelScene` (timer, `reset_loop()`, portals, parts, HUD) |
| `level.py` | Loads levels from `levels/*.json`: areas (text maps), walls, parts, machine, portals, each level's `track` (null = no race) and `loop_cap`; `Track` loads a race track: finish line, checkpoints, rival starts, waypoints |
| `levels/` | Level files, `areas/` maps, and `tiles.json` (the tile legend: symbol -> solid, colour, image) |
| `player.py` | Movement with `dt`, axis-by-axis wall collision, `teleport()` |
| `bag.py` | Limited-slot inventory; items have `kind` and `persistent` |
| `machine.py` | `Part` (states ON_GROUND / CARRIED / INSTALLED, dropping) and `Machine` |
| `camera.py` | World -> screen coordinates, follows the player, clamps at map edges; smooth follow and screen shake for racing |
| `car.py` | Arcade car: angle + velocity, eased steering, grip/handbrake drift, grass slowdown, barrier bounce; health, `take_damage()`, wrecks; `bump_cars()` for car-to-car crashes |
| `rival.py` | `RivalDriver`: steers a rival car along the track's waypoints; the 6-tile, 15% coin-flip rubber band |
| `tuning.py` | Live tuning panel on the track (Tab); F6 writes `tuning.txt` |
| `levels/tracks/` | Race tracks as text maps (`=` start/finish line, digits `1` `2` `3` = checkpoints in order, `>` `v` `<` `^` arrows, `,` grass at 25% speed), plus `rival_starts` and `waypoints` |
| `time_loop.py` | The countdown and `format_time()` |
| `progress.py` | Persistent state (never touched by `reset_loop()`), saved to `save.json`; `best_bonus` per level, and `loop_length()` worked out from it |
| `settings.py` | Every tunable number and colour |

Key rule: **loop state** is reset by `reset_loop()`; **persistent state** lives only in `Progress`.

## Status

Steps 1-11 done (loop, movement, timer, parts, progress/saving, levels/menu, research
facility + portals + camera, bag, arcade car with live tuning, race rules: "Race? Y/N"
at the 40% mark with the timer paused, 1 lap with checkpoints, bonus = slot + time left,
best bonus per level, loop cap 160 s placeholder, skip to race, race after clearing;
rival AI with the same car settings, car health 100 with damage from barriers and
car crashes, wrecks lose / all rivals wrecked wins at once).
Race rules: no race in the Prison (races start at the Research Facility); a bonus only
counts on the first visit to a level (replays are practice).
Next: Step 12 (weapons). Later: repairs/fuel/salvage, utilities, town puzzles/traps/NPCs. See the design doc.

## Conventions

- Beginner-friendly code with comments explaining *why*.
- Numbers go in `settings.py`; level content goes in `levels/`.
- Test headlessly with `SDL_VIDEODRIVER=dummy`. Don't touch the owner's `save.json`.
