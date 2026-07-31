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
import originals  # noqa: E402
from add_clans import is_module_dir, make_id, safe_filename  # noqa: E402
from extract_pdf import GUIDE, SOURCES, page_lines  # noqa: E402
from pdfkit import fix_encoding, normalize, to_html  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PAGES = (119, 124)
SOURCE_NOTE = "Руководство для игроков"
# Модуль объявляет систему wod5e — и путь к иконке обязан быть её.
# Пока стоял vtm5e, wod5e переносила пути при каждой загрузке мира
# и показывала плашку миграции на 246 записей.
ICON = "systems/wod5e/assets/icons/items/discipline.png"

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

# Глава «Кастомы»: свои перечни у каитиффов, слабокровных и гулей.
# У слабокровных папки уже есть — там лежат шестнадцать записей из Книги
# правил, и новые ложатся к ним.
CUSTOM_PAGES = (126, 146)
CUSTOM_FOLDERS = {
    ("Каитифф", "merit"): "Достоинства каитиффа",
    ("Каитифф", "flaw"): "Недостатки каитиффа",
    ("Слабокровные", "merit"): "Достоинства слабокровных",
    ("Слабокровные", "flaw"): "Недостатки слабокровных",
    ("Гули", "merit"): "Достоинства гулей",
    ("Гули", "flaw"): "Недостатки гулей",
}
NEW_FOLDERS = ("Мифические", "Прочие", "Достоинства каитиффа",
               "Недостатки каитиффа", "Достоинства гулей",
               "Недостатки гулей")

# Раздел «Фоны» (стр. 111–119) почти весь пересказывает Книгу правил, и эти
# записи в компендиуме давно есть. Новое выбирается поимённо: механически
# отличить пересказ от нового нельзя, а завести дубль Убежища легко.
#
# Фоны в паке лежат с featuretype «background» — и сам Фон, и привязанный
# к нему недостаток. Ноль очков означает сводную запись на все ступени.
BACKGROUND_PAGES = (110, 120)
BACKGROUND_PICKS = {
    "Враги": ("Союзники", "Недостаток: Враги", 0),
    "Страницы истории": ("Страницы истории", "Страницы истории", 0),
    "Линия крови": ("Страницы истории", "Линия крови", 0),
    "Торговля долгами": ("Мавла (или конкурент)", "Торговля долгами", 0),
    "ФУРКУС": ("Достоинства и недостатки убежища", "• Фуркус", 1),
    "МАШИНОСТРОИТЕЛЬНЫЙ ЦЕХ": ("Достоинства и недостатки убежища",
                               "• Машиностроительный цех", 1),
    "ОБЩЕСТВО": ("Достоинства и недостатки убежища",
                 "Недостаток: (•) Общество", 1),
    "ГОРОДСКИЕ ТАЙНЫ": ("Статус", "• Городские тайны", 1),
}
ASSETS = "Активы"
NEW_ASSET_FOLDERS = ("Страницы истории",)

# Слова, которые при снятии капса остаются с заглавной: имя собственное
# и игровой термин. Всё остальное книга набирает строчными.
KEEP_CAPS = {"ньюит": "Ньюит", "воля": "Воля", "крови": "Крови",
             "кровь": "Кровь", "каина": "Каина"}


def display_name(caps: str) -> str:
    words = [KEEP_CAPS.get(w.lower(), w.lower()) for w in caps.split()]
    joined = " ".join(words)
    name = joined[:1].upper() + joined[1:]
    # Машинный перевод названия правится по таблице; _id при этом выводится
    # из названия в книге, поэтому правка не заводит новую запись.
    return originals.RENAMES.get(name, name)


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
    # Раздел достоинств называет сторону заголовком («Недостатки внешности»),
    # глава «Кастомы» — отдельным полем. Приводим к одному виду.
    flaw = section["side"] in ("flaw",) or section["side"].startswith("Недостат")
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


def background_entry(section, folder, name, points):
    _id = make_id("background:" + section["name"])
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
            "featuretype": "background", "points": points, "macroid": "",
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
    placed = [(s, GROUPS[s["group"]]) for s in sections]

    custom = guide_clans.custom_merits(
        doc, CUSTOM_PAGES, fix_encoding, normalize, page_lines)
    unknown = sorted({(s["kind"], s["side"]) for s in custom
                      if (s["kind"], s["side"]) not in CUSTOM_FOLDERS})
    if unknown:
        sys.exit(f"незнакомые разделы «Кастомов»: {unknown}")
    placed += [(s, CUSTOM_FOLDERS[(s["kind"], s["side"])]) for s in custom]

    for section, folder_name in placed:
        folder = by_name.get((PARENT, folder_name))
        if folder is None:
            print(f"  ! нет папки {folder_name}")
            continue
        entry = merit_entry(section, folder)
        written.append(("запись", entry["name"], entry))

    # --- Фоны: только то, чего в компендиуме нет
    assets_id = by_name.get((None, ASSETS))
    if assets_id is None:
        sys.exit(f"не найдена папка {ASSETS!r}")
    for i, name in enumerate(NEW_ASSET_FOLDERS, 1):
        if (ASSETS, name) not in by_name:
            entry = folder_entry(name, assets_id, 950000 + i * 1000)
            by_name[(ASSETS, name)] = entry["_id"]
            written.append(("папка", f"{ASSETS} / {name}", entry))

    found = {}
    for section in guide_clans.backgrounds(
            doc, BACKGROUND_PAGES, fix_encoding, normalize, page_lines):
        if section["name"] in BACKGROUND_PICKS:
            found[section["name"]] = section
    missing = sorted(set(BACKGROUND_PICKS) - set(found))
    if missing:
        sys.exit(f"не нашлись в разделе Фонов: {missing}")

    for book_name, section in found.items():
        folder_name, entry_name, points = BACKGROUND_PICKS[book_name]
        folder = next((v for (parent, n), v in by_name.items()
                       if n == folder_name), None)
        if folder is None:
            print(f"  ! нет папки {folder_name}")
            continue
        entry = background_entry(section, folder, entry_name, points)
        written.append(("запись", entry["name"], entry))

    for kind, label, entry in written:
        wanted = source / safe_filename(entry["name"], entry["_id"])
        path = existing.get(entry["_id"], wanted)
        # Имя файла выводится из названия записи, а _id переживает правку
        # названия: без переименования рядом остался бы файл от прежнего.
        if path != wanted and not args.dry_run:
            path.unlink(missing_ok=True)
            path = wanted
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
