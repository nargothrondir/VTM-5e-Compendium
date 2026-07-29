"""Сборка data/mapping.yaml из таблицы соответствий.

Соответствия проставлены вручную: официальные русские названия часто не
переводятся буквально («Безпомилковий приціл» -> «Безупречная точность»),
поэтому строковое сходство здесь не работает. Мостом служит каноническое
английское название силы.

Скрипт лишь подставляет к ним номера страниц и украинские имена из данных,
чтобы в mapping.yaml не было опечаток, и проверяет полноту покрытия.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = ROOT / "data" / "book_sections.json"
OUT = ROOT / "data" / "mapping.yaml"

# _id записи компендиума -> заголовок раздела в русской книге.
# _id неизменен, поэтому таблица переживает и переименования, и переводы.
POWERS = {
    # --- Анимализм
    "ve12964atPPHF3QD": "ЧУТЬЁ НА ЗВЕРЯ",
    "jKi5asy0Vad7t2X7": "ФАМУЛУС",
    "4LY8gOGIhb2viROk": "ЯЗЫК ЖИВОТНЫХ",
    "q8hCTvKqgER4a7l5": "ЗВЕРСКИЙ АППЕТИТ",
    "c9y70r68bsjBwDNs": "ТРУПНЫЙ УЛЕЙ",
    "4001N574ixF79TIb": "УСМИРЕНИЕ ЗВЕРЯ",
    "Lsb2jp7KrSrSfN1F": "ПОГЛОЩЕНИЕ ДУХА",
    "r3Y2aoiqYzCvNKZj": "ОТЧУЖДЕНИЕ ЗВЕРЯ",
    "Xv1xV6OZ4XrsAvV2": "ЦАРЬ ЗВЕРЕЙ",
    # --- Величие
    "5P6YvhZZlastLrZo": "БЛАГОГОВЕНИЕ",
    "ny9InSRCZEfIyV0l": "УГРОЗА",
    "Cp1arvoKbkcONGwU": "НЕЗАБЫВАЕМЫЙ ПОЦЕЛУЙ",
    "J5RUvwLgB5VmdPZM": "ОЧАРОВАНИЕ",
    "ZtREmkrSoZZqmZkq": "УСТРАШАЮЩИЙ ВЗОР",
    "rD3mOz4YN5LKLh2h": "ПРИЗЫВ",
    "PmeH36jzllcXiuPb": "ПРИТЯГАТЕЛЬНЫЙ ГОЛОС",
    "cdeuhdY4ngD6cYKq": "ЗВЕЗДА ЭФИРА",
    "Qi20ayGyhBONe5n7": "ПРЕКЛОНЕНИЕ",
    # --- Доминирование
    "gyhnOSNiYqmWRLHT": "ПРИНУЖДЕНИЕ",
    "xCCtEroRVLAw314V": "ПРОВАЛ В ПАМЯТИ",
    "VrxvOv0sLz2ZhXCm": "ВНУШЕНИЕ",
    "yqx27v2VCeBK3zYp": "ПОМЕШАТЕЛЬСТВО",
    "l59qhQZHR8tynmEo": "ВНЕДРЁННАЯ ДИРЕКТИВА",
    "KmzCcdtTKJKLoFwi": "ЗАБВЕНИЕ",
    "HiBUwxtK2zKRkBuX": "ОПРАВДАНИЕ",
    "zR6f82C2yx1VwrvB": "СТАДНЫЙ ИНСТИНКТ",
    "Vlw5YO2nDmH777pH": "ПРИКАЗ НА САМОУНИЧТОЖЕНИЕ",
    # --- Метаморфозы
    "BIHT7ZDD6sNZXKn8": "ГЛАЗА ЗВЕРЯ",
    "I9lUpZ6Yb6LTVhOJ": "ЛЁГКОСТЬ ПЁРЫШКА",
    "m1YK7ZXtZ9ieusW8": "ОРУЖИЕ ЗВЕРЯ",
    "pmMRZAmWCDB3GngE": "СЛИЯНИЕ С ЗЕМЛЁЙ",
    "IREwXzpHFwnk8uQZ": "СМЕНА ОБЛИКА",
    "L0rzl2WvqmiiQRZf": "ПЕРЕВОПЛОЩЕНИЕ",
    "vphRUkShpusPJIdl": "ПРЕВРАЩЕНИЕ В ТУМАН",
    "dWnIXu8UZ7tzBGXP": "СВОБОДНОЕ СЕРДЦЕ",
    # --- Мощь
    "pUDiIlGhaaZbZXsv": "МОЩНЫЙ ПРЫЖОК",
    "ytEH2ugcTNChJrvl": "СМЕРТОНОСНОСТЬ",
    "24sZmHFlpHDUm27J": "СОКРУШЕНИЕ",
    "pLPZd3T1Dz3zrKJd": "ГРУБОЕ НАСЫЩЕНИЕ",
    "79Fv3STrOWoGwYNF": "ИСКРА ЯРОСТИ",
    "LSsDwUyiF01G3lkr": "МЁРТВАЯ ХВАТКА",
    "towCVvghMLnPPYMP": "ГЛОТОК МОГУЩЕСТВА",
    "aeTgjooyCrzyoQw2": "ЗЕМЛЕТРЯСЕНИЕ",
    "LGw7CrZGdfzGlsSK": "КУЛАК КАИНА",
    # --- Сокрытие
    "EnhLWsuFFFOw8B1D": "ПЛАЩ ТЕНЕЙ",
    "zkfXHOs9jNBjeRGT": "БЕЗМОЛВИЕ СМЕРТИ",
    "V2TztYXBIMMZWTPp": "НЕЗРИМАЯ ПОСТУПЬ",
    "eBgOKFagMvFn1gS3": "МАСКА ТЫСЯЧИ ЛИЦ",
    "fa47WL2EMvEVIyLn": "ЭЛЕКТРОННЫЙ ПРИЗРАК",
    "KwJQCizRvhSoKshJ": "БЕССЛЕДНОЕ ИСЧЕЗНОВЕНИЕ",
    "krXsNDqixwKgjMXy": "МАСКИРОВКА",
    "Tc0WCqxr66enu38u": "ЛИЧИНА САМОЗВАНЦА",
    "gIlltX5hOWguc82N": "ТАЙНОЕ СОБРАНИЕ",
    # --- Стойкость
    "Z3CHNqv25fYrIOWW": "СИЛА ЖИЗНИ",
    "0pXG5WPPUFZZbgfC": "ТВЁРДОСТЬ ДУХА",
    "SRUoS7NaGbca9JI3": "ЖИВУЧИЕ ЗВЕРИ",
    "kZilLHOGrPLd15aE": "НЕПРОШИБАЕМОСТЬ",
    "WmN6ihALeDJVbY6C": "ПРЕВОЗМОГАНИЕ ПРОКЛЯТИЯ",
    "w6NJOhp2vjk7yJHO": "УКРЕПЛЕНИЕ СОЗНАНИЯ",
    "pyYh72yD3Hm9D4V6": "ГЛОТОК УПОРСТВА",
    "5zbGyuRsnGOCbm29": "ГОРНИЛО БОЛИ",
    "T855yn4iB3gTBXRH": "МРАМОРНАЯ ПЛОТЬ",
    # --- Стремительность
    "wfnjLhQ0w1IaDsKn": "КОШАЧЬЯ ГРАЦИЯ",
    "bHccJKrsuYuAR5Fh": "БЫСТРАЯ РЕАКЦИЯ",
    "UXy1WD4lAqXrJbrq": "ПРОВОРСТВО",
    "7VztJcQXRNLngAUB": "БЫСТРЕЕ ВЕТРА",
    "1kgwezffskwhiDOR": "ТРАВЕРС",
    "VgQePRR5eOpGCHG1": "БЕЗУПРЕЧНАЯ ТОЧНОСТЬ",
    "6vuCIALreASFTSkL": "ГЛОТОК ИЗЯЩЕСТВА",
    "0CuTAz11OQyTu8QD": "МОЛНИЕНОСНЫЙ УДАР",
    "DB5yG7MhsDS3R3QH": "СКОРОСТЬ МЫСЛИ",
    # --- Ясновидение
    "qIAXLdBcSOKxqa9t": "ОБОСТРЕНИЕ ЧУВСТВ",
    "5gUFnvi0GFfyIEl2": "ПОТУСТОРОННЕЕ ЗРЕНИЕ",
    "W6UmkY8jGLF6nA5G": "ПРЕДВЕСТИЕ",
    "bjX7rOY682d4m13I": "ПОЗНАНИЕ ДУШИ",
    "iW0Age4PHhRqVOKi": "СЛИЯНИЕ ЧУВСТВ",
    "kJSVGJZvOX5gBCLS": "ПСИХОМЕТРИЯ",
    "JraucACRfWV8q9jq": "ВСЕЛЕНИЕ",
    "JeX6DGl9tWvID0Lm": "ДАЛЬНОВИДЕНИЕ",
    "bNgez7daRr5UKy2U": "ТЕЛЕПАТИЯ",
    # --- Кровавое чародейство
    "E0iETWlXHv8winFE": "ВКУС КРОВИ",
    "mDJ8uXmOcSZh3jZa": "ЕДКАЯ КРОВЬ",
    "1XvVZMsR8MiieIt3": "ИСТОНЧЕНИЕ ВИТЭ",
    "R9nWSmQwVMK6Wq41": "КАСАНИЕ СКОРПИОНА",
    "K1u9NnNbWLnWYGuP": "СГУЩЕНИЕ КРОВИ",
    "Dbs97SaeiVMZwjCp": "ХИЩЕНИЕ КРОВИ",
    "6xphi8PWFeATVp0K": "ЛАСКА ВААЛА",
    "tUIxhRo7tOri9cTs": "КОТЁЛ КРОВИ",
    # Помечены в компендиуме как sorcery, но по книге это ритуалы.
    "APmcewZQ2crjTfNg": "ВЕЧЕРНЯЯ БОДРОСТЬ",
    "qAqROiLe03kERTWy": "ЗАЩИТНЫЙ КРУГ ОТ ГУЛЕЙ",
    # --- Ритуалы
    "RxB4r0EYFzn4lCDh": "ЗАЩИТНАЯ ПЕЧАТЬ ОТ ГУЛЕЙ",
    "MaVj9RHYNZ2tmCCp": "ПАУЧЬИ ЛАПЫ",
    "NWxSwXb0gSbHMKI7": "ПОСТИЖЕНИЕ КРОВИ",
    "C0iwLjySwTL8LxSQ": "ПУТЕВОДНЫЙ КАМЕНЬ",
    "prWaqBaQRmkVIS6M": "ЗАЩИТНАЯ ПЕЧАТЬ ОТ ДУХОВ",
    "gyF7rY1XjAUZChze": "ИСТИНА В КРОВИ",
    "QQDtbsfMv7u9XZQI": "ОЧИ ВАВИЛОНСКИЕ",
    "rNK67AiWZqAdHTTn": "СВЕЧЕНИЕ СЛЕДОПЫТА",
    "xlTgyyAOaLDsmSOJ": "СВЯЗЬ С СИРОМ",
    "AmQD8nTMveykzlyB": "ЗАЩИТНАЯ ПЕЧАТЬ ОТ ЛЮПЕНОВ",
    "rRo6BRaXTIgxd0A7": "ЗАЩИТНЫЙ КРУГ ОТ ДУХОВ",
    "e8BFiWAIm4AbZ2PL": "ЗОВ ДАГОНА",
    "r1a89eztdu9w5rcB": "ОТТОРЖЕНИЕ ГУБИТЕЛЬНОГО ДРЕВА",
    "NAnFdAhLHdqafHfb": "ПОЖИРАТЕЛЬ ПЛАМЕНИ",
    "E7206bFG8iUjp6kz": "ЭССЕНЦИЯ ВОЗДУХА",
    "7KT49ezXCamJQSRX": "БЕСПЛОТНЫЙ ПУТЬ",
    "uASUntSIRrTfaDkS": "ЗАЩИТА НЕПРИКОСНОВЕННОГО УБЕЖИЩА",
    "hOnTX8eMdYCr7HU6": "ЗАЩИТНАЯ ПЕЧАТЬ ОТ КАИНИТОВ",
    "Yuu3WkK03qPUdWRL": "ЗАЩИТНЫЙ КРУГ ОТ ЛЮПЕНОВ",
    "d7Dqc34J4lt3ZBvr": "ОКО НОЧНОГО ЯСТРЕБА",
    "hOn4UVkzrseLhTY2": "ВРАТА ИСТИННОГО СВЯТИЛИЩА",
    "Qz8L3xX7Gg6nmoFb": "ЖАЛО НЕИЗБЕЖНОЙ ПОГИБЕЛИ",
    "OeIweEimZiq8Irgg": "ЗАЩИТНЫЙ КРУГ ОТ КАИНИТОВ",
    "iKsnbPJSqiyXGoQo": "КАМЕННОЕ СЕРДЦЕ",
    # --- Алхимия слабокровных
    "KIDOlLYXTa6gWAwU": "ДЛИННЫЕ РУКИ",
    "5H0ip9mA0bKiZ1Ic": "МАРЕВО",
    "5HnBgnuPH0GH4RcX": "СМОГ",
    "ajVkVf06GqJuqAMp": "НЕЧЕСТИВАЯ ИЕРОГАМИЯ",
    "7kiC8h5t2VIP1ql7": "ВОССТАНОВЛЕНИЕ КРОВИ",
    "gvPH9VCShpRxQgZ3": "ИМПУЛЬС",
    "4Ee6EUjcaVtYnzfG": "БУДИЛЬНИК",
}

# Типы охотника. Названия в переводе не буквальны и опознаются по смыслу:
# «Бестия» питается кровью Сородичей (Blood Leech), «Идол» — знаменитость
# или глава секты (Osiris), «Налётчик» берёт добычу силой (Alleycat).
PREDATOR_TYPES = {
    "BCVKeoYAt59ZkFWV": "Бестия",          # Кровопивця / Blood Leech
    "WRykPxFBJIHET2ij": "Джентльмен",      # Консенсуаліст / Consensualist
    "IET1GfclEDpIhIkb": "Идол",            # Осіріс / Osiris
    "Bagl9LOhtzPV3a2v": "Искуситель",      # Сирена / Siren
    "Kihkcn3qaxJlE3tT": "Морфей",          # Пісочна людина / Sandman
    "LMuKaffhHN1iI2AU": "Налётчик",        # Вуличний кіт / Alleycat
    "4IqaYfUhm75WTOur": "Семьянин",        # Сім'янин / Cleaver
    "TMdpcf5EJV13bDG4": "Суррогатчик",     # Заготівельник / Bagger
    "U3aFkYaQ5jIXmLIX": "Тусовщик",        # Королева сцени / Scene Queen
    "VdOPCYrSqRjxHHNr": "Фермер",          # Фермер / Farmer
}

BLOOD_POTENCY = {
    "oSaUNjeKe5Dl2CGk": "Сила Крови 0 (ноль): слабая кровь",
    "7XWp1JxbGtnuyiHP": "Сила Крови 1",
    "30rrUPOpyv2OeluD": "Сила Крови 2",
    "YqhcVuqAPXI5uOgu": "Сила Крови 3",
    "W4xJEGeafqxwhEUF": "Сила Крови 4",
    "Dubn4u1xi7ZrC19q": "Сила Крови 5",
    "Q7ck8s4VF3c6eJw9": "Сила Крови 6 и выше",
}

# Папки — это структура компендиума, а не текст книги: у них переводится
# только название. Таблица по украинскому имени, потому что «Рівень N»
# повторяется в каждой Дисциплине; в mapping.yaml она разворачивается по _id.
FOLDER_NAMES = {
    "Алхімія Тонкокровних": "Алхимия слабокровных",
    "Анімалізм": "Анимализм",
    "Ауспекс": "Ясновидение",
    "Домінування": "Доминирование",
    "Кривава Магія": "Кровавое чародейство",
    "Могутність": "Мощь",
    "Обфускація": "Сокрытие",
    "Присутність": "Величие",
    "Протеан": "Метаморфозы",
    "Ритуали": "Ритуалы",
    "Стрімкість": "Стремительность",
    "Стійкість": "Стойкость",
    "Рівень 1": "Уровень 1",
    "Рівень 2": "Уровень 2",
    "Рівень 3": "Уровень 3",
    "Рівень 4": "Уровень 4",
    "Рівень 5": "Уровень 5",
    "Сила Крові": "Сила Крови",
    "Тип Хижака": "Тип охотника",
}

# Пак -> (таблица соответствий, типы записей, виды разделов книги).
PACKS = {
    "disciplines": (POWERS, {"power"}, {"power"}),
    "blood-potency-predator-type": (
        {**PREDATOR_TYPES, **BLOOD_POTENCY},
        {"predatorType", "resonance"},
        {"predator_type", "blood_potency"},
    ),
}

# Разделы книги, которые записями компендиума не являются.
# Перечислены явно, чтобы проверка полноты не считала их потерянными.
NOT_ENTRIES = {
    "ЗАЩИТНАЯ ПЕЧАТЬ",   # общее пояснение про обереги перед списком ритуалов
}


def module_dir():
    return next(p for p in ROOT.iterdir()
                if p.is_dir() and p.name.startswith("vampire-the-masquerade"))


def quote(text):
    return chr(34) + text.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34)) + chr(34)


def main():
    sections = json.loads(SECTIONS.read_text(encoding="utf-8"))
    problems = []
    result = {}

    for pack, (table, entry_types, section_kinds) in PACKS.items():
        by_name = {}
        for s in sections:
            if s["kind"] in section_kinds:
                by_name.setdefault(s["name"], s)

        source = module_dir() / "packs" / pack / "_source"
        entries = {}
        for path in sorted(source.glob("*.json")):
            d = json.loads(path.read_text(encoding="utf-8"))
            if d.get("type") in entry_types:
                entries[d["_id"]] = d

        for _id, ru in table.items():
            if _id not in entries:
                problems.append(f"{pack}: нет записи {_id} (сопоставлена с {ru!r})")
            if ru not in by_name:
                problems.append(f"{pack}: нет раздела {ru!r} в книге (для {_id})")

        for _id in entries.keys() - table.keys():
            problems.append(f"{pack}: запись без соответствия: "
                            f"{entries[_id]['name']!r} ({_id})")

        used = set(table.values()) | NOT_ENTRIES
        for name in by_name.keys() - used:
            problems.append(f"{pack}: раздел книги не использован: "
                            f"{name!r} (с.{by_name[name]['page']})")

        folders = {}
        for path in sorted(source.glob("*.json")):
            d = json.loads(path.read_text(encoding="utf-8"))
            if not d.get("_key", "").startswith("!folders!"):
                continue
            ru = FOLDER_NAMES.get(d["name"])
            if ru is None:
                problems.append(f"{pack}: папка без перевода: {d['name']!r}")
            else:
                folders[d["_id"]] = (d["name"], ru)

        result[pack] = (table, entries, by_name, folders)

    if problems:
        print("ПРОБЛЕМЫ СОПОСТАВЛЕНИЯ:")
        for x in problems:
            print(f"  x {x}")
        return 1

    total = sum(len(t) + len(f) for t, _, _, f in result.values())
    lines = [
        "# Сопоставление записей компендиума с разделами русских книг правил.",
        "#",
        "# Ключ — _id записи: он неизменен и переживает перевод названия.",
        "# Файл собирается tools/make_mapping.py и правится руками — это точка",
        "# ручного контроля перед тем, как tools/apply.py перенесёт текст.",
        "#",
        f"# записей: {total}",
        "",
    ]
    for pack, (table, entries, by_name, folders) in result.items():
        lines.append(f"{pack}:")
        order = sorted(table, key=lambda i: (by_name[table[i]]["page"], table[i]))
        for _id in order:
            section = by_name[table[_id]]
            lines += [
                f"  {_id}:",
                f"    ua: {quote(entries[_id]['name'])}",
                f"    ru: {quote(section['name'])}",
                f"    page: {section['page']}",
                f"    book: {quote(section['book'])}",
            ]
        for _id in sorted(folders, key=lambda i: folders[i][1]):
            ua, ru = folders[_id]
            lines += [f"  {_id}:", f"    ua: {quote(ua)}", f"    name: {quote(ru)}"]
        print(f"{pack}: сопоставлено {len(table)}, папок {len(folders)}")

    OUT.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
    print(f"записано {total} соответствий -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
