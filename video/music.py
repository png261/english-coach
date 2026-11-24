#!/usr/bin/env python3
"""Compose the intro's background music: upbeat piano, strings and light drums, 128 BPM.

Original, generated from code (no samples). One bar = 1.875 s, and the sections
land on the video's scene changes (video runs at 1.5x the 63 s scene timeline):
  0-3.75 s      pad + single piano notes            (hook)
  3.75-7.5 s    quarter-note arpeggio, hi-hat       (question, title)
  7.5-28.1 s    eighth-note arpeggio, bass, kick    (demos)
  28.1-37.5 s   peak: strings, octave lifts, 4-on-the-floor kick (numbers, spinner)
  37.5-42 s     final chord, drums stop             (logo + install)
Plus soft click sounds at the cursor clicks.
Usage: python3 music.py [out.wav]
"""

import sys
import wave

import numpy as np

SR = 44100
BPM = 128
BEAT = 60 / BPM
BAR = 4 * BEAT                 # 1.875 s
DUR = 45.0
N = int(SR * DUR)
INTRO, BUILD, PEAK, END = 2 * BAR, 4 * BAR, 15 * BAR, 20 * BAR   # 3.75, 7.5, 28.1, 37.5 s
rng = np.random.default_rng(7)

# D major: Dmaj9 - Bm7 - Gmaj7 - Asus2, two bars each.
CHORDS = [
    [50, 57, 61, 64, 66],
    [47, 54, 57, 62, 66],
    [43, 50, 54, 59, 62],
    [45, 52, 57, 59, 64],
]
FINAL = [38, 50, 57, 61, 64, 66, 69]

