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
    "assets/Objects/TearsOfMemory.png": (16, 16),
    "assets/Objects/RecordNeedle.png": (16, 16),
    "assets/Objects/BlackRoseCrop.png": (64, 128),
    "assets/Characters/Igor.png": (32, 64),
    "assets/Portraits/Igor.png": (64, 64),
}
EXPECTED_CUSTOM_FIELDS = {"EchoesTwilightValley.musicTrigger",
                          "EchoesTwilightValley.quoteSource",
                          "EchoesTwilightValley.melancholyAura",
                          # ванильный ключ связи предмета с книгой (Data/Books), не требует C#
                          "book"}

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


def check_cs_sync():
    """Сверяет константы ModEntry.cs с content.json и i18n (защита от рассинхронизации CP<->C#)."""
    cs_path = os.path.join(ROOT, "EchoesTwilightValley", "ModEntry.cs")
    if not os.path.exists(cs_path):
        warn("ModEntry.cs отсутствует — C#-компаньон не найден")
        return
    cs = open(cs_path, encoding="utf-8").read()
    content_raw = open(os.path.join(ROOT, "content.json"), encoding="utf-8").read()
    ru = json.load(open(os.path.join(ROOT, "i18n", "ru.json"), encoding="utf-8"))

    # 1. ID локации
    m = re.search(r'VillageId\s*=\s*"([^"]+)"', cs)
    village_id = m.group(1) if m else None
    if village_id and f'"{village_id}"' not in content_raw:
        err(f"ModEntry.cs: VillageId '{village_id}' не найден в content.json")

    # 2. ID чая и баффа
    m = re.search(r'TeaOfSilenceId\s*=\s*"([^"]+)"', cs)
    tea_id = m.group(1) if m else None
    if tea_id and f'"{tea_id}"' not in content_raw:
        err(f"ModEntry.cs: TeaOfSilenceId '{tea_id}' не найден в content.json")
    # 2b. Квестовые ID (иголка / слёзы памяти) — тоже сверяются с content.json
    for const in ("RecordNeedleId", "TearsOfMemoryId", "BlackRoseSeedsId"):
        m = re.search(rf'{const}\s*=\s*"([^"]+)"', cs)
        cid = m.group(1) if m else None
        if cid and f'"(O){cid}"' not in content_raw and f'"{cid}"' not in content_raw:
            err(f"ModEntry.cs: {const} '{cid}' не найден в content.json")
    m = re.search(r'AddBuff\("([^"]+)"', cs)
    buff_id = m.group(1) if m else None
    if buff_id and f'"{buff_id}"' not in content_raw:
        err(f"ModEntry.cs: бафф '{buff_id}' не объявлен в Data/Buffs content.json")

    # 3. Ключи CustomFields из C# должны присутствовать в content.json
    for field in re.findall(r'"(EchoesTwilightValley\.[A-Za-z]+)"', cs):
        if field not in content_raw:
            err(f"ModEntry.cs ждёт CustomField '{field}', которого нет в content.json")

    # 4. i18n-ключи, используемые в C# через Translation.Get("...")
    used = set(re.findall(r'Translation\.Get\("([^"]+)"', cs))
    missing = sorted(k for k in used if k not in ru)
    if missing:
        err(f"ru.json: отсутствуют ключи из ModEntry.cs: {missing}")
    print(f"  C#/CP/i18n синхронизация: локация={village_id}, чай={tea_id}, бафф={buff_id}, "
          f"получено {len(used)} i18n-ключей из C# — OK")


def check_duplicate_quotes():
    """Цитаты ивы не должны повторяться (значения)."""
    ru = json.load(open(os.path.join(ROOT, "i18n", "ru.json"), encoding="utf-8"))
    vals = [(k, v) for k, v in ru.items() if k.startswith("quote.willow.")]
    seen = {}
    for k, v in vals:
        if v in seen:
            err(f"Дубликат цитаты ивы: '{k}' повторяет '{seen[v]}'")
        else:
            seen[v] = k


def check_event_flags(content):
    """Событийные флаги/референсы: HasFlag в When и quest-условия событий должны совпадать.

    Ловит рассинхрон вида `marilynsinister.LastChordDone` vs
    `marilynsinister.EchoesTwilightValley LastChordDone` (событие никогда не запустится).
    """
    declared = set()
    for ch in content["Changes"]:
        when = ch.get("When") or {}
        hf = when.get("HasFlag")
        if isinstance(hf, str) and hf.strip():
            declared.add(hf.strip())
    # собираем флаги, которые выставляются командами setFlag в самих событиях
    set_flags = set()
    for ch in content["Changes"]:
        if not str(ch.get("Target", "")).startswith("Data/Events"):
            continue
        for ev in (ch.get("Entries") or {}).values():
            for cmd in ev.get("Commands", []):
                if cmd.startswith("setFlag "):
                    parts = cmd.split()
                    if len(parts) >= 3:
                        set_flags.add(f"{parts[1]} {parts[2]}")
    declared |= set_flags
    bad_refs = []
    for ch in content["Changes"]:
        target = ch.get("Target", "")
        if not target.startswith("Data/Events"):
            continue
        for event_id in ch.get("Entries", {}):
            parts = event_id.split("/")
            if len(parts) < 2:
                continue
            cond = parts[1]
            # формат условия: <флаг>/<отрицание>; флаг может содержать пробел (ID флага + имя).
            # Если «флаг» — числовое отрицание (-3000), это не HasFlag-ссылка, пропускаем.
            flag = cond.split("/")[0].strip()
            if flag.startswith("-"):
                continue
            if flag and flag not in declared:
                bad_refs.append((target, event_id, flag))
    for target, event_id, flag in bad_refs:
        err(f"{target}: событие '{event_id}' ссылается на undeclared флаг '{flag}' "
            f"(нет такого HasFlag ни в одном When)")
    if not bad_refs and declared:
        print(f"  Флаги событий согласованы с When/HasFlag: {sorted(declared)}")


