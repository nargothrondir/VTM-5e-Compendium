"""Выгрузка кандидатов для сопоставления.

Кладёт рядом две стороны — записи компендиума и разделы русских книг,
сгруппированные по Дисциплине и уровню. Это вход для ручного (или
модельного) заполнения data/mapping.yaml, а не автоматический матчер:
официальные названия часто не переводятся буквально («Безпомилковий
приціл» -> «Безупречная точность»), и строковое сходство тут врёт.

    python tools/candidates.py disciplines
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = ROOT / "data" / "book_sections.json"

# Коды Дисциплин из system.discipline -> названия в русских книгах.
DISCIPLINE_RU = {
    "alchemy": "Алхимия слабокровных",
    "animalism": "Анимализм",
    "auspex": "Ясновидение",
    "celerity": "Стремительность",
    "dominate": "Доминирование",
    "fortitude": "Стойкость",
    "obfuscate": "Сокрытие",
    "potence": "Мощь",
    "presence": "Величие",
    "protean": "Метаморфозы",
    "rituals": "Ритуалы",
    "sorcery": "Кровавое чародейство",
}


def module_dir():
    return next(p for p in ROOT.iterdir()
                if p.is_dir() and p.name.startswith("vampire-the-masquerade"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pack", nargs="?", default="disciplines")
    args = ap.parse_args()

    if not SECTIONS.exists():
        sys.exit(f"нет {SECTIONS}; сначала: npm run extract")

    sections = json.loads(SECTIONS.read_text(encoding="utf-8"))
    ru = defaultdict(list)
    for s in sections:
        if s["kind"] == "power":
            ru[s["discipline"]].append(s)

    source = module_dir() / "packs" / args.pack / "_source"
    ua = defaultdict(list)
    for path in sorted(source.glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        if d.get("type") != "power":
            continue
        system = d["system"]
        ua[DISCIPLINE_RU.get(system.get("discipline"), "?")].append({
            "id": d["_id"],
            "name": d.get("name", ""),
            "level": system.get("level"),
        })

    for discipline in sorted(set(ua) | set(ru)):
        left = sorted(ua[discipline], key=lambda x: (x["level"] or 0, x["name"]))
        right = sorted(ru[discipline], key=lambda x: (x["level"] or 0, x["page"]))
        mark = "" if len(left) == len(right) else "   <-- НЕ СОВПАЛО"
        print(f"\n{'=' * 78}")
        print(f"{discipline}   компендиум: {len(left)}   книга: {len(right)}{mark}")
        print("=" * 78)

        for level in range(1, 6):
            lv_l = [x for x in left if x["level"] == level]
            lv_r = [x for x in right if x["level"] == level]
            if not lv_l and not lv_r:
                continue
            print(f"-- уровень {level}")
            for i in range(max(len(lv_l), len(lv_r))):
                a = lv_l[i] if i < len(lv_l) else None
                b = lv_r[i] if i < len(lv_r) else None
                aa = f"{a['name'][:34]:<34} {a['id']}" if a else " " * 51
                bb = f"{b['name'][:36]:<36} с.{b['page']}" if b else ""
                print(f"   {aa}  |  {bb}")

        orphan_l = [x for x in left if not x["level"]]
        for a in orphan_l:
            print(f"   {a['name'][:34]:<34} {a['id']}  |  (уровень не задан)")


if __name__ == "__main__":
    main()