L = np.zeros(N)
R = np.zeros(N)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def chord_at(t):
    return CHORDS[int(t // (2 * BAR)) % 4]


def add(sig, start, pan=0.0):
    s = int(start * SR)
    e = min(N, s + len(sig))
    if e > s:
        L[s:e] += sig[: e - s] * (1 - pan) / 2 * 2 ** 0.5
        R[s:e] += sig[: e - s] * (1 + pan) / 2 * 2 ** 0.5


def piano(m, length=2.4, vel=1.0):
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m)
    tone = np.zeros(n)
    for k, amp in enumerate([1.0, 0.45, 0.2, 0.09, 0.05], start=1):
        tone += amp * np.sin(2 * np.pi * f * k * (1 + 0.0004 * k * k) * t) * np.exp(-t * (1.6 + 1.1 * k))
    return vel * tone * np.clip(t / 0.006, 0, 1)


def pad(notes, start, end, level, octave=0, attack=1.2, release=1.4):
    s, e = int(start * SR), min(N, int((end + release) * SR))
    t = np.arange(e - s) / SR
    out = np.zeros(e - s)
    for m in notes:
        f = hz(m + octave)
        for det in (-0.12, 0.0, 0.12):
            fd, rate, depth = f + det, 4.8 + det, 0.0025
            phase = 2 * np.pi * fd * t - (fd * depth / rate) * np.cos(2 * np.pi * rate * t)
            out += np.sin(phase) + 0.25 * np.sin(2 * phase)
    env = np.clip(t / attack, 0, 1) * np.clip(((end - start) + release - t) / release, 0, 1)
    return level * out * env / (len(notes) * 3)


def kick(vel=1.0):
    t = np.arange(int(SR * 0.35)) / SR
    freq = 50 + 90 * np.exp(-t * 28)                 # pitch drop 140 -> 50 Hz
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return vel * np.sin(phase) * np.exp(-t * 9) * np.clip(t / 0.002, 0, 1)


def hat(vel=1.0, length=0.06):
    n = int(SR * length)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = noise - np.concatenate([[0], noise[:-1]])  # crude high-pass
    return vel * noise * np.exp(-t * 70)


# Pads and strings.
t = 0.0
while t < END - 1e-6:
    span_end = min(t + 2 * BAR, END)
    notes = chord_at(t)
    sig = pad(notes, t, span_end, 0.18)
    add(sig, t, -0.15); add(sig, t, 0.15)
    if t >= PEAK - 2 * BAR:
        add(pad(notes[1:], t, span_end, 0.14 if t < PEAK else 0.2, octave=12, attack=2.0), t, 0.3)
    t = span_end
add(pad(FINAL, END, DUR - 2.0, 0.24, attack=0.15, release=2.0), END)

# Piano, bass, drums on an eighth-note grid.
pattern = [0, 2, 1, 3, 2, 4, 3, 1]
step = BEAT / 2
i, t = 0, 0.0
while t < END - 1e-6:
    notes = chord_at(t)
    upper = sorted({n + 12 for n in notes} | {n + 24 for n in notes if n + 24 <= 81})
    upper = [n for n in upper if 62 <= n <= 81]
    pos = i % 8
    if t < INTRO:
        play, note = pos == 0, upper[0]
    elif t < BUILD:
        play, note = pos % 2 == 0, upper[pattern[pos] % len(upper)]
    else:
        lift = 12 if t >= PEAK and pos in (3, 5, 7) else 0
        play, note = True, upper[pattern[pos] % len(upper)] + lift
    if play:
        accent = 1.0 if pos in (0, 4) else 0.75
        energy = 0.55 if t < BUILD else 0.85 + 0.2 * np.clip((t - BUILD) / (PEAK - BUILD), 0, 1)
        add(piano(note, vel=0.3 * accent * energy * rng.uniform(0.92, 1.05)),
            t + rng.uniform(0, 0.006), rng.uniform(-0.35, 0.35))
    if t >= BUILD:
        if pos == 0:
            add(piano(notes[0], length=3.0, vel=0.22), t)              # bass on the bar
        if pos == 4:
            add(piano(notes[0], length=1.5, vel=0.14), t)              # bass push on beat 3
        if pos in (0, 4) or (t >= PEAK and pos % 2 == 0):
            add(kick(0.55 if t < PEAK else 0.62), t)
        if pos % 2 == 1:
            add(hat(0.035 if t < PEAK else 0.05), t, 0.25)
        if t >= PEAK and pos in (2, 6):
            add(hat(0.03, 0.18), t, -0.2)                              # open hat on the off-beat
    elif t >= INTRO and pos % 2 == 1:
        add(hat(0.022), t, 0.25)
    t += step
    i += 1

# Final chord as the logo lands.
for k, m in enumerate(FINAL):
    add(piano(m, length=4.5, vel=0.24), END + k * 0.025, (k - 3) * 0.08)

# Soft UI click sounds where the cursor clicks in the video.
CLICKS = []  # no cursor in the kinetic version


def click():
    t = np.arange(int(SR * 0.05)) / SR
    body = np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 160)
    snap = rng.standard_normal(len(t)) * np.exp(-t * 600) * 0.5
    return 0.22 * (body + snap)


for c in CLICKS:
    add(click(), c, 0.1)

# Reverb (FFT convolution with decaying stereo noise).
ir_len = int(SR * 2.2)
decay = np.exp(-np.arange(ir_len) / SR * 3.0)
irL = rng.standard_normal(ir_len) * decay
irR = rng.standard_normal(ir_len) * decay
irL[: int(0.015 * SR)] = 0; irR[: int(0.02 * SR)] = 0


def convolve(x, ir):
    size = 1 << (len(x) + len(ir) - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return y / (np.max(np.abs(y)) + 1e-9)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for j in range(len(x)):
        acc = (1 - a) * x[j] + a * acc
        y[j] = acc
    return y


wet = 0.24
peak = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-9
outL = (1 - wet) * L / peak + wet * convolve(L, irL)
outR = (1 - wet) * R / peak + wet * convolve(R, irR)

time = np.arange(N) / SR
fade = np.clip(time / 0.4, 0, 1) * np.clip((DUR - time) / 2.0, 0, 1)
chans = []
for x in (outL, outR):
    x = lowpass(x, 9000)
    x = x - lowpass(x, 40)                                             # low-cut
    chans.append(x * fade)
stereo = np.stack(chans, axis=1)
stereo = np.tanh(stereo / np.max(np.abs(stereo)) * 1.4) / np.tanh(1.4)  # gentle saturation
stereo *= 10 ** (-1.5 / 20)

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype("<i2").tobytes())
print(f"wrote {out} ({DUR:.0f} s, {BPM} BPM)")
