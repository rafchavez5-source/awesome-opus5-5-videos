# -*- coding: utf-8 -*-
"""
Edits, mixes and renders one episode of LOS ÚLTIMOS.

  python3 build_episode.py EP01                 # final: needs recursos/clips + narracion/audio
  python3 build_episode.py EP01 --previz        # pipeline test with placeholder slates

Output (final):  LOS_ULTIMOS/LOS_ULTIMOS_EP01.mp4
Output (previz): LOS_ULTIMOS/previz/PREVIZ_EP01.mp4   (NOT a deliverable)

Video: 1080x1920, 30 fps, H.264 High (yuv420p, CRF 17), +faststart
Audio: AAC-LC 48 kHz stereo 256 kb/s, loudness -14 LUFS / -1.5 dBTP
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np

import series as S
import synth_audio as A

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")
SFX = os.path.join(ROOT, "assets", "audio", "sfx")
MUS = os.path.join(ROOT, "assets", "audio", "music")
XF = 0.2            # dissolve length between shots (s)
SR = A.SR

GRADE = ("eq=contrast=1.07:saturation=0.80:gamma=0.97:brightness=-0.01,"
         "colorbalance=rs=-0.05:gs=-0.01:bs=0.05:rm=-0.02:bm=0.02:rh=0.05:gh=0.01:bh=-0.05,"
         "vignette=angle=PI/4.6")
GRAIN = "noise=c0s=4:c0f=t"


def run(cmd, quiet=True):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print(" ".join(cmd)[:2000])
        print(r.stderr[-4000:])
        sys.exit("ffmpeg falló")
    return r.stdout


def probe_dur(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", path])
    return float(out.strip())


def has_audio(path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
               "stream=index", "-of", "csv=p=0", path])
    return bool(out.strip())


# ------------------------------------------------------------ narration ----
def trim_silence(x, thr=0.012):
    mono = np.abs(x).max(axis=1)
    idx = np.where(mono > thr)[0]
    if len(idx) == 0:
        return x
    a = max(idx[0] - int(0.03 * SR), 0)
    b = min(idx[-1] + int(0.08 * SR), len(x))
    return x[a:b]


def process_voice(x, who):
    m = x.mean(axis=1)
    if who in ("RADIO", "MUJER"):
        m = A.bandpass(m, 380, 3000, 3)
        m = np.tanh(m / (np.max(np.abs(m)) + 1e-9) * 2.6) / np.tanh(2.6)
        st = A.bandpass(A.RNG.standard_normal(len(m)), 300, 4500) * 0.035
        crack = (A.RNG.random(len(m)) < 0.0015) * A.RNG.uniform(-0.25, 0.25, len(m))
        m = m * 0.8 + st + A.bandpass(crack, 900, 6000)
        m = A.reverb(m, 0.9, 0.12)[: len(m)]
    elif who == "ARCHIVO":
        m = A.bandpass(m, 170, 6000, 2)
        t = np.arange(len(m)) / SR
        m = m + np.sin(2 * np.pi * 60 * t) * 0.01
        m = A.reverb(m, 0.7, 0.10)[: len(m)]
    elif who == "DOBLE":
        m = A.highpass(m, 90)
        m = A.reverb(m, 1.4, 0.16)[: len(m)]
    else:  # N
        m = A.highpass(m, 70)
        m = np.tanh(m * 1.4) / np.tanh(1.4)
        m = A.reverb(m, 0.8, 0.06)[: len(m)]
    m = m / (np.max(np.abs(m)) + 1e-9) * 0.89
    return A.to_stereo(m)


def place_narration(ep, previz):
    """Returns (voice_track[n,2] or None, timeline list)."""
    total = S.total_length(ep)
    n = int(total * SR)
    track = np.zeros((n, 2))
    timeline, prev_end, have_audio = [], 0.0, True
    for i, (t0, who, text) in enumerate(ep["narration"]):
        f = os.path.join(ROOT, "narracion", "audio", ep["code"], f"{i:02d}_{who}.wav")
        if os.path.exists(f) and not previz:
            x = process_voice(trim_silence(A.read_wav(f)), who)
            dur = len(x) / SR
        else:
            have_audio = False
            x, dur = None, max(len(text) / 14.5, 0.8)
        start = max(t0, prev_end + 0.12) if timeline else t0
        if start != t0:
            print(f"   aviso: línea {i} desplazada {start - t0:+.2f}s para no solaparse")
        if x is not None:
            st = int(start * SR)
            seg = x[: max(n - st, 0)]
            track[st:st + len(seg)] += seg
        timeline.append({"i": i, "who": who, "text": text, "start": round(start, 3),
                         "end": round(start + dur, 3)})
        prev_end = start + dur
    if prev_end > S.picture_length(ep) + 0.4:
        print(f"   aviso: la narración termina en {prev_end:.2f}s, después del corte final")
    return (track if have_audio else None), timeline


# ---------------------------------------------------------------- audio ----
def load_sfx(name):
    return A.read_wav(os.path.join(SFX, name + ".wav"))


def envelope(x, attack=0.02, release=0.35):
    m = np.abs(x).max(axis=1)
    k = int(0.03 * SR)
    m = np.sqrt(np.convolve(m ** 2, np.ones(k) / k, mode="same"))
    out = np.zeros_like(m)
    a, r = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    # vectorised-ish one-pole with block processing
    blk = 240
    level = 0.0
    for b in range(0, len(m), blk):
        v = m[b:b + blk].max()
        level = v if v > level else level * (r ** blk) + v * (1 - r ** blk)
        out[b:b + blk] = level
    return np.clip(out / (out.max() + 1e-9), 0, 1)


def mix(ep, voice, clip_audio, bdir):
    total = S.total_length(ep)
    n = int(total * SR)
    starts = S.shot_starts(ep)
    music = A.read_wav(os.path.join(MUS, f"{ep['code']}_score.wav"))[:n]
    music = np.pad(music, ((0, n - len(music)), (0, 0)))

    amb = np.zeros((n, 2))
    gains = {"wind": -15, "rain": -14, "drip": -15, "hum": -19, "facility": -18, "cryo": -17}
    fade = int(0.4 * SR)
    for st, sh in zip(starts, ep["shots"]):
        bed = load_sfx("amb_" + sh["amb"])
        a, b = int(st * SR), int((st + sh["dur"]) * SR) + fade
        b = min(b, int(S.picture_length(ep) * SR) + fade, n)
        seg = bed[a % (len(bed) - (b - a)): a % (len(bed) - (b - a)) + (b - a)].copy()
        ramp = np.ones(len(seg))
        ramp[:fade] = np.linspace(0, 1, fade)
        ramp[-fade:] = np.linspace(1, 0, fade)
        amb[a:b] += seg * ramp[:, None] * 10 ** (gains.get(sh["amb"], -16) / 20)

    fx = np.zeros((n, 2))
    for st, sh in zip(starts, ep["shots"]):
        for (t, name, g) in sh["sfx"]:
            x = load_sfx(name)
            p = int((st + t) * SR)
            if p >= n:
                continue
            x = x[: n - p]
            fx[p:p + len(x)] += x * 10 ** ((g - 4) / 20)

    if clip_audio is not None:
        fx += clip_audio[:n] * 10 ** (-16 / 20)

    if voice is not None:
        env = envelope(voice)
        duck_m = (1 - 0.6 * env)[:, None]
        duck_a = (1 - 0.35 * env)[:, None]
    else:
        duck_m = duck_a = 1.0
    music_gain = 10 ** (-9 / 20)
    out = music * music_gain * duck_m + amb * duck_a + fx
    if voice is not None:
        out += voice * 10 ** (-1 / 20)
    # gentle bus limiter
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    A.write_wav(os.path.join(bdir, "mix.wav"), out)
    return os.path.join(bdir, "mix.wav")


# ------------------------------------------------------------ subtitles ----
def ass_time(t):
    t = max(t, 0)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


COLORS = {"N": "&H00FFFFFF", "RADIO": "&H0040C0FF", "MUJER": "&H0040C0FF",
          "DOBLE": "&H00FFE6C0", "ARCHIVO": "&H00D8F0D0"}


def chunks(text, max_chars=17):
    words = text.split()
    out, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if len(cand) > max_chars and cur:
            out.append(cur)
            cur = w
        else:
            cur = cand
        if cur.endswith((".", "?", "!", "…", ",", "»")) and len(cur) > 6:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    # never end a chunk on a weak word ("en los", "que", "te"...)
    weak = {"a", "al", "de", "del", "el", "la", "los", "las", "en", "y", "que", "un", "una",
            "no", "te", "me", "se", "mi", "tu", "lo", "por", "para", "con", "sin", "es", "era"}
    for k in range(len(out) - 1):
        w = out[k].split()
        while len(w) > 1 and w[-1].lower().strip("¿¡«") in weak:
            out[k + 1] = w.pop() + " " + out[k + 1]
        out[k] = " ".join(w)
    merged = []
    for c in out:          # glue tiny leftovers ("en", "Era") to the next chunk
        if merged and len(merged[-1]) <= 4:
            merged[-1] = merged[-1] + " " + c
        else:
            merged.append(c)
    final = []
    for c in merged:       # keep every chunk on one line (<= 900 px at 76 px Montserrat)
        w = c.split()
        if _width(c) > 900 and len(w) > 1:
            cut = max(range(1, len(w)), key=lambda i: -abs(_width(" ".join(w[:i])) - _width(" ".join(w[i:]))))
            final += [" ".join(w[:cut]), " ".join(w[cut:])]
        else:
            final.append(c)
    return [c for c in final if c]


_FONT = None


def _width(text):
    global _FONT
    if _FONT is None:
        from PIL import ImageFont
        _FONT = ImageFont.truetype(os.path.join(FONTS, "Montserrat_800ExtraBold.ttf"), 76)
    return _FONT.getlength(text.upper())


def esc(t):
    return t.replace("{", "(").replace("}", ")").replace("\n", "\\N")


def write_subs(ep, timeline, bdir, out_dir):
    pic = S.picture_length(ep)
    total = S.total_length(ep)
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {S.W}
PlayResY: {S.H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Montserrat ExtraBold,76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,7,3,5,90,90,0,1
Style: Who,Montserrat SemiBold,34,&H0040C0FF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,6,0,1,3,0,5,90,90,0,1
Style: Title,Bebas Neue,150,&H00F2F2F2,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,14,0,1,0,6,8,60,60,250,1
Style: Card,Bebas Neue,78,&H00E8E8E8,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,10,0,1,3,2,8,60,60,330,1
Style: Stamp,Montserrat Black,60,&H00FFFFFF,&H00FFFFFF,&H001C1CC0,&H001C1CC0,0,0,0,0,100,100,6,-4,3,16,0,5,60,60,0,1
Style: Hand,Montserrat SemiBold,66,&H00F0F0F0,&H00FFFFFF,&H00101010,&H96000000,0,0,0,0,100,100,2,-3,1,4,2,5,60,60,0,1
Style: Alert,Montserrat Black,54,&H00FFFFFF,&H00FFFFFF,&H001E1EC8,&H001E1EC8,0,0,0,0,100,100,4,0,3,18,0,8,60,60,380,1
Style: EndBig,Bebas Neue,120,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,10,0,1,0,0,5,60,60,0,1
Style: EndSmall,Montserrat SemiBold,42,&H00B0B0B0,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,12,0,1,0,0,5,60,60,0,1
Style: EndNext,Montserrat ExtraBold,56,&H0040C0FF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,4,0,1,0,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    srt = []
    Y = 1180   # subtitle centre: above TikTok's caption/UI zone
    for k, ln in enumerate(timeline):
        parts = chunks(ln["text"])
        span = ln["end"] - ln["start"]
        weights = np.array([max(len(p), 4) for p in parts], float)
        bounds = ln["start"] + np.concatenate([[0], np.cumsum(weights) / weights.sum() * span])
        col = COLORS[ln["who"]]
        for j, p in enumerate(parts):
            a, b = bounds[j], bounds[j + 1]
            if j == len(parts) - 1:
                nxt = timeline[k + 1]["start"] if k + 1 < len(timeline) else pic
                b = min(b + 0.35, nxt - 0.02, pic)
            pop = r"{\fscx86\fscy86\t(0,90,\fscx100\fscy100)}"
            ev.append(f"Dialogue: 1,{ass_time(a)},{ass_time(b)},Sub,,0,0,0,,"
                      f"{{\\pos(540,{Y})\\1c{col}}}{pop}{esc(p.upper())}")
        if ln["who"] in ("RADIO", "MUJER", "ARCHIVO", "DOBLE"):
            label = {"RADIO": "· RADIO ·", "MUJER": "· SEÑAL EXTERNA ·",
                     "ARCHIVO": "· ARCHIVO 2037 ·", "DOBLE": "· Nº 11 ·"}[ln["who"]]
            ev.append(f"Dialogue: 0,{ass_time(ln['start'])},{ass_time(min(ln['end'] + 0.3, pic))},Who,,0,0,0,,"
                      f"{{\\pos(540,{Y - 92})\\1c{col}\\fad(120,120)}}{label}")
        nxt_start = timeline[k + 1]["start"] - 0.02 if k + 1 < len(timeline) else pic
        srt.append(f"{k + 1}\n{srt_time(ln['start'])} --> {srt_time(min(ln['end'] + 0.25, nxt_start, pic))}\n"
                   f"{ln['text']}\n")

    for (a, b, text, style) in ep["overlays"]:
        if style == "title":
            ev.append(f"Dialogue: 2,{ass_time(a)},{ass_time(b)},Title,,0,0,0,,"
                      f"{{\\fad(150,400)\\blur1}}{esc(text)}")
        elif style == "card":
            ev.append(f"Dialogue: 2,{ass_time(a)},{ass_time(b)},Card,,0,0,0,,"
                      f"{{\\fad(300,300)}}{esc(text)}")
        elif style == "stamp":
            for j, part in enumerate(text.split("\n")):
                fs = "" if j == 0 else "\\fs42\\1c&H00E0E0FF&"
                ev.append(f"Dialogue: 2,{ass_time(a)},{ass_time(b)},Stamp,,0,0,0,,"
                          f"{{\\pos(540,{540 + j * 104})\\fscx140\\fscy140\\t(0,120,\\fscx100\\fscy100)"
                          f"\\fad(0,250){fs}}}{esc(part)}")
        elif style == "handwritten":
            for j, part in enumerate(text.split("\n")):
                ev.append(f"Dialogue: 2,{ass_time(a)},{ass_time(b)},Hand,,0,0,0,,"
                          f"{{\\pos(540,{660 + j * 95})\\fad(250,250)}}{esc(part)}")
        elif style == "alert":
            blink = "".join(f"\\t({i*500},{i*500+250},\\alpha&H60&)\\t({i*500+250},{i*500+500},\\alpha&H00&)"
                            for i in range(int((b - a) * 2)))
            ev.append(f"Dialogue: 2,{ass_time(a)},{ass_time(b)},Alert,,0,0,0,,{{{blink}}}{esc(text)}")

    # end card
    e0 = pic + 0.15
    ev.append(f"Dialogue: 2,{ass_time(e0)},{ass_time(total)},EndSmall,,0,0,0,,"
              f"{{\\pos(540,760)\\fad(300,0)}}CONTINUARÁ" if ep["num"] < 3 else
              f"Dialogue: 2,{ass_time(e0)},{ass_time(total)},EndSmall,,0,0,0,,"
              f"{{\\pos(540,760)\\fad(300,0)}}FIN DE LA TEMPORADA 1")
    ev.append(f"Dialogue: 2,{ass_time(e0 + 0.2)},{ass_time(total)},EndBig,,0,0,0,,"
              f"{{\\pos(540,900)\\fad(400,0)}}{S.TITLE}")
    ev.append(f"Dialogue: 2,{ass_time(e0 + 0.6)},{ass_time(total)},EndNext,,0,0,0,,"
              f"{{\\pos(540,1040)\\fad(300,0)}}{esc(ep['next'])}")
    ev.append(f"Dialogue: 2,{ass_time(e0 + 1.0)},{ass_time(total)},EndSmall,,0,0,0,,"
              f"{{\\pos(540,1130)\\fad(300,0)\\fs34}}SÍGUEME PARA NO PERDERTELO")

    os.makedirs(out_dir, exist_ok=True)
    ass_p = os.path.join(out_dir, f"LOS_ULTIMOS_{ep['code']}.ass")
    srt_p = os.path.join(out_dir, f"LOS_ULTIMOS_{ep['code']}.srt")
    open(ass_p, "w", encoding="utf-8").write(hdr + "\n".join(ev) + "\n")
    open(srt_p, "w", encoding="utf-8").write("\n".join(srt))
    shutil.copy(ass_p, os.path.join(bdir, "subs.ass"))
    return os.path.join(bdir, "subs.ass")


# ---------------------------------------------------------------- video ----
def wrap(text, width=34):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines


def previz_clip(ep, sh, path, length):
    """Animated placeholder slate (NOT a deliverable): drifting fog + shot info."""
    txtf = path + ".txt"
    open(txtf, "w", encoding="utf-8").write(
        f"{ep['code']} · {sh['id']}\n\n" + "\n".join(wrap(sh["frame"], 30)[:14]))
    font = os.path.join(FONTS, "Montserrat_600SemiBold.ttf")
    big = os.path.join(FONTS, "BebasNeue_400Regular.ttf")
    vf = (f"noise=alls=40:allf=t,gblur=sigma=30,eq=contrast=1.4:brightness=-0.05,"
          f"drawtext=fontfile={big}:text='PREVISUALIZACIÓN':fontsize=110:fontcolor=0xFF4040@0.85:"
          f"x=(w-tw)/2:y=170,"
          f"drawtext=fontfile={font}:textfile={txtf}:fontsize=40:fontcolor=white@0.85:"
          f"line_spacing=14:x=80:y=420,"
          f"drawtext=fontfile={font}:text='Sin video IA - esperando clave de API':fontsize=34:"
          f"fontcolor=0xFFC040:x=(w-tw)/2:y=h-260")
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
         f"color=c=0x16211f:s={S.W}x{S.H}:r={S.FPS}:d={length}", "-vf", vf,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", path])


def norm_clip(src, dst, length):
    """Scale/crop to 1080x1920, 30 fps; gently time-stretch (<=12%) if the
    generated clip is a bit shorter than the edit needs."""
    have = probe_dur(src)
    factor = max(1.0, length / max(have - 0.05, 0.1))
    if factor > 1.12:
        print(f"   aviso: {os.path.basename(src)} dura {have:.2f}s, se necesitan {length:.2f}s")
        factor = 1.12
    vf = (f"setpts={factor:.4f}*PTS,scale={S.W}:{S.H}:force_original_aspect_ratio=increase:flags=lanczos,"
          f"crop={S.W}:{S.H},fps={S.FPS},setsar=1,format=yuv420p")
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-t", f"{length:.3f}", "-vf", vf, "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "12", dst])


def build(code, previz=False, keep=False):
    ep = S.episode(code)
    bdir = os.path.join(ROOT, "build", code + ("_previz" if previz else ""))
    os.makedirs(bdir, exist_ok=True)
    clip_dir = os.path.join(ROOT, "recursos", "clips", code)
    shots = ep["shots"]
    pic = S.picture_length(ep)
    total = S.total_length(ep)
    print(f"== {code} {ep['title']}  ({pic:.1f}s + tarjeta = {total:.1f}s) {'[PREVIZ]' if previz else ''}")

    # 1. shots -> normalised segments
    segs = []
    clip_audio = np.zeros((int(total * SR), 2)) if not previz else None
    for i, (st, sh) in enumerate(zip(S.shot_starts(ep), shots)):
        length = sh["dur"] + XF   # every shot overlaps the next one (or the end card)
        seg = os.path.join(bdir, f"seg_{sh['id']}.mp4")
        if previz:
            previz_clip(ep, sh, seg, length)
        else:
            src = os.path.join(clip_dir, f"{sh['id']}.mp4")
            if not os.path.exists(src):
                sys.exit(f"Falta el clip {src}. Genera los clips (gen_assets.py clips) o usa --previz.")
            norm_clip(src, seg, length)
            if has_audio(src):
                wav = os.path.join(bdir, f"clipaudio_{sh['id']}.wav")
                run(["ffmpeg", "-y", "-v", "error", "-i", src, "-t", f"{length:.3f}", "-vn",
                     "-ac", "2", "-ar", str(SR), wav])
                x = A.read_wav(wav)
                p = int(st * SR)
                x = x[: len(clip_audio) - p]
                ramp = np.ones(len(x))
                k = min(int(0.15 * SR), len(x) // 2)
                ramp[:k] = np.linspace(0, 1, k)
                ramp[-k:] = np.linspace(1, 0, k)
                clip_audio[p:p + len(x)] += x * ramp[:, None]
        segs.append(seg)
    endcard = os.path.join(bdir, "seg_end.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
         f"color=c=black:s={S.W}x{S.H}:r={S.FPS}:d={S.END_CARD_SECONDS + XF}",
         "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", endcard])
    segs.append(endcard)

    # 2. narration + subtitles + mix
    voice, timeline = place_narration(ep, previz)
    json.dump(timeline, open(os.path.join(bdir, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    sub_dir = os.path.join(ROOT, "previz" if previz else "subtitulos")
    ass = write_subs(ep, timeline, bdir, sub_dir)
    wav = mix(ep, voice, clip_audio, bdir)

    # 3. dissolve chain
    inputs, fc, last = [], [], "[0:v]"
    for s in segs:
        inputs += ["-i", s]
    starts = S.shot_starts(ep) + [pic]
    for i in range(1, len(segs)):
        off = starts[i]
        lab = f"[x{i}]"
        trans = "fadeblack" if i == len(segs) - 1 else "fade"
        fc.append(f"{last}[{i}:v]xfade=transition={trans}:duration={XF}:offset={off:.3f}{lab}")
        last = lab
    fc.append(f"{last}{GRADE},format=yuv420p[graded]")
    picture = os.path.join(bdir, "picture.mp4")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc), "-map", "[graded]",
         "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-r", str(S.FPS), picture])

    # 4. final: burn subtitles, encode, mux loudness-normalised audio
    out = os.path.join(ROOT, "previz", f"PREVIZ_{code}.mp4") if previz else \
        os.path.join(ROOT, f"LOS_ULTIMOS_{code}.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    assf = ass.replace("\\", "/").replace(":", "\\:")
    run(["ffmpeg", "-y", "-v", "error", "-i", picture, "-i", wav,
         "-vf", ("" if previz else GRAIN + ",") + f"ass={assf}:fontsdir={FONTS}",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000",
         "-map", "0:v", "-map", "1:a", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-profile:v", "high", "-level", "4.2", "-preset", "medium", *(["-crf", "26"] if previz else ["-crf", "18", "-maxrate", "10M", "-bufsize", "20M"]),
         "-pix_fmt", "yuv420p", "-r", str(S.FPS), "-g", "60", "-bf", "2",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
         "-movflags", "+faststart", "-metadata", f"title=LOS ÚLTIMOS - {ep['title']}", out])
    print("   ->", out)
    if not keep:
        for f in os.listdir(bdir):
            if f.startswith(("seg_", "clipaudio_")):
                os.remove(os.path.join(bdir, f))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("episodes", nargs="*", default=[e["code"] for e in S.EPISODES])
    ap.add_argument("--previz", action="store_true")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    for c in a.episodes or [e["code"] for e in S.EPISODES]:
        build(c, a.previz, a.keep)
