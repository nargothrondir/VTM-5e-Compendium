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
