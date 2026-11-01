# Changelog — «Эхо Сумрачной Долины»

Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/), версионирование: [Semantic Versioning](https://semver.org/lang/ru/).

## [1.5.0] — 2026-11-02

### Добавлено
- **Фаза 3 — реальный audio-playback (v1)**: `PlayVinylCrackle()` в ModEntry.cs больше не ограничивается встроенным звуком-заглушкой — новый метод `PlayModAudioFile(name)` ищет `assets/Audio/{name}.{ogg,wav}` рядом с DLL мода и запускает воспроизведение; при отсутствии файла или ошибке резолва — корректный fallback на `smallSelect`, мод работоспособен в любой сборке. Треск винила теперь слышен и у Плакучей ивы, и при запуске проигрывателя.
- **Звуковой ассет**: `EchoesTwilightValley/assets/Audio/vinyl_crackle.wav` — бесшовный луп 2 с (mono, 44.1 кГц, 16-bit): щелчки с decay, сетевой гул 50/100 Гц, шипение, кроссфейд концов. Генерируется новым скриптом `tools/build_audio.py` (детерминированный seed).
- **csproj**: `Content Include="assets\Audio\**"` с `CopyToOutputDirectory="PreserveNewest"` — аудиокопия попадает в билд рядом с DLL; `<Version>` синхронизирован с manifest.json (1.5.0).
- Валидатор: `check_audio` — наличие звуковых файлов, подключение `PlayModAudioFile`/`vinyl_crackle` в C#, правило копирования в csproj и проверка RIFF/WAVE-заголовков каждого .wav.

### Исправлено
- ROADMAP: удалена опечатка (случайные CJK-иероглифы в строке о целях v1).

## [1.4.0] — 2026-11-01

### Добавлено
- **Гроза Тимура (Фаза 4, закрыто)**: C#-компаньон ловит момент первой молнии (`Game1.isLightning`, событие `GameLoop.UpdateTicked` с детектом фронта через `WasLightning`) и, если игрок стоит в Заброшенной деревне, включает «набат грозы» — HUD-сообщение `weather.thunder.timur` + звук `thunder1`. Не чаще одного раза за игровой день (флаг `ThunderHeard` в save-данных, сброс в `OnDayStarted`).
- **CP-слой грозы**: новое событие деревни `twelve twenty t/-5000 t Timur` (погодный ключ `t` = thunder) с репликой Тимура про барабаны; диалог-ключ `Thunder` у Тимура в `Data/NPCDialogue` («Гроза — это я разговариваю с небом. Палочками…»).
- Валидатор: новая проверка `check_thunder` — синхронизация C#-детекта молний, событийных заголовков с ключом `t`, диалога `Thunder` и i18n-ключа `weather.thunder.timur` (ru+en).

### Изменено
- content.json: 27 изменений (было 26); i18n: 72 ключа (было 71), покрытие ru/en 100%; manifest → 1.4.0.

## [1.3.0] — 2026-11-01

### Добавлено
- **Квест «Последний аккорд», часть 2**: два события у Мэрни (`Data/Events/Shop`) — зачин после `LastChordDone` (Мэрни отдаёт иголку за рыбу, пойманную в туман: `Conditions: (O)76 1` = Ling) и выдача квестового предмета `marilynsinister.RecordNeedle` с флагом `NeedleObtained`.
- **«Слёзы памяти» как настоящая валюта долины**: новый предмет `marilynsinister.TearsOfMemory` (Quest, non-giftable); в магазине Игоря саженец плакучей ивы теперь покупается за 2 слезы; Кола Джоджа сохранена на переходный период.
- **Обмен иголки в деревне (два пути)**: C#-компаньон при входе в деревню меняет иголку на слёзы (флаг `NeedleTraded` в save-данных, один раз за сохранение); CP-страховка — событие Тимура в дождь с магазином `marilynsinister.VillageExchange` (`Data/Shops/CatalogueEchoes`).
- Спрайты `TearsOfMemory.png` и `RecordNeedle.png` (16×16) в `tools/build_sprites.py`; `Portraits/Timur` (плейсхолдер из арта Игоря).
- Валидатор: сверка квестовых ID ModEntry.cs ↔ content.json, проверка `setFlag`-флагов событий против `When/HasFlag`, проверка предметов в `Conditions` событий, новые PNG в SPRITE_CHECKS.
- i18n (ru+en): `item.tears_of_memory(.desc)`, `item.record_needle(.desc)`, `quest.last_chord.part2.done` — итого 71 ключ, покрытие 100%.

### Изменено
- Переименование «хутор → деревня» везде: локация «Заброшенная деревня», карта `AbandonedVillage.tmx`, ID `Custom_marilynsinister_AbandonedVillage`, ключ `location.abandoned_village`, EN «Abandoned Village».
- content.json: 26 изменений (было 20).

## [1.2.0] — 2026-11-01

### Добавлено
- **Персистентность C#-компаньона**: счётчики механик (чаёв под дождём, запусков проигрывателя) сохраняются в save-файл через `Helper.Data.WriteSaveData` (`ModSaveData`); флаг первого посещения деревни — в world-data. Данные переживают завершение дня и перезапуск игры.
- **Тихие цели v1** (без внешнего мода Achievements): «Выпить чаю под дождём» (ступени 1/7/30 чашек, событие `Player.ItemConsumed`) и «Завести проигрыватель» (первый успешный запуск).
- **Приветствие деревни**: HUD-сообщение при первом warp на «Заброшенную деревню» (событие `Player.Warped`, один раз за игру).
- **`Data/Spaces`** в content.json: локация объявлена как открытое пространство (`IsOutdoors: true`) — погода (дождь/туман) и смена дня/ночи корректно работают в деревне.
- Валидатор `tools/validate.py`: новые проверки — синхронизация констант ModEntry.cs ↔ content.json ↔ i18n (ID локации, чая, баффа, CustomFields, ключи `Translation.Get`) и запрет дубликатов цитат ивы.
- i18n: ключи `location.welcome`, `achievement.rainy-tea`, `achievement.turntable.first` (ru + en).

### Исправлено
- Дубликат цитаты Плакучей ивы (`quote.willow.14` повторяла `quote.willow.8`) — заменена на новую.

## [1.1.1] — 2026-11-01

### Изменено
- ModEntry.cs переписан: взаимодействие с ивой/проигрывателем через `ObjectInfo` + CustomFields (удалён хрупкий ParentSheetIndex-хак), порог частоты сообщений «Замедления Сумрака», пасхальная цитата 1-го числа месяца, GMCM-экран настроек, XML-doc.
- content.json: плакучая ива получила `"Interactive": true`.
- i18n: цитаты ивы расширены до 16 + пасхальная; создан полный `en.json`; добавлены ключи `config.*`.
- Инструменты: автотест `tools/validate.py`, `.editorconfig`.
- README: разделы «Сборка C#-компонента» и «Установка музыки».

## [1.1.0] — 2026-11-01

### Добавлено
- Карта `assets/Maps/AbandonedVillage.tmx` (40×40) с генератором `tools/build_map.py`: все слои Stardew + интерактивные точки (колодец, скамейка, разбитое радио, ива).
- Спрайты корректных размеров + Characters/Portraits Игоря + культура чёрной розы (`tools/build_sprites.py`).
- Полный контент v1.1: бафф «Душевное равновесие», предметы (чай, роза, семена, пластинка, саженец, схема), big craftables, культура розы, рецепты (проигрыватель скрыт за флагом `LastChordDone`), магазин обмена Игоря, NPC-диалоги, события деревни, варп по погоде Rain/Fog.
- C#-компаньон `EchoesTwilightValley/` (csproj + ModEntry): замедление времени, шёпот ивы, проигрыватель.

## [1.0.0] — 2026-11-01

### Добавлено
- Базовая структура Content Patcher: manifest, content.json (бафф, предметы, магазин, диалоги, карта, локация), ru.json, README-концепт.
