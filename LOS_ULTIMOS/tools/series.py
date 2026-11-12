# -*- coding: utf-8 -*-
"""
LOS ÚLTIMOS - single source of truth for the series.

Everything (scripts, prompts, subtitles, sound design, edit) is generated
from this file, so the three episodes stay consistent.

Times are in seconds on the final edit timeline of each episode.
Voices:
  N       = Elías narrating (dry, close, cinematic)
  RADIO   = Elías's own voice processed as an old radio (the hidden clue)
  DOBLE   = copy #11 (same voice as Elías, dry, colder)
  ARCHIVO = the original Elías in a 2037 video log (voice + old monitor fx)
  MUJER   = unknown woman on the radio (season 2 hook)
"""

TITLE = "LOS ÚLTIMOS"
YEAR = "2042"

# ---------------------------------------------------------------- locks ----
CHARACTER_LOCK = (
    "ELÍAS VARELA, a 28-year-old Latino man with a lean, wiry build, short messy "
    "dark-brown hair, a short dark full beard, tired dark-brown eyes and a small "
    "pale scar that cuts vertically through his LEFT eyebrow. He wears a faded "
    "olive-green hooded field jacket with frayed cuffs over a charcoal thermal "
    "shirt, a dark-grey knitted scarf around his neck, worn tan cargo pants, "
    "scuffed brown leather boots, black fingerless gloves, and a weathered "
    "coyote-tan military rucksack with a dented steel canteen clipped to the "
    "left shoulder strap."
)

STYLE_LOCK = (
    "Photorealistic cinematic film still from a high-budget post-apocalyptic "
    "science-fiction movie set in 2042. Shot on ARRI Alexa 35 with anamorphic "
    "lenses, shallow depth of field, natural skin texture, subtle 35mm film "
    "grain. Desaturated colour grade: cold teal-grey shadows, muted moss greens, "
    "warm amber practical lights. Volumetric fog, floating dust particles, soft "
    "overcast or low-key motivated lighting. Mood: loneliness, danger, mystery."
)

VIDEO_STYLE = (
    "Cinematic, photorealistic, smooth and slow camera movement, natural human "
    "motion with correct anatomy, consistent face, 9:16 vertical framing, "
    "volumetric fog and dust, film grain, desaturated teal and amber grade. "
    "Ambient sound effects only, no dialogue, no speech, no music."
)

NEGATIVE = (
    "text, subtitles, captions, watermark, logo, cartoon, anime, CGI look, "
    "deformed hands, extra fingers, distorted face, morphing, flicker, "
    "jump cut, fast shaky camera, bright saturated colours, clean modern city, "
    "crowds, talking, speech, music"
)

# Voice / TTS direction (Gemini TTS uses natural-language style prompts)
VOICES = {
    "N": {"voice": "Charon", "style": (
        "Lee en español latinoamericano neutro, con voz masculina grave, cálida "
        "y cinematográfica, como el narrador de un tráiler de suspenso. Ritmo "
        "pausado, íntimo, casi en susurro, con pausas dramáticas naturales:")},
    "RADIO": {"voice": "Charon", "style": (
        "Lee en español latinoamericano neutro, voz masculina tensa y urgente, "
        "como un mensaje de emergencia grabado, con miedo contenido:")},
    "DOBLE": {"voice": "Charon", "style": (
        "Lee en español latinoamericano neutro, voz masculina serena, fría y "
        "triste, muy cerca del micrófono, lentamente:")},
    "ARCHIVO": {"voice": "Charon", "style": (
        "Lee en español latinoamericano neutro, voz masculina cansada y llena "
        "de culpa, como una confesión grabada en video:")},
    "MUJER": {"voice": "Kore", "style": (
        "Lee en español latinoamericano neutro, voz femenina joven, sin aliento, "
        "esperanzada y asustada, como por una radio de emergencia:")},
}

