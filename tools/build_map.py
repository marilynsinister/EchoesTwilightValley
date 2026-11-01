#!/usr/bin/env python3
"""
Генератор карты AbandonedFarm.tmx для мода «Эхо Сумрачной Долины».

Карта 40x40 в формате Tiled (TMX), совместимом со Stardew Valley:
  * Ground         — трава, дорога, лужи, грядка чёрных роз
  * Back           — забор по периметру
  * Front          — сарай, крыльцо, колодец
  * Paths          — проходимая дорога (свойство passable)
  * Overhead       — пустой слой поверх головы
  * Buildables     — место для построек
  * Water          — лужи (swimmable)
  * AlwaysObjects  — объекты, которые нельзя убрать
  * Properties     — Distant, FarmType и т.д.
  * Warp           — клетка обратного выхода в Лес
  * Objects        — интерактивные точки: колодец, скамейка, разбитое радио, ива

Запуск:  python3 tools/build_map.py
Выход:   assets/Maps/AbandonedFarm.tmx + assets/Maps/tiles.tsx + placeholder.png
"""
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from PIL import Image

W, H = 40, 40
TILE = 16
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "Maps")

PALETTE = [
    (52, 74, 58),    # gid 1 — тёмная сырая трава
    (90, 88, 80),    # gid 2 — мокрая земля / дорога
    (70, 96, 110),   # gid 3 — лужа (отражение неба)
    (40, 52, 46),    # gid 4 — кустарник / сорняки
    (62, 60, 66),    # gid 5 — камень / бетон
    (30, 34, 40),    # gid 6 — стена сарая
    (78, 62, 48),    # gid 7 — дерево крыльца
    (46, 70, 52),    # gid 8 — влажный мох
]


def gen_tileset_png(path):
    img = Image.new("RGBA", (TILE * len(PALETTE), TILE))
    px = img.load()
    for i, col in enumerate(PALETTE):
        for dy in range(TILE):
            for dx in range(TILE):
                shade = 12 if (dx + dy) % 4 == 0 else 0
                px[i * TILE + dx, dy] = (col[0] + shade, col[1] + shade, col[2] + shade, 255)
    img.save(path)


def blank(v=0):
    return [[v] * W for _ in range(H)]


_layer_id = [1]

def make_layer(name, grid, props=None):
    layer = ET.Element("layer", {"id": str(_layer_id[0]), "name": name,
                                 "width": str(W), "height": str(H)})
    _layer_id[0] += 1
    data = ET.SubElement(layer, "data", {"encoding": "csv", "tilewidth": str(W),
                                         "tileheight": str(H)})
    # каждая строка тайлов — отдельный текстовый потомок с переводом строки;
    # парсеры (Tiled/pytmx/Stardew) склеивают их в один CSV-поток
    for row in grid:
        data.append(ET.Comment(""))  # no-op,保持 структуру простой
        data.remove(data[-1])
        t = ET.Text if False else None
        if len(data):
            data[-1].tail = "\n" + ",".join(str(x) for x in row)
        else:
            data.text = ",".join(str(x) for x in row)
    data.tail = "\n"
    if props:
        cp = ET.SubElement(layer, "properties", {"version": "3"})
        for k, v in props.items():
            p = ET.SubElement(cp, "property", {"name": k, "value": str(v)})
    return layer


# ---------------- контент ----------------
ground = blank(1)
for y in range(H):
    for x in range(W):
        if (x * 7 + y * 13) % 23 == 0:
            ground[y][x] = 8
for y in range(8, 34):
    for x in range(9, 13):
        ground[y][x] = 2
for x in range(12, 30):
    ground[20][x] = 2
for (px, py, r) in [(18, 26, 3), (30, 12, 2), (7, 33, 2)]:
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            x, y = px + dx, py + dy
            if 0 <= x < W and 0 <= y < H and dx * dx + dy * dy <= r * r:
                ground[y][x] = 3
for y in range(24, 28):
    for x in range(26, 32):
        ground[y][x] = 4 if (x + y) % 2 else 8

back = blank(0)
for x in range(W):
    back[0][x] = back[H - 1][x] = 5
for y in range(H):
    back[y][0] = back[y][W - 1] = 5
back[H - 1][9] = back[H - 1][12] = 0  # дыра в заборе у дороги — вход на хутор

front = blank(0)
for y in range(10, 20):
    for x in range(14, 26):
        front[y][x] = 6
for y in range(18, 20):
    for x in range(16, 24):
        front[y][x] = 7
for y in range(20, 22):
    for x in range(21, 23):
        front[y][x] = 5

paths = blank(0)
for y in range(8, 34):
    for x in range(9, 13):
        paths[y][x] = 1
for x in range(12, 30):
    paths[20][x] = 1

water = blank(0)
for (px, py, r) in [(18, 26, 3), (30, 12, 2), (7, 33, 2)]:
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            x, y = px + dx, py + dy
            if 0 <= x < W and 0 <= y < H and dx * dx + dy * dy <= r * r:
                water[y][x] = 1

