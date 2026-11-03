#!/usr/bin/env python3
"""
Генерация авторских графических ассетов для мода «Эхо Сумрачной Долины».

Рисует детерминированно (сид RNG зашит) в стиле Stardew-пиксель-арта:
  * assets/Characters/Igor.png    32x64  — 4 ряда по 8 px: вниз / вправо / влево / вверх
  * assets/Portraits/Igor.png     64x64  — портрет: странник с пластинкой, туман и ивы
  * assets/Characters/Timur.png   32x64  — барабанщик: тёмная куртка, палочки, рыжеватые волосы
  * assets/Portraits/Timur.png    64x64  — портрет Тимура: дождь, метроном, грозовое небо
  * assets/Maps/VillageTiles.png  128x96 — тайлсет заброшенной деревни (8x6 тайлов 16x16):
        трава, дорога, вода+берег, стена дома, крыша, окно, дверь, дерево,
        фонарь, надгробие, колонна проигрывателя, кусты/цветы/травинки

Все размеры строго соответствуют требованиям Content Patcher / TMX (кратно 16).
Запуск:  python3 tools/build_art.py
"""
import os
import random
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
A_GROUND = (70, 108, 62, 255)     # влажная трава долины
A_GRASS_D = (52, 88, 48, 255)
A_GRASS_L = (96, 134, 82, 255)
A_PATH = (112, 98, 82, 255)       # мокрая каменная дорога
A_PATH_D = (88, 76, 64, 255)
A_PATH_L = (138, 122, 102, 255)
A_WATER = (52, 82, 104, 255)      # тёмный пруд
A_WATER_L = (86, 122, 146, 255)
A_MUD = (94, 74, 56, 255)         # берег
A_STONE = (122, 118, 112, 255)    # кладка стен
A_STONE_D = (90, 86, 82, 255)
A_STONE_L = (150, 146, 138, 255)
A_ROOF = (66, 54, 68, 255)        # готическая черепица
A_ROOF_D = (46, 36, 48, 255)
A_ROOF_L = (92, 76, 94, 255)
A_WOOD = (74, 56, 42, 255)        # доски / рамы
A_DOOR = (58, 42, 34, 255)
A_GLASS = (176, 196, 208, 255)    # светящееся окно
A_GLASS_D = (120, 140, 156, 255)
A_TRUNK = (66, 50, 38, 255)
A_LEAF = (44, 74, 50, 255)        # плакучие ивы
A_LEAF_L = (70, 104, 72, 255)
A_LANTERN = (222, 188, 96, 255)   # тёплый свет фонаря
A_INK = (24, 26, 32, 255)         # обводка
A_GREY = (150, 152, 158, 255)
A_ROSE = (58, 16, 38, 255)        # чёрная роза (акцент)
A_FOG = (168, 178, 190, 255)      # туман
A_SKIN = (222, 178, 140, 255)
A_HAIR = (58, 44, 36, 255)        # волосы Игоря — тёмно-каштановые
A_COAT = (44, 48, 60, 255)        # пальто Игоря
A_COAT_D = (30, 33, 42, 255)
A_SCARF = (72, 88, 96, 255)       # серый шарф
A_PANTS = (36, 38, 46, 255)
A_SHOE = (26, 26, 30, 255)
A_VINYL = (18, 18, 22, 255)
A_EYE = (30, 32, 40, 255)
A_TSHIRT = (210, 208, 200, 255)   # футболка под курткой Тимура
A_JACKET = (34, 36, 48, 255)      # куртка Тимура
A_HAIR_T = (122, 84, 46, 255)     # рыжевато-каштановые волосы Тимура
A_STICK = (188, 150, 100, 255)    # барабанные палочки
A_SKIN_T = (214, 170, 132, 255)


def new(w, h, color=(0, 0, 0, 0)):
    img = Image.new("RGBA", (w, h), color)
    return img, ImageDraw.Draw(img)


def save(img, rel):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("OK:", rel)


