"""Виды котерий: пятнадцать из Книги правил и семь из Руководства.

Категории в компендиуме не было вовсе — под неё заводится пак и запись
в манифесте.

Руководство перепечатывает книжные виды под своими названиями: «Чемпионы»
вместо «Рыцарей», «Дозорные» вместо «Патруля», «Вехме» вместо «Фемгерихта».
Берём официальный перевод, а из Руководства — только те семь, которых
в Книге правил нет.

В системе wod5e типа «котерия» нет, как не было и «лоршита»: запись
заводится как feature с featuretype «background».

    python tools/add_coteries.py --dry-run
    python tools/add_coteries.py
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
from add_loresheets import register  # noqa: E402
from extract_pdf import (CORE, GUIDE, SOURCES,  # noqa: E402
                         extract_coterie_types, page_lines)
from pdfkit import fix_encoding, normalize, to_html  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PACK = "coteries"
PACK_LABEL = "Виды котерий"
# Модуль объявляет систему wod5e — и путь к иконке обязан быть её.
# Пока стоял vtm5e, wod5e переносила пути при каждой загрузке мира
# и показывала плашку миграции на 246 записей.
ICON = "systems/wod5e/assets/icons/items/discipline.png"
GUIDE_PAGES = (159, 171)
MERIT_PAGES = (172, 177)
DOMAIN_PAGES = (177, 182)
MEMBERSHIP_PAGES = (180, 193)
GUIDE_NOTE = "Руководство для игроков"

FOLDERS = ("Виды котерий", "Достоинства котерии", "Недостатки котерии",
           "Достоинства домена", "Достоинства членства")
DOMAIN_FOLDERS = ("Шассе", "Льен", "Портильон")

# Правленое название встречается и внутри текста: книга зовёт достоинство
# «Болтовыми отверстиями» в самом описании. Без этой замены запись говорила
# бы об одном, а называлась по-другому.
TEXT_FIXES = [
    ('"Болтовые отверстия"', "«Норы»"),
    ("Болтовые отверстия", "Норы"),
]

# Виды, которые Руководство перепечатывает под своим названием. Ключ —
# как названо в Руководстве, значение — официальное название из Книги
# правил. Такие записи из Руководства не берутся вовсе.
GUIDE_ALIASES = {
    "Чемпионы": "Рыцари",
    "Охотничья группа": "Загонщики",
    "Квестари": "Искатели",
    "Дозорные": "Патруль",
    "Плюмайры": "Пташки",
    "Вехме": "Фемгерихт",
}


def module_dir():
    return next(p for p in ROOT.iterdir() if is_module_dir(p))


def folder_entry(name, parent, sort):
    _id = make_id("coterie-folder:" + name + (parent or ""))
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


def entry(section, folder=None, name=None, points=0, kind="merit"):
    # _id выводится из названия в книге, а не из того, что показывается:
    # правка машинного перевода не должна заводить новую запись.
    _id = make_id(f"coterie:{section['kind']}:{section['name']}")
    head = ""
    if section.get("source"):
        head = f"<p><em>Источник: {section['source']}</em></p>"
    if section.get("resonance"):
        head += f"<p>■ Резонанс: {section['resonance']}</p>"
    if section.get("clan"):
        head += f"<p>■ Клан: {section['clan']}</p>"
    body = section["text"]
    for wrong, right in TEXT_FIXES:
        body = body.replace(wrong, right)
    return {
        "folder": folder,
        "name": name or section["name"],
        "type": "feature",
        "_id": _id,
        "img": ICON,
        "system": {
            "description": head + to_html(body), "bonuses": [],
            "uses": {"max": 0, "current": 0, "enabled": False},
            "featuretype": kind, "points": points, "macroid": "",
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

    module = module_dir()
    source = module / "packs" / PACK / "_source"

    core = fitz.open(SOURCES / CORE)
    sections = extract_coterie_types(core, core.get_toc(), CORE)
    official = {s["name"] for s in sections}

    guide = fitz.open(SOURCES / GUIDE)
    for section in guide_clans.coterie_types(
            guide, GUIDE_PAGES, fix_encoding, normalize, page_lines):
        name = section["name"]
        if name in official or name in GUIDE_ALIASES:
            continue
        section["source"] = GUIDE_NOTE
        sections.append(section)

    short = [s["name"] for s in sections if len(s["text"]) < 200]
    if short:
        sys.exit(f"разобрались не полностью: {short}")

    existing = {}
    if source.is_dir():
        for path in source.glob("*.json"):
            existing[json.loads(path.read_text(encoding="utf-8"))["_id"]] = path
    if not args.dry_run:
        source.mkdir(parents=True, exist_ok=True)

    # --- папки
    written, folders = [], {}
    for i, name in enumerate(FOLDERS, 1):
        f = folder_entry(name, None, i * 1000)
        folders[name] = f["_id"]
        written.append(f)
    for i, name in enumerate(DOMAIN_FOLDERS, 1):
        f = folder_entry(name, folders["Достоинства домена"], i * 100)
        folders[name] = f["_id"]
        written.append(f)

    # --- виды
    for section in sections:
        written.append(entry(section, folders["Виды котерий"]))

    guide = fitz.open(SOURCES / GUIDE)
    dots = lambda n: "•" * max(n, 1)  # noqa: E731

    # --- достоинства и недостатки самой котерии
    for s in guide_clans.custom_merits(
            guide, MERIT_PAGES, fix_encoding, normalize, page_lines):
        if s["kind"] != "Котерия":
            continue
        s["source"] = GUIDE_NOTE
        flaw = s["side"] == "flaw"
        title = s["name"].capitalize()
        title = originals.RENAMES.get(title, title)
        name = (f"({dots(s['rating'])}) {title}" if flaw
                else f"{dots(s['rating'])} {title}")
        folder = folders["Недостатки котерии" if flaw else "Достоинства котерии"]
        written.append(entry(s, folder, name, s["rating"],
                             "flaw" if flaw else "merit"))

    # --- достоинства домена
    for s in guide_clans.domain_merits(
            guide, DOMAIN_PAGES, fix_encoding, normalize, page_lines):
        s["source"] = GUIDE_NOTE
        title = originals.RENAMES.get(s["name"], s["name"])
        name = f"{dots(s['rating'])} {title}"
        written.append(entry(s, folders[s["group"]], name, s["rating"]))

    # --- достоинства членства в клане
    for s in guide_clans.clan_coterie_merits(
            guide, MEMBERSHIP_PAGES, fix_encoding, normalize, page_lines):
        s["source"] = GUIDE_NOTE
        title = originals.RENAMES.get(s["name"], s["name"])
        name = f"{dots(s['rating'])} {title} ({s['clan']})"
        written.append(entry(s, folders["Достоинства членства"], name,
                             s["rating"]))

    for data in written:
        wanted = source / safe_filename(data["name"], data["_id"])
        path = existing.get(data["_id"], wanted)
        if path != wanted and not args.dry_run:
            path.unlink(missing_ok=True)
            path = wanted
        if not args.dry_run:
            text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    items = [d for d in written if d["_key"].startswith("!items!")]
    print(f"  записей {len(items)}, папок {len(written) - len(items)}")

    added = False if args.dry_run else register(
        module / "module.json", PACK, PACK_LABEL)
    verb = "добавилось бы" if args.dry_run else "добавлено"
    print(f"\n{verb}: видов {len(sections)}, всего записей {len(items)}")
    if added:
        print(f"пак {PACK!r} объявлен в манифесте")
    return 0


if __name__ == "__main__":
    sys.exit(main())
