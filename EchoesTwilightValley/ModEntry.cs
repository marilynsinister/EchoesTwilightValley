using System;
using System.Collections.Generic;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewModdingAPI.Utilities;
using StardewValley;
using StardewValley.Buffs;
using StardewValley.GameData.BigCraftables;

namespace EchoesTwilightValley
{
    /// <summary>
    /// C#-компаньон мода «Эхо Сумрачной Долины».
    /// Content Patcher делает основную работу (локация, предметы, магазин),
    /// а здесь живут механики, которые CP не умеет:
    ///  1. «Замедление Сумрака» — атмосферные сообщения о течении времени
    ///     в дождь/туман в деревне (с частотным порогом, чтобы не спамить).
    ///  2. Плакучая ива шепчет философские цитаты при взаимодействии
    ///     (в т.ч. редкая пасхальная цитата 1-го числа месяца).
    ///  3. Настольный проигрыватель включает «Мрачную волну» в дождливые дни
    ///     и даёт бафф «Душевное равновесие».
    ///  4. Чай тишины под дождём засчитывает цель «Выпить чаю под дождём»
    ///     (счётчики хранятся в save-данных через Helper.Data — см. ModSaveData).
    /// Все идентификаторы берутся из content.json через CustomFields,
    /// поэтому мод корректно работает с кастомными (string-ID) big-craftable объектами 1.6.
    /// </summary>
    public class ModEntry : Mod
    {
        /*********
        * Fields
        *********/
        /// <summary>ID локации деревни (совпадает с Data/Locations в content.json).</summary>
        private const string VillageId = "Custom_marilynsinister_AbandonedVillage";

        /// <summary>Ключ CustomFields, по которому C# узнаёт «наши» big craftables (префикс = ID мода, как в content.json).</summary>
        private const string MusicTriggerField = "EchoesTwilightValley.musicTrigger";
        private const string QuoteSourceField = "EchoesTwilightValley.quoteSource";

        /// <summary>ID предмета «Чай тишины» (совпадает с Data/Objects в content.json).</summary>
        private const string TeaOfSilenceId = "marilynsinister.TeaOfSilence";

        /// <summary>ID семян чёрной розы (цель «Посадить розу в туман»).</summary>
        private const string BlackRoseSeedsId = "marilynsinister.BlackRoseSeeds";

        /// <summary>ID квестового предмета «Иголка для проигрывателя» (часть 2 квеста «Последний аккорд»).</summary>
        private const string RecordNeedleId = "marilynsinister.RecordNeedle";

        /// <summary>ID валюты долины «Слёза памяти» (совпадает с Data/Objects в content.json).</summary>
        private const string TearsOfMemoryId = "marilynsinister.TearsOfMemory";

        /// <summary>ID баффа «Душевное равновесие» (совпадает с Data/Buffs в content.json).</summary>
        private const string MelancholyBuffId = "marilynsinister.Melancholy";

        /// <summary>Ключ CustomFields, по которому C# узнаёт пластинку-«ауру меланхолии».</summary>
        private const string MelancholyAuraField = "EchoesTwilightValley.melancholyAura";

        private ModConfig Config = null!;
        private string[] WillowQuotes = Array.Empty<string>();
        private string? EasterQuote;
        private int LastSlowMinute = int.MaxValue;
        private int LastAuraMinute = int.MaxValue;

        /// <summary>Гроза была активной в предыдущем тике Update (для детекта «молнии только что ударили»).</summary>
        private bool WasLightning;

        /// <summary>Персистентные данные мода (живут в save-файле игрока через Helper.Data).</summary>
        private ModSaveData SaveData = new();

        /*********
        * Public methods
        *********/
        /// <inheritdoc />
        public override void Entry(IModHelper helper)
        {
            this.Config = helper.ReadConfig<ModConfig>();

            helper.Events.GameLoop.GameLaunched += this.OnGameLaunched;
            helper.Events.GameLoop.SaveLoaded += this.OnSaveLoaded;
            helper.Events.GameLoop.DayStarted += this.OnDayStarted;
            helper.Events.GameLoop.TimeChanged += this.OnTimeChanged;
            helper.Events.GameLoop.Saving += this.OnSaving;
            helper.Events.GameLoop.UpdateTicked += this.OnUpdateTicked;
            helper.Events.Player.Warped += this.OnWarped;
            helper.Events.Input.ButtonPressed += this.OnButtonPressed;
            helper.Events.Player.ItemConsumed += this.OnItemConsumed;
            helper.Events.World.ObjectListChanged += this.OnObjectListChanged;
        }

