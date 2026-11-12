# -*- coding: utf-8 -*-
"""
Original score + sound effects for LOS ÚLTIMOS, synthesised from scratch with
numpy (no samples, no third-party audio -> no licensing issues).

    python3 synth_audio.py            # writes assets/audio/sfx/*.wav and music/EPxx_score.wav

The same motif, drone key (D minor) and sound palette are used in all three
episodes so the series keeps one sonic identity.
"""
import os
import wave
import numpy as np

import series as S

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFX_DIR = os.path.join(ROOT, "assets", "audio", "sfx")
MUS_DIR = os.path.join(ROOT, "assets", "audio", "music")
RNG = np.random.default_rng(2042)


# ------------------------------------------------------------- helpers ----
def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def white(sec):
    return RNG.standard_normal(int(sec * SR))


def spectral(x, fn):
    """Filter x with a frequency-domain gain function fn(freqs)->gain."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    return np.fft.irfft(X * fn(f), n)


def bandpass(x, lo, hi, order=2.0):
    def g(f):
        f = np.maximum(f, 1e-3)
        lowcut = 1 / np.sqrt(1 + (lo / f) ** (2 * order)) if lo else 1.0
        highcut = 1 / np.sqrt(1 + (f / hi) ** (2 * order)) if hi else 1.0
        return lowcut * highcut
    return spectral(x, g)


def lowpass(x, hi, order=2.0):
    return bandpass(x, None, hi, order)


def highpass(x, lo, order=2.0):
    return bandpass(x, lo, None, order)


def pink(sec):
    return spectral(white(sec), lambda f: 1 / np.sqrt(np.maximum(f, 20)))


def brown(sec):
    return spectral(white(sec), lambda f: 1 / np.maximum(f, 15))


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def env_adsr(n, a, d, s_level, r):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    s = max(n - a - d - r, 0)
    e = np.concatenate([np.linspace(0, 1, a, endpoint=False) if a else [],
                        np.linspace(1, s_level, d, endpoint=False) if d else [],
                        np.full(s, s_level),
                        np.linspace(s_level, 0, r) if r else []])
    e = np.asarray(e, dtype=float)
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)))
    return e[:n]


def decay(n, tau):
    return np.exp(-np.arange(n) / SR / tau)


def smooth_noise(sec, rate_hz, seed=None):
    """Slowly varying random curve in [0,1] (for gusts, flicker...)."""
    rng = np.random.default_rng(seed) if seed is not None else RNG
    pts = max(int(sec * rate_hz) + 3, 4)
    y = rng.random(pts)
    x = np.linspace(0, sec, pts)
    t = t_axis(sec)
    v = np.interp(t, x, y)
    k = int(SR / rate_hz / 2) or 1
    v = np.convolve(v, np.ones(k) / k, mode="same")
    return (v - v.min()) / (v.max() - v.min() + 1e-9)


_IR_CACHE = {}


def reverb(x, seconds=2.0, mix=0.3, bright=4000):
    key = (seconds, bright)
    if key not in _IR_CACHE:
        n = int(seconds * SR)
        ir = RNG.standard_normal(n) * decay(n, seconds / 6.5)
        ir = lowpass(ir, bright)
        ir[: int(0.012 * SR)] = 0
        _IR_CACHE[key] = ir / np.sqrt(np.sum(ir ** 2))
    ir = _IR_CACHE[key]
    n = len(x) + len(ir)
    N = 1 << (n - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[: len(x) + len(ir)]
    out = np.pad(x, (0, len(ir))) * (1 - mix) + wet * mix
    return out


def to_stereo(x, width=0.0, pan=0.0):
    l = x * np.sqrt(0.5 * (1 - pan))
    r = x * np.sqrt(0.5 * (1 + pan))
    if width:
        d = int(width * 0.012 * SR)
        r = np.concatenate([np.zeros(d), r[:-d]]) if d else r
    return np.stack([l, r], axis=1) * np.sqrt(2)


def write_wav(path, x):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if x.ndim == 1:
        x = to_stereo(x)
    x = np.clip(x, -1, 1)
    data = (x * 32767).astype("<i2").tobytes()
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)


def read_wav(path):
    with wave.open(path, "rb") as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        a = np.frombuffer(w.readframes(n), dtype="<i2").astype(float) / 32767
    a = a.reshape(-1, ch)
    if ch == 1:
        a = np.repeat(a, 2, axis=1)
    if sr != SR:
        t_old = np.arange(len(a)) / sr
        t_new = np.arange(int(len(a) * SR / sr)) / SR
        a = np.stack([np.interp(t_new, t_old, a[:, c]) for c in range(2)], axis=1)
    return a


# ---------------------------------------------------------- sound atoms ----
def thump(freq=70, sec=0.25, tau=0.06, sweep=1.6):
    t = t_axis(sec)
    f = freq * (1 + (sweep - 1) * np.exp(-t / 0.02))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * decay(len(t), tau)


def tinkle(n_hits=6, sec=0.6, lo=2500, hi=7500):
    out = np.zeros(int(sec * SR))
    for _ in range(n_hits):
        st = RNG.integers(0, int(sec * SR * 0.6))
        f = RNG.uniform(lo, hi)
        ln = int(RNG.uniform(0.03, 0.12) * SR)
        t = np.arange(ln) / SR
        out[st:st + ln] += np.sin(2 * np.pi * f * t) * decay(ln, 0.025) * RNG.uniform(0.2, 0.6)
    return out


def metal_partials(freqs, sec=1.0, tau=0.35):
    t = t_axis(sec)
    x = sum(np.sin(2 * np.pi * f * t + RNG.uniform(0, 6)) * decay(len(t), tau * RNG.uniform(.6, 1.2))
            for f in freqs)
    return x / len(freqs)


def creak(sec=1.6, base=420, spread=1.0):
    """Stick-slip friction: an irregular impulse train through resonances."""
    n = int(sec * SR)
    x = np.zeros(n)
    rate = 30 + 60 * smooth_noise(sec, 3)
    phase = np.cumsum(rate) / SR
    idx = np.where(np.diff(np.floor(phase)) > 0)[0]
    x[idx] = RNG.uniform(0.5, 1.0, len(idx))
    body = sum(bandpass(x, f * 0.92, f * 1.08, 3) for f in (base, base * 2.13 * spread, base * 3.7 * spread))
    return body * env_adsr(n, 0.08, 0.1, 0.9, 0.3)


def footstep(grit=1.0):
    n = int(0.35 * SR)
    low = thump(95, 0.35, 0.045, 1.3)
    g = bandpass(white(0.35), 1800, 6000) * decay(n, 0.03) * 0.5 * grit
    return reverb(low * 0.9 + g, 0.6, 0.15)[:n]


def make_sfx():
    s = {}
    # beds (long, loopable enough for an episode)
    L = 60.0
    t = t_axis(L)
    gust = 0.35 + 0.65 * smooth_noise(L, 0.25, 1)
    wind = bandpass(pink(L), 120, 1400) * gust
    whistle = bandpass(white(L), 700, 1600, 4) * (smooth_noise(L, 0.4, 2) ** 3) * 0.25
    s["amb_wind"] = norm(wind + whistle, 0.5)

    rain = highpass(white(L), 1200) * 0.3 + bandpass(pink(L), 200, 900) * 0.4
    drops = np.zeros(len(t))
    for st in RNG.integers(0, len(t) - 2000, 4000):
        drops[st:st + 400] += np.sin(2 * np.pi * RNG.uniform(1500, 4000) * np.arange(400) / SR) \
            * decay(400, 0.004) * RNG.uniform(0.1, 0.5)
    s["amb_rain"] = norm(rain + drops * 0.6, 0.5)

    room = lowpass(brown(L), 300) * 0.5
    dr = np.zeros(len(t))
    for st in np.sort(RNG.integers(0, len(t) - 6000, 26)):
        n = 3000
        tt = np.arange(n) / SR
        f = 1400 * np.exp(-tt * 9) + 700
        dr[st:st + n] += np.sin(2 * np.pi * np.cumsum(f) / SR) * decay(n, 0.03) * RNG.uniform(.3, .8)
    s["amb_drip"] = norm(room + reverb(dr, 1.8, 0.45)[: len(t)] * 0.5, 0.45)

    hum = sum(np.sin(2 * np.pi * 60 * k * t) / k ** 1.4 for k in range(1, 7)) * 0.25
    s["amb_hum"] = norm(hum * (0.85 + 0.15 * smooth_noise(L, 0.5, 3)) + lowpass(brown(L), 250) * 0.4, 0.4)

    fans = bandpass(pink(L), 250, 3500) * 0.35
    s["amb_facility"] = norm(s["amb_hum"] * 0.8 + fans, 0.45)
    s["amb_cryo"] = norm(lowpass(brown(L), 180) * 0.6 + highpass(white(L), 5000) * 0.05
                         + np.sin(2 * np.pi * 47 * t) * 0.15, 0.4)

    # one-shots
    n = int(1.3 * SR)
    crack = (RNG.random(n) < 0.004) * RNG.uniform(-1, 1, n)
    s["static_burst"] = norm(bandpass(white(1.3), 300, 4500) * 0.6 + bandpass(crack, 800, 6000) * 3,
                             0.8) * env_adsr(n, 0.01, 0.1, 0.7, 0.6)
    tt = t_axis(1.6)
    sweep = np.sin(2 * np.pi * np.cumsum(900 + 700 * np.sin(2 * np.pi * 0.7 * tt)) / SR) * 0.25
    s["radio_tune"] = norm(sweep + bandpass(white(1.6), 400, 3500) * 0.4, 0.7) * env_adsr(len(tt), .05, .2, .8, .5)

    hb = np.zeros(int(2.6 * SR))
    for k in range(3):
        for off, a in ((0.0, 1.0), (0.28, 0.7)):
            st = int((k * 0.86 + off) * SR)
            b = thump(52, 0.3, 0.07, 1.4) * a
            hb[st:st + len(b)] += b
    s["heartbeat"] = norm(lowpass(hb, 200), 0.9)

    groan = creak(2.2, 180, 0.8)
    clunk = thump(48, 1.2, 0.25, 1.8)
    hatch = np.zeros(int(3.2 * SR))
    hatch[: len(groan)] += norm(groan, 0.6)
    st = int(2.0 * SR)
    hatch[st:st + len(clunk)] += clunk + metal_partials([310, 742, 1350], 1.2, 0.3) * 0.4
    s["hatch_open"] = norm(reverb(hatch, 1.5, 0.25)[: len(hatch)], 0.95)
    s["metal_creak"] = norm(reverb(creak(1.6, 520), 1.2, 0.3)[: int(1.6 * SR)], 0.7)
    s["door_creak"] = norm(reverb(creak(2.0, 690, 1.1), 1.8, 0.35)[: int(2.4 * SR)], 0.8)

    tt = t_axis(1.2)
    w = bandpass(white(1.2), 300, 2500) * np.sin(np.pi * tt / 1.2) ** 2
    s["whoosh"] = norm(reverb(w, 1.0, 0.3)[: len(tt)], 0.7)

    s["footstep"] = norm(footstep(), 0.8)
    fg = np.zeros(int(0.7 * SR))
    fs = footstep(1.4)
    fg[: len(fs)] += fs
    fg += tinkle(7, 0.7) * 0.5
    s["footstep_glass"] = norm(fg, 0.8)
    sp = bandpass(white(0.5), 400, 3500) * env_adsr(int(0.5 * SR), 0.005, 0.08, 0.3, 0.3)
    s["footstep_water"] = norm(sp + np.pad(footstep(), (0, int(0.15 * SR)))[: len(sp)] * 0.5, 0.7)

    clink = metal_partials([1180, 2730, 4310, 5890], 0.9, 0.18)
    s["can_pick"] = norm(clink + bandpass(white(0.9), 2000, 7000) * decay(int(0.9 * SR), 0.05) * 0.3, 0.7)
    tt = t_axis(1.8)
    roll = bandpass(white(1.8), 500, 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * tt) ** 2) * \
        np.linspace(1, 0.2, len(tt)) * 0.4
    roll += metal_partials([980, 2260], 1.8, 0.9) * 0.15
    stop = np.zeros(len(tt))
    c2 = metal_partials([1180, 2730, 4310], 0.4, 0.1)
    stop[int(1.35 * SR): int(1.35 * SR) + len(c2)] += c2 * 0.6
    s["can_roll"] = norm(reverb(roll + stop, 1.4, 0.3)[: len(tt)], 0.7)

    gc = tinkle(25, 0.8, 2000, 9000) + bandpass(white(0.8), 1500, 8000) * decay(int(0.8 * SR), 0.06) * 0.6
    s["glass_crunch"] = norm(reverb(gc, 1.2, 0.3)[: int(0.8 * SR)], 0.85)

    tt = t_axis(3.5)
    sub = np.sin(2 * np.pi * np.cumsum(32 + 60 * np.exp(-tt / 0.15)) / SR) * decay(len(tt), 1.0)
    noise_hit = lowpass(white(3.5), 1500) * decay(len(tt), 0.12)
    boom = reverb(sub + noise_hit * 0.5, 3.0, 0.35)[: len(tt)]
    s["boom_hit"] = norm(boom, 0.98)
    s["boom_soft"] = norm(lowpass(boom, 400), 0.7)
    th = lowpass(brown(4.5), 400) * env_adsr(int(4.5 * SR), 0.05, 0.6, 0.5, 3.0)
    th *= 0.4 + 0.6 * smooth_noise(4.5, 6, 9)
    s["thunder"] = norm(th, 0.9)

    cl = np.zeros(int(0.3 * SR))
    for st in (0, int(0.07 * SR)):
        c = highpass(white(0.02), 2000) * decay(int(0.02 * SR), 0.003)
        cl[st:st + len(c)] += c
    s["flashlight_click"] = norm(cl, 0.6)

    dh = np.zeros(int(3.6 * SR))
    cr = creak(2.6, 210, 0.9)
    dh[: len(cr)] += norm(cr, 0.7)
    th2 = thump(55, 1.0, 0.2, 1.5) + metal_partials([260, 590, 1110], 1.0, 0.4) * 0.4
    dh[int(2.5 * SR): int(2.5 * SR) + len(th2)] += th2
    s["door_heavy"] = norm(reverb(dh, 2.0, 0.3)[: len(dh)], 0.95)

    la = np.zeros(int(0.8 * SR))
    for st, a in ((0, 1.0), (int(0.18 * SR), 0.8)):
        c = metal_partials([1650, 3400, 5200], 0.25, 0.05) + highpass(white(0.25), 3000) * decay(int(.25 * SR), .01)
        la[st:st + len(c)] += c * a
    s["door_latch"] = norm(reverb(la, 1.0, 0.3)[: len(la)], 0.8)

    tt = t_axis(2.0)
    flick = (smooth_noise(2.0, 25, 4) > 0.45).astype(float)
    buzz = sum(np.sin(2 * np.pi * 120 * k * tt) / k for k in range(1, 9)) * flick * 0.3
    ping = metal_partials([2100, 4400], 0.5, 0.1)
    buzz[: len(ping)] += ping * 0.4
    s["fluorescent"] = norm(buzz, 0.6)

    pr = bandpass(white(1.2), 1500, 9000) * (smooth_noise(1.2, 30, 5) ** 2) * env_adsr(int(1.2 * SR), .02, .1, .8, .3)
    s["paper_rustle"] = norm(pr, 0.6)
    rp = bandpass(white(0.5), 1000, 8000) * (RNG.random(int(0.5 * SR)) ** 4) * env_adsr(int(.5 * SR), .01, .05, .9, .1)
    s["paper_rip"] = norm(rp, 0.6)

    tt = t_axis(4.0)
    drone = sum(np.sin(2 * np.pi * f * tt) for f in (36.7, 73.4, 110.2, 146.8)) / 4
    s["low_drone_swell"] = norm(drone * env_adsr(len(tt), 2.0, 0.5, 0.8, 1.4), 0.7)
    tt = t_axis(0.15)
    s["beep"] = norm(np.sin(2 * np.pi * 1320 * tt) * env_adsr(len(tt), .005, .01, .9, .03), 0.4)
    tt = t_axis(1.5)
    motor = np.sin(2 * np.pi * np.cumsum(40 + 90 * np.minimum(tt / 0.8, 1)) / SR) * 0.3
    s["tape_start"] = norm(thump(80, 1.5, 0.08) + motor * env_adsr(len(tt), .3, .1, .8, .4), 0.7)
    tt = t_axis(1.5)
    crt = thump(60, 1.5, 0.1) + np.sin(2 * np.pi * 7800 * tt) * 0.05 * decay(len(tt), 0.8) + \
        bandpass(white(1.5), 500, 5000) * decay(len(tt), 0.3) * 0.4
    s["crt_on"] = norm(crt, 0.7)
    tt = t_axis(3.0)
    s["cryo_hiss"] = norm(bandpass(white(3.0), 2500, 9000) * env_adsr(len(tt), 0.05, 0.4, 0.6, 1.5)
                          + lowpass(brown(3.0), 200) * 0.6, 0.7)
    tt = t_axis(3.0)
    al = np.sin(2 * np.pi * np.where((tt * 2.5) % 1 < 0.5, 660, 880) * tt) * \
        ((tt * 5) % 1 < 0.6) * 0.4
    s["alarm_soft"] = norm(reverb(al, 1.2, 0.3)[: len(tt)], 0.5)
    return s


# ---------------------------------------------------------------- score ----
NOTE = lambda midi: 440.0 * 2 ** ((midi - 69) / 12)

# D minor - Bb - Gm - A : the series' harmonic loop
CHORDS = [[50, 53, 57, 62], [46, 50, 53, 58], [43, 50, 55, 58], [45, 49, 52, 57]]
MOTIF = [74, 77, 73]   # D5 - F5 - C#5 : "la señal"


def pad_voice(freq, sec, detune=0.12):
    t = t_axis(sec)
    x = np.zeros(len(t))
    for d in (-detune, 0, detune):
        f = freq * 2 ** (d / 12)
        # soft saw (few harmonics)
        for k in range(1, 7):
            x += np.sin(2 * np.pi * f * k * t + RNG.uniform(0, 6)) / k ** 1.3
    return x / 18


def bell(freq, sec=3.0):
    t = t_axis(sec)
    mod = np.sin(2 * np.pi * freq * 3.5 * t) * 2.2 * decay(len(t), 0.5)
    return np.sin(2 * np.pi * freq * t + mod) * decay(len(t), 0.9) * env_adsr(len(t), 0.004, 0, 1, 0.05)


def motif(at_gain=1.0):
    out = np.zeros(int(4.5 * SR))
    for i, m in enumerate(MOTIF):
        b = bell(NOTE(m), 3.0) * at_gain
        st = int(i * 0.55 * SR)
        out[st:st + len(b)] += b
    return out


def place(buf, x, t, gain_db=0.0):
    st = int(t * SR)
    if st >= len(buf):
        return
    x = x[: len(buf) - st]
    buf[st:st + len(x)] += x * 10 ** (gain_db / 20)


def score(ep, sfx):
    cue = ep["music"]
    total = S.total_length(ep)
    end_card = cue["end_card"]
    n = int(total * SR)
    t = t_axis(total)
    L = np.zeros(n)

    # 1) drone: sub D + fifth, slowly breathing
    drone = (np.sin(2 * np.pi * NOTE(26) * t) * 0.55 + np.sin(2 * np.pi * NOTE(38) * t) * 0.35
             + np.sin(2 * np.pi * NOTE(45) * t) * 0.12)
    drone *= 0.75 + 0.25 * smooth_noise(total, 0.2, ep["num"])
    L += drone * 0.35

    # 2) pads: chord loop, 8 s per chord with long crossfades
    seg = 8.0
    k = 0
    while k * seg < total:
        ch = CHORDS[k % len(CHORDS)]
        sec = seg + 3.0
        p = sum(pad_voice(NOTE(m), sec) for m in ch)
        p = lowpass(p, 900 + 500 * (k % 2))
        p *= env_adsr(len(p), 2.5, 0.5, 0.9, 3.0)
        place(L, p, k * seg, -8)
        k += 1

    # 3) tension: accelerating sub pulse from tension_start to riser end
    ts = cue["tension_start"]
    r0, r1 = cue["riser"]
    tt = ts
    while tt < r1:
        prog = (tt - ts) / max(r1 - ts, 1)
        place(L, thump(48, 0.5, 0.12, 1.5), tt, -6 + 4 * prog)
        tt += 0.95 - 0.5 * prog

    # 4) riser into the cliffhanger
    rl = r1 - r0
    rt = t_axis(rl)
    rise = np.sin(2 * np.pi * np.cumsum(NOTE(50) * 2 ** (rt / rl * 1.0)) / SR) * 0.3
    rise += bandpass(white(rl), 800, 7000) * 0.35
    rise *= (rt / rl) ** 2.2
    place(L, rise, r0, -4)

    # 5) hits + motif
    for h in cue["hits"]:
        place(L, sfx["boom_hit"][:, 0] if sfx["boom_hit"].ndim == 2 else sfx["boom_hit"], h, -3)
        place(L, motif(), h + 0.15, -9)

    # 6) silence gap after cliffhanger hit, soft motif on the end card
    gap0 = int((r1 + 0.05) * SR)
    gap1 = int((end_card + 0.2) * SR)
    fade = np.ones(n)
    fade[gap0:gap1] = 0.0
    fade[gap0 - int(0.05 * SR):gap0] = np.linspace(1, 0, int(0.05 * SR))
    keep_hit = np.zeros(n)
    place(keep_hit, sfx["boom_hit"] if sfx["boom_hit"].ndim == 1 else sfx["boom_hit"][:, 0], r1, -2)
    L = L * fade + keep_hit
    place(L, motif(0.8), end_card + 0.3, -8)
    tail = np.zeros(n)
    end_drone = drone[: n - int(end_card * SR)] * env_adsr(n - int(end_card * SR), 0.6, 0, 1, 1.2)
    place(tail, end_drone, end_card, -9)
    L += tail

    st = reverb(L, 3.5, 0.28)[:n]
    st = to_stereo(st, width=1.0)
    st[:, 0] = np.clip(st[:, 0], -1, 1)
    return st / (np.max(np.abs(st)) + 1e-9) * 0.85


def main():
    sfx = make_sfx()
    for name, x in sfx.items():
        write_wav(os.path.join(SFX_DIR, name + ".wav"), x)
    print("sfx:", len(sfx))
    for ep in S.EPISODES:
        mus = score(ep, sfx)
        write_wav(os.path.join(MUS_DIR, f"{ep['code']}_score.wav"), mus)
        print("score", ep["code"], len(mus) / SR, "s")


if __name__ == "__main__":
    main()
