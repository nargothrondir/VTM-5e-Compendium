"""Перенос русского текста из книг в записи компендиума.

Читает data/mapping.yaml (что чему соответствует) и data/book_sections.json
(сам текст), пишет в packs/*/_source. Шаг идемпотентный: повторный запуск
даёт тот же результат, поэтому его можно гонять сколько угодно, а правки
вносить в mapping.yaml, а не в JSON руками.

    python tools/apply.py --dry-run    # показать, что изменится
    python tools/apply.py
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import mapping_merits  # noqa: E402
from pdfkit import to_html  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = ROOT / "data" / "book_sections.json"
MAPPING = ROOT / "data" / "mapping.yaml"

# Заголовки в книге набраны капсом, а в компендиуме имя показывается как есть.
# Понижение регистра ломает имена собственные, поэтому они перечислены явно.
PROPER_NOUNS = {
    "каина": "Каина",
    "ваала": "Ваала",
    "дагона": "Дагона",
    "вавилонские": "вавилонские",
}


def display_name(heading: str) -> str:
    """«БЕЗУПРЕЧНАЯ ТОЧНОСТЬ» -> «Безупречная точность».

    Приводится только капс. Заголовки типов охотника («Бестия») и уровней
    Силы Крови («Сила Крови 6 и выше») набраны в книге обычным регистром —
    их надо брать как есть, иначе выйдет «Сила крови».
    """
    if heading != heading.upper():
        return heading

    words = heading.split()
    out = []
    for i, word in enumerate(words):
        low = word.lower()
        if low in PROPER_NOUNS:
            out.append(PROPER_NOUNS[low])
        elif i == 0:
            out.append(low.capitalize())
        else:
            out.append(low)
    return " ".join(out)


def dots(rating):
    return chr(8226) * rating


def merit_display_name(section, ua_name=""):
    """Имя записи достоинства или недостатка.

    Компендиум показывает в списке и вид записи, и рейтинг («Вада: (••)
    Архаїчний»), поэтому та же разметка сохраняется и в переводе — иначе
    в дереве не отличить недостаток от достоинства.
    """
    base = display_name(section["name"])
    base = base[:1].upper() + base[1:]

    if section["kind"] == "merit_category":
        prefix = "Недостаток: " if section["name"] in mapping_merits.FLAW_CATEGORIES else ""
        return prefix + base

    # Рейтинг книги приоритетен, но у части достоинств он набран на полях
    # и в строку не попадает. Тогда его берём из украинского названия —
    # там он записан явно («•••• Приголомшливий», «Вада: (••) Веган»).
    rating = section.get("rating") or ua_name.count(chr(8226))
    if section.get("flaw"):
        return f"Недостаток: ({dots(rating)}) {base}" if rating else f"Недостаток: {base}"
    return f"{dots(rating)} {base}" if rating else base


def category_text(section, sections):
    """Текст сводной записи: вводный абзац плюс ступени раздела.

    Фон в компендиуме — одна запись со всеми ступенями, а книга разносит их
    по отдельным записям. Недостатки категории сюда не входят: под них в
    компендиуме заведены свои записи.
    """
    levels = [s for s in sections
              if s["kind"] == "merit_entry"
              and s.get("category") == section["name"]
              and not s.get("flaw")]

    # У низших ступеней фона точки набраны на полях и в строку не попадают.
    # Восстанавливаем их по позиции, но только там, где ступеней ровно пять
    # и все распознанные рейтинги совпали с номерами: у достоинств убежища
    # шкалы нет, и позиция там ничего не значит.
    ratings = [s.get("rating") or 0 for s in levels]
    ordered = (len(levels) == 5
               and all(r == 0 or r == i + 1 for i, r in enumerate(ratings)))
    if ordered:
        ratings = [i + 1 for i in range(len(levels))]

    parts = [section["text"]] if section["text"] else []
    for other, rating in zip(levels, ratings):
        name = other["name"][:1].upper() + other["name"][1:]
        rate = dots(rating)
        head = f"{chr(9632)} {rate} {name}." if rate else f"{chr(9632)} {name}."
        parts.append(f"{head} {other['text']}")
    return chr(10).join(parts)


def module_dir():
    return next(p for p in ROOT.iterdir()
                if p.is_dir() and p.name.startswith("vampire-the-masquerade"))


def write_json(path: Path, data: dict) -> None:
    """Сохраняет запись в том же виде, в каком её пишет Foundry."""
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pack", action="append",
                    help="какой пак переносить; по умолчанию все из маппинга")
    args = ap.parse_args()

    if not MAPPING.exists():
        sys.exit(f"нет {MAPPING}; сначала: python tools/make_mapping.py")

    mapping = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))
    sections = json.loads(SECTIONS.read_text(encoding="utf-8"))
    # Разделы, разобранные постранично (достоинства и недостатки), заголовка
    # не имеют — у них имена записей идут инлайном. Здесь они не нужны.
    by_name = {}
    for s in sections:
        if "name" in s:
            by_name.setdefault(s["name"], s)

    total = Counter()
    renames = []

    for pack in args.pack or list(mapping):
        source = module_dir() / "packs" / pack / "_source"
        by_id = {}
        for path in sorted(source.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            by_id[data["_id"]] = (path, data)
        apply_pack(pack, mapping[pack], by_id, by_name, sections,
                   args.dry_run, total, renames)

    verb = "изменилось бы" if args.dry_run else "изменено"
    print(f"{verb}: {total['changed']}, без изменений: {total['skipped']}")

    if renames:
        print(f"\nпереименования ({len(renames)}):")
        for was, now in renames:
            print(f"  {was:<36} -> {now}")
    return 0


def apply_pack(pack, mapping, by_id, by_name, all_sections, dry_run, total, renames):
    for _id, entry in mapping.items():
        if _id not in by_id:
            print(f"  ! {pack}: нет записи {_id} ({entry['ua']})")
            continue

        path, data = by_id[_id]

        # У папки нет раздела в книге — переводится только название.
        if "ru" not in entry:
            if data.get("name") == entry["name"]:
                total["skipped"] += 1
            else:
                renames.append((data.get("name", ""), entry["name"]))
                data["name"] = entry["name"]
                total["changed"] += 1
                if not dry_run:
                    write_json(path, data)
            continue

        section = by_name.get(entry["ru"])
        if not section:
            print(f"  ! {pack}: нет раздела {entry['ru']!r} для {_id}")
            continue

        if section["kind"] in ("merit_entry", "merit_category"):
            new_name = (mapping_merits.NAME_OVERRIDES.get(_id)
                        or merit_display_name(section, entry.get("ua", "")))
            new_desc = to_html(category_text(section, all_sections)
                               if section["kind"] == "merit_category"
                               else section["text"])
        else:
            new_name = display_name(section["name"])
            new_desc = to_html(section["text"])

        if data.get("name") == new_name and data["system"].get("description") == new_desc:
            total["skipped"] += 1
            continue

        if data.get("name") != new_name:
            renames.append((data.get("name", ""), new_name))

        data["name"] = new_name
        data["system"]["description"] = new_desc
        total["changed"] += 1
        if not dry_run:
            write_json(path, data)


if __name__ == "__main__":
    sys.exit(main())