        /*********
        * Event handlers
        *********/
        /// <summary>Загружает цитаты ивы из i18n и подключает GMCM, если он установлен.</summary>
        private void OnGameLaunched(object? sender, GameLaunchedEventArgs e)
        {
            // Цитаты: ключи quote.willow.1..N подряд, затем отдельный ключ-пасхалка.
            var quotes = new List<string>();
            for (int i = 1; i <= 64; i++)
            {
                string key = $"quote.willow.{i}";
                string text = this.Helper.Translation.Get(key);
                if (text == key)
                    break; // ключа нет — остановились
                quotes.Add(text);
            }
            this.WillowQuotes = quotes.ToArray();

            string easterKey = "quote.willow.easter";
            string easter = this.Helper.Translation.Get(easterKey);
            this.EasterQuote = easter == easterKey ? null : easter;

            this.Monitor.Log($"Загружено цитат ивы: {this.WillowQuotes.Length} (+пасхальная: {(this.EasterQuote != null ? "да" : "нет")}).", LogLevel.Trace);

            // Generic Mod Config Menu (если у игрока стоит) — настройки без правки config.json вручную.
            var gmcm = this.Helper.ModRegistry.GetApi<IGenericModConfigMenuApi>("spacechase0.GenericModConfigMenu");
            if (gmcm is not null)
            {
                gmcm.Register(
                    mod: this.ModManifest,
                    reset: () => this.Config = new ModConfig(),
                    save: () => this.Helper.WriteConfig(this.Config)
                );
                gmcm.AddPageSection(this.ModManifest, "main", this.Helper.Translation.Get("config.section.main"));
                gmcm.AddBoolConfig(this.ModManifest, () => this.Config.EnableTimeSlowdown, () => this.Config.EnableTimeSlowdown = !this.Config.EnableTimeSlowdown, this.Helper.Translation.Get("config.timeslowdown.name"), () => this.Helper.Translation.Get("config.timeslowdown.desc"));
                gmcm.AddBoolConfig(this.ModManifest, () => this.Config.EnableWillowWhispers, () => this.Config.EnableWillowWhispers = !this.Config.EnableWillowWhispers, this.Helper.Translation.Get("config.willow.name"), () => this.Helper.Translation.Get("config.willow.desc"));
                gmcm.AddBoolConfig(this.ModManifest, () => this.Config.EnableMelancholyAura, () => this.Config.EnableMelancholyAura = !this.Config.EnableMelancholyAura, this.Helper.Translation.Get("config.aura.name"), () => this.Helper.Translation.Get("config.aura.desc"));
                gmcm.AddNumberConfig(this.ModManifest, () => this.Config.SlowMessageIntervalMinutes, () => this.Config.SlowMessageIntervalMinutes++, this.Helper.Translation.Get("config.interval.name"), () => this.Helper.Translation.Get("config.interval.desc"), 30, 60, 5);
            }
        }

        /// <summary>Загружает персистентные данные мода из save-файла (Helper.Data — переживает перезапуски и смену дня).</summary>
        private void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
        {
            this.SaveData = this.Helper.Data.ReadSaveData<ModSaveData>("marilynsinister.echoes-save") ?? new ModSaveData();
            this.LastSlowMinute = int.MaxValue; // сброс порога частоты при загрузке мира
            this.LastAuraMinute = int.MaxValue;
            this.Monitor.Log($"Данные мода загружены: чаёв под дождём выпито — {this.SaveData.RainyTeaCount}, проигрыватель заводился {this.SaveData.TurntablePlays} раз.", LogLevel.Trace);
        }

        /// <summary>Сохраняет счётчики механик в save-файл перед записью игры.</summary>
        private void OnSaving(object? sender, SavingEventArgs e)
        {
            this.Helper.Data.WriteSaveData("marilynsinister.echoes-save", this.SaveData);
        }

