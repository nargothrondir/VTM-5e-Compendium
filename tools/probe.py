"""Разведка вёрстки книги: что за гарнитуры, где заголовки, как идут колонки.

Извлечение здесь держится на начертании, а не на тексте, поэтому всякая
новая книга начинается с одного и того же вопроса: каким шрифтом и кеглем
свёрстан заголовок записи, каким — тело, и не врёт ли порядок чтения.

Скрипт отвечает на него сводкой, а не дампом: полосы книги дают сотни строк
координат, из которых нужны единицы.

    python tools/probe.py "Книга правил" --pages 384 409
    python tools/probe.py "Cults" --pages 100 130 --fonts
    python tools/probe.py "Cults" --pages 112 --lines      # одна полоса целиком
    python tools/probe.py --list
"""

import argparse
import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_pdf import SOURCES, page_lines  # noqa: E402
from pdfkit import fix_encoding  # noqa: E402

# Строки, которые не несут содержимого: колонцифра и колонтитул вразрядку.
NOISE = re.compile(r"^[\d\s]+$|^(?:[A-Za-zА-Яа-яЁё]\s){3,}[A-Za-zА-Яа-яЁё]\s*$")


def find_book(needle):
    books = sorted(SOURCES.glob("*.pdf"))
    if not needle:
        return books
    hits = [b for b in books if needle.lower() in b.name.lower()]
    if not hits:
        sys.exit(f"не нашлось книги по «{needle}». Есть: "
                 + ", ".join(b.name for b in books))
    return hits[:1]


def line_rows(doc, first, last):
    for pno in range(first, min(last, doc.page_count)):
        for line in page_lines(doc[pno]):
            spans = [s for s in line.get("spans", []) if s["text"].strip()]
            if not spans:
                continue
            text = fix_encoding("".join(s["text"] for s in spans)).strip()
            yield pno, line, spans, text


def show_fonts(doc, first, last):
    """Какие начертания и кегли встречаются и сколько строк каждым набрано."""
    tally = collections.Counter()
    sample = {}
    for _, _, spans, text in line_rows(doc, first, last):
        key = (spans[0]["font"], round(spans[0]["size"], 1))
        tally[key] += 1
        if key not in sample and not NOISE.match(text):
            sample[key] = text[:56]
    print(f"{'гарнитура':<28}{'кегль':>6}{'строк':>7}  пример")
    for (font, size), count in sorted(tally.items(),
                                      key=lambda kv: (-kv[1], kv[0])):
        print(f"  {font:<26}{size:>6}{count:>7}  {sample.get((font, size), '')}")


def show_headings(doc, first, last, floor):
    """Кандидаты в заголовки: всё, что крупнее тела, без колонцифр."""
    body = collections.Counter()
    for _, _, spans, _ in line_rows(doc, first, last):
        body[round(spans[0]["size"], 1)] += 1
    common = body.most_common(1)[0][0] if body else 10.0
    cut = floor if floor else common + 1.5
    print(f"тело набрано {common} кеглем; крупнее {cut}:")
    for pno, line, spans, text in line_rows(doc, first, last):
        size = round(spans[0]["size"], 1)
        if size >= cut and not NOISE.match(text):
            print(f"  стр.{pno + 1:<5}[{spans[0]['font']:<24}{size:>6}] "
                  f"{text[:60]}")


def show_columns(doc, first, last):
    """Врёт ли порядок чтения.

    page_lines разводит колонки по разрыву абсцисс, но на полосах, где
    перечень идёт вперемежку с текстом во всю ширину, разрыва нет — и всё
    сваливается в одну колонку. Тогда обход ставит записи не в том порядке,
    и описания уходят соседям. Признак — колонка одна, а абсциссы двух-трёх
    разных семейств.
    """
    for pno in range(first, min(last, doc.page_count)):
        cols, buckets = set(), collections.Counter()
        for line in page_lines(doc[pno]):
            if not [s for s in line.get("spans", []) if s["text"].strip()]:
                continue
            cols.add(line.get("col"))
            buckets[int(line["x0"] // 190)] += 1
        if len(cols) < len(buckets):
            print(f"  стр.{pno + 1:<5} колонок опознано {len(cols)}, "
                  f"а по абсциссам их {len(buckets)} {dict(sorted(buckets.items()))}"
                  f"  <-- порядок чтения ненадёжен")


def show_lines(doc, first, last):
    """Полоса целиком, отсортированная по колонке и вертикали."""
    for pno in range(first, min(last, doc.page_count)):
        print(f"===== стр. {pno + 1}")
        rows = sorted(line_rows(doc, pno, pno + 1),
                      key=lambda r: (int(r[1]["x0"] // 190),
                                     round(r[1]["y0"], 1)))
        for _, line, spans, text in rows:
            print(f"  к{int(line['x0'] // 190)} x={line['x0']:>6.1f} "
                  f"y={line['y0']:>6.1f} [{spans[0]['font']:<22}"
                  f"{spans[0]['size']:>5.1f}] {text[:58]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("book", nargs="?", help="часть имени файла книги")
    ap.add_argument("--pages", nargs="+", type=int, metavar="N",
                    help="страница или диапазон, по книге (с единицы)")
    ap.add_argument("--fonts", action="store_true", help="перепись начертаний")
    ap.add_argument("--headings", action="store_true", help="кандидаты в заголовки")
    ap.add_argument("--columns", action="store_true", help="проверка порядка чтения")
    ap.add_argument("--lines", action="store_true", help="полоса целиком")
    ap.add_argument("--floor", type=float, help="свой порог кегля для заголовков")
    ap.add_argument("--list", action="store_true", help="какие книги есть")
    ap.add_argument("--toc", action="store_true", help="оглавление")
    args = ap.parse_args()

    import fitz

    if args.list or not args.book:
        for book in find_book(None):
            doc = fitz.open(book)
            print(f"  {book.name}  — {doc.page_count} стр.")
        return 0

    path = find_book(args.book)[0]
    doc = fitz.open(path)
    print(f"# {path.name}, {doc.page_count} стр.\n")

    if args.toc:
        for lvl, title, page in doc.get_toc():
            print(f"  {'  ' * (lvl - 1)}[{lvl}] стр.{page:<5} {title}")
        return 0

    pages = args.pages or [1, doc.page_count + 1]
    first = pages[0] - 1
    last = (pages[1] if len(pages) > 1 else pages[0]) if args.pages else pages[1]

    if not any((args.fonts, args.headings, args.columns, args.lines)):
        args.fonts = args.headings = args.columns = True

    if args.fonts:
        print("## начертания\n")
        show_fonts(doc, first, last)
        print()
    if args.headings:
        print("## заголовки\n")
        show_headings(doc, first, last, args.floor)
        print()
    if args.columns:
        print("## порядок чтения\n")
        show_columns(doc, first, last)
        print()
    if args.lines:
        show_lines(doc, first, last)
    return 0


if __name__ == "__main__":
    sys.exit(main())
