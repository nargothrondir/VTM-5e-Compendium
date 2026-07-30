"""Разбор кланов из Руководства для игроков.

Отдельный модуль, потому что книга свёрстана совершенно иначе, чем основная:
своя гарнитура заголовков (B52) и тела (LiteraturnayaC), плавающий кегль,
английские колонтитулы посреди страницы и местами испорченная кодировка.

Четыре клана — Бану Хаким, Геката, Ласомбра и Министерство — существуют
только здесь, официального перевода у них пока нет.
"""

import re

TITLE_FONT = "B52"
BODY_FONT = "LiteraturnayaC"
BODY_SIZE = (8.5, 11.5)

# Заголовки разделов внутри клана. Кегль гуляет, поэтому опознаём по тексту.
ABOUT_RE = re.compile(r"^Кто такие\b")
DISCIPLINES_RE = re.compile(r"^Дисциплины\b")
BANE_RE = re.compile(r"^Проклятье\b")
BANE_NAME_RE = re.compile(r"^Клановый изъян\s*:\s*(.+)$")
ARCHETYPES_RE = re.compile(r"Архетипы\b")

# Мусор, который лезет в тело: колонтитулы и колонцифры.
JUNK_RE = re.compile(r"VAMPIRE|MASQUERADE|PLAYERS?\s+GUIDE|Chapter\s+\w+:|^[\d\s]+$", re.I)


def _spans(line):
    return [s for s in line.get("spans", []) if s["text"].strip()]


def _is_title(sp):
    return sp and sp[0]["font"] == TITLE_FONT


def _is_body(sp):
    return any(s["font"] == BODY_FONT
               and BODY_SIZE[0] < s["size"] < BODY_SIZE[1] for s in sp)


def extract(doc, pages, name, fix_encoding, normalize):
    """Один клан: описание, список Дисциплин, название изъяна и его текст."""
    part = None
    out = {"about": [], "disciplines": [], "bane": []}
    bane_name = ""

    for pno in range(*pages):
        for block in doc[pno].get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                sp = _spans(line)
                if not sp:
                    continue
                text = fix_encoding("".join(s["text"] for s in sp)).strip()

                if _is_title(sp):
                    hit = BANE_NAME_RE.match(text)
                    if hit:
                        bane_name = hit.group(1).strip()
                        continue
                    if ABOUT_RE.match(text):
                        part = "about"
                    elif DISCIPLINES_RE.match(text):
                        part = "disciplines"
                    elif BANE_RE.match(text):
                        part = "bane"
                    elif ARCHETYPES_RE.search(text):
                        part = None      # типажи в компендиум не переносим
                    continue

                if part and _is_body(sp) and not JUNK_RE.search(text):
                    out[part].append(text)

    return {
        "kind": "clan_entry", "name": name, "page": pages[0] + 1,
        "bane_name": bane_name,
        "text": normalize("\n".join(out["about"])),
        "disciplines_text": normalize("\n".join(out["disciplines"])),
        "bane": normalize("\n".join(out["bane"])),
    }


# Названия Дисциплин, встречающиеся в книге, — для вытаскивания их из прозы.
KNOWN = [
    "Анимализм", "Величие", "Доминирование", "Кровавое чародейство",
    "Метаморфозы", "Мощь", "Небытие", "Сокрытие", "Стойкость",
    "Стремительность", "Ясновидение", "Тауматургия", "Забвение",
]


def disciplines_from(text):
    """Названия Дисциплин в порядке появления в тексте раздела."""
    found = []
    for name in KNOWN:
        pos = text.find(name)
        if pos >= 0:
            found.append((pos, name))
    return [name for _, name in sorted(found)]

# Типы питания в Руководстве набраны двумя гарнитурами вперемешку —
# видимо, вёрстку собирали из разных источников. Опознаём по кеглю.
PREDATOR_TITLE_FONTS = {"LiteraturnayaC", "DXLubava-Regular"}
PREDATOR_TITLE_SIZE = (18.0, 22.0)
# Кегль тела гуляет между 9 и 10 пунктами: нижняя граница строгой быть
# не может, иначе последняя запись раздела осталась бы без текста.
PREDATOR_BODY_SIZE = (8.5, 11.5)
BULLET_FONTS = ("Wingdings", "ZapfDingbats")


