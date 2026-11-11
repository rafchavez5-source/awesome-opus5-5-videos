# -*- coding: utf-8 -*-
"""
Generates every AI asset for LOS ÚLTIMOS through the Google Gemini API
(one key covers image, video and speech):

  1. character anchor sheet  (image model)       -> recursos/personaje/
  2. one keyframe per shot   (image model + anchor as reference) -> recursos/keyframes/
  3. one video clip per shot (Veo, image-to-video, 9:16)          -> recursos/clips/
  4. narration, one file per line (Gemini TTS)                   -> narracion/audio/

Everything is cached: a file that already exists is never paid for twice.

Key: export GEMINI_API_KEY=...   (or let the session proxy inject it; then any
dummy value works, e.g. GEMINI_API_KEY=proxy)

Usage:
  python3 gen_assets.py models                       # list models the key can use
  python3 gen_assets.py estimate                     # cost estimate, no calls
  python3 gen_assets.py anchor
  python3 gen_assets.py keyframes [EP01 ...]
  python3 gen_assets.py tts       [EP01 ...]
  python3 gen_assets.py clips     [EP01 ...] --budget 40   # stops before exceeding USD 40
  python3 gen_assets.py all --budget 40
Options:
  --video-model NAME --image-model NAME --tts-model NAME --resolution 1080p|720p
  --price-per-second 0.15   (used for the budget guard; check ai.google.dev/pricing)
"""
import argparse
import base64
import json
import os
import struct
import sys
import time
import urllib.error
import urllib.request

import series as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "recursos")
API = "https://generativelanguage.googleapis.com/v1beta"
LEDGER = os.path.join(RES, "ledger.json")


# ------------------------------------------------------------------ http ----
def key():
    k = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not k:
        sys.exit("Falta GEMINI_API_KEY (ver README).")
    return k


def http(method, url, body=None, raw=False, timeout=600):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("x-goog-api-key", key())
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                payload = r.read()
                return payload if raw else json.loads(payload or b"{}")
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:2000]
            if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                wait = 2 ** attempt * 5
                print(f"   HTTP {e.code}, reintento en {wait}s")
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP {e.code} {url}\n{msg}")
        except urllib.error.URLError as e:
            if attempt < 5:
                time.sleep(2 ** attempt * 2)
                continue
            raise


def ledger_add(kind, item, usd, meta=None):
    os.makedirs(RES, exist_ok=True)
    data = json.load(open(LEDGER)) if os.path.exists(LEDGER) else {"entries": []}
    data["entries"].append({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": kind,
                            "item": item, "usd_est": round(usd, 4), "meta": meta or {}})
    data["total_usd_est"] = round(sum(e["usd_est"] for e in data["entries"]), 4)
    json.dump(data, open(LEDGER, "w"), indent=1, ensure_ascii=False)
    return data["total_usd_est"]


def spent():
    if not os.path.exists(LEDGER):
        return 0.0
    return json.load(open(LEDGER)).get("total_usd_est", 0.0)


# ---------------------------------------------------------------- models ----
def list_models():
    out, tok = [], None
    while True:
        url = API + "/models?pageSize=200" + (f"&pageToken={tok}" if tok else "")
        r = http("GET", url)
        out += r.get("models", [])
        tok = r.get("nextPageToken")
        if not tok:
            return out


PREF_VIDEO = ["veo-3.1-generate", "veo-3.1-fast", "veo-3.0-generate", "veo-3.0-fast", "veo"]
PREF_IMAGE = ["gemini-3-pro-image", "gemini-3.1-flash-image", "gemini-2.5-flash-image",
              "image"]
PREF_TTS = ["gemini-3.8-flash-tts", "gemini-3.1-flash-tts", "gemini-2.5-pro-preview-tts",
            "gemini-2.5-flash-preview-tts", "tts"]


def pick(models, prefs, method):
    names = [m["name"].split("/", 1)[1] for m in models
             if method in m.get("supportedGenerationMethods", [])]
    for p in prefs:
        c = sorted([n for n in names if p in n], reverse=True)
        if c:
            return c[0]
    return None


def resolve_models(a):
    if a.video_model and a.image_model and a.tts_model:
        return a.video_model, a.image_model, a.tts_model
    ms = list_models()
    v = a.video_model or pick(ms, PREF_VIDEO, "predictLongRunning")
    i = a.image_model or pick(ms, PREF_IMAGE, "generateContent")
    t = a.tts_model or pick(ms, PREF_TTS, "generateContent")
    print(f"modelos -> video: {v} | imagen: {i} | voz: {t}")
    return v, i, t


