# -*- coding: utf-8 -*-
"""Writes scripts, narration texts and generation prompts from series.py."""
import os

import series as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WHO = {"N": "ELÍAS (narración)", "RADIO": "VOZ EN LA RADIO", "DOBLE": "Nº 11 (el doble)",
       "ARCHIVO": "ELÍAS ORIGINAL (video 2037)", "MUJER": "MUJER (señal externa)"}


def fmt(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def lines_in(ep, a, b):
    return [(t, w, x) for (t, w, x) in ep["narration"] if a <= t < b]


def script(ep):
    st = S.shot_starts(ep)
    out = [f"# LOS ÚLTIMOS — Episodio {ep['num']}: {ep['title']}", "",
           f"**Duración:** {S.total_length(ep):.1f} s (imagen {S.picture_length(ep):.1f} s + tarjeta final "
           f"{S.END_CARD_SECONDS:.0f} s) · **Formato:** 9:16, 1080×1920, 30 fps", "",
           f"**Sinopsis:** {ep['logline']}", "",
           "Colores de subtítulo: blanco = narración de Elías · ámbar = radio · azul hielo = el doble · "
           "verde pálido = archivo 2037.", ""]
    for i, sh in enumerate(ep["shots"]):
        a = st[i]
        b = a + sh["dur"]
        out += [f"## {sh['id']} · {fmt(a)}–{fmt(b)}", "",
                f"**Imagen:** {sh['frame']}", "",
                f"**Movimiento / cámara:** {sh['motion']}", "",
                f"**Ambiente:** {sh['amb']} · **Efectos:** " +
                (", ".join(f"{n} (+{t:.1f}s)" for t, n, g in sh["sfx"]) or "—"), ""]
        for (t, w, x) in lines_in(ep, a, b):
            out.append(f"> **{WHO[w]}** ({fmt(t)}): {x}")
        for (oa, ob, txt, style) in ep["overlays"]:
            if a <= oa < b:
                out.append(f"> *Gráfico en pantalla ({style}, {fmt(oa)}–{fmt(ob)}):* "
                           f"{txt.replace(chr(10), ' / ')}")
        out.append("")
    out += [f"## TARJETA FINAL · {fmt(S.picture_length(ep))}–{fmt(S.total_length(ep))}", "",
            "Negro. «CONTINUARÁ» / «FIN DE LA TEMPORADA 1» · logo LOS ÚLTIMOS · "
            f"«{ep['next']}» · «SÍGUEME PARA NO PERDERTELO». Motivo musical de la señal.", ""]
    m = ep["music"]
    out += ["## Música (partitura original)", "",
            f"Drone en re menor + progresión Dm–B♭–Gm–A, motivo de campanas re–fa–do♯ "
            f"(«la señal»). Pulso de tensión desde {m['tension_start']} s, crescendo "
            f"{m['riser'][0]}–{m['riser'][1]} s, golpes en {', '.join(str(h) for h in m['hits'])} s, "
            f"silencio tras el golpe final y motivo suave sobre la tarjeta.", ""]
    return "\n".join(out)


def narration(ep):
    out = [f"LOS ÚLTIMOS — EP{ep['num']:02d}: {ep['title']}", "",
           "Formato: [tiempo] VOZ: texto   (las voces se generan por separado y se colocan en el tiempo indicado;",
           " si una línea es más larga, la siguiente se desplaza automáticamente)", ""]
    for (t, w, x) in ep["narration"]:
        out.append(f"[{fmt(t)}] {WHO[w]}: {x}")
    out += ["", "Dirección de voz (TTS):"]
    for w in sorted({w for _, w, _ in ep["narration"]}):
        v = S.VOICES[w]
        out.append(f"- {WHO[w]} -> voz '{v['voice']}': {v['style']}")
    return "\n".join(out) + "\n"


def prompts(ep):
    out = [f"# Prompts de generación — EP{ep['num']:02d}: {ep['title']}", "",
           "Cada plano se genera en dos pasos: (1) fotograma clave con el modelo de imagen, pasando "
           "la hoja de personaje como referencia cuando aparece Elías; (2) clip de video con Veo, "
           "imagen→video, 9:16, usando ese fotograma como primer cuadro.", "",
           f"**Prompt negativo (todos los clips):** `{S.NEGATIVE}`", ""]
    for sh in ep["shots"]:
        out += [f"## {sh['id']} ({sh['dur']} s en edición, {sh['gen']} s generados)", "",
                "**Fotograma clave:**", "", "```", S.keyframe_prompt(sh), "```", "",
                "**Video:**", "", "```", S.video_prompt(sh), "```", ""]
    return "\n".join(out)


def main():
    for d in ("guiones", "narracion", "prompts"):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    open(os.path.join(ROOT, "prompts", "00_personaje_y_estilo.md"), "w", encoding="utf-8").write(
        "# Biblia visual — LOS ÚLTIMOS\n\n## Personaje (bloqueado en todos los planos)\n\n"
        f"{S.CHARACTER_LOCK}\n\n## Estilo (bloqueado)\n\n{S.STYLE_LOCK}\n\n"
        f"## Estilo de video\n\n{S.VIDEO_STYLE}\n\n## Hoja de personaje (anchor)\n\n```\n{S.ANCHOR_PROMPT}\n```\n")
    for ep in S.EPISODES:
        c = ep["code"]
        open(os.path.join(ROOT, "guiones", f"{c}_guion.md"), "w", encoding="utf-8").write(script(ep))
        open(os.path.join(ROOT, "narracion", f"{c}_narracion.txt"), "w", encoding="utf-8").write(narration(ep))
        open(os.path.join(ROOT, "prompts", f"{c}_prompts.md"), "w", encoding="utf-8").write(prompts(ep))
    print("docs ok")


if __name__ == "__main__":
    main()
