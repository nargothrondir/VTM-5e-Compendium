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


def AT_HAND_ONLY(table):
    """Записи из книг, которые у проекта есть."""
    return [name for book, names in table.items() for name in names
            if book in AT_HAND or name in originals.ALSO_IN_GUIDE]

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
    # Пак запоминается: по типу записи котерии от лоршитов не отличить —
    # и те и другие лежат как feature с featuretype «background».
    by_pack = {}
    entries = []
    for path in mod.glob("packs/*/_source/*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        by_pack.setdefault(path.parent.parent.name, []).append(data)
        entries.append(data)
    by_type = {}
    for entry in entries:
        by_type.setdefault(entry.get("type"), []).append(entry)

    # Считаем по пакам, а не по таблице оригиналов: та покрывает только
    # силы из основной книги, для которых сверены английские названия.
    powers_done = len(by_type.get("power", []))
    powers_total = sum(len(v) for v in originals.CANON_POWERS.values())
    guide_powers = sum(len(v) for v in originals.PLAYERS_GUIDE_POWERS.values())
    predators_done = len(originals.PREDATOR_TYPES)
    predators_total = len(originals.CANON_PREDATOR_TYPES)
    clans_done = len(by_type.get("clan", []))

    in_packs = {e.get("name") for e in entries}
    guide_left = sum(1 for g in originals.PLAYERS_GUIDE_POWERS
                     for n, _ in originals.PLAYERS_GUIDE_POWERS[g]
                     if n not in in_packs)

    # Канон сверен только для десяти Дисциплин основной книги; Обливион,
    # ритуалы и алхимия в него не входят, и мерить их той же меркой нельзя.
    canon = {n for names in originals.CANON_POWERS.values() for n in names}
    canon_done = sum(1 for ru, en in originals.POWERS.items() if en in canon)

    ready = [(en, book) for en, book in originals.CANON_PREDATOR_TYPES
             if book in AT_HAND and en not in originals.PREDATOR_TYPES.values()]

    # Достоинства из Руководства: три перечня — основной раздел, глава
    # «Кастомы» и выборка из Фонов. Часть оригиналов сверить не удалось,
    # и это честнее показать числом, чем прятать.
    guide_tables = (originals.PLAYERS_GUIDE_MERITS,
                    originals.PLAYERS_GUIDE_CUSTOM,
                    originals.PLAYERS_GUIDE_BACKGROUNDS)
    # Клановые достоинства котерии лежат в паке котерий, а не среди
    # достоинств, поэтому в guide_features они не входят — но в счёт
    # несверенных попасть должны.
    unverified_extra = sum(1 for v in originals.CLAN_COTERIE_MERITS.values()
                           if not v)
    guide_features = sum(len(t) for t in guide_tables)
    unverified = sum(1 for t in guide_tables for v in t.values() if not v)
    unverified += unverified_extra

    # Лоршиты лежат в своём паке и в by_type попадают как feature — считаем
    # их отдельно, иначе они смешаются с достоинствами.
    loresheets = sum(1 for e in by_pack.get("loresheets", [])
                     if e.get("_key", "").startswith("!items!"))

    # Внутри пака котерий виды отделяются от достоинств по имени папки.
    coteries = by_pack.get("coteries", [])
    names = {e["_id"]: e["name"] for e in coteries
             if e.get("_key", "").startswith("!folders!")}
    items = [e for e in coteries if e.get("_key", "").startswith("!items!")]
    coterie_done = sum(1 for e in items
                       if names.get(e.get("folder")) == "Виды котерий")
    traits_done = len(items) - coterie_done

    lore_total = sum(len(v) for v in originals.CANON_LORESHEETS.values())
    coterie_total = sum(len(v) for v in originals.CANON_COTERIE_TYPES.values())
    coterie_traits = sum(len(v)
                         for v in originals.CANON_COTERIE_TRAITS.values())

    parts = [INTRO]

    # --- сводка
    rows = [
        ["Кланы", clans_done, len(originals.CANON_CLANS), "закрыто"],
        ["Силы десяти Дисциплин", canon_done, powers_total,
         "канон сверён по вики"],
        ["Обливион, ритуалы, алхимия", powers_done - canon_done, "—",
         "канон не сверялся"],
        ["Типы охотника", predators_done, predators_total,
         "закрыто" if not ready else f"{len(ready)} доступны в Руководстве"],
        ["Сила Крови", len(make_mapping.BLOOD_POTENCY),
         len(make_mapping.BLOOD_POTENCY), "закрыто"],
        # Лоршиты и котерии тоже feature — вычитаем, иначе они удвоятся.
        ["Достоинства и недостатки", len(by_type.get("feature", []))
         - guide_features - loresheets - len(items), "—",
         "канон не сверялся"],
        ["Достоинства из Руководства", guide_features, guide_features,
         f"{unverified} записей без оригинала"
         if unverified else "канон сверён по вики"],
        ["Страницы истории", loresheets, lore_total,
         "имеющиеся книги закрыты"],
        ["Типы котерии", coterie_done, coterie_total,
         "имеющиеся книги закрыты"],
        ["Достоинства котерии", traits_done, coterie_traits,
         "имеющиеся книги закрыты"],
    ]
    parts.append("## Сводка" + NL * 2 + table(
        rows, ["Раздел", "Сделано", "Всего", "Примечание"]))

    # --- доступно сейчас
    # Перенесённое отсеивается по именам записей: список из книги снят
    # один раз, и сверять его надо с тем, что в паках уже лежит.
    chunks = []
    for group in sorted(originals.PLAYERS_GUIDE_POWERS):
        rows = [[TODO, name, page]
                for name, page in originals.PLAYERS_GUIDE_POWERS[group]
                if name not in in_packs]
        if rows:
            chunks.append(f"### {group} — {len(rows)}" + NL * 2
                          + table(rows, ["", "Название в книге", "Стр."]))


    predator_block = table([[TODO, en, book] for en, book in ready],
                           ["", "Оригинал", "Книга"]) if ready else         "Все типы питания из имеющихся книг перенесены."

    coterie_ready = [n for n in AT_HAND_ONLY(originals.CANON_COTERIE_TYPES)
                     if coterie_done == 0]
    traits_ready = [n for n in AT_HAND_ONLY(originals.CANON_COTERIE_TRAITS)
                    if traits_done == 0]
    total_ready = (guide_left + len(ready)
                   + len(coterie_ready) + len(traits_ready))

    powers_block = (
        f"### Силы из Руководства для игроков — {guide_left}{NL}{NL}"
        + (f"Руководство описывает целую Дисциплину Обливион с церемониями, "
           f"а также по три-пять новых сил почти к каждой Дисциплине "
           f"основной книги.{NL}{NL}" + NL.join(c + NL for c in chunks)
           if chunks else "Все силы из Руководства перенесены." + NL))

    parts.append(
        f"## Доступно сейчас{NL}{NL}Работа, для которой источник уже есть на "
        f"руках. Всего **{total_ready} записей**.{NL}{NL}"
        + powers_block
        + f"{NL}### Типы охотника — {len(ready)}{NL}{NL}"
        + predator_block
        + f"{NL}{NL}### Котерии — {len(coterie_ready) + len(traits_ready)}{NL}{NL}"
        + ("Всё, что описано в имеющихся книгах, перенесено: двадцать два "
           "вида котерии, десять её достоинств и недостатков, восемнадцать "
           "владений и пятнадцать клановых достоинств членства."
           if not coterie_ready and not traits_ready else
           table([[TODO, n] for n in coterie_ready + traits_ready],
                 ["", "Оригинал"])))

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
                ["Оригинал", "Книга"])
        + NL * 2 + "### Страницы истории" + NL * 2
        + f"Имеющиеся книги закрыты целиком: двадцать пять из Книги правил "
        f"и семь линий крови Гекаты из Руководства. Линейка прирастала "
        f"лоршитами десять лет, и остальное разбросано по книгам, которых "
        f"у проекта нет.{NL}{NL}"
        + table([[book, len(names), ", ".join(names[:3])
                  + ("…" if len(names) > 3 else "")]
                 for book, names in originals.CANON_LORESHEETS.items()
                 if book not in AT_HAND],
                ["Книга", "Лоршитов", "Например"])
        + NL * 2 + "### Котерии" + NL * 2
        + table([[book, len(names)]
                 for table_ in (originals.CANON_COTERIE_TYPES,
                                originals.CANON_COTERIE_TRAITS)
                 for book, names in table_.items() if book not in AT_HAND],
                ["Книга", "Записей"]))

    parts.append(
        f"## Что дальше{NL}{NL}"
        f"1. **Котерии** — {len(coterie_ready) + len(traits_ready)} записей "
        f"и целая категория, которой в компендиуме нет: типы котерии, их "
        f"достоинства и владения. Всё описано в книгах, что уже на руках.{NL}"
        f"2. **Досверить оригиналы** — {unverified} записей Руководства "
        f"остались без английского названия: вики держит перечень Фонов "
        f"сводным, без разбивки по книгам.{NL}"
        f"3. **Выправить машинный перевод названий** — «Проверить ствол» "
        f"это Check the Trunk, багажник с инструментом; «Перемешник» — "
        f"Mockingbird, пересмешник; «Слова-карриды» — Word-Scarred. "
        f"Тексты записей при этом читаемы, вопрос только в заголовках.{NL}{NL}"
        f"Оговорка про качество: Руководство для игроков переведено "
        f"фанатами, а не официально. Всё, что берётся оттуда, помечается "
        f"источником прямо в тексте записи — как уже сделано с "
        f"альтернативными изъянами и четырьмя кланами.")

    OUT.write_text((NL * 2 + "---" + NL * 2).join(parts).rstrip() + NL,
                   encoding="utf-8")
    print(f"собран план -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
