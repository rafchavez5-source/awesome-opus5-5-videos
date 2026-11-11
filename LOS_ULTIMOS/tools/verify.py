# -*- coding: utf-8 -*-
"""Technical QA of the rendered episodes.

Checks: container/codecs, 1080x1920, ~30 fps, 45-60 s, AAC 48 kHz stereo,
loudness, full decode without errors, long black sections, subtitle cues
inside the video and matching the narration timeline, continuity markers.
"""
import argparse
import json
import os
import re
import subprocess
import sys

import series as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def check(code, previz):
    ep = S.episode(code)
    path = os.path.join(ROOT, "previz", f"PREVIZ_{code}.mp4") if previz else \
        os.path.join(ROOT, f"LOS_ULTIMOS_{code}.mp4")
    sub_dir = os.path.join(ROOT, "previz" if previz else "subtitulos")
    res, ok = [], True

    def r(name, cond, info):
        nonlocal ok
        ok &= bool(cond)
        res.append(("OK " if cond else "FALLO") + f"  {name}: {info}")

    if not os.path.exists(path):
        return False, [f"FALLO  no existe {path}"]
    p = json.loads(sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path]).stdout)
    v = [s for s in p["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in p["streams"] if s["codec_type"] == "audio"]
    dur = float(p["format"]["duration"])
    fps = eval(v["avg_frame_rate"])
    r("contenedor", "mp4" in p["format"]["format_name"], p["format"]["format_name"])
    r("video", v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p", f"{v['codec_name']} {v.get('profile')} {v['pix_fmt']}")
    r("resolución", (v["width"], v["height"]) == (1080, 1920), f"{v['width']}x{v['height']}")
    r("fps", abs(fps - 30) < 0.05, f"{fps:.3f}")
    r("duración", 45 <= dur <= 60, f"{dur:.2f}s")
    r("audio", bool(a) and a[0]["codec_name"] == "aac" and a[0]["sample_rate"] == "48000" and a[0]["channels"] == 2,
      f"{a[0]['codec_name']} {a[0]['sample_rate']}Hz {a[0]['channels']}ch {int(a[0].get('bit_rate', 0))//1000}kb/s" if a else "sin audio")
    r("tamaño", os.path.getsize(path) < 287e6, f"{os.path.getsize(path)/1e6:.1f} MB, {int(p['format']['bit_rate'])//1000} kb/s")

    e = sh(["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"])
    r("decodificación completa", not e.stderr.strip(), "sin errores" if not e.stderr.strip() else e.stderr[:200])

    ld = sh(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", ld)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", ld)
    if I:
        r("sonoridad", -16.5 <= float(I[-1]) <= -12.5, f"{I[-1]} LUFS, pico {tp[-1] if tp else '?'} dBTP")

    bd = sh(["ffmpeg", "-i", path, "-vf", "blackdetect=d=1.2:pix_th=0.06", "-an", "-f", "null", "-"]).stderr
    blacks = [(float(x), float(y)) for x, y in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)]
    bad = [b for b in blacks if b[0] < S.picture_length(ep) - 0.5]
    r("sin negros largos en la imagen", not bad, f"{bad or 'ninguno (la tarjeta final es negra a propósito)'}")

    srt = open(os.path.join(sub_dir, f"LOS_ULTIMOS_{code}.srt"), encoding="utf-8").read()
    cues = re.findall(r"(\d\d):(\d\d):(\d\d),(\d+) --> (\d\d):(\d\d):(\d\d),(\d+)\n(.+)", srt)
    tos = lambda h, m, s, ms: int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    tl = json.load(open(os.path.join(ROOT, "build", code + ("_previz" if previz else ""), "timeline.json")))
    sync = all(abs(tos(*c[:4]) - l["start"]) < 0.01 and c[8].strip() == l["text"] for c, l in zip(cues, tl))
    inside = all(tos(*c[4:8]) <= dur for c in cues)
    mono = all(tos(*cues[i][:4]) >= tos(*cues[i - 1][4:8]) - 1e-3 for i in range(1, len(cues)))
    r("subtítulos", len(cues) == len(ep["narration"]) and sync and inside and mono,
      f"{len(cues)} líneas, sincronía con voz={'sí' if sync else 'NO'}, dentro del video={'sí' if inside else 'NO'}, "
      f"sin solapes={'sí' if mono else 'NO'}")
    return ok, res


def continuity():
    out = []
    e1, e2, e3 = S.EPISODES
    txt = lambda e: " ".join(x for _, _, x in e["narration"]).lower()
    out.append(("EP1 termina con la radio diciendo su nombre y EP2 empieza ahí",
                "elías" in txt(e1).split("vuelta")[0][-40:] and e2["narration"][0][2].startswith("Elías")))
    out.append(("EP2 termina con alguien abriendo la puerta y EP3 empieza con el hombre de la puerta",
                "door" in e2["shots"][-2]["frame"].lower() and "puerta" in e3["narration"][0][2].lower()))
    out.append(("La advertencia de la radio aparece en EP1 y se explica en EP3",
                "no confíes en los sobrevivientes" in txt(e1) and "no confíes en los sobrevivientes" in txt(e3)))
    out.append(("«Sujeto 12» (EP2) = «Tú eres el doce» (EP3)", "doce" in txt(e2) and "doce" in txt(e3)))
    out.append(("Protocolo Eco / fecha 14·03·2037 coherente en EP2 y EP3",
                any("2037" in o[2] for o in e2["overlays"]) and any("2037" in o[2] for o in e3["overlays"])))
    out.append(("Todo plano donde aparece Elías usa la hoja de personaje como referencia",
                all(s["ref"] for e in S.EPISODES for s in e["shots"] if "elías" in s["frame"].lower())))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("episodes", nargs="*")
    ap.add_argument("--previz", action="store_true")
    a = ap.parse_args()
    all_ok = True
    report = []
    for c in a.episodes or [e["code"] for e in S.EPISODES]:
        ok, res = check(c, a.previz)
        all_ok &= ok
        report.append(f"== {c} ==")
        report += res
    report.append("== CONTINUIDAD ==")
    for name, ok in continuity():
        all_ok &= ok
        report.append(("OK " if ok else "FALLO") + "  " + name)
    text = "\n".join(report)
    print(text)
    out = os.path.join(ROOT, "previz" if a.previz else ".", "VERIFICACION.txt")
    open(out, "w", encoding="utf-8").write(text + "\n")
    sys.exit(0 if all_ok else 1)
