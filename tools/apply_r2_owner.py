#!/usr/bin/env python3
"""Apply Warren's 11 Oct 2026 R2-D2 solid-dome rulings.

The rulings live in data/references/owner-verified/r2-d2.md.
COO and factory-match builds call this after the Leia apply, so a regeneration
keeps the rulings. Running this file applies them to the data on disk.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "data" / "references" / "owner-verified" / "r2-d2.md"
COO = ROOT / "data" / "coo-figures.json"
STAMPS = ROOT / "data" / "coo-owner-stamps.json"
MATCH = ROOT / "data" / "factory-match.json"
PART1 = ROOT / "data" / "figures" / "r2-d2-reference-1.txt"
PART2 = ROOT / "data" / "figures" / "r2-d2-reference-2.txt"
VV = "https://www.variantvillain.com/characters/sw/r2-d2/"
CREDIT = "COO guide 3.7 © wdobafett / variantvillain.com"
NOTE = "Owner Warren, 11 Oct 2026. data/references/owner-verified/r2-d2.md."

REQUIRED = [
    "Date: 2026-10-11",
    "Source: owner Warren",
    "underside of the body",
    "around the base hole",
    "not on the legs",
    "one continuous line",
    "MADE IN HONG KONG",
    "MADE IN TAIWAN",
    "opposite side",
    "Lili Ledy Regreso",
    "shows 1978",
    "Kader M5",
    "Family 5 is Unitoy",
    "cavity 1 or 2",
    "cavity 5 or 6",
    "cavity 3 or 4",
    "line spacing",
    "red circle",
    "Poch",
    "PBP",
    "B-type sticker",
    "Takara wind-up",
    "Droid Factory",
    "not part of the core Kenner carded line",
    "no golden dome",
    "no dimple dome",
    "no No-COO solid-dome",
    "Never use Mint as a grade",
    "partial or cut-off country name counts as No COO",
    "COO guide 3.7",
    "wdobafett",
]

WHERE = (
    "Look on the underside of the body, around the base hole, not on the legs. "
    "A partial or cut-off country name counts as No COO. "
    "The picture is COO guide 3.7. Unitoy, Smile and the second Unitoy family share one continuous Hong Kong line, "
    "and the red marks show the line spacing."
)
EXPLANATION = (
    "The country of origin (COO) stamp on this R2-D2 is on the underside of the body, around the base hole, "
    "not on the legs. A partial or cut-off country name counts as No COO."
)
HK_LINE = "'© G.M.F.G.I. 1977 MADE IN HONG KONG' in one continuous line along the top of the underside"
TW_LINE = "'© G.M.F.G.I. 1977 MADE IN TAIWAN' in one continuous line along the top of the underside"
OPPOSITE = "'© G.M.F.G.I. 1977' at the top of the underside and 'HONG KONG' at the bottom, on the opposite side"
RETORNO = "No COO. The licensing line shows 1978. Cavity 5 or 6"
NON = "Not part of the core Kenner carded line."


def load_owner():
    if not OWNER.is_file():
        raise SystemExit(f"missing owner record {OWNER}")
    text = OWNER.read_text(encoding="utf-8")
    folded = text.casefold()
    missing = [phrase for phrase in REQUIRED if phrase.casefold() not in folded]
    if missing:
        raise SystemExit("owner record is missing rulings: " + "; ".join(missing))
    return text


def option(id, label, coo, factories, conclusion, sure, follow_ups=None):
    return {
        "id": id,
        "label": label,
        "coo": coo,
        "factories": factories,
        "examples": [label],
        "conclusion": conclusion,
        "sure": sure,
        "followUps": follow_ups or [],
    }


def follow(id, label, factories, conclusion):
    return {"id": id, "label": label, "factories": factories, "conclusion": conclusion, "sure": True}


def r2_options():
    return [
        option(
            "hong-kong-continuous",
            HK_LINE,
            "Hong Kong",
            ["Unitoy M1", "Smile M2", "Unitoy M5", "Poch"],
            "",
            False,
            [
                follow(
                    "smile-eye",
                    "Large crimson eye and a darker wedge",
                    ["Smile M2"],
                    "That is the Smile M2. Smile has a large crimson eye and a darker wedge. "
                    "The continuous Hong Kong line is shared with Unitoy, and the guide's red marks show the line spacing.",
                ),
                follow(
                    "unitoy-m1-sticker",
                    "Halftone two-part sticker, or a Unitoy dome from very dark blue to mid-blue",
                    ["Unitoy M1"],
                    "That is the Unitoy M1. Early figures have a 2-part halftone sticker. Later ones have a 1-part sticker and a mid-blue dome.",
                ),
                follow(
                    "unitoy-m5-dome",
                    "Loose dome with gaps underneath, on a 41-back, small red eye or a double-painted eye",
                    ["Unitoy M5"],
                    "That is the Unitoy M5. Family 5 is Unitoy, not Kader. The dome is loose, with gaps underneath.",
                ),
                follow(
                    "poch-dome",
                    "Bright blue dull-chrome dome, messy paint, burrs or a crooked sticker",
                    ["Poch"],
                    "That is the Poch. It is built from Unitoy or Kader parts, with a dull-chrome dome and messy paint.",
                ),
            ],
        ),
        option(
            "hong-kong-opposite",
            OPPOSITE,
            "Hong Kong",
            ["Kader M3", "Kader M4", "Kader M7", "Lili Ledy Regreso", "PBP"],
            "",
            False,
            [
                follow(
                    "kader-m3-cavity",
                    "Cavity 1 or 2, matt mid-blue legs",
                    ["Kader M3"],
                    "That is the Kader M3. Cavity 1 or 2. The number is not visible from the other side.",
                ),
                follow(
                    "kader-m4-cavity",
                    "Cavity 5 or 6, matt mid-blue legs, a short run",
                    ["Kader M4"],
                    "That is the Kader M4. Cavity 5 or 6. It is a short run, with a minor COO variation beside Kader M3 and Kader M7.",
                ),
                follow(
                    "kader-m7-cavity",
                    "Cavity 3 or 4, matt mid-blue legs",
                    ["Kader M7"],
                    "That is the Kader M7. Cavity 3 or 4. The paint matches Kader M3, and the two were made alongside each other.",
                ),
                follow(
                    "ll-regreso",
                    "Light-blue legs and an A-type or C-type Lili Ledy sticker",
                    ["Lili Ledy Regreso"],
                    "That is the Lili Ledy Regreso. It uses the Kader stamp, with light-blue legs. The torso can be hard or soft.",
                ),
                follow(
                    "pbp-sticker",
                    "B-type Lili Ledy sticker, greenish-grey panels, carded in Spain",
                    ["PBP"],
                    "That is the PBP. It is a Lili Ledy Regreso figure carded in Spain, with a B-type sticker.",
                ),
            ],
        ),
        option(
            "taiwan-continuous",
            TW_LINE,
            "Taiwan",
            ["Taiwan M6"],
            "That is the Taiwan M6. '© G.M.F.G.I. 1977 MADE IN TAIWAN' is one continuous line. "
            "The red circle and arrows on COO guide 3.7 mark that line.",
            True,
        ),
        option(
            "retorno-1978",
            RETORNO,
            "No COO",
            ["Lili Ledy Retorno"],
            "That is the Lili Ledy Retorno. No COO, and the licensing line shows 1978. Cavity 5 or 6. "
            "This is not the myth of a No-COO Kenner solid dome.",
            True,
        ),
        option(
            "takara-wind-up",
            "Not part of the core Kenner carded line: Takara wind-up",
            "Japan",
            ["Takara 1-1", "Takara 1-2", "Takara 2"],
            "",
            False,
            [
                follow(
                    "takara-1-1",
                    "JAPAN COO, no Takara stamp. Smaller dome rim, larger chrome buttons",
                    ["Takara 1-1"],
                    f"That is the Takara 1-1. {NON} JAPAN COO, no Takara stamp.",
                ),
                follow(
                    "takara-1-2",
                    "JAPAN COO with Takara on the back of the torso. Smaller dome rim, larger chrome buttons",
                    ["Takara 1-2"],
                    f"That is the Takara 1-2. {NON} JAPAN COO with Takara on the back of the torso.",
                ),
                follow(
                    "takara-2",
                    "No COO and no Takara stamp. Larger dome rim, smaller chrome buttons",
                    ["Takara 2"],
                    f"That is the Takara 2. {NON} No COO and no Takara stamp.",
                ),
            ],
        ),
        option(
            "droid-factory",
            "Not part of the core Kenner carded line: Droid Factory playset",
            "No COO",
            ["Droid Factory Kenner wavy", "Droid Factory Kenner straight", "Droid Factory Palitoy"],
            "",
            False,
            [
                follow(
                    "df-wavy",
                    "Kenner sticker, wavy top line, removable third leg",
                    ["Droid Factory Kenner wavy"],
                    f"That is the Droid Factory Kenner wavy sticker. {NON} Unique sculpt, removable third leg, reversed artwork.",
                ),
                follow(
                    "df-straight",
                    "Kenner sticker, straight top line, removable third leg",
                    ["Droid Factory Kenner straight"],
                    f"That is the Droid Factory Kenner straight sticker. {NON} Unique sculpt, removable third leg, reversed artwork.",
                ),
                follow(
                    "df-palitoy",
                    "Palitoy sticker, very wavy top line, removable third leg",
                    ["Droid Factory Palitoy"],
                    f"That is the Droid Factory Palitoy sticker. {NON} The top line is very wavy.",
                ),
            ],
        ),
    ]


def r2_stamps():
    return [
        f"Unitoy M1 = {HK_LINE}.",
        f"Smile M2 = {HK_LINE}. The red marks show the line spacing.",
        f"Unitoy M5 = {HK_LINE}. Family 5 is Unitoy.",
        "Poch = Unitoy or Kader parts, with the continuous Hong Kong line.",
        f"Kader M3 = {OPPOSITE}. Cavity 1 or 2.",
        f"Kader M4 = {OPPOSITE}. Cavity 5 or 6.",
        f"Kader M7 = {OPPOSITE}. Cavity 3 or 4.",
        "Lili Ledy Regreso = the same opposite Kader layout.",
        "PBP = a Lili Ledy Regreso figure with a B-type sticker, carded in Spain.",
        f"Taiwan M6 = {TW_LINE}.",
        "Lili Ledy Retorno = No COO. The licensing line shows 1978. Cavity 5 or 6.",
        "Takara wind-up and Droid Factory are not part of the core Kenner carded line.",
    ]


def reference_image():
    return {
        "url": "/images/r2-d2-coo-guide-3.7.png",
        "alt": "R2-D2 underside COO stamps by family",
        "title": "R2-D2 COO guide",
        "caption": CREDIT,
        "credit": CREDIT,
    }


def apply_coo_figures(figures):
    load_owner()
    record = next((fig for fig in figures if fig.get("name") == "R2-D2"), None)
    if not record:
        raise SystemExit("R2-D2 is not in coo-figures")
    record["whereToLook"] = WHERE
    record["cooExplanation"] = EXPLANATION
    record["ask"] = "Which stamp do you see?"
    record["source"] = "owner"
    record["sourceNote"] = NOTE
    record["verified"] = True
    record["hasDetails"] = True
    record["options"] = r2_options()
    record["ownerStamps"] = r2_stamps()
    record["stamps"] = r2_stamps()
    record["missing"] = ""
    record["tells"] = []
    record["referenceImage"] = reference_image()
    return figures


def sync_owner_stamps(r2):
    owner = json.loads(STAMPS.read_text(encoding="utf-8"))
    entry = {
        "name": "R2-D2",
        "recorded": "2026-10-11",
        "source": "owner",
        "whereToLook": r2["whereToLook"],
        "ask": r2["ask"],
        "stamps": r2["ownerStamps"],
        "options": r2["options"],
        "referenceImage": r2["referenceImage"],
        "missing": "",
    }
    figures = owner.get("figures") or []
    owner["figures"] = [fig for fig in figures if fig.get("name") != "R2-D2"] + [entry]
    owner["r2Note"] = "R2-D2 stamps follow data/references/owner-verified/r2-d2.md (owner Warren, 2026-10-11)."
    STAMPS.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def coo(detail):
    return {"category": "coo", "detail": detail, "where": "Look at the country stamp on the underside of the body."}


def plastic(detail):
    return {"category": "plastic", "detail": detail, "where": "Look at the plastic colour or shade."}


def paint(detail):
    return {"category": "paint", "detail": detail, "where": "Look at the paint colour."}


def accessory(detail):
    return {"category": "accessory", "detail": detail, "where": "Look at the sticker."}


def cavity(detail):
    return {"category": "cavity", "detail": detail, "where": "Look for a cavity mark or a mark by the screw."}


def mould(detail):
    return {"category": "mould", "detail": detail, "where": "Look at the mould: shape, proportions, tip or hilt."}


def card(detail):
    return {"category": "cardback", "detail": detail, "where": "If it is still carded, which card is it on?"}


def variant(id, factory, mould_name, tells, nonstandard=False):
    note = NOTE
    if nonstandard:
        note = f"{NOTE} {NON}"
    return {
        "id": id,
        "figure": "R2-D2",
        "factory": factory,
        "mould": mould_name,
        "source": "owner",
        "sourceUrl": VV,
        "sourceNote": note,
        "tells": tells,
    }


def r2_variants():
    spacing = (
        "One continuous line along the top of the underside: '© G.M.F.G.I. 1977 MADE IN HONG KONG'. "
        "The red marks on COO guide 3.7 show the line spacing. The words alone do not separate Unitoy from Smile."
    )
    opposite = (
        "'© G.M.F.G.I. 1977' at the top of the underside and 'HONG KONG' at the bottom, on the opposite side."
    )
    return [
        variant("r2-d2--unitoy-m1", "Unitoy M1", "M1", [
            coo(spacing),
            plastic("Very dark blue dome, 2-part halftone sticker, mid-blue legs. Early Bird era and 12-backs."),
            plastic("Dark blue dome with a 1-part sticker and no halftone."),
            plastic("Mid-blue dome and mid-blue legs on the ESB 41-back."),
            accessory("Small-wedge Sensorscope sticker on the transition figure, with darker legs."),
        ]),
        variant("r2-d2--smile-m2", "Smile M2", "M2", [
            coo(spacing),
            paint("Large crimson eye."),
            accessory("Darker wedge. The grey darkens over the run."),
            plastic("Dark blue dome and glossy darker legs, the early figure."),
            plastic("Electric mid-blue dome and lighter legs on 12-backs."),
            plastic("ESB legs return to a darker shade, and the wedge is almost gone."),
        ]),
        variant("r2-d2--unitoy-m5", "Unitoy M5", "M5", [
            coo(spacing + " Family 5 is Unitoy, not Kader."),
            mould("Loose dome with gaps around the underside. Poorly made, messy paint."),
            plastic("Mid-blue or light-blue dome and legs."),
            paint("Very small red eye, or a larger crimson eye with a double blue paint pass."),
            card("Seen on the 41-back."),
        ]),
        variant("r2-d2--poch", "Poch", "", [
            coo("Built from Unitoy or Kader parts. The Hong Kong line is the continuous Unitoy line on the underside."),
            plastic("Bright blue dull-chrome dome. Glossy mid-blue legs, sometimes with a misty spray."),
            paint("Crimson eye that can look purple where paint pooled. Messy paint, burrs, flashing, crooked stickers."),
            plastic("Late Jedi-era figure: very light-blue dull dome and a small red eye, on Meccano 65-back and French Trilogo."),
        ]),
        variant("r2-d2--kader-m3", "Kader M3", "M3", [
            coo(opposite),
            cavity("Cavity 1 or 2 near the screw. The number is not visible from the other side."),
            plastic("Dark blue dome, then a mid-blue dome. Matt mid-blue legs."),
            paint("Large crimson-red eye."),
            card("Made through the 32-back."),
        ]),
        variant("r2-d2--kader-m4", "Kader M4", "M4", [
            coo(opposite + " Minor COO variation beside Kader M3 and Kader M7."),
            cavity("Cavity 5 or 6."),
            plastic("Dark blue or mid-blue dome. Short run. Matt mid-blue legs."),
            mould("This 1977 torso mould was later used for R5-D4."),
        ]),
        variant("r2-d2--kader-m7", "Kader M7", "M7", [
            coo(opposite),
            cavity("Cavity 3 or 4."),
            plastic("Same paint as Kader M3: dark blue dome, then mid-blue, matt mid-blue legs. Made alongside Kader M3."),
        ]),
        variant("r2-d2--lili-ledy-regreso", "Lili Ledy Regreso", "M3", [
            coo(opposite + " Lili Ledy Regreso uses this Kader layout."),
            plastic("Light-blue legs throughout. Dome can be vibrant dark blue, dull purplish dark blue, or greenish light blue."),
            accessory("A-type or C-type Lili Ledy sticker."),
            mould("The torso can be hard or soft on both Lili Ledy COOs."),
        ]),
        variant("r2-d2--pbp", "PBP", "", [
            coo(opposite + " The figure is a Lili Ledy Regreso."),
            accessory("B-type sticker. Greenish-grey panels on glossier paper."),
            plastic("Mid-blue dome and light-blue legs."),
            card("Lili Ledy Regreso figure imported and carded in Spain."),
        ]),
        variant("r2-d2--lili-ledy-retorno", "Lili Ledy Retorno", "M4", [
            coo("No COO. The licensing line shows 1978. This is not a No-COO Kenner solid dome."),
            cavity("Cavity 5 or 6."),
            plastic("Dull dark blue dome, large crimson eye, glossy light-blue legs."),
            accessory("A-type or C-type Lili Ledy sticker."),
            mould("The torso can be hard or soft on both Lili Ledy COOs."),
        ]),
        variant("r2-d2--taiwan-m6", "Taiwan M6", "M6", [
            coo(
                "One continuous line along the top of the underside: '© G.M.F.G.I. 1977 MADE IN TAIWAN'. "
                "The red circle and arrows on COO guide 3.7 mark this line."
            ),
            plastic("Dark blue, mid-blue, or green-blue dome. Light-blue legs."),
            paint("Large orange-red eye."),
            accessory("Three-colour sticker with a halftone grid on the wedge."),
            card("12-back only."),
        ]),
        variant("r2-d2--takara-1-1", "Takara 1-1", "1-1", [
            coo("JAPAN COO. No Takara stamp."),
            mould(f"{NON} Smaller dome rim. Larger chrome buttons."),
            accessory("Clear sticker, with or without TM."),
        ], True),
        variant("r2-d2--takara-1-2", "Takara 1-2", "1-2", [
            coo("JAPAN COO, with Takara on the back of the torso."),
            mould(f"{NON} Smaller dome rim. Larger chrome buttons."),
            accessory("Clear sticker, with or without TM."),
        ], True),
        variant("r2-d2--takara-2", "Takara 2", "2", [
            coo("No COO and no Takara stamp."),
            mould(f"{NON} Larger dome rim. Smaller chrome buttons."),
            accessory("Clear sticker, with or without TM."),
        ], True),
        variant("r2-d2--droid-factory-kenner-wavy", "Droid Factory Kenner wavy", "", [
            mould(f"{NON} Unique sculpt with a removable third leg."),
            accessory("Kenner sticker drafted in reverse. Wavy top line on the central blue rectangle."),
        ], True),
        variant("r2-d2--droid-factory-kenner-straight", "Droid Factory Kenner straight", "", [
            mould(f"{NON} Unique sculpt with a removable third leg."),
            accessory("Kenner sticker drafted in reverse. Straight top line on the central blue rectangle."),
        ], True),
        variant("r2-d2--droid-factory-palitoy", "Droid Factory Palitoy", "", [
            mould(f"{NON} Unique sculpt with a removable third leg."),
            accessory("Palitoy sticker. The top line is very wavy."),
        ], True),
    ]


def apply_factory_match(payload):
    load_owner()
    fresh = r2_variants()
    out = []
    inserted = False
    for variant_row in payload.get("figureVariants") or []:
        if variant_row.get("figure") == "R2-D2":
            if not inserted:
                out.extend(fresh)
                inserted = True
            continue
        out.append(variant_row)
    if not inserted:
        out.extend(fresh)
    payload["figureVariants"] = out
    payload["r2Owner"] = "data/references/owner-verified/r2-d2.md"
    return payload


STAMP_BLOCK = """STAMP