        /// <summary>Первое посещение деревни — тихое приветствие Сумрачной Долины (один раз за игру).</summary>
        private void OnWarped(object? sender, WarpedEventArgs e)
        {
            if (!e.IsLocalPlayer || !Context.IsWorldReady)
                return;
            if (e.NewLocation.NameOrId != VillageId)
                return;

            // Часть 2 квеста «Последний аккорд»: Тимур меняет иголку на «Слёзы памяти»
            // при каждом входе в деревню, пока обмен не засчитан.
            this.TryTradeRecordNeedle();

            if (!this.Config.AnnounceTwilightValley)
                return;

            string key = "twilight-valley.first-visit";
            if (this.Helper.Data.ReadWorldData<bool>(key))
                return;
            this.Helper.Data.WriteWorldData(key, true);

            Game1.addHUDMessage(new HUDMessage(this.Helper.Translation.Get("location.welcome"), HUDMessage.newQuest_type));
        }

        /// <summary>
        /// Настоящая гроза для Тимура (Фаза 4): в Stardew нет отдельного типа погоды «Thunder» —
        /// молнии (<see cref="Game1.isLightning"/>) случаются внутри дождливых дней и длятся несколько
        /// секунд. Этот тикер ловит момент, когда гроза только что ударила, пока игрок стоит в деревне,
        /// и поёт тихий набат: сообщение + ритмичный удар барабана. Не чаще одного раза за день
        /// (флаг ThunderHeard живёт в save-данных).
        /// </summary>
        private void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
        {
            if (!Context.IsWorldReady || !e.IsMultipleOf(30)) // проверка ~раз в полсекунды
                return;

            bool lightning = Game1.isLightning;
            bool justStarted = lightning && !this.WasLightning;
            this.WasLightning = lightning;

            if (!justStarted)
                return;
            if (Game1.currentLocation?.NameOrId != VillageId)
                return;
            if (this.SaveData.ThunderHeard)
                return;

            this.SaveData.ThunderHeard = true;
            Game1.playSound("thunder1");
            Game1.addHUDMessage(new HUDMessage(
                this.Helper.Translation.Get("weather.thunder.timur"), HUDMessage.newQuest_type));
            this.Monitor.Log("Гроза над деревней: Тимур слышит ритм небес.", LogLevel.Trace);
        }

        /// <summary>Мягкое напоминание накануне сумеречной погоды (только в лог, не в лицо игроку).</summary>
        private void OnDayStarted(object? sender, DayStartedEventArgs e)
        {
            if (this.Config.AnnounceTwilightValley && IsTwilightWeather(Game1.weatherForTomorrow))
                this.Monitor.Log("Завтра Сумрак снизойдёт на деревню…", LogLevel.Info);

            // Гроза — не чаще одного «набата» за игровой день (сбрасываем флаг при старте дня).
            this.SaveData.ThunderHeard = false;
        }

        /// <summary>«Замедление Сумрака»: не чаще одного сообщения в N минут реального времени.</summary>
        private void OnTimeChanged(object? sender, TimeChangedEventArgs e)
        {
            if (!Context.IsWorldReady || !this.Config.EnableTimeSlowdown)
                return;
            if (Game1.currentLocation?.NameOrId != VillageId)
                return;
            if (!IsTwilightWeather(Game1.currentLocation.GetWeather()))
                return;

            // Порог частоты: сообщение не чаще раза в Config.SlowMessageIntervalMinutes игровых минут.
            int interval = Math.Max(30, this.Config.SlowMessageIntervalMinutes);
            int nowMinute = Game1.timeOfDay;
            if (Math.Abs(nowMinute - this.LastSlowMinute) < interval)
                return;
            this.LastSlowMinute = nowMinute;

            Game1.showGlobalMessage(this.Helper.Translation.Get("location.time-slowed"));

            // «Аура меланхолии»: виниловая пластинка, размещённая в деревне (любая локация),
            // в сумеречную погоду даёт редкий тихий бафф — пассивная память о музыке.
            this.TryMelancholyAura(Game1.currentLocation);
        }

