"""Канонические английские названия — для словаря терминов.

Сопоставление при переводе шло через них, но в данных они не сохранялись:
оставались в голове и в комментариях. Здесь собраны и сверены по спискам
paradoxwikis, а не по памяти — расхождения находились («Violent Temper»,
а не «Rage»; «Abhors the Light», а не «Light Sensitive»).

Ключ — русское название, как оно стоит в компендиуме.
"""

POWERS = {
    # Анимализм
    "Фамулус": "Bond Famulus",
    "Чутьё на зверя": "Sense the Beast",
    "Язык животных": "Feral Whispers",
    "Зверский аппетит": "Animal Succulence",
    "Трупный улей": "Unliving Hive",
    "Усмирение зверя": "Quell the Beast",
    "Поглощение духа": "Subsume the Spirit",
    "Отчуждение зверя": "Drawing Out the Beast",
    "Царь зверей": "Animal Dominion",
    # Величие
    "Благоговение": "Awe",
    "Угроза": "Daunt",
    "Незабываемый поцелуй": "Lingering Kiss",
    "Очарование": "Entrancement",
    "Устрашающий взор": "Dread Gaze",
    "Призыв": "Summon",
    "Притягательный голос": "Irresistible Voice",
    "Звезда эфира": "Star Magnetism",
    "Преклонение": "Majesty",
    # Доминирование
    "Принуждение": "Compel",
    "Провал в памяти": "Cloud Memory",
    "Внушение": "Mesmerize",
    "Помешательство": "Dementation",
    "Внедрённая директива": "Submerged Directive",
    "Забвение": "Forgetful Mind",
    "Оправдание": "Rationalize",
    "Приказ на самоуничтожение": "Terminal Decree",
    "Стадный инстинкт": "Mass Manipulation",
    # Метаморфозы
    "Глаза зверя": "Eyes of the Beast",
    "Лёгкость пёрышка": "Weight of the Feather",
    "Оружие зверя": "Feral Weapons",
    "Слияние с землёй": "Earth Meld",
    "Смена облика": "Shapechange",
    "Перевоплощение": "Metamorphosis",
    "Превращение в туман": "Mist Form",
    "Свободное сердце": "The Unfettered Heart",
    # Мощь
    "Мощный прыжок": "Soaring Leap",
    "Смертоносность": "Lethal Body",
    "Сокрушение": "Prowess",
    "Грубое насыщение": "Brutal Feed",
    "Искра ярости": "Spark of Rage",
    "Мёртвая хватка": "Uncanny Grip",
    "Глоток могущества": "Draught of Might",
    "Землетрясение": "Earth Shock",
    "Кулак Каина": "Fist of Caine",
    # Сокрытие
    "Безмолвие смерти": "Silence of Death",
    "Плащ теней": "Cloak of Shadows",
    "Незримая поступь": "Unseen Passage",
    "Маска тысячи лиц": "Mask of a Thousand Faces",
    "Электронный призрак": "Ghost in the Machine",
    "Бесследное исчезновение": "Vanish",
    "Маскировка": "Conceal",
    "Личина самозванца": "Impostor's Guise",
    "Тайное собрание": "Cloak the Gathering",
    # Стойкость
    "Сила жизни": "Resilience",
    "Твёрдость духа": "Unswayable Mind",
    "Живучие звери": "Enduring Beasts",
    "Непрошибаемость": "Toughness",
    "Превозмогание проклятия": "Defy Bane",
    "Укрепление сознания": "Fortify the Inner Façade",
    "Глоток упорства": "Draught of Endurance",
    "Горнило боли": "Prowess from Pain",
    "Мраморная плоть": "Flesh of Marble",
    # Стремительность
    "Быстрая реакция": "Rapid Reflexes",
    "Кошачья грация": "Cat's Grace",
    "Проворство": "Fleetness",
    "Быстрее ветра": "Blink",
    "Траверс": "Traversal",
    "Безупречная точность": "Unerring Aim",
    "Глоток изящества": "Draught of Elegance",
    "Молниеносный удар": "Lightning Strike",
    "Скорость мысли": "Split Second",
    # Ясновидение
    "Обострение чувств": "Heightened Senses",
    "Потустороннее зрение": "Sense the Unseen",
    "Предвестие": "Premonition",
    "Познание души": "Scry the Soul",
    "Слияние чувств": "Share the Senses",
    "Психометрия": "Spirit's Touch",
    "Вселение": "Possession",
    "Дальновидение": "Clairvoyance",
    "Телепатия": "Telepathy",
    # Кровавое чародейство
    "Вкус крови": "A Taste for Blood",
    "Едкая кровь": "Corrosive Vitae",
    "Истончение витэ": "Extinguish Vitae",
    "Касание скорпиона": "Scorpion's Touch",
    "Сгущение крови": "Blood of Potency",
    "Хищение крови": "Theft of Vitae",
    "Котёл крови": "Cauldron of Blood",
    "Ласка Ваала": "Baal's Caress",
    # Ритуалы
    "Вечерняя бодрость": "Wake with Evening's Freshness",
    "Защитная печать от гулей": "Ward Against Ghouls",
    "Паучьи лапы": "Clinging of the Insect",
    "Постижение крови": "Blood Walk",
    "Путеводный камень": "Craft Bloodstone",
    "Защитная печать от духов": "Ward against Spirits",
    "Защитный круг от гулей": "Warding Circle against Ghouls",
    "Истина в крови": "Truth of Blood",
    "Очи вавилонские": "Eyes of Babel",
    "Свечение следопыта": "Illuminate Trail of Prey",
    "Связь с сиром": "Communicate with Kindred Sire",
    "Защитная печать от люпенов": "Ward against Lupines",
    "Защитный круг от духов": "Warding Circle against Spirits",
    "Зов Дагона": "Dagon's Call",
    "Отторжение губительного древа": "Deflection of Wooden Doom",
    "Пожиратель пламени": "Firewalker",
    "Эссенция воздуха": "Essence of Air",
    "Бесплотный путь": "Incorporeal Passage",
    "Защита неприкосновенного убежища": "Defense of the Sacred Haven",
    "Защитная печать от каинитов": "Ward against Cainites",
    "Защитный круг от люпенов": "Warding Circle against Lupines",
    "Око ночного ястреба": "Eyes of the Nighthawk",
    "Врата истинного святилища": "Escape to True Sanctuary",
    "Жало неизбежной погибели": "Shaft of Belated Dissolution",
    "Защитный круг от каинитов": "Warding Circle against Cainites",
    "Каменное сердце": "Heart of Stone",
    # Алхимия слабокровных
    "Длинные руки": "Far Reach",
    "Марево": "Haze",
    "Смог": "Envelop",
    "Нечестивая иерогамия": "Profane Hieros Gamos",
    "Восстановление крови": "Defractionate",
    "Импульс": "Airborne Momentum",
    "Будильник": "Awaken the Sleeper",
}