The licensing line and the country stamp are on the underside of the body, around the base hole, not on the legs.

Unitoy M1, Smile M2 and Unitoy M5 share one continuous line, "© G.M.F.G.I. 1977 MADE IN HONG KONG". The red marks on COO guide 3.7 show the line spacing. Taiwan is one continuous line, "© G.M.F.G.I. 1977 MADE IN TAIWAN", marked with a red circle and arrows.

Kader M3, M4 and M7 have "© G.M.F.G.I. 1977" at the top and "HONG KONG" at the bottom, on the opposite side. Cavity 1 or 2 is M3, cavity 5 or 6 is M4, and cavity 3 or 4 is M7. Family 5 is Unitoy. A Kader M5 was mentioned, and that family stays Unitoy.

Lili Ledy Regreso uses the Kader layout. Lili Ledy Retorno is No COO and the licensing line shows 1978.

"""


def apply_guides():
    load_owner()
    part1 = PART1.read_text(encoding="utf-8")
    if "underside of the body" not in part1:
        part1 = part1.replace("\nFIGURE VARIANT FAMILIES\n", "\n" + STAMP_BLOCK + "FIGURE VARIANT FAMILIES\n", 1)
    old_unitoy = """Notes:
- Some late figures appear rushed or inconsistent
- M5 family appears briefly with unclear production reasoning
"""
    new_unitoy = """Notes:
- M1 is the early halftone sticker and the later 1-part sticker. Do not put the loose-dome tells on M1.
- M5 is a different Unitoy family. Loose dome, gaps underneath, 41-back, small red eye or a double-painted eye.
"""
    if old_unitoy in part1:
        part1 = part1.replace(old_unitoy, new_unitoy, 1)
    myth = "- “No COO solid dome R2 exists” → FALSE  \n  → These are body swaps from Sensorscope figures\n"
    myth_new = myth + "- A 1978 No COO figure is the Lili Ledy Retorno. That is a real figure, not this myth.\n"
    if "Lili Ledy Retorno. That is a real figure" not in part1 and myth in part1:
        part1 = part1.replace(myth, myth_new, 1)
    PART1.write_text(part1, encoding="utf-8")

    part2 = PART2.read_text(encoding="utf-8")
    if "Cavity 1 or 2 is Kader M3" not in part2:
        part2 = part2.replace(
            "- Large crimson eye\n",
            "- Large crimson eye\n- Cavity 1 or 2 is Kader M3. Cavity 5 or 6 is Kader M4. Cavity 3 or 4 is Kader M7.\n",
            1,
        )
    old_ll = """LILI LEDY (MEXICO)

Key Traits:
- Unique sticker artwork
- Light-blue legs consistent across variants

