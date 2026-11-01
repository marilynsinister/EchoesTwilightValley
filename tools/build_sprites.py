#!/usr/bin/env python3
"""
Генерация/обновление плейсхолдер-спрайтов для мода «Эхо Сумрачной Долины».

Создаёт (перезаписывает) в assets/Objects/:
  * TeaOfSilence.png   16x16 — чашка чая (одна клетка, как требует Data/Objects)
  * BlackRoseSeeds.png 16x16 — пакетик семян
  * VinylRecord.png    48x96 — декорация: 3 ряда по 16x16 (placed, front, back)
  * WeepingWillow.png  64x64 — декорация 4x4 клетки
  * Turntable.png      48x64 — настольный проигрыватель (квест «Последний аккорд»)
  * BlackRose.png      16x16 — сам цветок чёрной розы (урожай)

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
TEA = (120, 96, 70, 255)
WILLOW = (46, 70, 52, 255)


def canvas(w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save(img, name):
    path = os.path.join(OUT, name)
    img.save(path)
    print("OK:", path)


# ---------- Чай тишины (16x16) ----------
img, d = canvas(16, 16)
d.rectangle([3, 6, 11, 13], fill=PALE, outline=INK)          # чашка
d.rectangle([4, 7, 10, 9], fill=TEA)                          # чай
d.rectangle([11, 8, 13, 11], outline=INK)                     # ручка
for i in range(3):                                            # пар
    d.line([5 + i * 3, 4, 4 + i * 3, 2], fill=GREY)
save(img, "TeaOfSilence.png")

# ---------- Семена чёрной розы (16x16) ----------
img, d = canvas(16, 16)
d.polygon([(3, 4), (13, 4), (14, 14), (2, 14)], fill=(60, 55, 70, 255), outline=INK)
d.rectangle([3, 4, 13, 6], fill=GREY)                         # сгиб пакетика
d.ellipse([7, 8, 9, 10], fill=ROSE)                           # росток розы
d.line([8, 10, 8, 13], fill=WILLOW)
save(img, "BlackRoseSeeds.png")

# ---------- Цветок чёрной розы (16x16) ----------
img, d = canvas(16, 16)
d.line([8, 15, 8, 8], fill=WILLOW)                            # стебель
d.line([8, 12, 5, 10], fill=WILLOW)                           # лист
d.polygon([(8, 2), (11, 5), (10, 8), (6, 8), (5, 5)], fill=ROSE, outline=INK)
d.point((8, 5), fill=(90, 20, 50, 255))
save(img, "BlackRose.png")

# ---------- Виниловая пластинка (декорация 1x3: placed/front/back) ----------
img, d = canvas(48, 96)
for row, shade in [(0, 30), (32, 20), (64, 15)]:              # placed ярче, back темнее
    cx, cy = 24, row + 16
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(shade, shade, shade + 4, 255),
              outline=INK)
    for r in (9, 6):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(50, 50, 56, 255))
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=ROSE)    # центр этикетки
    d.point((cx, cy), fill=PALE)                              # отверстие
save(img, "VinylRecord.png")

# ---------- Плакучая ива (декорация 4x4) ----------
img, d = canvas(64, 64)
d.rectangle([29, 34, 34, 62], fill=(58, 44, 34, 255), outline=INK)   # ствол
d.polygon([(14, 36), (50, 36), (42, 20), (22, 20)], fill=WILLOW, outline=INK)
for x0 in range(16, 50, 6):                                     # свисающие ветви
    length = 14 + (x0 % 3) * 6
    d.line([x0, 34, x0 - 1, 34 + length], fill=(70, 100, 78, 255))
save(img, "WeepingWillow.png")

# ---------- Настольный проигрыватель (декорация 3x4 клетки -> 48x64) ----------
img, d = canvas(48, 64)
d.rectangle([4, 34, 43, 52], fill=(40, 38, 44, 255), outline=INK)     # корпус
d.rectangle([4, 52, 43, 60], fill=(28, 26, 32, 255), outline=INK)     # подставка
d.ellipse([10, 36, 34, 50], fill=(18, 18, 22, 255), outline=INK)      # пластинка
d.ellipse([19, 40, 25, 46], fill=ROSE)
d.line([36, 34, 24, 43], fill=PALE)                                   # тонарм
d.rectangle([34, 30, 42, 34], fill=GREY, outline=INK)                 # усилитель
d.point((38, 32), fill=(200, 180, 90, 255))                           # лампочка
save(img, "Turntable.png")

print("\nВсе спрайты обновлены.")