DISCIPLINES = {
    "Анимализм": "Animalism",
    "Величие": "Presence",
    "Доминирование": "Dominate",
    "Кровавое чародейство": "Blood Sorcery",
    "Метаморфозы": "Protean",
    "Мощь": "Potence",
    "Сокрытие": "Obfuscate",
    "Стойкость": "Fortitude",
    "Стремительность": "Celerity",
    "Ясновидение": "Auspex",
    "Ритуалы": "Blood Sorcery Rituals",
    "Алхимия слабокровных": "Thin-blood Alchemy",
    "Обливион": "Oblivion",
}

PREDATOR_TYPES = {
    "Бестия": "Blood Leech",
    "Джентльмен": "Consensualist",
    "Идол": "Osiris",
    "Искуситель": "Siren",
    "Морфей": "Sandman",
    "Налётчик": "Alleycat",
    "Семьянин": "Cleaver",
    "Суррогатчик": "Bagger",
    "Тусовщик": "Scene Queen",
    "Фермер": "Farmer",
    "Вымогатель": "Extortionist",
    "Расхититель могил": "Graverobber",
    "Мрачный жнец": "Grim Reaper",
    "Монтеро": "Montero",
    "Преследователь": "Pursuer",
    "Лазутчик": "Trapdoor",
}