Variants:
- Dark blue dome
- Dull blue dome (purple hue)
- Light blue dome (greenish tone)
- Mid-blue dome (possible PBP-linked version)

Sticker Types:
- Type A (blank rectangles)
- Type B (green-grey panels)
- Type C (light-grey panels)

Important:
- Porous sticker material → poor durability
- Some versions imported into Spain (PBP)
"""
    new_ll = """LILI LEDY REGRESO

Key Traits:
- Same opposite Hong Kong stamp as Kader
- Light-blue legs
- A-type or C-type sticker
- The torso can be hard or soft

PBP

- A Regreso figure carded in Spain
- B-type sticker, greenish-grey panels, glossier paper
- This note does not belong on the Retorno

LILI LEDY RETORNO

- No COO. The licensing line shows 1978
- Cavity 5 or 6
- Dull dark blue dome, glossy light-blue legs
- A-type or C-type sticker
"""
    if old_ll in part2:
        part2 = part2.replace(old_ll, new_ll, 1)
    if "not part of the core Kenner carded line" not in part2:
        part2 = part2.replace(
            "DROID FACTORY PLAYSET\n\nKey Traits:\n",
            "DROID FACTORY PLAYSET\n\nNot part of the core Kenner carded line.\n\nKey Traits:\n",
            1,
        )
        part2 = part2.replace(
            "TAKARA WIND-UP R2 (JAPAN)\n\nKey Traits:\n",
            "TAKARA WIND-UP R2 (JAPAN)\n\nNot part of the core Kenner carded line.\n\nKey Traits:\n",
            1,
        )
    PART2.write_text(part2, encoding="utf-8")


def main():
    load_owner()
    coo = json.loads(COO.read_text(encoding="utf-8"))
    apply_coo_figures(coo["figures"])
    COO.write_text(json.dumps(coo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    r2 = next(fig for fig in coo["figures"] if fig["name"] == "R2-D2")
    sync_owner_stamps(r2)
    match = json.loads(MATCH.read_text(encoding="utf-8"))
    apply_factory_match(match)
    MATCH.write_text(json.dumps(match, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    apply_guides()
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_factory_match", ROOT / "tools" / "build-factory-match.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_report(match)
    print("r2 owner applied")


if __name__ == "__main__":
    main()
