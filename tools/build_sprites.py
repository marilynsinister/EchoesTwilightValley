#!/usr/bin/env python3
"""
Генерация авторских спрайтов предметов для мода «Эхо Сумрачной Долины».

Рисует детерминированно (LFSR-шум с фиксированным зерном — побитово
воспроизводимо между запусками и машинами) в единой сумрачной палитре.
Создаёт (перезаписывает) в assets/Objects/:
  * TeaOfSilence.png     16x16  — фарфоровая чашка с паром над чаем
  * BlackRoseSeeds.png   16x16  — крафтовый пакетик семян с ростком розы
  * VinylRecord.png      48x96  — декорация: 3 ряда по 16x16 (placed/front/back)
  * WeepingWillow.png    64x64  — плакучая ива 4x4 (крона, ствол, корни, отражение)
  * WillowSapling.png    16x16  — саженец ивы (валюта деревни / предмет магазина)
  * Turntable.png        48x64  — настольный проигрыватель (квест «Последний аккорд»)
  * BlackRose.png        16x16  — бутон чёрной розы (урожай) + стебель/лист
  * BlackRoseCrop.png    64x128 — стадийная грядка розы: 8 фаз роста x 16px
  * TearsOfMemory.png    16x16  — «Слёзы памяти»: светящиеся капли валюты
  * RecordNeedle.png     16x16  — квестовая игла грампластинки с медным наконечником

Запуск:  python3 tools/build_sprites.py
"""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "Objects")
OUT = os.path.abspath(OUT)

INK = (20, 22, 28, 255)        # почти чёрный — силуэт в духе пост-панк
GREY = (90, 95, 105, 255)
PALE = (170, 175, 185, 255)
ROSE = (48, 12, 30, 255)       # глубокий чёрно-бордовый
ROSE_HI = (96, 26, 56, 255)    # подсветка лепестков
TEA = (120, 96, 70, 255)
WILLOW = (46, 70, 52, 255)
WILLOW_D = (30, 48, 36, 255)   # тёмная зелень кроны
WILLOW_L = (78, 112, 84, 255)  # светлые пряди
TRUNK = (58, 44, 34, 255)      # кора
TRUNK_D = (40, 30, 24, 255)
MUD = (94, 74, 56, 255)        # земля под корнями
WATER = (52, 82, 104, 255)     # тёмная вода (отражения)
PORCELAIN = (206, 210, 218, 255)  # фарфор чашки
COPPER = (170, 105, 60, 255)   # медь иглы
TEAR = (128, 150, 175, 255)    # слёзы
TEAR_HI = (220, 230, 240, 255)


class Lcg:
    """Детерминированный мультипликативный генератор (без float-зависимостей)."""

    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFF or 1

    def next(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s

    def randint(self, a, b):
        return a + self.next() % (b - a + 1)

    def chance(self, num, den):
        return self.next() % den < num


def px(d, x, y, c):
    """Точка строго в границах холста."""
    w, h = d.im.size
    if 0 <= x < w and 0 <= y < h:
        d.point((x, y), fill=c)


def canvas(w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save(img, name):
    path = os.path.join(OUT, name)
    img.save(path)
    print("OK:", path)


# ---------- Чай тишины (16x16) ----------
img, d = canvas(16, 16)
d.rectangle([3, 6, 11, 13], fill=PORCELAIN, outline=INK)      # фарфоровая чашка
d.line([4, 7, 10, 7], fill=(232, 236, 242, 255))              # светлый ободок
d.line([4, 12, 10, 12], fill=(150, 156, 168, 255))            # тень на донышке
d.rectangle([4, 8, 10, 10], fill=TEA)                         # чай (тёмно-янтарный)
d.point((5, 8), fill=(168, 138, 100, 255))                   # блик на заварке
d.rectangle([11, 8, 13, 11], outline=INK)                     # ручка
d.line([12, 9, 12, 10], fill=PALE)                            # блик ручки
rnd = Lcg(7)
for i in range(3):                                            # извилистый пар
    x0 = 5 + i * 3
    for j in range(3):
        y = 4 - j
        off = rnd.randint(-1, 1)
        px(d, x0 + off, y, (GREY[0], GREY[1], GREY[2], 200 - j * 50))
save(img, "TeaOfSilence.png")

# ---------- Семена чёрной розы (16x16) ----------
img, d = canvas(16, 16)
d.polygon([(3, 4), (13, 4), (14, 14), (2, 14)], fill=(60, 55, 70, 255), outline=INK)
d.rectangle([3, 4, 13, 6], fill=GREY)                         # сгиб пакетика
d.line([3, 6, 13, 6], fill=INK)
d.ellipse([7, 8, 9, 10], fill=ROSE_HI)                        # росток розы
d.ellipse([7, 8, 9, 9], fill=ROSE)
d.line([8, 10, 8, 13], fill=WILLOW)                           # стебель
d.line([8, 12, 6, 11], fill=WILLOW_L)                         # листик
d.point((12, 12), fill=(44, 40, 54, 255))                     # пятно-тень
save(img, "BlackRoseSeeds.png")

# ---------- Цветок чёрной розы (16x16) ----------
img, d = canvas(16, 16)
d.line([8, 15, 8, 8], fill=WILLOW)                            # стебель
d.line([8, 12, 5, 10], fill=WILLOW)                           # лист
d.line([5, 10, 4, 11], fill=WILLOW_L)                         # жилка листа
d.polygon([(8, 1), (11, 4), (10, 8), (6, 8), (5, 4)], fill=ROSE, outline=INK)
d.point((8, 4), fill=ROSE_HI)                                 # подсветка бутона
d.line([(7, 3), (9, 5)], fill=(24, 8, 18, 255))               # складка лепестка
d.point((8, 6), fill=(120, 40, 70, 255))                      # сердцевина
save(img, "BlackRose.png")

# ---------- Виниловая пластинка (декорация 1x3: placed/front/back) ----------
img, d = canvas(48, 96)
for row, shade in [(0, 30), (32, 20), (64, 15)]:              # placed ярче, back темнее
    cx, cy = 24, row + 16
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(shade, shade, shade + 4, 255),
              outline=INK)
    for r in (9, 6):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(50, 50, 56, 255))
    d.arc([cx - 11, cy - 11, cx + 11, cy + 11], 200, 300,
          fill=(70, 70, 80, 255))                             # блик канта
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=ROSE)    # центр этикетки
    d.point((cx, cy), fill=PALE)                              # отверстие