BANES = {
    "Буйный нрав": "Violent Temper",
    "Изысканный вкус": "Rarefied Tastes",
    "Звериные черты": "Bestial Features",
    "Расколотое восприятие": "Fractured Perspective",
    "Отвратительность": "Repulsiveness",
    "Жажда красоты": "Aesthetic Fixation",
    "Ущербная Кровь": "Deficient Blood",
    "Кровавая зависимость": "Blood Addiction",
    "Болезненный Поцелуй": "Painful Kiss",
    "Искажённое отражение": "Distorted Image",
    "Неприятие света": "Abhors the Light",
    "Обречённость": "Doomed",
    "Гонимые": "Hunted",
    "Привязанность": "Grounded",
    "Изгой": "Outcast",
}

BANE_VARIANTS = {
    "Ядовитая кровь": "Noxious Blood",
    "Насилие": "Violence",
    "Инстинкты Выживания": "Survival Instincts",
    "Распад": "Decay",
    "Черствость": "Callousness",
    "Неестественные проявления": "Unnatural Manifestations",
    "Хладнокровный": "Cold-Blooded",
    "Заражение": "Infestation",
    "Нерожденное Имя": "Unbirth Name",
    "Аскетизм": "Asceticism",
    "Мучительное сочувствие": "Agonizing Empathy",
    "Украденная кровь": "Stolen Blood",
    "Проклятая учтивость": "Cursed Courtesy",
    "Иерархия": "Hierarchy",
}

COMPULSIONS = {
    "бунт": "Rebellion",
    "превосходство": "Arrogance",
    "животные порывы": "Feral Impulses",
    "наваждение": "Delusion",
    "криптомания": "Cryptophilia",
    "восхищение": "Obsession",
    "перфекционизм": "Perfectionism",
    "приговор": "Judgment",
    "болезненность": "Morbidity",
    "безжалостность": "Ruthlessness",
    "преступление": "Transgression",
    "искушение судьбы": "Tempting Fate",
    "аффективное сопереживание": "Affective Empathy",
    "алчность": "Covetousness",
}

STRUCTURE = {
    "Амальгама": "Amalgam",
    "Расплата": "Cost",
    "Пул": "Dice Pool",
    "Правила": "System",
    "Длительность": "Duration",
    "Компоненты": "Ingredients",
    "Изъян": "Bane",
    "Одержимость": "Compulsion",
    "Сила Крови": "Blood Potency",
    "витэ": "vitae",
    "Становление": "Embrace",
    "Сородичи": "Kindred",
    "Голод": "Hunger",
    "Человечность": "Humanity",
    "Тип охотника": "Predator Type",
}

# Достоинства и недостатки из Руководства для игроков. Сверено по вики, и
# сверять было за чем: перевод там местами машинный, и по названию оригинал
# не угадывается. «Проверить ствол» — это Check the Trunk, багажник машины
# с полезным скарбом, а не оружие; «Устаревающий упадок» — Starving Decay.
# Ключ — название в книге, как оно стоит в записи.
PLAYERS_GUIDE_MERITS = {
    "Известное лицо": "Famous Face",
    "Ангел": "Ingénue",
    "Замечательная особенность": "Remarkable Feature",
    "Распознавание сосудов": "Vessel Recognition",
    "Дьявольская удача": "Luck of the Devil",
    "Режим Ньюит": "Nuit Mode",
    "Проверить ствол": "Check the Trunk",
    "Сторонний хастлер": "Side Hustler",
    "Темперированная Воля": "Tempered Will",
    "Неприкосновенный": "Untouchable",
    "Зловоние": "Stench",
    "Транспарент": "Transparent",
    "Венозная лента": "Vein Tapper",
    "Устаревающий упадок": "Starving Decay",
    "Двойное проклятье": "Twice Cursed",
    "Жаждущий знаний": "Knowledge Hungry",
    "Долги по кредитам": "Prestation Debts",
    "Рисковый игрок": "Risk-Taker",
    "Слабая Воля": "Weak-Willed",
}