# ============================ ТАЙЛСЕТ ДЕРЕВНИ ============================
def tile_ground(d, ox, oy, rnd):
    """Трава с вариацией."""
    d.rectangle([ox, oy, ox + 15, oy + 15], fill=A_GROUND)
    for _ in range(10):
        x, y = rnd.randint(0, 14), rnd.randint(0, 14)
        c = A_GRASS_D if rnd.random() < 0.5 else A_GRASS_L
        d.point((ox + x, oy + y), fill=c)
    for _ in range(3):  # травинки
        x, y = rnd.randint(1, 13), rnd.randint(2, 13)
        d.line([ox + x, oy + y, ox + x, oy + y - 2], fill=A_GRASS_L)


def tile_path(d, ox, oy, rnd):
    """Мокрая каменная дорога: плиты + блики."""
    d.rectangle([ox, oy, ox + 15, oy + 15], fill=A_PATH)
    for yy in (0, 8):
        d.line([ox, oy + yy, ox + 15, oy + yy], fill=A_PATH_D)
    off = 4 if rnd.random() < 0.5 else 0
    for xx in range(off, 16, 8):
        d.line([ox + xx, oy, ox + xx, oy + 15], fill=A_PATH_D)
    for _ in range(6):  # лужицы-блики
        x, y = rnd.randint(1, 13), rnd.randint(1, 13)
        d.point((ox + x, oy + y), fill=A_PATH_L)


def tile_water_edge(d, ox, oy, rnd):
    """Пруд: вода сверху, тина/берег снизу."""
    d.rectangle([ox, oy, ox + 15, oy + 10], fill=A_WATER)
    d.rectangle([ox, oy + 11, ox + 15, oy + 15], fill=A_MUD)
    d.line([ox, oy + 10, ox + 15, oy + 10], fill=A_MUD)
    for x in (2, 8):  # блики воды
        d.line([ox + x, oy + 3, ox + x + 3, oy + 3], fill=A_WATER_L)
        d.point((ox + x + 5, oy + 7), fill=A_WATER_L)
    for x in range(0, 16, 5):  # травинки на берегу
        d.point((ox + x + 1, oy + 13), fill=A_GRASS_D)


def tile_wall(d, ox, oy, rnd):
    """Кладка серого камня со сколами."""
    d.rectangle([ox, oy, ox + 15, oy + 15], fill=A_STONE)
    for yy in (0, 5, 10):
        d.line([ox, oy + yy, ox + 15, oy + yy], fill=A_STONE_D)
    off = 0 if yy % 10 == 0 else 4
    for xx in (off, off + 8):
        if xx < 16:
            d.line([ox + xx, oy, ox + xx, oy + 15], fill=A_STONE_D)
    for _ in range(4):
        x, y = rnd.randint(1, 14), rnd.randint(1, 14)
        d.point((ox + x, oy + y), fill=A_STONE_L)
    d.point((ox + 3, oy + 12), fill=A_STONE_D)  # трещина
    d.point((ox + 4, oy + 13), fill=A_STONE_D)


def tile_roof(d, ox, oy, rnd):
    """Черепичная крыша со свесом."""
    d.rectangle([ox, oy, ox + 15, oy + 15], fill=A_ROOF)
    for yy in (3, 7, 11):
        d.line([ox, oy + yy, ox + 15, oy + yy], fill=A_ROOF_D)
        d.line([ox, oy + yy - 1, ox + 15, oy + yy - 1], fill=A_ROOF_L)
    d.line([ox, oy + 15, ox + 15, oy + 15], fill=A_ROOF_D)  # карниз
    for xx in (4, 12):  # вертикальные швы черепицы
        d.point((ox + xx, oy + 5), fill=A_ROOF_D)
        d.point((ox + xx, oy + 9), fill=A_ROOF_D)


def tile_window(d, ox, oy, rnd):
    """Светящееся окно в стене."""
    tile_wall(d, ox, oy, rnd)
    d.rectangle([ox + 4, oy + 4, ox + 11, oy + 11], fill=A_WOOD)      # рама
    d.rectangle([ox + 5, oy + 5, ox + 10, oy + 10], fill=A_GLASS)     # стекло
    d.line([ox + 8, oy + 5, ox + 8, oy + 10], fill=A_WOOD)            # переплёт
    d.line([ox + 5, oy + 8, ox + 10, oy + 8], fill=A_WOOD)
    d.point((ox + 6, oy + 6), fill=(232, 240, 246, 255))              # блик
    d.rectangle([ox + 3, oy + 12, ox + 12, oy + 12], fill=A_STONE_D)  # подоконник


