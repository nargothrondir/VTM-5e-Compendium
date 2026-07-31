"""Страницы истории (лоршиты) из Книги правил.

Двадцать четыре штуки, стр. 385–408, по одному на полосу. Единственная
категория книги, которой в компендиуме не было вовсе, — под неё заводится
новый пак и запись в манифесте.

Ступени лежат внутри записи, а не отдельными записями: так же собраны Фоны
(«со всеми пятью ступенями в одной записи»), и так решил владелец репозитория.

В системе wod5e типа «лоршит» нет — из двадцати одного типа предметов
подходящего не нашлось, — поэтому запись заводится как feature с
featuretype «background»: это ближайшее по смыслу, и лист её принимает.

Скрипт идемпотентен: _id выводится из названия.

    python tools/add_loresheets.py --dry-run
    python tools/add_loresheets.py
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fitz  # noqa: E402
import guide_clans  # noqa: E402
from add_clans import is_module_dir, make_id, safe_filename  # noqa: E402
from extract_pdf import (CORE, GUIDE, SOURCES, extract_loresheets,  # noqa: E402
                         page_lines)
from pdfkit import fix_encoding, normalize, to_html  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PACK = "loresheets"
PACK_LABEL = "Страницы истории"
GUIDE_PAGES = (224, 232)
GUIDE_NOTE = "Руководство для игроков"
ICON = "systems/vtm5e/assets/icons/items/discipline.png"


def module_dir():
    return next(p for p in ROOT.iterdir() if is_module_dir(p))


def entry(section):
    _id = make_id("loresheet:" + section["name"])
    head = ""
    if section.get("source"):
        head = f"<p><em>Источник: {section['source']}</em></p>"
    if section.get("subtitle"):
        head += f"<p><em>{section['subtitle'].capitalize()}</em></p>"
    body = head + to_html(section["text"]) + "".join(
        to_html(f"■ {'●' * lvl['rating']} {lvl['name']}: {lvl['text']}")
        for lvl in section["levels"])
    return {
        "folder": None,
        "name": section["name"],
        "type": "feature",
        "_id": _id,
        "img": ICON,
        "system": {
            "description": body, "bonuses": [],
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


def register(manifest_path):
    """Пак объявляется в манифесте — иначе Foundry его не увидит."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if any(p["name"] == PACK for p in manifest["packs"]):
        return False
    manifest["packs"].append({
        "name": PACK, "label": PACK_LABEL, "path": f"packs/{PACK}",
        "type": "Item", "system": "wod5e",
        "ownership": {"PLAYER": "OBSERVER", "ASSISTANT": "OWNER"},
    })
    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    manifest_path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    module = module_dir()
    source = module / "packs" / PACK / "_source"

    doc = fitz.open(SOURCES / CORE)
    sections = extract_loresheets(doc, doc.get_toc(), CORE)

    # Руководство отдаёт ещё семь — линии крови Гекаты, стр. 225–231.
    # Своя глава «Страницы истории», свёрстанная совершенно иначе.
    guide = fitz.open(SOURCES / GUIDE)
    for section in guide_clans.loresheets(
            guide, GUIDE_PAGES, fix_encoding, normalize, page_lines):
        section["source"] = GUIDE_NOTE
        sections.append(section)

    broken = [s["name"] for s in sections
              if len(s["levels"]) != 5 or not s["text"]]
    if broken:
        sys.exit(f"разобрались не полностью: {broken}")

    existing = {}
    if source.is_dir():
        for path in source.glob("*.json"):
            existing[json.loads(path.read_text(encoding="utf-8"))["_id"]] = path

    if not args.dry_run:
        source.mkdir(parents=True, exist_ok=True)

    for section in sections:
        data = entry(section)
        path = existing.get(data["_id"]) or \
            source / safe_filename(data["name"], data["_id"])
        print(f"  {'обновлено' if data['_id'] in existing else 'создано':<9}"
              f" {data['name']:<24} ступеней {len(section['levels'])}")
        if not args.dry_run:
            text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

    added = False if args.dry_run else register(module / "module.json")
    verb = "добавилось бы" if args.dry_run else "добавлено"
    print(f"\n{verb} Страниц истории: {len(sections)}")
    if added:
        print(f"пак {PACK!r} объявлен в манифесте")
    return 0


if __name__ == "__main__":
    sys.exit(main())