# Глава «Кастомы»: свои достоинства у каитиффов, слабокровных и гулей.
# Перевод здесь ещё грубее: «Перемешник» — это Mockingbird, то есть
# пересмешник, а «Слова-карриды» — Word-Scarred, где «scarred» прочитано
# как имя. «Надежность» — Faith-Proof, стойкость к Истинной Вере, а вовсе
# не надёжность.
#
# «Солнцезащитный» (•••••) в перечне вики отсутствует; оригинал не сверен
# и оставлен пустым намеренно — выдумывать его хуже, чем признать пробел.
PLAYERS_GUIDE_CUSTOM = {
    "Любимая Кровь": "Favored Blood",
    "Метка Каина": "Mark of Caine",
    "Перемешник": "Mockingbird",
    "Солнцезащитный": "",
    "Клыкастый дядя": "Uncle Fangs",
    "Животное витэ": "Befouling Vitae",
    "Проклятие клана": "Clan Curse",
    "Долговая яма": "Debt Peon",
    "Ликвидатор": "Liquidator",
    "Мутная Кровь": "Muddled Blood",
    "Ходячий омен": "Walking Omen",
    "Слова-карриды": "Word-Scarred",
    "Гелиофобия": "Heliophobia",
    "Ночные кошмары": "Night Terrors",
    "Носитель чумы": "Plague Bearers",
    "Неаккуратное питье": "Sloppy Drinker",
    "Выраканный на солнце": "Sun-Faded",
    "Сверхъестественное присутствие": "Supernatural Tell",
    "Сумерочное присутствие": "Twilight Presence",
    "Непрерывный голод": "Unending Hunger",
    "Отвратительная Кровь": "Abhorrent Blood",
    "Надежность": "Faith-Proof",
    "Низкий аппетит": "Low Appetite",
    "Осознанный мечтатель": "Lucid Dreamer",
    "Образ смертных": "Mortality's Mien",
    "Быстрый питатель": "Swift Feeder",
    "Сопереживание Крови": "Blood Empathy",
    "Потускневшая аура": "Unseemly Aura",
    "Кровь с изъяном": "Baneful Blood",
    "Проклятие старения": "Crone's Curse",
    "Пугающие клыки": "Distressing Fangs",
}

# Фоны из Руководства. Сверено меньше, чем хотелось бы: вики держит перечень
# Фонов сводным, без разбивки по книгам, и пять записей в нём не опознаются.
# Пустая строка означает «оригинал не сверен», а не «совпадает с русским».
PLAYERS_GUIDE_BACKGROUNDS = {
    "Недостаток: Враги": "Enemy",
    "• Фуркус": "Furcus",
    "• Машиностроительный цех": "Machine Shop",
    "Недостаток: (•) Общество": "",
    "Страницы истории": "",
    "Линия крови": "",
    "Торговля долгами": "",
    "• Городские тайны": "",
}


# ---------------------------------------------------------------------------
# Канонические списки: всё, что существует в линейке, а не только переведённое.
# Нужны затем, чтобы глоссарий работал планом: видно, что сделано, что нет
# и что вообще недостижимо, пока нет соответствующей книги.
# Сверено по paradoxwikis.
# ---------------------------------------------------------------------------

