"""Добавление типов питания из Руководства для игроков.

Основная книга описывает десять типов, они переведены. Руководство добавляет
ещё шесть — включая Вымогателя и Расхитителя могил, которые вики приписывает
Cults of the Blood God: Руководство их перепечатывает, так что книга для них
у проекта есть.

Перевод Руководства фанатский, поэтому источник помечается прямо в записи.

Скрипт идемпотентен: _id выводится из названия.

    python tools/add_predators.py --dry-run
    python tools/add_predators.py
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

# Страницы раздела «Типы питания» с запасом с обеих сторон.
PAGES = (100, 115)

SOURCE_NOTE = "Руководство для игроков"

# Название в книге -> каноническое английское. Нужно, чтобы глоссарий и план
# сходились с вики: у «Лазутчика» оригинал Trapdoor, у «Монтеро» — Montero.
ENGLISH = {
    "Вымогатель": "Extortionist",
    "Расхититель могил": "Graverobber",
    "Мрачный жнец": "Grim Reaper",
    "Монтеро": "Montero",
    "Преследователь": "Pursuer",
    "Лазутчик": "Trapdoor",
}

# Папка «Тип Хижака» из украинской версии; в ней лежат остальные типы.
FOLDER_NAME = "Тип охотника"
# Модуль объявляет систему wod5e — и путь к иконке обязан быть её.
# Пока стоял vtm5e, wod5e переносила пути при каждой загрузке мира
# и показывала плашку миграции на 246 записей.
ICON = "systems/wod5e/assets/icons/items/discipline.png"


def module_dir():
    return next(p for p in ROOT.iterdir() if is_module_dir(p))


def build_entry(name, text, folder):
    _id = make_id("predator:" + name)
    body = f"<p><em>Источник: {SOURCE_NOTE}</em></p>" + to_html(text)
    return {
        "folder": folder,
        "name": name,
        "type": "predatorType",
        "_id": _id,
        "img": ICON,
        "system": {"description": body, "bonuses": [], "gamesystem": "vampire"},
        "effects": [],
        "sort": 0,
        "ownership": {"default": 0},
        "flags": {},
        "_stats": {
            "compendiumSource": None, "duplicateSource": None,
            "exportSource": None, "coreVersion": "13.346",
            "systemId": "vtm5e", "systemVersion": "5.1.4",
            "createdTime": 0, "modifiedTime": 0, "lastModifiedBy": None,
        },
        "_key": f"!items!{_id}",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    source = module_dir() / "packs" / "blood-potency-predator-type" / "_source"

    folder = None
    existing = {}
    for path in source.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        existing[data["_id"]] = path
        if data.get("name") == FOLDER_NAME and data.get("_key", "").startswith("!folders!"):
            folder = data["_id"]
    if folder is None:
        sys.exit(f"не найдена папка {FOLDER_NAME!r}")

    doc = fitz.open(SOURCES / GUIDE)
    sections = guide_clans.predator_types(
        doc, PAGES, fix_encoding, normalize, page_lines)

    unknown = [s["name"] for s in sections if s["name"] not in ENGLISH]
    if unknown:
        sys.exit(f"незнакомые типы в книге: {unknown}")

    for section in sections:
        entry = build_entry(section["name"], section["text"], folder)
        path = existing.get(entry["_id"]) or \
            source / safe_filename(entry["name"], entry["_id"])
        mark = "обновлён" if path.exists() else "создан"
        print(f"  {mark:<9} {section['name']:<20} {ENGLISH[section['name']]:<14}"
              f" {len(section['text']):>5}")
        if not args.dry_run:
            text = json.dumps(entry, ensure_ascii=False, indent=2) + "\n"
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

    verb = "добавилось бы" if args.dry_run else "добавлено"
    print(f"\n{verb} типов питания: {len(sections)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
