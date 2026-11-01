#!/usr/bin/env python3
"""Генерация звуковых ассетов EchoesTwilightValley (Фаза 3).

Детерминированно создаёт бесшовный луп винилового треска
(EchoesTwilightValley/assets/Audio/vinyl_crackle.wav): щелчки с экспоненциальным
decay, тёплый сетевой гул 50/100 Гц, лёгкое шипение, кроссфейд концов для лупа.

Использование:  python3 tools/build_audio.py
Заменяет существующий файл. Авторские музыкальные треки (ogg) добавляются
вручную звукорежиссёром — этот скрипт покрывает только эмбиент-заглушки.
"""
import math
import os
import random
import struct
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "EchoesTwilightValley", "assets", "Audio", "vinyl_crackle.wav")

SAMPLE_RATE = 44100
DURATION_S = 2.0
SEED = 42


def render() -> bytes:
    rng = random.Random(SEED)
    n = int(SAMPLE_RATE * DURATION_S)
    fade = int(SAMPLE_RATE * 0.05)
    out = bytearray()
    prev = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        crackle = 0.0
        if rng.random() < 0.0015:  # редкие щелчки иглы
            crackle = rng.choice((-1, 1)) * rng.uniform(0.5, 0.9)
        hum = 0.06 * math.sin(2 * math.pi * 50 * t) + 0.03 * math.sin(2 * math.pi * 100 * t)
        hiss = (rng.random() * 2 - 1) * 0.02
        prev = crackle * 0.8 + prev * 0.2
        s = max(-1.0, min(1.0, prev + hum + hiss))
        w = 1.0
        if i < fade:
            w = i / fade
        elif i > n - fade:
            w = (n - i) / fade
        out += struct.pack("<h", int(s * w * 32767 * 0.7))
    return bytes(out)


def main() -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with wave.open(OUT, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(render())
    print(f"OK: {os.path.relpath(OUT, ROOT)} ({DURATION_S}s, mono, {SAMPLE_RATE} Hz)")


if __name__ == "__main__":
    main()
