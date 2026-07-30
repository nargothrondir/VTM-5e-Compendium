"""Книги правил -> data/book_sections.json.

Шаг детерминированный: ни одного обращения к ИИ. Разделы находятся по
начертанию шрифта, которым свёрстаны заголовки, поэтому результат
воспроизводится байт в байт и его можно смело перегенерировать.

    python tools/extract_pdf.py
    python tools/extract_pdf.py --pages 245 291   # отладка одного разворота
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).parent))
import merits  # noqa: E402
from pdfkit import (HYPHENS, INVISIBLE_SPACES, fix_encoding,  # noqa: E402
                    normalize)

ROOT = Path(__file__).resolve().parent.parent
SOURCES = Path(os.environ.get("VTM_SOURCES", ROOT / "sources"))
OUT = ROOT / "data" / "book_sections.json"

CORE = "Книга правил.pdf"
LORE = "Малая книга знаний.pdf"
GUIDE = "Руководство для игроков.pdf"

# Руководство свёрстано другой гарнитурой и другим кеглем, чем основная
# книга: там свои константы.
VARIANT_FONT = "B52"
TITLE_SIZE = (13.0, 25.0)
VARIANT_RE = re.compile(r"[А-ЯЁ][А-Яа-яёЁ  -]{2,20}:\s*[А-ЯЁа-яё][А-Яа-яёЁ ]{2,40}")
COLOPHON_RE = re.compile(r"VAMPIRE|MASQUERADE|Chapter\s+\w+:|^\d[\d ]*$")

# Роли элементов вёрстки, установленные осмотром текстового слоя STV501.
# Вся сегментация держится на них, поэтому она воспроизводима и не требует ИИ.
#
#   GillSansNova-Bold 8pt капсом   -> название силы Дисциплины
#   CormorantGaramond-Bold  14pt   -> разделитель «Уровень N»
#   CormorantGaramond-*     10pt   -> тело записи
#   CormorantGaramond-*      8pt   -> врезка («ПРИМЕР») — в запись не входит
#   CormorantGaramond-Bold  10pt   -> название достоинства/недостатка, инлайном
#   ZapfDingbats                   -> маркер списка (в текстовом слое даёт «n»)
#   GillSansNova-SemiBold/Heavy    -> колонтитул и подзаголовок врезки
POWER_HEADING_FONT = "GillSansNova-Bold"
POWER_HEADING_SIZE = (7.5, 8.5)
BODY_FONT_PREFIX = "CormorantGaramond"
BODY_SIZE = (9.0, 11.0)
LEVEL_SIZE = (13.0, 15.0)
BULLET_FONT = "ZapfDingbats"
# Название Дисциплины. Той же гарнитурой набран и титул главы, но 56-м кеглем.
DISCIPLINE_TITLE_FONT = "BodoniSevITC-Book"
DISCIPLINE_TITLE_SIZE = (20.0, 24.0)
CHAPTER_TITLE_SIZE = (34.0, 38.0)
# Уровни Силы Крови набраны тем же начертанием, что и разделители «Уровень N».
POTENCY_HEADING_FONT = "CormorantGaramond-Bold"

# Врезки и колонтитулы, которые попадают под фильтр заголовков, но записями не являются.
NOT_AN_ENTRY = {
    "ПРИМЕР", "ДРУГИЕ НАЗВАНИЯ:", "ЭФФЕКТИВНОСТЬ", "НАДЁЖНОСТЬ",
    "КОЛИЧЕСТВО УСПЕХОВ", "БАЗОВЫЙ ПОКАЗАТЕЛЬ УБЕЖИЩА",
}

LEVEL_RE = re.compile(r"^Уровень\s+([1-5])$", re.M)


def load_toc(doc):
    """Оглавление -> список (уровень, заголовок, страница с нуля)."""
    return [(lvl, re.sub(r"\s+", " ", title).strip(), page - 1)
            for lvl, title, page in doc.get_toc()]


def section_range(toc, title, doc):
    """Границы раздела [начало, конец) по его названию в оглавлении.

    Заголовок может встречаться несколько раз на разной глубине: «Дисциплины»
    — это и подраздел Силы Крови (уровень 4, стр. 221), и глава книги
    (уровень 1, стр. 245). Нужен всегда самый верхний по иерархии.
    """
    matches = [i for i, (_, name, _) in enumerate(toc) if name == title]
    if not matches:
        raise KeyError(f"раздел не найден в оглавлении: {title!r}")

    i = min(matches, key=lambda idx: toc[idx][0])
    lvl, _, page = toc[i]
    for nxt_lvl, _, nxt_page in toc[i + 1:]:
        if nxt_lvl <= lvl:
            return page, nxt_page
    return page, doc.page_count


def spans(page):
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                yield span


def page_lines(page, significant=None):
    """Строки страницы в порядке чтения.

    Разворот свёрстан в колонки, и наивный обход блоков склеивает их
    вперемешку: строка из правой колонки попадает в середину фразы из левой.
    """
    lines = []
    for bno, block in enumerate(page.get_text("dict")["blocks"]):
        for line in block.get("lines", []):
            sp = [s for s in line.get("spans", []) if s["text"].strip()]
            if sp:
                # Номер блока = граница абзаца: книга разносит «Амальгама: …»
                # и следующее за ней описание по разным блокам.
                lines.append({"spans": sp, "block": bno,
                              "x0": line["bbox"][0], "y0": line["bbox"][1]})
    if not lines:
        return []

    # Число колонок на развороте не постоянно: стр. 257 набрана в три, стр. 269
    # — в две. Поэтому колонки не ищутся по одной границе, а кластеризуются:
    # координаты начала строк группируются, и всякий разрыв шире порога
    # открывает новую колонку. Отступ внутри колонки (~16 pt) порога не берёт,
    # межколоночный интервал (140–200 pt) берёт с запасом.
    # Границы считаются только по значимым строкам. Колонцифра и колонтитул
    # стоят на полях и в одноколоночной полосе давали ложную границу, разводя
    # по разным «колонкам» соседние абзацы.
    width = page.rect.width
    basis = [l for l in lines if significant is None or significant(l)] or lines
    xs = sorted({round(l["x0"]) for l in basis})
    bounds = [b for a, b in zip(xs, xs[1:]) if b - a > width * 0.10]

    # Округление обязано быть тем же, что и при расчёте границ: иначе строки,
    # отличающиеся на доли пункта, оказываются по разные стороны границы.
    for l in lines:
        l["col"] = sum(1 for b in bounds if round(l["x0"]) >= b)
    lines.sort(key=lambda l: (l["col"], round(l["y0"], 1)))
    return lines


def line_text(line):
    """Текст строки с восстановленным маркером списка.

    Неразрывные пробелы схлопываются сразу: в теле их всё равно уберёт
    normalize, а в заголовке «Сила Крови 6 и выше» такой пробел ломает
    сверку с таблицей соответствий.
    """
    text = "".join(s["text"] for s in line["spans"])
    for ch in INVISIBLE_SPACES:
        text = text.replace(ch, " ")
    if line["spans"][0]["font"] == BULLET_FONT:
        # Символ маркера из ZapfDingbats в текстовом слое выглядит как «n».
        text = text[1:] if text[:1] == "n" else text
        text = "■ " + text.lstrip()
    return text


def classify(line):
    """Роль строки: heading | level | body | skip."""
    sp = line["spans"]
    text = "".join(s["text"] for s in sp).strip()
    if not text:
        return "skip"

    significant = [s for s in sp if s["font"] != BULLET_FONT]
    if not significant:
        return "skip"

    if all(s["font"] == DISCIPLINE_TITLE_FONT
           and DISCIPLINE_TITLE_SIZE[0] < s["size"] < DISCIPLINE_TITLE_SIZE[1]
           for s in significant):
        return "discipline"

    if all(s["font"] == POWER_HEADING_FONT
           and POWER_HEADING_SIZE[0] < s["size"] < POWER_HEADING_SIZE[1]
           for s in significant):
        # Отсекает подпись под эпиграфом («АББАТ АВГУСТИН КАЛЬМЕ,»):
        # название силы никогда не кончается запятой.
        ok = (len(text) > 3 and text == text.upper()
              and text not in NOT_AN_ENTRY
              and not text.endswith(",")
              and re.match(r"^[А-ЯЁ][А-ЯЁ\s\-«», ]+$", text))
        return "heading" if ok else "skip"

    if LEVEL_RE.match(text) and any(LEVEL_SIZE[0] < s["size"] < LEVEL_SIZE[1]
                                    for s in significant):
        return "level"

    # Тело записи — только основной кегль. Врезки набраны той же гарнитурой,
    # но восьмым кеглем, а колонтитулы — вообще другой.
    if any(s["font"].startswith(BODY_FONT_PREFIX)
           and BODY_SIZE[0] < s["size"] < BODY_SIZE[1] for s in significant):
        return "body"

    return "skip"


def add_body_line(current, line, text):
    """Дописывает строку в тело записи, отслеживая границы абзацев.

    Смена блока PDF обычно значит границу абзаца, но не всегда: блок рвётся
    и посреди фразы. Настоящую границу подтверждает завершённость предыдущей
    строки — не висящий перенос и не оборванное на полуслове предложение.
    """
    prev = current["lines"][-1] if current["lines"] else ""
    finished = prev.endswith((".", "!", "?", ":", ";")) and not prev.endswith(tuple(HYPHENS))
    if prev and line["block"] != current["block"] and finished:
        current["lines"].append("")
    current["lines"].append(text)
    current["block"] = line["block"]


def title_pages(doc, title, size_range, start, end):
    """Границы раздела, титул которого набран крупным кеглем.

    Нужно там, где раздела нет в оглавлении: у «Стиля охоты», части главы
    о персонажах, отдельной записи в оглавлении нет.
    """
    found = None
    for pno in range(start, end):
        for line in page_lines(doc[pno]):
            sp = [s for s in line["spans"] if s["text"].strip()]
            if not sp or not all(s["font"] == DISCIPLINE_TITLE_FONT
                                 and size_range[0] < s["size"] < size_range[1]
                                 for s in sp):
                continue
            text = "".join(s["text"] for s in sp).strip()
            if found is None and text == title:
                found = pno
            elif found is not None and text != title:
                return found, pno + 1
    if found is None:
        raise KeyError(f"титул не найден: {title!r}")
    return found, end


def is_chapter_title(line):
    """Титул главы — самый крупный кегль на полосе."""
    sp = [s for s in line["spans"] if s["text"].strip()]
    return bool(sp) and all(s["font"] == DISCIPLINE_TITLE_FONT
                            and CHAPTER_TITLE_SIZE[0] < s["size"] < CHAPTER_TITLE_SIZE[1]
                            for s in sp)


def extract_flat(doc, pages, book, kind, is_heading, stop=None):
    """Записи раздела: заголовок по предикату, тело — до следующего заголовка.

    Диапазон страниц захватывает и полосу, на которой начинается следующая
    глава: последняя запись раздела дотягивается до неё. Поэтому нужен `stop` —
    иначе титул новой главы будет принят за очередную запись.
    """
    sections, current = [], None

    def flush():
        nonlocal current
        if current:
            current.pop("block", None)
            current["text"] = normalize(chr(10).join(current.pop("lines")))
            sections.append(current)
            current = None

    for pno in range(*pages):
        for line in page_lines(doc[pno], lambda l: classify(l) != "skip"):
            text = line_text(line).strip()
            if stop and stop(line, text):
                flush()
                return sections
            if is_heading(line, text):
                flush()
                current = {"kind": kind, "book": book, "name": text,
                           "page": pno + 1, "lines": [], "block": None}
            elif classify(line) == "body" and current:
                add_body_line(current, line, text)

    flush()
    return sections


def extract_merits(doc, pages, book):
    """Записи раздела достоинств и недостатков."""
    sections, current, cat = [], None, None

    def flush():
        nonlocal current
        if current:
            current.pop("block", None)
            current["text"] = normalize(chr(10).join(current.pop("lines")))
            sections.append(current)
            current = None

    for pno in range(*pages):
        for line in page_lines(doc[pno], lambda l: classify(l) != "skip"):
            # Диапазон захватывает полосу, где начинается следующая глава:
            # последняя запись раздела дотягивается до неё. Без обрыва
            # «Эксклюзивное расположение» вбирало в себя «Создание котерии».
            if is_chapter_title(line) and line_text(line).strip() != "Преимущества":
                flush()
                return sections

            heading = merits.category(line)
            if heading:
                flush()
                cat = heading
                # Вводный абзац категории — основной текст для сводных записей
                # компендиума: «Статус» там одна запись со всеми ступенями,
                # тогда как книга разносит ступени по отдельным записям.
                intro = line_text(line).strip()
                if intro.startswith(heading):
                    intro = intro[len(heading):].lstrip(". ")
                current = {"kind": "merit_category", "book": book, "name": cat,
                           "category": cat, "page": pno + 1,
                           "lines": [intro] if intro else [],
                           "block": line["block"]}
                continue
            if classify(line) != "body":
                continue

            start = merits.entry_start(line, BULLET_FONT, INVISIBLE_SPACES)
            text = line_text(line).strip()
            if start:
                flush()
                current = {"kind": "merit_entry", "book": book,
                           "name": start["name"], "rating": start["rating"],
                           "flaw": start["flaw"], "category": cat,
                           "page": pno + 1, "lines": [start["rest"]],
                           "block": line["block"]}
            elif current:
                add_body_line(current, line, text)

    flush()
    return sections


CLAN_SUBTITLE_FONT = "BodoniSevITC-Book"
CLAN_SUBTITLE_SIZE = (20.0, 24.0)
# Основная книга набирает названия Дисциплин полужирным и отделяет точкой,
# Малая книга знаний — сверхжирным и двоеточием. Признак один: капс в начале.
CLAN_DISCIPLINE_FONTS = {"GillSansNova-Bold", "GillSansNova-Heavy"}
CLAN_DISCIPLINE_SIZE = (7.0, 8.0)
# Буквица: первая литера вводного абзаца набрана в семь раз крупнее строки
# и обычным фильтром тела отсекается — без неё выходит «лан, почти
# истреблённый» вместо «Клан, почти истреблённый».
CLAN_DROPCAP_SIZE = 40.0


def extract_clans(doc, toc, book, names):
    """Кланы: вводное описание, список Дисциплин и раздел «Изъян».

    Описание — это текст до первого подзаголовка полосы; дальше идут
    «Какими бывают …?», «Дисциплины» и «Изъян», каждый со своим титулом
    в 22 пункта.
    """
    sections = []
    for clan in names:
        first, last = section_range(toc, clan, doc)
        subtitle, lead, bane, disciplines = None, [], [], []
        dropcap = ""

        for pno in range(first, last):
            for line in page_lines(doc[pno], lambda l: classify(l) != "skip"):
                sp = [s for s in line["spans"] if s["text"].strip()]
                text = line_text(line).strip()

                if (not dropcap and subtitle is None and len(text) == 1
                        and sp[0]["size"] > CLAN_DROPCAP_SIZE):
                    dropcap = text
                    continue

                if all(s["font"] == CLAN_SUBTITLE_FONT
                       and CLAN_SUBTITLE_SIZE[0] < s["size"] < CLAN_SUBTITLE_SIZE[1]
                       for s in sp):
                    subtitle = text
                    continue

                # Название Дисциплины набрано капсом и заканчивается точкой:
                # «ВЕЛИЧИЕ. Бруха применяют эту Дисциплину, когда…»
                if (sp[0]["font"] in CLAN_DISCIPLINE_FONTS
                        and CLAN_DISCIPLINE_SIZE[0] < sp[0]["size"] < CLAN_DISCIPLINE_SIZE[1]):
                    head = re.match(r"^([А-ЯЁ][А-ЯЁ ]+)[.:]", text)
                    if head:
                        disciplines.append(head.group(1).strip().capitalize())
                    continue

                if classify(line) != "body":
                    continue
                if subtitle is None:
                    lead.append(text)
                elif subtitle == "Изъян":
                    bane.append(text)

        sections.append({
            "kind": "clan_entry", "book": book, "name": clan,
            "page": first + 1,
            "disciplines": list(dict.fromkeys(disciplines)),
            "text": dropcap + normalize(chr(10).join(lead)),
            "bane": normalize(chr(10).join(bane)),
        })
    return sections


def extract_bane_variants(doc, book):
    """Альтернативные проклятья кланов из Руководства для игроков.

    Раздел свёрстан своим шрифтом B52, и кегль заголовка гуляет от 14 до 20
    пунктов — привязываться к размеру нельзя, опознаём по гарнитуре и по
    формату строки «Клан: Название варианта».
    """
    def titles(page, least, most):
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for s in line.get("spans", []):
                    if (s["font"] == VARIANT_FONT and least < s["size"] < most
                            and s["text"].strip()):
                        yield fix_encoding(s["text"]).strip()

    # Начало ищется по титулу главы, а не по словам: то же название стоит
    # в оглавлении, и поиск по тексту приводил на страницу с содержанием.
    start = next((pno for pno in range(doc.page_count)
                  if any("Клановые" in x for x in titles(doc[pno], 40, 80))), None)
    if start is None:
        return []

    # Двоеточие в заголовке набрано другой гарнитурой, поэтому границу
    # раздела задаёт само наличие заголовочных строк, а не их текст.
    end = start + 1
    while (end < doc.page_count and end - start < 12
           and any(titles(doc[end], *TITLE_SIZE))):
        end += 1

    sections, current, in_title = [], None, False

    def flush():
        nonlocal current
        if current:
            current["text"] = normalize(chr(10).join(current.pop("lines")))
            clan, _, title = current["name"].partition(":")
            current["clan"], current["variant"] = clan.strip(), title.strip()
            sections.append(current)
            current = None

    for pno in range(start, end):
        for b in doc[pno].get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                sp = [s for s in line.get("spans", []) if s["text"].strip()]
                if not sp:
                    continue
                text = fix_encoding("".join(s["text"] for s in sp)).strip()

                # Заголовок опознаётся по гарнитуре и кеглю: двоеточие в нём
                # набрано другим шрифтом, а кегль гуляет от 14 до 20 пунктов.
                title = (sp[0]["font"] == VARIANT_FONT
                         and TITLE_SIZE[0] < sp[0]["size"] < TITLE_SIZE[1])

                if title and ":" in text:
                    flush()
                    current = {"kind": "bane_variant", "book": book,
                               "name": text, "page": pno + 1, "lines": []}
                    in_title = True
                elif title and in_title and current:
                    current["name"] += " " + text      # заголовок в две строки
                elif current and not COLOPHON_RE.search(text):
                    in_title = False
                    current["lines"].append(text)

    flush()
    return sections


def extract_powers(doc, toc, book):
    """Силы Дисциплин: заголовок капсом, тело — до следующего заголовка.

    Сегментация идёт по позиции строки в потоке чтения, а не по странице:
    на одной странице умещается до пяти сил.
    """
    start, end = section_range(toc, "Дисциплины", doc)

    # Название Дисциплины из оглавления — запасной вариант: титул на полосе
    # набран крупным кеглем и ловится по начертанию (роль "discipline"), но
    # если его почему-то нет, страница задаёт Дисциплину хотя бы приблизительно.
    discipline_at = {page: name for lvl, name, page in toc
                     if lvl == 2 and start <= page < end}

    sections, current = [], None
    discipline, level, prev_heading = None, None, False

    def flush():
        nonlocal current
        if current:
            current.pop("block", None)
            current["text"] = normalize("\n".join(current.pop("lines")))
            sections.append(current)
            current = None

    for pno in range(start, end):
        page = doc[pno]
        # Дисциплина меняется не на границе страницы: на стр. 267 в левой
        # колонке ещё идёт последняя сила Мощи, а в правой уже начинается
        # Стремительность. Поэтому титул ловится по месту в потоке, ниже.
        if discipline is None and pno in discipline_at:
            discipline = discipline_at[pno]

        for line in page_lines(page, lambda l: classify(l) != "skip"):
            role = classify(line)
            if role == "skip":
                continue

            text = line_text(line).strip()

            if role == "discipline":
                flush()
                discipline = text
                # Первая группа сил после титула Дисциплины — всегда первый
                # уровень; отдельного маркера «Уровень 1» книга там не ставит.
                level = 1
                prev_heading = False
            elif role == "level":
                level = int(LEVEL_RE.match(text).group(1))
                prev_heading = False
            elif role == "heading":
                if prev_heading and current:
                    current["name"] += " " + text   # длинный заголовок в две строки
                else:
                    flush()
                    current = {"kind": "power", "book": book, "name": text,
                               "page": pno + 1, "discipline": discipline,
                               "level": level, "lines": [], "block": None}
                prev_heading = True
            else:
                prev_heading = False
                if current:
                    add_body_line(current, line, text)

    flush()
    return sections


def extract_toc_section(doc, toc, title, book, kind):
    """Раздел целиком, одним куском (кланы, типы охотника и т. п.)."""
    start, end = section_range(toc, title, doc)
    text = " ".join(normalize(doc[p].get_text("text")) for p in range(start, end))
    return [{"kind": kind, "book": book, "name": title,
             "page": start + 1, "pages": [start + 1, end], "text": text}]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", nargs=2, type=int, metavar=("FROM", "TO"),
                    help="выгрузить сырой и нормализованный текст диапазона и выйти")
    args = ap.parse_args()

    core_path = SOURCES / CORE
    if not core_path.exists():
        sys.exit(f"нет файла: {core_path}\nположи книги в sources/ или задай VTM_SOURCES")

    core = fitz.open(core_path)

    if args.pages:
        for pno in range(args.pages[0] - 1, args.pages[1]):
            print(f"\n{'=' * 70}\nстр. {pno + 1}\n{'=' * 70}")
            print(normalize(core[pno].get_text("text")))
        return

    toc = load_toc(core)
    sections = []
    sections += extract_powers(core, toc, CORE)
    merit_pages = title_pages(core, "Преимущества", CHAPTER_TITLE_SIZE, 175, 215)
    sections += extract_merits(core, merit_pages, CORE)
    for clan in ("Бруха", "Вентру", "Гангрел", "Малкавиане", "Носферату",
                 "Тореадор", "Тремер", "Каитифы", "Слабая кровь"):
        sections += extract_toc_section(core, toc, clan, CORE, "clan")
    # Типы охотника. Раздела нет в оглавлении, поэтому границы берутся по титулу.
    hunt = title_pages(core, "Стиль охоты", CHAPTER_TITLE_SIZE, 150, 200)
    sections += extract_flat(
        core, hunt, CORE, "predator_type",
        lambda line, text: classify(line) == "discipline" and text != "Стиль охоты",
        stop=lambda line, text: is_chapter_title(line) and text != "Стиль охоты")

    # Уровни Силы Крови: заголовки набраны 14-м кеглем внутри своего подраздела.
    potency = title_pages(core, "Сила Крови", DISCIPLINE_TITLE_SIZE, 210, 225)
    sections += extract_flat(
        core, potency, CORE, "blood_potency",
        lambda line, text: text.startswith("Сила Крови ") and all(
            s["font"] == POTENCY_HEADING_FONT and LEVEL_SIZE[0] < s["size"] < LEVEL_SIZE[1]
            for s in line["spans"] if s["text"].strip()))

    guide_path = SOURCES / GUIDE
    if guide_path.exists():
        sections += extract_bane_variants(fitz.open(guide_path), GUIDE)

    lore_path = SOURCES / LORE
    if lore_path.exists():
        lore = fitz.open(lore_path)
        lore_toc = load_toc(lore)
        for clan in ("Равнос", "Салюбри", "Цимисхи"):
            sections += extract_toc_section(lore, lore_toc, clan, LORE, "clan")
        sections += extract_toc_section(lore, lore_toc, "Силы Дисциплин", LORE, "power_extra")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(sections, ensure_ascii=False, indent=2), encoding="utf-8")

    by_kind = {}
    for s in sections:
        by_kind[s["kind"]] = by_kind.get(s["kind"], 0) + 1
    print(f"записано {len(sections)} разделов -> {OUT.relative_to(ROOT)}")
    for kind, n in sorted(by_kind.items()):
        print(f"  {kind:<15} {n}")


if __name__ == "__main__":
    main()