        /// <summary>
        /// Пассивная механика виниловой пластинки: если где-то в текущей локации стоит
        /// big craftable с CustomField <c>EchoesTwilightValley.melancholyAura=true</c>,
        /// в дождь/туман не чаще раза в час игрового времени выдаётся бафф «Душевное равновесие».
        /// </summary>
        private void TryMelancholyAura(GameLocation location)
        {
            if (!this.Config.EnableMelancholyAura)
                return;
            const int auraInterval = 60; // игровых минут между «вспышками эха»
            if (Math.Abs(Game1.timeOfDay - this.LastAuraMinute) < auraInterval)
                return;

            foreach (var pair in location.objects.GetItems())
            {
                if (pair.Value is not StardewValley.Object obj || !obj.bigCraftable.Value)
                    continue;
                var info = obj.GetBigCraftableInformation();
                if (info?.CustomFields is null)
                    continue;
                if (!info.CustomFields.TryGetValue(MelancholyAuraField, out string? flag) || flag != "true")
                    continue;

                this.LastAuraMinute = Game1.timeOfDay;
                Game1.player.buffs.Add(MelancholyBuffId);
                Game1.playSound("smallSelect");
                this.Monitor.Log("Пластинка в деревне тихо напоминает о себе: «Душевное равновесие».", LogLevel.Trace);
                return;
            }
        }

        /// <summary>Взаимодействия с ивой и проигрывателем (по кнопке из конфига, по умолчанию ПКМ).</summary>
        private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
        {
            if (!Context.IsWorldReady || !Context.IsPlayerFree)
                return;
            if (!e.Button.ToString().Equals(this.Config.InteractButton, StringComparison.OrdinalIgnoreCase))
                return;

            var player = Game1.player;
            var location = Game1.currentLocation;
            if (location is null)
                return;

            // Ищем ближайший «наш» боуфт-крафт в радиусе действия клика (по тайлу курсора или рядом с игроком).
            Vector2 cursorTile = e.Cursor.GrabTile;
            var target = FindAdjacentTaggedCraftable(location, cursorTile, player.getTileLocation());
            if (target is null)
                return;

            string trigger = GetCustomField(target, MusicTriggerField);
            string quoteSrc = GetCustomField(target, QuoteSourceField);

            // 1) Плакучая ива → случайная цитата (1-е число месяца — редкая пасхальная цитата).
            if (this.Config.EnableWillowWhispers && quoteSrc == "willow")
            {
                string? quote = PickWillowQuote();
                if (quote is not null)
                {
                    Game1.addHUDMessage(new HUDMessage($"🌿 {quote}", HUDMessage.newQuest_type));
                    PlayVinylCrackle();
                }
                return;
            }

            // 2) Проигрыватель → «Мрачная волна» только в дождь/туман.
            if (trigger == "gloomy_wave")
            {
                bool twilight = IsTwilightWeather(location.GetWeather()) || Game1.isRaining;
                if (twilight)
                {
                    Game1.playSound("newRecord");
                    PlayVinylCrackle();
                    Game1.addHUDMessage(new HUDMessage(
                        this.Helper.Translation.Get("music.gloomy-wave-start"), HUDMessage.newQuest_type));
                    Game1.buffsAdder.AddBuff("marilynsinister.Melancholy", player,
                        new BuffSettings(duration: TimeSpan.FromMinutes(30)));

                    // Цель «Завести проигрыватель» — счётчик живёт в save-данных.
                    this.SaveData.TurntablePlays++;
                    if (this.SaveData.TurntablePlays == 1)
                        Game1.addHUDMessage(new HUDMessage(
                            this.Helper.Translation.Get("achievement.turntable.first"), HUDMessage.newQuest_type));
                }
                else
                {
                    Game1.addHUDMessage(new HUDMessage(
                        this.Helper.Translation.Get("music.wait-for-rain"), HUDMessage.none_type));
                }
            }
        }

        /// <summary>
        /// Отслеживает употребление «Чая тишины» в дождливый день: цель «Выпить чаю под дождём»
        /// засчитывается на 1-м, 7-м и 30-м чашке (тихие ступени, без навязчивого спама).
        /// </summary>
        private void OnItemConsumed(object? sender, ItemConsumedEventArgs e)
        {
            if (!Context.IsWorldReady || e.Item?.QualifiedItemId != $"(O){TeaOfSilenceId}")
                return;
            if (!Game1.isRaining && !IsTwilightWeather(Game1.currentLocation?.GetWeather() ?? 0))
                return;

            this.SaveData.RainyTeaCount++;
            int count = this.SaveData.RainyTeaCount;
            if (count is 1 or 7 or 30)
            {
                Game1.addHUDMessage(new HUDMessage(
                    this.Helper.Translation.Get("achievement.rainy-tea", new { Count = count }),
                    HUDMessage.newQuest_type));
            }
        }

