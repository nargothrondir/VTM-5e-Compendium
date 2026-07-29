"""Проверка исходников компендиума.

Работает только с packs/*/_source и module.json — книги правил не нужны,
поэтому запускается и локально, и в CI.

Ошибки ломают сборку: это поломки, из-за которых модуль не соберётся или
загрузится битым. Незавершённость перевода ошибкой не считается и попадает
лишь в отчёт, иначе CI будет красным до последней переведённой записи.

    python tools/verify.py
    python tools/verify.py --progress-only   # только отчёт, без проверок
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pdfkit import UKRAINIAN_ONLY, strip_html  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Поля, которые подлежат переводу. По ним же считается прогресс.
TRANSLATABLE = ("name", "system.description", "system.bane")

# Пустые элементы HTML — закрывающего тега не требуют.
VOID_TAGS = {"br", "hr", "img", "input", "meta", "link", "source", "wbr"}


class TagBalance(HTMLParser):
    """Ищет незакрытые и лишние закрывающие теги."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.problems = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if not self.stack:
            self.problems.append(f"лишний закрывающий </{tag}>")
        elif self.stack[-1] != tag:
            self.problems.append(f"</{tag}> закрывает <{self.stack[-1]}>")
            self.stack.pop()
        else:
            self.stack.pop()

    def finish(self):
        for tag in reversed(self.stack):
            self.problems.append(f"не закрыт <{tag}>")
        return self.problems


def get_path(data, dotted):
    node = data
    for part in dotted.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def module_dir():
    dirs = [p for p in ROOT.iterdir()
            if p.is_dir() and p.name.startswith("vampire-the-masquerade")]
    if len(dirs) != 1:
        sys.exit(f"ожидался один каталог модуля в корне, найдено: {len(dirs)}")
    return dirs[0]


def check_html(value, where, errors):
    parser = TagBalance()
    try:
        parser.feed(value)
    except Exception as exc:                      # noqa: BLE001
        errors.append(f"{where}: HTML не разбирается ({exc})")
        return
    for problem in parser.finish():
        errors.append(f"{where}: {problem}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--progress-only", action="store_true")
    args = ap.parse_args()

    mod = module_dir()
    manifest = json.loads((mod / "module.json").read_text(encoding="utf-8"))
    mid = manifest["id"]

    errors, warnings = [], []

    # Имя каталога обязано совпадать с id: Foundry распаковывает релиз
    # в Data/modules/<id>, иначе все внутренние пути к ассетам не сойдутся.
    if mod.name != mid:
        errors.append(f"каталог модуля {mod.name!r} не совпадает с id {mid!r}")

    declared = {p["name"]: mod / p["path"] for p in manifest["packs"]}
    on_disk = {p.name for p in (mod / "packs").iterdir()
               if p.is_dir() and p.name != "assets"}

    for name in declared.keys() - on_disk:
        errors.append(f"пак {name!r} объявлен в манифесте, но каталога нет")
    for name in on_disk - declared.keys():
        warnings.append(f"каталог пака {name!r} есть, но в манифесте не объявлен")

    stats = defaultdict(Counter)

    for pack_name, pack_dir in sorted(declared.items()):
        source = pack_dir / "_source"
        if not source.is_dir():
            errors.append(f"пак {pack_name!r}: нет каталога _source")
            continue

        seen_ids = {}
        folder_ids = set()
        item_folders = []

        for path in sorted(source.glob("*.json")):
            rel = f"{pack_name}/{path.name}"
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}: битый JSON ({exc})")
                continue

            _id = data.get("_id")
            if not _id:
                errors.append(f"{rel}: нет _id")
                continue

            # Foundry ждёт, что имя файла кончается идентификатором записи:
            # по нему `fvtt package unpack` находит, куда писать обратно.
            if path.stem.rsplit("_", 1)[-1] != _id:
                errors.append(f"{rel}: имя файла не оканчивается на _id {_id!r}")

            if _id in seen_ids:
                errors.append(f"{rel}: _id {_id!r} уже занят ({seen_ids[_id]})")
            seen_ids[_id] = path.name

            key = data.get("_key", "")
            if not re.fullmatch(r"!(items|folders)!" + re.escape(_id), key):
                errors.append(f"{rel}: _key {key!r} не соответствует _id")

            if key.startswith("!folders!"):
                folder_ids.add(_id)
            elif data.get("folder"):
                item_folders.append((rel, data["folder"]))

            img = data.get("img")
            if img:
                m = re.match(r"modules/([^/]+)/(.+)", img)
                if m and m.group(1) == mid:
                    if not (mod / m.group(2)).exists():
                        errors.append(f"{rel}: нет файла ассета {img!r}")
                elif m:
                    warnings.append(f"{rel}: ассет из чужого модуля {img!r}")

            for field in TRANSLATABLE:
                value = get_path(data, field)
                if not isinstance(value, str) or not value.strip():
                    continue
                if "<" in value:
                    check_html(value, f"{rel}:{field}", errors)
                stats[pack_name]["всего"] += 1
                if UKRAINIAN_ONLY & set(strip_html(value)):
                    stats[pack_name]["не переведено"] += 1

        for rel, folder in item_folders:
            if folder not in folder_ids:
                errors.append(f"{rel}: ссылка на несуществующую папку {folder!r}")

    print(f"модуль: {mid}\n")
    print(f"{'пак':<32}{'полей':>8}{'осталось':>10}{'готово':>9}")
    total = done = 0
    for pack in sorted(stats):
        n = stats[pack]["всего"]
        left = stats[pack]["не переведено"]
        total += n
        done += n - left
        print(f"{pack:<32}{n:>8}{left:>10}{(n - left) / n:>8.0%}")
    if total:
        print(f"{'ИТОГО':<32}{total:>8}{total - done:>10}{done / total:>8.0%}")

    if args.progress_only:
        return 0

    if warnings:
        print(f"\nпредупреждения ({len(warnings)}):")
        for w in warnings[:20]:
            print(f"  ! {w}")
        if len(warnings) > 20:
            print(f"  … и ещё {len(warnings) - 20}")

    if errors:
        print(f"\nОШИБКИ ({len(errors)}):")
        for e in errors[:40]:
            print(f"  x {e}")
        if len(errors) > 40:
            print(f"  … и ещё {len(errors) - 40}")
        return 1

    print("\nпроверки пройдены")
    return 0


if __name__ == "__main__":
    sys.exit(main())