def predator_types(doc, pages, fix_encoding, normalize, lines_of,
                   opening="ТИПЫ ПИТАНИЯ"):
    """Типы питания из Руководства: имя и текст до следующего заголовка.

    Перечень обрывается титулом следующего раздела, но первым таким титулом
    идёт заголовок самого перечня — его надо пропустить, иначе разбор
    завершится, не начавшись.
    """
    out, current, started, bullet = [], None, False, False

    def flush():
        nonlocal current
        if current:
            current["text"] = normalize(chr(10).join(current.pop("lines")))
            out.append(current)
            current = None

    # Обход строго в порядке чтения: заголовок «Лазутчика» и титул
    # следующего раздела стоят на одной полосе, и обход блоков подряд
    # обрывал перечень до того, как забирал последнюю запись.
    for pno in range(*pages):
        for line in lines_of(doc[pno]):
            if True:
                sp = _spans(line)
                if not sp:
                    continue
                text = fix_encoding("".join(s["text"] for s in sp)).strip()
                font, size = sp[0]["font"], sp[0]["size"]

                if font == TITLE_FONT and size > 24:
                    if not started and opening in text.upper():
                        started = True
                        continue
                    if started:          # титул следующего раздела
                        flush()
                        return out
                    continue

                if not started:
                    continue

                # Маркер списка стоит отдельной строкой своим шрифтом:
                # запоминаем и приклеиваем к следующей строке.
                if font.startswith(BULLET_FONTS):
                    bullet = True
                    continue

                if (font in PREDATOR_TITLE_FONTS
                        and PREDATOR_TITLE_SIZE[0] < size < PREDATOR_TITLE_SIZE[1]
                        and 2 < len(text) < 40):
                    flush()
                    current = {"name": text, "page": pno + 1, "lines": []}
                    bullet = False
                elif (current and font in PREDATOR_TITLE_FONTS
                      and PREDATOR_BODY_SIZE[0] < size < PREDATOR_BODY_SIZE[1]
                      and not JUNK_RE.search(text)):
                    current["lines"].append(("■ " if bullet else "") + text)
                    bullet = False

    flush()
    return out

# Раздел «Силы дисциплин». Имя силы набрано отдельной гарнитурой капсом,
# уровень — «Уровень N» шестнадцатым кеглем, тело — девятым.
POWER_NAME_FONT = "DXLubava-Regular"
POWER_NAME_SIZE = (9.0, 10.5)
POWER_LEVEL_SIZE = (15.0, 17.0)
# Кегль названия Дисциплины гуляет: «Кровавое чародейство» набрано
# шестнадцатым, остальные двадцатым. Гарнитура отличает его от
# «Уровень N», который тоже шестнадцатый, но другой гарнитурой.
POWER_DISC_SIZE = (15.0, 22.0)
LEVEL_RE = re.compile(r"^Уровень\s*([1-5])")


def discipline_powers(doc, pages, fix_encoding, normalize, lines_of,
                      opening="СИЛЫ ДИСЦИПЛИН"):
    """Новые силы Дисциплин из Руководства."""
    out, current, started = [], None, False
    discipline, level, bullet, prev_title = None, None, False, False

    def flush():
        nonlocal current
        if current:
            current["text"] = normalize(chr(10).join(current.pop("lines")))
            out.append(current)
            current = None

    for pno in range(*pages):
        for line in lines_of(doc[pno]):
            sp = _spans(line)
            if not sp:
                continue
            text = fix_encoding("".join(s["text"] for s in sp)).strip()
            font, size = sp[0]["font"], sp[0]["size"]

            if font == TITLE_FONT and size > 24:
                if not started and opening in text.upper():
                    started = True
                    continue
                if started:
                    flush()
                    return out
                continue
            if not started:
                continue

            if font == TITLE_FONT and POWER_DISC_SIZE[0] < size < POWER_DISC_SIZE[1]:
                flush()
                # «Ритуалы кровавого чародейства» переносится на две строки.
                if prev_title:
                    discipline = f"{discipline} {text}"
                else:
                    discipline, level = text, None
                prev_title = True
                continue
            prev_title = False

            hit = LEVEL_RE.match(text)
            if hit and POWER_LEVEL_SIZE[0] < size < POWER_LEVEL_SIZE[1]:
                flush()
                level = int(hit.group(1))
                continue

            if font.startswith(BULLET_FONTS):
                bullet = True
                continue

            if (font == POWER_NAME_FONT
                    and POWER_NAME_SIZE[0] < size < POWER_NAME_SIZE[1]
                    and text == text.upper() and len(text) > 3):
                flush()
                current = {"name": text.capitalize(), "discipline": discipline,
                           "level": level, "page": pno + 1, "lines": []}
                bullet = False
            elif (current and PREDATOR_BODY_SIZE[0] < size < PREDATOR_BODY_SIZE[1]
                  and not JUNK_RE.search(text)):
                current["lines"].append(("■ " if bullet else "") + text)
                bullet = False

    flush()
    return out

