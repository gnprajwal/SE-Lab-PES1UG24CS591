"""Task 4: sound effects.

All sounds are synthesised in code when the game starts, so the project
needs no audio files and no extra dependencies (no numpy). If the computer
has no audio device the game still runs - it just stays silent.

Sounds:
    bounce   - short wooden "tock" when the marble hits a wall (louder for
               harder hits)
    goal     - rising arpeggio when the marble reaches the goal
    tick     - soft tick for each of the last 5 seconds
    timeout  - descending "wah-wah" when the timer runs out
"""
import array
import math
import random

import pygame

RATE = 44100


def _envelope(i, n, attack=0.004, decay=None):
    t = i / RATE
    a = min(1.0, t / attack) if attack > 0 else 1.0
    if decay is None:
        # linear fade-out over the last 20% so notes don't click
        tail = max(1, int(n * 0.2))
        d = min(1.0, (n - i) / tail)
    else:
        d = math.exp(-t / decay)
    return a * d


def _tone(freq, seconds, volume=0.5, decay=None, harmonics=((1, 1.0),), vibrato=0.0):
    n = int(RATE * seconds)
    out = []
    for i in range(n):
        t = i / RATE
        f = freq * (1 + vibrato * math.sin(2 * math.pi * 6 * t))
        s = sum(amp * math.sin(2 * math.pi * f * mult * t) for mult, amp in harmonics)
        out.append(s * volume * _envelope(i, n, decay=decay))
    return out


def _concat(*parts):
    out = []
    for p in parts:
        out.extend(p)
    return out


def _make_bounce():
    rng = random.Random(7)
    n = int(RATE * 0.07)
    out = []
    for i in range(n):
        t = i / RATE
        body = math.sin(2 * math.pi * 260 * t) * math.exp(-t / 0.018)
        click = (rng.random() * 2 - 1) * math.exp(-t / 0.003)
        out.append(0.55 * body + 0.25 * click)
    return out


def _make_goal():
    bright = ((1, 1.0), (2, 0.35), (3, 0.15))
    notes = [523.25, 659.25, 783.99]  # C5 E5 G5
    parts = [_tone(f, 0.09, 0.35, harmonics=bright) for f in notes]
    parts.append(_tone(1046.5, 0.45, 0.35, decay=0.18, harmonics=bright))  # C6
    return _concat(*parts)


def _make_tick():
    return _tone(1400, 0.035, 0.25, decay=0.008)


def _make_timeout():
    brass = ((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.15))
    return _concat(
        _tone(392.00, 0.22, 0.32, harmonics=brass),   # G4
        _tone(369.99, 0.22, 0.32, harmonics=brass),   # F#4
        _tone(349.23, 0.22, 0.32, harmonics=brass),   # F4
        _tone(329.63, 0.75, 0.32, harmonics=brass, vibrato=0.012),  # E4 (held)
    )


class SoundBank:
    def __init__(self):
        self.rate = RATE
        # mono float samples in [-1, 1]; kept so the sounds can be reused
        # (e.g. by a recorder) even when there is no audio device
        self.samples = {
            "bounce": _make_bounce(),
            "goal": _make_goal(),
            "tick": _make_tick(),
            "timeout": _make_timeout(),
        }
        self.muted = False
        self.sounds = {}
        self.enabled = self._init_mixer()
        if self.enabled:
            for name, data in self.samples.items():
                try:
                    self.sounds[name] = pygame.mixer.Sound(buffer=self._to_pcm(data))
                except pygame.error:
                    pass

    def _init_mixer(self):
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(RATE, -16, 1, 512)
            freq, fmt, channels = pygame.mixer.get_init()
        except pygame.error:
            return False
        if fmt not in (-16, 16):  # we only synthesise 16-bit audio
            return False
        self._mixer_rate, self._channels = freq, channels
        return True

    def _to_pcm(self, data):
        # resample (nearest) if the mixer runs at a different rate
        if self._mixer_rate != RATE:
            step = RATE / self._mixer_rate
            data = [data[int(i * step)] for i in range(int(len(data) / step))]
        pcm = array.array("h")
        for s in data:
            v = int(max(-1.0, min(1.0, s)) * 32000)
            pcm.extend([v] * self._channels)
        return pcm.tobytes()

    def play(self, name, volume=1.0):
        if self.muted:
            return
        snd = self.sounds.get(name)
        if snd is None:
            return
        snd.set_volume(max(0.0, min(1.0, volume)))
        snd.play()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted and self.enabled:
            pygame.mixer.stop()
