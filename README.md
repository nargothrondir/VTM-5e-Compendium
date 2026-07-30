[![Русский](https://img.shields.io/badge/Русский-8B0000?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/English-2B2B2B?style=for-the-badge)](README.en.md)

# VTM 5e Компендиум — русский перевод

Компендиум для **Vampire: The Masquerade 5th edition** в Foundry VTT: кланы,
Дисциплины, Сила Крови, типы охотника, достоинства и недостатки — на русском
языке, по официальному изданию.

Работает с неофициальной системой 5-й редакции
[wod5e](https://github.com/WoD5E-Developers/wod5e) от Veilza и Rayji96.
Foundry VTT 11–13.

---

## Происхождение

Это форк украинского модуля
[**vampire-the-masquerade-5e-compendium-ukr**](https://github.com/SexyCrowbar/vampire-the-masquerade-5e-compendium-ukr)
за авторством **SexyCrowbar** — низький уклін за виконану роботу. Дякую!

Украинская версия, в свою очередь, выросла из
[**vampire-the-masquerade-5e-compendium**](https://github.com/Clownf1sh/vampire-the-masquerade-5e-compendium)
за авторством **Nathaneal**.

Здесь переведён текст и переработана сборка; структура компендиума,
идентификаторы записей и иконки унаследованы без изменений — благодаря этому
персонажи, созданные на украинской версии, не ломаются.

---

## Что переведено

**239 записей и 98 папок** — весь компендиум целиком.

| Компендиум | Записей |
|---|---:|
| Кланы | 16 |
| Дисциплины | 121 |
| Сила крови и тип охотника | 17 |
| Преимущества и недостатки | 85 |

Подробнее:

- **Кланы** — все шестнадцать: описание, список Дисциплин и Изъян. Для семи
  кланов добавлен **альтернативный изъян**. Бану Хаким, Геката, Ласомбра и
  Министерство есть только в Руководстве для игроков, официального перевода у
  них пока нет — в таких записях источник указан прямо в тексте.
- **Дисциплины** — 90 сил десяти Дисциплин, 24 ритуала Кровавого чародейства и
  7 формул Алхимии слабокровных. У каждой указаны Амальгама, Расплата, Пул,
  Правила и Длительность.
- **Сила крови и тип охотника** — 7 уровней Силы Крови (от слабой крови до
  шестого и выше) и 10 типов охотника.
- **Преимущества и недостатки** — достоинства, недостатки и фоны. Фоны собраны
  целиком, со всеми пятью ступенями в одной записи.

Терминология — как переводится термин и почему — в [глоссарии](GLOSSARY.md).
Что уже сделано и что предстоит — в [плане перевода](ROADMAP.md).

Терминология взята из официального русского издания, а не переведена заново.
Поэтому «Безупречная точность», а не «Безошибочный прицел»; «Ласка Ваала»,
а не «Прикосновение Баала».

---

## Установка

В Foundry VTT: **Настройки → Управление модулями → Установить модуль**, вставить
в поле адреса манифеста:

```
https://github.com/nargothrondir/VTM-5e-Compendium/releases/latest/download/module.json
```

Либо скачать `module.zip` из
[релизов](https://github.com/nargothrondir/VTM-5e-Compendium/releases) и
распаковать в `Data/modules/`.

---

## Как это собрано

Перевод не набивался руками: текст **извлекается из книг и переносится
скриптами**, а решения о том, какой раздел книги какой записи компендиума
отвечает, зафиксированы в `data/mapping.yaml` — по одной строке на запись.

```
книги (PDF)  ──extract──▶  data/book_sections.json
                                     │
             data/mapping.yaml ──────┼──apply──▶  packs/*/_source/*.json
                                                          │
                                                        build
                                                          ▼
                                                    база LevelDB
```

| Команда | Что делает |
|---|---|
| `npm run extract` | разбирает книги на разделы |
| `npm run mapping` | собирает таблицу соответствий |
| `npm run apply` | переносит текст в записи компендиума |
| `npm run emphasize` | поднимает регистр терминов и размечает начертанием |
| `npm run build` | собирает `_source` в базу, которую читает Foundry |
| `npm run verify` | проверяет целостность и показывает прогресс |
| `npm run roundtrip` | доказывает, что сборка обратима |

Смысл затеи — в воспроизводимости: нашли огрех, поправили строку в
`data/mapping.yaml`, прогнали заново. Шаг переноса идемпотентен, JSON руками
трогать не нужно.

Извлечение **детерминированное**: разделы опознаются по начертанию, которым они
свёрстаны в книге, — заголовок силы, разделитель уровня, маркер списка, — а не
угадываются по тексту. Никаких обращений к внешним сервисам.

Истина хранится в `packs/*/_source/*.json`. Скомпилированная база LevelDB и
`module.zip` — артефакты сборки, в репозитории их нет.

### Книги

Переведённый текст взят из официальных
[источников по Vampire: The Masquerade](https://vtm.paradoxwikis.com/Official_TTRPG_sources) —
**Corebook**, **Companion** (Равнос, Салюбри, Цимисхи) и **Players Guide**
(четыре клана и альтернативные изъяны).

**Книги в репозиторий не входят и не будут** — они защищены авторским правом.
Чтобы запустить извлечение, положите свои экземпляры в `sources/`. Для правки
уже переведённых записей книги не нужны.

---

## Участники

- **[SexyCrowbar](https://github.com/SexyCrowbar)** — украинский модуль, на
  котором всё основано: структура компендиума, подбор записей, иконки.
- **Nathaneal** — исходный англоязычный модуль.
- **[nargothrondir](https://github.com/nargothrondir)** — русский перевод,
  сверка с официальным изданием, ведение форка.
- **Claude (Opus 5, Anthropic)** — инструменты извлечения и переноса, сборка и
  CI, сопоставление записей с разделами книг. Участие отражено в истории
  коммитов через `Co-Authored-By`.

Отдельная благодарность разработчикам системы
[wod5e](https://github.com/WoD5E-Developers/wod5e).

---

## Dark Pack

<img src="https://images.ctfassets.net/u73tyf0fa8v1/3oBTHBZk9XmfcBlUPylvFh/673e4a6b14566548c03424ddf627b944/darkpack_logo2.png?w=3840&q=75" alt="Dark Pack" width="200" />

“Portions of the materials are the copyrights and trademarks of Paradox
Interactive AB, and are used with permission. All rights reserved. For more
information please visit [worldofdarkness.com](http://worldofdarkness.com).”

- You may not remove or alter any copyright or trademark notices of World of
  Darkness.
- Your use of World of Darkness IP is strictly for non-commercial purposes only.
  For example, you may not offer goods or services for sale in connection with
  your use of the World of Darkness IP.
- You may not sell or charge any fees in connection with Your Material, with
  these exceptions:
  - You may accept donations for your time and materials through Patreon or
    similar services, or through sponsorships.
  - You may accept subscription fees and revenues allowable through streaming
    platforms such as Twitch, YouTube, Mixer, etc.
  - You may sell your Material through the Storytellers Vault, our official
    program that allows you to create and sell certain types of content through
    our authorized web portal.
- You warrant and represent that Your Material at all times shall comply with
  all applicable laws, and that it does not infringe any third party’s
  intellectual property rights or any other right.

Проект некоммерческий. Текст правил принадлежит правообладателям; модуль
распространяется как фанатский материал в рамках Dark Pack.
