"""Проверка самой проверки: ловит ли `audit` то, ради чего написан.

Каждый случай здесь — настоящий огрех из истории репозитория, а не выдумка.
Без этих тестов `audit` был бы украшением: он молчит на исправном дереве,
и молчание ничего не доказывает.

    python tools/test_audit.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import audit  # noqa: E402


def record(_id, text, name="Проба", field="description"):
    return (Path(f"{name}_{_id}.json"),
            {"_id": _id, "name": name, "_key": f"!items!{_id}",
             "system": {field: text}})


def lengths_of(rows):
    return {key for key, _ in audit.check_lengths({"проба": rows})}


def markup_of(rows):
    found = []
    audit.check_markup({"проба": rows}, found)
    return found


NORMAL = "<p>" + "Ровный текст записи. " * 20 + "</p>"


def case(name, condition):
    condition = bool(condition)
    print(f"  {'ok ' if condition else 'ПРОВАЛ'} {name}")
    return condition


def main():
    ok = True

    # «Ликвидатор» и «Неприкосновенный» — запись создалась, тело пустое.
    rows = [record(f"norm{i}", NORMAL) for i in range(9)]
    rows.append(record("empty", "<p>нет</p>"))
    ok &= case("обрыв разбора: пустое тело",
               "проба:empty:description" in lengths_of(rows))

    # «Слова-карриды» вобрали повествовательную часть главы.
    rows = [record(f"norm{i}", NORMAL) for i in range(9)]
    rows.append(record("huge", "<p>" + "слово " * 4000 + "</p>"))
    ok &= case("вобран соседний раздел",
               "проба:huge:description" in lengths_of(rows))

    # Исправное дерево обязано молчать.
    rows = [record(f"norm{i}", NORMAL) for i in range(10)]
    ok &= case("на ровном тексте молчит", not lengths_of(rows))

    # «Богатство»: полужирным стало полпредложения.
    bad = "<p>■ • <strong>Рабочий класс. Ты живёшь от зарплаты:</strong> кв.</p>"
    ok &= case("в подпись попало предложение", markup_of([record("b", bad)]))

    # Честный заголовок изъяна в сорок семь знаков — не огрех.
    good = "<p><strong>Альтернативный изъян: Неестественные проявления</strong></p>"
    ok &= case("длинный, но честный заголовок пропускает",
               not markup_of([record("g", good)]))

    # Колонтитул Руководства в хвосте у Салюбри.
    head = "<p>в этом домене. VA M P I R E T H E M A S Q U E R A D E</p>"
    ok &= case("колонтитул латиницей", markup_of([record("h", head)]))

    # Предлог «ПО», уцелевший от починки кодировки.
    ok &= case("непочиненная кодировка",
               markup_of([record("m", "<p>ДОЛГИ ÏÎ КРЕДИТАМ</p>")]))

    # Ударение из книги порчей не считается — «Мавлá» беречь особо оговорено.
    ok &= case("ударение не принимает за порчу",
               not markup_of([record("a", "<p>Мавлá и мавали</p>")]))

    # Осмысленная латиница внутри русского текста тоже законна.
    ok &= case("латиница не принимается за порчу",
               not markup_of([record("l", "<p>Книга Vampire: The Masquerade</p>")]))

    # Точки третьей ступени, выпавшие как глиф без таблицы соответствий.
    ok &= case("глиф без таблицы", markup_of([record("d", "<p>฀฀฀ Вонь</p>")]))

    # Вложенный курсив — след двойного прогона разметки.
    ok &= case("вложенный тег",
               markup_of([record("n", "<p><em>Смекалка <em>+</em></em></p>")]))

    # Украинская буква — непереведённый остаток.
    ok &= case("украинская буква",
               markup_of([record("u", "<p>Ясновидіння</p>")]))

    print("\nвсе случаи пройдены" if ok else "\nЕСТЬ ПРОВАЛЫ")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