# ------------------------------------------------------------- episodes ----
# shot keys:
#   id, dur (seconds used in the edit), gen (seconds generated),
#   frame  -> keyframe (first frame) image prompt
#   motion -> what moves / camera move, sent to the video model
#   ref    -> True when Elías appears (anchor image is passed as reference)
#   sfx    -> list of (time_in_shot, sound_name, gain_db)
#   amb    -> ambience bed for the shot
# narration: list of (start, voice, text)
# overlays : on-screen graphic text (start, end, text, style)
# music    : cue sheet for the original score

EPISODES = [
# ============================================================== EP 01 =====
{
 "num": 1,
 "code": "EP01",
 "title": "EL DÍA QUE TERMINÓ TODO",
 "next": "EP. 2 · NO ESTAMOS SOLOS",
 "logline": "Elías sale de su refugio por provisiones y una radio olvidada le "
            "devuelve la primera voz humana en cinco años... con una advertencia.",
 "thumb_shot": "S10",
 "thumb_text": ["NO CONFÍES", "EN LOS", "SOBREVIVIENTES"],
 "shots": [
  {"id": "S01", "dur": 3.0, "gen": 4, "ref": False, "amb": "rain",
   "frame": "Macro close-up of an old military field radio lying on wet cracked "
            "concrete inside a ruined building, its round amber frequency dial "
            "glowing in darkness, rain drops splashing around it, rust and moss "
            "on the casing.",
   "motion": "Very slow push-in towards the glowing dial, the needle trembles, "
             "rain drops hit the casing, dust drifts in a thin beam of light.",
   "sfx": [(0.0, "static_burst", -4), (0.0, "radio_tune", -8)]},
  {"id": "S02", "dur": 3.5, "gen": 4, "ref": True, "amb": "hum",
   "frame": "Extreme close-up of Elías lying on a narrow cot inside a dark "
            "concrete underground bunker, his eyes opening, a red emergency "
            "lamp pulsing on the wall and painting half his face red.",
   "motion": "His eyes open slowly and he exhales; the red light pulses; "
             "subtle slow push-in.",
   "sfx": [(0.2, "heartbeat", -10)]},
  {"id": "S03", "dur": 4.5, "gen": 6, "ref": True, "amb": "wind",
   "frame": "Low-angle shot from inside a concrete shaft looking up: Elías "
            "pushes open a heavy rusted steel hatch, grey daylight and dust "
            "pouring down around his silhouette.",
   "motion": "The heavy hatch swings open, dust and dry leaves fall into the "
             "shaft, he climbs up into the light; camera holds steady then "
             "tilts up slightly.",
   "sfx": [(0.3, "hatch_open", -3), (1.6, "metal_creak", -8)]},
  {"id": "S04", "dur": 5.0, "gen": 6, "ref": False, "amb": "wind",
   "frame": "Epic extreme wide aerial shot of a destroyed Latin American "
            "megacity in 2042: collapsed skyscrapers wrapped in vines and "
            "trees, rusted cars on a broken elevated highway, low fog between "
            "buildings, a single tiny human figure walking across the overpass.",
   "motion": "Slow majestic aerial drone glide forward and down over the "
             "ruins, birds circling far away, fog moving between towers.",
   "sfx": [(0.0, "whoosh", -10)]},
  {"id": "S05", "dur": 4.0, "gen": 6, "ref": True, "amb": "wind",
   "frame": "Ground-level close tracking shot of Elías's scuffed brown leather "
            "boots stepping carefully over broken glass, ivy and puddles on a "
            "cracked street, the puddles reflecting a grey sky.",
   "motion": "Camera tracks low alongside his boots as they step slowly; "
             "a puddle ripples; glass shards shift.",
   "sfx": [(0.3, "footstep_glass", -6), (1.3, "footstep_glass", -7),
           (2.3, "footstep_glass", -6), (3.3, "footstep_glass", -7)]},
  {"id": "S06", "dur": 4.5, "gen": 6, "ref": True, "amb": "wind",
   "frame": "Medium shot of Elías walking towards camera between rows of "
            "rusted abandoned cars covered in vines on a foggy avenue, his "
            "scarf moving in the wind, watchful eyes, rucksack on his back.",
   "motion": "Smooth slow dolly backwards in front of him as he walks; wind "
             "moves his scarf and the vines; fog drifts.",
   "sfx": [(0.4, "footstep", -9), (1.4, "footstep", -9), (2.4, "footstep", -9),
           (3.4, "footstep", -9)]},
  {"id": "S07", "dur": 4.5, "gen": 6, "ref": True, "amb": "drip",
   "frame": "Interior of a looted abandoned supermarket with a collapsed "
            "ceiling, shafts of grey daylight full of dust, empty overturned "
            "shelves; Elías crouches and picks up a dented food can.",
   "motion": "He wipes the dust off the can and puts it in his rucksack; "
             "slow lateral tracking shot; dust particles float in light shafts.",
   "sfx": [(1.0, "can_pick", -6), (2.6, "metal_creak", -12),
           (3.2, "static_burst", -6)]},
  {"id": "S08", "dur": 3.5, "gen": 4, "ref": True, "amb": "drip",
   "frame": "Close-up profile of Elías in the dim supermarket, frozen, "
            "turning his head sharply towards an off-screen sound, shallow "
            "depth of field, dust in the air.",
   "motion": "He turns his head quickly but naturally towards the sound and "
             "holds his breath; rack focus to his eyes.",
   "sfx": [(0.0, "static_burst", -3), (0.6, "radio_tune", -6)]},
  {"id": "S09", "dur": 5.0, "gen": 6, "ref": False, "amb": "hum",
   "frame": "The same old military field radio sitting on a dusty checkout "
            "counter under a broken skylight, amber dial glowing, beam of "
            "light with dust, a gloved hand entering frame from the right.",
   "motion": "Slow push-in on the radio; the black fingerless-gloved hand "
             "reaches in and gently turns the tuning knob; dial needle moves.",
   "sfx": [(0.2, "radio_tune", -4)]},
  {"id": "S10", "dur": 5.0, "gen": 6, "ref": True, "amb": "hum",
   "frame": "Extreme emotional close-up of Elías's face lit by warm amber "
            "light from the radio dial below, the scar on his left eyebrow "
            "visible, eyes wet with hope and fear, dust floating.",
   "motion": "Very slow push-in on his face; his lips part, his eyes glisten; "
             "his breathing becomes faster.",
   "sfx": [(0.0, "heartbeat", -8)]},
  {"id": "S11", "dur": 4.0, "gen": 6, "ref": False, "amb": "drip",
   "frame": "Dark aisle of the abandoned supermarket seen from behind a "
            "shelf, backlit fog at the far end, a dented can slowly rolling "
            "across the dirty floor towards camera.",
   "motion": "The can rolls slowly across the floor and stops; fog shifts at "
             "the end of the aisle; camera very slowly pushes in.",
   "sfx": [(0.0, "can_roll", -4), (1.6, "glass_crunch", -2)]},
  {"id": "S12", "dur": 4.0, "gen": 6, "ref": True, "amb": "drip",
   "frame": "Close-up of Elías from the front, eyes wide, frozen, the radio's "
            "amber glow on his face; behind him, out of focus in a fog-filled "
            "backlit doorway, a tall dark human silhouette stands still.",
   "motion": "He slowly starts turning his head; rack focus from his face to "
             "the motionless silhouette in the background.",
   "sfx": [(0.0, "heartbeat", -6), (1.2, "footstep_glass", -6)]},
  {"id": "S13", "dur": 3.5, "gen": 4, "ref": False, "amb": "drip",
   "frame": "Wide shot of the empty fog-filled supermarket aisle, backlit by "
            "cold daylight from a doorway, a long human shadow stretched "
            "across the floor towards camera.",
   "motion": "The shadow on the floor moves one step closer; fog swirls; "
             "camera holds still.",
   "sfx": [(0.0, "boom_hit", 0)]},
 ],
 "narration": [
  (0.15, "RADIO", "No confíes en los sobrevivientes."),
  (3.20, "N", "Hace cinco años que el mundo se quedó en silencio."),
  (6.80, "N", "Hoy salí a buscar comida… y encontré algo peor."),
  (11.20, "N", "La ciudad ya no es nuestra."),
  (13.40, "N", "Es del óxido, de la hierba… y del viento."),
  (16.60, "N", "Aprendí a caminar sin hacer ruido."),
  (20.30, "N", "Aprendí a no esperar a nadie."),
  (25.80, "N", "Hasta que el silencio se rompió."),
  (33.20, "RADIO", "Si alguien puede escucharme…"),
  (38.10, "RADIO", "…no confíes en los sobrevivientes."),
  (41.30, "N", "¿Sobrevivientes? Aquí no queda nadie."),
  (44.90, "N", "Entonces lo escuché. Detrás de mí."),
  (48.20, "RADIO", "Elías… no te des la vuelta."),
 ],
 "overlays": [
  (0.0, 2.9, "LOS ÚLTIMOS", "title"),
  (11.2, 14.8, "AÑO 2042 · DÍA 1.847", "card"),
 ],
 "music": {"tension_start": 25.0, "riser": (44.0, 50.5), "hits": [0.0, 32.5, 50.5],
           "end_card": 54.0},
},
# ============================================================== EP 02 =====
{
 "num": 2,
 "code": "EP02",
 "title": "NO ESTAMOS SOLOS",
 "next": "EP. 3 · LA VERDAD",
 "logline": "Elías sigue la señal hasta un refugio subterráneo lleno de rostros "
            "desaparecidos... y encuentra una foto suya tomada hace tres días.",
 "thumb_shot": "S10",
 "thumb_text": ["ESTA FOTO", "ES DE", "HACE 3 DÍAS"],
 "shots": [
  {"id": "S01", "dur": 3.0, "gen": 4, "ref": False, "amb": "rain",
   "frame": "Extreme close-up of the speaker grille of the old military field "
            "radio at night, rain drops on it, a small red LED blinking and the "
            "amber dial glowing.",
   "motion": "Slow push-in; the red LED blinks; the speaker grille vibrates "
             "with static; rain drops slide down.",
   "sfx": [(0.0, "static_burst", -3)]},
  {"id": "S02", "dur": 4.5, "gen": 6, "ref": True, "amb": "rain",
   "frame": "Night, heavy rain: Elías walks along a flooded, ruined avenue "
            "holding the old field radio up in front of him, its amber dial "
            "lighting his wet face, antenna extended, distant lightning "
            "behind collapsed towers.",
   "motion": "Slow tracking shot in front of him as he walks through ankle-deep "
             "water; rain falls; lightning flashes softly in the distance.",
   "sfx": [(0.5, "footstep_water", -7), (1.5, "footstep_water", -7),
           (2.5, "footstep_water", -7), (3.5, "footstep_water", -7),
           (1.0, "thunder", -6)]},
  {"id": "S03", "dur": 4.5, "gen": 6, "ref": True, "amb": "rain",
   "frame": "Wide shot of the entrance of an abandoned metro station half "
            "swallowed by vines and roots, its stairs descending into total "
            "darkness, fog; Elías stands at the top holding a flashlight.",
   "motion": "He switches on his flashlight and the beam cuts the fog down the "
             "stairs; slow push-in from behind.",
   "sfx": [(0.8, "flashlight_click", -4), (1.0, "whoosh", -12)]},
  {"id": "S04", "dur": 4.0, "gen": 6, "ref": True, "amb": "drip",
   "frame": "Tracking shot from behind Elías descending broken metro stairs "
            "into darkness, flashlight beam cutting through fog and dust, "
            "water dripping from the ceiling, old tiles covered in moss.",
   "motion": "Camera follows him down the stairs smoothly; water drips through "
             "the flashlight beam.",
   "sfx": [(0.3, "footstep", -7), (1.1, "footstep", -7), (1.9, "footstep", -7),
           (2.7, "footstep", -7), (3.5, "footstep", -7)]},
  {"id": "S05", "dur": 4.0, "gen": 6, "ref": True, "amb": "hum",
   "frame": "A heavy rusted blast door in an underground tunnel, slightly "
            "ajar, with a faded stencil number seven painted on it; Elías's "
            "gloved hand pushes it open, flashlight light spilling inside.",
   "motion": "The heavy door slowly swings open with resistance; a flickering "
             "fluorescent light inside turns on.",
   "sfx": [(0.2, "door_heavy", -2), (2.4, "fluorescent", -6)]},
  {"id": "S06", "dur": 5.0, "gen": 6, "ref": True, "amb": "hum",
   "frame": "Inside a cramped underground shelter: old metal cots, maps pinned "
            "to concrete walls, dusty CRT monitors, and an entire wall covered "
            "with dozens of photographs of different people connected with red "
            "string; Elías stands in front of it, small in frame, flashlight raised.",
   "motion": "Slow dolly forward towards the photo wall as his flashlight beam "
             "sweeps across the faces; dust floats.",
   "sfx": [(0.5, "paper_rustle", -10)]},
  {"id": "S07", "dur": 4.0, "gen": 6, "ref": False, "amb": "hum",
   "frame": "Overhead close-up of black fingerless-gloved hands opening a thick "
            "worn manila folder full of typed documents with redacted black "
            "bars and red stamps, on a metal desk under a flashlight beam.",
   "motion": "The hands flip pages slowly; dust lifts from the paper.",
   "sfx": [(0.3, "paper_rustle", -4), (2.0, "paper_rustle", -6)]},
  {"id": "S08", "dur": 4.0, "gen": 6, "ref": False, "amb": "hum",
   "frame": "Macro shot of a typed classified document page with heavy black "
            "redaction bars and a blood-red rubber stamp, a world map diagram "
            "with red zones, lit by a flashlight beam.",
   "motion": "Very slow lateral glide across the page, flashlight beam moves "
             "over the red stamp.",
   "sfx": [(0.0, "low_drone_swell", -6)]},
  {"id": "S09", "dur": 4.5, "gen": 6, "ref": True, "amb": "hum",
   "frame": "Close-up of Elías's face lit from below by the bounce of his "
            "flashlight on paper, scar on his left eyebrow, horror slowly "
            "growing in his eyes, dark shelter behind him.",
   "motion": "Slow push-in; his eyes move as he reads, then stop and look up "
             "at something on the wall.",
   "sfx": [(1.0, "heartbeat", -9)]},
  {"id": "S10", "dur": 4.5, "gen": 6, "ref": True, "amb": "hum",
   "frame": "Close-up of a gloved hand pulling an instant polaroid photograph "
            "off the photo wall; the polaroid clearly shows Elías from behind, "
            "with his tan rucksack, standing at the rusted hatch of his own "
            "bunker in daylight.",
   "motion": "The hand slowly pulls the polaroid from the pin and brings it "
             "closer to the flashlight; slight tremble.",
   "sfx": [(0.4, "paper_rip", -6)]},
  {"id": "S11", "dur": 4.5, "gen": 6, "ref": False, "amb": "hum",
   "frame": "Extreme close-up of the white border at the back of an instant "
            "photo held by gloved fingers, handwritten ink marks, lit by a "
            "harsh flashlight, deep black background.",
   "motion": "Fingers turn the photo over slowly; flashlight beam trembles.",
   "sfx": [(0.0, "boom_soft", -6)]},
  {"id": "S12", "dur": 4.0, "gen": 6, "ref": False, "amb": "hum",
   "frame": "Dark concrete corridor behind the shelter's doorway, a metal door "
            "at the end with its lever handle; thin cold light leaks from "
            "under the door, fog on the floor.",
   "motion": "The lever handle slowly turns down by itself from the other side "
             "and the door begins to open, light spilling into the fog.",
   "sfx": [(0.4, "door_latch", -2), (1.2, "door_creak", -2)]},
  {"id": "S13", "dur": 3.5, "gen": 4, "ref": True, "amb": "hum",
   "frame": "Close-up of Elías frozen with his back to a doorway, holding the "
            "polaroid, eyes wide, his breath visible in the cold air, light "
            "spilling onto his shoulder from behind.",
   "motion": "He stops breathing and his eyes slide sideways towards the door "
             "behind him without turning his head; light grows on his shoulder.",
   "sfx": [(0.3, "footstep", -4), (1.1, "footstep", -4)]},
 ],
 "narration": [
  (0.10, "RADIO", "Elías…"),
  (1.00, "N", "La radio sabía mi nombre."),
  (3.40, "N", "La seguí toda la noche. Cada calle, la señal era más fuerte."),
  (8.20, "N", "Me llevó bajo tierra."),
  (16.30, "N", "Un refugio. Alguien vivió aquí… después del fin."),
  (20.60, "N", "Decenas de rostros. Todos desaparecidos."),
  (25.20, "N", "Y documentos. Sobre el día que terminó todo."),
  (29.20, "N", "No fue un accidente. Alguien lo planeó."),
  (33.40, "N", "Entonces la vi."),
  (37.80, "N", "Una foto mía. Frente a mi refugio."),
  (42.20, "N", "Tomada hace tres días."),
  (44.30, "N", "Atrás decía: «Sujeto doce. Aún no recuerda»."),
  (48.30, "N", "Cinco años solo… y alguien me estaba esperando."),
  (52.00, "DOBLE", "Por fin llegaste, Elías."),
 ],
 "overlays": [
  (0.0, 2.9, "LOS ÚLTIMOS · EP. 2", "title"),
  (25.2, 28.9, "PROTOCOLO ECO\nCLASIFICADO", "stamp"),
  (29.1, 32.9, "LIBERACIÓN CONTROLADA\n14 · 03 · 2037", "stamp"),
  (44.3, 48.1, "SUJETO 12\nAÚN NO RECUERDA", "handwritten"),
 ],
 "music": {"tension_start": 16.0, "riser": (46.0, 52.0), "hits": [0.0, 37.8, 52.0],
           "end_card": 54.0},
},
# ============================================================== EP 03 =====
{
 "num": 3,
 "code": "EP03",
 "title": "LA VERDAD",
 "next": "TEMPORADA 2 · PRÓXIMAMENTE",
 "logline": "El hombre de la puerta tiene su cara. Bajo la ciudad, una "
            "instalación secreta revela quién terminó el mundo... y quién "
            "sigue transmitiendo.",
 "thumb_shot": "S01",
 "thumb_text": ["TENÍA", "MI CARA"],
 "shots": [
  {"id": "S01", "dur": 3.0, "gen": 4, "ref": True, "amb": "hum",
   "frame": "A man stands in an open metal doorway, strongly backlit by cold "
            "white light and fog, his face emerging from the shadow as he "
            "steps forward: he is exactly Elías, identical face, short dark "
            "beard, scar on the left eyebrow, olive-green field jacket.",
   "motion": "The man steps slowly forward out of the backlight and his face "
             "becomes visible; fog swirls around him.",
   "sfx": [(0.0, "boom_hit", -2), (0.6, "footstep", -6)]},
  {"id": "S02", "dur": 4.5, "gen": 6, "ref": True, "amb": "hum",
   "frame": "Close-up of the man with Elías's exact face under a cold white "
            "fluorescent light, calm and deeply sad expression, scar on his "
            "left eyebrow, shallow depth of field, dark corridor behind him.",
   "motion": "He blinks slowly and tilts his head slightly; very subtle "
             "push-in; fluorescent light flickers once.",
   "sfx": [(0.5, "fluorescent", -9)]},
  {"id": "S03", "dur": 4.5, "gen": 6, "ref": True, "amb": "hum",
   "frame": "Long concrete underground corridor with flickering fluorescent "
            "tubes and thick cables along the walls; two men in identical "
            "olive-green jackets walk away from camera towards a far door.",
   "motion": "Slow smooth tracking shot behind the two men as they walk; "
             "fluorescent lights flicker above them.",
   "sfx": [(0.3, "footstep", -8), (1.0, "footstep", -9), (1.7, "footstep", -8),
           (2.4, "footstep", -9), (3.1, "footstep", -8), (3.8, "footstep", -9)]},
  {"id": "S04", "dur": 5.0, "gen": 6, "ref": False, "amb": "facility",
   "frame": "Epic wide shot of a vast secret underground facility still "
            "running: rows of server racks with blinking blue and amber lights, "
            "a giant radio transmitter column in the centre with cables, "
            "volumetric light beams through haze, a tiny human figure on a "
            "catwalk for scale.",
   "motion": "Slow majestic crane movement descending and pushing forward "
             "towards the transmitter; server lights blink; haze drifts.",
   "sfx": [(0.0, "whoosh", -8), (0.5, "low_drone_swell", -6)]},
  {"id": "S05", "dur": 4.5, "gen": 6, "ref": True, "amb": "facility",
   "frame": "Elías seen from behind, small, standing before a huge wall of "
            "monitors showing a glowing world map covered by spreading red "
            "zones and data graphs, the light reflecting on him.",
   "motion": "Slow push-in from behind him; the red zones on the map spread "
             "across continents; monitors flicker.",
   "sfx": [(0.2, "beep", -8), (2.0, "beep", -10)]},
  {"id": "S06", "dur": 4.0, "gen": 6, "ref": False, "amb": "facility",
   "frame": "Close-up of an old radio broadcast console in the facility: a "
            "vintage studio microphone, glowing VU meters and a reel-to-reel "
            "tape machine with its reels turning, red ON AIR lamp lit.",
   "motion": "The tape reels turn slowly; VU meter needles bounce with a "
             "voice; slow lateral glide.",
   "sfx": [(0.0, "tape_start", -5)]},
  {"id": "S07", "dur": 5.0, "gen": 6, "ref": True, "amb": "facility",
   "frame": "An old monitor in the dark facility playing an archival video "
            "log: on the screen, a man with Elías's exact face but clean, "
            "well groomed, beard trimmed, wearing a white lab coat in a bright "
            "laboratory, speaking to the camera with guilt. Scan lines.",
   "motion": "Slow push-in on the monitor; the man on the screen speaks and "
             "lowers his eyes; scan lines roll; screen flickers.",
   "sfx": [(0.0, "crt_on", -4)]},
  {"id": "S08", "dur": 4.5, "gen": 6, "ref": True, "amb": "facility",
   "frame": "Extreme close-up of Elías's face lit by the cold flicker of a "
            "monitor, a single tear running down his cheek, scar on his left "
            "eyebrow, devastated, dust in the air.",
   "motion": "Very slow push-in; a tear rolls down; his jaw tightens; monitor "
             "light flickers on his skin.",
   "sfx": [(0.0, "heartbeat", -9)]},
  {"id": "S09", "dur": 5.0, "gen": 6, "ref": False, "amb": "cryo",
   "frame": "A long row of frosted cryogenic pods in a cold blue-lit chamber, "
            "each pod holding a sleeping man whose face is blurred by frost, "
            "stencilled numbers on each pod, cold mist on the floor.",
   "motion": "Slow lateral dolly along the row of pods; cold mist flows across "
             "the floor; frost glitters.",
   "sfx": [(0.0, "cryo_hiss", -6)]},
  {"id": "S10", "dur": 4.5, "gen": 6, "ref": False, "amb": "cryo",
   "frame": "An open, empty cryogenic pod with the large stencilled number 12 "
            "on it, thick white cold mist pouring out of it onto the floor, "
            "blue light, frost on the glass door.",
   "motion": "Cold mist pours out slowly over the edge of the pod; slow push-in "
             "towards the number.",
   "sfx": [(0.0, "cryo_hiss", -4)]},
  {"id": "S11", "dur": 4.5, "gen": 6, "ref": False, "amb": "facility",
   "frame": "The radio console: a second waveform appears on an old oscilloscope "
            "screen and a red warning lamp starts blinking, amber dial "
            "glowing, dark facility around.",
   "motion": "The red lamp blinks; the oscilloscope waveform jumps alive; the "
             "dial needle swings.",
   "sfx": [(0.0, "alarm_soft", -8), (0.2, "static_burst", -5)]},
  {"id": "S12", "dur": 5.5, "gen": 6, "ref": True, "amb": "facility",
   "frame": "Extreme close-up of Elías's face lit by a blinking red light, "
            "tears on his cheek, he looks up with a mix of hope and fear, "
            "scar on his left eyebrow, shallow depth of field.",
   "motion": "Slow push-in; he raises his eyes; the red light blinks on his "
             "face; his breathing stops.",
   "sfx": [(0.0, "heartbeat", -7)]},
 ],
 "narration": [
  (0.15, "N", "El hombre de la puerta tenía mi cara."),
  (3.30, "DOBLE", "Soy el número once. Tú eres el doce."),
  (7.70, "N", "Me llevó más abajo. A un lugar que seguía vivo."),
  (12.30, "N", "Servidores encendidos. Y una antena… transmitiendo al mundo entero."),
  (17.30, "N", "El fin del mundo no fue un accidente. Tenía nombre."),
  (21.60, "RADIO", "No confíes en los sobrevivientes."),
  (23.70, "N", "Era una grabación."),
  (25.80, "ARCHIVO", "Me llamo Elías Varela. Yo provoqué la catástrofe."),
  (30.40, "ARCHIVO", "Si escuchas esto, eres una copia. Perdóname."),
  (33.70, "N", "Era mi voz."),
  (35.30, "N", "Doce copias. Cada una despertó sola… creyendo ser el último."),
  (40.30, "DOBLE", "La radio nos mantenía separados. Para que nunca supiéramos."),
  (44.80, "MUJER", "¿Hola? ¿Alguien me escucha? Somos cuarenta… y somos humanos."),
  (50.00, "N", "No éramos los últimos."),
  (52.20, "DOBLE", "Y el original… sigue vivo."),
 ],
 "overlays": [
  (0.0, 2.9, "LOS ÚLTIMOS · EP. 3", "title"),
  (17.3, 21.4, "PROTOCOLO ECO\nINICIO: 14 · 03 · 2037", "stamp"),
  (35.3, 39.8, "COPIAS ACTIVAS: 12", "card"),
  (44.6, 49.6, "SEÑAL EXTERNA DETECTADA", "alert"),
 ],
 "music": {"tension_start": 17.0, "riser": (44.5, 54.5), "hits": [0.0, 25.8, 33.7, 50.0],
           "end_card": 54.5},
},
]

