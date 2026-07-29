"""Нормализация текста, извлечённого из книг правил.

Артефактов ровно три, и все они чинятся без ИИ:
  * NBSP (\xa0) и прочие невидимые пробелы;
  * мягкие переносы на конце строки (в STV501 это U+2011, местами обычный дефис);
  * маркер списка, который выводится как латинская `n` (символ Wingdings).
"""

import re

# Дефисы, которыми книга разрывает СЛОВО на переносе: обычный дефис-минус,
# мягкий перенос, дефис и неразрывный дефис. Длинное и среднее тире сюда
# не входят: в конце строки это полноценная пунктуация («грозным — как
# правило»), и склейка по ним слепляла бы соседние слова.
HYPHENS = "-­‐‑"

# Невидимые пробелы: NBSP, узкий неразрывный, тонкий, волосяной, zero-width.
INVISIBLE_SPACES = "      ﻿​"

# Маркер списка. В шрифте книги это залитый квадрат, но в текстовый слой
# он попадает как одинокая `n` в начале строки — иногда с ведущим пробелом.
BULLET_RE = re.compile(r"^[ \t]*n(?=[  ])", re.M)

# Колонтитул: разрядка капсом («П е Р С о н а ж и») плюс номер страницы.
RUNNING_HEAD_RE = re.compile(
    r"^\s*(?:\d[\d\s]*)?(?:[А-ЯЁа-яё]\s){2,}[А-ЯЁа-яё]\s*(?:\d[\d\s]*)?\s*$", re.M
)

# Сноска-ссылка на перевод терминов: «1 Прим. пер.: velocitas (лат.) — …».
TRANSLATOR_NOTE_RE = re.compile(r"^\s*\d+\s*\nПрим\. пер\.:.*?$", re.M | re.S)


# Кириллица, прочитанная как Latin-1: «Ãàíãðåë» вместо «Гангрел». Так выходит,
# когда у шрифта нет таблицы ToUnicode и байты CP1251 читаются побайтово.
MOJIBAKE_RE = re.compile(r"[À-ÿ]+")
CYRILLIC_RE = re.compile(r"[а-яёА-ЯЁ]")


def fix_encoding(text: str) -> str:
    """Чинит кириллицу, выпавшую из PDF как Latin-1.

    Порча бывает и точечной — «Если â истории нет сцен», — поэтому внутри
    заведомо кириллического текста чинится прогон любой длины. Там, где
    кириллицы нет, порог выше: осмысленный латинский текст трогать нельзя.
    """
    if not text or not MOJIBAKE_RE.search(text):
        return text

    least = 1 if CYRILLIC_RE.search(text) else 3

    def repair(match):
        run = match.group(0)
        if len(run) < least:
            return run
        try:
            return run.encode("latin-1").decode("cp1251")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return run

    return MOJIBAKE_RE.sub(repair, text)


def normalize(text: str) -> str:
    """Сырой текстовый слой -> связный текст в одну строку на абзац."""
    if not text:
        return ""

    text = fix_encoding(text)

    text = TRANSLATOR_NOTE_RE.sub("", text)

    for ch in INVISIBLE_SPACES:
        text = text.replace(ch, " ")

    # Маркер списка -> ■, до склейки строк: он всегда стоит в начале строки.
    text = BULLET_RE.sub("■", text)

    text = RUNNING_HEAD_RE.sub("", text)

    # Пустая строка — граница абзаца, проставленная по границе блока PDF.
    # Прячем её, чтобы не потерять при схлопывании остальных переводов строк.
    text = re.sub(r"\n[ \t]*\n[\s]*", "\x00", text)

    # Склейка переносов: дефис + перевод строки + отступ следующей строки.
    # Именно здесь рождалось «до ма» / «под обной» при копировании мышью.
    text = re.sub(rf"[{HYPHENS}]\s*\n\s*", "", text)

    # Оставшиеся переводы строк внутри абзаца — это вёрстка по ширине колонки,
    # а не границы абзацев.
    text = re.sub(r"\s*\n\s*", " ", text)

    text = re.sub(r"\s*\x00\s*", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_paragraphs(text: str) -> list[str]:
    """Режет нормализованный текст на абзацы: по границам блоков и маркерам."""
    parts = re.split(r"\n|(?=■)", text)
    return [p.strip() for p in parts if p.strip()]


def to_html(text: str) -> str:
    """Абзацы -> HTML в том же виде, в каком его хранит компендиум."""
    return "".join(f"<p>{p}</p>" for p in split_paragraphs(text))


def strip_html(html: str) -> str:
    """HTML описания -> голый текст (для диффов и проверок)."""
    text = re.sub(r"<[^>]+>", "\n", html or "")
    for ch in INVISIBLE_SPACES:
        text = text.replace(ch, " ")
    return re.sub(r"\s+", " ", text).strip()


# Украинские буквы, которых нет в русском алфавите. Самый дешёвый
# и самый надёжный детектор непереведённого текста.
UKRAINIAN_ONLY = set("іїєґІЇЄҐ")


def has_ukrainian(text: str) -> bool:
    return bool(UKRAINIAN_ONLY & set(text or ""))
