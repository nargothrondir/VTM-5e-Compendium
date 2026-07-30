"""Разметка описаний: подпись параметра — полужирным, термин — курсивом.

`to_html` размечает то, что проходит через него, но записи в паках уже лежат
готовым HTML, и часть из них конвейер не перегенерирует (кланы правятся
точечно, а `apply` без книг в `sources/` не запускается вовсе). Этот проход
доводит до одного вида всё, что есть в `_source`, и ничего не требует, кроме
самих паков.

Идемпотентен: размеченный абзац пропускается.

    python tools/emphasize.py --dry-run
    python tools/emphasize.py
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from add_clans import is_module_dir  # noqa: E402
from pdfkit import emphasize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def module_dir():
    return next(p for p in ROOT.iterdir() if is_module_dir(p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    changed = 0
    for path in sorted(module_dir().glob("packs/*/_source/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        system = data.get("system")
        if not isinstance(system, dict):
            continue

        # Текст записи не всегда лежит в `description`: у кланов проклятие
        # вынесено в отдельную вкладку и в отдельное поле `bane`. Идём по
        # всякому полю с абзацами, чтобы разметка не обрывалась на вкладке.
        fields = [k for k, v in system.items()
                  if isinstance(v, str) and "<p>" in v]
        touched = [k for k in fields if emphasize(system[k]) != system[k]]
        if not touched:
            continue

        changed += 1
        print(f"  {data.get('name', path.stem)}"
              + (f"  [{', '.join(touched)}]" if touched != ["description"] else ""))
        if not args.dry_run:
            for k in touched:
                system[k] = emphasize(system[k])
            text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

    verb = "разметилось бы" if args.dry_run else "размечено"
    print(f"\n{verb} записей: {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
