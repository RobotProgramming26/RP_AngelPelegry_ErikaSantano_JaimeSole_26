"""
ROBOT FACTORY  -  HARD EDITION
==============================
Juego arcade de piezas que caen, hecho con Python + Pygame.

Objetivo
--------
Mueve el robot morado de izquierda a derecha para atrapar SOLO las piezas
correctas de cada nivel. Completa los 7 niveles para montar el robot final.

MODO EXTREMO - que lo hace mas dificil
--------------------------------------
    * Caida muy rapida y muchos mas objetos incorrectos (hasta 80 %).
    * Piezas trampa parecidas a las correctas, sin aviso visual.
    * BOMBAS: quitan una vida, puntos y 3 segundos de tiempo.
    * Objetos con zigzag y objetos que aceleran (dash) a mitad de caida.
    * OLEADAS: filas de objetos peligrosos con un unico hueco libre.
    * El robot tiene inercia: resbala al frenar.
    * Tiempo limite corto por nivel; si se acaba pierdes una vida y repites.
    * 3 piezas correctas perdidas = pierdes una vida.
    * COMBO: encadena aciertos para multiplicar los puntos (hasta x5);
      cualquier error lo reinicia.

Niveles
-------
    1. SENSORS (5)   2. CABLES (7)    3. CIRCUITS (6)   4. BATTERIES (6)
    5. ARMS (5)      6. LEGS (5)      7. CORE (4)

Controles
---------
    IZQUIERDA / DERECHA (o A / D) : mover
    ENTER / ESPACIO               : elegir boton
    P                             : pausa
    ESC                           : salir

Requisitos
----------
    pip install pygame
    python game.py
"""

import colorsys
import math
import random
import sys

import pygame

# =============================================================================
# 1. CONSTANTES Y CONFIGURACION DE NIVELES
# =============================================================================

WIDTH, HEIGHT = 800, 600
FPS = 60
FLOOR_Y = HEIGHT - 44

# --- Colores ---
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

PURPLE = (150, 70, 230)          # El jugador DEBE ser morado
PURPLE_LIGHT = (195, 145, 255)
PURPLE_DARK = (95, 45, 165)

# --- Jugabilidad ---
START_LIVES = 3
POINTS_NORMAL = 10
POINTS_RARE = 25
POINTS_LEVEL = 50
POINTS_PENALTY = 25              # Al atrapar un objeto incorrecto
POINTS_MISS = 8                  # Al dejar caer una pieza correcta
MISS_LIMIT = 3                   # Piezas perdidas = 1 vida
RARE_TIME_BONUS = 1.5            # Segundos extra al coger una pieza dorada
BOMB_TIME_PENALTY = 3.0          # Segundos que quita una bomba
PLAYER_ACCEL = 2.4               # El robot tiene inercia (resbala al frenar)
PLAYER_FRICTION = 0.80
PLAYER_MAX_SPEED = 9.5
INVULNERABLE_TIME = 0.9
LEVEL_INTRO_TIME = 2.2
LEVEL_COMPLETE_TIME = 2.8
COMBO_STEP = 3                   # Cada 3 aciertos seguidos sube el multiplicador
WAVE_EVERY = (7.0, 10.0)         # Segundos entre oleadas (desde el nivel 2)

MAGENTA = (255, 70, 200)
NEON = [CYAN, MAGENTA, GOLD, GREEN, (150, 110, 255), ORANGE]
# Cada nivel tiene su propio color de ambiente
LEVEL_ACCENTS = [CYAN, MAGENTA, GREEN, (100, 150, 255), ORANGE,
                 (190, 120, 255), GOLD]

# Cada nivel es mas duro:
#   speed / interval / max_items / wrong_ratio / rare_chance / max_gap / time
#   sway : probabilidad de zigzag      dash : probabilidad de acelerar a mitad
LEVELS = [
    dict(name="SENSORS",   kind="sensor",  target=5, speed=2.9, interval=0.90,
         max_items=9,  wrong_ratio=0.50, rare_chance=0.06, max_gap=4.5,
         time=35, sway=0.20, dash=0.00),
    dict(name="CABLES",    kind="cable",   target=7, speed=3.5, interval=0.75,
         max_items=10, wrong_ratio=0.56, rare_chance=0.07, max_gap=4.5,
         time=40, sway=0.30, dash=0.10),
    dict(name="CIRCUITS",  kind="circuit", target=6, speed=4.1, interval=0.62,
         max_items=11, wrong_ratio=0.62, rare_chance=0.08, max_gap=4.3,
         time=40, sway=0.40, dash=0.20),
    dict(name="BATTERIES", kind="battery", target=6, speed=4.7, interval=0.52,
         max_items=12, wrong_ratio=0.67, rare_chance=0.09, max_gap=4.2,
         time=40, sway=0.50, dash=0.30),
    dict(name="ARMS",      kind="arm",     target=5, speed=5.4, interval=0.44,
         max_items=13, wrong_ratio=0.72, rare_chance=0.10, max_gap=4.0,
         time=38, sway=0.60, dash=0.35),
    dict(name="LEGS",      kind="leg",     target=5, speed=6.1, interval=0.37,
         max_items=14, wrong_ratio=0.76, rare_chance=0.11, max_gap=4.0,
         time=38, sway=0.70, dash=0.40),
    dict(name="CORE",      kind="core",    target=4, speed=6.9, interval=0.31,
         max_items=15, wrong_ratio=0.80, rare_chance=0.12, max_gap=3.8,
         time=38, sway=0.80, dash=0.45),
]
NUM_LEVELS = len(LEVELS)

PART_KINDS = [lvl["kind"] for lvl in LEVELS]
JUNK_KINDS = ["crate", "gear", "bomb"]

# Color de la estela de cada objeto
TRAIL_COLORS = {
    "sensor": CYAN, "cable": (190, 110, 255), "circuit": GREEN,
    "battery": (70, 130, 255), "arm": PURPLE_LIGHT, "leg": PURPLE_LIGHT,
    "core": CYAN, "crate": RED, "gear": (190, 195, 215),
    "bomb": ORANGE,
}

STATE_START = "start"
STATE_PLAYING = "playing"
STATE_LEVEL_COMPLETE = "level_complete"
STATE_VICTORY = "victory"
STATE_GAME_OVER = "game_over"

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
# 2. FUNCIONES DE DIBUJO
# =============================================================================

def draw_text(surface, text, font, color, pos, anchor="center", shadow=True):
    image = font.render(text, True, color)
    rect = image.get_rect(**{anchor: pos})
    if shadow:
        surface.blit(font.render(text, True, BLACK), rect.move(2, 2))
    surface.blit(image, rect)
    return rect


_panel_cache = {}


