"""Добавление сил Дисциплин из Руководства для игроков.

Основная книга дала 121 запись, Руководство добавляет ещё 71: по три-пять
новых сил почти к каждой Дисциплине, девять ритуалов Кровавого чародейства
и целую Дисциплину Обливион с церемониями.

Обливиона и его церемоний в компендиуме нет вовсе, поэтому под них создаются
папки — корневая и пять уровневых, как у остальных Дисциплин.

Перевод Руководства фанатский; источник помечается прямо в записи.
Скрипт идемпотентен: _id выводится из названия силы.

    python tools/add_powers.py --dry-run
    python tools/add_powers.py
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fitz  # noqa: E402
import guide_clans  # noqa: E402
from add_clans import is_module_dir, make_id, safe_filename  # noqa: E402
from extract_pdf import GUIDE, SOURCES, page_lines  # noqa: E402
from pdfkit import fix_encoding, normalize, to_html  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PAGES = (68, 110)
SOURCE_NOTE = "Руководство для игроков"

# Как Дисциплина названа в Руководстве -> (папка в компендиуме, код системы,
# иконка). Руководство зовёт Potence «Могуществом»; приводим к основной книге.
DISCIPLINES = {
    "Анимализм": ("Анимализм", "animalism", "330px-Animalism_symbol.png"),
    "Ясновидение": ("Ясновидение", "auspex", "330px-Auspex_symbol.png"),
    "Стремительность": ("Стремительность", "celerity", "330px-Aclarity_symbol.png"),
    "Доминирование": ("Доминирование", "dominate", "330px-Dominate_symbol.png"),
    "Стойкость": ("Стойкость", "fortitude", "330px-Fortitude_symbol.png"),
    "Сокрытие": ("Сокрытие", "obfuscate", "330px-Obfuscate_symbol.png"),
    "Могущество": ("Мощь", "potence", "330px-Potence_symbol.png"),
    "Величие": ("Величие", "presence", "330px-Presence_symbol.png"),
    "Метаморфозы": ("Метаморфозы", "protean", "330px-Protean_symbol.png"),
    "Кровавое чародейство": ("Кровавое чародейство", "sorcery",
                             "330px-Blood_Sorcery_symbol.png"),
    "Ритуалы кровавого чародейства": ("Ритуалы", "rituals",
                                      "330px-Blood_Sorcery_symbol.png"),
    "Обливион": ("Обливион", "oblivion", "1024px-Oblivion_symbol.png"),
    "Церемонии Обливиона": ("Церемонии Обливиона", "oblivion",
                            "1024px-Oblivion_symbol.png"),
}

# Папки, которых в компендиуме нет: Обливион в него не входил.
NEW_FOLDERS = ("Обливион", "Церемонии Обливиона")
LEVELS = [f"Уровень {n}" for n in range(1, 6)]


def module_dir():
    return next(p for p in ROOT.iterdir() if is_module_dir(p))


def folder_entry(name, parent, sort):
    _id = make_id("folder:" + name + (parent or ""))
    return {
        "name": name, "sorting": "a", "folder": parent, "type": "Item",
        "_id": _id, "description": "", "sort": sort, "color": "#9f90a2",
        "flags": {},
        "_stats": {"compendiumSource": None, "duplicateSource": None,
                   "coreVersion": "13.346", "systemId": "vtm5e",
                   "systemVersion": "5.1.4", "createdTime": 0,
                   "modifiedTime": 0, "lastModifiedBy": None},
        "_key": f"!folders!{_id}",
    }


def power_entry(section, folder, code, icon):
    _id = make_id("power:" + section["name"])
    body = (f"<p><em>Источник: {SOURCE_NOTE}</em></p>"
            + to_html(guide_clans.split_labels(section["text"])))
    return {
        "folder": folder,
        "name": section["name"],
        "type": "power",
        "_id": _id,
        "img": f"modules/vampire-the-masquerade-5e-compendium-ru/packs/assets/{icon}",
        "system": {
            "description": body, "bonuses": [], "discipline": code,
            "duration": "", "level": section["level"], "dicepool": {},
            "cost": 1, "gamesystem": "vampire", "macroid": "",
        },
        "effects": [], "sort": 0, "ownership": {"default": 0}, "flags": {},
        "_stats": {"compendiumSource": None, "duplicateSource": None,
                   "coreVersion": "13.346", "systemId": "vtm5e",
                   "systemVersion": "5.1.4", "createdTime": 0,
                   "modifiedTime": 0, "lastModifiedBy": None,
                   "exportSource": None},
        "_key": f"!items!{_id}",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    source = module_dir() / "packs" / "disciplines" / "_source"

    folders, existing = {}, {}
    for path in source.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        existing[data["_id"]] = path
        if data.get("_key", "").startswith("!folders!"):
            folders[data["_id"]] = data

    by_name = {}
    for f in folders.values():
        parent = folders.get(f.get("folder"))
        key = (parent["name"] if parent else None, f["name"])
        by_name[key] = f["_id"]

    written = []

    # Папки для Обливиона: корневая и пять уровневых.
    for root_name in NEW_FOLDERS:
        if (None, root_name) not in by_name:
            entry = folder_entry(root_name, None, 900000)
            by_name[(None, root_name)] = entry["_id"]
            written.append(("папка", root_name, entry))
        root_id = by_name[(None, root_name)]
        for i, level in enumerate(LEVELS, 1):
            if (root_name, level) not in by_name:
                entry = folder_entry(level, root_id, i * 100000)
                by_name[(root_name, level)] = entry["_id"]
                written.append(("папка", f"{root_name} / {level}", entry))

    doc = fitz.open(SOURCES / GUIDE)
    sections = guide_clans.discipline_powers(
        doc, PAGES, fix_encoding, normalize, page_lines)

    unknown = sorted({s["discipline"] for s in sections
                      if s["discipline"] not in DISCIPLINES})
    if unknown:
        sys.exit(f"незнакомые Дисциплины в книге: {unknown}")

    for section in sections:
        folder_name, code, icon = DISCIPLINES[section["discipline"]]
        level = f"Уровень {section['level']}"
        folder = by_name.get((folder_name, level))
        if folder is None:
            print(f"  ! нет папки {folder_name} / {level}")
            continue
        written.append(("сила", section["name"],
                        power_entry(section, folder, code, icon)))

    for kind, label, entry in written:
        path = existing.get(entry["_id"]) or \
            source / safe_filename(entry["name"], entry["_id"])
        if not args.dry_run:
            text = json.dumps(entry, ensure_ascii=False, indent=2) + "\n"
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

    powers = [w for w in written if w[0] == "сила"]
    new_folders = [w for w in written if w[0] == "папка"]
    verb = "добавилось бы" if args.dry_run else "добавлено"
    print(f"{verb}: сил {len(powers)}, папок {len(new_folders)}")
    for _, label, _ in new_folders:
        print(f"  папка: {label}")
    short = [w[1] for w in powers if len(w[2]["system"]["description"]) < 200]
    if short:
        print(f"\nкороткие описания ({len(short)}): {short}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
