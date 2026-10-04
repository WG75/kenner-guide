#!/usr/bin/env python3
"""Write Warren's Palitoy UK release list as retrieval files.

The list is Warren's own UK record for 1978-1983. He wrote "1978 to 1975";
that means 1978 to 1983. There is no public URL. Reliability is primary for
UK release years. It is not a Variant Villain page.

Carry-forward waves are expanded here, in the file, so the chat does not
have to infer them:

- 1979-1980 first wave is the 1978 first-wave names.
- From 1981 the first wave uses Star Destroyer Commander instead of
  Death Squad Commander.
- 1982 and 1983 first wave also drop Artoo-Detoo (R2-D2) and
  See-Threepio (C-3PO).
- Second wave, wherever it is carried, is the 1979 second-wave names.
- 1980 third wave and 1981 third wave are the names written for those years.
- 1982 and 1983 "third wave" is those two lists combined.
- 1983 fourth wave is the 1982 fourth-wave names.
- "not released" is kept only on the years Warren wrote it. A later carry
  of that same line is status "not stated", with a note that he did not
  repeat the words.

Names are normalised. The original spelling stays in a note.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE_DIR = ROOT / "data-source"
OUT_DIR = DATA / "references"
MAX_CHARS = 6800
RECORDED = "2026-10-04"
CITATION = "Warren UK list | primary | 2026-10-04 | no URL"

SOURCE = {
    "name": "Warren's Palitoy UK release list",
    "reliability": "primary",
    "recorded": RECORDED,
    "url": None,
    "note": (
        'Warren wrote "1978 to 1975", meaning 1978 to 1983. '
        "His own UK list. No public URL. Not a Variant Villain page."
    ),
}


def entry(name, kind, line, year, wave="", status="released", notes=None, aliases=None):
    return {
        "name": name,
        "kind": kind,
        "line": line,
        "year": year,
        "wave": wave,
        "status": status,
        "notes": list(notes or []),
        "aliases": list(aliases or []),
    }


ITEMS = []


def add(name, kind, line, year, wave="", status="released", notes=None, aliases=None):
    ITEMS.append(entry(name, kind, line, year, wave, status, notes, aliases))


def add_many(names, kind, line, year, wave="", status="released", notes=None, aliases=None):
    shared = list(notes or [])
    for name in names:
        extra_notes = shared
        extra_aliases = list(aliases or [])
        if isinstance(name, tuple):
            label = name[0]
            extra_notes = shared + list(name[1] if len(name) > 1 else [])
            if len(name) > 2:
                extra_aliases = extra_aliases + list(name[2])
        else:
            label = name
        add(label, kind, line, year, wave, status, extra_notes, extra_aliases)


MASKS_1978 = [
    ("Darth Vader", ["Palitoy display box."]),
    ("Stormtrooper", ["Palitoy display box."]),
    ("C-3PO", ["Palitoy display box."]),
    (
        "Sand People",
        ["Palitoy display box. Warren wrote Sandpeople."],
        ["Sandpeople"],
    ),
    ("Chewbacca", ["Palitoy display box."]),
]

FIRST_WAVE = [
    "Han Solo",
    "Luke Skywalker",
    "Princess Leia Organa",
    "Ben (Obi-Wan) Kenobi",
    (
        "Artoo-Detoo (R2-D2)",
        ["Card name kept."],
        ["R2-D2", "Artoo-Detoo", "Artoo Detoo"],
    ),
    (
        "See-Threepio (C-3PO)",
        ["Card name kept."],
        ["C-3PO", "See-Threepio", "See Threepio"],
    ),
    "Darth Vader",
    "Death Squad Commander",
    "Jawa",
    "Stormtrooper",
    "Sand People",
]

FIRST_WAVE_RENAMED = []
for figure in FIRST_WAVE:
    label = figure[0] if isinstance(figure, tuple) else figure
    if label == "Death Squad Commander":
        FIRST_WAVE_RENAMED.append(
            (
                "Star Destroyer Commander",
                ["Death Squad Commander on the earlier first wave. Warren said the name changed."],
                ["Death Squad Commander"],
            )
        )
    else:
        FIRST_WAVE_RENAMED.append(figure)

DROIDS = {"Artoo-Detoo (R2-D2)", "See-Threepio (C-3PO)"}
FIRST_WAVE_NO_DROIDS = [
    figure
    for figure in FIRST_WAVE_RENAMED
    if (figure[0] if isinstance(figure, tuple) else figure) not in DROIDS
]

SECOND_WAVE = [
    "Hammerhead",
    "Snaggletooth",
    "Walrus Man",
    "Greedo",
    "Power Droid",
    "Death Star Droid",
    "R5-D4",
    (
        "Luke Skywalker (X-Wing Pilot)",
        ["Warren wrote Luke Skywalker X-Wing Pilot."],
        ["Luke Skywalker X-Wing Pilot", "Luke X-Wing Pilot"],
    ),
]

THIRD_1980 = [
    "Han Solo (Hoth Outfit)",
    "Luke Skywalker (Bespin Fatigues)",
    (
        "Princess Leia Organa (Bespin Gown)",
        ["Warren wrote Leia Organa (Bespin Gown)."],
        ["Leia Organa (Bespin Gown)", "Leia Bespin", "Bespin Leia"],
    ),
    "Lando Calrissian",
    "Rebel Soldier (Hoth Battle Gear)",
    "Imperial Stormtrooper (Hoth Battle Gear)",
    "FX-7 (Medical Droid)",
    (
        "IG-88 (Bounty Hunter)",
        [],
        ["IG-88"],
    ),
    "Bespin Security Guard",
    "Bossk (Bounty Hunter)",
    "Boba Fett",
]

THIRD_1981 = [
    "Dengar",
    "Lobot",
    "Yoda",
    "Han Solo (Bespin Outfit)",
    "Ugnaught",
    "2-1B",
    "AT-AT Driver",
    "Imperial Commander",
    "Rebel Commander",
    (
        "Princess Leia Organa (Hoth Outfit)",
        ["Warren wrote Leia (Hoth Outfit)."],
        ["Leia (Hoth Outfit)", "Leia Hoth", "Hoth Leia"],
    ),
    "Bespin Security Guard",
]


def wave_names(wave):
    out = []
    for figure in wave:
        out.append(figure[0] if isinstance(figure, tuple) else figure)
    return out


THIRD_COMBINED = list(THIRD_1980)
seen_third = set(wave_names(THIRD_1980))
for figure in THIRD_1981:
    label = figure[0] if isinstance(figure, tuple) else figure
    if label in seen_third:
        continue
    THIRD_COMBINED.append(figure)
    seen_third.add(label)

FOURTH_WAVE = [
    "Luke Skywalker (Hoth Battle Gear)",
    "AT-AT Commander",
    (
        "Cloud Car Pilot",
        ["Warren wrote (Twin-Pod) Cloud Car Pilot."],
        ["Twin-Pod Cloud Car Pilot", "Twin Pod Cloud Car Pilot"],
    ),
    "Bespin Security Guard",
    "Imperial TIE Fighter Pilot",
    (
        "Artoo-Detoo (R2-D2) with Sensorscope",
        ["Card name kept."],
        ["R2-D2 with Sensorscope", "R2-D2 Sensorscope", "Sensorscope"],
    ),
    (
        "C-3PO with Removable Limbs",
        [],
        ["C-3PO Removable Limbs"],
    ),
    (
        "4-LOM",
        ["Warren wrote 4-Lom."],
        ["4-Lom", "4LOM", "4 Lom"],
    ),
    "Zuckuss",
]

FIFTH_WAVE = [
    "Gamorrean Guard",
    "Bib Fortuna",
    "Emperor's Royal Guard",
    "Admiral Ackbar",
    "Chief Chirpa",
    "Logray (Ewok Medicine Man)",
    "Klaatu",
    "Princess Leia Organa (Boushh Disguise)",
    (
        "Rebel Commando",
        ["Listed twice on Warren's 1983 fifth wave. Stored once."],
    ),
    "Weequay",
    "General Madine",
    (
        "Ree Yees",
        ["Warren wrote Ree-Yees."],
        ["Ree-Yees", "ReeYees"],
    ),
    "Biker Scout",
    (
        "Nien Nunb",
        ["Warren wrote Nien Numb."],
        ["Nien Numb", "Nien Nunb"],
    ),
    "Lando Calrissian (Skiff Guard Outfit)",
    "Luke Skywalker (Jedi Knight Outfit)",
    "Squid Head",
]

DIE_CAST_FIRST = [
    ("X-Wing Fighter", ["Die-cast."], ["X-Wing", "X Wing"]),
    ("TIE Fighter", ["Die-cast."], ["TIE"]),
    ("Darth Vader TIE Fighter", ["Die-cast."], ["Vader TIE", "Darth Vader TIE"]),
    (
        "Landspeeder",
        ["Die-cast. Warren wrote Landspeeder."],
        ["Land Speeder"],
    ),
]
DIE_CAST_SECOND = [
    "Imperial Cruiser",
    ("Millennium Falcon", ["Die-cast."], ["Falcon", "Millenium Falcon"]),
    ("Y-Wing", ["Die-cast."], ["Y Wing", "Y-Wing Fighter"]),
]
DIE_CAST_THIRD = [
    (
        "Twin-Pod Cloud Car",
        ["Die-cast. Warren wrote Twin-Pod."],
        ["Twin-Pod", "Twin Pod"],
    ),
    (
        "Slave I",
        ["Die-cast. Warren wrote Slave One."],
        ["Slave One", "Slave 1"],
    ),
    ("Snowspeeder", ["Die-cast."], ["Rebel Armoured Snowspeeder"]),
    ("TIE Bomber", ["Die-cast."], ["Tie Bomber"]),
]

LARGE_FIRST = ["Luke Skywalker", "Princess Leia"]
LARGE_SECOND = [
    ("Boba Fett", ["Large size."]),
    (
        "IG-88",
        ["Large size."],
        ["IG88"],
    ),
]


def add_masks(year, line, repeat=False):
    for name, notes, *rest in [(m[0], m[1], *m[2:]) for m in MASKS_1978]:
        aliases = rest[0] if rest else []
        use_notes = list(notes)
        if repeat:
            use_notes = ["Same five masks as 1978."] + [
                note for note in use_notes if note != "Palitoy display box."
            ]
        add(name, "mask", line, year, "", "released", use_notes, aliases)


def add_light_saber(year, line):
    add(
        "Light Saber",
        "weapon",
        line,
        year,
        "",
        "released",
        ["Warren's spelling of this early saber."],
        ["Lightsaber", "Light Saber"],
    )


def add_force_saber(year, line, loose_word):
    add(
        "The Force Lightsaber",
        "weapon",
        line,
        year,
        "",
        "released",
        [f"Red and yellow. {loose_word}. Sold loose is a sales note, not an unreleased item."],
        ["Force Lightsaber", "Force Lightsabre"],
    )


def add_tie_sticker(year, line_note):
    add(
        "TIE Fighter",
        "vehicle",
        "Kenner with Palitoy sticker",
        year,
        "",
        "released",
        [line_note],
        ["TIE", "Tie Fighter"],
    )


def add_vehicles_1978_79(year):
    add("Land Speeder", "vehicle", "Palitoy SW", year, "", "released", aliases=["Landspeeder"])
    add(
        "X-Wing Fighter",
        "vehicle",
        "Palitoy SW",
        year,
        "",
        "released",
        aliases=["X-Wing", "X Wing"],
    )
    add("Death Star", "playset", "Palitoy SW", year)


def add_playsets_sw(year):
    for name in ["Cantina", "Land of the Jawas", "Droid Factory"]:
        add(name, "playset", "Palitoy SW", year)
    add(
        "Imperial Troop Transporter",
        "vehicle",
        "Palitoy SW",
        year,
        aliases=["ITT", "Troop Transporter"],
    )


def add_die_cast(year, waves, line, bomber_status=None, bomber_note=None):
    lists = {"first": DIE_CAST_FIRST, "second": DIE_CAST_SECOND, "third": DIE_CAST_THIRD}
    for wave in waves:
        for figure in lists[wave]:
            label = figure[0] if isinstance(figure, tuple) else figure
            notes = list(figure[1]) if isinstance(figure, tuple) and len(figure) > 1 else ["Die-cast."]
            aliases = list(figure[2]) if isinstance(figure, tuple) and len(figure) > 2 else []
            status = "released"
            if label == "TIE Bomber" and bomber_status:
                status = bomber_status
                if bomber_note:
                    notes = notes + [bomber_note]
            add(label, "die-cast", line, year, wave, status, notes, aliases)


def add_crafts_unconfirmed(year):
    add(
        "Yoda",
        "craft",
        "Palitoy ESB",
        year,
        "",
        "unconfirmed",
        ["Craft Master figurine. Warren marked this ESB unconfirmed."],
        ["Craft Master Yoda"],
    )
    add(
        "Luke Skywalker on Tauntaun",
        "craft",
        "Palitoy ESB",
        year,
        "",
        "unconfirmed",
        ["Craft Master figurine. Warren marked this ESB unconfirmed."],
        ["Craft Master Luke", "Luke on Tauntaun"],
    )
    add(
        "Glow Paint by Numbers Craft Master",
        "craft",
        "Palitoy ESB",
        year,
        "",
        "unconfirmed",
        [
            "Subjects Warren named: Luke, Vader, Han, Leia. He marked this ESB unconfirmed."
        ],
        ["Glow Paint by Numbers", "Paint by Numbers"],
    )


# --- 1978 ---
add_masks(1978, "Palitoy SW")
add("Dip Dots painting set", "craft", "Palitoy SW", 1978, aliases=["Dip Dots"])
add("Keel kite", "other", "Palitoy SW", 1978, aliases=["kite", "Keel"])
add(
    "Poster art set",
    "craft",
    "Palitoy SW",
    1978,
    notes=["Warren wrote Playnts. That spelling is kept as his wording."],
    aliases=["Playnts", "Poster art"],
)
add("Play-Doh set", "craft", "Palitoy SW", 1978, aliases=["Play-Doh", "Play Doh"])
for game in [
    "Escape the Death Star game",
    "The Adventures of R2-D2 game",
    "Destroy the Death Star game",
]:
    add(game, "game", "Palitoy SW", 1978, aliases=[game.replace(" game", "")])
add_light_saber(1978, "Palitoy SW")
add_many(FIRST_WAVE, "figure", "Palitoy SW", 1978, "first")
add_vehicles_1978_79(1978)
add_tie_sticker(1978, "Kenner box with a Palitoy sticker.")
add_many(LARGE_FIRST, "large-figure", "Palitoy SW", 1978, "first", notes=["Large size action figure."])

# --- 1979 ---
add_masks(1979, "Palitoy SW", repeat=True)
add("3D Poster Art", "craft", "Palitoy SW", 1979, aliases=["3D poster"])
add("Dip Dots painting set", "craft", "Palitoy SW", 1979, aliases=["Dip Dots"])
add_light_saber(1979, "Palitoy SW")
add_many(
    FIRST_WAVE,
    "figure",
    "Palitoy SW",
    1979,
    "first",
    notes=["Carried as the first wave."],
)
add_many(SECOND_WAVE, "figure", "Palitoy SW", 1979, "second")
add_vehicles_1978_79(1979)
add_tie_sticker(1979, "Kenner box with a Palitoy sticker. Warren wrote Kenner w/ Palitoy sticker.")
add_many(LARGE_FIRST, "large-figure", "Palitoy SW", 1979, "first", notes=["Large size action figure. Carried first wave."])
add_die_cast(1979, ["first", "second"], "Palitoy SW")
add("Blaster Pistol", "weapon", "Palitoy SW", 1979, aliases=["Blaster"])
add(
    "Three Position Laser Rifle",
    "weapon",
    "Palitoy SW",
    1979,
    aliases=["Laser Rifle", "Three Position Rifle"],
)
add("Radio Controlled R2-D2", "other", "Palitoy SW", 1979, aliases=["RC R2-D2", "Radio Controlled R2"])
add("Talking R2-D2", "other", "Palitoy SW", 1979, aliases=["Talking R2"])
add(
    "Darth Vader TIE Fighter",
    "vehicle",
    "Palitoy SW",
    1979,
    aliases=["Vader TIE Fighter", "Darth Vader TIE"],
)
add_playsets_sw(1979)

# --- 1980 ---
add_many(FIRST_WAVE, "figure", "Palitoy SW", 1980, "first", notes=["Warren marked this wave Palitoy SW."])
add_many(SECOND_WAVE, "figure", "Palitoy SW", 1980, "second", notes=["Warren marked this wave Palitoy SW."])
add_many(THIRD_1980, "figure", "Palitoy ESB", 1980, "third", notes=["Warren marked this wave Palitoy ESB."])
add("Land Speeder", "vehicle", "Palitoy SW", 1980, aliases=["Landspeeder"])
add_tie_sticker(1980, "Kenner SW box with a Palitoy sticker.")
add("Death Star", "playset", "Palitoy SW", 1980)
add_many(LARGE_FIRST, "large-figure", "Palitoy SW", 1980, "first", notes=["Large size. Warren marked this wave SW."])
add(
    "Boba Fett",
    "large-figure",
    "Kenner ESB",
    1980,
    "second",
    "released",
    ["Large size. Second wave."],
)
add(
    "IG-88",
    "large-figure",
    "Kenner ESB",
    1980,
    "second",
    "not released",
    ["Large size. Warren marked IG-88 not released."],
    ["IG88"],
)
add_die_cast(1980, ["first", "second"], "Palitoy SW")
add("Blaster Pistol", "weapon", "Palitoy ESB", 1980, aliases=["Blaster"])
add("Three Position Laser Rifle", "weapon", "Palitoy SW", 1980, aliases=["Laser Rifle"])
add("Radio Controlled R2-D2", "other", "Palitoy SW", 1980, aliases=["RC R2-D2"])
add("Talking R2-D2", "other", "Palitoy SW", 1980, aliases=["Talking R2"])
add("Darth Vader TIE Fighter", "vehicle", "Palitoy SW", 1980, aliases=["Vader TIE Fighter"])
add_playsets_sw(1980)
add("Yoda Hand Puppet", "other", "Palitoy ESB", 1980, aliases=["Yoda puppet"])
add("Millennium Falcon", "vehicle", "Palitoy ESB", 1980, aliases=["Falcon", "Millenium Falcon"])
add("Tauntaun", "creature", "Palitoy ESB", 1980)
add(
    "Rebel Armoured Snowspeeder",
    "vehicle",
    "Palitoy ESB",
    1980,
    aliases=["Snowspeeder", "Rebel Armored Snowspeeder"],
)
add(
    "Twin-Pod Cloud Car",
    "vehicle",
    "Palitoy ESB",
    1980,
    notes=["Warren wrote Twin Pod Cloud Car."],
    aliases=["Twin Pod Cloud Car", "Cloud Car"],
)
add("X-Wing Fighter", "vehicle", "Palitoy ESB", 1980, aliases=["X-Wing"])
add_force_saber(1980, "loose", "Sold loose")

# --- 1981 ---
add_many(
    FIRST_WAVE_RENAMED,
    "figure",
    "Palitoy ESB",
    1981,
    "first",
    notes=["Warren marked the first wave ESB."],
)
add_many(SECOND_WAVE, "figure", "Palitoy ESB", 1981, "second", notes=["Warren marked the second wave ESB."])
add_many(THIRD_1981, "figure", "Palitoy ESB", 1981, "third")
add_tie_sticker(1981, "Kenner SW box with a Palitoy sticker.")
add("X-Wing Fighter", "vehicle", "Palitoy ESB", 1981, aliases=["X-Wing"])
add(
    "Boba Fett",
    "large-figure",
    "Kenner ESB",
    1981,
    "second",
    "released",
    ["Large size. Second wave."],
)
add(
    "IG-88",
    "large-figure",
    "Kenner ESB",
    1981,
    "second",
    "not released",
    ["Large size. Warren marked IG-88 not released."],
    ["IG88"],
)
add_die_cast(1981, ["first", "second"], "Palitoy SW")
add_die_cast(
    1981,
    ["third"],
    "Kenner ESB",
    bomber_status="not released",
    bomber_note="Warren marked the TIE Bomber not released.",
)
add("Blaster Pistol", "weapon", "Palitoy ESB", 1981, aliases=["Blaster"])
add("Three Position Laser Rifle", "weapon", "Palitoy SW", 1981, aliases=["Laser Rifle"])
add(
    "Darth Vader TIE Fighter",
    "vehicle",
    "Palitoy SW",
    1981,
    notes=["SW with a Bounty Hunter offer."],
    aliases=["Vader TIE Fighter"],
)
add(
    "Imperial Troop Transporter",
    "vehicle",
    "Palitoy SW",
    1981,
    notes=["SW with a Bounty Hunter offer."],
    aliases=["ITT"],
)
add("Yoda Hand Puppet", "other", "Palitoy ESB", 1981, aliases=["Yoda puppet"])
add("Tauntaun", "creature", "Palitoy ESB", 1981)
add(
    "Rebel Armoured Snowspeeder",
    "vehicle",
    "Palitoy ESB",
    1981,
    aliases=["Snowspeeder"],
)
add(
    "Twin-Pod Cloud Car",
    "vehicle",
    "Palitoy ESB",
    1981,
    aliases=["Twin Pod Cloud Car", "Cloud Car"],
)
add("Turret and Probot playset", "playset", "Palitoy ESB", 1981, aliases=["Turret & Probot", "Probot playset"])
add("Imperial Attack Base", "playset", "Palitoy ESB", 1981, aliases=["Attack Base"])
add_force_saber(1981, "loose", "Loose")
add_crafts_unconfirmed(1981)

# --- 1982 ---
add_many(
    FIRST_WAVE_NO_DROIDS,
    "figure",
    "Palitoy ESB",
    1982,
    "first",
    notes=["First wave minus Artoo-Detoo and See-Threepio. Warren marked this wave ESB."],
)
add_many(SECOND_WAVE, "figure", "Palitoy ESB", 1982, "second", notes=["Carried second wave. Warren marked it ESB."])
add_many(
    THIRD_COMBINED,
    "figure",
    "Palitoy ESB",
    1982,
    "third",
    notes=["Carried third wave: 1980 names plus 1981 names. Warren marked it ESB."],
)
add_many(FOURTH_WAVE, "figure", "Palitoy ESB", 1982, "fourth")
add_tie_sticker(1982, "Kenner SW box with a Palitoy sticker.")
add(
    "Battle Damaged X-Wing Fighter",
    "vehicle",
    "Palitoy ESB",
    1982,
    notes=["White. Warren wrote Battle Damaged X-Wing Fighter white."],
    aliases=["Battle Damaged X-Wing", "X-Wing white"],
)
add(
    "Boba Fett",
    "large-figure",
    "Kenner ESB",
    1982,
    "second",
    "released",
    ["Large size. Carried second wave. Warren marked the line Kenner ESB."],
)
add(
    "IG-88",
    "large-figure",
    "Kenner ESB",
    1982,
    "second",
    "not stated",
    [
        "Large size. Warren carried the second-wave large-size line and did not repeat 'not released' for IG-88. This list does not turn that into a release."
    ],
    ["IG88"],
)
add_die_cast(1982, ["first", "second"], "Palitoy SW")
add_die_cast(
    1982,
    ["third"],
    "Kenner ESB",
    bomber_status="not stated",
    bomber_note="Warren carried the third-wave die-cast line and did not repeat 'not released' for the TIE Bomber. This list does not turn that into a release.",
)
add("Blaster Pistol", "weapon", "Palitoy ESB", 1982, aliases=["Blaster"])
add(
    "Three Position Laser Rifle",
    "weapon",
    "Palitoy SW",
    1982,
    notes=["Warren wrote Laser Rifle."],
    aliases=["Laser Rifle"],
)
add(
    "Darth Vader TIE Fighter",
    "vehicle",
    "Palitoy SW",
    1982,
    notes=["SW, Bounty Hunter offer. Warren wrote Vader TIE Fighter."],
    aliases=["Vader TIE Fighter"],
)
add(
    "Imperial Troop Transporter",
    "vehicle",
    "Palitoy SW",
    1982,
    notes=["SW, Bounty Hunter offer."],
    aliases=["ITT"],
)
add("Yoda Hand Puppet", "other", "Palitoy ESB", 1982, aliases=["Yoda puppet"])
add("Tauntaun", "creature", "Palitoy ESB", 1982)
add("Rebel Armoured Snowspeeder", "vehicle", "Palitoy ESB", 1982, aliases=["Snowspeeder"])
add("Twin-Pod Cloud Car", "vehicle", "Palitoy ESB", 1982, aliases=["Twin Pod Cloud Car", "Cloud Car"])
add_force_saber(1982, "loose", "Loose")
for rig, aliases in [
    ("INT-4 Interceptor", ["INT-4"]),
    ("CAP-2 Captivator", ["CAP-2"]),
    ("MTV-7 Multi-Terrain Vehicle", ["MTV-7"]),
    ("MLC-3 Mobile Laser Cannon", ["MLC-3", "MLC"]),
    ("PDT-8 Personnel Deployment Transport", ["PDT-8"]),
]:
    notes = []
    if rig.startswith("MLC-3"):
        notes = ["Warren wrote MLC Mobile Laser Cannon."]
    add(rig, "mini-rig", "Palitoy ESB", 1982, "", "released", notes, aliases)
add(
    "Tauntaun with Open Belly Rescue Feature",
    "creature",
    "Palitoy ESB",
    1982,
    aliases=["Open Belly Tauntaun", "Tauntaun open belly"],
)
add(
    "Slave I",
    "vehicle",
    "Palitoy ESB",
    1982,
    notes=["Boba Fett's spaceship. Warren wrote Slave 1."],
    aliases=["Slave 1", "Slave One", "Boba Fett's Spaceship"],
)
add("Wampa", "creature", "Palitoy ESB", 1982)
add("Dagobah Action Playset", "playset", "Palitoy ESB", 1982, aliases=["Dagobah"])
add(
    "AT-AT",
    "vehicle",
    "Palitoy ESB",
    1982,
    notes=["Warren wrote AT-AT All Terrain Armoured Transport."],
    aliases=["AT-AT All Terrain Armoured Transport", "All Terrain Armoured Transport"],
)
add("Millennium Falcon", "vehicle", "Palitoy ESB", 1982, aliases=["Falcon"])
add(
    "Darth Vader's Star Destroyer Action Playset",
    "playset",
    "Palitoy ESB",
    1982,
    aliases=["Darth Vader's Star Destroyer", "Star Destroyer Action Playset"],
)

# --- 1983 ---
add_many(
    FIRST_WAVE_NO_DROIDS,
    "figure",
    "Palitoy ROTJ",
    1983,
    "first",
    notes=["First wave minus Artoo-Detoo and See-Threepio. Warren marked this wave ROTJ."],
)
add_many(SECOND_WAVE, "figure", "Palitoy ROTJ", 1983, "second", notes=["Carried second wave. Warren marked it ROTJ."])
add_many(
    THIRD_COMBINED,
    "figure",
    "Palitoy ROTJ",
    1983,
    "third",
    notes=["Carried third wave. Warren marked it ROTJ."],
)
add_many(FOURTH_WAVE, "figure", "Palitoy ROTJ", 1983, "fourth", notes=["Carried fourth wave. Warren marked it ROTJ."])
add_many(FIFTH_WAVE, "figure", "Palitoy ROTJ", 1983, "fifth")

for name, kind, aliases, notes in [
    ("Rebel Armoured Snowspeeder", "vehicle", ["Snowspeeder"], []),
    (
        "Tauntaun with Open Belly Rescue Feature",
        "creature",
        ["Open Belly Tauntaun"],
        [],
    ),
    ("Wampa", "creature", [], []),
    ("Slave I", "vehicle", ["Slave 1", "Slave One"], ["Warren wrote Slave 1."]),
    ("AT-AT", "vehicle", ["AT-AT All Terrain Armoured Transport"], []),
    (
        "Battle Damaged X-Wing Fighter",
        "vehicle",
        ["Battle Damaged X-Wing"],
        ["White and grey. Warren wrote Battle Damaged X-Wing white and grey."],
    ),
    ("Radar Laser Cannon", "mini-rig", ["Radar Laser"], []),
    ("Tri-pod Laser Cannon", "mini-rig", ["Tripod Laser Cannon", "Tri-pod"], ["Warren wrote Tri-pod Laser Cannon."]),
    ("Vehicle Maintenance Energizer", "mini-rig", ["VME"], []),
    ("INT-4 Interceptor", "mini-rig", ["INT-4"], []),
    ("CAP-2 Captivator", "mini-rig", ["CAP-2"], []),
    ("MTV-7 Multi-Terrain Vehicle", "mini-rig", ["MTV-7"], []),
    ("MLC-3 Mobile Laser Cannon", "mini-rig", ["MLC-3"], ["Warren wrote MLC-3."]),
]:
    add(name, kind, "Bilogo", 1983, "", "released", notes, aliases)

add(
    "Darth Vader TIE Fighter",
    "vehicle",
    "Palitoy SW",
    1983,
    notes=["SW with a Bounty Hunter offer."],
    aliases=["Vader TIE Fighter"],
)
add(
    "Darth Vader's Star Destroyer Action Playset",
    "playset",
    "Palitoy ESB",
    1983,
    aliases=["Darth Vader's Star Destroyer"],
)
add("Rebel Transport", "vehicle", "Palitoy ROTJ", 1983, aliases=["Rebel Transport vehicle"])
add("Scout Walker", "vehicle", "Palitoy ROTJ", 1983, aliases=["Scout Walker vehicle"])
add("Jabba the Hutt Action Playset", "playset", "Kenner ROTJ", 1983, aliases=["Jabba the Hutt", "Jabba playset"])
add("Speeder Bike", "vehicle", "Kenner ROTJ", 1983)
add(
    "AST-5 Armoured Sentinel Transport",
    "mini-rig",
    "Kenner ROTJ",
    1983,
    aliases=["AST-5"],
)
add(
    "ISP-6 Imperial Shuttle Pod",
    "mini-rig",
    "Kenner ROTJ",
    1983,
    aliases=["ISP-6"],
)


YEAR_INTROS = {
    1978: (
        "Warren did not print a film line on 1978. Items with no other line are stored as Palitoy SW, the original Star Wars range. "
        "The TIE Fighter is the exception: Kenner with a Palitoy sticker."
    ),
    1979: (
        "1979 continues the original range, stored as Palitoy SW where Warren did not name another line. "
        "First-wave figures are the 1978 names. Second-wave figures are the names he listed for 1979."
    ),
    1980: (
        "First and second waves are Palitoy SW. The third wave is the ESB names he listed, stored as Palitoy ESB. "
        "Vehicles keep the line he wrote (SW or ESB)."
    ),
    1981: (
        "Figure waves are Palitoy ESB. The first wave is the 1978 names, with Death Squad Commander changed to Star Destroyer Commander. "
        "The second wave is the 1979 names. The third wave is only the names he listed for 1981, not the 1980 third wave."
    ),
    1982: (
        "Figure waves are Palitoy ESB. The first wave drops Artoo-Detoo (R2-D2) and See-Threepio (C-3PO). "
        "The second wave is the 1979 names. The third wave is the 1980 third-wave names plus the 1981 third-wave names. "
        "The fourth wave is the names he listed for 1982."
    ),
    1983: (
        "First through fourth figure waves are the 1982 waves, stored as Palitoy ROTJ because that is the line he wrote. "
        "The first wave still omits Artoo-Detoo and See-Threepio. The fifth wave is the names he listed for 1983. "
        "Bilogo, Palitoy ESB, Palitoy ROTJ, Palitoy SW and Kenner ROTJ are kept as he labelled them."
    ),
}


def format_item(item, include_aliases=True):
    wave = item["wave"] or "-"
    notes = "; ".join(item["notes"])
    aliases = "; ".join(item["aliases"])
    bits = [
        item["name"],
        item["kind"],
        f"wave: {wave}",
        item["line"],
        item["status"],
        CITATION,
        f"year: {item['year']}",
    ]
    if include_aliases and aliases:
        bits.append(f"aka: {aliases}")
    if notes:
        bits.append(f"note: {notes}")
    return "- " + " | ".join(bits)


def header(title, body_lines, continued=False):
    if continued:
        lines = [
            title,
            f"Source name: {SOURCE['name']}. Source URL: none. Reliability: {SOURCE['reliability']}. Recorded: {SOURCE['recorded']}.",
            "Continued. Each entry still cites Warren UK list | primary | 2026-10-04 | no URL.",
            "",
        ]
    else:
        lines = [
            title,
            f"Source name: {SOURCE['name']}. Source URL: none. Reliability: {SOURCE['reliability']}. Recorded: {SOURCE['recorded']}.",
            SOURCE["note"],
            "Each entry below repeats that source as 'Warren UK list | primary | 2026-10-04 | no URL'.",
            "Repeat unconfirmed, not released, and not stated whenever you answer from an entry. Do not drop a spelling note.",
            *body_lines,
            "",
        ]
    return "\n".join(lines) + "\n"


def split_parts(title, intro_lines, item_lines):
    head = header(title, intro_lines)
    parts = []
    current = head
    for line in item_lines:
        candidate = current + line + "\n"
        if len(candidate) > MAX_CHARS and current != head:
            parts.append(current.rstrip() + "\n")
            current = header(title + " (continued)", intro_lines, continued=True) + line + "\n"
        else:
            current = candidate
    if current.strip():
        parts.append(current.rstrip() + "\n")
    for part in parts:
        if len(part) > 7000:
            raise SystemExit(f"{title} part is {len(part)} characters")
    return parts


def write_parts(stem, parts):
    written = []
    for index, text in enumerate(parts):
        name = f"{stem}.txt" if index == 0 else f"{stem}-{index + 1}.txt"
        path = OUT_DIR / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


def year_files():
    written = []
    for year in range(1978, 1984):
        year_items = [item for item in ITEMS if item["year"] == year]
        lines = [format_item(item) for item in year_items]
        parts = split_parts(
            f"Palitoy UK releases, {year}",
            [YEAR_INTROS[year]],
            lines,
        )
        written.extend(write_parts(f"palitoy-uk-{year}", parts))
    return written


def not_figure_files():
    lines = []
    for item in ITEMS:
        if item["kind"] in ("figure", "large-figure"):
            continue
        lines.append(format_item(item, include_aliases=False))
    parts = split_parts(
        "Palitoy UK items that are not action figures",
        [
            "This file is the non-figure list: masks, crafts, games, weapons, vehicles, playsets, die-cast, mini-rigs, creatures and other toys.",
            "Action figures and large-size action figures are left out. Ask for a year if you need those.",
            "Die-cast vehicles are not action figures. A Kenner box with a Palitoy sticker is still on this list.",
        ],
        lines,
    )
    if len(parts) > 4:
        raise SystemExit(f"not-figures split into {len(parts)} parts; the chat can inject 4")
    return write_parts("palitoy-uk-not-figures", parts)


def when_lines():
    groups = {}
    for item in ITEMS:
        key = (item["name"], item["kind"], item["line"])
        groups.setdefault(key, []).append(item)
    lines = []
    for key in sorted(groups, key=lambda item: (item[0].lower(), item[1], item[2])):
        grouped = groups[key]
        name, kind, line = key
        by_status = {}
        notes = []
        aliases = []
        for item in grouped:
            by_status.setdefault(item["status"], []).append(str(item["year"]))
            for note in item["notes"]:
                if note not in notes:
                    notes.append(note)
            for alias in item["aliases"]:
                if alias not in aliases:
                    aliases.append(alias)
        if len(by_status) == 1:
            status, years = next(iter(by_status.items()))
            status_text = status
            year_text = ", ".join(years)
        else:
            status_text = "mixed"
            year_text = "; ".join(
                f"{', '.join(years)} {status}" for status, years in by_status.items()
            )
        bits = [
            name,
            kind,
            f"wave: -",
            line,
            status_text,
            CITATION,
            f"years: {year_text}",
        ]
        if aliases:
            bits.append("aka: " + "; ".join(aliases))
        if notes:
            bits.append("note: " + "; ".join(notes))
        lines.append("- " + " | ".join(bits))
    return lines


def when_files():
    parts = split_parts(
        "Palitoy UK release years by item",
        [
            "Use this file to answer when Palitoy released an item. Years are UK years from Warren's list.",
            "A mixed status means the status changed by year. Read the years field. Do not treat not stated as released.",
        ],
        when_lines(),
    )
    return write_parts("palitoy-uk-when", parts)


def overview_file():
    counts = {}
    for item in ITEMS:
        counts.setdefault(item["year"], {"all": 0, "figure": 0, "other": 0})
        counts[item["year"]]["all"] += 1
        if item["kind"] in ("figure", "large-figure"):
            counts[item["year"]]["figure"] += 1
        else:
            counts[item["year"]]["other"] += 1
    lines = []
    for year in range(1978, 1984):
        row = counts[year]
        lines.append(
            f"- {year} | {row['all']} entries | figures and large figures: {row['figure']} | other toys: {row['other']} | {CITATION}"
        )
    specials = [
        "- Nien Nunb | figure | 1983 fifth wave | Palitoy ROTJ | released | " + CITATION + " | aka: Nien Numb | note: Warren wrote Nien Numb.",
        "- Ree Yees | figure | 1983 fifth wave | Palitoy ROTJ | released | " + CITATION + " | aka: Ree-Yees | note: Warren wrote Ree-Yees.",
        "- 4-LOM | figure | fourth wave | Palitoy ESB in 1982 and Palitoy ROTJ in 1983 | released | " + CITATION + " | aka: 4-Lom | note: Warren wrote 4-Lom.",
        "- Rebel Commando | figure | 1983 fifth wave | Palitoy ROTJ | released | " + CITATION + " | note: Listed twice on Warren's 1983 fifth wave. Stored once.",
        "- IG-88 large size | large-figure | Kenner ESB | not released in 1980 and 1981 | " + CITATION + " | note: 1982 carries the line as not stated. Warren did not repeat not released.",
        "- TIE Bomber die-cast | die-cast | Kenner ESB | not released in 1981 | " + CITATION + " | note: 1982 carries the line as not stated.",
        "- Craft Master figurines and Glow Paint by Numbers | craft | 1981 | Palitoy ESB | unconfirmed | " + CITATION,
        "- TIE Fighter vehicle | vehicle | Kenner with Palitoy sticker | 1978, 1979, 1980, 1981, 1982 | " + CITATION + " | note: Kenner box with a Palitoy sticker.",
        "- The Force Lightsaber | weapon | loose | 1980, 1981, 1982 | released | " + CITATION + " | note: Red and yellow, sold loose. That is a sales note, not unreleased.",
    ]
    text_parts = split_parts(
        "Palitoy UK release list, overview",
        [
            "Ask for a year (1978 to 1983) for the full list of that year. This overview does not name every toy.",
            "Lines used on the entries: Palitoy SW, Palitoy ESB, Palitoy ROTJ, Bilogo, Kenner with Palitoy sticker, Kenner ESB, Kenner ROTJ, loose.",
            "Bilogo is Warren's line label. This list does not define the company.",
        ],
        lines + specials,
    )
    return write_parts("palitoy-uk-overview", text_parts)


HISTORY = """Palitoy company history

