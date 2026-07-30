"""Добавление достоинств и недостатков из Руководства для игроков.

Основная книга дала 85 записей, Руководство добавляет ещё 18: раздел
«Новые Достоинства и Недостатки» (стр. 120–123).

Сторона записи — достоинство или недостаток — из текста не выводится вовсе:
книга различает их только тем, под каким из двух заголовков запись стоит.
Рейтинг набран точками прямо в строке имени, и он же идёт в `points`.

Перевод Руководства фанатский; источник помечается прямо в записи.
Скрипт идемпотентен: _id выводится из названия.

    python tools/add_merits.py --dry-run
    python tools/add_merits.py
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
PAGES = (119, 124)
SOURCE_NOTE = "Руководство для игроков"
ICON = "systems/vtm5e/assets/icons/items/discipline.png"

# Разряд в книге -> папка компендиума. Три разряда ложатся в существующие
# папки, два своих в компендиуме нет: «Мифические» и «Прочие».
GROUPS = {
    "Достоинства внешности": "Внешность",
    "Недостатки внешности": "Внешность",
    "Достоинства питания": "Пищевые привычки",
    "Недостаток питания": "Пищевые привычки",
    "Мифические достоинства": "Мифические",
    "Мифические недостатки": "Мифические",
    "Другие достоинства": "Прочие",
    "Другие недостатки": "Прочие",
}
PARENT = "Особенности"
NEW_FOLDERS = ("Мифические", "Прочие")

# Слова, которые при снятии капса остаются с заглавной: имя собственное
# и игровой термин. Всё остальное книга набирает строчными.
KEEP_CAPS = {"ньюит": "Ньюит", "воля": "Воля", "крови": "Крови",
             "кровь": "Кровь"}


def display_name(caps: str) -> str:
    words = [KEEP_CAPS.get(w.lower(), w.lower()) for w in caps.split()]
    return " ".join(words)[:1].upper() + " ".join(words)[1:]


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


def merit_entry(section, folder):
    flaw = section["side"].startswith("Недостат")
    dots = "•" * max(section["rating"], 1)
    title = display_name(section["name"])
    name = f"Недостаток: ({dots}) {title}" if flaw else f"{dots} {title}"
    _id = make_id("merit:" + section["name"])
    body = (f"<p><em>Источник: {SOURCE_NOTE}</em></p>"
            + to_html(section["text"]))
    return {
        "folder": folder,
        "name": name,
        "type": "feature",
        "_id": _id,
        "img": ICON,
        "system": {
            "description": body, "bonuses": [],
            "uses": {"max": 0, "current": 0, "enabled": False},
            "featuretype": "flaw" if flaw else "merit",
            "points": max(section["rating"], 1), "macroid": "",
        },
        "effects": [], "sort": 0, "ownership": {"default": 0}, "flags": {},
        "_stats": {"compendiumSource": None, "duplicateSource": None,
                   "exportSource": None, "coreVersion": "13.346",
                   "systemId": "vtm5e", "systemVersion": "5.1.4",
                   "createdTime": 0, "modifiedTime": 0,
                   "lastModifiedBy": None},
        "_key": f"!items!{_id}",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    source = module_dir() / "packs" / "advantages-flaws" / "_source"

    folders, existing = {}, {}
    for path in source.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        existing[data["_id"]] = path
        if data.get("_key", "").startswith("!folders!"):
            folders[data["_id"]] = data

    by_name = {}
    for f in folders.values():
        parent = folders.get(f.get("folder"))
        by_name[(parent["name"] if parent else None, f["name"])] = f["_id"]

    written = []
    parent_id = by_name.get((None, PARENT))
    if parent_id is None:
        sys.exit(f"не найдена папка {PARENT!r}")

    for i, name in enumerate(NEW_FOLDERS, 1):
        if (PARENT, name) not in by_name:
            entry = folder_entry(name, parent_id, 900000 + i * 1000)
            by_name[(PARENT, name)] = entry["_id"]
            written.append(("папка", f"{PARENT} / {name}", entry))

    doc = fitz.open(SOURCES / GUIDE)
    sections = guide_clans.merits(
        doc, PAGES, fix_encoding, normalize, page_lines)

    unknown = sorted({s["group"] for s in sections
                      if s["group"] not in GROUPS})
    if unknown:
        sys.exit(f"незнакомые разряды в книге: {unknown}")

    for section in sections:
        folder = by_name.get((PARENT, GROUPS[section["group"]]))
        if folder is None:
            print(f"  ! нет папки {GROUPS[section['group']]}")
            continue
        entry = merit_entry(section, folder)
        written.append(("запись", entry["name"], entry))

    for kind, label, entry in written:
        path = existing.get(entry["_id"]) or \
            source / safe_filename(entry["name"], entry["_id"])
        mark = "обновлено" if entry["_id"] in existing else "создано"
        if kind == "запись":
            print(f"  {mark:<9} {label}")
        if not args.dry_run:
            text = json.dumps(entry, ensure_ascii=False, indent=2) + "\n"
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

    items = [w for w in written if w[0] == "запись"]
    new_folders = [w for w in written if w[0] == "папка"]
    verb = "добавилось бы" if args.dry_run else "добавлено"
    print(f"\n{verb}: записей {len(items)}, папок {len(new_folders)}")
    for _, label, _ in new_folders:
        print(f"  папка: {label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