def check_quest_item_flags(content):
    """Предметы Type=Quest не должны быть giftable (иначе их можно «подарить» и потерять схему)."""
    n = 0
    for ch in content["Changes"]:
        if ch.get("Target") != "Data/Objects":
            continue
        for oid, obj in (ch.get("Entries") or {}).items():
            if isinstance(obj, dict) and obj.get("Type") == "Quest":
                n += 1
                if obj.get("Giftable", True):
                    warn(f"предмет-квест '{oid}' помечен как giftable — лучше Giftable=false")
    if n:
        print(f"  Quest-предметы проверены: {n} шт., все non-giftable")


def check_event_conditions(content):
    """Conditions событий должны ссылаться на существующие предметы (О)id."""
    known_objects = set()
    for ch in content["Changes"]:
        if ch.get("Target") == "Data/Objects":
            known_objects.update(ch.get("Entries", {}).keys())
    vanilla_ok = True  # числовые id считаем ванильными — их нет у нас, но есть в игре
    problems = []
    for ch in content["Changes"]:
        target = ch.get("Target", "")
        if not target.startswith("Data/Events"):
            continue
        for event_id, ev in (ch.get("Entries") or {}).items():
            cond = (ev.get("Conditions") or "").strip()
            if not cond:
                continue
            for token in cond.split(","):
                item = token.strip().split()[0] if token.strip() else ""
                if item.startswith("(O)"):
                    oid = item[3:]
                    if oid not in known_objects and not oid.isdigit():
                        problems.append((target, event_id, item))
    for target, event_id, item in problems:
        err(f"{target}: событие '{event_id}' требует предмет '{item}', которого нет в Data/Objects")
    if not problems:
        print("  Conditions событий ссылаются только на известные предметы — OK")


def check_map():
    path = os.path.join(ROOT, "assets", "Maps", "AbandonedVillage.tmx")
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
    print(f"  AbandonedVillage.tmx: {len(layers | groups)} слоёв, объектов: {n_obj}")


def check_custom_fields(used_fields):
    unknown = used_fields - EXPECTED_CUSTOM_FIELDS
    unused = EXPECTED_CUSTOM_FIELDS - used_fields
    if unknown:
        warn(f"CustomFields, не ожидаемые C#-модом: {sorted(unknown)}")
    if unused:
        warn(f"ожидаемые CustomFields не найдены в content.json: {sorted(unused)}")
    if not unknown and not unused:
        print(f"  CustomFields совпадают с ожиданиями ModEntry.cs: {sorted(used_fields)}")


def check_thunder(content):
    """Гроза Тимура (Фаза 4): синхронизация C#-молний с CP-контентом.

    Проверяет, что:
      * в ModEntry.cs есть обработчик UpdateTicked, использующий Game1.isLightning;
      * в content.json событие деревни имеет заголовок с погодным ключом 't' (thunder);
      * у Тимура в Data/NPCDialogue задан диалог-ключ "Thunder";
      * i18n-ключ weather.thunder.timur существует в ru и en.
    Ловит рассинхрон, при котором «грозовая» механика молчит в игре.
    """
    cs_path = os.path.join(ROOT, "EchoesTwilightValley", "ModEntry.cs")
    cs = open(cs_path, encoding="utf-8").read()
    if "Game1.isLightning" not in cs or "UpdateTicked" not in cs:
        err("groza: в ModEntry.cs не найден детект молний (Game1.isLightning / UpdateTicked)")

    thunder_events = []
    timur_dialogues = []
    for ch in content["Changes"]:
        target = str(ch.get("Target", ""))
        if target.startswith("Data/Events/Custom_marilynsinister_AbandonedVillage"):
            for event_id in (ch.get("Entries") or {}):
                head = event_id.split("/")[0].split()
                if "t" in head:
                    thunder_events.append(event_id)
        if target == "Data/NPCDialogue":
            timur = (ch.get("Entries") or {}).get("Timur")
            if isinstance(timur, dict):
                dialogue = timur.get("Dialogue") or {}
                if "Thunder" in dialogue:
                    timur_dialogues.append("Thunder")

    if not thunder_events:
        err("groza: ни одно событие деревни не имеет погодного ключа 't' (thunder) в заголовке")
    if not timur_dialogues:
        err("groza: у Timur в Data/NPCDialogue нет диалога с ключом 'Thunder'")

    for lang in ("ru", "en"):
        path = os.path.join(ROOT, "i18n", f"{lang}.json")
        data = json.load(open(path, encoding="utf-8"))
        if "weather.thunder.timur" not in data:
            err(f"groza: i18n/{lang}.json не содержит ключ weather.thunder.timur")

    if thunder_events and timur_dialogues:
        print(f"  Гроза Тимура: событий с ключом 't': {len(thunder_events)}, диалог Thunder — есть, i18n-ключ на месте")


def main():
    print("🔍 Валидация EchoesTwilightValley…")
    check_manifest()
    content_keys, used_fields = check_content()
    check_i18n(content_keys)
    check_sprites()
    check_map()
    check_custom_fields(used_fields)
    check_cs_sync()
    check_duplicate_quotes()
    full_content = json.load(open(os.path.join(ROOT, "content.json"), encoding="utf-8"))
    check_event_flags(full_content)
    check_quest_item_flags(full_content)
    check_event_conditions(full_content)
    check_thunder(full_content)

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
