#!/usr/bin/env python3
"""Compose the intro's background music: calm felt piano + soft strings, 90 BPM.

Original, generated from code (no samples). Sections follow the video:
  0-6 s   pad + single piano notes      (hook)
  6-12 s  quarter-note arpeggio         (question, title)
  12-44 s eighth-note arpeggio, bass    (demos)
  44-56 s strings swell, higher octave  (numbers, spinner)
  56-63 s final chord, fade             (call to action)
Usage: python3 music.py [out.wav]
"""

import sys
import wave

import numpy as np

SR = 44100
DUR = 63.0
BPM = 90
BEAT = 60 / BPM
BAR = 4 * BEAT
N = int(SR * DUR)
rng = np.random.default_rng(7)

# Chords as MIDI notes (D major: Dmaj9 - Bm7 - Gmaj7 - Asus), two bars each.
CHORDS = [
    [50, 57, 61, 64, 66],  # Dmaj9
    [47, 54, 57, 62, 66],  # Bm7
    [43, 50, 54, 59, 62],  # Gmaj7
    [45, 52, 57, 59, 64],  # Asus2
]
FINAL = [38, 50, 57, 61, 64, 66, 69]  # Dmaj9, wide voicing


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def chord_at(t):
    return CHORDS[int(t // (2 * BAR)) % 4]


def piano(m, length=3.2, vel=1.0):
    """Felt-piano-like tone: a few partials, soft attack, exponential decay."""
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m)
    tone = np.zeros(n)
    for k, amp in enumerate([1.0, 0.42, 0.18, 0.08, 0.04], start=1):
        fk = f * k * (1 + 0.0004 * k * k)  # slight inharmonicity
        tone += amp * np.sin(2 * np.pi * fk * t) * np.exp(-t * (1.1 + 0.9 * k))
    attack = np.clip(t / 0.012, 0, 1)
    return vel * tone * attack


def pad(notes, start, end, level, octave=0, attack=2.5, release=2.5):
    """Soft sustained pad/strings: detuned sines with slow vibrato."""
    s, e = int(start * SR), min(N, int((end + release) * SR))
    t = np.arange(e - s) / SR
    out = np.zeros(e - s)
    for m in notes:
        f = hz(m + octave)
        for det in (-0.12, 0.0, 0.12):  # small detune in Hz for a chorus effect
            fd, rate, depth = f + det, 4.8 + det, 0.0025
            # Integrated phase of fd * (1 + depth*sin(2*pi*rate*t)): steady, gentle vibrato.
            phase = 2 * np.pi * fd * t - (fd * depth / rate) * np.cos(2 * np.pi * rate * t)
            out += np.sin(phase) + 0.25 * np.sin(2 * phase)
    env = np.clip(t / attack, 0, 1) * np.clip(((end - start) + release - t) / release, 0, 1)
    return s, level * out * env / (len(notes) * 3)


L = np.zeros(N)
R = np.zeros(N)


def add(sig, start, pan=0.0):
    s = int(start * SR)
    e = min(N, s + len(sig))
    if e <= s:
        return
    L[s:e] += sig[: e - s] * (1 - pan) / 2 * 2 ** 0.5
    R[s:e] += sig[: e - s] * (1 + pan) / 2 * 2 ** 0.5


# Pads: one per chord span, louder strings an octave up during 44-56 s.
t = 0.0
while t < 56.0:
    span_end = min(t + 2 * BAR, 56.0)
    notes = chord_at(t)
    s, sig = pad(notes, t, span_end, 0.20, attack=1.8, release=1.6)
    add(sig, t, pan=-0.15); add(sig, t, pan=0.15)
    if t >= 42.0:
        s, sig = pad(notes[1:], t, span_end, 0.16 if t < 50 else 0.20, octave=12, attack=3.0, release=2.0)
        add(sig, t, pan=0.3)
    t = span_end
s, sig = pad(FINAL, 56.0, DUR - 2.6, 0.24, attack=0.4, release=2.6)
add(sig, 56.0)

# Piano.
step = BEAT / 2
t = 0.0
i = 0
while t < 56.0 - 1e-6:
    notes = chord_at(t)
    upper = sorted({n + 12 for n in notes} | {n + 24 for n in notes if n + 24 <= 81})
    upper = [n for n in upper if 62 <= n <= 81]
    pattern = [0, 2, 1, 3, 2, 4, 3, 1]
    pos = i % 8
    if t < 6.0:
        play = pos == 0  # one note per bar
        note = upper[0]
    elif t < 12.0:
        play = pos % 2 == 0  # quarter notes
        note = upper[pattern[pos] % len(upper)]
    else:
        play = True
        octave = 12 if 44.0 <= t < 56.0 and pos in (3, 5) else 0
        note = upper[pattern[pos] % len(upper)] + octave
    if play:
        accent = 1.0 if pos == 0 else 0.78
        swell = 0.85 + 0.25 * np.clip((t - 30) / 20, 0, 1)
        vel = accent * (0.55 if t < 12 else swell) * rng.uniform(0.92, 1.05)
        add(piano(note, vel=vel * 0.32), t + rng.uniform(0, 0.008), pan=rng.uniform(-0.35, 0.35))
    # Bass on each bar from 12 s.
    if pos == 0 and 12.0 <= t:
        add(piano(notes[0], length=4.0, vel=0.20), t, pan=0.0)  # 98-147 Hz: warm, not boomy
    t += step
    i += 1

# Final piano chord at 56 s.
for k, m in enumerate(FINAL):
    add(piano(m, length=7.0, vel=0.24), 56.0 + k * 0.035, pan=(k - 3) * 0.08)

# Reverb: convolve with decaying stereo noise (FFT convolution).
ir_len = int(SR * 2.8)
tt = np.arange(ir_len) / SR
decay = np.exp(-tt * 2.4)
irL = rng.standard_normal(ir_len) * decay
irR = rng.standard_normal(ir_len) * decay
irL[: int(0.02 * SR)] = 0; irR[: int(0.025 * SR)] = 0  # pre-delay


def convolve(x, ir):
    n = len(x) + len(ir)
    size = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return y / np.max(np.abs(y) + 1e-9)


wet = 0.32
dryL, dryR = L / (np.max(np.abs(L)) + 1e-9), R / (np.max(np.abs(R)) + 1e-9)
outL = (1 - wet) * dryL + wet * convolve(L, irL)
outR = (1 - wet) * dryR + wet * convolve(R, irR)

# Gentle low-pass (one-pole) for warmth, fades, normalize to -3 dBFS.
def lowpass(x, cutoff=7000):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    # vectorized via lfilter-like recursion is not in numpy; use cumulative trick in chunks
    for j in range(len(x)):
        acc = (1 - a) * x[j] + a * acc
        y[j] = acc
    return y

time = np.arange(N) / SR
fade = np.clip(time / 1.5, 0, 1) * np.clip((DUR - time) / 2.5, 0, 1)
def highpass(x, cutoff=45):
    return x - lowpass(x, cutoff)


stereo = np.stack([highpass(lowpass(outL)) * fade, highpass(lowpass(outR)) * fade], axis=1)
stereo *= 10 ** (-3 / 20) / np.max(np.abs(stereo))

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype("<i2").tobytes())
print(f"wrote {out} ({DUR:.0f} s)")