CANON_POWERS = {
    "Анимализм": [
        "Bond Famulus", "Sense the Beast", "Animal Messenger", "Atavism",
        "Feral Whispers", "Leash the Beast", "Messenger's Command",
        "Animal Succulence", "Plague of Beasts", "Quell the Beast",
        "Scent of Prey", "Unliving Hive", "Augury", "Awaken the Parasite",
        "Subsume the Spirit", "Sway the Flock", "Animal Dominion",
        "Coax the Bestial Temper", "Drawing Out the Beast", "Spirit Walk",
    ],
    "Величие": [
        "Awe", "Daunt", "Eyes of the Serpent", "Lingering Kiss", "Melpominee",
        "Clear the Field", "Dread Gaze", "Entrancement", "Passion Leech",
        "Thrown Voice", "True Love's Face", "Invigorating Display",
        "Inflame Desire", "Irresistible Voice", "Magnum Opus",
        "Suffuse the Edifice", "Summon", "Wingman", "Majesty",
        "Star Magnetism",
    ],
    "Доминирование": [
        "Cloud Memory", "Compel", "Slavish Devotion", "Mesmerize",
        "Dementation", "Domitor's Favor", "The Stolen Voice", "Forgetful Mind",
        "Submerged Directive", "Ancestral Dominion", "Implant Suggestion",
        "Rationalize", "Tabula Rasa", "Lethe's Call", "Mass Manipulation",
        "Terminal Decree",
    ],
    "Кровавое чародейство": [
        "Corrosive Vitae", "Shape the Sanguine Sacrament", "A Taste for Blood",
        "Koldunic Sorcery", "Blood's Curse", "Extinguish Vitae",
        "Scour Secrets", "Blood of Potency", "Scorpion's Touch",
        "Transitive Bond", "Ripples of the Heart", "Theft of Vitae",
        "Blood Aegis", "Fulminating Vitae", "Marionette", "Baal's Caress",
        "Cauldron of Blood", "Reclamation of Vitae",
    ],
    "Метаморфозы": [
        "Eyes of the Beast", "Squirm", "Weight of the Feather", "Feral Weapons",
        "Vicissitude", "Serpent's Kiss", "The False Sip", "Earth Meld",
        "Fleshcrafting", "Shapechange", "Visceral Absorption",
        "Masque of Death", "Horrid Form", "Metamorphosis", "Blood Form",
        "The Heart of Darkness", "Master of Forms", "Mist Form",
        "One with the Land", "Swarm", "The Unfettered Heart",
        "Face of the Victim",
    ],
    "Мощь": [
        "Fluent Strength", "Lethal Body", "Soaring Leap", "Prowess",
        "Relentless Grasp", "Brutal Feed", "Exuberance", "Spark of Rage",
        "Uncanny Grip", "Wrecker", "Draught of Might", "Crash Down",
        "Earth Shock", "Fist of Caine", "Subtle Hammer",
    ],
    "Сокрытие": [
        "Cloak of Shadows", "Ensconce", "Silence of Death", "Mask of Ages",
        "Cache", "Chimerstry", "Ghost's Passing", "Unseen Passage",
        "Ventriloquism", "Doubletalk", "Fata Morgana", "Ghost in the Machine",
        "Mask of a Thousand Faces", "Mask of Isolation", "Mental Maze",
        "Mind Masque", "Guise of the Departed", "Conceal", "Vanish",
        "Seclusion", "Cloak the Gathering", "Impostor's Guise",
    ],
    "Стойкость": [
        "Fluent Endurance", "Resilience", "Unswayable Mind",
        "Earth's Perseverance", "Enduring Beasts", "Invigorating Vitae",
        "Obdurate", "Toughness", "Self-Assurance", "Defy Bane",
        "Fortify the Inner Façade", "Seal the Beast's Maw", "Valeren",
        "Calloused Soul", "Draught of Endurance", "Gorgon's Scales", "Shatter",
        "Flesh of Marble", "Prowess from Pain", "Meat Shields",
    ],
    "Стремительность": [
        "Cat's Grace", "Fluent Swiftness", "Rapid Reflexes", "Fleetness",
        "Rush Job", "Blink", "Traversal", "Weaving", "A Thousand Cuts",
        "Blurred Momentum", "Draught of Elegance", "Unerring Aim",
        "Unseen Strike", "Faster than Light", "Lightning Strike",
        "Split Second",
    ],
    "Ясновидение": [
        "Heightened Senses", "Sense the Unseen", "Panacea", "Premonition",
        "Reveal Temperament", "Unerring Pursuit", "Vermin Vision",
        "Fatal Flaw", "Scry the Soul", "Share the Senses", "Haruspex",
        "Spirit's Touch", "Heart Laid Bare", "Clairvoyance", "Possession",
        "Telepathy", "Unburdening the Bestial Soul",
    ],
}

