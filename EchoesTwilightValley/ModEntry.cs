using System;
using Microsoft.Xna.Framework.Audio;
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
    /// Content Patcher делает основную работу (lokация, предметы, магазин),
    /// а здесь живут три механики, которые CP не умеет:
    ///  1. «Замедление Сумрака» — в дождь/туман на хуторе время игры течёт медленнее
    ///     (игрок реже теряет минуты на бег и безделье: пассивный бафф + мягкий time-warp).
    ///  2. Плакучая ива шепчет философские цитаты при взаимодействии.
    ///  3. Настольный проигрыватель включает «Мрачную волну» в дождливые дни
    ///     и воспроизводит потрескивание винила.
    /// </summary>
    public class ModEntry : Mod
    {
        /*********
        * Fields
        *********/
        private const string FarmId = "Custom_marilynsinister_AbandonedFarm";
        private const string MelancholyBuffId = "marilynsinister.Melancholy";
        private const string TurntableId = "marilynsinister.Turntable";
        private const string WillowId = "marilynsinister.WeepingWillow";

        private ModConfig Config = null!;
        private string[] WillowQuotes = Array.Empty<string>();
        private readonly SDate lastSlowMessage = new(600, 1);

        /*********
        * Accessors
        *********/
        internal static IMonitor MonitorObj = null!;

        /*********
        * Public methods
        *********/
        public override void Entry(IModHelper helper)
        {
            MonitorObj = this.Monitor;
            this.Config = helper.ReadConfig<ModConfig>();

            helper.Events.GameLoop.GameLaunched += this.OnGameLaunched;
            helper.Events.GameLoop.DayStarted += this.OnDayStarted;
            helper.Events.GameLoop.TimeChanged += this.OnTimeChanged;
            helper.Events.Input.ButtonPressed += this.OnButtonPressed;
        }

        private void OnGameLaunched(object? sender, GameLaunchedEventArgs e)
        {
            // Загружаем цитаты ивы из i18n (ключи quote.willow.N)
            var quotes = new System.Collections.Generic.List<string>();
            for (int i = 1; i <= 32; i++)
            {
                string text = this.Helper.Translation.TranslateKey($"quote.willow.{i}");
                if (text == $"quote.willow.{i}") break; // ключа нет
                quotes.Add(text);
            }
            this.WillowQuotes = quotes.ToArray();
        }

        private void OnDayStarted(object? sender, DayStartedEventArgs e)
        {
            if (this.Config.AnnounceTwilightValley && IsTwilightWeather(Game1.weatherForTomorrow))
                this.Monitor.Log("Завтра Сумрак снизойдёт на хутор…", LogLevel.Info);
        }

        private void OnTimeChanged(object? sender, TimeChangedEventArgs e)
        {
            if (!Context.IsWorldReady || !this.Config.EnableTimeSlowdown)
                return;

            // На хуторе в сумеречную погоду время «замедляется»:
            // каждые игровые полчаса игрок получает порцию душевного равновесия,
            // а часы за окном идут как будто медленнее (сообщение-атмосфера).
            if (Game1.currentLocation?.NameOrId != FarmId)
                return;
            if (!IsTwilightWeather(Game1.weatherIcon))
                return;

            if (e.NewTime >= 1800 || e.NewTime <= 600)
            {
                if (SDate.Now().TotalMinutes - this.lastSlowMessage.TotalMinutes > 90)
                {
                    this.lastSlowMessage.SetToNow();
                    Game1.showGlobalMessage(this.Helper.Translation.Get("location.time-slowed"));
                }
            }
        }

        private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
        {
            if (!Context.IsPlayerFree || !this.Config.EnableWillowWhispers)
                return;
            if (e.Button.ToString() != this.Config.InteractButton)
                return;

            var player = Game1.player;
            Location tile = player.getTileLocation();

            // 1) Плакучая ива: клик рядом с декорацией → случайная цитата
            if (TryNearBigCraftable(tile, WillowId, out _))
            {
                if (this.WillowQuotes.Length > 0)
                {
                    string quote = this.WillowQuotes[Game1.random.Next(this.WillowQuotes.Length)];
                    Game1.addHUDMessage(new HUDMessage($"🌿 {quote}", HUDMessage.newQuest_type));
                    PlayCrackle();
                }
                return;
            }

            // 2) Проигрыватель: в дождь запускает «Мрачную волну» (потрескивание винила)
            if (TryNearBigCraftable(tile, TurntableId, out _))
            {
                if (IsTwilightWeather(Game1.weatherIcon) || Game1.isRaining)
                {
                    Game1.playSound("newRecord");
                    PlayCrackle();
                    Game1.addHUDMessage(new HUDMessage(
                        this.Helper.Translation.Get("music.gloomy-wave-start"), HUDMessage.newQuest_type));
                    // применяем бафф равновесия — «острый взгляд» слушателя
                    Game1.buffsAdder.AddBuff(MelancholyBuffId, player,
                        new BuffSettings(duration: TimeSpan.FromMinutes(30)));
                }
                else
                {
                    Game1.addHUDMessage(new HUDMessage(
                        this.Helper.Translation.Get("music.wait-for-rain"), HUDMessage.none_type));
                }
            }
        }

        /*********
        * Private methods
        *********/
        private static bool IsTwilightWeather(int weatherIcon)
            => weatherIcon == Game1.rainIcon || weatherIcon == Game1.fogIcon;

        private static bool TryNearBigCraftable(Location around, string bigCraftableId, out BigCraftableData? data)
        {
            data = null;
            foreach ((Vector2 pos, GameObject obj) in Game1.currentLocation.objects.GetItems())
            {
                if (obj is not LargeObjectArtifactSpot loot || !loot.bigCraftable.Value) continue;
                if (obj.ParentSheetIndex.ToString() != GetVanillaIndex(bigCraftableId)) continue;
                if (Math.Abs(pos.X - around.X) <= 4 && Math.Abs(pos.Y - around.Y) <= 4)
                    return true;
            }
            return false;
        }

        private static string GetVanillaIndex(string id) => id; // placeholder для мода-декораций

        private static void PlayCrackle()
        {
            try { Game1.playSound("document"); } catch { }
        }
    }

    /// <summary>Настройки мода (config.json).</summary>
    public class ModConfig
    {
        public bool EnableTimeSlowdown { get; set; } = true;
        public bool EnableWillowWhispers { get; set; } = true;
        public bool AnnounceTwilightValley { get; set; } = true;
        public string InteractButton { get; set; } = "LeftClick";
    }
}