END_CARD_SECONDS = 3.0
FPS = 30
W, H = 1080, 1920


def episode(code):
    for e in EPISODES:
        if e["code"] == code:
            return e
    raise KeyError(code)


def shot_starts(ep):
    t, out = 0.0, []
    for s in ep["shots"]:
        out.append(t)
        t += s["dur"]
    return out


def picture_length(ep):
    return sum(s["dur"] for s in ep["shots"])


def total_length(ep):
    return picture_length(ep) + END_CARD_SECONDS


def keyframe_prompt(shot):
    who = ("The man in this image is the same person as in the reference "
           "character sheet: " + CHARACTER_LOCK + " ") if shot["ref"] else ""
    return (f"{STYLE_LOCK}\n\nScene: {shot['frame']}\n{who}"
            "Vertical 9:16 composition, the subject framed for a phone screen. "
            "No text, no watermark, no logos.")


def video_prompt(shot):
    who = ("The man is " + CHARACTER_LOCK + " Keep his face and clothes "
           "exactly as in the first frame. ") if shot["ref"] else ""
    return (f"{shot['frame']} {shot['motion']} {who}{VIDEO_STYLE}")


ANCHOR_PROMPT = (
    STYLE_LOCK + "\n\nCharacter reference sheet on a neutral dark-grey "
    "concrete backdrop, soft cinematic key light from the left: three views of "
    "the same man side by side - front view head-and-shoulders, three-quarter "
    "view, and full body standing. " + CHARACTER_LOCK + " Same face, same "
    "clothes and same rucksack in all three views. No text, no watermark. "
    "Vertical 9:16."
)
