# RP_AngelPelegry_ErikaSantano_JaimeSole_26

# 🤖 Robot Factory Game

A fast, neon styled arcade game built with **Python 3** and **Pygame**. Falling parts rain down from the ceiling of a robot factory. Slide your robot left and right to catch **only the correct part** for each level, dodge traps and bombs, and survive all 7 levels to assemble the final robot and win the game.

> Self contained game: Only one filed required, (logic, graphics, UI) lives in `game2.py`.

---

## Index

1. [Game overview](#game-overview)
2. [Installation](#installation)
3. [Running the game](#running-the-game)
4. [How to play](#how-to-play)
5. [Levels and difficulty](#levels-and-difficulty)
6. [Scoring](#scoring)
7. [Code structure (for developers)](#code-structure-for-developers)
8. [Configuration and tweaking](#configuration-and-tweaking)
 
---

## Game overview

| Item | Value |
|------|-------|
| Genre | Arcade / falling object catcher |
| Language | Python 3 |
| Library | Pygame |
| Window size | 800 × 600 px (fixed) |
| Frame rate | 60 FPS |
| Player | Purple robot (64 × 48 px) with inertia |
| Levels | 7 (Sensors → Cables → Circuits → Batteries → Arms → Legs → Core) |
| Lives | 3 |
| Goal | Collect every required part to assemble the final robot |

Each level asks you to collect a specific type of part. Everything else that falls is a hazard: wrong parts that look similar to the right one, crates, spinning gears and bombs. When you finish all 7 levels, the parts you collected assemble into a complete robot.

---

## Installation

### Prerequisites

- **Python 3.8 or newer** (check with `python --version`)
- **pip**

### Steps

1. Put `game2.py` in a folder of your choice.
2. (Recommended) Create and activate a virtual environment.
3. Install the only dependency:

   ```bash
   pip install pygame
   ```

---

## Running the game

From the folder that contains the file:

```bash
python game2.py
```
## How to play

### Controls

| Key | Action |
|-----|--------|
| `←` / `→` or `A` / `D` | Move the robot left / right |
| `Enter` / `Space` | Confirm the selected button or skip the assembly animation on the victory screen |
| `←` / `→` or `A` / `D` | Change the selected button on the end screens |
| `P` | Pause / resume |
| `Esc` | Quit the game at any time |
| Mouse | Click or hover on the buttons of the end screens |

**Note**: The robot has **inertia** so it accelerates when you press a key and slides a little when you let go.

### Game flow

1. **Welcome screen** shows the title and *"PRESS ANY KEY TO START"*. The game waits until a key (or mouse button) is pressed.
2. **Level intro banner** tells you what to collect. The timer and spawning start after about 2 seconds.
3. **Playing** catch the correct parts, avoid everything else.
4. **Level complete** bonus points are awarded and the next level starts automatically.
5. **End screen** either **GAME OVER** or **ROBOT COMPLETED!**, both showing the final score and two buttons: **PLAY AGAIN** and **EXIT**.

### Rules

- ✅ **Catch the correct part** → points, combo and level progress.
- ❌ **Catch anything else** → you lose points **and one life**.
- 💣 **Bombs** are worse: bigger point penalty, one life and **3 seconds** removed from the clock.
- 🕳️ **Miss a correct part** (it hits the floor) → small point penalty. **3 missed parts = 1 life lost.**
- ⏱️ **Time runs out** → you lose a life and the level restarts.
- 💀 **0 lives** → Game Over.
- ⭐ **Golden parts** are rare, worth more points and add **+1.5 seconds** to the clock.
- 🛡️ After a hit you flash for about 0.9 s and are **invulnerable** to wrong items.

### Potential game hazards

- **Decoys**: parts from other levels that look very similar to the correct one.
- **Zigzag items**: objects that sway left and right while falling.
- **Dash items**: objects that suddenly accelerate mid fall.
- **Waves** (from level 2): a full row of dangerous objects with a **single gap** to slip through. A *"WAVE INCOMING"* warning flashes just before.

### HUD information

- **Level name** and number
- **Current score** (`SCORE: …`)
- **Lives** (hearts)
- **Progress** for the current part (`SENSORS: 3/5`) with a progress bar
- **Time bar** and remaining seconds
- **Misses** counter (3 dots)
- **Combo** counter and multiplier

---

## Levels and difficulty

Difficulty rises every level: objects fall faster, spawn more often, more of them are wrong, and zigzag / dash behavior becomes more common.

| # | Level | Parts needed | Fall speed | Spawn interval (s) | Wrong ratio | Time (s) |
|---|-------|:-----------:|:----------:|:------------------:|:-----------:|:--------:|
| 1 | SENSORS   | 5 | 2.9 | 0.90 | 50 % | 35 |
| 2 | CABLES    | 7 | 3.5 | 0.75 | 56 % | 40 |
| 3 | CIRCUITS  | 6 | 4.1 | 0.62 | 62 % | 40 |
| 4 | BATTERIES | 6 | 4.7 | 0.52 | 67 % | 40 |
| 5 | ARMS      | 5 | 5.4 | 0.44 | 72 % | 38 |
| 6 | LEGS      | 5 | 6.1 | 0.37 | 76 % | 38 |
| 7 | CORE      | 4 | 6.9 | 0.31 | 80 % | 38 |

The game has been designed to be hard but never impossible.

---

## Scoring

| Event | Points |
|-------|-------:|
| Correct part | **+10** × combo multiplier |
| Golden (rare) part | **+25** × combo multiplier (and +1.5 s) |
| Level completed | **+50** + time bonus (2 × seconds left) |
| Wrong item | **−25** and −1 life |
| Bomb | **−50**, −1 life and −3 s |
| Missed correct part | **−8** |

**Combo system:** every 3 correct catches in a row raises the multiplier by one, up to **×5**, but any mistake resets the combo to zero (limited to 0).

---

## Code structure (for developers)

The file is organized into numbered sections:

| Section | Contents |
|---------|----------|
| **1. Constants and level config** | Screen size, FPS, colors, gameplay values, the `LEVELS` list, state names, font loading (`load_fonts`). |
| **2. Drawing helpers** | `draw_text`, `draw_panel`, `draw_glow`, `get_trail`, `draw_heart`, `draw_star`, `draw_rainbow_text`, `build_background`. Glows, panels and trails are **cached** so they are only rendered once. |
| **3. Object drawing** | One `draw_<kind>()` function per object (sensor, cable, circuit, battery, arm, leg, core, crate, gear, bomb), registered in the `DRAWERS` dict. `get_icon()` caches scaled icons. |
| **4. Classes** | `FallingItem` (falling object logic), `Player` (movement with inertia), `Button` (menu buttons), and `draw_player()`. |
| **5. Final robot** | `ROBOT_PARTS` and `part_*()` functions that build the victory screen robot piece by piece; `draw_robot()` animates the assembly. |
| **6. `Game` class** | The main controller: state machine, event handling, update logic, spawning, collisions, rendering and the main loop (`run`). |
| **7. `main()`** | Entry point: `Game().run()`. |

### Game states diagram

```
START ──any key──▶ PLAYING ──level target reached──▶ LEVEL_COMPLETE
                      │                                    │
                      │                        next level ◀┘ (or after level 7)
                      │                                    ▼
                      └──0 lives──▶ GAME_OVER           VICTORY
                                        │                  │
                                        └── PLAY AGAIN ────┘──▶ PLAYING
```

### Main loop

```python
while self.running:
    dt = min(self.clock.tick(FPS) / 1000.0, 0.05)  # 60 FPS
    self.handle_events()
    self.update(dt)
    self.draw()
```

## Configuration and tweaking

Everything is controlled by constants near the top of `game2.py`:

| Constant | What it does |
|----------|--------------|
| `WIDTH, HEIGHT` | Window size |
| `FPS` | Frame rate cap |
| `START_LIVES` | Starting lives (default 3) |
| `MISS_LIMIT` | Missed correct parts needed to lose a life |
| `POINTS_*` | All point values |
| `PLAYER_ACCEL`, `PLAYER_FRICTION`, `PLAYER_MAX_SPEED` | Robot movement feel |
| `COMBO_STEP` | Correct catches per multiplier increase |
| `WAVE_EVERY` | Seconds between waves |
| `LEVELS` | Per level speed, spawn interval, wrong ratio, time limit, zigzag and dash chance |

---