def tile_door(d, ox, oy, rnd):
    """Дверь с аркой, ручкой и ступенью."""
    tile_wall(d, ox, oy, rnd)
    d.rectangle([ox + 4, oy + 2, ox + 11, oy + 14], fill=A_DOOR)
    d.rectangle([ox + 4, oy + 2, ox + 11, oy + 3], fill=A_WOOD)   # арка
    d.line([ox + 7, oy + 4, ox + 7, oy + 14], fill=(40, 28, 22, 255))  # стык досок
    d.point((ox + 9, oy + 8), fill=A_LANTERN)                     # ручка-латунь
    d.rectangle([ox + 3, oy + 14, ox + 12, oy + 15], fill=A_STONE_L)  # ступень


def tile_tree(d, ox, oy, rnd):
    """Ива: ствол внизу, пышная крона сверху."""
    tile_ground(d, ox, oy, rnd)
    d.rectangle([ox + 7, oy + 9, ox + 9, oy + 15], fill=A_TRUNK)
    for r, c in ((7, A_LEAF), (5, A_LEAF_L)):
        d.ellipse([ox + 8 - r, oy + 4 - r, ox + 8 + r, oy + 4 + r], fill=c)
    for x in (3, 6, 10, 13):  # свисающие пряди
        ln = 4 + (x % 3)
        d.line([ox + x, oy + 7, ox + x - 1, oy + 7 + ln], fill=A_LEAF)


def tile_lantern(d, ox, oy, rnd):
    """Уличный фонарь на столбе."""
    tile_ground(d, ox, oy, rnd)
    d.rectangle([ox + 7, oy + 5, ox + 8, oy + 14], fill=A_INK)          # столб
    d.rectangle([ox + 5, oy + 1, ox + 10, oy + 5], fill=A_INK)          # корпус
    d.rectangle([ox + 6, oy + 2, ox + 9, oy + 4], fill=A_LANTERN)       # свет
    d.polygon([(ox + 5, oy + 1), (ox + 7, oy - 0 + 0), (ox + 10, oy + 1)], fill=A_GREY)
    d.point((ox + 7, oy + 3), fill=(255, 232, 160, 255))                # filament
    d.rectangle([ox + 6, oy + 14, ox + 9, oy + 15], fill=A_STONE_D)     # основание
    for x, y in ((4, 6), (11, 7), (5, 9)):  # тёплое сияние
        d.point((ox + x, oy + y), fill=(180, 150, 90, 120))


def tile_grave(d, ox, oy, rnd):
    """Надгробие с крестом и мхом."""
    tile_ground(d, ox, oy, rnd)
    d.rectangle([ox + 4, oy + 5, ox + 11, oy + 13], fill=A_STONE)
    d.polygon([(ox + 4, oy + 5), (ox + 7, oy + 2), (ox + 11, oy + 5)], fill=A_STONE)
    d.line([ox + 7, oy + 5, ox + 7, oy + 10], fill=A_STONE_D)   # крест
    d.line([ox + 5, oy + 7, ox + 9, oy + 7], fill=A_STONE_D)
    d.point((ox + 5, oy + 11), fill=A_GRASS_D)                  # мох
    d.point((ox + 10, oy + 12), fill=A_GRASS_D)
    d.rectangle([ox + 3, oy + 13, ox + 12, oy + 14], fill=A_STONE_D)


