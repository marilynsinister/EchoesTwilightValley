#!/usr/bin/env python3
"""Валидатор структуры мода «Эхо Сумрачной Долины».

Проверяет:
  1. manifest.json — валидный JSON, обязательные поля, UniqueID.
  2. content.json  — валидный JSON, Format >= 2.0, все Action из белого списка CP.
  3. i18n-ключи    — каждое i18n<key> в content.json существует в ru.json (и en.json, если есть).
  4. PNG-спрайты   — файлы существуют и имеют допустимые размеры сетки (кратность 16 по высоте).
  5. TMX-карта     — парсится ElementTree, содержит слой Warp и группу Objects.
  6. CustomFields  — ключи EchoesTwilightValley.* в content.json ожидаются C#-компаньоном.

Запуск:  python3 tools/validate.py   (из корня репозитория)
Выход:   0 — всё ок; 1 — найдены проблемы.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_ACTIONS = {
    "EditData", "EditImage", "Load", "EditMap", "LoadDynamicAsset",
    "Include", "SetProperties", "Log",
}
# Ожидаемые кастомные спрайты: путь -> минимальная ширина/высота (0 = не проверять)
SPRITE_CHECKS = {
    "assets/Objects/TeaOfSilence.png": (16, 16),
    "assets/Objects/BlackRose.png": (16, 16),
    "assets/Objects/BlackRoseSeeds.png": (16, 16),
    "assets/Objects/VinylRecord.png": (48, 96),
    "assets/Objects/WeepingWillow.png": (64, 64),
    "assets/Objects/Turntable.png": (48, 64),
    "assets/Objects/BlackRoseCrop.png": (64, 128),
    "assets/Characters/Igor.png": (32, 64),
    "assets/Portraits/Igor.png": (64, 64),
}
EXPECTED_CUSTOM_FIELDS = {"EchoesTwilightValley.musicTrigger",
                          "EchoesTwilightValley.quoteSource",
                          "EchoesTwilightValley.melancholyAura"}

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def png_size(path):
    """Размер PNG без внешних зависимостей (IHDR-заголовок)."""
    with open(path, "rb") as f:
        head = f.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    w = int.from_bytes(head[16:20], "big")
    h = int.from_bytes(head[20:24], "big")
    return w, h


def check_manifest():
    path = os.path.join(ROOT, "manifest.json")
    data = json.load(open(path, encoding="utf-8"))
    for field in ("Name", "Author", "Version", "UniqueID", "Description"):
        if field not in data:
            err(f"manifest.json: нет поля '{field}'")
    deps = {d.get("UniqueID") for d in data.get("Dependencies", [])}
    if "Pathoschild.ContentPatcher" not in deps:
        err("manifest.json: нет зависимости Pathoschild.ContentPatcher")
    print(f"  manifest.json: {data['Name']} v{data['Version']} — OK")
    return data


def collect_i18n_keys(node, found):
    if isinstance(node, str):
        found.update(re.findall(r"i18n<( [^>]+ )>", node.replace("<", "< ", 0)) if False else
                     re.findall(r"i18n<([^>]+)>", node))
    elif isinstance(node, dict):
        for v in node.values():
            collect_i18n_keys(v, found)
    elif isinstance(node, list):
        for v in node:
            collect_i18n_keys(v, found)


def check_content():
    path = os.path.join(ROOT, "content.json")
    data = json.load(open(path, encoding="utf-8"))
    fmt = tuple(int(x) for x in data.get("Format", "0").split("."))
    if fmt < (2, 0):
        err(f"content.json: Format {fmt} слишком старый для Stardew 1.6 (нужен >= 2.0)")
    changes = data.get("Changes", [])
    used_fields = set()
    for i, ch in enumerate(changes):
        action = ch.get("Action")
        if action not in ALLOWED_ACTIONS:
            err(f"content.json: Changes[{i}] неизвестный Action '{action}'")
        target = ch.get("Target", "")
        # собираем CustomFields из EditData по BigCraftables
        for entries in ([ch.get("Entries")] if isinstance(ch.get("Entries"), dict) else []):
            for key, val in (entries or {}).items():
                if isinstance(val, dict) and "CustomFields" in val:
                    used_fields.update(val["CustomFields"].keys())
    keys = set()
    collect_i18n_keys(data, keys)
    print(f"  content.json: {len(changes)} изменений, {len(keys)} уникальных i18n-ключей")
    return keys, used_fields


def check_i18n(content_keys):
    ru_path = os.path.join(ROOT, "i18n", "ru.json")
    ru = json.load(open(ru_path, encoding="utf-8"))
    missing = sorted(k for k in content_keys if k not in ru)
    if missing:
        err(f"ru.json: отсутствуют ключи из content.json: {missing}")
    quotes = [k for k in ru if k.startswith("quote.willow.") and k != "quote.willow.easter"]
    easter = "quote.willow.easter" in ru
    print(f"  i18n/ru.json: {len(ru)} ключей; цитат ивы: {len(quotes)} (+пасхальная: {'да' if easter else 'НЕТ'})")
    if len(quotes) < 15:
        warn(f"план роадмапа: 15–20 цитат, сейчас {len(quotes)}")
    en_path = os.path.join(ROOT, "i18n", "en.json")
    if os.path.exists(en_path):
        en = json.load(open(en_path, encoding="utf-8"))
        missing_en = sorted(k for k in ru if k not in en)
        if missing_en:
            warn(f"en.json: отсутствует {len(missing_en)} ключей из ru.json")
        else:
            print(f"  i18n/en.json: покрытие полное ({len(en)} ключей)")
    else:
        warn("en.json ещё не создан (Фаза 5)")


def check_sprites():
    ok = 0
    for rel, (min_w, min_h) in SPRITE_CHECKS.items():
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            err(f"спрайт отсутствует: {rel}")
            continue
        size = png_size(p)
        if size is None:
            err(f"битый PNG: {rel}")
            continue
        w, h = size
        if w % 16 or h % 16:
            warn(f"{rel}: размер {w}x{h} кратен 16? (нет) — проверьте сетку тайлов")
        if w < min_w or h < min_h:
            err(f"{rel}: размер {w}x{h} меньше ожидаемого {min_w}x{min_h}")
        else:
            ok += 1
    print(f"  спрайты: {ok}/{len(SPRITE_CHECKS)} файлов в порядке")


def check_map():
    path = os.path.join(ROOT, "assets", "Maps", "AbandonedFarm.tmx")
    tree = ET.parse(path)
    root = tree.getroot()
    layers = {l.get("name") for l in root.findall("layer")}
    groups = {g.get("name") for g in root.findall("group")}
    needed_layers = {"Ground", "Back", "Front", "Paths", "Overhead", "Buildables", "Water",
                     "AlwaysObjects", "Properties", "Warp"}
    missing = needed_layers - layers - groups
    if missing:
        err(f"TMX: отсутствуют слои {sorted(missing)}")
    obj_groups = [g for g in root.findall("objectgroup") if g.get("name") == "Objects"]
    n_obj = sum(len(g.findall("object")) for g in obj_groups)
    if n_obj == 0:
        err("TMX: группа Objects пуста — не будет колодца/радио/ивы")
    print(f"  AbandonedFarm.tmx: {len(layers | groups)} слоёв, объектов: {n_obj}")


def check_custom_fields(used_fields):
    unknown = used_fields - EXPECTED_CUSTOM_FIELDS
    unused = EXPECTED_CUSTOM_FIELDS - used_fields
    if unknown:
        warn(f"CustomFields, не ожидаемые C#-модом: {sorted(unknown)}")
    if unused:
        warn(f"ожидаемые CustomFields не найдены в content.json: {sorted(unused)}")
    if not unknown and not unused:
        print(f"  CustomFields совпадают с ожиданиями ModEntry.cs: {sorted(used_fields)}")


def main():
    print("🔍 Валидация EchoesTwilightValley…")
    check_manifest()
    content_keys, used_fields = check_content()
    check_i18n(content_keys)
    check_sprites()
    check_map()
    check_custom_fields(used_fields)

    for w in warnings:
        print(f"  ⚠️  {w}")
    for e in errors:
        print(f"  ❌ {e}")
    if errors:
        print(f"ИТОГ: ПРОВАЛ ({len(errors)} ошибок, {len(warnings)} предупреждений)")
        sys.exit(1)
    print(f"ИТОГ: OK ✅ ({len(warnings)} предупреждений)")


if __name__ == "__main__":
    main()
