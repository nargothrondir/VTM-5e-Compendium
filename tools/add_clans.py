"""Добавление кланов, которых нет в компендиуме.

Украинская версия ограничилась девятью кланами основной книги, хотя иконки
для остальных семи в модуль уже положила. Скрипт создаёт недостающие записи.

Источники неравноценны, и это отражено в тексте записи:

  Равнос, Салюбри, Цимисхи        Малая книга знаний — официальный перевод,
                                  та же вёрстка, что и основная книга;
  Бану Хаким, Геката, Ласомбра,   Руководство для игроков — фанатский
  Министерство                    перевод, официального пока нет.

Скрипт идемпотентен: _id выводится из названия клана, поэтому повторный
запуск переписывает те же файлы, а не плодит дубликаты.

    python tools/add_clans.py --dry-run
    python tools/add_clans.py
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fitz  # noqa: E402
import guide_clans  # noqa: E402
from extract_pdf import (CORE, GUIDE, LORE, SOURCES,  # noqa: E402
                         extract_clans, load_toc)
from pdfkit import fix_encoding, normalize, to_html  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Клан -> (иконка, страницы в Руководстве с нуля). Диапазоны взяты из
# оглавления книги; оно английское, поэтому названия сопоставлены вручную.
FROM_GUIDE = {
    "Бану Хаким": ("1024px-Banu_Haqim_Symbol.png", (16, 22)),
    "Геката": ("1280px-Hecata_symbol.png", (22, 28)),
    "Ласомбра": ("1024px-Lasombra_symbol.png", (28, 34)),
    "Министерство": ("1024px-Ministry_symbol.png", (34, 40)),
}

FROM_LORE = {
    "Равнос": "1024px-Ravnos_symbol.png",
    "Салюбри": "1024px-Salubri_symbol.png",
    "Цимисхи": "1024px-Tzimisce_symbol.png",
}

# Руководство зовёт Дисциплины по-своему. Приводим к официальным названиям
# основной книги, чтобы в компендиуме была одна терминология.
# «Обливион» остаётся как есть: в основной книге этой Дисциплины нет вовсе,
# и придумывать ей перевод хуже, чем взять слово из единственного источника.
DISCIPLINE_ALIASES = {
    "КОЛДОВСТВО КРОВИ": "Кровавое чародейство",
    "МОГУЩЕСТВО": "Мощь",
    "ОБЛИВИОН": "Обливион",
}

GUIDE_MARK = "Руководство для игроков"
CAPS_RE = re.compile(r"([А-ЯЁ][А-ЯЁ ]{3,30}):")

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def make_id(name):
    """Устойчивый 16-символьный идентификатор в стиле Foundry.

    Выводится из названия клана, а не случайный: повторный запуск скрипта
    должен обновлять ту же запись, иначе в паке заведутся близнецы.
    """
    digest = hashlib.sha256(("vtm-ru-clan:" + name).encode("utf-8")).digest()
    return "".join(ALPHABET[b % len(ALPHABET)] for b in digest[:16])


def safe_filename(name, _id):
    stem = re.sub(r"[^0-9A-Za-zА-Яа-яЁё]+", "_", name).strip("_")
    return f"{stem}_{_id}.json"


def official_disciplines(raw):
    """Названия Дисциплин из прозы Руководства -> официальные."""
    out = []
    for caps in CAPS_RE.findall(raw):
        caps = caps.strip()
        name = DISCIPLINE_ALIASES.get(caps, caps.capitalize())
        if name not in out:
            out.append(name)
    return out


def build_entry(name, icon, disciplines, description, bane, source_note=None):
    body = [f"<h5>Дисциплины: {', '.join(disciplines)}</h5>"] if disciplines else []
    body.append(to_html(description))
    bane_html = to_html(bane)
    if source_note:
        bane_html = f"<p><em>Источник: {source_note}</em></p>" + bane_html

    _id = make_id(name)
    return {
        "name": name,
        "type": "clan",
        "img": f"modules/vampire-the-masquerade-5e-compendium-ru/packs/assets/{icon}",
        "system": {
            "description": "".join(body),
            "bonuses": [],
            "gamesystem": "vampire",
            "bane": bane_html,
        },
        "effects": [],
        "folder": None,
        "ownership": {"default": 0},
        "flags": {},
        "_stats": {
            "compendiumSource": None,
            "duplicateSource": None,
            "coreVersion": "13.346",
            "systemId": "vtm5e",
            "systemVersion": "5.0.11",
            "createdTime": 0,
            "modifiedTime": 0,
            "lastModifiedBy": None,
            "exportSource": None,
        },
        "_id": _id,
        "sort": 0,
        "_key": f"!items!{_id}",
    }


def is_module_dir(path):
    manifest = path / "module.json"
    if not path.is_dir() or not manifest.is_file():
        return False
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("id") == path.name
    except (json.JSONDecodeError, OSError):
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    entries = []

    lore = fitz.open(SOURCES / LORE)
    for section in extract_clans(lore, load_toc(lore), LORE, list(FROM_LORE)):
        entries.append(build_entry(
            section["name"], FROM_LORE[section["name"]],
            section["disciplines"], section["text"], section["bane"]))

    guide = fitz.open(SOURCES / GUIDE)
    for name, (icon, pages) in FROM_GUIDE.items():
        section = guide_clans.extract(guide, pages, name, fix_encoding, normalize)
        bane = section["bane"]
        if section["bane_name"]:
            bane = f"■ Клановый изъян: {section['bane_name']}.\n{bane}"
        entries.append(build_entry(
            name, icon, official_disciplines(section["disciplines_text"]),
            section["text"], bane, source_note=GUIDE_MARK))

    source = next(p for p in ROOT.iterdir() if is_module_dir(p)) / "packs" / "clans" / "_source"
    existing = {json.loads(p.read_text(encoding="utf-8"))["_id"]: p
                for p in source.glob("*.json")}

    for entry in entries:
        path = existing.get(entry["_id"]) or source / safe_filename(entry["name"], entry["_id"])
        mark = "обновлён" if path.exists() else "создан"
        print(f"  {mark:<9} {entry['name']:<14} "
              f"описание {len(entry['system']['description']):>5}  "
              f"изъян {len(entry['system']['bane']):>5}")
        if not args.dry_run:
            text = json.dumps(entry, ensure_ascii=False, indent=2) + "\n"
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

    verb = "добавилось бы" if args.dry_run else "добавлено"
    print(f"\n{verb} кланов: {len(entries)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
