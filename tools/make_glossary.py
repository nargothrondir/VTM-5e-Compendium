"""Сборка GLOSSARY.md — глоссария и плана перевода.

Глоссарий генерируется из тех же данных, по которым собран компендиум, а не
пишется руками: иначе он неизбежно разойдётся с содержимым паков. Пояснения
и спорные решения — в тексте этого скрипта, чтобы документ можно было
перегенерировать целиком.

    python tools/make_glossary.py
"""

import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import fix_clans  # noqa: E402
import make_mapping  # noqa: E402
import originals  # noqa: E402
from add_clans import DISCIPLINE_ALIASES  # noqa: E402
from apply import PROPER_NOUNS  # noqa: E402
from candidates import DISCIPLINE_RU  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "GLOSSARY.md"

DONE, TODO = chr(9989), chr(11036)
NL = chr(10)

# Одержимости из основной книги (стр. 212—213). Остальные семь — из
# Руководства, они лежат в fix_clans.GUIDE_COMPULSIONS.
COMPULSIONS_BY_CLAN = {
    "Бруха": "бунт", "Вентру": "превосходство", "Гангрел": "животные порывы",
    "Малкавиан": "наваждение", "Носферату": "криптомания",
    "Тореадор": "восхищение", "Тремер": "перфекционизм",
}

INTRO = """# Глоссарий

Терминология русского компендиума: **термин — оригинал — статус**. Собрана
по ходу перевода и **сгенерирована из тех же данных, по которым собран
модуль**, — расходиться с содержимым паков она не может. Перегенерируется
командой `npm run glossary`.

Зачем: перевод шёл не пословно, а сопоставлением с официальным русским
изданием, поэтому названия сплошь и рядом далеки от оригинала. Глоссарий
фиксирует, какое решение принято и почему.

Английские названия сверены по спискам
[paradoxwikis](https://vtm.paradoxwikis.com/Clans), а не взяты по памяти:
проверка находила расхождения — у бруха проклятие называется Violent Temper,
а не Rage; у Министерства — Abhors the Light, а не Light Sensitive.

## Как выбиралась терминология

1. **Приоритет за официальным изданием.** Если книга даёт слово, берётся её
   слово, даже когда оно далеко от оригинала: Unerring Aim — «Безупречная
   точность», Baal's Caress — «Ласка Ваала».
2. **Где официального перевода нет — слово ищется в словаре самой книги,**
   а не в общем. Так появились названия проклятий.
3. **Ничего не выдумано молча.** Каждое решение, где источник не дал прямого
   ответа, перечислено в разделе «Спорные решения».
"""

STRUCTURE_DOC = """## Структурные термины

Подписи, которыми размечены блоки внутри записей.

| Термин | Оригинал | Где встречается |
|---|---|---|
| Амальгама | Amalgam | силы, требующие второй Дисциплины |
| Расплата | Cost | силы |
| Пул | Dice Pool | силы |
| Правила | System | силы |
| Длительность | Duration | силы |
| Компоненты | Ingredients | ритуалы-обереги |
| Изъян | Bane | кланы |
| Одержимость | Compulsion | кланы (в компендиум пока не внесена) |
| Сила Крови | Blood Potency | отдельный пак |
| Тип охотника | Predator Type | отдельный пак |
| Голод | Hunger | сквозной термин |
| Человечность | Humanity | сквозной термин |
| Становление | Embrace | сквозной термин |
| Сородичи | Kindred | сквозной термин |
| витэ | vitae | сквозной термин |

Слово «Кровь» в значении игрового термина книга пишет с заглавной
(«испытание Крови», «Сила Крови»), в бытовом значении — со строчной.
"""

