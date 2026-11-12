# LOS ÚLTIMOS — miniserie de ciencia ficción para TikTok

Tres episodios verticales (9:16) de unos 57 segundos cada uno.

| Episodio | Título | Cliffhanger |
|---|---|---|
| EP01 | El día que terminó todo | La radio le dice su nombre: «Elías… no te des la vuelta». |
| EP02 | No estamos solos | Una foto suya de hace tres días y una puerta que se abre: «Por fin llegaste, Elías». |
| EP03 | La verdad | Él es la copia nº 12 del hombre que provocó la catástrofe. Hay humanos reales ahí afuera, y el original sigue vivo. |

## Estado

| Pieza | Estado |
|---|---|
| Historia, guiones, narración, prompts por plano | ✅ Hecho (`guiones/`, `narracion/`, `prompts/`) |
| Música original y 34 efectos de sonido (sintetizados, sin licencias de terceros) | ✅ Hecho (`assets/audio/`) |
| Pipeline de edición: mezcla, ducking, subtítulos, etalonaje y exportación H.264/AAC | ✅ Hecho y probado (`tools/`) |
| Previsualización técnica de los 3 episodios (rótulos animados, **no es el entregable**) | ✅ `previz/` |
| Hoja de personaje, fotogramas clave, clips de video IA y voces | ⏳ **Necesita una clave de Gemini API** (de pago, ver costo abajo) |
| `LOS_ULTIMOS_EP01.mp4` … `EP03.mp4` finales | ⏳ Se generan con un solo comando cuando haya clave |

Ningún archivo `LOS_ULTIMOS_EPxx.mp4` existe todavía: los videos finales necesitan
escenas generadas por un modelo de video, y este entorno no tiene ningún servicio
de IA de video configurado. No se usaron imágenes estáticas como sustituto.

## Qué servicio se usa y por qué

Un solo servicio cubre todo: **Google Gemini API** (`generativelanguage.googleapis.com`,
el único proveedor de IA accesible desde la red de este entorno):

| Necesidad | Modelo (se elige solo según lo que tu clave tenga disponible) |
|---|---|
| Hoja de personaje y fotogramas clave | Modelo de imagen de Gemini, con la hoja de personaje como referencia |
| Video (imagen a video, 9:16, 1080p, con sonido ambiente) | Veo |
| Narración masculina en español latinoamericano | Gemini TTS (voz «Charon»; voz femenina «Kore» para la señal externa) |

`python3 tools/gen_assets.py models` muestra los modelos que ve tu clave.
`--video-model`, `--image-model` y `--tts-model` permiten fijar uno concreto.

### Costo estimado (consulta precios actuales en ai.google.dev/pricing)

38 planos · 214 s de video generado · 39 imágenes · 42 líneas de voz.

| Opción | Estimado |
|---|---|
| Veo «fast» (~0,12–0,15 USD/s) | **~35–50 USD** (incluye 30 % de margen para repetir tomas) |
| Veo estándar (~0,40 USD/s) | ~110–160 USD |
| Imágenes + voz | ~2 USD |

Si el modelo exige clips de 8 s en 1080p (`--force8`), el costo sube aproximadamente un 40 %.
El script lleva la cuenta del gasto estimado en `recursos/ledger.json` y **se detiene** antes de pasar el límite `--budget`.

## Cómo producir los videos finales

```bash
cd LOS_ULTIMOS/tools
export GEMINI_API_KEY=...            # o se inyecta por el proxy de la sesión
python3 synth_audio.py               # 0) música y efectos (los WAV grandes no van en git; semilla fija)
python3 gen_assets.py estimate       # costo, sin llamadas
python3 gen_assets.py anchor         # 1) hoja de personaje -> REVISAR antes de seguir
python3 gen_assets.py keyframes      # 2) 38 fotogramas clave -> revisar consistencia
python3 gen_assets.py tts            # 3) voces
python3 gen_assets.py clips --budget 50 --price-per-second 0.15   # 4) video
python3 build_episode.py             # 5) edición y render de los 3 episodios
python3 make_thumbs.py               # 6) miniaturas
python3 verify.py                    # 7) control de calidad -> VERIFICACION.txt
```

