"""Сборка GLOSSARY.md — терминологического словаря проекта.

Словарь генерируется из тех же данных, по которым собран компендиум, а не
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
from add_clans import DISCIPLINE_ALIASES  # noqa: E402
from apply import PROPER_NOUNS  # noqa: E402
from candidates import DISCIPLINE_RU  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "GLOSSARY.md"

# Английские названия — мост, по которому шло сопоставление. В таблицах они
# нужны затем, чтобы читатель мог сверить перевод с любым другим источником.
DISCIPLINE_EN = {
    "Анимализм": "Animalism", "Величие": "Presence",
    "Доминирование": "Dominate", "Кровавое чародейство": "Blood Sorcery",
    "Метаморфозы": "Protean", "Мощь": "Potence", "Сокрытие": "Obfuscate",
    "Стойкость": "Fortitude", "Стремительность": "Celerity",
    "Ясновидение": "Auspex", "Ритуалы": "Rituals",
    "Алхимия слабокровных": "Thin-blood Alchemy", "Обливион": "Oblivion",
}

PREDATOR_EN = {
    "Бестия": "Blood Leech", "Джентльмен": "Consensualist", "Идол": "Osiris",
    "Искуситель": "Siren", "Морфей": "Sandman", "Налётчик": "Alleycat",
    "Семьянин": "Cleaver", "Суррогатчик": "Bagger", "Тусовщик": "Scene Queen",
    "Фермер": "Farmer",
}

BANE_EN = {
    "Буйный нрав": "Violent Temper", "Изысканный вкус": "Rarefied Tastes",
    "Звериные черты": "Bestial Features",
    "Расколотое восприятие": "Fractured Perspective",
    "Отвратительность": "Repulsiveness", "Жажда красоты": "Aesthetic Fixation",
    "Ущербная Кровь": "Deficient Blood",
    "Кровавая зависимость": "Blood Addiction",
    "Болезненный Поцелуй": "Painful Kiss",
    "Искажённое отражение": "Distorted Image",
    "Неприятие света": "Abhors the Light", "Обречённость": "Doomed",
    "Гонимые": "Hunted", "Привязанность": "Grounded", "Изгой": "Outcast",
}

# Одержимости из основной книги (стр. 212—213). В компендиум пока не внесены.
COMPULSIONS_CORE = {
    "Бруха": "бунт", "Вентру": "превосходство", "Гангрел": "животные порывы",
    "Малкавиан": "наваждение", "Носферату": "криптомания",
    "Тореадор": "восхищение", "Тремер": "перфекционизм",
}

INTRO = """# Словарь терминов

Терминология русского компендиума. Собрана по ходу перевода и **сгенерирована
из тех же данных, по которым собран модуль** — расходиться с содержимым паков
она не может. Перегенерируется командой `npm run glossary`.

Зачем: перевод шёл не с украинского, а сопоставлением с официальным русским
изданием, поэтому названия сплошь и рядом не буквальны. Словарь фиксирует,
какое решение принято и почему, — чтобы правки не разъезжались с уже
переведённым.

## Как выбиралась терминология

1. **Приоритет за официальным изданием.** Если книга даёт слово, берётся её
   слово, даже когда оно далеко от оригинала: Unerring Aim — «Безупречная
   точность», Baal's Caress — «Ласка Ваала».
2. **Мост — каноническое английское название.** Украинское и русское названия
   часто не похожи ни друг на друга, ни на оригинал, и сводить их напрямую
   бессмысленно. «Стрижень Відкладеного Розпаду» и «Жало неизбежной погибели» —
   это Shaft of Belated Quiescence.
3. **Где официального перевода нет — слово ищется в словаре самой книги,**
   а не в общем. Так появились названия проклятий (см. ниже).
4. **Ничего не выдумано молча.** Каждое решение, где источник не дал прямого
   ответа, перечислено в разделе «Спорные решения».
"""

DECISIONS = """## Спорные решения

Случаи, где источник не дал прямого ответа и решение принято осознанно.

**Названия клановых проклятий.** В оригинале имя есть у каждого проклятия,
но ни основная книга, ни Малая книга знаний их не приводят — ставят заголовок
«Изъян» и сразу текст. Похоже на упрощение при переводе. Названия переведены
с канонических английских, причём в словаре самой книги: четыре она подарила
дословно — «болезненный Поцелуй», «отвратительные», «жаждут красоты»,
«привязанность». Остальные собраны из её же лексики.

**«Обливион».** Дисциплины Oblivion в основной книге нет вовсе, а «Забвение»
там занято силой Доминирования (Forgetful Mind). Взято слово из Руководства
для игроков — единственного источника, который её описывает. Придумывать
термин показалось хуже.

**«Изъян» против «Одержимости».** Руководство для игроков подписывает
«Клановый изъян: X» то, что на деле является Одержимостью: текст под этим
заголовком описывает принуждение на одну сцену. Официальное название термина —
«Одержимость» (Книга правил, стр. 210). В компендиуме сохранено официальное
разделение.

**«Мощь», а не «Могущество».** Руководство зовёт Potence «МОГУЩЕСТВОМ»,
основная книга — «Мощью». Приведено к основной книге, как и «КОЛДОВСТВО
КРОВИ» → «Кровавое чародейство».