DECISIONS = """## Спорные решения

Случаи, где источник не дал прямого ответа и решение принято осознанно.

**Названия клановых проклятий.** В оригинале имя есть у каждого проклятия,
но ни основная книга, ни Малая книга знаний их не приводят — ставят заголовок
«Изъян» и сразу текст. Похоже на упрощение при переводе. Названия переведены
с канонических английских, причём в словаре самой книги: четыре она подарила
дословно — «болезненный Поцелуй», «отвратительные», «жаждут красоты»,
«привязанность». Остальные собраны из её же лексики: «Буйный нрав» при «едва
удаётся сдерживать свою ярость», «Обречённость» при «Равнос обречены»,
«Гонимые» при «на салюбри охотятся».

**«Обливион».** Дисциплины Oblivion в основной книге нет вовсе, а «Забвение»
там занято силой Доминирования (Forgetful Mind). Взято слово из Руководства
для игроков — единственного источника, который её описывает. Придумывать
термин показалось хуже.

**«Изъян» против «Одержимости».** Руководство подписывает «Клановый изъян: X»
то, что на деле является Одержимостью: текст под этим заголовком описывает
принуждение на одну сцену. Официальное название термина — «Одержимость»
(Книга правил, стр. 210). В компендиуме сохранено официальное разделение.

**«Мощь», а не «Могущество».** Руководство зовёт Potence «МОГУЩЕСТВОМ»,
основная книга — «Мощью». Приведено к основной книге, как и «КОЛДОВСТВО
КРОВИ» → «Кровавое чародейство».

**Коллизии с недостатками.** Rarefied Tastes переведено «Изысканным вкусом»,
а не «разборчивостью», потому что «разборчивость» уже занята недостатком
питания. По той же причине Repulsiveness — «Отвратительность», а не
«Омерзительность».

**Фанатский перевод помечен.** Бану Хаким, Геката, Ласомбра и Министерство
переведены только в Руководстве для игроков; в этих записях источник указан
прямо в тексте, чтобы отличать их от официального.
"""


def module_dir():
    return next(p for p in ROOT.iterdir() if fix_clans.is_module_dir(p))