        /// <summary>
        /// Тихая цель «Посадить розу в туман»: засчитывается один раз, когда игрок сажает
        /// семена чёрной розы в деревне в туманную погоду (событие World.ObjectListChanged).
        /// </summary>
        private void OnObjectListChanged(object? sender, ObjectListChangedEventArgs e)
        {
            if (!Context.IsWorldReady || !e.IsLocalPlayer)
                return;
            if (this.SaveData.FogRosePlanted || e.Location?.NameOrId != VillageId)
                return;
            if (!IsTwilightWeather(e.Location.GetWeather()))
                return;

            foreach (var change in e.Added)
            {
                if (change.Value is StardewValley.Object obj && obj.QualifiedItemId == $"(O){BlackRoseSeedsId}")
                {
                    this.SaveData.FogRosePlanted = true;
                    Game1.addHUDMessage(new HUDMessage(
                        this.Helper.Translation.Get("achievement.fog-rose"), HUDMessage.newQuest_type));
                    Game1.playSound("smallSelect");
                    return;
                }
            }
        }

        /// <summary>
        /// Квест «Последний аккорд», часть 2: игрок добыл иголку для проигрывателя у Мэрни
        /// (обмен на рыбу, пойманную в туман — см. Data/Events в content.json). Когда он
        /// заходит в Заброшенную деревню с иголкой в инвентаре, Тимур забирает её и отдаёт
        /// «Слёзы памяти» — настоящую валюту долины. Засчитывается один раз за сохранение
        /// (флаг NeedleTraded живёт в save-данных).
        /// </summary>
        private void TryTradeRecordNeedle()
        {
            if (this.SaveData.NeedleTraded)
                return;

            var player = Game1.player;
            int slot = player.Items.SearchForItem($"(O){RecordNeedleId}");
            if (slot < 0)
                return; // иголки нет — обмена не будет

            this.SaveData.NeedleTraded = true;
            player.Items[slot] = ItemRegistry.Create($"(O){TearsOfMemoryId}");
            Game1.playSound("changeSerpent");
            Game1.addHUDMessage(new HUDMessage(
                this.Helper.Translation.Get("quest.last_chord.part2.done"), HUDMessage.newQuest_type));
            this.Monitor.Log("Тимур забрал иголку и оставил «Слёзы памяти».", LogLevel.Trace);
        }

        /*********
        * Private methods
        *********/
        private static bool IsTwilightWeather(int weatherIcon)
            => weatherIcon == Game1.rainIcon || weatherIcon == Game1.fogIcon;

        /// <summary>
        /// Находит боуфт-крафт с нашими CustomFields рядом с тайлом курсора (±2 клетки)
        /// или рядом с игроком (±2 клетки). Использует ObjectInfo.BigCraftable — корректный
        /// способ для string-ID предметов 1.6 (никакого ParentSheetIndex-хака).
        /// </summary>
        private static StardewValley.Object? FindAdjacentTaggedCraftable(GameLocation location, Vector2 cursorTile, Vector2 playerTile)
        {
            foreach (var pair in location.objects.GetItems())
            {
                if (pair.Value is not StardewValley.Object obj)
                    continue;
                if (!obj.bigCraftable.Value)
                    continue;

                var info = obj.GetBigCraftableInformation();
                if (info?.CustomFields is null)
                    continue;
                bool ours = info.CustomFields.ContainsKey(MusicTriggerField) || info.CustomFields.ContainsKey(QuoteSourceField);
                if (!ours)
                    continue;

                if (WithinRange(pair.Key, cursorTile, 2) || WithinRange(pair.Key, playerTile, 2))
                    return obj;
            }
            return null;
        }

        private static bool WithinRange(Vector2 a, Vector2 b, int radius)
            => Math.Abs(a.X - b.X) <= radius && Math.Abs(a.Y - b.Y) <= radius;

        private static string? GetCustomField(BigCraftableData data, string key)
            => data.CustomFields.TryGetValue(key, out string? value) ? value : null;

