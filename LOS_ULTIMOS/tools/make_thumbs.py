# -*- coding: utf-8 -*-
"""Vertical 1080x1920 thumbnails, one per episode.

Background = a frame of the graded episode (build/EPxx/picture.mp4, no subtitles),
taken from the episode's `thumb_shot`.  --previz uses the previz render.
"""
import argparse
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import series as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "assets", "fonts")


def frame(ep, previz):
    bdir = os.path.join(ROOT, "build", ep["code"] + ("_previz" if previz else ""))
    src = os.path.join(bdir, "picture.mp4")
    idx = [s["id"] for s in ep["shots"]].index(ep["thumb_shot"])
    t = S.shot_starts(ep)[idx] + ep["shots"][idx]["dur"] * 0.6
    out = os.path.join(bdir, "thumb_bg.png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", out],
                   check=True)
    return out


def make(ep, previz):
    bg = Image.open(frame(ep, previz)).convert("RGB").resize((S.W, S.H))
    # darken top & bottom for legibility
    grad = Image.new("L", (1, S.H))
    for y in range(S.H):
        top = max(0, 1 - y / 520)
        bot = max(0, (y - 1000) / 920)
        grad.putpixel((0, y), int(255 * min(0.88, max(top * 0.8, bot))))
    grad = grad.resize((S.W, S.H))
    bg = Image.composite(Image.new("RGB", bg.size, (5, 8, 9)), bg, grad)
    d = ImageDraw.Draw(bg)
    bebas = lambda s: ImageFont.truetype(os.path.join(F, "BebasNeue_400Regular.ttf"), s)
    mont = lambda s: ImageFont.truetype(os.path.join(F, "Montserrat_900Black.ttf"), s)

    def center(y, text, font, fill, stroke=0, sfill=(0, 0, 0), spacing=0):
        w = d.textlength(text, font=font) + spacing * (len(text) - 1)
        x = (S.W - w) / 2
        if spacing:
            for ch in text:
                d.text((x, y), ch, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill)
                x += d.textlength(ch, font=font) + spacing
        else:
            d.text((x, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill)

    center(120, S.TITLE, bebas(170), (240, 240, 240), spacing=18)
    center(310, f"EPISODIO {ep['num']} · {ep['title']}", mont(40), (255, 192, 64))
    lines = ep["thumb_text"]
    y = 1290 if len(lines) == 3 else 1400
    for i, ln in enumerate(lines):
        col = (255, 192, 64) if i == len(lines) - 1 else (255, 255, 255)
        center(y, ln, mont(128 if len(ln) <= 9 else 104), col, stroke=8)
        y += 150
    if previz:
        center(1820, "PREVISUALIZACIÓN — NO FINAL", mont(40), (255, 80, 80))
    out_dir = os.path.join(ROOT, "previz" if previz else "miniaturas")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"LOS_ULTIMOS_{ep['code']}_miniatura.jpg")
    bg.save(out, quality=93)
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("episodes", nargs="*")
    ap.add_argument("--previz", action="store_true")
    a = ap.parse_args()
    for c in a.episodes or [e["code"] for e in S.EPISODES]:
        make(S.episode(c), a.previz)