This is a short paraphrase. It is not a copy of the page, and it is not Warren's UK release list. UK toy years are in the Palitoy UK release files. If a release year here conflicts with that list, say the sources disagree and keep his status notes. If a supplied reference disagrees about a variant, a factory or a cardback, Variant Villain wins unless the file says otherwise.

Palitoy was a British toy company. The business began in 1919 in Coalville, Leicestershire, when Alfred Edward Pallett founded the Cascelloid Company. A toy followed in 1920 and a doll in 1925. British Xylonite bought Cascelloid in 1931, and Palitoy was the trademark used from 1935 for the toy side of that business.
Source name: Wikipedia, Palitoy. Source URL: https://en.wikipedia.org/wiki/Palitoy. Reliability: lower. Fetched: 2026-10-04.

General Mills bought Palitoy in 1968, and it sat in that company's toy group. The article describes Palitoy as a maker of popular British toys, including licensed lines, and it names Star Wars figures and Play-Doh among the products. It does not give a year-by-year UK Star Wars release list.
Source name: Wikipedia, Palitoy. Source URL: https://en.wikipedia.org/wiki/Palitoy. Reliability: lower. Fetched: 2026-10-04.

The same article says the design department closed in 1984, leaving mainly sales and marketing. In 1985 General Mills left the toy business. Palitoy took the Kenner Parker name, and on 1 May 1985 most of the Coalville work ended, with manufacturing moved overseas. Tonka bought Kenner Parker, including Palitoy, in 1987. Hasbro bought Tonka in 1991 and closed the old Palitoy site in 1994. Play-Doh production there moved to a Hasbro factory in Ireland.
Source name: Wikipedia, Palitoy. Source URL: https://en.wikipedia.org/wiki/Palitoy. Reliability: lower. Fetched: 2026-10-04.