# ---------------------------------------------------------------- images ----
def gen_image(model, prompt, refs=(), aspect="9:16"):
    parts = [{"inline_data": {"mime_type": "image/png",
                              "data": base64.b64encode(open(p, "rb").read()).decode()}}
             for p in refs]
    parts.append({"text": prompt})
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"],
                                 "imageConfig": {"aspectRatio": aspect}}}
    r = http("POST", f"{API}/models/{model}:generateContent", body)
    for c in r.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            d = p.get("inlineData") or p.get("inline_data")
            if d and d.get("data"):
                return base64.b64decode(d["data"])
    raise RuntimeError("El modelo de imagen no devolvió imagen: " + json.dumps(r)[:800])


def anchor(a, models):
    out = os.path.join(RES, "personaje", "ELIAS_anchor.png")
    if os.path.exists(out):
        print("anchor: ya existe")
        return out
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img = gen_image(models[1], S.ANCHOR_PROMPT)
    open(out, "wb").write(img)
    ledger_add("image", "anchor", a.price_image)
    print("anchor ->", out)
    return out


def keyframes(a, models, eps):
    anc = anchor(a, models)
    for ep in eps:
        for sh in ep["shots"]:
            out = os.path.join(RES, "keyframes", ep["code"], f"{sh['id']}.png")
            if os.path.exists(out):
                continue
            os.makedirs(os.path.dirname(out), exist_ok=True)
            refs = [anc] if sh["ref"] else []
            print(f"keyframe {ep['code']} {sh['id']}")
            img = gen_image(models[1], S.keyframe_prompt(sh), refs)
            open(out, "wb").write(img)
            ledger_add("image", f"{ep['code']}/{sh['id']}", a.price_image)


# ----------------------------------------------------------------- video ----
def veo_request(model, prompt, image_path, seconds, resolution):
    inst = {"prompt": prompt}
    if image_path:
        inst["image"] = {"bytesBase64Encoded": base64.b64encode(open(image_path, "rb").read()).decode(),
                         "mimeType": "image/png"}
    params = {"aspectRatio": "9:16", "durationSeconds": seconds, "resolution": resolution,
              "negativePrompt": S.NEGATIVE, "personGeneration": "allow_adult",
              "sampleCount": 1}
    return http("POST", f"{API}/models/{model}:predictLongRunning",
                {"instances": [inst], "parameters": params})


def veo_wait(op):
    name = op["name"]
    while True:
        r = http("GET", f"{API}/{name}")
        if r.get("done"):
            if "error" in r:
                raise RuntimeError(json.dumps(r["error"]))
            return r
        time.sleep(10)


def veo_uri(r):
    resp = r.get("response", {})
    for k in ("generateVideoResponse", "generate_video_response"):
        if k in resp:
            resp = resp[k]
    samples = resp.get("generatedSamples") or resp.get("videos") or []
    if not samples:
        raise RuntimeError("Veo no devolvió video (¿filtro de seguridad?): " + json.dumps(r)[:800])
    v = samples[0].get("video", samples[0])
    return v.get("uri"), v.get("bytesBase64Encoded")


def clips(a, models, eps):
    for ep in eps:
        for sh in ep["shots"]:
            out = os.path.join(RES, "clips", ep["code"], f"{sh['id']}.mp4")
            if os.path.exists(out):
                continue
            kf = os.path.join(RES, "keyframes", ep["code"], f"{sh['id']}.png")
            if not os.path.exists(kf):
                sys.exit(f"Falta keyframe {kf}: ejecuta primero 'keyframes'.")
            seconds = 8 if a.resolution == "1080p" and a.force8 else sh["gen"]
            cost = seconds * a.price_per_second
            if spent() + cost > a.budget:
                sys.exit(f"Presupuesto alcanzado (gastado ~USD {spent():.2f}, "
                         f"límite {a.budget}). Sube --budget para continuar.")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            print(f"clip {ep['code']} {sh['id']} ({seconds}s {a.resolution}) ...", flush=True)
            try:
                op = veo_request(models[0], S.video_prompt(sh), kf, seconds, a.resolution)
            except RuntimeError as e:
                if "duration" in str(e).lower() or "resolution" in str(e).lower():
                    print("   el modelo exige 8 s para esta resolución; reintento con 8 s")
                    seconds, cost = 8, 8 * a.price_per_second
                    op = veo_request(models[0], S.video_prompt(sh), kf, seconds, a.resolution)
                else:
                    raise
            r = veo_wait(op)
            uri, b64 = veo_uri(r)
            data = base64.b64decode(b64) if b64 else http("GET", uri, raw=True)
            open(out, "wb").write(data)
            tot = ledger_add("video", f"{ep['code']}/{sh['id']}", cost,
                             {"seconds": seconds, "model": models[0], "res": a.resolution})
            print(f"   ok -> {out}   (acumulado ~USD {tot:.2f})")


