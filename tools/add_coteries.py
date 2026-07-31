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
from add_clans import is_module_dir, make_id, safe_filename  # noqa: E402
from add_loresheets import register  # noqa: E402
from extract_pdf import (CORE, GUIDE, SOURCES,  # noqa: E402
                         extract_coterie_types, page_lines)
from pdfkit import fix_encoding, normalize, to_html  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PACK = "coteries"
PACK_LABEL = "Виды котерий"
ICON = "systems/vtm5e/assets/icons/items/discipline.png"
GUIDE_PAGES = (159, 171)
GUIDE_NOTE = "Руководство для игроков"

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


def entry(section):
    _id = make_id("coterie:" + section["name"])
    head = ""
    if section.get("source"):
        head = f"<p><em>Источник: {section['source']}</em></p>"
    return {
        "folder": None,
        "name": section["name"],
        "type": "feature",
        "_id": _id,
        "img": ICON,
        "system": {
            "description": head + to_html(section["text"]), "bonuses": [],
            "uses": {"max": 0, "current": 0, "enabled": False},
            "featuretype": "background", "points": 0, "macroid": "",
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

    for section in sorted(sections, key=lambda s: s["name"]):
        data = entry(section)
        path = existing.get(data["_id"]) or \
            source / safe_filename(data["name"], data["_id"])
        mark = "обновлено" if data["_id"] in existing else "создано"
        print(f"  {mark:<9} {data['name']:<22}"
              f" {section.get('source', 'Книга правил')}")
        if not args.dry_run:
            text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

    added = False if args.dry_run else register(
        module / "module.json", PACK, PACK_LABEL)
    verb = "добавилось бы" if args.dry_run else "добавлено"
    print(f"\n{verb} видов котерий: {len(sections)}")
    if added:
        print(f"пак {PACK!r} объявлен в манифесте")
    return 0


if __name__ == "__main__":
    sys.exit(main())