# Типы питания. Источник указан затем, чтобы было видно, что достижимо:
# четыре из Руководства для игроков переводимы хоть сейчас, остальные
# требуют книг, которых у проекта нет.
CANON_PREDATOR_TYPES = [
    ("Alleycat", "Corebook"), ("Bagger", "Corebook"),
    ("Blood Leech", "Corebook"), ("Cleaver", "Corebook"),
    ("Consensualist", "Corebook"), ("Farmer", "Corebook"),
    ("Osiris", "Corebook"), ("Sandman", "Corebook"),
    ("Scene Queen", "Corebook"), ("Siren", "Corebook"),
    # Руководство перепечатывает оба, так что источник у проекта есть.
    ("Extortionist", "Players Guide"),
    ("Graverobber", "Players Guide"),
    ("Roadside Killer", "Let the Streets Run Red"),
    ("Grim Reaper", "Players Guide"), ("Montero", "Players Guide"),
    ("Pursuer", "Players Guide"), ("Trapdoor", "Players Guide"),
    ("Tithe Collector", "In Memoriam"),
]

# Страницы истории. Книга правил закрыта целиком; остальное перечислено,
# чтобы охват не выглядел полным по недосмотру — линейка прирастала
# лоршитами десять лет, и в каноне их больше полутора сотен.
# Сверено по https://vtm.paradoxwikis.com/Loresheets
CANON_LORESHEETS = {
    "Corebook": [
        "The Bahari", "Theo Bell", "Cainite Heresy", "Carna",
        "The Circulatory System", "Convention of Thorns",
        "The First Inquisition", "Golconda", "Descendant of Hardestadt",
        "Descendant of Helena", "Sect War Veteran", "The Trinity",
        "Jeanette/Therese Voerman", "The Week of Nightmares", "Rudi",
        "Descendant of Tyler", "Descendant of Zelios",
        "Descendant of Vasantasena", "High Clan", "Low Clan",
        "Ambrus Maropis", "Carmelita Neillson", "Fiorenza Savona",
        "Descendant of Karl Schrekt", "Descendant of Xaviar",
    ],
    "Anarch": [
        "Salvador Garcia", "Agata Starek", "Hesha Ruhadze",
        "The Church of Set", "Ruins of Carthage", "Blood Plagued",
        "Anarch Revolt",
    ],
    "Camarilla": [
        "Fatima Al-Faqadi", "Pure Ventrue Lineage", "The Cult of Mithras",
        "The Pyramid", "Victoria Ash",
    ],
    "Chicago by Night": [
        "Annabelle", "Ballard Industries", "Blacksite 24", "The Blue Velvet",
        "The Book of Nod", "Capone Gang", "The Cobweb", "Cultivar",
        "Cult of Shalim", "Descendant of Lodin", "Descendant of Montano",
        "Fires and Floods and the Devil's Night", "Firstlight",
        "Kevin Jackson", "Kindred Iconography", "The Labyrinth",
        "Lupine Expert", "Nathaniel Bordruff", "The Painted Lady",
        "Revenant Family: Ducheski", "The Society of St. Leopold", "Talley",
        "Wauneka",
    ],
    "Chicago Folios": [
        "Archons", "The Convention of Chicago", "Descendant of Menele",
        "Goblin Roads", "Justicar Lucinde", "Khalid Al-Rashid",
        "Kindred Dueling", "Malkavian Family", "Occult Artifacts",
        "The Pony Express", "Sheriff Damien", "The Wolf Pack",
    ],
    "Let the Streets Run Red": [
        "The Anubi", "Eletria", "Kindred Social Media Influencer", "Juggler",
        "Lost Secrets of the Milwaukee Chantry", "Mark Decker", "Maxwell",
        "The Milwaukee \"Null Zone\"", "Modius",
    ],
    "Cults of the Blood Gods": [
        "Bankers of Dunsirn", "Children of Tenochtitlan",
        "The Nation of Blood", "Flesh-Eaters", "Harbingers of Ashur",
        "La Famiglia Giovanni", "The Criminal Puttanesca", "The Gorgons",
        "Calling the Family Reunion", "Child of the Angel Michael",
        "Servitor of Irad", "The Promise of 1528",
    ],
    "Children of the Blood": [
        "Little Siblings", "Grudge Masters", "The Ashfinders", "Amaranthan",
        "Cleopatras", "Meneleans", "The One True Way", "Starfall Ranch",
    ],
    "Forbidden Religions": [
        "1444 Chamber", "Blood Asceticism", "Gehenna Cults",
        "Plagues of Gehenna", "Praepositor", "Spear of Orthia",
    ],
    "Fall of London": [
        "Agent of Justicar Parr", "Court of Shadows", "Hunt Club",
        "London under London", "Operation Antigen", "Oskar Anasov",
    ],
    "In Memoriam": [
        "Birth of the Anarch Free States", "Childe of the Revolution",
        "Descendant of Dracula", "The Order of Repentants", "The Red Lady",
        "The Vanderbilt Ventrue",
    ],
    "Live from the Succubus Club": [
        "Descendant of Idder", "Descendant of Kerwiya",
        "Descendant of Phaedyme", "Descendant of The Fallen Lord",
        "Succubus Club Copycat", "Road Courier", "Stories of the Daughters",
        "Temple of Boom Contract",
    ],
    "Winter's Teeth": [
        "Wolves in Sheep's Clothing", "The Nictuku", "Minneapolis",
        "St. Paul", "The Mortician's Army",
    ],
    "Blood Sigils": [
        "Descendant of Al-Ashrad", "Student of Kirin Taunk",
        "Veins of the Earth", "Vienna Zero",
    ],
    "Courts of the Damned": [
        "Descendant of Count Jocalo", "Descendant of Marconius",
        "Descendant of Meerlinda", "Descendant of Rasalon",
    ],
    "Trails of Ash and Bone": [
        "The Ruby Throat", "Descendant of Roger de Camden",
        "Relics of the Veil",
    ],
    "Gehenna War": ["Beckett", "The Eternal Arena", "Tegyrius the Vizier"],
    "Boston by Night": ["The Hartford Chantry", "The Boston Camarilla"],
    "Tattered Façade": [
        "Descendant of the Ankou", "Descendant of Baron Vollgirre",
    ],
    "Book of Nod Apocrypha": ["Machinations of Saulot"],
}