save(img, "VinylRecord.png")

# ---------- Плакучая ива (декорация 4x4) ----------
img, d = canvas(64, 64)
rnd = Lcg(31)
# крона — три яруса эллипсов от тёмного к светлому
d.ellipse([8, 6, 56, 34], fill=WILLOW_D)
d.ellipse([12, 8, 52, 30], fill=WILLOW)
d.ellipse([18, 10, 46, 24], fill=WILLOW_L)
# свисающие пряди разной длины
for x0 in range(12, 54, 4):
    length = 10 + (x0 * 7 % 11)
    tint = WILLOW_L if rnd.chance(1, 3) else WILLOW
    d.line([x0, 28, x0 - 1, 28 + length], fill=tint)
    px(d, x0 - 1, 29 + length, WILLOW_D)                      # кончик пряди
# ствол с корой и корнями
d.rectangle([29, 30, 34, 58], fill=TRUNK, outline=TRUNK_D)
d.line([31, 34, 31, 56], fill=TRUNK_D)                        # борозда коры
d.line([29, 54, 25, 60], fill=TRUNK)                          # левый корень
d.line([34, 54, 39, 60], fill=TRUNK)                          # правый корень
d.line([31, 56, 31, 62], fill=TRUNK_D)
# мокрая земля и отражение в луже
d.line([20, 62, 44, 62], fill=MUD)
for x in range(26, 40, 2):
    px(d, x, 63, (WATER[0], WATER[1], WATER[2], 160))         # полоска воды
px(d, 30, 63, (WILLOW_L[0], WILLOW_L[1], WILLOW_L[2], 90))   # зелёный отблеск
save(img, "WeepingWillow.png")

# ---------- Саженец ивы (16x16) — новый спрайт вместо 64x64-ивы в сетке предметов ----------
img, d = canvas(16, 16)
d.line([8, 15, 8, 7], fill=TRUNK, width=2)                    # тонкий стволик
d.line([8, 15, 6, 15], fill=MUD)                              # холмик земли
d.point((9, 15), fill=MUD)
d.line([8, 9, 5, 6], fill=WILLOW)                             # нижняя ветвь
d.line([8, 7, 11, 4], fill=WILLOW)                            # верхняя ветвь
for x0, y0, ln in [(4, 5, 4), (6, 4, 5), (10, 3, 5), (12, 4, 3)]:
    d.line([x0, y0, x0, y0 + ln], fill=WILLOW_L)              # молоденькие пряди
d.point((8, 3), fill=WILLOW_L)                                # макушка
save(img, "WillowSapling.png")

# ---------- Настольный проигрыватель (декорация 3x4 клетки -> 48x64) ----------
img, d = canvas(48, 64)
d.rectangle([4, 34, 43, 52], fill=(40, 38, 44, 255), outline=INK)     # корпус
d.line([5, 35, 42, 35], fill=(64, 62, 70, 255))                       # светлая грань
d.rectangle([4, 52, 43, 60], fill=(28, 26, 32, 255), outline=INK)     # подставка
d.ellipse([10, 36, 34, 50], fill=(18, 18, 22, 255), outline=INK)      # пластинка
for r in (5, 7):
    d.ellipse([22 - r, 43 - r, 22 + r, 43 + r], outline=(46, 46, 54, 255))