Si un plano sale mal (cara deformada, artefactos), borra su `recursos/clips/EPxx/Sxx.mp4`
(o el fotograma clave) y vuelve a ejecutar el paso: lo demás está en caché y no se paga dos veces.

## Especificaciones de salida

* MP4 · H.264 High 4.2 · yuv420p · 1080×1920 · 30 fps · CRF 18 (máximo 16 Mb/s) · `faststart`
* AAC-LC 48 kHz estéreo 256 kb/s · sonoridad −14 LUFS, pico −1,5 dBTP (estándar de redes sociales)
* Subtítulos quemados (Montserrat ExtraBold, en bloques de 2 o 3 palabras con animación de entrada,
  colocados por encima de la zona de interfaz de TikTok) + `.srt` y `.ass` aparte
* Etalonaje común a los tres episodios: sombras verde azulado, altas luces ámbar,
  saturación −20 %, viñeta y grano de película

## Continuidad (cómo se mantiene)

* `tools/series.py` es la **única fuente**: personaje, estilo, planos, diálogos, efectos y música.
  Guiones, prompts, subtítulos y mezcla se generan desde ahí.
* Personaje fijo (`CHARACTER_LOCK`): 28 años, cabello oscuro, barba corta, delgado,
  chaqueta verde oliva gastada, bufanda gris, mochila militar tostada con cantimplora,
  **cicatriz en la ceja izquierda**. Se genera una hoja de personaje y se pasa como referencia
  a cada fotograma clave donde aparece Elías. Cada clip de video parte de su fotograma clave.
* El mismo motivo musical (re–fa–do♯, «la señal»), el mismo drone en re menor y los mismos sonidos
  de radio en los tres episodios.
* Pista oculta: la voz de la radio es la **misma voz** que la del narrador, con filtro de radio.
  En el EP03 se revela que es la suya.

## Estructura

```
LOS_ULTIMOS/
├── README.md
├── LOS_ULTIMOS_EP01.mp4 … EP03.mp4   (se crean al ejecutar el paso 5)
├── guiones/       guion completo por episodio (plano a plano, con tiempos)
├── narracion/     textos de narración + audio/ (voces generadas)
├── prompts/       biblia visual + prompts de imagen y video por plano
├── subtitulos/    .srt y .ass finales (se crean en el paso 5, sincronizados con las voces reales;
│                  en previz/ hay una versión con tiempos estimados)
├── miniaturas/    miniatura vertical por episodio
├── recursos/      personaje/, keyframes/, clips/, ledger.json (gasto)
├── assets/        fonts/ (OFL) · audio/music (partituras) · audio/sfx (efectos)
├── previz/        previsualizaciones técnicas (NO son los entregables)
└── tools/         series.py · gen_assets.py · synth_audio.py · build_episode.py
                   make_docs.py · make_thumbs.py · verify.py
```

## Herramientas

* FFmpeg 6.1 (libx264, AAC, libass, loudnorm) · Python 3 + numpy + Pillow
* Fuentes: Montserrat y Bebas Neue (SIL Open Font License)
* Música y efectos: síntesis propia en `tools/synth_audio.py` (sin samples externos)
* IA: Google Gemini API (imagen, Veo, TTS), pendiente de clave

## Previsualización y control de calidad ya realizados

`python3 build_episode.py --previz` renderiza los tres episodios con rótulos animados en lugar de escenas
(sin voz, con música, efectos, subtítulos, gráficos y tarjeta final) para probar todo el pipeline.
`previz/VERIFICACION.txt`: 39 de 39 comprobaciones superadas (formato, 1080×1920, 30 fps, 57 s, AAC 48 kHz,
−14 LUFS, decodificación completa, subtítulos sincronizados y sin solapes, continuidad entre episodios).