# Подписи блоков внутри силы. Руководство ставит их сплошным текстом и
# местами без пробела после двоеточия («Амальгами:Ясновидение 1»), тогда
# как в компендиуме каждый блок — отдельный абзац с маркером. Порядок
# важен: длинные подписи проверяются раньше коротких, иначе «Пулы кубиков»
# разрежется по «Пул».
POWER_LABELS = [
    "Амальгами", "Амальгама", "Необходимые условия", "Необходимая сила",
    "Пулы кубиков", "Пул кубиков", "Стоимость", "Ингредиенты", "Процесс",
    "Продолжительность", "Длительность", "Система", "Пул",
]
LABEL_RE = re.compile(r"\s*(" + "|".join(POWER_LABELS) + r")\s*:\s*")


# Значение амальгамы — «Дисциплина N». Отдельного маркера между ним и
# описанием силы книга не ставит, поэтому режем по цифре уровня.
AMALGAM_RE = re.compile("■ Амальгам[аи]: [^\\n\\d]+\\d(?=\\s+[А-ЯЁ])")


# Раздел «Новые Достоинства и Недостатки». Имя записи набрано B52 капсом
# и несёт рейтинг точками прямо в строке: «ГОРОДСКИЕ ТАЙНЫ •». Разряд
# («Достоинства внешности») — шестнадцатым, сторона («Достоинства»,
# «Недостатки») — двадцатым, причём «Недостатки» ещё и другой гарнитурой.
MERIT_NAME_FONT = "B52"
MERIT_NAME_SIZE = (9.0, 10.0)
MERIT_GROUP_SIZE = (15.0, 17.0)
MERIT_SIDE_SIZE = (19.0, 21.0)
# Кегль тела гуляет между девятым и десятым: «Неприкосновенный» набран
# десятым и при строгой верхней границе оставался вовсе без текста.
MERIT_BODY_SIZE = (8.5, 10.5)

# Рейтинг: точки подряд, иногда в скобках — «ЛИКВИДАТОР (•)».
RATING_RE = re.compile(r"\s*\(?\s*([•·∙]+)\s*\)?\s*$")


def merits(doc, pages, fix_encoding, normalize, lines_of,
           opening="НОВЫЕ"):
    """Достоинства и недостатки из Руководства.

    Сторона записи (достоинство или недостаток) не выводится из текста —
    только из того, под каким из двух заголовков она стоит.
    """
    out, current, started = [], None, False
    side, group, prev_title = None, None, False

    def flush():
        nonlocal current
        if current:
            current["text"] = normalize(chr(10).join(current.pop("lines")))
            out.append(current)
            current = None

    for pno in range(*pages):
        for line in lines_of(doc[pno]):
            sp = _spans(line)
            if not sp:
                continue
            text = fix_encoding("".join(s["text"] for s in sp)).strip()
            font, size = sp[0]["font"], sp[0]["size"]

            if font == TITLE_FONT and size > 24:
                # Заголовок раздела занимает три строки — «Новые»,
                # «Достоинства и», «Недостатки», — и продолжение нельзя
                # принять за титул следующей главы.
                if not started and opening in text.upper():
                    started, prev_title = True, True
                    continue
                if started and not prev_title:
                    flush()
                    return out
                continue
            prev_title = False
            if not started:
                continue

            if MERIT_SIDE_SIZE[0] < size < MERIT_SIDE_SIZE[1]:
                flush()
                side, group = text, None
                continue
            if MERIT_GROUP_SIZE[0] < size < MERIT_GROUP_SIZE[1]:
                flush()
                group = text
                continue

            # Опорой служит рейтинг, а не капс: «Двойное проклятье ••»
            # набрано строчными и по капсу терялось целиком.
            hit = (RATING_RE.search(text)
                   if font == MERIT_NAME_FONT
                   and MERIT_NAME_SIZE[0] < size < MERIT_NAME_SIZE[1]
                   and len(text) > 3 else None)
            if hit:
                flush()
                current = {"name": RATING_RE.sub("", text).strip(),
                           "rating": len(hit.group(1)),
                           "side": side, "group": group,
                           "page": pno + 1, "lines": []}
            elif (current and MERIT_BODY_SIZE[0] < size < MERIT_BODY_SIZE[1]
                  and not JUNK_RE.search(text)):
                current["lines"].append(text)

    flush()
    return out


def split_labels(text):
    """Сплошной текст силы -> абзацы с маркерами, как в остальном компендиуме."""
    marked = LABEL_RE.sub(lambda m: chr(10) + chr(9632) + " " + m.group(1) + ": ",
                          text)
    # Значение амальгамы — «Дисциплина N», дальше сразу идёт описание силы.
    # Отдельного маркера между ними в книге нет, режем по цифре уровня.
    marked = AMALGAM_RE.sub(lambda m: m.group(0) + "." + chr(10), marked)
    return re.sub(r"[ \t]{2,}", " ", marked).strip()
