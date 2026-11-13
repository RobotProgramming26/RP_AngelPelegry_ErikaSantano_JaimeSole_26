#!/usr/bin/env python3
"""
ROBOT FACTORY - ROS 1 GAME NODE (HARD EDITION WITH FULL GRAPHICS)
==================================================================
This node handles the main Pygame graphics, game loop, and ROS 1 communication:
- Subscribes to /user_information (GameUserMsg) to trigger Phase 1 (Welcome) -> Phase 2 (Game).
- Subscribes to /keyboard_control (std_msgs/String) for remote movement commands.
- Publishes final score to /result_information (std_msgs/Int64) in Phase 3 (Final).
"""

import colorsys
import math
import random
import sys
import pygame
import rospy

from std_msgs.msg import String, Int64
from game_msgs.msg import GameUserMsg

# =============================================================================
# 1. CONSTANTS AND LEVEL CONFIGURATION
# =============================================================================

WIDTH, HEIGHT = 800, 600
FPS = 60
FLOOR_Y = HEIGHT - 44
ROS_CONTROL_COMMAND_HOLD = 0.55
ROS_CONTROL_STRENGTH = 1.0

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CYAN = (0, 230, 255)
CYAN_DIM = (30, 120, 140)
RED = (255, 70, 70)
GREEN = (80, 230, 120)
GOLD = (255, 205, 60)
ORANGE = (255, 150, 30)
MUTED = (150, 175, 195)
PANEL_FILL = (6, 16, 30)
STEEL = (190, 198, 215)

PURPLE = (150, 70, 230)
PURPLE_LIGHT = (195, 145, 255)
PURPLE_DARK = (95, 45, 165)

# --- Gameplay Rules ---
START_LIVES = 3
POINTS_NORMAL = 10
POINTS_RARE = 25
POINTS_LEVEL = 50
POINTS_PENALTY = 25
POINTS_MISS = 8
MISS_LIMIT = 3
RARE_TIME_BONUS = 1.5
BOMB_TIME_PENALTY = 3.0
PLAYER_ACCEL = 2.4
PLAYER_FRICTION = 0.80
PLAYER_MAX_SPEED = 9.5
INVULNERABLE_TIME = 0.9
LEVEL_INTRO_TIME = 2.2
LEVEL_COMPLETE_TIME = 2.8
COMBO_STEP = 3
WAVE_EVERY = (7.0, 10.0)

MAGENTA = (255, 70, 200)
NEON = [CYAN, MAGENTA, GOLD, GREEN, (150, 110, 255), ORANGE]
LEVEL_ACCENTS = [CYAN, MAGENTA, GREEN, (100, 150, 255), ORANGE, (190, 120, 255), GOLD]

LEVELS = [
    dict(name="SENSORS",   kind="sensor",  target=5, speed=2.9, interval=0.90, max_items=9,  wrong_ratio=0.50, rare_chance=0.06, max_gap=4.5, time=35, sway=0.20, dash=0.00),
    dict(name="CABLES",    kind="cable",   target=7, speed=3.5, interval=0.75, max_items=10, wrong_ratio=0.56, rare_chance=0.07, max_gap=4.5, time=40, sway=0.30, dash=0.10),
    dict(name="CIRCUITS",  kind="circuit", target=6, speed=4.1, interval=0.62, max_items=11, wrong_ratio=0.62, rare_chance=0.08, max_gap=4.3, time=40, sway=0.40, dash=0.20),
    dict(name="BATTERIES", kind="battery", target=6, speed=4.7, interval=0.52, max_items=12, wrong_ratio=0.67, rare_chance=0.09, max_gap=4.2, time=40, sway=0.50, dash=0.30),
    dict(name="ARMS",      kind="arm",     target=5, speed=5.4, interval=0.44, max_items=13, wrong_ratio=0.72, rare_chance=0.10, max_gap=4.0, time=38, sway=0.60, dash=0.35),
    dict(name="LEGS",      kind="leg",     target=5, speed=6.1, interval=0.37, max_items=14, wrong_ratio=0.76, rare_chance=0.11, max_gap=4.0, time=38, sway=0.70, dash=0.40),
    dict(name="CORE",      kind="core",    target=4, speed=6.9, interval=0.31, max_items=15, wrong_ratio=0.80, rare_chance=0.12, max_gap=3.8, time=38, sway=0.80, dash=0.45),
]
NUM_LEVELS = len(LEVELS)

PART_KINDS = [lvl["kind"] for lvl in LEVELS]
JUNK_KINDS = ["crate", "gear", "bomb"]

TRAIL_COLORS = {
    "sensor": CYAN, "cable": (190, 110, 255), "circuit": GREEN, "battery": (70, 130, 255),
    "arm": PURPLE_LIGHT, "leg": PURPLE_LIGHT, "core": CYAN, "crate": RED,
    "gear": (190, 195, 215), "bomb": ORANGE,
}

FONTS = {}

def load_fonts():
    names = "segoeui,arial,helvetica,dejavusans"
    FONTS["title"] = pygame.font.SysFont(names, 76, bold=True)
    FONTS["score"] = pygame.font.SysFont(names, 54, bold=True)
    FONTS["h1"] = pygame.font.SysFont(names, 44, bold=True)
    FONTS["h2"] = pygame.font.SysFont(names, 30, bold=True)
    FONTS["h3"] = pygame.font.SysFont(names, 24, bold=True)
    FONTS["body"] = pygame.font.SysFont(names, 19, bold=True)
    FONTS["small"] = pygame.font.SysFont(names, 16, bold=True)


# =============================================================================
# 2. DRAWING FUNCTIONS AND HELPERS
# =============================================================================

def draw_text(surface, text, font, color, pos, anchor="center", shadow=True):
    image = font.render(text, True, color)
    rect = image.get_rect(**{anchor: pos})
    if shadow:
        surface.blit(font.render(text, True, BLACK), rect.move(2, 2))
    surface.blit(image, rect)
    return rect

_panel_cache = {}