**Коллизии с недостатками.** Rarefied Tastes переведено «Изысканным вкусом»,
а не «разборчивостью», потому что «разборчивость» уже занята недостатком
питания. По той же причине Repulsiveness — «Отвратительность», а не
«Омерзительность».

**Фанатский перевод помечен.** Бану Хаким, Геката, Ласомбра и Министерство
переведены только в Руководстве для игроков; в этих записях источник указан
прямо в тексте, чтобы отличать их от официального текста.
"""

STRUCTURE = """## Структурные термины

Подписи, которыми размечены блоки внутри записей. Взяты из основной книги.

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
| витэ | vitae | сквозной термин |
| Становление | Embrace | сквозной термин |
| Сородичи | Kindred | сквозной термин |

Слово «Кровь» в значении игрового термина книга пишет с заглавной
(«испытание Крови», «Сила Крови»), в бытовом значении — со строчной.
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
    mapping = yaml.safe_load((ROOT / "data" / "mapping.yaml").read_text(encoding="utf-8"))

    entries = {}
    for path in mod.glob("packs/*/_source/*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        entries[data["_id"]] = data

    parts = [INTRO, STRUCTURE]

    # --- Дисциплины
    rows = []
    for code, ru in sorted(DISCIPLINE_RU.items(), key=lambda kv: kv[1]):
        ua = next((k for k, v in make_mapping.FOLDER_NAMES.items()
                   if v == ru and k != ru), "—")
        rows.append([ru, DISCIPLINE_EN.get(ru, "—"), f"`{code}`", ua])
    parts.append("## Дисциплины\n\n" + table(
        rows, ["Русский", "Оригинал", "Код в системе", "Украинский"]))

    # --- Силы, ритуалы, алхимия
    by_group = {}
    for _id, item in mapping["disciplines"].items():
        entry = entries.get(_id)
        if not entry or entry.get("type") != "power":
            continue
        group = DISCIPLINE_RU.get(entry["system"].get("discipline"), "?")
        by_group.setdefault(group, []).append([entry["name"], item["ua"],
                                              str(item.get("page", ""))])
    chunks = []
    for group in sorted(by_group):
        rows = sorted(by_group[group])
        chunks.append(f"### {group}\n\n" + table(
            rows, ["Русский", "Украинский", "Стр."]))
    parts.append("## Силы Дисциплин, ритуалы и формулы\n\n"
                 "Всего " + str(sum(len(v) for v in by_group.values()))
                 + " записей.\n\n" + "\n\n".join(chunks))

    # --- Кланы
    rows = []
    for entry in sorted(entries.values(), key=lambda e: e.get("name", "")):
        if entry.get("type") != "clan":
            continue
        bane = fix_clans.BANE_NAMES.get(entry["name"], "—")
        variant = re.search(r"<strong>Альтернативное проклятие: ([^<]+)</strong>",
                            entry["system"].get("bane") or "")
        rows.append([entry["name"], bane, BANE_EN.get(bane, "—"),
                     variant.group(1) if variant else "—",
                     COMPULSIONS_CORE.get(entry["name"],
                                          fix_clans.GUIDE_COMPULSIONS.get(
                                              entry["name"], "—"))])
    parts.append("## Кланы\n\n" + table(
        rows, ["Клан", "Изъян", "Оригинал", "Альтернативный изъян",
               "Одержимость"]))

    # --- Типы охотника и Сила Крови
    rows = []
    for _id, ru in make_mapping.PREDATOR_TYPES.items():
        ua = mapping["blood-potency-predator-type"].get(_id, {}).get("ua", "—")
        rows.append([ru, PREDATOR_EN.get(ru, "—"), ua])
    parts.append("## Типы охотника\n\n" + table(
        sorted(rows), ["Русский", "Оригинал", "Украинский"]))

    rows = [[ru, mapping["blood-potency-predator-type"].get(_id, {}).get("ua", "—")]
            for _id, ru in make_mapping.BLOOD_POTENCY.items()]
    parts.append("## Сила Крови\n\n" + table(rows, ["Русский", "Украинский"]))

    # --- Достоинства и недостатки
    rows = []
    for _id, item in mapping["advantages-flaws"].items():
        entry = entries.get(_id)
        if entry and "ru" in item:
            rows.append([entry["name"], item["ua"]])
    parts.append("## Достоинства и недостатки\n\n"
                 f"Всего {len(rows)} записей.\n\n"
                 + table(sorted(rows), ["Русский", "Украинский"]))

    # --- Прочее
    rows = [[ru, ua] for ua, ru in sorted(make_mapping.FOLDER_NAMES.items())
            if ua != ru]
    parts.append("## Названия папок\n\n" + table(rows, ["Русский", "Украинский"]))

    rows = [[ru, ua] for ua, ru in sorted(DISCIPLINE_ALIASES.items())]
    parts.append("## Названия из Руководства для игроков\n\n"
                 "Руководство зовёт Дисциплины по-своему; приведено "
                 "к основной книге.\n\n"
                 + table(rows, ["Как в основной книге", "Как в Руководстве"]))

    parts.append("## Имена собственные\n\n"
                 "Заголовки в книге набраны капсом, и при переводе в обычный "
                 "регистр эти слова сохраняют заглавную:\n\n"
                 + table([[v] for v in sorted(set(PROPER_NOUNS.values()))
                          if v[:1].isupper()], ["Слово"]))

    parts.append(DECISIONS)

    OUT.write_text("\n\n---\n\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print(f"собран словарь -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