def table(rows, headers):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def main():
    mod = module_dir()
    mapping = yaml.safe_load(
        (ROOT / "data" / "mapping.yaml").read_text(encoding="utf-8"))

    entries = {}
    for path in mod.glob("packs/*/_source/*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        entries[data["_id"]] = data

    parts = [INTRO, STRUCTURE_DOC]

    rows = [[ru, originals.DISCIPLINES.get(ru, "—"), f"`{code}`"]
            for code, ru in sorted(DISCIPLINE_RU.items(), key=lambda kv: kv[1])]
    parts.append("## Дисциплины\n\n"
                 + table(rows, ["Термин", "Оригинал", "Код в системе"]))

    # Силы: перечисляется весь канон, а не только переведённое, — иначе
    # документ не работает планом. Русское имя и страница берутся из данных.
    ru_by_en, level_by_en, page_by_en = {}, {}, {}
    for _id, item in mapping["disciplines"].items():
        entry = entries.get(_id)
        if not entry or entry.get("type") != "power":
            continue
        english = originals.POWERS.get(entry["name"])
        if english:
            ru_by_en[english] = entry["name"]
            level_by_en[english] = entry["system"].get("level")
            page_by_en[english] = item.get("page")

    chunks, done, total = [], 0, 0
    for group in sorted(originals.CANON_POWERS):
        rows = []
        for english in originals.CANON_POWERS[group]:
            ru = ru_by_en.get(english)
            total += 1
            done += 1 if ru else 0
            rows.append([DONE if ru else TODO, ru or "—", english,
                         str(level_by_en.get(english) or "—"),
                         str(page_by_en.get(english) or "—")])
        have = sum(1 for r in rows if r[0] == DONE)
        chunks.append(f"### {group} — {have} из {len(rows)}" + NL * 2
                      + table(rows, ["", "Термин", "Оригинал", "Ур.", "Стр."]))

    extra = []
    for group in ("Ритуалы", "Алхимия слабокровных"):
        rows = []
        for _id, item in mapping["disciplines"].items():
            entry = entries.get(_id)
            if not entry or entry.get("type") != "power":
                continue
            if DISCIPLINE_RU.get(entry["system"].get("discipline")) != group:
                continue
            rows.append([DONE, entry["name"],
                         originals.POWERS.get(entry["name"], "—"),
                         str(entry["system"].get("level") or "—"),
                         str(item.get("page", "—"))])
        extra.append(f"### {group} — переведено {len(rows)}" + NL * 2
                     + table(sorted(rows, key=lambda r: (r[3], r[1])),
                             ["", "Термин", "Оригинал", "Ур.", "Стр."]))

    parts.append(f"## Силы Дисциплин" + NL * 2 + f"Переведено **{done} из "
                 f"{total}**. Непереведённые — из книг, которых у проекта "
                 f"нет: линейка прирастала силами в дополнениях." + NL * 2
                 + (NL * 2).join(chunks))
    parts.append("## Ритуалы и формулы" + NL * 2 + "Полный канон здесь не "
                 "приводится: в линейке их под две сотни, и почти все — из "
                 "книг, которых у проекта нет." + NL * 2 + (NL * 2).join(extra))
    rows = []
    for entry in sorted(entries.values(), key=lambda e: e.get("name", "")):
        if entry.get("type") != "clan":
            continue
        bane = fix_clans.BANE_NAMES.get(entry["name"], "—")
        found = re.search(r"<strong>Альтернативное проклятие: ([^<]+)</strong>",
                          entry["system"].get("bane") or "")
        variant = found.group(1) if found else "—"
        rows.append([entry["name"], bane, originals.BANES.get(bane, "—"),
                     variant, originals.BANE_VARIANTS.get(variant, "—")])
    parts.append("## Кланы и проклятия\n\n"
                 + table(rows, ["Клан", "Изъян", "Оригинал",
                                "Альтернативный изъян", "Оригинал"]))

    both = {**COMPULSIONS_BY_CLAN, **fix_clans.GUIDE_COMPULSIONS}
    rows = [[clan, ru, originals.COMPULSIONS.get(ru, "—")]
            for clan, ru in sorted(both.items())]
    parts.append("## Одержимости\n\nВ записи компендиума пока не внесены. "
                 "Семь названий — из Книги правил (стр. 212—213), семь — "
                 "из Руководства для игроков.\n\n"
                 + table(rows, ["Клан", "Термин", "Оригинал"]))

    by_english = {en: ru for ru, en in originals.PREDATOR_TYPES.items()}
    rows = [[DONE if en in by_english else TODO, by_english.get(en, "—"),
             en, book] for en, book in originals.CANON_PREDATOR_TYPES]
    have = sum(1 for r in rows if r[0] == DONE)
    parts.append(f"## Типы охотника — {have} из {len(rows)}\n\n"
                 "Четыре непереведённых — из Руководства для игроков, которое "
                 "у проекта есть: их можно взять хоть сейчас. Остальные "
                 "требуют книг, которых нет.\n\n"
                 + table(rows, ["", "Термин", "Оригинал", "Книга"]))

    rows = [[ru, "Blood Potency " + (ru.split()[2].rstrip(":") if len(ru.split()) > 2 else "")]
            for ru in make_mapping.BLOOD_POTENCY.values()]
    parts.append("## Сила Крови\n\n" + table(rows, ["Термин", "Оригинал"]))

    rows = []
    for _id, item in mapping["advantages-flaws"].items():
        entry = entries.get(_id)
        if not entry or "ru" not in item:
            continue
        rating = entry["name"].count("•")
        clean = entry["name"].replace("•", "").replace("()", "")
        rows.append([re.sub(r"\s+", " ", clean).strip(),
                     "•" * rating if rating else "—",
                     str(item.get("page", "—"))])
    parts.append(f"## Достоинства и недостатки\n\nВсего {len(rows)} записей. "
                 "Английских названий здесь нет: компактного сверенного списка "
                 "для них найти не удалось, а восстанавливать по памяти — ровно "
                 "тот риск, которого проект избегал.\n\n"
                 + table(sorted(rows), ["Термин", "Рейтинг", "Стр."]))

    rows = [[ru, ua] for ua, ru in sorted(DISCIPLINE_ALIASES.items())]
    parts.append("## Приведение названий из Руководства\n\nРуководство для "
                 "игроков зовёт Дисциплины по-своему; в компендиуме приведено "
                 "к основной книге.\n\n"
                 + table(rows, ["Как в основной книге", "Как в Руководстве"]))

    parts.append("## Имена собственные\n\nЗаголовки в книге набраны капсом, "
                 "и при переводе в обычный регистр эти слова сохраняют "
                 "заглавную.\n\n"
                 + table([[v] for v in sorted(set(PROPER_NOUNS.values()))
                          if v[:1].isupper()], ["Слово"]))

    parts.append(DECISIONS)

    OUT.write_text("\n\n---\n\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print(f"собран глоссарий -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
