"""Сборка ROADMAP.md — плана перевода.

Отделён от глоссария сознательно. Документы отвечают на разные вопросы и
живут в разном ритме: глоссарий — справочник «как переводится термин», он
меняется, когда принято решение, то есть редко; план — «что сделано и что
дальше», он меняется с каждой записью. В одном файле план погребал справочник
под сотней пустых строк.

Ключевое для плана измерение, которого у глоссария нет, — **доступность
источника**. Непереведённое делится на то, что можно взять имеющимися
книгами, и то, что требует книг, которых у проекта нет. Без этого деления
список работ превращается в список желаний.

    python tools/make_roadmap.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fix_clans  # noqa: E402
import make_mapping  # noqa: E402
import originals  # noqa: E402
from candidates import DISCIPLINE_RU  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ROADMAP.md"

DONE, TODO = chr(9989), chr(11036)
NL = chr(10)

# Книги, которые у проекта есть. Всё, что описано в них, — работа, которую
# можно взять хоть сейчас; остальное ждёт появления источника.
AT_HAND = {"Corebook", "Companion", "Players Guide"}

INTRO = """# План перевода

Что уже перенесено в компендиум, что можно взять прямо сейчас и что ждёт
книг, которых у проекта нет. Собирается командой `npm run roadmap` из тех же
данных, что и сам модуль.

Как переводится конкретный термин и почему — в [глоссарии](GLOSSARY.md).
Здесь только охват.

Непереведённое разделено по **доступности источника**: без этого деления
список работ превращается в список желаний. Линейка Vampire прирастала
содержимым десяток лет, и догнать её целиком силами одного репозитория
нельзя — но видно, докуда можно дойти имеющимися книгами.
"""


def module_dir():
    return next(p for p in ROOT.iterdir() if fix_clans.is_module_dir(p))


def table(rows, headers):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return NL.join(out)


def main():
    mod = module_dir()
    entries = [json.loads(p.read_text(encoding="utf-8"))
               for p in mod.glob("packs/*/_source/*.json")]
    by_type = {}
    for entry in entries:
        by_type.setdefault(entry.get("type"), []).append(entry)

    powers_done = len(originals.POWERS)
    powers_total = sum(len(v) for v in originals.CANON_POWERS.values())
    guide_powers = sum(len(v) for v in originals.PLAYERS_GUIDE_POWERS.values())
    predators_done = len(originals.PREDATOR_TYPES)
    predators_total = len(originals.CANON_PREDATOR_TYPES)
    clans_done = len(by_type.get("clan", []))

    parts = [INTRO]

    # --- сводка
    rows = [
        ["Кланы", clans_done, len(originals.CANON_CLANS), "закрыто"],
        ["Силы Дисциплин", powers_done, powers_total,
         f"{guide_powers} доступны в Руководстве"],
        ["Типы охотника", predators_done, predators_total,
         "4 доступны в Руководстве"],
        ["Сила Крови", len(make_mapping.BLOOD_POTENCY),
         len(make_mapping.BLOOD_POTENCY), "закрыто"],
        ["Достоинства и недостатки", len(by_type.get("feature", [])), "—",
         "канон не сверялся"],
    ]
    parts.append("## Сводка" + NL * 2 + table(
        rows, ["Раздел", "Сделано", "Всего", "Примечание"]))

    # --- доступно сейчас
    chunks = []
    for group in sorted(originals.PLAYERS_GUIDE_POWERS):
        rows = [[TODO, name, page]
                for name, page in originals.PLAYERS_GUIDE_POWERS[group]]
        chunks.append(f"### {group} — {len(rows)}" + NL * 2
                      + table(rows, ["", "Название в книге", "Стр."]))

    ready = [(en, book) for en, book in originals.CANON_PREDATOR_TYPES
             if book in AT_HAND and en not in originals.PREDATOR_TYPES.values()]
    predator_block = table([[TODO, en, book] for en, book in ready],
                           ["", "Оригинал", "Книга"])

    parts.append(
        f"## Доступно сейчас{NL}{NL}Работа, для которой источник уже есть на "
        f"руках. Всего **{guide_powers + len(ready)} записей**.{NL}{NL}"
        f"### Силы из Руководства для игроков — {guide_powers}{NL}{NL}"
        f"Руководство описывает целую Дисциплину Обливион с церемониями, "
        f"а также по три-пять новых сил почти к каждой Дисциплине основной "
        f"книги. Названия ниже — как они стоят в книге.{NL}{NL}"
        + NL.join(c + NL for c in chunks)
        + f"{NL}### Типы охотника из Руководства — {len(ready)}{NL}{NL}"
        + predator_block)

    # --- требует других книг
    blocked = {}
    have = set(originals.POWERS.values())
    guide_ru = {n for v in originals.PLAYERS_GUIDE_POWERS.values()
                for n, _ in v}
    for group, names in sorted(originals.CANON_POWERS.items()):
        rest = [n for n in names if n not in have]
        if rest:
            blocked[group] = rest

    rows = [[group, len(names), ", ".join(names[:4]) + ("…" if len(names) > 4 else "")]
            for group, names in blocked.items()]
    other_predators = [(en, book) for en, book in originals.CANON_PREDATOR_TYPES
                       if book not in AT_HAND
                       and en not in originals.PREDATOR_TYPES.values()]

    parts.append(
        f"## Требует книг, которых нет{NL}{NL}"
        f"Перечислено, чтобы охват не выглядел неполным по недосмотру. "
        f"Часть этих сил описана в Руководстве и попала в раздел выше — "
        f"пересечение неизбежно, канонический список не размечен по книгам.{NL}{NL}"
        + table(rows, ["Дисциплина", "Осталось", "Например"])
        + NL * 2 + "### Типы охотника" + NL * 2
        + table([[en, book] for en, book in other_predators],
                ["Оригинал", "Книга"]))

    parts.append(
        f"## Что дальше{NL}{NL}"
        f"1. **Типы охотника из Руководства** — четыре записи, механика та же, "
        f"что у переведённых десяти. Самое дешёвое.{NL}"
        f"2. **Новые силы Дисциплин основной книги** — по три-пять к каждой, "
        f"ложатся в существующие папки уровней.{NL}"
        f"3. **Обливион** — отдельная Дисциплина: 19 сил и 17 церемоний, "
        f"нужны новые папки и иконка (она уже лежит в ассетах).{NL}"
        f"4. **Достоинства и недостатки** — канон не сверялся, объём "
        f"неизвестен; сперва нужен список.{NL}{NL}"
        f"Оговорка про качество: Руководство для игроков переведено "
        f"фанатами, а не официально. Всё, что берётся оттуда, помечается "
        f"источником прямо в тексте записи — как уже сделано с "
        f"альтернативными проклятиями и четырьмя кланами.")

    OUT.write_text((NL * 2 + "---" + NL * 2).join(parts).rstrip() + NL,
                   encoding="utf-8")
    print(f"собран план -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