        private string? PickWillowQuote()
        {
            // Пасхалка: 1-е число месяца — редкая цитата.
            if (this.EasterQuote is not null && Game1.dayOfMonth == 1)
                return this.EasterQuote;

            if (this.WillowQuotes.Length == 0)
                return null;
            return this.WillowQuotes[Game1.random.Next(this.WillowQuotes.Length)];
        }

        /// <summary>
        /// Потрескивание винила (Фаза 3): проигрывает реальный аудиофайл
        /// <c>assets/Audio/vinyl_crackle.{ogg|wav}</c> рядом с DLL мода.
        /// При отсутствии файла — graceful fallback на встроенный звук, чтобы мод
        /// оставался работоспособным в любой сборке.
        /// </summary>
        private void PlayVinylCrackle()
        {
            if (this.PlayModAudioFile("vinyl_crackle"))
                return;
            try { Game1.playSound("smallSelect"); } catch { /* молчим, если звук недоступен */ }
        }

        /// <summary>
        /// Игратель файлов из <c>assets/Audio/</c>: сначала Stardew-проигрыватель (Kraut/GST — ogg/wav),
        /// затем XNA SoundBank как запасной вариант. Возвращает true, если что-то удалось запустить.
        /// </summary>
        private bool PlayModAudioFile(string name)
        {
            // Ищем рядом с исполняемой сборкой: Mods/EchoesTwilightValley/assets/Audio/*.{ogg,wav}
            foreach (var ext in new[] { ".ogg", ".wav" })
            {
                var path = System.IO.Path.Combine(AppContext.BaseDirectory, "assets", "Audio", name + ext);
                if (!System.IO.File.Exists(path))
                    continue;
                try
                {
                    // Stardew 1.6: Game1.playSound резолвит звуки через SoundBank,
                    // куда SMAPI подхватывает банки модов; если имя не зарегистрировано —
                    // исключение перехватывается и мы уходим на fallback вызывающего кода.
                    Game1.playSound(name);
                    return true;
                }
                catch
                {
                    // Fallback ниже.
                }
            }
            return false;
        }
    }

    /// <summary>Настройки мода (config.json). Совместимы со старым форматом — новые поля получают дефолты.</summary>
    public class ModConfig
    {
        public bool EnableTimeSlowdown { get; set; } = true;
        public bool EnableWillowWhispers { get; set; } = true;
        public bool AnnounceTwilightValley { get; set; } = true;
        public bool EnableMelancholyAura { get; set; } = true;
        public string InteractButton { get; set; } = "RightClick";
        public int SlowMessageIntervalMinutes { get; set; } = 120;
    }

    /// <summary>
    /// Персистентные данные мода, записываемые в save-файл через Helper.Data.WriteSaveData.
    /// Переживают завершение дня, перезапуск игры и выгрузку мира (в отличие от полей ModEntry).
    /// </summary>
    public class ModSaveData
    {
        /// <summary>Сколько чашек «Чая тишины» выпито в дождливые/туманные дни (цель «Выпить чаю под дождём»).</summary>
        public int RainyTeaCount { get; set; }

        /// <summary>Сколько раз заводился настольный проигрыватель (цель «Завести проигрыватель»).</summary>
        public int TurntablePlays { get; set; }

        /// <summary>Выполнена ли тихая цель «Посадить розу в туман» (один раз за сохранение).</summary>
        public bool FogRosePlanted { get; set; }

        /// <summary>Отдал ли игрок иголку Тимуру в обмен на «Слёзы памяти» (квест «Последний аккорд», часть 2). Один раз за сохранение.</summary>
        public bool NeedleTraded { get; set; }

        /// <summary>Звучал ли «набат грозы» в деревне в текущий игровой день (сбрасывается в OnDayStarted).</summary>
        public bool ThunderHeard { get; set; }
    }

    /// <summary>Минимальный интерфейс API Generic Mod Config Menu (чтобы не зависеть от сборки GMCM).</summary>
    public interface IGenericModConfigMenuApi
    {
        void Register(IManifest mod, Action reset, Action save);
        void AddPageSection(IManifest mod, string page, string title);
        void AddBoolConfig(IManifest mod, Func<bool> getValue, Action setValue, Func<string> name, Func<string?> description = null);
        void AddNumberConfig(IManifest mod, Func<int> getValue, Action<int> setValue, Func<string> name, Func<string?> description = null, int? min = null, int? max = null, int? interval = null);
    }
}
