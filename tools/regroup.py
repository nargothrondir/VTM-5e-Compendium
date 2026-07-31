"""Достоинства и недостатки — по папкам, а не по подписи в названии.

Украинская версия различала их припиской: «Вада: (••) Архаїчний». Перевод
приписку унаследовал — «Недостаток: (••) Ходячий анахронизм», — и она
дублировала то, что у записи и так есть: `featuretype`, который Foundry
показывает отдельным полем «Тип преимущества».

В списке от неё был один вред. Сортировка идёт по названию, поэтому все
недостатки сбивались в одну кучу на букву «Н», а рядом с достоинством того
же разряда запись не стояла никогда.

Здесь приписка снимается, а недостатки отделяются папкой — но только там,
где в папке и правда есть и те и другие. Заводить «Недостатки» в папке,
где одни недостатки, незачем: имя папки и так всё говорит.

Проход бескнижный и идемпотентный: `_id` не меняется, повторный прогон
ничего не делает.

    python tools/regroup.py --dry-run
    python tools/regroup.py
"""

import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit import module_dir  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PACKS = ("advantages-flaws", "coteries")
SIDES = {"merit": "Достоинства", "flaw": "Недостатки"}

# Приписка, доставшаяся от украинской версии.
PREFIX_RE = re.compile(r"^Недостаток:\s*")

# Скобки вокруг рейтинга. Книга метила ими недостаток, но это делает папка,
# и в списке они только разводили одинаковые по сути записи: «• Ищейка»
# рядом с «(•) Разборчивость». Ловится лишь ведущая группа — «Союзники
# (надёжность)» и «Мавла (или конкурент)» скобки сохраняют.
PARENS_RE = re.compile(r"^\(([•●]+)\)\s*")

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def make_id(name):
    import hashlib
    digest = hashlib.sha256(("vtm-ru-regroup:" + name).encode("utf-8")).digest()
    return "".join(ALPHABET[b % len(ALPHABET)] for b in digest[:16])


def folder_doc(name, parent, sort):
    _id = make_id(f"{parent}/{name}")
    return {
        "name": name, "sorting": "a", "folder": parent, "type": "Item",
        "_id": _id, "description": "", "sort": sort, "color": "#9f90a2",
        "flags": {},
        "_stats": {"compendiumSource": None, "duplicateSource": None,
                   "coreVersion": "13.346", "systemId": "wod5e",
                   "systemVersion": "5.1.4", "createdTime": 0,
                   "modifiedTime": 0, "lastModifiedBy": None},
        "_key": f"!folders!{_id}",
    }


def write(path, data):
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    module = module_dir()
    renamed = moved = added = 0

    for pack in PACKS:
        source = module / "packs" / pack / "_source"
        if not source.is_dir():
            continue

        docs = {}
        for path in sorted(source.glob("*.json")):
            docs[path] = json.loads(path.read_text(encoding="utf-8"))
        folders = {d["_id"]: d for d in docs.values()
                   if d.get("_key", "").startswith("!folders!")}
        items = {p: d for p, d in docs.items()
                 if not d.get("_key", "").startswith("!folders!")}

        # --- приписка
        for path, data in items.items():
            fresh = PREFIX_RE.sub("", data.get("name", "")).strip()
            fresh = PARENS_RE.sub(lambda m: m.group(1) + " ", fresh).strip()
            if fresh and fresh != data["name"]:
                data["name"] = fresh
                renamed += 1
                if not args.dry_run:
                    write(path, data)

        # --- папки: делим только смешанные
        sides = collections.defaultdict(collections.Counter)
        for data in items.values():
            sides[data.get("folder")][data["system"].get("featuretype")] += 1

        for parent, tally in sides.items():
            present = [s for s in SIDES if tally.get(s)]
            if parent is None or len(present) < 2:
                continue
            host = folders.get(parent)
            if host is None:
                continue

            child = {}
            for i, side in enumerate(("merit", "flaw"), 1):
                doc = folder_doc(SIDES[side], parent, i * 10)
                child[side] = doc["_id"]
                if doc["_id"] not in folders:
                    added += 1
                    if not args.dry_run:
                        write(source / f"{SIDES[side]}_{doc['_id']}.json", doc)

            for path, data in items.items():
                if data.get("folder") != parent:
                    continue
                side = data["system"].get("featuretype")
                if side in child:
                    data["folder"] = child[side]
                    moved += 1
                    if not args.dry_run:
                        write(path, data)
            print(f"  {pack}: {host['name']} -> "
                  f"{tally.get('merit', 0)} достоинств, {tally.get('flaw', 0)} недостатков")

    verb = "было бы" if args.dry_run else "сделано"
    print(f"\n{verb}: поправлено названий {renamed}, заведено папок {added}, "
          f"перенесено записей {moved}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
