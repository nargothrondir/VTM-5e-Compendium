[![Русский](https://img.shields.io/badge/Русский-2B2B2B?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/English-8B0000?style=for-the-badge)](README.en.md)

# VTM 5e Compendium — Russian translation

A Foundry VTT compendium for **Vampire: The Masquerade 5th edition** in Russian:
clans, Disciplines, Blood Potency, predator types, advantages and flaws.

Built for the unofficial 5th edition system
[wod5e](https://github.com/WoD5E-Developers/wod5e) by Veilza and Rayji96.
Foundry VTT 11–13.

---

## Origin

This is a fork of the Ukrainian module
[**vampire-the-masquerade-5e-compendium-ukr**](https://github.com/SexyCrowbar/vampire-the-masquerade-5e-compendium-ukr)
by **SexyCrowbar** — deep thanks for the work that made this possible. Thanks!

The Ukrainian version in turn grew out of the
[**vampire-the-masquerade-5e-compendium**](https://github.com/Clownf1sh/vampire-the-masquerade-5e-compendium)
by **Nathaneal**.

The text here is translated and the build was reworked, but the compendium
structure, entry identifiers and icons are inherited unchanged. Characters built
on the Ukrainian version keep working.

---

## What is translated

**405 entries and 117 folders** — the entire compendium.

| Compendium | Entries |
|---|---:|
| Clans | 16 |
| Disciplines | 191 |
| Blood Potency & Predator Type | 23 |
| Advantages & Flaws | 143 |
| Loresheets | 32 |

In detail:

- **Clans** — all sixteen: description, Discipline list and Bane. Seven clans
  also carry an **alternative Bane**. Banu Haqim, Hecata, Lasombra and Ministry
  exist only in the Players Guide, whose translation is fan-made rather than
  official — those entries state their source in the text.
- **Disciplines** — 121 powers across ten Disciplines, 35 Blood Sorcery rituals
  and 7 Thin-blood Alchemy formulae, plus the whole of **Oblivion**: 18 powers
  and 10 ceremonies. Each entry carries Amalgam, Cost, Dice Pool, System and
  Duration.
- **Blood Potency & Predator Type** — 7 Blood Potency levels and 16 predator
  types.
- **Advantages & Flaws** — merits, flaws and backgrounds, including 58 entries
  from the Players Guide: its new merits and flaws, the Caitiff, Thin-blood and
  Ghoul lists, and eight backgrounds. Backgrounds are kept whole, with all five
  dot levels in a single entry.
- **Loresheets** — all twenty-five from the Corebook (Theo Bell, the Cainite
  Heresy, Golconda, the First Inquisition, the High and Low Clans) plus the
  seven Hecata bloodlines from the Players Guide. Each carries its
  introduction and five named dot levels.

Terminology — how a term is rendered and why — lives in the [glossary](GLOSSARY.md).
What is done and what is left — in the [roadmap](ROADMAP.md).

Terminology follows the official Russian edition rather than being re-translated,
so an English reader should expect the published Russian names, not literal
renderings of the English ones.

---

## Installation

In Foundry VTT: **Settings → Add-on Modules → Install Module**, then paste the
manifest URL:

```
https://github.com/nargothrondir/VTM-5e-Compendium/releases/latest/download/module.json
```

Or download `module.zip` from
[Releases](https://github.com/nargothrondir/VTM-5e-Compendium/releases) and
unpack it into `Data/modules/`.

---

## How it is built

The translation was not typed in by hand. Text is **extracted from the
sourcebooks and applied by scripts**, and every decision about which book
section belongs to which compendium entry lives in `data/mapping.yaml` — one
line per entry.

```
sourcebooks (PDF)  ──extract──▶  data/book_sections.json
                                          │
                  data/mapping.yaml ──────┼──apply──▶  packs/*/_source/*.json
                                                              │
                                                            build
                                                              ▼
                                                        LevelDB pack
```

| Command | What it does |
|---|---|
| `npm run extract` | splits the sourcebooks into sections |
| `npm run mapping` | builds the correspondence table |
| `npm run apply` | writes the text into compendium entries |
| `npm run emphasize` | capitalises game terms and marks up labels |
| `npm run build` | compiles `_source` into the pack Foundry reads |
| `npm run verify` | checks integrity and reports progress |
| `npm run roundtrip` | proves the build is reversible |

The point is reproducibility: spot a mistake, fix one line in
`data/mapping.yaml`, run it again. The apply step is idempotent, so the JSON is
never edited by hand.

Extraction is **deterministic** — sections are recognised by the typography they
are set in (power heading, level divider, list marker), not by guessing at the
prose. No external services are involved.

`packs/*/_source/*.json` is the source of truth. The compiled LevelDB pack and
`module.zip` are build artifacts and are not stored in the repository.

### Sourcebooks

Translated text comes from the official
[Vampire: The Masquerade sourcebooks](https://vtm.paradoxwikis.com/Official_TTRPG_sources) —
the **Corebook**, the free **Companion** (Ravnos, Salubri, Tzimisce) and the
**Players Guide** (four clans and the Bane variants).

**The books are not included in this repository and never will be** — they are
copyrighted. To run extraction yourself, place your own copies in `sources/`.
Editing already-translated entries does not require them.

---

## Contributors

- **[SexyCrowbar](https://github.com/SexyCrowbar)** — the Ukrainian module this
  is built on: compendium structure, entry selection, icons.
- **Nathaneal** — the original English module.
- **[nargothrondir](https://github.com/nargothrondir)** — Russian translation,
  proofing against the official edition, maintaining this fork.
- **Claude (Opus 5, Anthropic)** — extraction and apply tooling, build and CI,
  matching entries to book sections. Recorded in the commit history via
  `Co-Authored-By`.

Thanks also to the developers of the
[wod5e](https://github.com/WoD5E-Developers/wod5e) system.

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

This is a non-commercial fan project. The rules text belongs to its rights
holders; the module is distributed as fan material under the Dark Pack.