def draw_panel(surface, rect, border=CYAN, fill=PANEL_FILL, alpha=215,
               radius=12, width=2):
    """Panel tecnologico con esquinas cortadas y borde de neon brillante."""
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
        # Brillo suave en la parte superior del panel
        shine = pygame.Surface((w - 2 * cut, max(4, h // 3)), pygame.SRCALPHA)
        shine.fill((*border, 14))
        surf.blit(shine, (pad + cut, pad + 3))
        # Borde con resplandor (3 capas)
        pygame.draw.polygon(surf, (*border, 35), pts, width + 6)
        pygame.draw.polygon(surf, (*border, 90), pts, width + 3)
        pygame.draw.polygon(surf, border, pts, width)
        # Pequenos detalles de esquina
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
    """Estela vertical que se desvanece hacia arriba (como en la imagen)."""
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
    """Texto cuyas letras cambian de color y ondulan."""
    widths = [font.size(c)[0] for c in text]
    x = center[0] - sum(widths) // 2
    for i, ch in enumerate(text):
        y = center[1] + int(3 * math.sin(t * 3 + i * 0.6))
        draw_text(surface, ch, font, hsv(t * speed + i * 0.06), (x, y),
                  "midleft")
        x += widths[i]


def draw_bomb(s, cx, cy, t):
    """WRONG: bomba con mecha chispeante."""
    pygame.draw.circle(s, (38, 38, 54), (cx, cy + 3), 16)
    pygame.draw.circle(s, (255, 120, 40), (cx, cy + 3), 16, 2)
    pygame.draw.circle(s, (120, 125, 150), (cx - 6, cy - 2), 3)
    pygame.draw.line(s, (200, 170, 120), (cx + 6, cy - 10), (cx + 12, cy - 17), 3)
    spark = (255, 255, 120) if int(t * 12) % 2 else (255, 90, 40)
    draw_glow(s, cx + 13, cy - 18, 10, spark)
    pygame.draw.circle(s, spark, (cx + 13, cy - 18), 3)


def build_background(accent=CYAN, red=False):
    """Almacen de fabrica oscuro con luces de neon, cajas y suelo en
    perspectiva. Se pre-renderiza una sola vez."""
    bg = pygame.Surface((WIDTH, HEIGHT))
    top = (22, 8, 14) if red else (5, 10, 22)
    bot = (34, 12, 20) if red else (9, 22, 38)
    for y in range(HEIGHT):
        t = y / HEIGHT
        pygame.draw.line(bg, tuple(int(top[i] + (bot[i] - top[i]) * t)
                                   for i in range(3)), (0, y), (WIDTH, y))
    draw_glow(bg, WIDTH // 2, 340, 330, dim(accent, 0.22))

    grid = (44, 16, 24) if red else (14, 30, 46)
    for x in range(0, WIDTH, 40):
        pygame.draw.line(bg, grid, (x, 0), (x, FLOOR_Y))
    for y in range(0, FLOOR_Y, 40):
        pygame.draw.line(bg, grid, (0, y), (WIDTH, y))

    # Barras de neon en las paredes
    for x in (14, 786):
        draw_glow(bg, x, 190, 70, dim(accent, 0.6))
        pygame.draw.rect(bg, accent, (x - 2, 120, 4, 140))
    for y, x0 in ((215, 0), (260, 740)):
        draw_glow(bg, x0 + 30, y, 50, dim(accent, 0.5))
        pygame.draw.rect(bg, accent, (x0, y - 2, 60, 4))

    # Lamparas de techo multicolor con rayos de luz
    for i, x in enumerate(range(70, WIDTH, 110)):
        col = accent if i % 3 == 0 else NEON[(i + 1) % len(NEON)]
        if red:
            col = RED if i % 2 == 0 else ORANGE
        cone = pygame.Surface((WIDTH, 330), pygame.SRCALPHA)
        pygame.draw.polygon(cone, (*col, 16), [(x - 10, 0), (x + 10, 0),
                                               (x + 70, 320), (x - 70, 320)])
        bg.blit(cone, (0, 0))
        draw_glow(bg, x, 4, 46, dim(col, 0.7))
        pygame.draw.rect(bg, col, (x - 18, 0, 36, 5), border_radius=2)

    # Pilas de cajas a los lados
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
                pygame.draw.rect(bg, dim(accent, 0.75),
                                 (box.x + 6, box.y + 8, box.w - 12, 3))
            if rng.random() < 0.35:
                pygame.draw.circle(bg, ORANGE if rng.random() < 0.5 else GOLD,
                                   (box.right - 8, box.bottom - 8), 2)
            y -= h

    # Suelo en perspectiva
    pygame.draw.rect(bg, (12, 18, 30) if not red else (26, 10, 16),
                     (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y))
    line_col = dim(accent, 0.28)
    for i in range(-10, 11):
        pygame.draw.line(bg, line_col, (WIDTH // 2 + i * 70, FLOOR_Y),
                         (WIDTH // 2 + i * 150, HEIGHT))
    for dy in (9, 21, 35):
        pygame.draw.line(bg, line_col, (0, FLOOR_Y + dy),
                         (WIDTH, FLOOR_Y + dy))
    pygame.draw.line(bg, dim(accent, 0.35), (0, FLOOR_Y - 1),
                     (WIDTH, FLOOR_Y - 1), 3)
    pygame.draw.line(bg, accent, (0, FLOOR_Y), (WIDTH, FLOOR_Y), 2)
    for x0 in (25, 600):
        draw_glow(bg, x0 + 90, FLOOR_Y + 22, 60, dim(accent, 0.6))
        pygame.draw.rect(bg, accent, (x0, FLOOR_Y + 20, 180, 5))
    return bg


# =============================================================================
# 3. DIBUJO DE OBJETOS
# =============================================================================

def draw_sensor(s, cx, cy, t):
    pygame.draw.circle(s, (30, 40, 60), (cx, cy), 18)
    pygame.draw.circle(s, CYAN, (cx, cy), 18, 3)
    pygame.draw.circle(s, (15, 18, 28), (cx, cy), 10)
    pygame.draw.circle(s, CYAN, (cx, cy), 6)
    pygame.draw.circle(s, WHITE, (cx - 2, cy - 3), 2)


def draw_cable(s, cx, cy, t):
    pts = [(cx - 20 + i * 2, cy + int(8 * math.sin(i * 0.5 + t * 3)))
           for i in range(21)]
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
        pygame.draw.line(s, (130, 255, 170), (cx + dx * 7, cy + dy * 7),
                         (cx + dx * 17, cy + dy * 17), 2)
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
    pygame.draw.polygon(s, GOLD, [(cx + 2, cy - 10), (cx - 6, cy + 4),
                                  (cx - 1, cy + 4), (cx - 3, cy + 14),
                                  (cx + 6, cy - 2), (cx + 1, cy - 2)])


def draw_arm(s, cx, cy, t):
    pygame.draw.rect(s, STEEL, (cx - 22, cy - 7, 44, 14), border_radius=6)
    pygame.draw.rect(s, PURPLE, (cx - 8, cy - 7, 16, 14))
    pygame.draw.rect(s, (110, 120, 145), (cx - 22, cy - 7, 44, 14), 2,
                     border_radius=6)
    for dx in (-16, 16):
        pygame.draw.circle(s, (110, 120, 145), (cx + dx, cy), 7)
        pygame.draw.circle(s, (50, 55, 75), (cx + dx, cy), 3)


def draw_leg(s, cx, cy, t):
    pygame.draw.rect(s, STEEL, (cx - 7, cy - 22, 14, 32), border_radius=5)
    pygame.draw.rect(s, PURPLE, (cx - 7, cy - 8, 14, 12))
    pygame.draw.rect(s, (110, 120, 145), (cx - 7, cy - 22, 14, 32), 2,
                     border_radius=5)
    pygame.draw.circle(s, (110, 120, 145), (cx, cy - 18), 8)
    pygame.draw.circle(s, (50, 55, 75), (cx, cy - 18), 3)
    pygame.draw.rect(s, PURPLE_DARK, (cx - 13, cy + 10, 26, 10),
                     border_radius=4)


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
            pts.append((cx + rad * math.cos(base + da),
                        cy + rad * math.sin(base + da)))
    pygame.draw.polygon(s, (90, 95, 108), pts)
    pygame.draw.polygon(s, (225, 70, 70), pts, 2)
    pygame.draw.circle(s, (90, 95, 108), (cx, cy), 12)
    pygame.draw.circle(s, (225, 70, 70), (cx, cy), 12, 2)
    pygame.draw.circle(s, (20, 22, 30), (cx, cy), 5)


DRAWERS = {
    "sensor": draw_sensor, "cable": draw_cable, "circuit": draw_circuit,
    "battery": draw_battery, "arm": draw_arm, "leg": draw_leg,
    "core": draw_core, "crate": draw_crate, "gear": draw_gear,
    "bomb": draw_bomb,
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
# 4. CLASES
# =============================================================================

class FallingItem:
    """Objeto que cae. Puede hacer zigzag (sway) o acelerar (dash)."""

    SIZE = 44

    def __init__(self, kind, x, speed, wrong, rare=False, sway=0.0,
                 dash=False):
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
        self.cur_speed = self.speed * (1.7 if self.dash and
                                       self.y > self.dash_y else 1.0)
        self.y += self.cur_speed * dt * FPS
        self.rect.y = int(self.y)
        self.age += dt
        if self.amp:
            x = self.base_x + self.amp * math.sin(self.age * self.freq
                                                  + self.phase)
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
            draw_star(surface, cx + 17, cy - 17,
                      5 + int(2 * math.sin(self.age * 10)), GOLD)


def draw_player(surface, rect, dead=False):
    """Robot MORADO (64 x 48)."""
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
    pygame.draw.rect(surface, (15, 18, 35), (x + 18, y + 5, 28, 14),
                     border_radius=5)
    for ex in (26, 38):
        if dead:
            pygame.draw.line(surface, CYAN, (ex + x - 3, y + 8),
                             (ex + x + 3, y + 16), 2)
            pygame.draw.line(surface, CYAN, (ex + x - 3, y + 16),
                             (ex + x + 3, y + 8), 2)
        else:
            pygame.draw.rect(surface, CYAN, (x + ex - 2, y + 8, 4, 8),
                             border_radius=2)
    pygame.draw.circle(surface, PURPLE_DARK, (x + 11, y + 12), 4)
    pygame.draw.circle(surface, PURPLE_DARK, (x + 53, y + 12), 4)


class Player:
    """Robot morado con inercia."""

    WIDTH = 64
    HEIGHT = 48

    def __init__(self):
        self.rect = pygame.Rect(0, 0, self.WIDTH, self.HEIGHT)
        self.x = 0.0
        self.vx = 0.0
        self.invulnerable = 0.0
        self.reset()

    def reset(self):
        self.x = WIDTH / 2 - self.WIDTH / 2
        self.vx = 0.0
        self.rect.x = int(self.x)
        self.rect.bottom = FLOOR_Y + 2
        self.invulnerable = 0.0

    @property
    def hitbox(self):
        return self.rect.inflate(-10, -4)

    def move(self, dt, direction):
        f = dt * FPS
        self.vx += direction * PLAYER_ACCEL * f
        self.vx *= PLAYER_FRICTION ** f
        self.vx = max(-PLAYER_MAX_SPEED, min(PLAYER_MAX_SPEED, self.vx))
        self.x += self.vx * f
        if self.x < 0:
            self.x, self.vx = 0.0, 0.0
        elif self.x > WIDTH - self.WIDTH:
            self.x, self.vx = float(WIDTH - self.WIDTH), 0.0
        self.rect.x = int(self.x)
        if self.invulnerable > 0:
            self.invulnerable -= dt

    def draw(self, surface, t=0.0):
        cx = self.rect.centerx
        pulse = 0.75 + 0.25 * math.sin(t * 5)
        draw_glow(surface, cx, self.rect.centery + 4, 62,
                  dim((180, 90, 255), pulse))
        pygame.draw.ellipse(surface, (70, 30, 120),
                            (cx - 30, FLOOR_Y + 1, 60, 9))
        if self.invulnerable > 0 and int(self.invulnerable * 12) % 2 == 0:
            return
        draw_player(surface, self.rect)


class Button:
    def __init__(self, label, action, rect, color=CYAN):
        self.label = label
        self.action = action
        self.rect = pygame.Rect(rect)
        self.color = color

    def draw(self, surface, selected):
        c = self.color
        if selected:
            draw_glow(surface, *self.rect.center, 125, dim(c, 0.65))
            draw_panel(surface, self.rect, border=c, fill=dim(c, 0.38),
                       alpha=245, radius=14, width=3)
            color = WHITE
        else:
            draw_panel(surface, self.rect, border=dim(c, 0.65),
                       fill=dim(c, 0.12), alpha=230, radius=14, width=2)
            color = tuple((v + 255) // 2 for v in c)
        draw_text(surface, self.label, FONTS["h3"], color, self.rect.center)


# =============================================================================
# 5. ROBOT FINAL (pantalla de victoria)
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
        pygame.draw.rect(s, PURPLE_LIGHT, (x - 6, 302, 38, 16),
                         border_radius=6)


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
    pygame.draw.line(s, (130, 255, 170), (118, 126), (104, 126), 2)
    pygame.draw.line(s, (130, 255, 170), (142, 126), (156, 126), 2)


def part_battery(s):
    body = pygame.Rect(150, 162, 22, 46)
    pygame.draw.rect(s, STEEL, (156, 157, 10, 6), border_radius=2)
    pygame.draw.rect(s, (40, 110, 230), body, border_radius=4)
    pygame.draw.rect(s, (150, 195, 255), body, 2, border_radius=4)
    pygame.draw.polygon(s, GOLD, [(162, 170), (155, 187), (160, 187),
                                  (158, 202), (167, 183), (162, 183)])


def part_cables(s):
    for x in (112, 148):
        pygame.draw.lines(s, ORANGE, False,
                          [(x, 78), (x + 5, 84), (x - 5, 89), (x, 96)], 4)
    pygame.draw.lines(s, ORANGE, False,
                      [(104, 148), (98, 162), (108, 176), (116, 184)], 4)
    pygame.draw.lines(s, ORANGE, False,
                      [(145, 188), (148, 186), (150, 188)], 3)


def part_arms(s):
    for side in (0, 1):
        def mx(v):
            return v if side == 0 else ROBOT_W - v
        pygame.draw.circle(s, STEEL, (mx(64), 112), 15)
        pygame.draw.rect(s, PURPLE, (mx(64) - 12, 118, 24, 50),
                         border_radius=8)
        pygame.draw.circle(s, STEEL, (mx(64), 172), 11)
        pygame.draw.rect(s, STEEL, (mx(64) - 10, 172, 20, 46),
                         border_radius=8)
        pygame.draw.rect(s, PURPLE_LIGHT, (mx(64) - 10, 184, 20, 10))
        pygame.draw.circle(s, PURPLE_LIGHT, (mx(64), 226), 13)
        pygame.draw.circle(s, PURPLE_DARK, (mx(64), 226), 13, 2)


def part_head(s):
    pygame.draw.line(s, STEEL, (130, 12), (130, 2), 3)
    pygame.draw.circle(s, RED, (130, 3), 4)
    for x in (80, 180):
        pygame.draw.circle(s, PURPLE, (x, 46), 9)
    pygame.draw.rect(s, (228, 230, 245), (82, 12, 96, 70), border_radius=16)
    pygame.draw.rect(s, STEEL, (82, 12, 96, 70), 3, border_radius=16)
    pygame.draw.rect(s, (22, 26, 44), (91, 24, 78, 44), border_radius=10)


def part_sensors(s):
    for x in (112, 148):
        draw_glow(s, x, 46, 18, CYAN)
        pygame.draw.circle(s, (15, 18, 28), (x, 46), 12)
        pygame.draw.circle(s, CYAN, (x, 46), 12, 3)
        pygame.draw.circle(s, CYAN, (x, 46), 6)
        pygame.draw.circle(s, WHITE, (x - 2, 44), 2)


def part_core(s):
    draw_glow(s, 130, 186, 38, CYAN)
    pygame.draw.circle(s, (0, 170, 200), (130, 186), 17)
    pygame.draw.circle(s, (160, 250, 255), (130, 186), 12)
    pygame.draw.circle(s, WHITE, (130, 186), 5)
    pygame.draw.circle(s, CYAN, (130, 186), 18, 2)


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
        if progress <= 0:
            continue
        progress = min(progress, 1.0)
        eased = 1 - (1 - progress) ** 3
        part = get_robot_part(name, func)
        part.set_alpha(int(255 * eased))
        surface.blit(part, (left + offset[0] * (1 - eased),
                            top + offset[1] * (1 - eased)))


# =============================================================================
# 6. CLASE GAME
# =============================================================================

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Robot Factory - Extreme Edition")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        load_fonts()
        self.backgrounds = {a: build_background(a) for a in LEVEL_ACCENTS}
        self.backgrounds["red"] = build_background(RED, red=True)
        self.particles = []
        self.ambient = [dict(x=random.randint(0, WIDTH),
                             y=random.randint(0, HEIGHT),
                             vy=random.uniform(8, 30),
                             r=random.choice((4, 5, 6, 8)),
                             color=dim(random.choice(NEON), 0.55),
                             ph=random.random() * 6.28) for _ in range(38)]

        self.running = True
        self.time = 0.0
        self.state = STATE_START
        self.player = Player()
        self.decor = []
        self.buttons = []
        self.selected = 0
        self.paused = False
        self.assembly_time = 0.0
        self.time_bonus = 0
        self.reset_game()

    @property
    def cfg(self):
        return LEVELS[self.level_index]

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
        self.state_timer = 0.0
        self.player.reset()

    def make_buttons(self, y):
        self.buttons = [
            Button("PLAY AGAIN", "play", (190, y, 200, 52), GREEN),
            Button("EXIT", "exit", (410, y, 200, 52), RED),
        ]
        self.selected = 0

    def activate(self, action):
        if action == "play":
            self.reset_game()
            self.state = STATE_PLAYING
        elif action == "exit":
            self.running = False

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            elif self.state == STATE_START:
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    self.reset_game()
                    self.state = STATE_PLAYING
            elif self.state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.paused = not self.paused
            elif self.state == STATE_VICTORY and \
                    self.assembly_time < ASSEMBLY_TOTAL:
                if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_RETURN, pygame.K_SPACE):
                    self.assembly_time = ASSEMBLY_TOTAL
            elif self.state in (STATE_VICTORY, STATE_GAME_OVER):
                self.handle_menu_event(event)

    def handle_menu_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(self.buttons)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(self.buttons)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.activate(self.buttons[self.selected].action)
        elif event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    self.activate(button.action)

    # ------------------------------------------------------------------
    # Logica
    # ------------------------------------------------------------------
    def update(self, dt):
        self.time += dt
        for popup in self.popups:
            popup["y"] -= 45 * dt
            popup["life"] -= dt
        self.popups = [p for p in self.popups if p["life"] > 0]
        self.flash = max(0.0, self.flash - dt)
        self.shake = max(0.0, self.shake - dt)
        self.update_fx(dt)

        if self.state == STATE_START:
            self.update_start(dt)
        elif self.state == STATE_PLAYING:
            self.update_playing(dt)
        elif self.state == STATE_LEVEL_COMPLETE:
            self.update_level_complete(dt)
        elif self.state == STATE_VICTORY:
            self.assembly_time += dt

    def update_start(self, dt):
        if len(self.decor) < 9 and random.random() < dt * 2.5:
            kind = random.choice(PART_KINDS + JUNK_KINDS)
            self.decor.append(FallingItem(kind, random.randint(30, WIDTH - 30),
                                          random.uniform(1.0, 2.2), False))
        for item in self.decor:
            item.update(dt)
        self.decor = [i for i in self.decor if not i.off_screen()]

    def update_playing(self, dt):
        if self.paused:
            return

        keys = pygame.key.get_pressed()
        direction = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - \
                    (keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.player.move(dt, direction)

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
                    if self.state != STATE_PLAYING:
                        break
            elif self.player.hitbox.colliderect(item.hitbox):
                if item.wrong and self.player.invulnerable > 0:
                    continue
                self.items.remove(item)
                self.handle_collision(item)
                if self.state != STATE_PLAYING:
                    break

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
        if self.level_index >= 1:                      # Oleadas
            self.wave_timer -= dt
            self.wave_warn = 0 < self.wave_timer < 1.2
            if self.wave_timer <= 0:
                self.spawn_wave()
                self.wave_timer = max(4.0, random.uniform(*WAVE_EVERY)
                                      - 0.5 * self.level_index)

    def spawn_wave(self):
        """Una fila de objetos peligrosos con un unico hueco libre."""
        cfg = self.cfg
        gap = random.randint(110, WIDTH - 110)
        speed = cfg["speed"] * 0.95
        others = [k for k in PART_KINDS if k != cfg["kind"]]
        for x in range(40, WIDTH - 30, 64):
            if abs(x - gap) < 72:
                continue
            kind = random.choice(others) if random.random() < 0.3 \
                else random.choice(JUNK_KINDS)
            self.items.append(FallingItem(kind, x, speed, wrong=True))
        if random.random() < 0.75:                    # Premio en el hueco
            self.items.append(FallingItem(cfg["kind"], gap, speed,
                                          wrong=False))
            self.since_correct = 0.0

    def spawn_item(self, force_correct=False):
        cfg = self.cfg
        speed = cfg["speed"] * random.uniform(0.85, 1.2)
        sway = cfg["sway"]
        dash = random.random() < cfg["dash"]
        if not force_correct and random.random() < cfg["wrong_ratio"]:
            decoy_chance = 0.30 + 0.06 * self.level_index
            if random.random() < decoy_chance:
                kind = random.choice([k for k in PART_KINDS
                                      if k != cfg["kind"]])
            else:
                kind = random.choice(JUNK_KINDS)
            item = FallingItem(kind, self.pick_spawn_x(), speed, wrong=True,
                               sway=sway, dash=dash)
        else:
            rare = random.random() < cfg["rare_chance"]
            item = FallingItem(cfg["kind"], self.pick_spawn_x(), speed,
                               wrong=False, rare=rare, sway=sway, dash=dash)
            self.since_correct = 0.0
        self.items.append(item)

    def pick_spawn_x(self):
        x = random.randint(60, WIDTH - 60)
        for _ in range(12):
            x = random.randint(60, WIDTH - 60)
            if all(i.rect.top > 60 or abs(i.base_x - x) >= 52
                   for i in self.items):
                break
        return x

    def add_popup(self, text, pos, color):
        self.popups.append(dict(text=text, x=pos[0], y=pos[1], life=1.0,
                                color=color))

    def lose_life(self):
        """Resta una vida. Devuelve True si fue Game Over."""
        self.lives -= 1
        self.player.invulnerable = INVULNERABLE_TIME
        self.flash = 0.35
        self.shake = 0.3
        if self.lives <= 0:
            self.state = STATE_GAME_OVER
            self.make_buttons(420)
            return True
        return False

    def multiplier(self):
        return min(5, 1 + self.combo // COMBO_STEP)

    def on_miss(self, item):
        """Una pieza correcta se cayo al suelo."""
        self.combo = 0
        self.score = max(0, self.score - POINTS_MISS)
        self.misses += 1
        self.burst(item.rect.centerx, FLOOR_Y, ORANGE, 8, size=4)
        self.add_popup("MISS", (item.rect.centerx, FLOOR_Y - 30), ORANGE)
        if self.misses >= MISS_LIMIT:
            self.misses = 0
            self.add_popup("-1 LIFE", (WIDTH // 2, 300), RED)
            self.lose_life()

    def on_timeout(self):
        self.combo = 0
        self.add_popup("TIME UP!", (WIDTH // 2, 300), RED)
        if not self.lose_life():
            self.start_level(self.level_index)

    def handle_collision(self, item):
        cx, cy = item.rect.center
        if not item.wrong:
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)
            mult = self.multiplier()
            points = (POINTS_RARE if item.rare else POINTS_NORMAL) * mult
            self.score += points
            self.collected += 1
            label = f"+{points}" + (f"  x{mult}" if mult > 1 else "")
            self.add_popup(label, item.rect.midtop,
                           GOLD if item.rare else GREEN)
            self.burst(cx, cy, GOLD if item.rare else TRAIL_COLORS[item.kind],
                       30 if item.rare else 16)
            if item.rare:
                self.time_left = min(self.cfg["time"],
                                     self.time_left + RARE_TIME_BONUS)
                self.add_popup(f"+{RARE_TIME_BONUS:g}s",
                               (cx, item.rect.top - 24), CYAN)
            if self.collected >= self.cfg["target"]:
                self.complete_level()
        else:
            self.combo = 0
            bomb = item.kind == "bomb"
            self.score = max(0, self.score - POINTS_PENALTY
                             - (25 if bomb else 0))
            self.add_popup("BOOM!" if bomb else f"-{POINTS_PENALTY}",
                           item.rect.midtop, RED)
            self.burst(cx, cy, ORANGE if bomb else RED, 44 if bomb else 22,
                       size=7)
            if bomb:
                self.time_left = max(1.0, self.time_left - BOMB_TIME_PENALTY)
                self.add_popup(f"-{BOMB_TIME_PENALTY:g}s",
                               (cx, item.rect.top - 24), RED)
            if not self.lose_life() and bomb:
                self.shake = 0.5

    def complete_level(self):
        self.time_bonus = int(self.time_left) * 2
        self.score += POINTS_LEVEL + self.time_bonus
        self.levels_completed = self.level_index + 1
        self.items = []
        self.state = STATE_LEVEL_COMPLETE
        self.state_timer = 0.0
        self.confetti(WIDTH // 2, 300, 90)

    def update_level_complete(self, dt):
        self.state_timer += dt
        if self.state_timer < LEVEL_COMPLETE_TIME:
            return
        if self.level_index + 1 >= NUM_LEVELS:
            self.state = STATE_VICTORY
            self.assembly_time = 0.0
            self.make_buttons(522)
        else:
            self.start_level(self.level_index + 1)
            self.state = STATE_PLAYING

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def draw(self):
        surface = self.canvas
        if self.state == STATE_START:
            self.draw_start(surface)
        elif self.state == STATE_PLAYING:
            self.draw_playing(surface)
        elif self.state == STATE_LEVEL_COMPLETE:
            self.draw_level_complete(surface)
        elif self.state == STATE_VICTORY:
            self.draw_victory(surface)
        elif self.state == STATE_GAME_OVER:
            self.draw_game_over(surface)

        self.draw_particles(surface)
        offset = (0, 0)
        if self.shake > 0:
            amount = int(8 * self.shake / 0.3) + 1
            offset = (random.randint(-amount, amount),
                      random.randint(-amount, amount))
        self.screen.fill(BLACK)
        self.screen.blit(self.canvas, offset)
        pygame.display.flip()

    # ---------- Efectos visuales ----------
    @property
    def accent(self):
        if self.state in (STATE_PLAYING, STATE_LEVEL_COMPLETE):
            return LEVEL_ACCENTS[self.level_index]
        return CYAN

    def draw_bg(self, s, red=False):
        s.blit(self.backgrounds["red" if red else self.accent], (0, 0))
        for a in self.ambient:                       # Luciérnagas de neon
            draw_glow(s, int(a["x"]), int(a["y"]), a["r"], a["color"])

    def burst(self, x, y, color, n=14, speed=230, size=5):
        for _ in range(n):
            ang = random.random() * 6.283
            v = random.uniform(0.3, 1.0) * speed
            life = random.uniform(0.4, 0.9)
            self.particles.append(dict(
                x=x, y=y, vx=math.cos(ang) * v, vy=math.sin(ang) * v - 60,
                g=320, life=life, max=life, color=color,
                size=random.uniform(2, size), shape="circle"))

    def confetti(self, x, y, n=60, fall=False):
        for _ in range(n):
            life = random.uniform(1.6, 2.8)
            if fall:
                vx, vy = random.uniform(-40, 40), random.uniform(60, 160)
            else:
                vx, vy = random.uniform(-300, 300), random.uniform(-520, -120)
            self.particles.append(dict(
                x=x, y=y, vx=vx, vy=vy, g=0 if fall else 420, life=life,
                max=life, color=hsv(random.random(), 0.8, 1.0),
                size=random.uniform(3, 5), shape="rect"))
        del self.particles[:-450]

    def update_fx(self, dt):
        for a in self.ambient:
            a["y"] -= a["vy"] * dt
            a["x"] += math.sin(self.time * 0.8 + a["ph"]) * 12 * dt
            if a["y"] < -10:
                a["y"] = HEIGHT + 10
                a["x"] = random.randint(0, WIDTH)
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += p["g"] * dt
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]
        if self.state == STATE_VICTORY and \
                self.assembly_time >= ASSEMBLY_TOTAL and random.random() < 0.5:
            self.confetti(random.randint(0, WIDTH), -10, 2, fall=True)

    def draw_particles(self, s):
        for p in self.particles:
            k = p["life"] / p["max"]
            x, y = int(p["x"]), int(p["y"])
            if p["shape"] == "rect":
                r = pygame.Rect(0, 0, int(p["size"] * 2), max(2, int(p["size"])))
                r.center = (x, y)
                pygame.draw.rect(s, p["color"], r)
            else:
                rad = max(1, int(p["size"] * (0.4 + k)))
                if rad > 2:
                    draw_glow(s, x, y, rad * 3, dim(p["color"], 0.6))
                pygame.draw.circle(s, p["color"], (x, y), rad)

    # ---------- Inicio ----------
    def draw_start(self, s):
        self.draw_bg(s)
        for item in self.decor:
            item.draw(s)

        frame = pygame.Rect(90, 80, 620, 150)
        draw_glow(s, WIDTH // 2, 155, 300, dim(MAGENTA, 0.35))
        draw_panel(s, frame, border=hsv(self.time * 0.15), alpha=190,
                   width=2, radius=22)
        corner_cols = (CYAN, MAGENTA, GOLD, GREEN)
        for col, (cx, cy, dx, dy) in zip(corner_cols, (
                (frame.left, frame.top, 1, 1), (frame.right, frame.top, -1, 1),
                (frame.left, frame.bottom, 1, -1),
                (frame.right, frame.bottom, -1, -1))):
            pygame.draw.line(s, col, (cx, cy), (cx + 36 * dx, cy), 4)
            pygame.draw.line(s, col, (cx, cy), (cx, cy + 36 * dy), 4)

        draw_rainbow_text(s, "ROBOT FACTORY", FONTS["score"],
                          (WIDTH // 2, 155), self.time)
        draw_rainbow_text(s, "BUILD YOUR ROBOT  -  EXTREME EDITION",
                          FONTS["h3"], (WIDTH // 2, 262), self.time, 0.5)

        pulse = 0.5 + 0.5 * math.sin(self.time * 4)
        box = pygame.Rect(0, 0, 440, 64)
        box.center = (WIDTH // 2, 345)
        bcol = hsv(self.time * 0.3, 0.8, 1.0)
        draw_glow(s, *box.center, 160, dim(bcol, 0.3 + 0.3 * pulse))
        draw_panel(s, box, border=bcol, fill=dim(bcol, 0.2), radius=18,
                   width=3)
        draw_text(s, "PRESS ANY KEY TO START", FONTS["h3"],
                  (int(190 + 65 * pulse),) * 3, box.center)

        draw_text(s, "LEFT / RIGHT ARROWS: move     P: pause     ESC: quit",
                  FONTS["small"], MUTED, (WIDTH // 2, 410))
        draw_text(s, f"Waves, bombs, slippery wheels and a ticking clock!  "
                     f"{MISS_LIMIT} missed pieces = -1 life",
                  FONTS["small"], GOLD, (WIDTH // 2, 435))

        # Fila de piezas a coleccionar
        for i, kind in enumerate(PART_KINDS):
            x = WIDTH // 2 + (i - 3) * 72
            draw_glow(s, x, 482, 34, dim(LEVEL_ACCENTS[i], 0.8))
            s.blit(get_icon(kind, 38), (x - 19, 463 + int(3 * math.sin(
                self.time * 3 + i))))

        demo = pygame.Rect(0, 0, Player.WIDTH, Player.HEIGHT)
        demo.midbottom = (int(WIDTH / 2 + 220 * math.sin(self.time * 0.9)),
                          FLOOR_Y + 2)
        draw_glow(s, demo.centerx, demo.centery, 56, PURPLE_DARK)
        draw_player(s, demo)

    # ---------- Juego ----------
    def draw_playing(self, s):
        self.draw_bg(s)
        for item in self.items:
            item.draw(s)
        self.player.draw(s, self.time)
        for popup in self.popups:
            img = FONTS["h3"].render(popup["text"], True, popup["color"])
            shadow = FONTS["h3"].render(popup["text"], True, BLACK)
            a = int(255 * min(1.0, popup["life"] / 0.4))
            img.set_alpha(a)
            shadow.set_alpha(a)
            rect = img.get_rect(midbottom=(popup["x"], popup["y"]))
            s.blit(shadow, rect.move(2, 2))
            s.blit(img, rect)

        self.draw_hud(s)

        if self.wave_warn and self.intro_timer <= 0 and not self.paused \
                and int(self.time * 8) % 2 == 0:
            draw_glow(s, WIDTH // 2, 140, 160, dim(RED, 0.5))
            draw_panel(s, (WIDTH // 2 - 175, 120, 350, 44), border=RED,
                       fill=(60, 8, 14), radius=14, width=3)
            draw_text(s, "!!  WAVE INCOMING  !!", FONTS["h3"], GOLD,
                      (WIDTH // 2, 142))

        if self.flash > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, int(100 * self.flash / 0.35)))
            s.blit(overlay, (0, 0))

        if self.intro_timer > 0:
            self.draw_level_banner(s)
        if self.paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            s.blit(overlay, (0, 0))
            draw_rainbow_text(s, "PAUSED", FONTS["h1"], (WIDTH // 2, 270),
                              self.time)
            draw_text(s, "Press P to resume", FONTS["body"], MUTED,
                      (WIDTH // 2, 320))

    def draw_hud(self, s):
        cfg = self.cfg
        acc = self.accent
        draw_panel(s, (10, 10, 236, 52), border=acc)
        s.blit(get_icon(cfg["kind"], 30), (20, 21))
        draw_text(s, f"LEVEL {self.level_index + 1} — {cfg['name']}",
                  FONTS["small"], WHITE, (148, 36))
        draw_panel(s, (256, 10, 150, 52), border=GOLD)
        draw_text(s, f"SCORE: {self.score}", FONTS["body"], GOLD, (331, 36))
        draw_panel(s, (416, 10, 160, 52), border=RED)
        draw_text(s, "LIVES:", FONTS["body"], WHITE, (426, 36), "midleft")
        for i in range(START_LIVES):
            draw_heart(s, 512 + i * 24, 33, 5, RED, filled=i < self.lives)
        draw_panel(s, (586, 10, 204, 52), border=GREEN)
        draw_text(s, f"{cfg['name']}: {self.collected}/{cfg['target']}",
                  FONTS["body"], WHITE, (688, 28))
        bar = pygame.Rect(600, 43, 176, 9)
        pygame.draw.rect(s, (20, 40, 55), bar, border_radius=4)
        fill = bar.copy()
        fill.width = int(bar.width * self.collected / cfg["target"])
        if fill.width > 0:
            pygame.draw.rect(s, GREEN, fill, border_radius=4)
        for i in range(1, cfg["target"]):
            x = bar.x + bar.w * i // cfg["target"]
            pygame.draw.line(s, (10, 20, 30), (x, bar.y), (x, bar.bottom), 2)
        pygame.draw.rect(s, dim(GREEN, 0.6), bar, 1, border_radius=4)

        # Barra de tiempo
        frac = max(0.0, min(1.0, self.time_left / cfg["time"]))
        tcol = acc if self.time_left > 15 else GOLD if self.time_left > 8 \
            else RED
        if self.time_left <= 8 and int(self.time * 6) % 2 == 0:
            tcol = WHITE
        tbar = pygame.Rect(10, 74, 780, 8)
        pygame.draw.rect(s, (14, 28, 42), tbar, border_radius=4)
        if frac > 0:
            pygame.draw.rect(s, tcol, (10, 74, int(780 * frac), 8),
                             border_radius=4)
            draw_glow(s, 10 + int(780 * frac), 78, 16, tcol)
        pygame.draw.rect(s, dim(acc, 0.5), tbar, 1, border_radius=4)

        # Fallos permitidos (puntos)
        draw_text(s, "MISSES", FONTS["small"], MUTED, (12, 98), "midleft")
        for i in range(MISS_LIMIT):
            c = (96 + i * 20, 98)
            if i < self.misses:
                pygame.draw.circle(s, ORANGE, c, 7)
            else:
                pygame.draw.circle(s, MUTED, c, 7, 2)
        draw_text(s, f"TIME: {max(0, int(math.ceil(self.time_left)))}s",
                  FONTS["small"], tcol, (788, 98), "midright")
        if self.combo >= 1:
            mult = self.multiplier()
            txt = f"COMBO {self.combo}   x{mult}"
            if mult > 1:
                draw_rainbow_text(s, txt, FONTS["body"], (WIDTH // 2, 98),
                                  self.time, 0.8)
            else:
                draw_text(s, txt, FONTS["body"], MUTED, (WIDTH // 2, 98))

    def draw_level_banner(self, s):
        cfg = self.cfg
        acc = self.accent
        box = pygame.Rect(0, 0, 460, 175)
        box.center = (WIDTH // 2, 260)
        draw_glow(s, *box.center, 270, dim(acc, 0.5))
        draw_panel(s, box, border=acc, alpha=240, radius=20, width=3)
        draw_text(s, f"LEVEL {self.level_index + 1}", FONTS["h1"], acc,
                  (WIDTH // 2, box.top + 38))
        draw_text(s, f"Collect {cfg['target']} {cfg['name']}", FONTS["h3"],
                  WHITE, (WIDTH // 2, box.top + 80))
        draw_text(s, "Avoid everything else!", FONTS["body"], GOLD,
                  (WIDTH // 2, box.top + 112))
        draw_text(s, f"{cfg['time']}s limit   |   {MISS_LIMIT} misses = -1 life",
                  FONTS["small"], MUTED, (WIDTH // 2, box.top + 142))
        icon = get_icon(cfg["kind"], 44)
        for x in (box.left + 22, box.right - 66):
            draw_glow(s, x + 22, box.top + 42, 36, dim(acc, 0.8))
            s.blit(icon, (x, box.top + 20))

    # ---------- Nivel completado ----------
    def draw_level_complete(self, s):
        self.draw_bg(s)
        cfg = self.cfg
        acc = self.accent
        draw_glow(s, WIDTH // 2, 100, 230, dim(acc, 0.45))
        draw_panel(s, (150, 50, 500, 96), border=acc, alpha=235, width=3,
                   radius=22)
        draw_rainbow_text(s, "LEVEL COMPLETED!", FONTS["h1"],
                          (WIDTH // 2, 98), self.time, 0.3)

        cx, cy = WIDTH // 2, 290
        draw_glow(s, cx, cy, 160, acc)
        for i in range(16):
            angle = math.radians(i * 22.5 + self.time * 40)
            inner = 78 + 6 * math.sin(self.time * 6 + i)
            p1 = (cx + inner * math.cos(angle), cy + inner * math.sin(angle))
            p2 = (cx + (inner + 38) * math.cos(angle),
                  cy + (inner + 38) * math.sin(angle))
            pygame.draw.line(s, NEON[i % len(NEON)], p1, p2, 3)
        for i in range(8):
            a = self.time * 1.5 + i * 0.8
            draw_star(s, int(cx + 125 * math.cos(a)),
                      int(cy + 98 * math.sin(a)), 6, NEON[i % len(NEON)])
        icon = get_icon(cfg["kind"], 130)
        s.blit(icon, icon.get_rect(center=(cx, cy)))

        draw_text(s, f"{cfg['name']} collected   +{POINTS_LEVEL} BONUS",
                  FONTS["h3"], GOLD, (WIDTH // 2, 410))
        draw_text(s, f"Time bonus: +{self.time_bonus}", FONTS["body"], acc,
                  (WIDTH // 2, 438))
        draw_panel(s, (240, 466, 320, 58), border=acc, alpha=235, radius=20)
        label = "Assembling robot..." if self.level_index + 1 >= NUM_LEVELS \
            else "Preparing next piece..."
        draw_text(s, label, FONTS["h3"], WHITE, (WIDTH // 2, 495))

    # ---------- Victoria ----------
    def draw_victory(self, s):
        self.draw_bg(s)
        t = self.assembly_time
        done = t >= ASSEMBLY_TOTAL

        draw_glow(s, WIDTH // 2, 60, 230, dim(MAGENTA, 0.4))
        draw_panel(s, (150, 14, 500, 86), border=MAGENTA if done else CYAN,
                   alpha=235, width=3, radius=22)
        if done:
            draw_rainbow_text(s, "ROBOT COMPLETED!", FONTS["h1"],
                              (WIDTH // 2, 46), self.time, 0.4)
            draw_text(s, "You built the robot.", FONTS["h3"], PURPLE_LIGHT,
                      (WIDTH // 2, 80))
        else:
            draw_text(s, "ASSEMBLING ROBOT...", FONTS["h1"], CYAN,
                      (WIDTH // 2, 46))
            draw_text(s, "Press ENTER to skip", FONTS["body"], MUTED,
                      (WIDTH // 2, 80))

        draw_panel(s, (20, 125, 205, 235), border=GOLD)
        draw_text(s, "FINAL SCORE:", FONTS["body"], WHITE, (36, 148), "midleft")
        draw_text(s, str(self.score), FONTS["score"], GOLD, (36, 188),
                  "midleft")
        pygame.draw.line(s, dim(GOLD, 0.5), (36, 222), (210, 222), 2)
        draw_text(s, "LEVELS COMPLETED:", FONTS["small"], WHITE, (36, 245),
                  "midleft")
        draw_text(s, f"{self.levels_completed}/{NUM_LEVELS}", FONTS["h3"],
                  CYAN, (36, 270), "midleft")
        draw_text(s, "LIVES REMAINING:", FONTS["small"], WHITE, (36, 301),
                  "midleft")
        for i in range(START_LIVES):
            draw_heart(s, 48 + i * 26, 322, 5, RED, filled=i < self.lives)
        draw_text(s, f"BEST COMBO: {self.best_combo}", FONTS["small"],
                  MAGENTA, (36, 345), "midleft")

        panel = pygame.Rect(575, 125, 205, 256)
        draw_panel(s, panel, border=GREEN)
        unlock_time = {}
        for i, (_n, kind, _o, _f) in enumerate(ROBOT_PARTS):
            if kind:
                unlock_time[kind] = i * ASSEMBLY_STEP + ASSEMBLY_SLIDE * 0.6
        for row, cfg in enumerate(LEVELS):
            y = panel.top + 26 + row * 34
            s.blit(get_icon(cfg["kind"], 26), (panel.left + 12, y - 13))
            draw_text(s, cfg["name"], FONTS["small"], WHITE,
                      (panel.left + 48, y), "midleft")
            if t >= unlock_time[cfg["kind"]]:
                draw_check(s, panel.right - 26, y, LEVEL_ACCENTS[row])
            else:
                pygame.draw.circle(s, (50, 70, 85), (panel.right - 26, y), 8, 2)

        ring = hsv(self.time * 0.2, 0.7, 1.0) if done else CYAN
        draw_glow(s, WIDTH // 2, 300, 215, dim(ring, 0.9 if done else 0.4))
        pygame.draw.ellipse(s, (10, 40, 55), (270, 448, 260, 40))
        pygame.draw.ellipse(s, ring, (270, 448, 260, 40), 3)
        pygame.draw.ellipse(s, dim(ring, 0.6), (295, 456, 210, 26), 2)
        pygame.draw.ellipse(s, dim(ring, 0.4), (250, 440, 300, 56), 1)
        draw_robot(s, 270, 112, t)

        if done:
            for i, button in enumerate(self.buttons):
                button.draw(s, i == self.selected)

    # ---------- Game over ----------
    def draw_game_over(self, s):
        self.draw_bg(s, red=True)
        glow = 0.5 + 0.5 * math.sin(self.time * 3)
        draw_glow(s, WIDTH // 2, 100, 240, dim(RED, 0.3 + 0.25 * glow))

        draw_panel(s, (220, 50, 360, 96), border=RED, alpha=235, width=3,
                   radius=22)
        draw_text(s, "GAME OVER", FONTS["h1"], RED, (WIDTH // 2, 98))

        draw_panel(s, (210, 190, 380, 200), border=ORANGE, alpha=235,
                   radius=22)
        draw_text(s, "FINAL SCORE:", FONTS["h3"], WHITE, (WIDTH // 2, 225))
        draw_text(s, str(self.score), FONTS["score"], GOLD, (WIDTH // 2, 275))
        pygame.draw.line(s, dim(ORANGE, 0.6), (250, 315), (550, 315), 2)
        draw_text(s, "LEVEL REACHED:", FONTS["body"], WHITE,
                  (WIDTH // 2, 340))
        draw_text(s, f"{self.level_reached}/{NUM_LEVELS}", FONTS["h2"], CYAN,
                  (WIDTH // 2, 370))

        for i, button in enumerate(self.buttons):
            button.draw(s, i == self.selected)

        sprite = pygame.Surface((Player.WIDTH, Player.HEIGHT), pygame.SRCALPHA)
        draw_player(sprite, sprite.get_rect(), dead=True)
        sprite = pygame.transform.rotate(sprite, 70)
        s.blit(sprite, sprite.get_rect(midbottom=(90, FLOOR_Y + 8)))

    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.handle_events()
            self.update(dt)
            self.draw()


# =============================================================================
# 7. MAIN
# =============================================================================

def main():
    Game().run()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