A Variant Villain figure page already in the reference data describes Palitoy as head of Star Wars European operations for General Mills, and as a Coalville distribution hub. It says the grey-limb Hoth stormtrooper was not produced by Palitoy. That is a figure claim, not a UK release year. If that claim and this history pull in different directions, say the sources disagree. Variant Villain wins on the figure.
Source name: Variant Villain, Imperial Stormtrooper (Hoth Battle Gear). Source URL: https://www.variantvillain.com/characters/esb/imperial-stormtrooper-hoth-battle-gear/. Reliability: high. Recorded: 2026-10-04. Taken from the figure notes already stored. Not a new page fetch.

The Fandom Palitoy article was not used. On 2026-10-04 a polite request for https://starwars.fandom.com/robots.txt came back as a Cloudflare challenge (HTTP 403), so the page was skipped.
Source name: starwars.fandom.com robots check. Source URL: https://starwars.fandom.com/robots.txt. Reliability: lower. Fetched: 2026-10-04. Result: skipped.
"""


def history_file():
    text = HISTORY.strip() + "\n"
    if len(text) > 7000:
        raise SystemExit(f"history is {len(text)} characters")
    path = OUT_DIR / "palitoy-history.txt"
    path.write_text(text, encoding="utf-8")
    return [path]


def check_invariants():
    def names(year, kind=None, status=None):
        found = []
        for item in ITEMS:
            if item["year"] != year:
                continue
            if kind and item["kind"] != kind:
                continue
            if status and item["status"] != status:
                continue
            found.append(item["name"])
        return found

    figure_1981 = names(1981, "figure")
    if "Star Destroyer Commander" not in figure_1981:
        raise SystemExit("1981 first wave missing Star Destroyer Commander")
    if "Death Squad Commander" in figure_1981:
        raise SystemExit("1981 still has Death Squad Commander")
    if figure_1981.count("Bespin Security Guard") != 1:
        raise SystemExit("1981 Bespin Security Guard should appear once")

    for year in (1982, 1983):
        figures = names(year, "figure")
        if "Artoo-Detoo (R2-D2)" in figures or "See-Threepio (C-3PO)" in figures:
            raise SystemExit(f"{year} first wave still has a droid")
        if "Nien Nunb" in figures and year != 1983:
            raise SystemExit("Nien Nunb in the wrong year")
    if names(1983, "figure").count("Rebel Commando") != 1:
        raise SystemExit("Rebel Commando should be stored once")
    if names(1983, "figure").count("Nien Nunb") != 1:
        raise SystemExit("Nien Nunb missing")
    if any(item["name"] == "Nien Numb" for item in ITEMS):
        raise SystemExit("Nien Numb was not normalised")

    def status_of(year, name, kind):
        hits = [
            item["status"]
            for item in ITEMS
            if item["year"] == year and item["name"] == name and item["kind"] == kind
        ]
        if len(hits) != 1:
            raise SystemExit(f"expected one {name} {kind} in {year}, got {hits}")
        return hits[0]

    if status_of(1980, "IG-88", "large-figure") != "not released":
        raise SystemExit("1980 large IG-88")
    if status_of(1981, "IG-88", "large-figure") != "not released":
        raise SystemExit("1981 large IG-88")
    if status_of(1982, "IG-88", "large-figure") != "not stated":
        raise SystemExit("1982 large IG-88")
    if status_of(1981, "TIE Bomber", "die-cast") != "not released":
        raise SystemExit("1981 TIE Bomber")
    if status_of(1982, "TIE Bomber", "die-cast") != "not stated":
        raise SystemExit("1982 TIE Bomber")
    if status_of(1981, "Yoda", "craft") != "unconfirmed":
        raise SystemExit("Craft Master Yoda")
    sticker = [
        item
        for item in ITEMS
        if item["name"] == "TIE Fighter" and item["kind"] == "vehicle"
    ]
    if [item["year"] for item in sticker] != [1978, 1979, 1980, 1981, 1982]:
        raise SystemExit("TIE sticker years")
    if any(item["line"] != "Kenner with Palitoy sticker" for item in sticker):
        raise SystemExit("TIE sticker line")
    for item in ITEMS:
        if not item["name"] or not item["kind"] or not item["line"] or not item["status"]:
            raise SystemExit(f"blank field on {item}")


def clear_old():
    for path in OUT_DIR.glob("palitoy-*.txt"):
        path.unlink()


def main():
    check_invariants()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    clear_old()
    written = []
    written.extend(year_files())
    written.extend(not_figure_files())
    written.extend(when_files())
    written.extend(overview_file())
    written.extend(history_file())
    payload = {
        "source": SOURCE,
        "span": "1978-1983",
        "wording_note": 'Warren wrote "1978 to 1975", meaning 1978 to 1983.',
        "count": len(ITEMS),
        "items": ITEMS,
    }
    source_path = SOURCE_DIR / "palitoy-uk-releases.json"
    source_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    subprocess.check_call([sys.executable, str(ROOT / "tools" / "build-retrieval-index.py")])
    print(f"items {len(ITEMS)}")
    for path in written:
        print(f"{path.relative_to(ROOT)} {path.stat().st_size}")


if __name__ == "__main__":
    main()