def tile_column(d, ox, oy, rnd):
    """колонна-постамент с виниловой пластинкой — символ долины."""
    tile_ground(d, ox, oy, rnd)
    d.rectangle([ox + 5, oy + 8, ox + 10, oy + 14], fill=A_STONE)
    d.rectangle([ox + 4, oy + 14, ox + 11, oy + 15], fill=A_STONE_D)  # база
    d.rectangle([ox + 4, oy + 7, ox + 11, oy + 8], fill=A_STONE_L)    # капитель
    cx, cy = ox + 8, oy + 4
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=A_VINYL, outline=A_INK)
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], outline=(50, 50, 58, 255))
    d.point((cx, cy), fill=A_ROSE)  # этикетка


def tile_bush_flowers(d, ox, oy, rnd):
    """Куст с ягодами и полевыми цветами."""
    tile_ground(d, ox, oy, rnd)
    for r, c in ((5, A_LEAF), (3, A_LEAF_L)):
        d.ellipse([ox + 8 - r, oy + 9 - r, ox + 8 + r, oy + 9 + r], fill=c)
    for x, y in ((6, 7), (10, 9), (8, 11)):
        d.point((ox + x, oy + y), fill=A_ROSE)  # розы-ягоды
    for x, y in ((2, 13), (13, 12)):  # цветы рядом
        d.point((ox + x, oy + y), fill=(210, 190, 120, 255))
        d.point((ox + x, oy + y - 1), fill=(230, 230, 235, 255))


def build_village_tiles():
    img, d = new(128, 96)
    rnd = random.Random(777)
    layout = [
        [tile_ground, tile_path, tile_water_edge, tile_wall,
         tile_roof, tile_window, tile_door, tile_tree],
        [tile_ground, tile_lantern, tile_grave, tile_column,
         tile_bush_flowers, tile_path, tile_ground, tile_water_edge],
    ]
    for row, tiles in enumerate(layout):
        for col, fn in enumerate(tiles):
            fn(d, col * 16, row * 16, rnd)
    save(img, "assets/Maps/VillageTiles.png")


# ============================ ПЕРСОНАЖ ИГОРЯ ============================
def draw_head(d, ox, oy, facing, hair=A_HAIR, skin=A_SKIN):
    """Голова 8x8 в слоте (ox,oy); facing: down/right/left/up."""
    d.rectangle([ox + 1, oy + 1, ox + 6, oy + 6], fill=skin)
    if facing == "down":
        d.rectangle([ox + 1, oy, ox + 6, oy + 1], fill=hair)          # чёлка
        d.line([ox + 1, oy + 2, ox + 1, oy + 5], fill=hair)           # виски
        d.line([ox + 6, oy + 2, ox + 6, oy + 5], fill=hair)
        d.point((ox + 2, oy + 3), fill=A_EYE)
        d.point((ox + 5, oy + 3), fill=A_EYE)
        d.point((ox + 3, oy + 5), fill=(180, 130, 105, 255))          # рот
    elif facing == "up":
        d.rectangle([ox + 1, oy, ox + 6, oy + 5], fill=hair)          # затылок
        d.point((ox + 3, oy + 2), fill=(70, 54, 44, 255))             # блик волос
    else:  # right / left
        hx = ox + 6 if facing == "right" else ox + 1
        ex = ox + 2 if facing == "right" else ox + 5
        d.rectangle([ox + 1, oy, ox + 6, oy + 1], fill=hair)
        d.line([hx, oy + 1, hx, oy + 5], fill=hair)                   # волосы сбоку
        d.point((ex, oy + 3), fill=A_EYE)


