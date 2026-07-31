"""Смысловая проверка компендиума — то, о чём `verify` молчит.

`verify` ловит поломки: битый JSON, дубль `_id`, пропавший ассет. Это нужное,
но за всю работу оно спасло ровно один раз. Все остальные огрехи были
**тихими**: запись создавалась, схема оставалась целой, текст был русским —
а внутри лежало не то.

Проверяется пять вещей, и каждая заведена по конкретному случаю:

  * **счёт по канону** — «Бахари» не доехал, и лоршитов было 24 вместо 25;
    сравнить оказалось не с чем, потому что канон жил только в плане;
  * **выбросы по длине** — «Слова-карриды» вобрали двадцать тысяч знаков
    повествования, а «Ликвидатор» остался вовсе без текста;
  * **санитария разметки** — вложенный курсив, полразмеченного предложения
    у «Богатства», колонтитул Руководства в хвосте у Салюбри, предлог «ПО»,
    уцелевший от починки кодировки;
  * **объявленность паков** — каталог `coteries` чуть не остался вне
    манифеста, и Foundry его бы не увидел;
  * **числа в README** — он отставал на два релиза, и заметилось это
    случайно: документ правится руками, а записи прибывают скриптами.

Книги не нужны: читается только `packs/*/_source` и таблицы канона.

Известные исключения лежат в `data/audit_baseline.json` — иначе честная
короткая запись («У тебя нет ни денег, ни дома») шумела бы вечно. Падение
происходит только на **новом** выбросе.

    python tools/audit.py
    python tools/audit.py --update-baseline   # принять текущие выбросы
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import originals  # noqa: E402
from pdfkit import strip_html  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "data" / "audit_baseline.json"

# Книги, которые у проекта есть. Канон считается только по ним: остальное
# ждёт появления источника и в недостачу не записывается.
AT_HAND = {"Corebook", "Companion", "Players Guide"}

# Границы коридора длины. Ниже нижней — почти наверняка обрыв разбора,
# выше верхней — почти наверняка запись вобрала соседний раздел.
FLOOR = 40
CEILING_FACTOR = 6          # во столько раз длиннее медианы своего пака

# --- санитария разметки ---------------------------------------------------
CHECKS = (
    ("вложенный тег", re.compile(r"<(em|strong)>[^<]*<(?:em|strong)>")),
    # Опора — граница предложения внутри подписи, а не её длина: у
    # «Богатства» полужирным стало «Рабочий класс. Ты живёшь от зарплаты
    # до зарплаты:», тогда как честный заголовок «Альтернативный изъян:
    # Неестественные проявления» и без того в сорок семь знаков.
    ("в подпись попало предложение",
     re.compile(r"<strong>[^<]*\.\s+[А-ЯЁA-Z][^<]*</strong>")),
    ("подпись неправдоподобно длинная",
     re.compile(r"<strong>[^<]{81,}</strong>")),
    ("глиф без таблицы соответствий", re.compile(r"฀")),
    ("колонтитул латиницей", re.compile(r"(?:[A-Z]\s+){5,}[A-Z]")),
    ("обрывок английского колонтитула",
     re.compile(r"Chapter\s+\w+:|VAMPIRETHEMASQUERADE", re.I)),
    ("украинская буква", re.compile(r"[іїєґІЇЄҐ]")),
)

# Порча кодировки стоит отдельно: одним выражением её не поймать. Прогон
# латиницы сам по себе законен («ad hoc», «Vampire: The Masquerade»), а вот
# такой же прогон посреди русского текста — уцелевший огрызок вроде «ПО»
# в «ДОЛГИ ÏÎ КРЕДИТАМ». Одиночный знак не в счёт: это ударение из книги
# («Мавлá»), и его беречь особо оговорено в `fix_encoding`.
CYRILLIC = re.compile(r"[А-Яа-яЁё]")
MOJIBAKE = re.compile(r"(?<![A-Za-zÀ-ÿ])[À-ÿ]{2,}(?![A-Za-zÀ-ÿ])")


def find_mojibake(value):
    return bool(CYRILLIC.search(value) and MOJIBAKE.search(value))


def module_dir():
    manifests = (p for p in ROOT.iterdir() if (p / "module.json").is_file())
    for path in manifests:
        data = json.loads((path / "module.json").read_text(encoding="utf-8"))
        if data.get("id") == path.name:
            return path
    raise SystemExit("каталог модуля не найден")


def load_packs(mod):
    packs = {}
    for path in sorted(mod.glob("packs/*/_source/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        packs.setdefault(path.parent.parent.name, []).append((path, data))
    return packs


def texts(data):
    """Поля записи, несущие прозу, вместе с их именем."""
    system = data.get("system")
    if not isinstance(system, dict):
        return
    for key, value in system.items():
        if isinstance(value, str) and "<p>" in value:
            yield key, value


def at_hand(table):
    """Сколько записей канона покрыто имеющимися книгами.

    Того, чего в русском издании нет вовсе, канон не требует: иначе
    проверка была бы красной всегда.
    """
    return sum(
        1 for book, names in table.items() for name in names
        if name not in originals.NOT_IN_RU
        and (book in AT_HAND or name in originals.ALSO_IN_GUIDE))


def count_canon(packs, errors):
    """Счёт записей против канонических перечней.

    Сверяется только то, для чего канон разложен по книгам: иначе проверка
    ругалась бы на содержимое книг, которых у проекта нет.
    """
    items = {name: [d for _, d in rows
                    if not d.get("_key", "").startswith("!folders!")]
             for name, rows in packs.items()}

    def n(pack):
        return len(items.get(pack, []))

    expected = [
        ("кланы", len([d for d in items.get("clans", [])
                       if d.get("type") == "clan"]),
         len(originals.CANON_CLANS)),
        ("Страницы истории", n("loresheets"),
         at_hand(originals.CANON_LORESHEETS)),
        ("типы охотника", len([d for d in items.get(
            "blood-potency-predator-type", [])
            if d.get("type") == "predatorType"]),
         len([1 for _, book in originals.CANON_PREDATOR_TYPES
              if book in AT_HAND])),
    ]
    for label, have, want in expected:
        if have != want:
            errors.append(
                f"{label}: в паках {have}, по канону имеющихся книг {want}")

    # Виды котерий лежат в одном паке с достоинствами — считаем по папке.
    coteries = packs.get("coteries", [])
    names = {d["_id"]: d["name"] for _, d in coteries
             if d.get("_key", "").startswith("!folders!")}
    kinds = sum(1 for _, d in coteries
                if names.get(d.get("folder")) == "Виды котерий")
    want = at_hand(originals.CANON_COTERIE_TYPES)
    if kinds and kinds != want:
        errors.append(f"виды котерий: в паке {kinds}, по канону {want}")


def check_lengths(packs):
    """Выбросы по длине: обрыв разбора и вобранный соседний раздел.

    Возвращает пары «ключ, пояснение»: ключ идёт в базу известных, чтобы
    честная короткая запись не шумела вечно.
    """
    found = []
    for pack, rows in sorted(packs.items()):
        lengths, names = {}, {}
        for path, data in rows:
            if data.get("_key", "").startswith("!folders!"):
                continue
            for field, value in texts(data):
                lengths[(data["_id"], field)] = len(strip_html(value))
                names[data["_id"]] = data.get("name", path.stem)
        if not lengths:
            continue
        median = statistics.median(lengths.values())
        ceiling = max(median * CEILING_FACTOR, 2000)
        for (_id, field), size in sorted(lengths.items()):
            if FLOOR <= size <= ceiling:
                continue
            found.append((
                f"{pack}:{_id}:{field}",
                f"{pack}: {names[_id]} ({field}) — {size} знаков, "
                f"медиана пака {median:.0f}"))
    return found


def check_markup(packs, errors):
    for pack, rows in sorted(packs.items()):
        for path, data in rows:
            for field, value in texts(data):
                where = f"{pack}: {data.get('name', path.stem)}.{field}"
                for label, pattern in CHECKS:
                    if pattern.search(value):
                        errors.append(f"{where} — {label}")
                if find_mojibake(value):
                    errors.append(f"{where} — непочиненная кодировка")


README_COUNT_RE = re.compile(
    r"\*\*(\d+)\s+(?:записей|записи|entries)\s+и\s+(\d+)\s+папок\*\*"
    r"|\*\*(\d+)\s+entries\s+and\s+(\d+)\s+folders\*\*")


def check_readme(packs, errors):
    """Числа в README против паков.

    README отставал на два релиза, и заметил я это случайно: документ
    правится руками, а записи прибывают скриптами.
    """
    items = folders = 0
    for rows in packs.values():
        for _, data in rows:
            if data.get("_key", "").startswith("!folders!"):
                folders += 1
            else:
                items += 1

    for name in ("README.md", "README.en.md"):
        path = ROOT / name
        if not path.is_file():
            continue
        hit = README_COUNT_RE.search(path.read_text(encoding="utf-8"))
        if not hit:
            errors.append(f"{name}: не нашлось строки со счётом записей")
            continue
        said_items, said_folders = (int(x) for x in hit.groups() if x)
        if (said_items, said_folders) != (items, folders):
            errors.append(
                f"{name}: сказано {said_items} записей и {said_folders} папок,"
                f" а в паках {items} и {folders}")


def check_manifest(mod, packs, errors):
    manifest = json.loads((mod / "module.json").read_text(encoding="utf-8"))
    declared = {p["name"] for p in manifest.get("packs", [])}
    for name in packs:
        if name not in declared:
            errors.append(f"пак {name!r} не объявлен в манифесте — "
                          f"Foundry его не увидит")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update-baseline", action="store_true")
    args = ap.parse_args()

    mod = module_dir()
    packs = load_packs(mod)
    known = set(json.loads(BASELINE.read_text(encoding="utf-8"))["длина"]
                if BASELINE.is_file() else [])

    errors = []
    count_canon(packs, errors)
    check_markup(packs, errors)
    check_manifest(mod, packs, errors)
    check_readme(packs, errors)

    outliers = check_lengths(packs)
    if args.update_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(
            json.dumps({"длина": sorted(k for k, _ in outliers)},
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print(f"в базу принято выбросов: {len(outliers)}")
        return 0

    report = [note for key, note in outliers if key in known]
    errors += [note for key, note in outliers if key not in known]
    stale = known - {key for key, _ in outliers}
    if stale:
        print(f"в базе есть записи, которые больше не выбиваются "
              f"({len(stale)}) — уберите их: {sorted(stale)[:3]}")

    if report:
        print(f"известные выбросы ({len(report)}):")
        for line in report:
            print(f"  · {line}")

    if errors:
        print(f"\nНАЙДЕНО ({len(errors)}):")
        for line in errors[:40]:
            print(f"  x {line}")
        if len(errors) > 40:
            print(f"  … и ещё {len(errors) - 40}")
        return 1

    print("смысловая проверка пройдена")
    return 0


if __name__ == "__main__":
    sys.exit(main())