# Типы котерий. В компендиуме их нет вовсе, а взять можно двадцать семь:
# шестнадцать из Книги правил и одиннадцать из Руководства.
# Сверено по https://vtm.paradoxwikis.com/Coterie_types
CANON_COTERIE_TYPES = {
    "Corebook": [
        "Blood Cult", "Cerberus", "Champions", "Commando", "Co-op",
        "Day Watch", "Fang Gang", "Hunting Party", "Nomad", "Plumaire",
        "Questari", "Regency", "Sbirri", "Vanguard", "Vehme", "Watchmen",
    ],
    "Players Guide": [
        "Carnival", "Corporate", "Envoys", "Excommunicates", "Family",
        "Flagellant", "Fugitive", "Gatekeeper", "Maréchal", "Nemeses",
        "Saboteur",
    ],
    "Cults of the Blood Gods": ["Diocese", "Think Tank"],
    "Children of the Blood": [
        "Missionaries", "Schism", "Theologian Society",
    ],
    "Chicago by Night": ["Rectorate", "Somnophile"],
    "In Memoriam": [
        "Archonium", "Primogen's Council", "Prince's Court",
        "The Decade Club",
    ],
    "Winter's Teeth": ["Support Group"],
    "Forbidden Religions": ["The Household"],
}

# Достоинства, недостатки и владения котерии. Тоже нет ни одного, а доступны
# все двадцать восемь: десять из Книги правил и восемнадцать владений
# из Руководства.
# Сверено по https://vtm.paradoxwikis.com/Coterie_Backgrounds_and_Merits
CANON_COTERIE_TRAITS = {
    "Corebook": [
        "Bolt Holes", "On Tap", "Privileged", "Transportation",
        "Bullies", "Cursed", "Custodians", "Targeted", "Territorial",
        "Under Siege",
    ],
    "Players Guide": [
        "Apartment Towers", "Back Alleys", "Funerary", "Gated Community",
        "Hospital", "Nightlife", "Shelter",
        "Campus", "City Hall", "Cultural Landmark", "Marketplace",
        "Members Only", "Transitions",
        "Abandoned Building", "Firehouse", "Police Station", "Prison",
        "Transit",
    ],
}