def draw_igor_body(d, ox, oy, facing):
    """Тело 8x12 в слоте; пальто, шарф, штаны, ботинки."""
    coat_x0, coat_x1 = ox + 1, ox + 6
    if facing == "down":
        d.rectangle([coat_x0, oy, coat_x1, oy + 7], fill=A_COAT)
        d.rectangle([ox + 2, oy, ox + 5, oy + 1], fill=A_SCARF)       # шарф
        d.line([ox + 3, oy + 2, ox + 3, oy + 6], fill=A_COAT_D)       # полы
        d.line([ox + 4, oy + 2, ox + 4, oy + 6], fill=A_COAT_D)
        buttons = [(ox + 3, oy + 3), (ox + 3, oy + 5), (ox + 4, oy + 4)]
        for bx, by in buttons:
            d.point((bx, by), fill=A_GREY)
        arms_y = (oy + 2, oy + 6)
    elif facing == "up":
        d.rectangle([coat_x0, oy, coat_x1, oy + 7], fill=A_COAT_D)
        d.line([ox + 3, oy + 1, ox + 3, oy + 6], fill=(22, 24, 30, 255))
    else:
        d.rectangle([coat_x0, oy, coat_x1, oy + 7], fill=A_COAT)
        front_x = ox + 5 if facing == "right" else ox + 2
        d.line([front_x, oy + 1, front_x, oy + 6], fill=A_COAT_D)     # передний край
        d.point((front_x, oy + 3), fill=A_GREY)                       # пуговица
        arm_front_x = ox + 6 if facing == "right" else ox + 1
        d.line([arm_front_x, oy + 2, arm_front_x, oy + 6], fill=A_COAT_D)
        arms_y = None
    # руки- sleeve концы
    if facing in ("down", "up"):
        d.point((ox + 1, oy + 6), fill=A_SKIN)
        d.point((ox + 6, oy + 6), fill=A_SKIN)
    # ноги
    d.rectangle([ox + 2, oy + 8, ox + 3, oy + 10], fill=A_PANTS)
    d.rectangle([ox + 4, oy + 8, ox + 5, oy + 10], fill=A_PANTS)
    dx = 0
    if facing == "right":
        dx = 1
    elif facing == "left":
        dx = -1
    d.rectangle([ox + 2 - dx, oy + 11, ox + 3 - dx, oy + 11], fill=A_SHOE)
    d.rectangle([ox + 4 + dx, oy + 11, ox + 5 + dx, oy + 11], fill=A_SHOE)


def build_igor_character():
    img, d = new(32, 64)
    slots = [("down", 0), ("right", 1), ("left", 2), ("up", 3)]
    for facing, i in slots:
        ox = i * 8
        draw_head(d, ox, 0, facing)
        draw_igor_body(d, ox, 8, facing)
    save(img, "assets/Characters/Igor.png")


# ============================ ПЕРСОНАЖ ТИМУРА ============================
def draw_timur_body(d, ox, oy, facing):
    """Куртка расстёгнута поверх футболки; палочки в руках."""
    d.rectangle([ox + 1, oy, ox + 6, oy + 7], fill=A_JACKET)
    shirt_x0, shirt_x1 = ox + 3, ox + 4
    d.rectangle([shirt_x0, oy + 1, shirt_x1, oy + 6], fill=A_TSHIRT)  # футболка
    d.line([ox + 2, oy + 1, ox + 2, oy + 7], fill=(22, 24, 32, 255))  # край куртки
    d.line([ox + 5, oy + 1, ox + 5, oy + 7], fill=(22, 24, 32, 255))
    if facing == "down":
        # руки чуть в стороны, палочки торчат
        d.point((ox + 1, oy + 6), fill=A_SKIN_T)
        d.point((ox + 6, oy + 6), fill=A_SKIN_T)
        d.line([ox + 1, oy + 6, ox, oy + 4], fill=A_STICK)
        d.line([ox + 6, oy + 6, ox + 7, oy + 4], fill=A_STICK)
    elif facing in ("right", "left"):
        fx = ox + 6 if facing == "right" else ox + 1
        bx = ox + 1 if facing == "right" else ox + 6
        d.point((fx, oy + 5), fill=A_SKIN_T)
        d.line([fx, oy + 5, fx + (1 if facing == "right" else -1), oy + 3], fill=A_STICK)
        d.point((bx, oy + 6), fill=A_SKIN_T)
    else:
        d.point((ox + 1, oy + 6), fill=A_SKIN_T)
        d.point((ox + 6, oy + 6), fill=A_SKIN_T)
    d.rectangle([ox + 2, oy + 8, ox + 3, oy + 10], fill=A_PANTS)
    d.rectangle([ox + 4, oy + 8, ox + 5, oy + 10], fill=A_PANTS)
    d.rectangle([ox + 2, oy + 11, ox + 3, oy + 11], fill=A_SHOE)
    d.rectangle([ox + 4, oy + 11, ox + 5, oy + 11], fill=A_SHOE)