def draw_panel(surface, rect, border=CYAN, fill=PANEL_FILL, alpha=215, radius=12, width=2):
    rect = pygame.Rect(rect)
    key = (rect.size, border, fill, alpha, radius, width)
    pad = 8
    if key not in _panel_cache:
        w, h = rect.size
        cut = max(4, min(radius, h // 3, w // 3))
        pts = [(pad + cut, pad), (pad + w - cut, pad), (pad + w, pad + cut),
               (pad + w, pad + h - cut), (pad + w - cut, pad + h),
               (pad + cut, pad + h), (pad, pad + h - cut), (pad, pad + cut)]
        surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (*fill, alpha), pts)
        shine = pygame.Surface((w - 2 * cut, max(4, h // 3)), pygame.SRCALPHA)
        shine.fill((*border, 14))
        surf.blit(shine, (pad + cut, pad + 3))
        pygame.draw.polygon(surf, (*border, 35), pts, width + 6)
        pygame.draw.polygon(surf, (*border, 90), pts, width + 3)
        pygame.draw.polygon(surf, border, pts, width)
        for (px, py), (dx, dy) in (((pts[0]), (1, 0)), ((pts[2]), (0, 1)),
                                   ((pts[4]), (-1, 0)), ((pts[6]), (0, -1))):
            pygame.draw.circle(surf, WHITE, (px, py), 2)
        _panel_cache[key] = surf
    surface.blit(_panel_cache[key], (rect.x - pad, rect.y - pad))

_glow_cache = {}

def get_glow(radius, color):
    key = (radius, color)
    if key not in _glow_cache:
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -2):
            alpha = int(120 * (1 - r / radius) ** 2)
            pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
        _glow_cache[key] = surf
    return _glow_cache[key]

def draw_glow(surface, cx, cy, radius, color):
    surface.blit(get_glow(radius, color), (cx - radius, cy - radius))

_trail_cache = {}

def get_trail(color, length):
    key = (color, length)
    if key not in _trail_cache:
        surf = pygame.Surface((12, length), pygame.SRCALPHA)
        for y in range(length):
            a = int(120 * (y / length) ** 2)
            pygame.draw.line(surf, (*color, a // 3), (3, y), (8, y))
            pygame.draw.line(surf, (*color, a), (5, y), (6, y))
        _trail_cache[key] = surf
    return _trail_cache[key]

def draw_heart(surface, cx, cy, r, color, filled=True):
    width = 0 if filled else 2
    pygame.draw.circle(surface, color, (cx - r, cy - r // 2), r, width)
    pygame.draw.circle(surface, color, (cx + r, cy - r // 2), r, width)
    pygame.draw.polygon(surface, color,
                        [(cx - 2 * r + 1, cy - r // 2 + 2),
                         (cx + 2 * r - 1, cy - r // 2 + 2),
                         (cx, cy + 2 * r)], width)

def draw_star(surface, cx, cy, r, color):
    points = []
    for i in range(8):
        angle = i * math.pi / 4
        radius = r if i % 2 == 0 else r / 3
        points.append((cx + radius * math.cos(angle),
                       cy + radius * math.sin(angle)))
    pygame.draw.polygon(surface, color, points)

def draw_check(surface, cx, cy, color=CYAN):
    pygame.draw.lines(surface, color, False,
                      [(cx - 7, cy), (cx - 2, cy + 6), (cx + 8, cy - 6)], 3)

def dim(color, k):
    return tuple(int(c * k) for c in color)

def hsv(h, s=0.75, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))

def draw_rainbow_text(surface, text, font, center, t, speed=0.25):
    widths = [font.size(c)[0] for c in text]
    x = center[0] - sum(widths) // 2
    for i, ch in enumerate(text):
        y = center[1] + int(3 * math.sin(t * 3 + i * 0.6))
        draw_text(surface, ch, font, hsv(t * speed + i * 0.06), (x, y), "midleft")
        x += widths[i]

def draw_bomb(s, cx, cy, t):
    pygame.draw.circle(s, (38, 38, 54), (cx, cy + 3), 16)
    pygame.draw.circle(s, (255, 120, 40), (cx, cy + 3), 16, 2)
    pygame.draw.circle(s, (120, 125, 150), (cx - 6, cy - 2), 3)
    pygame.draw.line(s, (200, 170, 120), (cx + 6, cy - 10), (cx + 12, cy - 17), 3)
    spark = (255, 255, 120) if int(t * 12) % 2 else (255, 90, 40)
    draw_glow(s, cx + 13, cy - 18, 10, spark)
    pygame.draw.circle(s, spark, (cx + 13, cy - 18), 3)

def build_background(accent=CYAN, red=False):
    bg = pygame.Surface((WIDTH, HEIGHT))
    top = (22, 8, 14) if red else (5, 10, 22)
    bot = (34, 12, 20) if red else (9, 22, 38)
    for y in range(HEIGHT):
        t = y / HEIGHT
        pygame.draw.line(bg, tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)), (0, y), (WIDTH, y))
    draw_glow(bg, WIDTH // 2, 340, 330, dim(accent, 0.22))

    grid = (44, 16, 24) if red else (14, 30, 46)
    for x in range(0, WIDTH, 40):
        pygame.draw.line(bg, grid, (x, 0), (x, FLOOR_Y))
    for y in range(0, FLOOR_Y, 40):
        pygame.draw.line(bg, grid, (0, y), (WIDTH, y))

    for x in (14, 786):
        draw_glow(bg, x, 190, 70, dim(accent, 0.6))
        pygame.draw.rect(bg, accent, (x - 2, 120, 4, 140))
    for y, x0 in ((215, 0), (260, 740)):
        draw_glow(bg, x0 + 30, y, 50, dim(accent, 0.5))
        pygame.draw.rect(bg, accent, (x0, y - 2, 60, 4))

    for i, x in enumerate(range(70, WIDTH, 110)):
        col = accent if i % 3 == 0 else NEON[(i + 1) % len(NEON)]
        if red:
            col = RED if i % 2 == 0 else ORANGE
        cone = pygame.Surface((WIDTH, 330), pygame.SRCALPHA)
        pygame.draw.polygon(cone, (*col, 16), [(x - 10, 0), (x + 10, 0), (x + 70, 320), (x - 70, 320)])
        bg.blit(cone, (0, 0))
        draw_glow(bg, x, 4, 46, dim(col, 0.7))
        pygame.draw.rect(bg, col, (x - 18, 0, 36, 5), border_radius=2)

    rng = random.Random(7)
    for x0, x1 in ((0, 60), (60, 120), (680, 740), (740, 800)):
        y = FLOOR_Y
        width = rng.randint(50, 62)
        while y > 330:
            h = rng.randint(44, 70)
            box = pygame.Rect(x0 + rng.randint(-10, 6), y - h, width, h - 3)
            pygame.draw.rect(bg, (8, 15, 26) if not red else (22, 9, 14), box)
            pygame.draw.rect(bg, dim(accent, 0.28), box, 2)
            if rng.random() < 0.6:
                pygame.draw.rect(bg, dim(accent, 0.75), (box.x + 6, box.y + 8, box.w - 12, 3))
            if rng.random() < 0.35:
                pygame.draw.circle(bg, ORANGE if rng.random() < 0.5 else GOLD, (box.right - 8, box.bottom - 8), 2)
            y -= h

    pygame.draw.rect(bg, (12, 18, 30) if not red else (26, 10, 16), (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y))
    line_col = dim(accent, 0.28)
    for i in range(-10, 11):
        pygame.draw.line(bg, line_col, (WIDTH // 2 + i * 70, FLOOR_Y), (WIDTH // 2 + i * 150, HEIGHT))
    for dy in (9, 21, 35):
        pygame.draw.line(bg, line_col, (0, FLOOR_Y + dy), (WIDTH, FLOOR_Y + dy))
    pygame.draw.line(bg, dim(accent, 0.35), (0, FLOOR_Y - 1), (WIDTH, FLOOR_Y - 1), 3)
    pygame.draw.line(bg, accent, (0, FLOOR_Y), (WIDTH, FLOOR_Y), 2)
    for x0 in (25, 600):
        draw_glow(bg, x0 + 90, FLOOR_Y + 22, 60, dim(accent, 0.6))
        pygame.draw.rect(bg, accent, (x0, FLOOR_Y + 20, 180, 5))
    return bg


# =============================================================================
# 3. ITEM DRAWERS
# =============================================================================

def draw_sensor(s, cx, cy, t):
    pygame.draw.circle(s, (30, 40, 60), (cx, cy), 18)
    pygame.draw.circle(s, CYAN, (cx, cy), 18, 3)
    pygame.draw.circle(s, (15, 18, 28), (cx, cy), 10)
    pygame.draw.circle(s, CYAN, (cx, cy), 6)
    pygame.draw.circle(s, WHITE, (cx - 2, cy - 3), 2)

def draw_cable(s, cx, cy, t):
    pts = [(cx - 20 + i * 2, cy + int(8 * math.sin(i * 0.5 + t * 3))) for i in range(21)]
    pygame.draw.lines(s, ORANGE, False, pts, 5)
    pygame.draw.lines(s, (255, 225, 140), False, pts, 1)
    for px, py in (pts[0], pts[-1]):
        pygame.draw.rect(s, STEEL, (px - 4, py - 5, 8, 10), border_radius=2)

def draw_circuit(s, cx, cy, t):
    board = pygame.Rect(0, 0, 38, 38)
    board.center = (cx, cy)
    pygame.draw.rect(s, (25, 130, 70), board, border_radius=5)
    pygame.draw.rect(s, (90, 230, 130), board, 2, border_radius=5)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        pygame.draw.line(s, (130, 255, 170), (cx + dx * 7, cy + dy * 7), (cx + dx * 17, cy + dy * 17), 2)
    chip = pygame.Rect(0, 0, 14, 14)
    chip.center = (cx, cy)
    pygame.draw.rect(s, (20, 25, 30), chip)
    pygame.draw.rect(s, (170, 180, 190), chip, 1)
    for dx, dy in ((-14, -14), (14, -14), (-14, 14), (14, 14)):
        pygame.draw.circle(s, (255, 230, 120), (cx + dx, cy + dy), 2)

def draw_battery(s, cx, cy, t):
    body = pygame.Rect(0, 0, 24, 38)
    body.center = (cx, cy + 2)
    pygame.draw.rect(s, STEEL, (cx - 5, body.top - 5, 10, 6), border_radius=2)
    pygame.draw.rect(s, (40, 110, 230), body, border_radius=4)
    pygame.draw.rect(s, (150, 195, 255), body, 2, border_radius=4)
    pygame.draw.polygon(s, GOLD, [(cx + 2, cy - 10), (cx - 6, cy + 4), (cx - 1, cy + 4),
                                  (cx - 3, cy + 14), (cx + 6, cy - 2), (cx + 1, cy - 2)])

def draw_arm(s, cx, cy, t):
    pygame.draw.rect(s, STEEL, (cx - 22, cy - 7, 44, 14), border_radius=6)
    pygame.draw.rect(s, PURPLE, (cx - 8, cy - 7, 16, 14))
    pygame.draw.rect(s, (110, 120, 145), (cx - 22, cy - 7, 44, 14), 2, border_radius=6)
    for dx in (-16, 16):
        pygame.draw.circle(s, (110, 120, 145), (cx + dx, cy), 7)
        pygame.draw.circle(s, (50, 55, 75), (cx + dx, cy), 3)

def draw_leg(s, cx, cy, t):
    pygame.draw.rect(s, STEEL, (cx - 7, cy - 22, 14, 32), border_radius=5)
    pygame.draw.rect(s, PURPLE, (cx - 7, cy - 8, 14, 12))
    pygame.draw.rect(s, (110, 120, 145), (cx - 7, cy - 22, 14, 32), 2, border_radius=5)
    pygame.draw.circle(s, (110, 120, 145), (cx, cy - 18), 8)
    pygame.draw.circle(s, (50, 55, 75), (cx, cy - 18), 3)
    pygame.draw.rect(s, PURPLE_DARK, (cx - 13, cy + 10, 26, 10), border_radius=4)

def draw_core(s, cx, cy, t):
    pulse = 1 + 0.1 * math.sin(t * 6)
    draw_glow(s, cx, cy, int(30 * pulse), CYAN)
    pygame.draw.circle(s, (0, 170, 200), (cx, cy), 16)
    pygame.draw.circle(s, (160, 250, 255), (cx, cy), 11)
    pygame.draw.circle(s, WHITE, (cx, cy), 5)
    pygame.draw.circle(s, CYAN, (cx, cy), 17, 2)

def draw_crate(s, cx, cy, t):
    box = pygame.Rect(0, 0, 34, 34)
    box.center = (cx, cy)
    pygame.draw.rect(s, (150, 25, 40), box, border_radius=6)
    pygame.draw.rect(s, (255, 80, 80), box, 3, border_radius=6)
    pygame.draw.line(s, WHITE, (cx - 9, cy - 9), (cx + 9, cy + 9), 4)
    pygame.draw.line(s, WHITE, (cx - 9, cy + 9), (cx + 9, cy - 9), 4)

def draw_gear(s, cx, cy, t):
    teeth = 8
    pts = []
    for i in range(teeth):
        base = t * 1.2 + i * 2 * math.pi / teeth
        for da, rad in ((-0.17, 14), (-0.10, 19), (0.10, 19), (0.17, 14)):
            pts.append((cx + rad * math.cos(base + da), cy + rad * math.sin(base + da)))
    pygame.draw.polygon(s, (90, 95, 108), pts)
    pygame.draw.polygon(s, (225, 70, 70), pts, 2)
    pygame.draw.circle(s, (90, 95, 108), (cx, cy), 12)
    pygame.draw.circle(s, (225, 70, 70), (cx, cy), 12, 2)
    pygame.draw.circle(s, (20, 22, 30), (cx, cy), 5)

DRAWERS = {
    "sensor": draw_sensor, "cable": draw_cable, "circuit": draw_circuit,
    "battery": draw_battery, "arm": draw_arm, "leg": draw_leg,
    "core": draw_core, "crate": draw_crate, "gear": draw_gear, "bomb": draw_bomb,
}

_icon_cache = {}

def get_icon(kind, size):
    key = (kind, size)
    if key not in _icon_cache:
        base = pygame.Surface((64, 64), pygame.SRCALPHA)
        DRAWERS[kind](base, 32, 32, 0)
        _icon_cache[key] = pygame.transform.smoothscale(base, (size, size))
    return _icon_cache[key]


# =============================================================================
# 4. GAME OBJECT CLASSES
# =============================================================================

class FallingItem:
    SIZE = 44

    def __init__(self, kind, x, speed, wrong, rare=False, sway=0.0, dash=False):
        self.kind = kind
        self.wrong = wrong
        self.rare = rare
        self.speed = speed
        self.cur_speed = speed
        self.dash = dash
        self.dash_y = random.uniform(120, 300)
        self.rect = pygame.Rect(0, 0, self.SIZE, self.SIZE)
        self.base_x = x
        self.rect.centerx = x
        self.rect.bottom = 0
        self.y = float(self.rect.y)
        self.age = random.random() * 10
        self.amp = random.uniform(25, 65) if random.random() < sway else 0
        self.freq = random.uniform(1.6, 3.2)
        self.phase = random.random() * 6.28

    @property
    def hitbox(self):
        return self.rect.inflate(-8, -8)

    def update(self, dt):
        self.cur_speed = self.speed * (1.7 if self.dash and self.y > self.dash_y else 1.0)
        self.y += self.cur_speed * dt * FPS
        self.rect.y = int(self.y)
        self.age += dt
        if self.amp:
            x = self.base_x + self.amp * math.sin(self.age * self.freq + self.phase)
            self.rect.centerx = int(max(24, min(WIDTH - 24, x)))

    def off_screen(self):
        return self.rect.top > HEIGHT

    def draw(self, surface):
        cx, cy = self.rect.center
        col = TRAIL_COLORS[self.kind]
        length = max(16, (int(self.cur_speed * 16) // 8) * 8)
        surface.blit(get_trail(col, length), (cx - 6, cy - 16 - length))
        draw_glow(surface, cx, cy, 34, dim(col, 0.55))
        if self.rare:
            pulse = 1 + 0.12 * math.sin(self.age * 8)
            draw_glow(surface, cx, cy, int(38 * pulse), GOLD)
        DRAWERS[self.kind](surface, cx, cy, self.age)
        if self.rare:
            draw_star(surface, cx + 17, cy - 17, 5 + int(2 * math.sin(self.age * 10)), GOLD)


def draw_player_sprite(surface, rect, dead=False):
    x, y = rect.topleft
    for wx in (14, 50):
        pygame.draw.circle(surface, (30, 30, 45), (x + wx, y + 41), 7)
        pygame.draw.circle(surface, (120, 120, 150), (x + wx, y + 41), 7, 2)
    body = pygame.Rect(x + 8, y + 17, 48, 24)
    pygame.draw.rect(surface, PURPLE, body, border_radius=7)
    pygame.draw.rect(surface, PURPLE_LIGHT, body, 2, border_radius=7)
    pygame.draw.circle(surface, CYAN, (x + 32, y + 29), 4)
    head = pygame.Rect(x + 13, y, 38, 24)
    pygame.draw.rect(surface, PURPLE, head, border_radius=8)
    pygame.draw.rect(surface, PURPLE_LIGHT, head, 2, border_radius=8)
    pygame.draw.rect(surface, (15, 18, 35), (x + 18, y + 5, 28, 14), border_radius=5)
    for ex in (26, 38):
        if dead:
            pygame.draw.line(surface, CYAN, (ex + x - 3, y + 8), (ex + x + 3, y + 16), 2)
            pygame.draw.line(surface, CYAN, (ex + x - 3, y + 16), (ex + x + 3, y + 8), 2)
        else:
            pygame.draw.rect(surface, CYAN, (x + ex - 2, y + 8, 4, 8), border_radius=2)
    pygame.draw.circle(surface, PURPLE_DARK, (x + 11, y + 12), 4)
    pygame.draw.circle(surface, PURPLE_DARK, (x + 53, y + 12), 4)


class Player:
    WIDTH = 64
    HEIGHT = 48

    def __init__(self):
        self.rect = pygame.Rect(0, 0, self.WIDTH, self.HEIGHT)
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.invulnerable = 0.0
        self.reset()

    def reset(self):
        self.x = WIDTH / 2 - self.WIDTH / 2
        self.y = FLOOR_Y - self.HEIGHT + 2
        self.vx = 0.0
        self.vy = 0.0
        self.rect.x = int(self.x)
        self.rect.bottom = FLOOR_Y + 2
        self.invulnerable = 0.0

    @property
    def hitbox(self):
        return self.rect.inflate(-10, -4)

    def move(self, dt, direction_x, direction_y=0):
        f = dt * FPS
        self.vx += direction_x * PLAYER_ACCEL * f
        self.vx *= PLAYER_FRICTION ** f
        self.vx = max(-PLAYER_MAX_SPEED, min(PLAYER_MAX_SPEED, self.vx))
        self.x += self.vx * f
        if self.x < 0:
            self.x, self.vx = 0.0, 0.0
        elif self.x > WIDTH - self.WIDTH:
            self.x, self.vx = float(WIDTH - self.WIDTH), 0.0
        self.rect.x = int(self.x)

        # Support vertical movement (UP/DOWN)
        self.vy += direction_y * PLAYER_ACCEL * f
        self.vy *= PLAYER_FRICTION ** f
        self.vy = max(-PLAYER_MAX_SPEED, min(PLAYER_MAX_SPEED, self.vy))
        self.y += self.vy * f
        self.y = max(100.0, min(float(FLOOR_Y - self.HEIGHT + 2), self.y))
        self.rect.y = int(self.y)

        if self.invulnerable > 0:
            self.invulnerable -= dt

    def draw(self, surface, t=0.0):
        cx = self.rect.centerx
        pulse = 0.75 + 0.25 * math.sin(t * 5)
        draw_glow(surface, cx, self.rect.centery + 4, 62, dim((180, 90, 255), pulse))
        pygame.draw.ellipse(surface, (70, 30, 120), (cx - 30, FLOOR_Y + 1, 60, 9))
        if self.invulnerable > 0 and int(self.invulnerable * 12) % 2 == 0:
            return
        draw_player_sprite(surface, self.rect)


# =============================================================================
# 5. FINAL ROBOT DISPLAY (VICTORY SCREEN)
# =============================================================================

ROBOT_W, ROBOT_H = 260, 340
ASSEMBLY_STEP = 0.7
ASSEMBLY_SLIDE = 0.5

def part_legs(s):
    for x in (94, 140):
        pygame.draw.rect(s, PURPLE_DARK, (x, 222, 26, 84), border_radius=8)
        pygame.draw.rect(s, PURPLE, (x + 3, 240, 20, 36), border_radius=5)
        pygame.draw.circle(s, STEEL, (x + 13, 232), 10)
        pygame.draw.circle(s, (60, 65, 85), (x + 13, 232), 4)
        pygame.draw.rect(s, PURPLE_LIGHT, (x - 6, 302, 38, 16), border_radius=6)

def part_torso(s):
    pygame.draw.rect(s, PURPLE, (78, 92, 104, 134), border_radius=14)
    pygame.draw.rect(s, PURPLE_LIGHT, (78, 92, 104, 134), 3, border_radius=14)
    pygame.draw.rect(s, PURPLE_DARK, (88, 212, 84, 14), border_radius=5)

def part_circuit(s):
    board = pygame.Rect(98, 104, 64, 44)
    pygame.draw.rect(s, (25, 130, 70), board, border_radius=6)
    pygame.draw.rect(s, (90, 230, 130), board, 2, border_radius=6)
    pygame.draw.rect(s, (20, 25, 30), (118, 114, 24, 24))
    pygame.draw.rect(s, (170, 180, 190), (118, 114, 24, 24), 1)
    for x in (104, 108, 152, 156):
        pygame.draw.line(s, (130, 255, 170), (x, 112), (x, 140), 1)

def part_battery(s):
    body = pygame.Rect(150, 162, 22, 46)
    pygame.draw.rect(s, STEEL, (156, 157, 10, 6), border_radius=2)
    pygame.draw.rect(s, (40, 110, 230), body, border_radius=4)
    pygame.draw.rect(s, (150, 195, 255), body, 2, border_radius=4)

def part_cables(s):
    for x in (112, 148):
        pygame.draw.lines(s, ORANGE, False, [(x, 78), (x + 5, 84), (x - 5, 89), (x, 96)], 4)

def part_arms(s):
    for side in (0, 1):
        def mx(v): return v if side == 0 else ROBOT_W - v
        pygame.draw.circle(s, STEEL, (mx(64), 112), 15)
        pygame.draw.rect(s, PURPLE, (mx(64) - 12, 118, 24, 50), border_radius=8)

def part_head(s):
    pygame.draw.rect(s, (228, 230, 245), (82, 12, 96, 70), border_radius=16)
    pygame.draw.rect(s, (22, 26, 44), (91, 24, 78, 44), border_radius=10)

def part_sensors(s):
    for x in (112, 148):
        draw_glow(s, x, 46, 18, CYAN)
        pygame.draw.circle(s, CYAN, (x, 46), 12, 3)

def part_core(s):
    draw_glow(s, 130, 186, 38, CYAN)
    pygame.draw.circle(s, (0, 170, 200), (130, 186), 17)

ROBOT_PARTS = [
    ("legs",    "leg",     (0, 90),    part_legs),
    ("torso",   None,      (0, -90),   part_torso),
    ("circuit", "circuit", (-110, 0),  part_circuit),
    ("battery", "battery", (110, 0),   part_battery),
    ("cables",  "cable",   (0, -70),   part_cables),
    ("arms",    "arm",     (0, -90),   part_arms),
    ("head",    None,      (0, -120),  part_head),
    ("sensors", "sensor",  (0, -120),  part_sensors),
    ("core",    "core",    (0, 0),     part_core),
]
ASSEMBLY_TOTAL = len(ROBOT_PARTS) * ASSEMBLY_STEP + ASSEMBLY_SLIDE + 0.4
_robot_surfaces = {}

def get_robot_part(name, func):
    if name not in _robot_surfaces:
        surf = pygame.Surface((ROBOT_W, ROBOT_H), pygame.SRCALPHA)
        func(surf)
        _robot_surfaces[name] = surf
    return _robot_surfaces[name]

def draw_robot(surface, left, top, elapsed):
    for i, (name, _kind, offset, func) in enumerate(ROBOT_PARTS):
        progress = (elapsed - i * ASSEMBLY_STEP) / ASSEMBLY_SLIDE
        if progress <= 0: continue
        progress = min(progress, 1.0)
        eased = 1 - (1 - progress) ** 3
        part = get_robot_part(name, func)
        part.set_alpha(int(255 * eased))
        surface.blit(part, (left + offset[0] * (1 - eased), top + offset[1] * (1 - eased)))


# =============================================================================
# 6. ROS NODE CLASS (GAME_NODE)
# =============================================================================

class GameNode(object):
    def __init__(self):
        # Initialize ROS Node
        rospy.init_node('game_node')

        # Encapsulated ROS Publishers and Subscribers
        self.__pub_result = rospy.Publisher('/result_information', Int64, queue_size=10, latch=True)
        rospy.Subscriber('/user_information', GameUserMsg, self.__user_info_callback)
        rospy.Subscriber('/keyboard_control', String, self.__keyboard_control_callback)

        # Player profile and ROS state machine variables
        self.__user_name = ""
        self.__user_username = ""
        self.__user_age = 0
        self.__current_phase = "WELCOME" # WELCOME -> GAME -> FINAL
        self.__control_command = ""
        self.__control_command_timer = 0.0
        self.welcome_timer = 0.0 # Countdown timer for Welcome screen display

        # Pygame setup
        pygame.init()
        pygame.display.set_caption("Robot Factory - ROS Game Node")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        load_fonts()

        # Visual assets and background caches
        self.backgrounds = {a: build_background(a) for a in LEVEL_ACCENTS}
        self.backgrounds["red"] = build_background(RED, red=True)
        self.particles = []
        self.ambient = [dict(x=random.randint(0, WIDTH), y=random.randint(0, HEIGHT),
                             vy=random.uniform(8, 30), r=random.choice((4, 5, 6, 8)),
                             color=dim(random.choice(NEON), 0.55), ph=random.random() * 6.28)
                        for _ in range(38)]

        self.time = 0.0
        self.player = Player()
        self.decor = []
        self.paused = False
        self.assembly_time = 0.0
        self.time_bonus = 0

        self.reset_game()
        rospy.loginfo("Welcome phase started.")

    @property
    def cfg(self):
        return LEVELS[self.level_index]

    # --- ROS CALLBACKS ---
    def __user_info_callback(self, msg):
        self.__user_name = msg.name
        self.__user_username = msg.username
        self.__user_age = msg.age
        rospy.loginfo("Game Node received player info: Name='%s', Username='%s', Age=%d",
                      self.__user_name, self.__user_username, self.__user_age)
        
        # Start a 4-second timer to keep the Welcome screen clearly visible
        if self.__current_phase == "WELCOME" and self.welcome_timer <= 0:
            self.welcome_timer = 4.0

    def __keyboard_control_callback(self, msg):
        if msg.data in ("LEFT", "RIGHT", "UP", "DOWN"):
            self.__control_command = msg.data
            self.__control_command_timer = ROS_CONTROL_COMMAND_HOLD
        elif msg.data == "STOP":
            self.__control_command = ""
            self.__control_command_timer = 0.0

    # --- GAME LOGIC ---
    def reset_game(self):
        self.score = 0
        self.lives = START_LIVES
        self.levels_completed = 0
        self.level_reached = 1
        self.popups = []
        self.flash = 0.0
        self.shake = 0.0
        self.paused = False
        self.combo = 0
        self.best_combo = 0
        self.start_level(0)

    def start_level(self, index):
        self.level_index = index
        self.level_reached = max(self.level_reached, index + 1)
        self.collected = 0
        self.misses = 0
        self.items = []
        self.spawn_timer = 0.3
        self.since_correct = 0.0
        self.intro_timer = LEVEL_INTRO_TIME
        self.time_left = float(LEVELS[index]["time"])
        self.wave_timer = random.uniform(5.0, 8.0)
        self.wave_warn = False
        self.player.reset()

    # --- PHASE TRANSITIONS ---
    def transition_to_game_phase(self):
        self.__current_phase = "GAME"
        rospy.loginfo("Game phase started.")

    def transition_to_final_phase(self):
        self.__current_phase = "FINAL"
        rospy.loginfo("Final phase reached, calculating score.")
        
        # Publish final score to RESULT_GAME_NODE
        res = Int64()
        res.data = int(self.score)
        self.__pub_result.publish(res)
        rospy.loginfo("Published final score (%d) to /result_information topic.", self.score)

    # --- UPDATE LOOPS ---
    def update(self, dt):
        self.time += dt
        for popup in self.popups:
            popup["y"] -= 45 * dt
            popup["life"] -= dt
        self.popups = [p for p in self.popups if p["life"] > 0]
        self.flash = max(0.0, self.flash - dt)
        self.shake = max(0.0, self.shake - dt)
        self.update_fx(dt)

        if self.__current_phase == "WELCOME":
            self.update_welcome(dt)
        elif self.__current_phase == "GAME":
            self.update_game(dt)
        elif self.__current_phase == "FINAL":
            self.assembly_time += dt

    def update_welcome(self, dt):
        if len(self.decor) < 9 and random.random() < dt * 2.5:
            kind = random.choice(PART_KINDS + JUNK_KINDS)
            self.decor.append(FallingItem(kind, random.randint(30, WIDTH - 30),
                                          random.uniform(1.0, 2.2), False))
        for item in self.decor:
            item.update(dt)
        self.decor = [i for i in self.decor if not i.off_screen()]

        # Countdown logic to switch from WELCOME to GAME phase
        if self.__user_name and self.welcome_timer > 0:
            self.welcome_timer -= dt
            if self.welcome_timer <= 0:
                self.transition_to_game_phase()

    def update_game(self, dt):
        if self.paused:
            return

        # Direction from /keyboard_control topic or local keyboard fallback
        dir_x, dir_y = 0, 0
        # Keep each ROS direction active long enough to bridge the terminal's
        # initial key-repeat delay. Repeated key events refresh this timer.
        if self.__control_command_timer > 0.0:
            if self.__control_command == "LEFT":
                dir_x = -ROS_CONTROL_STRENGTH
            elif self.__control_command == "RIGHT":
                dir_x = ROS_CONTROL_STRENGTH
            elif self.__control_command == "UP":
                dir_y = -ROS_CONTROL_STRENGTH
            elif self.__control_command == "DOWN":
                dir_y = ROS_CONTROL_STRENGTH
            self.__control_command_timer = max(0.0, self.__control_command_timer - dt)
        else:
            self.__control_command = ""

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dir_x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dir_x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: dir_y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dir_y = 1

        self.player.move(dt, dir_x, dir_y)

        if self.intro_timer > 0:
            self.intro_timer -= dt
        else:
            self.time_left -= dt
            if self.time_left <= 0:
                self.on_timeout()
                return
            self.update_spawning(dt)

        for item in self.items[:]:
            item.update(dt)
            if item.off_screen():
                self.items.remove(item)
                if not item.wrong:
                    self.on_miss(item)
            elif self.player.hitbox.colliderect(item.hitbox):
                if item.wrong and self.player.invulnerable > 0:
                    continue
                self.items.remove(item)
                self.handle_collision(item)

    def update_spawning(self, dt):
        cfg = self.cfg
        self.spawn_timer -= dt
        self.since_correct += dt
        if self.spawn_timer <= 0:
            if len(self.items) < cfg["max_items"]:
                self.spawn_item()
            self.spawn_timer = cfg["interval"] * random.uniform(0.7, 1.3)
        if self.since_correct > cfg["max_gap"]:
            self.spawn_item(force_correct=True)
            self.spawn_timer = max(self.spawn_timer, 0.25)

    def spawn_item(self, force_correct=False):
        cfg = self.cfg
        speed = cfg["speed"] * random.uniform(0.85, 1.2)
        sway = cfg["sway"]
        dash = random.random() < cfg["dash"]
        if not force_correct and random.random() < cfg["wrong_ratio"]:
            kind = random.choice([k for k in PART_KINDS if k != cfg["kind"]]) if random.random() < 0.4 else random.choice(JUNK_KINDS)
            item = FallingItem(kind, random.randint(60, WIDTH - 60), speed, wrong=True, sway=sway, dash=dash)
        else:
            rare = random.random() < cfg["rare_chance"]
            item = FallingItem(cfg["kind"], random.randint(60, WIDTH - 60), speed, wrong=False, rare=rare, sway=sway, dash=dash)
            self.since_correct = 0.0
        self.items.append(item)

    def on_miss(self, item):
        self.combo = 0
        self.score = max(0, self.score - POINTS_MISS)
        self.misses += 1
        if self.misses >= MISS_LIMIT:
            self.misses = 0
            self.lose_life()

    def on_timeout(self):
        self.combo = 0
        self.lose_life()

    def lose_life(self):
        self.lives -= 1
        self.player.invulnerable = INVULNERABLE_TIME
        self.flash = 0.35
        self.shake = 0.3
        if self.lives <= 0:
            self.transition_to_final_phase()

    def handle_collision(self, item):
        cx, cy = item.rect.center
        if not item.wrong:
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)
            self.score += POINTS_NORMAL
            self.collected += 1
            self.burst(cx, cy, GOLD if item.rare else CYAN, 16)
            if self.collected >= self.cfg["target"]:
                if self.level_index + 1 < NUM_LEVELS:
                    self.start_level(self.level_index + 1)
                else:
                    self.levels_completed = NUM_LEVELS
                    self.transition_to_final_phase()
        else:
            self.combo = 0
            self.score = max(0, self.score - POINTS_PENALTY)
            self.burst(cx, cy, RED, 22)
            self.lose_life()

    # --- GRAPHICAL RENDERING ---
    def draw(self):
        surface = self.canvas
        if self.__current_phase == "WELCOME":
            self.draw_welcome(surface)
        elif self.__current_phase == "GAME":
            self.draw_game(surface)
        elif self.__current_phase == "FINAL":
            self.draw_final(surface)

        self.draw_particles(surface)
        offset = (0, 0)
        if self.shake > 0:
            amount = int(8 * self.shake / 0.3) + 1
            offset = (random.randint(-amount, amount), random.randint(-amount, amount))
        self.screen.fill(BLACK)
        self.screen.blit(self.canvas, offset)
        pygame.display.flip()

    def draw_bg(self, s, red=False):
        acc = LEVEL_ACCENTS[self.level_index] if self.__current_phase == "GAME" else CYAN
        s.blit(self.backgrounds["red" if red else acc], (0, 0))
        for a in self.ambient:
            draw_glow(s, int(a["x"]), int(a["y"]), a["r"], a["color"])

    def burst(self, x, y, color, n=14):
        for _ in range(n):
            ang = random.random() * 6.283
            v = random.uniform(0.3, 1.0) * 230
            self.particles.append(dict(x=x, y=y, vx=math.cos(ang) * v, vy=math.sin(ang) * v - 60,
                                       g=320, life=0.6, max=0.6, color=color, size=4, shape="circle"))

    def update_fx(self, dt):
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += p["g"] * dt
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]

    def draw_particles(self, s):
        for p in self.particles:
            draw_glow(s, int(p["x"]), int(p["y"]), 8, dim(p["color"], 0.6))

    # --- PHASE 1: WELCOME SCREEN ---
    def draw_welcome(self, s):
        self.draw_bg(s)
        for item in self.decor:
            item.draw(s)

        frame = pygame.Rect(90, 80, 620, 150)
        draw_glow(s, WIDTH // 2, 155, 300, dim(MAGENTA, 0.35))
        draw_panel(s, frame, border=hsv(self.time * 0.15), alpha=190, width=2, radius=22)
        draw_rainbow_text(s, "ROBOT FACTORY", FONTS["score"], (WIDTH // 2, 155), self.time)

        box = pygame.Rect(0, 0, 560, 90)
        box.center = (WIDTH // 2, 330)
        draw_panel(s, box, border=CYAN, fill=dim(CYAN, 0.2), radius=18, width=3)
        
        if self.__user_name:
            draw_text(s, f"WELCOME, {self.__user_name.upper()}!", FONTS["h2"], GOLD, (WIDTH // 2, 305))
            secs = max(1, int(math.ceil(self.welcome_timer)))
            draw_text(s, f"Username: {self.__user_username} | Starting game in {secs}s...", FONTS["body"], WHITE, (WIDTH // 2, 345))
        else:
            draw_text(s, "WAITING FOR USER DATA ON TERMINAL...", FONTS["h3"], WHITE, (WIDTH // 2, 330))

        draw_text(s, "Control using terminal node or Arrow Keys", FONTS["small"], MUTED, (WIDTH // 2, 430))

    # --- PHASE 2: GAME SCREEN ---
    def draw_game(self, s):
        self.draw_bg(s)
        for item in self.items:
            item.draw(s)
        self.player.draw(s, self.time)
        self.draw_hud(s)

    def draw_hud(self, s):
        cfg = self.cfg
        acc = LEVEL_ACCENTS[self.level_index]
        draw_panel(s, (10, 10, 236, 52), border=acc)
        s.blit(get_icon(cfg["kind"], 30), (20, 21))
        draw_text(s, f"PLAYER: {self.__user_name if self.__user_name else 'Player'}", FONTS["small"], WHITE, (135, 26))
        draw_text(s, f"LEVEL {self.level_index + 1} — {cfg['name']}", FONTS["small"], CYAN, (135, 42))

        draw_panel(s, (256, 10, 150, 52), border=GOLD)
        draw_text(s, f"SCORE: {self.score}", FONTS["body"], GOLD, (331, 36))

        draw_panel(s, (416, 10, 160, 52), border=RED)
        draw_text(s, "LIVES:", FONTS["body"], WHITE, (426, 36), "midleft")
        for i in range(START_LIVES):
            draw_heart(s, 512 + i * 24, 33, 5, RED, filled=i < self.lives)

        draw_panel(s, (586, 10, 204, 52), border=GREEN)
        draw_text(s, f"{cfg['name']}: {self.collected}/{cfg['target']}", FONTS["body"], WHITE, (688, 36))

    # --- PHASE 3: FINAL SCREEN ---
    def draw_final(self, s):
        self.draw_bg(s, red=self.lives <= 0)
        
        # Explicit Phase 3 Header Banner as specified in requirements
        header_box = pygame.Rect(140, 20, 520, 85)
        draw_glow(s, WIDTH // 2, 60, 250, dim(GOLD if self.lives > 0 else RED, 0.4))
        draw_panel(s, header_box, border=GOLD if self.lives > 0 else RED, alpha=240, width=3, radius=20)
        draw_text(s, "PHASE 3 — FINAL", FONTS["h2"], GOLD, (WIDTH // 2, 45))
        title_text = "ROBOT COMPLETED!" if self.lives > 0 else "GAME OVER"
        draw_rainbow_text(s, title_text, FONTS["h1"], (WIDTH // 2, 78), self.time)

        # Player profile and score panel
        info_box = pygame.Rect(180, 120, 440, 130)
        draw_panel(s, info_box, border=CYAN, fill=PANEL_FILL, alpha=235, radius=18)
        
        uname = self.__user_username if self.__user_username else "player01"
        uage = self.__user_age if self.__user_age > 0 else "--"
        draw_text(s, f"Score: {self.score}", FONTS["score"], GOLD, (WIDTH // 2, 155))
        draw_text(s, f"Username: {uname}  •  Age: {uage}", FONTS["body"], WHITE, (WIDTH // 2, 195))
        
        # ROS 1 Communication Status confirmation badge
        draw_panel(s, (WIDTH // 2 - 180, 215, 360, 28), border=GREEN, fill=(10, 40, 20), alpha=230, radius=10)
        draw_text(s, "✓ Result published to /result_information", FONTS["small"], GREEN, (WIDTH // 2, 229))

        # Visual illustration below
        if self.lives > 0:
            draw_robot(s, 270, 265, self.assembly_time)
        else:
            sprite = pygame.Surface((Player.WIDTH, Player.HEIGHT), pygame.SRCALPHA)
            draw_player_sprite(sprite, sprite.get_rect(), dead=True)
            sprite = pygame.transform.rotate(sprite, 70)
            s.blit(sprite, sprite.get_rect(center=(WIDTH // 2, 380)))

    # --- MAIN LOOP ---
    def run(self):
        while not rospy.is_shutdown():
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    rospy.signal_shutdown("Pygame window closed")
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    rospy.signal_shutdown("ESC key pressed")

            self.update(dt)
            self.draw()

        pygame.quit()


if __name__ == '__main__':
    try:
        node = GameNode()
        node.run()
    except rospy.ROSInterruptException:
        pass
