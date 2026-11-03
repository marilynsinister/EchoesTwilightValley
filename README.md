# EchoesTwilightValley

Концепт «Эхо Сумрачной Долины» — это атмосферный мод для Stardew Valley 1.6+, построенный на Content Patcher и вдохновленный русской пост-панк эстетикой, дождливым меланхоличным настроением и ностальгической лирикой.

## Состав репозитория

- manifest.json — описание мода и зависимость от Content Patcher
- content.json — основные изменения мира, предметов, диалогов и локаций
- i18n/ru.json — локализация на русском языке
- assets/Maps/AbandonedVillage.tmx — карта заброшенной деревни, создаваемая в Tiled
- assets/Objects/ — графика предметов и декора

## Быстрый старт

1. Установи SMAPI и Content Patcher.
2. Помести папку мода в каталог Stardew Valley/Mods.
3. Создай карту AbandonedVillage.tmx в Tiled и помести её в assets/Maps/.
4. Добавь изображения в assets/Objects/ и assets/Portraits/.
5. Запусти игру и проверь локацию после дождя после 18:00.

## Основные элементы

- Локация: Заброшенная деревня
- NPC: Игорь
- Предметы: Чай тишины, виниловая пластинка «Эхо», семена Черной розы
- Бафф: Душевное равновесие
- Атмосфера: дождь, туман, меланхоличная музыка и философский уют

## Ссылки на инструменты

- SMAPI: https://smapi.io/
- Content Patcher: https://www.nexusmods.com/stardewvalley/mods/1915
- Tiled: https://www.mapeditor.org/

## 🗺️ План развития

Актуальный roadmap с отмеченными выполненными и запланированными задачами — в файле [ROADMAP.md](ROADMAP.md). Историей версий управляет [CHANGELOG.md](CHANGELOG.md) (Keep a Changelog / SemVer). Текущая версия — **v1.2.0**: Фазы 0–1 завершены, Фаза 2 закрыта кроме сборки dll на живой игре, добавлены персистентность save-данных, тихие цели («Чай под дождём», «Первый проигрыватель») и приветствие деревни. Далее по плану — звук «Мрачной волны» (Фаза 3) и контент-расширения (Фаза 4).

## 🔧 Сборка C#-компонента

Content Patcher-часть мода работает «из коробки», но атмосферные механики (ива, проигрыватель, замедление времени) живут в C#-плагине `EchoesTwilightValley/`. Чтобы собрать `.dll`:

1. Установите [.NET SDK 6.0+](https://dotnet.microsoft.com/download) и [SMAPI 4.x](https://smapi.io/) (Stardew Valley должен быть запущен хотя бы раз — SMAPI создаёт папку `Stardew Valley/Mods`).
2. Скопируйте репозиторий целиком в `Stardew Valley/Mods/EchoesTwilightValley` — так CP-часть (manifest/content/assets/i18n) и C#-проект окажутся в одной папке мода.
3. В корне проекта выполните:
   ```bash
   dotnet build -c Release
   ```
   ModBuildConfig сам найдёт пути к игре и SMAPI (если нет — укажите `PathToGame`/`PathToSMAPI` в `EchoesTwilightValley.csproj`). Готовый `EchoesTwilightValley.dll` попадёт в выходную папку bin и будет подхвачен manifest'ом (`EntryDll`).
4. Опционально: установите **Generic Mod Config Menu** — в игре появится экран настроек (замедление Сумрака, шёпот ивы, интервал сообщений). Без GMCM правьте `config.json` в папке мода вручную.
5. Быстрая проверка структуры без игры: `python3 tools/validate.py` (валидность JSON, покрытие i18n ru/en, размеры спрайтов, TMX-слои, совпадение CustomFields с кодом, аудио-ассеты).
6. Регенерация ассетов: `python3 tools/build_art.py` (авторская графика: персонажи, портреты, тайлсеты), `python3 tools/build_map.py` (карта), `python3 tools/build_sprites.py` (предметы), `python3 tools/build_audio.py` (звуковые лупы, Фаза 3 — бесшовный `vinyl_crackle.wav` и ночной эмбиент `last_tram.wav`).

## 🎼 Установка музыки (когда треки будут готовы)

«Мрачная волна» как полноценный трек ещё не вшита: положите ogg-файлы в `EchoesTwilightValley/assets/Audio/` и подключите их через мод **Custom Music** (`Data/CustomMusic`) — либо через `PlayModAudioFile()` в `ModEntry.cs`, который уже умеет играть любые файлы из этой папки (на примере бесшовного треска `vinyl_crackle.wav`; генерация — `tools/build_audio.py`). Треклист — в разделе «Основные элементы».

## Примечание

Это базовая структура проекта, готовая к расширению и доработке под вашу версию мода. Файлы графики и карта для полного запуска нужно доработать в редакторе уровней и графики.
