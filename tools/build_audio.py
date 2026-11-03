#!/usr/bin/env python3
"""Генерация звуковых ассетов EchoesTwilightValley (Фаза 3).

Детерминированно создаёт звуковые ассеты мода:
- vinyl_crackle.wav — бесшовный луп винилового треска: щелчки с экспоненциальным
  decay, тёплый сетевой гул 50/100 Гц, лёгкое шипение, кроссфейд концов для лупа;
- last_tram.wav — ночной эмбиент пасхалки «Последний трамвай»: далёкий гудок
  (нечётные обертоны, медленная атака), низкий гул рельсов и тихие удаляющиеся
  стуки колёс, затухание в тишину сумеречной долины.

Использование:  python3 tools/build_audio.py
Заменяет существующие файлы. Авторские музыкальные треки (ogg) добавляются
вручную звукорежиссёром — этот скрипт покрывает только эмбиент-заглушки.
"""
import math
import os
import random
import struct
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(ROOT, "EchoesTwilightValley", "assets", "Audio")

SAMPLE_RATE = 44100
SEED = 42


def write_wav(path: str, samples: list[float]) -> None:
    """Сохраняет нормализованные сэмплы [-1..1] как mono 16-bit PCM WAV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    frames = b"".join(
        struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples
    )
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(frames)


def render_vinyl(duration_s: float = 2.0) -> list[float]:
    rng = random.Random(SEED)
    n = int(SAMPLE_RATE * duration_s)
    fade = int(SAMPLE_RATE * 0.05)
    out: list[float] = []
    prev = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        crackle = 0.0
        if rng.random() < 0.0015:  # редкие щелчки иглы
            crackle = rng.choice((-1, 1)) * rng.uniform(0.5, 0.9)
        hum = 0.06 * math.sin(2 * math.pi * 50 * t) + 0.03 * math.sin(2 * math.pi * 100 * t)
        hiss = (rng.random() * 2 - 1) * 0.02
        prev = crackle * 0.8 + prev * 0.2
        s = prev + hum + hiss
        w = 1.0
        if i < fade:
            w = i / fade
        elif i > n - fade:
            w = (n - i) / fade
        out.append(s * w * 0.7)
    return out


def render_last_tram(duration_s: float = 6.0) -> list[float]:
    """Ночной эмбиент: гудок трамвая ~220/330 Гц с медленной атакой и длинным
    спадом, низкий гул рельсов 55 Гц, редкие приглушённые стуки колёс,
    общий затухающий хвост — трамвай «уходит» в туман."""
    rng = random.Random(SEED + 1)
    n = int(SAMPLE_RATE * duration_s)
    out: list[float] = []
    click_env = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        # Гудок: два нечётных обертонa, появляется на t=0.6 c, плавно тонет к концу.
        horn = 0.0
        if t > 0.6:
            a_in = min(1.0, (t - 0.6) / 1.2)          # медленная атака 1.2 c
            a_out = max(0.0, 1.0 - (t - 0.6) / 5.0)   # долгий спад
            env = a_in * a_out * a_out
            horn = env * (0.30 * math.sin(2 * math.pi * 220 * t)
                           + 0.12 * math.sin(2 * math.pi * 330 * t)
                           + 0.05 * math.sin(2 * math.pi * 440 * t))
        rails = 0.05 * math.sin(2 * math.pi * 55 * t) * max(0.0, 1.0 - t / duration_s)
        if rng.random() < 0.004:  # удаляющиеся стуки колёс
            click_env = rng.uniform(0.25, 0.5) * max(0.0, 1.0 - t / duration_s)
        click_env *= 0.85
        hiss = (rng.random() * 2 - 1) * 0.015
        out.append((horn + rails + click_env + hiss) * 0.8)
    return out


def main() -> None:
    write_wav(os.path.join(AUDIO_DIR, "vinyl_crackle.wav"), render_vinyl())
    print("OK: vinyl_crackle.wav (2.0s, mono, 44100 Hz)")
    write_wav(os.path.join(AUDIO_DIR, "last_tram.wav"), render_last_tram())
    print("OK: last_tram.wav (6.0s, mono, 44100 Hz)")


if __name__ == "__main__":
    main()
