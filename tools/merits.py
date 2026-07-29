"""Разбор раздела достоинств и недостатков.

Свёрстан он иначе, чем силы Дисциплин: имя записи не вынесено в заголовок,
а набрано жирным прямо в потоке текста —

    ■ Недостаток: (••) фермер. Ты питаешься исключительно кровью животных…
    ••• Крепкий желудок. Холодная и испорченная кровь…

Поэтому начало записи опознаётся по связке «маркер списка или рейтинг из
точек, а сразу за ним — жирное имя», а не по отдельной строке-заголовку.
"""

import re

MERIT_NAME_FONT = "CormorantGaramond-Bold"
MERIT_NAME_SIZE = (9.5, 10.5)

# Категории набраны двумя разными начертаниями: достоинства — вразрядку
# капсом («ВНЕШНОСТЬ.»), факты биографии — обычным кеглем («Богатство»).
MERIT_CATEGORY_FONTS = {("GillSansNova-Book", 7.5), ("CormorantGaramond-Bold", 14.0)}

# Рейтинг записи: точки, кружки и скобки вокруг них.
RATING_CHARS = set("●○◦•⬜⬛■□()")

FLAW_PREFIX_RE = re.compile(r"^недостаток\s*:?\s*$", re.I)


def _spans(line):
    return [s for s in line["spans"] if s["text"].strip()]


def _is_name_span(span):
    return (span["font"] == MERIT_NAME_FONT
            and MERIT_NAME_SIZE[0] < span["size"] < MERIT_NAME_SIZE[1])


def category(line):
    """Название категории, если строка её открывает.

    Заголовок набран «в подбор»: название и первая фраза вводного абзаца
    стоят в одной строке («ВНЕШНОСТЬ. Далеко не все вампиры выглядят…»),
    поэтому смотреть надо только на ведущие спаны, а не на строку целиком.
    """
    sp = _spans(line)
    if not sp:
        return None
    key = (sp[0]["font"], round(sp[0]["size"], 1))
    if key not in MERIT_CATEGORY_FONTS:
        return None

    parts = []
    for s in sp:
        if (s["font"], round(s["size"], 1)) != key:
            break
        parts.append(s["text"])
    text = re.sub(r"\s+", " ", "".join(parts)).strip()

    # Капсом набраны именно категории; жирный той же гарнитуры в потоке —
    # это имя записи, и капсом оно не бывает.
    if key == ("GillSansNova-Book", 7.5) and text != text.upper():
        return None
    return text.rstrip(".").strip() or None


def entry_start(line, bullet_font, invisible_spaces):
    """Начало записи: имя, рейтинг и признак недостатка. Иначе None.

    Рейтинг обязателен для сопоставления: в компендиуме соседние записи
    различаются именно им, а не названием. «Вада: (•) Життя в минулому» и
    «Вада: (••) Архаїчний» — это «ходячий анахронизм» и «ретроград», и по
    одним названиям не определить, какое из них однодотовое.
    """
    sp = _spans(line)
    if not sp:
        return None

    # Запись может открываться и просто жирным именем: рейтинг набран отдельным
    # мелким кеглем и в строку попадает не всегда («Важный. Окружающие…»).
    # Ложных срабатываний это не даёт: продолжение абзаца всегда идёт светлым.
    i, rating, is_flaw = 0, 0, False
    while i < len(sp):
        text = sp[i]["text"].strip()
        if sp[i]["font"] == bullet_font or (text and set(text) <= RATING_CHARS):
            rating += text.count("●")
            i += 1
        elif _is_name_span(sp[i]) and FLAW_PREFIX_RE.match(text):
            is_flaw = True                    # «Недостаток:» — не имя, а метка
            i += 1
        else:
            break

    if i >= len(sp) or not _is_name_span(sp[i]):
        return None

    parts = []
    while i < len(sp) and _is_name_span(sp[i]):
        parts.append(sp[i]["text"])
        i += 1

    name = "".join(parts)
    for ch in invisible_spaces:
        name = name.replace(ch, " ")
    name = re.sub(r"\s+", " ", name).strip().rstrip(".").strip()
    if not name:
        return None

    # Остаток строки после имени. Имя, рейтинг и метку «Недостаток:» несёт
    # заголовок записи, и в тексте они были бы вторым экземпляром: получалось
    # «Известный. Известный. Неонат, представленный…».
    rest = "".join(s["text"] for s in sp[i:])
    for ch in invisible_spaces:
        rest = rest.replace(ch, " ")
    rest = rest.lstrip(". ")

    return {"name": name, "rating": rating, "flaw": is_flaw, "rest": rest}