CANON_CLANS = [
    "Banu Haqim", "Brujah", "Caitiff", "Gangrel", "Hecata", "Lasombra",
    "Malkavian", "Ministry", "Nosferatu", "Ravnos", "Salubri", "Thin-blood",
    "Toreador", "Tremere", "Tzimisce", "Ventrue",
]

# Силы из Руководства для игроков. Перечень снимается тем же разбором,
# который переносит их в компендиум, — иначе списки расходятся: грубый
# фильтр принимал за названия подзаголовки внутри церемоний.
PLAYERS_GUIDE_POWERS = {
    'Анимализм': [
        ('Вестник зверей', 71),
        ('Приказ вестника', 71),
        ('Чума зверей', 71),
        ('Управление стаями', 71),
        ('Усмирить пением зверя', 72),
    ],
    'Ясновидение': [
        ('Панацея', 72),
        ('Выявление темперамента', 72),
        ('Смертельная ошибка', 73),
        ('Очищение падшей душ', 73),
    ],
    'Стремительность': [
        ('Оперативная работа', 74),
        ('Пропульсия', 74),
        ('Размытый импульс', 74),
    ],
    'Доминирование': [
        ('Рабская преданность', 75),
        ('Наследственное господство', 76),
        ('Нота внедрения', 76),
    ],
    'Стойкость': [
        ('Стойкость земли', 76),
        ('Витэ жизни', 77),
        ('Валерен', 77),
        ('Чешуя горгоны', 77),
    ],
    'Сокрытие': [
        ('Химерия', 78),
        ('Фата моргана', 79),
        ('Ментальный лабиринт', 79),
        ('Маска разума', 80),
    ],
    'Могущество': [
        ('Безжалостная хватка', 81),
        ('Губительное сокрушение', 81),
        ('Разрушительное падение', 81),
        ('Ловкий молот', 81),
    ],
    'Величие': [
        ('Мельпомена', 82),
        ('Громогласный голос', 82),
        ('Пронизывание здания', 82),
    ],
    'Метаморфозы': [
        ('Преображение', 83),
    ],
    'Обливион': [
        ('Прах к праху', 87),
        ('Узреть оковы', 87),
        ('Покров теней', 87),
        ('Руки аримана', 88),
        ('Знамение смерти', 89),
        ('Призыв  тени', 89),
        ('Прорехи в саване', 89),
        ('Прорехи в саване', 90),
        ('Аура разложения', 90),
        ('Пир страстей', 90),
        ('Взгляд из тени', 91),
        ('Слуга тени', 91),
        ('Прикосновение тьмы', 91),
        ('Некро чума', 91),
        ('Покров стигии', 92),
        ('Шаг сквозь тень', 92),
        ('Обещание скульд', 93),
        ('Аватар тьмы', 93),
        ('Иссушение духа', 93),
    ],
    'Церемонии Обливиона': [
        ('Дар ложной жизни', 94),
        ('Призвание духа', 94),
        ('Слуга гомункул', 95),
        ('Подчинение духа', 96),
        ('Вселение духа', 96),
        ('Шаркающие орды', 97),
        ('Сковать дух', 98),
        ('Разорвать покров', 98),
        ('Благословление лазаря', 99),
        ('Шаг в бездну', 100),
    ],
    'Кровавое чародейство': [
        ('Искатель секретов', 100),
        ('Кровь аэгиса', 100),
    ],
    'Ритуалы кровавого чародейства': [
        ('Уничтожить страх перед огнем', 101),
        ('Запечатать клеймо', 101),
        ('Как туман по воде', 102),
        ('Калликс секретюс', 102),
        ('Усыпляющее прикосновение', 102),
        ('Пламя в крови', 102),
        ('Один с лезвием', 103),
        ('Праздник пепла', 103),
        ('Управляемое воспоминание', 103),
    ],
}