# ------------------------------------------------------------------- tts ----
def pcm_to_wav(pcm, rate=24000):
    hdr = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " + \
        struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16) + b"data" + struct.pack("<I", len(pcm))
    return hdr + pcm


def tts(a, models, eps):
    for ep in eps:
        for i, (t0, who, text) in enumerate(ep["narration"]):
            out = os.path.join(ROOT, "narracion", "audio", ep["code"], f"{i:02d}_{who}.wav")
            if os.path.exists(out):
                continue
            os.makedirs(os.path.dirname(out), exist_ok=True)
            v = S.VOICES[who]
            body = {"contents": [{"parts": [{"text": f"{v['style']} {text}"}]}],
                    "generationConfig": {"responseModalities": ["AUDIO"],
                                         "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig":
                                                                          {"voiceName": v["voice"]}}}}}
            print(f"tts {ep['code']} {i:02d} {who}: {text}")
            r = http("POST", f"{API}/models/{models[2]}:generateContent", body)
            d = r["candidates"][0]["content"]["parts"][0]["inlineData"]
            rate = 24000
            mt = d.get("mimeType", "")
            if "rate=" in mt:
                rate = int(mt.split("rate=")[1].split(";")[0])
            open(out, "wb").write(pcm_to_wav(base64.b64decode(d["data"]), rate))
            ledger_add("tts", f"{ep['code']}/{i:02d}", a.price_tts_line)


# ------------------------------------------------------------- estimate ----
def estimate(a):
    shots = [s for e in S.EPISODES for s in e["shots"]]
    sec_var = sum(s["gen"] for s in shots)
    sec_8 = 8 * len(shots)
    lines = sum(len(e["narration"]) for e in S.EPISODES)
    imgs = len(shots) + 1
    print(f"planos: {len(shots)} | segundos de video: {sec_var} (variable) / {sec_8} (todo a 8 s)")
    print(f"imágenes: {imgs} | líneas de voz: {lines}")
    for label, pps in (("Veo rápido (~0.12-0.15 USD/s)", 0.15), ("Veo estándar (~0.40 USD/s)", 0.40)):
        lo = sec_var * pps + imgs * a.price_image + lines * a.price_tts_line
        hi = sec_8 * pps + imgs * a.price_image + lines * a.price_tts_line
        print(f"{label}: USD {lo:.0f} - {hi:.0f}  (+~30% para repetir tomas fallidas)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["models", "estimate", "anchor", "keyframes", "clips", "tts", "all"])
    ap.add_argument("episodes", nargs="*")
    ap.add_argument("--video-model")
    ap.add_argument("--image-model")
    ap.add_argument("--tts-model")
    ap.add_argument("--resolution", default="1080p")
    ap.add_argument("--force8", action="store_true", help="generar siempre 8 s (algunos modelos lo exigen en 1080p)")
    ap.add_argument("--budget", type=float, default=0.0, help="límite de gasto estimado en USD para video")
    ap.add_argument("--price-per-second", type=float, default=0.15)
    ap.add_argument("--price-image", type=float, default=0.04)
    ap.add_argument("--price-tts-line", type=float, default=0.002)
    a = ap.parse_args()

    if a.step == "estimate":
        return estimate(a)
    if a.step == "models":
        for m in list_models():
            meth = m.get("supportedGenerationMethods", [])
            if any(x in m["name"] for x in ("veo", "image", "tts", "imagen")):
                print(m["name"], meth)
        return
    eps = [S.episode(c) for c in a.episodes] if a.episodes else S.EPISODES
    models = resolve_models(a)
    if a.step in ("anchor",):
        anchor(a, models)
    if a.step in ("keyframes", "all"):
        keyframes(a, models, eps)
    if a.step in ("tts", "all"):
        tts(a, models, eps)
    if a.step in ("clips", "all"):
        if a.budget <= 0:
            sys.exit("Para generar video indica un límite: --budget USD")
        clips(a, models, eps)
    print(f"gasto estimado acumulado: USD {spent():.2f}")


if __name__ == "__main__":
    main()