def build_timur_character():
    img, d = new(32, 64)
    for facing, i in [("down", 0), ("right", 1), ("left", 2), ("up", 3)]:
        ox = i * 8
        draw_head(d, ox, 0, facing, hair=A_HAIR_T, skin=A_SKIN_T)
        draw_timur_body(d, ox, 8, facing)
    save(img, "assets/Characters/Timur.png")


# --------- тайлсет-строка для TMX-карты деревни (8 тайлов, как tiles.tsx) ---------
def tileset_row(d, ox0, oy, rnd):
    """Один ряд 8x16 из авторских тайлов — тот же порядок, что в VillageTiles."""
    for col, fn in enumerate([tile_ground, tile_path, tile_water_edge, tile_wall,
                              tile_roof, tile_window, tile_door, tile_tree]):
        fn(d, ox0 + col * 16, oy, rnd)


def build_map_tileset():
    """Обновляет assets/Maps/placeholder.png: верхний ряд — настоящие арт-тайлы
    (их использует TMX через tiles.tsx), нижняя половина остаётся запасной."""
    path = os.path.join(ROOT, "assets", "Maps", "placeholder.png")
    img, d = new(128, 16)
    tileset_row(d, 0, 0, random.Random(777))
    save(img, "assets/Maps/placeholder.png")


# ============================ ПОРТРЕТЫ ============================
def portrait_bg(d, w, h, seed):
    rnd = random.Random(seed)
    # градиент сумеречного неба
    for y in range(h):
        t = y / (h - 1)
        r = int(38 + (70 - 38) * t)
        g = int(42 + (84 - 42) * t)
        b = int(60 + (96 - 60) * t)
        d.line([(0, y), (w, y)], fill=(r, g, b, 255))
    # луна в дымке
    d.ellipse([w - 24, 6, w - 12, 18], fill=(210, 214, 220, 120))
    d.ellipse([w - 22, 8, w - 14, 16], fill=(228, 232, 238, 200))
    # силуэт дальних холмов
    d.polygon([(0, 44), (12, 36), (26, 42), (40, 34), (54, 40), (w, 38), (w, h), (0, h)],
              fill=(30, 36, 44, 255))
    # туманные полосы
    for y in (40, 46, 52):
        for _ in range(6):
            x = rnd.randint(0, w - 10)
            d.line([(x, y), (x + rnd.randint(6, 14), y)], fill=(A_FOG[0], A_FOG[1], A_FOG[2], 40))


def silhouette_willow(d, x, base_y, scale=1.0):
    """Мини-ива на заднем плане портрета."""
    r = int(7 * scale)
    d.rectangle([x - 1, base_y - int(10 * scale), x + 1, base_y], fill=(24, 30, 26, 255))
    d.ellipse([x - r, base_y - int(16 * scale), x + r, base_y - int(6 * scale)],
              fill=(34, 52, 40, 255))
    for dx in range(-r + 1, r, 3):
        ln = int((5 + abs(dx) % 3) * scale)
        d.line([(x + dx, base_y - int(8 * scale)),
                (x + dx - 1, base_y - int(8 * scale) + ln)], fill=(44, 66, 48, 255))


