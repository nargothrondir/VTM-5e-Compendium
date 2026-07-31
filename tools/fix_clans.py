"""Правка пака кланов и добавление альтернативных проклятий.

Описания кланов — редакторская выборка из книги, а не механически выводимый
кусок: где-то взят вводный разворот, где-то раздел «Какими бывают…». Поэтому
пак не пересобирается целиком, как остальные, а правится точечно — иначе
отбор был бы затёрт.

Скрипт идемпотентен: повторный запуск ничего не меняет.

    python tools/fix_clans.py --dry-run
    python tools/fix_clans.py
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_pdf import GUIDE, SOURCES, extract_bane_variants  # noqa: E402
from pdfkit import LATIN_RUNNING_HEAD_RE, to_html  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Опечатки и разнобой, найденные сверкой с книгой. Слева — как в компендиуме,
# справа — как в официальном переводе.
TEXT_FIXES = [
    ("любойДисциплине", "любой Дисциплине"),          # склейка при копировании
    ("Ясновиденье", "Ясновидение"),                   # у Тремера уже верно
    ("Кровавое Чародейство", "Кровавое чародейство"),
    ("Алхимия Слабокровны", "Алхимия слабокровных"),  # оборвано на середине
]

# То же для вкладки изъяна. «Клановые Проклятья Альтернативы» — колонтитул
# раздела, а не текст; «изза» — потерянный дефис на переносе.
BANE_HEADING_RE = re.compile(
    r"<p>(?:<strong>)?\s*(Изъян:|Альтернативный изъян:)\s*([^<(]+?)\s*"
    r"(?:</strong>)?\s*(\([^<)]*\))?\s*</p>")

BANE_FIXES = [
    ("Клановые Проклятья Альтернативы", ""),
    ("изза", "из-за"),
]

# Описание Бруха оборвалось при копировании на первом же абзаце.
BRUJAH_HEAD = "Бруха всегда предпочитали тех"
BRUJAH_TAIL = "которые его породили."

# Клан в Руководстве для игроков -> имя записи в компендиуме.
# В источнике две опечатки: «Малкваиан» и «Тремере». «Министрий» — не
# опечатка, а другой вариант перевода того же клана.
#
# Вариантов в книге четырнадцать, и все четырнадцать здесь: у каитифов и
# слабокровных кланового проклятия нет, поэтому им и вариант не полагается.
VARIANT_CLANS = {
    "Бану Хаким": "Бану Хаким",
    "Бруха": "Бруха",
    "Вентру": "Вентру",
    "Гангрел": "Гангрел",
    "Геката": "Геката",
    "Ласомбра": "Ласомбра",
    "Малкваиан": "Малкавиан",
    "Министрий": "Министерство",
    "Носферату": "Носферату",
    "Равнос": "Равнос",
    "Салюбри": "Салюбри",
    "Тореадор": "Тореадор",
    "Тремере": "Тремер",
    "Цимисхи": "Цимисхи",
}

# Заголовки внутри вкладки. Слово одно на оба: вкладка в Foundry называется
# «Клановый изъян», и книга ставит над этим текстом «Изъян». «Проклятие»
# осталось от первой редакции скрипта и разводило два соседних абзаца одной
# вкладки по разной терминологии.
VARIANT_MARK = "Альтернативный изъян"
OLD_VARIANT_MARK = "Альтернативное проклятие"
BANE_MARK = "Изъян:"
COMPULSION_MARK = "Одержимость:"

# Русские книги проклятия не называют — ни основная, ни Малая книга знаний
# не дают им заголовков, хотя в оригинале имя есть у каждого. Пробел
# восполнен переводом канонических названий в словаре самой книги: там, где
# она уже подобрала слово, взято её («болезненный Поцелуй», «отвратительные»,
# «жаждут красоты», «привязанность»).
BANE_NAMES = {
    "Бруха": "Буйный нрав",                  # Violent Temper
    "Вентру": "Изысканный вкус",             # Rarefied Tastes
    "Гангрел": "Звериные черты",             # Bestial Features
    "Малкавиан": "Расколотое восприятие",    # Fractured Perspective
    "Носферату": "Отвратительность",         # Repulsiveness
    "Тореадор": "Жажда красоты",             # Aesthetic Fixation
    "Тремер": "Ущербная Кровь",              # Deficient Blood
    "Бану Хаким": "Кровавая зависимость",    # Blood Addiction
    "Геката": "Болезненный Поцелуй",         # Painful Kiss
    "Ласомбра": "Искажённое отражение",      # Distorted Image
    "Министерство": "Неприятие света",       # Abhors the Light
    "Равнос": "Обречённость",                # Doomed
    "Салюбри": "Гонимые",                    # Hunted
    "Цимисхи": "Привязанность",              # Grounded
    "Каитиф": "Изгой",                       # Outcast
}

# То, что Руководство подписывает «Клановый изъян: X», — не проклятие, а
# Одержимость: текст под этим заголовком описывает принуждение на одну сцену.
# Официальное название термина — «Одержимость» (Книга правил, стр. 210).
GUIDE_COMPULSIONS = {
    "Бану Хаким": "приговор",
    "Геката": "болезненность",
    "Ласомбра": "безжалостность",
    "Министерство": "преступление",
    "Равнос": "искушение судьбы",
    "Салюбри": "аффективное сопереживание",
    "Цимисхи": "алчность",
}


def is_module_dir(path):
    """Каталог модуля — тот, чей module.json объявляет id, равный его имени.

    По имени опознавать нельзя: рядом остаётся каталог прежней раскладки.
    По одному лишь наличию манифеста — тоже: он есть и в dist/ после сборки
    релиза. Совпадение id с именем каталога — это ровно то, чего требует
    Foundry, и потому надёжный признак.
    """
    manifest = path / "module.json"
    if not path.is_dir() or not manifest.is_file():
        return False
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("id") == path.name
    except (json.JSONDecodeError, OSError):
        return False


def module_dir():
    return next(p for p in ROOT.iterdir() if is_module_dir(p))


def brujah_full_text():
    """Полный абзац про бруха из основной книги."""
    import fitz
    from extract_pdf import CORE
    from pdfkit import normalize

    doc = fitz.open(SOURCES / CORE)
    text = normalize(" ".join(doc[p].get_text("text") for p in range(66, 70)))
    start = text.find(BRUJAH_HEAD)
    end = text.find(BRUJAH_TAIL)
    if start < 0 or end < 0:
        sys.exit("не найден текст бруха в книге")
    return text[start:end + len(BRUJAH_TAIL)]


def unwrap_headings(html):
    """Тело описания переносится из <h5> в <p>.

    В <h5> оправдана только строка Дисциплин: остальное — обычный текст,
    и заголовочная разметка показывала его в Foundry крупным жирным шрифтом.
    """
    blocks = re.findall(r"<(h5|p)>(.*?)</\1>", html, flags=re.S)
    out = []
    for i, (_, inner) in enumerate(blocks):
        # Заголовком остаётся только сама строка Дисциплин. У каитифов на её
        # месте стоит пояснение на несколько предложений — это уже текст.
        head = i == 0 and inner.startswith("Дисциплины:") and len(inner) < 120
        tag = "h5" if head else "p"
        out.append(f"<{tag}>{inner}</{tag}>")
    return "".join(out)


def main():
    import fitz
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    variants = {}
    for section in extract_bane_variants(fitz.open(SOURCES / GUIDE), GUIDE):
        name = VARIANT_CLANS.get(section["clan"])
        if name:
            variants[name] = section

    source = module_dir() / "packs" / "clans" / "_source"
    brujah = brujah_full_text()
    changed = []

    for path in sorted(source.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        system = data["system"]
        before = json.dumps(system, ensure_ascii=False)
        notes = []

        desc = system.get("description") or ""

        if data["name"] == "Бруха" and BRUJAH_TAIL not in desc:
            desc = desc.replace(
                desc[desc.find(BRUJAH_HEAD):].rstrip("</h5>").rstrip(),
                brujah)
            notes.append("описание восстановлено целиком")

        for wrong, right in TEXT_FIXES:
            if wrong in desc:
                desc = desc.replace(wrong, right)
                notes.append(f"{wrong!r} -> {right!r}")

        fixed = unwrap_headings(desc)
        if fixed != desc:
            notes.append("тело описания переведено из <h5> в <p>")
        system["description"] = fixed

        bane = system.get("bane") or ""

        # Подпись «Клановый изъян: X» из Руководства сюда попала по ошибке:
        # это Одержимость, а не проклятие. Убираем — название проклятия ниже.
        wrong = re.search(r"<p>■ Клановый изъян:[^<]*</p>", bane)
        if wrong:
            bane = bane.replace(wrong.group(0), "")
            notes.append("убрана подпись Одержимости, выданная за изъян")

        # Заголовки изъяна приводятся к одному виду здесь, где они и
        # заводятся: полужирный на «Изъян: Название», источник — прямым.
        # Проход разметки о них не знает и снимал с них полужирный.
        fixed_heads = BANE_HEADING_RE.sub(
            lambda m: f"<p><strong>{m.group(1)} {m.group(2)}</strong>"
                      + (f" {m.group(3)}" if m.group(3) else "") + "</p>",
            bane)
        if fixed_heads != bane:
            bane = fixed_heads
            notes.append("восстановлен полужирный на заголовке изъяна")

        # Хвост варианта у Бруха и Салюбри забрал колонтитулы Руководства:
        # латинскую «шапку» и название раздела. Оба стоят вплотную к тексту,
        # без пустой строки, поэтому сегментация их не отсекла.
        cleaned = LATIN_RUNNING_HEAD_RE.sub("", bane)
        for junk, right in BANE_FIXES:
            cleaned = cleaned.replace(junk, right)
        cleaned = re.sub(r"\s+(</p>)", r"\1", cleaned)
        if cleaned != bane:
            bane = cleaned
            notes.append("убран колонтитул из хвоста варианта")

        # Прежний заголовок варианта переименовывается, а не дописывается
        # заново: иначе проверка ниже не нашла бы его и завела второй блок.
        if OLD_VARIANT_MARK in bane:
            bane = bane.replace(OLD_VARIANT_MARK, VARIANT_MARK)
            notes.append(f"заголовок варианта -> «{VARIANT_MARK}»")

        name = BANE_NAMES.get(data["name"])
        if name and bane and BANE_MARK not in bane:
            head = f"<p><strong>{BANE_MARK} {name}</strong></p>"
            note = re.match(r"<p><em>Источник:[^<]*</em></p>", bane)
            if note:                       # подпись источника остаётся первой
                bane = note.group(0) + head + bane[note.end():]
            else:
                bane = head + bane
            notes.append(f"название изъяна: «{name}»")

        system["bane"] = bane

        variant = variants.get(data["name"])
        if variant and VARIANT_MARK not in (system.get("bane") or ""):
            body = to_html(variant["text"])
            system["bane"] = (system.get("bane") or "") + \
                f"<p><strong>{VARIANT_MARK}: {variant['variant']}</strong> " \
                f"(Руководство для игроков)</p>" + body
            notes.append(f"добавлен альтернативный изъян «{variant['variant']}»")

        if json.dumps(system, ensure_ascii=False) != before:
            changed.append((data["name"], notes))
            if not args.dry_run:
                text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
                path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

    verb = "изменилось бы" if args.dry_run else "изменено"
    print(f"{verb} записей: {len(changed)}")
    for name, notes in changed:
        print(f"  {name}")
        for n in notes:
            print(f"      - {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
