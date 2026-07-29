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
        apply_pack(pack, mapping[pack], by_id, by_name,
                   args.dry_run, total, renames)

    verb = "изменилось бы" if args.dry_run else "изменено"
    print(f"{verb}: {total['changed']}, без изменений: {total['skipped']}")

    if renames:
        print(f"\nпереименования ({len(renames)}):")
        for was, now in renames:
            print(f"  {was:<36} -> {now}")
    return 0


def apply_pack(pack, mapping, by_id, by_name, dry_run, total, renames):
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