def draw_portrait_figure(d, hair, coat, scarf, vinyl, seed):
    """Бюст персонажа по центру 64x64."""
    cx = 32
    # плечи/пальто
    d.polygon([(cx - 18, 64), (cx - 16, 44), (cx - 8, 38), (cx + 8, 38),
               (cx + 16, 44), (cx + 18, 64)], fill=coat)
    d.line([(cx - 16, 44), (cx + 16, 44)], fill=(20, 22, 28, 255))
    # шея
    d.rectangle([cx - 3, 34, cx + 3, 40], fill=A_SKIN)
    # голова
    d.ellipse([cx - 10, 14, cx + 10, 36], fill=A_SKIN)
    # волосы объёмные
    d.pieslice([cx - 12, 10, cx + 12, 32], 180, 360, fill=hair)
    d.rectangle([cx - 12, 20, cx - 8, 28], fill=hair)
    d.rectangle([cx + 8, 20, cx + 12, 28], fill=hair)
    rnd = random.Random(seed)
    for _ in range(8):  # пряди
        x = rnd.randint(cx - 9, cx + 9)
        d.line([(x, 14), (x + rnd.choice((-1, 0, 1)), 20)],
               fill=tuple(min(255, c + 18) for c in hair[:3]) + (255,))
    # глаза — мечтательные, полуприкрытые
    for ex in (cx - 5, cx + 4):
        d.rectangle([ex, 25, ex + 2, 26], fill=A_EYE)
        d.line([(ex - 1, 24), (ex + 3, 24)], fill=(120, 96, 76, 255))  # брови
    # нос, рот
    d.point((cx, 29), fill=(188, 142, 110, 255))
    d.line([(cx - 2, 32), (cx + 2, 32)], fill=(150, 100, 84, 255))
    # лёгкие тени под скулами
    d.point((cx - 7, 30), fill=(200, 156, 122, 255))
    d.point((cx + 7, 30), fill=(200, 156, 122, 255))
    # шарф
    d.rectangle([cx - 9, 38, cx + 9, 44], fill=scarf)
    d.line([(cx - 9, 41), (cx + 9, 41)], fill=tuple(max(0, c - 18) for c in scarf[:3]) + (255,))
    if vinyl:
        # пластинка у груди
        vx, vy = cx + 11, 50
        d.ellipse([vx - 8, vy - 8, vx + 8, vy + 8], fill=A_VINYL, outline=A_INK)
        for r in (5, 3):
            d.ellipse([vx - r, vy - r, vx + r, vy + r], outline=(48, 48, 56, 255))
        d.ellipse([vx - 2, vy - 2, vx + 2, vy + 2], fill=A_ROSE)
        d.point((vx, vy), fill=A_GREY)


def build_igor_portrait():
    img, d = new(64, 64)
    portrait_bg(d, 64, 64, seed=11)
    silhouette_willow(d, 8, 56, 1.0)
    silhouette_willow(d, 56, 54, 0.8)
    draw_portrait_figure(d, A_HAIR, A_COAT, A_SCARF, vinyl=True, seed=21)
    save(img, "assets/Portraits/Igor.png")


def build_timur_portrait():
    img, d = new(64, 64)
    portrait_bg(d, 64, 64, seed=13)
    # дождевые косые штрихи поверх неба
    rnd = random.Random(5)
    for _ in range(26):
        x, y = rnd.randint(0, 63), rnd.randint(0, 34)
        d.line([(x, y), (x - 2, y + 5)], fill=(150, 165, 185, 90))
    silhouette_willow(d, 54, 55, 0.9)
    # фигура Тимура: та же схема, другие цвета + палочки и метроном
    draw_portrait_figure(d, A_HAIR_T, A_JACKET, (60, 62, 74), vinyl=False, seed=23)
    cx = 32
    d.line([(cx - 14, 48), (cx - 20, 40)], fill=A_STICK)   # палочка вверх
    d.point((cx - 20, 40), fill=(222, 190, 140, 255))      # набалдашник
    d.line([(cx + 15, 50), (cx + 21, 42)], fill=A_STICK)
    d.point((cx + 21, 42), fill=(222, 190, 140, 255))
    # метроном справа внизу
    mx = 52
    d.polygon([(mx - 4, 63), (mx + 4, 63), (mx + 2, 50), (mx - 2, 50)], fill=A_WOOD)
    d.line([(mx, 60), (mx + 3, 52)], fill=A_GREY)          # груз-рычаг
    d.point((mx + 2, 55), fill=A_INK)
    save(img, "assets/Portraits/Timur.png")


def main():
    build_village_tiles()
    build_igor_character()
    build_timur_character()
    build_igor_portrait()
    build_timur_portrait()
    build_map_tileset()   # арт-тайлы для TMX (placeholder.png, 128x16)
    print("\nАвторские ассеты обновлены.")


if __name__ == "__main__":
    main()