always = blank(0)
for y in range(10, 20):
    for x in range(14, 26):
        always[y][x] = 1
for y in range(20, 22):
    for x in range(21, 23):
        always[y][x] = 1

warp_grid = blank(0)
warp_grid[H - 1][10] = 1  # клетка обратного варпа

# ================= TMX =================
root = ET.Element("map", {
    "version": "1.10", "tiledversion": "1.10.2", "orientation": "orthogonal",
    "renderorder": "right-down", "width": str(W), "height": str(H),
    "tilewidth": str(TILE), "tileheight": str(TILE), "infinite": "0",
    "nextlayerid": str(_layer_id[0] + 1), "nextobjectid": "5",
})

ts = ET.SubElement(root, "tileset", {"firstgid": "1", "source": "tiles.tsx"})

root.append(make_layer("Ground", ground))
root.append(make_layer("Back", back))
root.append(make_layer("Front", front))
root.append(make_layer("Paths", paths, {"passable": True}))
root.append(make_layer("Overhead", blank(0)))
root.append(make_layer("Buildables", blank(0), {"passable": False}))
root.append(make_layer("Water", water, {"passable": False, "swimmable": True}))
root.append(make_layer("AlwaysObjects", always, {"passable": False}))
root.append(make_layer("Properties", blank(0), {
    "Distant": True, "CanBeSetDown": False, "CanBeGrabbed": False,
    "FarmType": "Forest", "RevealDefault": 0,
}))
root.append(make_layer("Warp", warp_grid))

obj_layer = ET.Element("objectgroup", {"id": str(_layer_id[0]), "name": "Objects",
                                       "draworder": "topdown", "opacity": "1",
                                       "visible": "1", "x": "0", "y": "0"})
_layer_id[0] += 1
objects = [
    (1, "Well", 21, 20),
    (2, "Bench", 13, 22),
    (3, "BrokenRadio", 24, 19),
    (4, "Willow", 6, 30),
]
for oid, name, tx, ty in objects:
    o = ET.SubElement(obj_layer, "object", {"id": str(oid), "name": name, "type": "",
                                            "x": str(tx * TILE), "y": str(ty * TILE),
                                            "width": str(TILE), "height": str(TILE)})
    ocp = ET.SubElement(o, "properties", {"version": "3"})
    ET.SubElement(ocp, "property", {"name": "TileIndex", "value": "0"})
    ET.SubElement(ocp, "property", {"name": "TileObject", "value": "true"})
root.append(obj_layer)

# prettify без разрушения CSV-текста (minidom добавлял переводы строк внутрь <data>)
raw = ET.tostring(root, encoding="unicode")
root_xml = minidom.parseString(raw)
for node in root_xml.getElementsByTagName("*"):
    if node.tagName == "data":
        node.normalize()
lines = []

def ser(node, indent):
    tag = node.tagName
    attrs = "".join(f' {a.name}="{a.value}"' for a in node.attributes.values())
    text = "".join(c.data for c in node.childNodes if c.nodeType == c.TEXT_NODE)
    kids = [c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE]
    pad = "  " * indent
    if not kids and not text:
        lines.append(f'{pad}<tag{attrs}/>'.replace("<tag", "<" + tag))
        return
    if kids and not text.strip():
        lines.append(f"{pad}<{tag}{attrs}>")
        for k in kids:
            ser(k, indent + 1)
        lines.append(f"{pad}</{tag}>")
        return
    if text and "\n" in text:
        lines.append(f"{pad}<{tag}{attrs}>{text}</{tag}>")
    else:
        lines.append(f"{pad}<{tag}{attrs}>{text.strip()}</{tag}>")

for node in root_xml.childNodes:
    if node.nodeType == node.ELEMENT_NODE:
        ser(node, 0)
tmx_path = os.path.abspath(os.path.join(OUT_DIR, "AbandonedFarm.tmx"))
with open(tmx_path, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + "\n".join(lines) + "\n")

# --------- tiles.tsx ----------
tsx = ET.Element("tileset", {"version": "1.10", "tiledversion": "1.10.2",
                             "name": "TwilightTiles", "tilecount": str(len(PALETTE)),
                             "columns": str(len(PALETTE)), "tilewidth": str(TILE),
                             "tileheight": str(TILE), "spacing": "0", "margin": "0"})
ET.SubElement(tsx, "image", {"source": "placeholder.png",
                             "width": str(TILE * len(PALETTE)), "height": str(TILE)})
with open(os.path.abspath(os.path.join(OUT_DIR, "tiles.tsx")), "w", encoding="utf-8") as f:
    f.write(minidom.parseString(ET.tostring(tsx, encoding="utf-8")).toprettyxml(indent="  "))

gen_tileset_png(os.path.abspath(os.path.join(OUT_DIR, "placeholder.png")))

print("OK:", tmx_path)