d.ellipse([19, 40, 25, 46], fill=ROSE)
d.point((22, 43), fill=PALE)                                         # шпиндель
d.line([36, 34, 24, 43], fill=PALE)                                  # тонарм
d.ellipse([35, 32, 38, 35], fill=GREY, outline=INK)                  # база тонарма
d.rectangle([34, 28, 42, 33], fill=GREY, outline=INK)                # усилитель
d.point((36, 30), fill=(222, 188, 96, 255))                          # лампочка
d.point((39, 30), fill=(120, 100, 60, 255))                          # вторая кнопка
save(img, "Turntable.png")

# ---------- Чёрная роза: грядка со стадиями роста (64x128, 8 фаз по 16 px) ----------
# content.json использует стандартную схему Data/Crops (8 стадий, Texture = этот файл).
img, d = canvas(64, 128)
rnd = Lcg(97)
for stage in range(8):
    y0 = stage * 16
    cx = 32                                   # роза растёт в середине кадра (клетка 2)
    # борозда во всех стадиях
    d.line([cx - 6, y0 + 14, cx + 6, y0 + 14], fill=MUD)
    d.point((cx - 4, y0 + 13), fill=(74, 58, 44, 255))
    d.point((cx + 5, y0 + 13), fill=(74, 58, 44, 255))
    if stage == 0:
        px(d, cx, y0 + 12, TRUNK_D)           # семечко в земле
    elif stage == 1:
        d.line([cx, y0 + 14, cx, y0 + 11], fill=WILLOW)
        px(d, cx - 1, y0 + 11, WILLOW_L)      # первый листик
    elif stage <= 3:                          # подрастающий стебель
        h = 4 + stage * 2
        d.line([cx, y0 + 14, cx, y0 + 14 - h], fill=WILLOW)
        d.line([cx, y0 + 12, cx - 3, y0 + 10], fill=WILLOW)      # листья
        d.line([cx, y0 + 10 - stage, cx + 3, y0 + 8 - stage], fill=WILLOW)
    else:                                     # бутон -> роспуск
        top = y0 + 14 - (10 + stage)
        d.line([cx, y0 + 14, cx, top + 3], fill=WILLOW)
        d.line([cx, y0 + 11, cx - 3, y0 + 9], fill=WILLOW)
        d.line([cx, y0 + 9, cx + 3, y0 + 7], fill=WILLOW)
        r = 1 if stage == 4 else (2 if stage == 5 else 3)
        d.ellipse([cx - r, top - r + 1, cx + r, top + r + 1],
                  fill=ROSE, outline=INK)
        if stage >= 6:
            px(d, cx, top + 1, ROSE_HI)       # раскрытие бутона
        if stage == 7:
            px(d, cx - 2, top, (120, 40, 70, 255))  # зрелый цветок готов к сбору
            px(d, cx + 2, top + 2, (120, 40, 70, 255))
DUST_PATTERN = [(5, 3), (13, 9), (21, 2), (44, 5), (52, 11), (58, 1),
                (7, 21), (17, 27), (49, 19), (55, 29)]   # фикс. позиции вне колонки розы
for sx, sy in DUST_PATTERN:
    px(d, sx, sy, (60, 60, 66, 255))
save(img, "BlackRoseCrop.png")

# ---------- Слёзы памяти (16x16, валюта долины) ----------
img, d = canvas(16, 16)
for cx, cy, r in [(5, 9, 3), (11, 10, 2)]:                    # две капли
    d.polygon([(cx, cy - r - 2), (cx - r, cy), (cx + r, cy)], fill=TEAR, outline=INK)
    d.ellipse([cx - r, cy - 1, cx + r, cy + r], fill=TEAR, outline=INK)
    px(d, cx - 1, cy - 1, TEAR_HI)                            # блик
    px(d, cx + 1, cy + 2, (90, 110, 136, 255))                # тень капли
px(d, 8, 4, (200, 214, 228, 120))                             # искорка между каплями
save(img, "TearsOfMemory.png")

# ---------- Иголка для проигрывателя (16x16, квестовый предмет) ----------
img, d = canvas(16, 16)
d.line([3, 13, 12, 4], fill=COPPER, width=2)                  # медное древко
d.line([4, 12, 11, 5], fill=(214, 140, 84, 255))              # блик меди
d.line([12, 4, 14, 2], fill=PALE)                             # стальное остриё
px(d, 14, 2, PORCELAIN)
d.ellipse([2, 12, 5, 15], outline=INK)                        # ушко держателя
d.rectangle([1, 13, 3, 15], fill=GREY, outline=INK)           # цанга
save(img, "RecordNeedle.png")

print("\nВсе спрайты обновлены.")
