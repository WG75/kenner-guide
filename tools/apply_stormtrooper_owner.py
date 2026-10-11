#!/usr/bin/env python3
"""Apply Warren's 11 Oct 2026 Imperial Stormtrooper rulings.

The rulings live in data/references/owner-verified/stormtrooper.md.
COO and factory-match builds call this after the Darth Vader apply.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "data" / "references" / "owner-verified" / "stormtrooper.md"
COO = ROOT / "data" / "coo-figures.json"
STAMPS = ROOT / "data" / "coo-owner-stamps.json"
MATCH = ROOT / "data" / "factory-match.json"
FIGURE = ROOT / "data" / "figures" / "stormtrooper-reference.txt"

REQUIRED = [
    "Date: 2026-10-11",
    "Source: owner Warren",
    "back of the left thigh",
    "three side-by-side columns",
    "two side-by-side columns",
    "H of HONG starts under the ©",
    "Kader M8",
    "family VII",
    "CHINA",
    "raised bar",
    "no 'MADE IN'",
    "JAPAN",
    "1978",
    "hard torso",
    "very wide mouth",
    "thin or small mouth",
    "extra mouthpiece flaps",
    "Poch M2",
    "HONG KONG COO",
    "soft torso",
    "cross-slot screw",
    "no markings at all",
    "no peg holes",
    "dimple on the chest knob",
    "helmet back A or B",
    "Poon is a reproduction",
    "Boba Fett only",
    "Survival Kit only",
    "Never use Mint as a grade",
    "Imperial Blaster",
]

NOTE = "Owner Warren, 11 Oct 2026. data/references/owner-verified/stormtrooper.md."
WHERE = (
    "Look on the back of the left thigh. The stamp runs vertically in side-by-side columns. "
    "A partial or cut-off country name counts as No COO. The picture is COO guide 3.1."
)
EXPLANATION = (
    "The country of origin (COO) stamp on this Stormtrooper is on the back of the left thigh. "
    "It runs vertically in side-by-side columns. "
    "A partial or cut-off country name counts as No COO."
)
THIGH = "The stamp is on the back of the left thigh."
THREE = (
    "Three side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I.', 'HONG KONG' and '1977'"
)
CHINA = (
    "Three side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I.', 'CHINA' on a raised bar, and '1977'"
)
TWO = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I. 1977' and 'HONG KONG'"
)
SMILE_NC = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I.' and '1977', with no country"
)
LINE = (
    "Only the licensing line on the back of the left thigh: "
    "'© G.M.F.G.I. 1977', with no country"
)
JAPAN = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I. 1978' and 'JAPAN'"
)
BARE = (
    "No markings at all on the back of the left thigh: "
    "no copyright line and no country, and no peg holes"
)
H_UNDER = "The H of HONG starts under the ©"
KADER_I = f"{H_UNDER}, and it matches family I on the guide, with no extra mouthpiece flaps"
KADER_VII = f"{H_UNDER}, and it matches family VII on the guide"
POCH_FLAPS = "Extra mouthpiece flaps"
SMILE_IV = "It matches family IV on the guide"
UNITOY_II = "It matches family II on the guide, with no extra mouthpiece flaps"
POCH_II = "It matches family II on the guide, with extra mouthpiece flaps"
UNITOY_III = "It matches family III on the guide"
LL = "A hard torso and a very wide mouth"
PBP = "A thin or small mouth"


def load_owner():
    if not OWNER.is_file():
        raise SystemExit(f"missing owner record {OWNER}")
    text = OWNER.read_text(encoding="utf-8")
    folded = text.casefold()
    missing = [phrase for phrase in REQUIRED if phrase.casefold() not in folded]
    if missing:
        raise SystemExit("owner record is missing rulings: " + "; ".join(missing))
    return text


def follow(fid, label, factories, conclusion):
    return {"id": fid, "label": label, "factories": factories, "conclusion": conclusion, "sure": True}


def option(fid, label, coo, factories, conclusion, sure, follow_ups=None):
    return {
        "id": fid,
        "label": label,
        "coo": coo,
        "factories": factories,
        "examples": [label],
        "conclusion": conclusion,
        "sure": sure,
        "followUps": follow_ups or [],
    }


def trooper_options():
    return [
        option(
            "hong-kong-3",
            THREE,
            "Hong Kong",
            ["Kader M1", "Kader M7", "Poch M1", "Smile M4"],
            "",
            False,
            [
                follow(
                    "kader-m1",
                    KADER_I,
                    ["Kader M1"],
                    f"That is the Kader M1, family I. {THIGH} {H_UNDER}. "
                    "A dimple on the chest knob tells the two torso moulds apart. Compare family I on COO guide 3.1.",
                ),
                follow(
                    "kader-m7",
                    KADER_VII,
                    ["Kader M7"],
                    f"That is the Kader M7, family VII. {THIGH} {H_UNDER}. "
                    "Warren's Kader M8 is this Kader M7. "
                    "Figure family VII is not Imperial Blaster M7. Compare family VII on COO guide 3.1.",
                ),
                follow(
                    "poch-m1",
                    POCH_FLAPS,
                    ["Poch M1"],
                    "That is the Poch M1. It uses the family I three-column HONG KONG stamp, with extra mouthpiece flaps.",
                ),
                follow(
                    "smile-m4",
                    SMILE_IV,
                    ["Smile M4"],
                    "That is the Smile M4 with the COO. Three side-by-side columns, family IV on COO guide 3.1. "
                    "Helmet back A or B tells the torso moulds apart.",
                ),
            ],
        ),
        option(
            "kader-china",
            CHINA,
            "China",
            ["Kader China"],
            "That is Kader China. 'CHINA' is on a raised bar. There is no 'MADE IN'.",
            True,
        ),
        option(
            "hong-kong-2",
            TWO,
            "Hong Kong",
            ["Unitoy II", "Poch M2", "Unitoy III"],
            "",
            False,
            [
                follow(
                    "unitoy-ii",
                    UNITOY_II,
                    ["Unitoy II"],
                    "That is the Unitoy on family II. Two side-by-side columns. "
                    "Imperial Blaster M1 and M2 are a different series.",
                ),
                follow(
                    "poch-m2",
                    POCH_II,
                    ["Poch M2"],
                    "That is the Poch M2. It has a HONG KONG COO, so Poch is not only No COO. Extra mouthpiece flaps.",
                ),
                follow(
                    "unitoy-iii",
                    UNITOY_III,
                    ["Unitoy III"],
                    "That is the Unitoy on family III. Two side-by-side columns of HONG KONG. Compare family III on COO guide 3.1.",
                ),
            ],
        ),
        option(
            "smile-no-coo",
            SMILE_NC,
            "No COO",
            ["Smile M4 No COO"],
            "That is the Smile M4 without the COO. Two side-by-side columns, '© G.M.F.G.I.' and '1977', with no country. "
            "A soft torso is Smile. A hard torso on this stamp, without the very wide mouth, is not assigned.",
            True,
        ),
        option(
            "licensing-line",
            LINE,
            "No COO",
            ["Lili Ledy", "PBP", "Poch No COO"],
            "",
            False,
            [
                follow(
                    "lili-ledy",
                    LL,
                    ["Lili Ledy"],
                    "That is the Lili Ledy. A hard torso and a very wide mouth. The licensing line is the only marking.",
                ),
                follow(
                    "pbp",
                    PBP,
                    ["PBP"],
                    "That is the PBP. A thin or small mouth. The licensing line is the only marking.",
                ),
                follow(
                    "poch-no-coo",
                    POCH_FLAPS,
                    ["Poch No COO"],
                    "That is the Poch with no country. Extra mouthpiece flaps. Family III limbs. Poch M2 is the one with a HONG KONG COO.",
                ),
            ],
        ),
        option(
            "takara",
            JAPAN,
            "Japan",
            ["Takara"],
            "That is the Takara. '© G.M.F.G.I. 1978' and 'JAPAN', with no 'MADE IN' and no raised bar. "
            "A cross-slot screw is in the back. Warren confirmed '© G.M.F.G.I. 1978' and 'JAPAN'.",
            True,
        ),
        option(
            "top-toys",
            BARE,
            "",
            ["Top Toys"],
            "That is the Top Toys. There are no markings at all, and no peg holes.",
            True,
        ),
    ]


def trooper_stamps():
    return [
        f"Kader M1 = {THREE}. {H_UNDER}. Family I on the guide.",
        f"Kader M7 = {THREE}. {H_UNDER}. Family VII on the guide. Warren's Kader M8 is this Kader M7.",
        "Poch M1 = the family I three-column HONG KONG stamp, with extra mouthpiece flaps.",
        "Kader China = 'CHINA' on a raised bar. No 'MADE IN'. Not 'Made in China'.",
        f"Unitoy family II = {TWO}.",
        "Poch M2 = the family II two-column HONG KONG stamp, with extra mouthpiece flaps. Poch M2 has a HONG KONG COO.",
        f"Unitoy family III = {TWO}.",
        "Smile M4 with the COO = three side-by-side columns. Family IV. Helmet back A or B.",
        f"Smile M4 without the COO = {SMILE_NC}. A soft torso is Smile.",
        "Lili Ledy = the licensing line only. A hard torso and a very wide mouth.",
        "PBP = the licensing line only. A thin or small mouth.",
        "Poch No COO = the licensing line only, with extra mouthpiece flaps.",
        f"Takara = {JAPAN}. No 'MADE IN' and no raised bar. A cross-slot screw is in the back.",
        "Top Toys = no markings at all, and no peg holes.",
    ]


def apply_coo_figures(figures):
    load_owner()
    record = next((fig for fig in figures if fig.get("name") == "Stormtrooper"), None)
    if not record:
        raise SystemExit("Stormtrooper is not in coo-figures")
    record["whereToLook"] = WHERE
    record["cooExplanation"] = EXPLANATION
    record["ask"] = "Which stamp do you see?"
    record["source"] = "owner"
    record["sourceNote"] = NOTE
    record["verified"] = True
    record["hasDetails"] = True
    record["options"] = trooper_options()
    record["ownerStamps"] = trooper_stamps()
    record["stamps"] = trooper_stamps()
    record["missing"] = ""
    record["tells"] = []
    record["guide"] = [
        "I: Kader/ Poch/ Kader China",
        "II: Unitoy/ Poch",
        "III: Unitoy/ Poch/ PBP/ Lili Ledy",
        "IV: Smile",
        "V: Takara",
        "VI: Top Toys",
        "VII: Kader",
    ]
    record["referenceImage"] = {"id": "stormtrooper-coo-guide-3.1"}
    return figures


def sync_owner_stamps(record):
    owner = json.loads(STAMPS.read_text(encoding="utf-8"))
    entry = {
        "name": "Stormtrooper",
        "recorded": "2026-10-11",
        "source": "owner",
        "whereToLook": record["whereToLook"],
        "ask": record["ask"],
        "stamps": record["ownerStamps"],
        "options": record["options"],
        "referenceImage": record["referenceImage"],
        "missing": "",
    }
    figures = owner.get("figures") or []
    owner["figures"] = [fig for fig in figures if fig.get("name") != "Stormtrooper"] + [entry]
    owner["stormtrooperNote"] = (
        "Stormtrooper stamps follow data/references/owner-verified/stormtrooper.md (owner Warren, 2026-10-11)."
    )
    STAMPS.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def coo(detail):
    return {"category": "coo", "detail": detail, "where": "Look at the country stamp on the back of the left thigh."}


def paint(detail):
    return {"category": "paint", "detail": detail, "where": "Look at the paint on the helmet."}


def mould(detail):
    return {"category": "mould", "detail": detail, "where": "Look at the mould: shape, proportions, tip or hilt."}


def assembly(detail):
    return {"category": "assembly", "detail": detail, "where": "Look at how the figure is put together."}


def variant(vid, factory, mould_name, tells):
    return {
        "id": vid,
        "figure": "Stormtrooper",
        "factory": factory,
        "mould": mould_name,
        "source": "owner",
        "sourceUrl": "https://www.variantvillain.com/characters/sw/stormtrooper/",
        "sourceNote": NOTE,
        "tells": tells,
    }


DIMPLE = "A dimple on the chest knob tells the two torso moulds apart."
ROCKET = "Rocket mouth."
FLAPS = "Extra mouthpiece flaps."
HARD = "Hard ABS torso."
HELMET = "Helmet back A or B tells the two torso moulds apart."


def trooper_variants():
    return [
        variant("stormtrooper--kader-m1", "Kader M1", "M1", [
            coo(f"{THIGH} {THREE}. {H_UNDER}. Family I on COO guide 3.1."),
            mould(DIMPLE),
            paint(ROCKET),
        ]),
        variant("stormtrooper--kader-m7", "Kader M7", "M7", [
            coo(f"{THIGH} {THREE}. {H_UNDER}. Family VII on COO guide 3.1. "
                "Warren's Kader M8 is this Kader M7."),
        ]),
        variant("stormtrooper--poch-m1", "Poch M1", "M1", [
            coo(f"{THIGH} {THREE}. Family I, the same stamp as Kader M1."),
            mould(DIMPLE),
            paint(FLAPS),
        ]),
        variant("stormtrooper--kader-china", "Kader China", "M1", [
            coo(f"{THIGH} {CHINA}. There is no 'MADE IN'."),
            mould(DIMPLE),
            paint(ROCKET),
        ]),
        variant("stormtrooper--unitoy-ii", "Unitoy II", "II", [
            coo(f"{THIGH} {TWO}. Family II on COO guide 3.1."),
            paint("Line mouth, slim or wide."),
        ]),
        variant("stormtrooper--poch-m2", "Poch M2", "M2", [
            coo(f"{THIGH} {TWO}. Family II. Poch M2 has a HONG KONG COO."),
            paint(FLAPS),
        ]),
        variant("stormtrooper--unitoy-iii", "Unitoy III", "III", [
            coo(f"{THIGH} {TWO}. Family III on COO guide 3.1."),
            paint("Mouth slim or wide."),
        ]),
        variant("stormtrooper--smile-m4", "Smile M4", "M4", [
            coo(f"{THIGH} {THREE}. Family IV on COO guide 3.1."),
            mould(HELMET),
            paint("Rocket mouth or a standard mouth."),
        ]),
        variant("stormtrooper--smile-m4-no-coo", "Smile M4 No COO", "M4", [
            coo(f"{THIGH} {SMILE_NC}. A soft torso is Smile."),
            mould("Soft torso. A hard torso on this stamp, without the very wide mouth, is not assigned."),
            mould(HELMET),
        ]),
        variant("stormtrooper--lili-ledy", "Lili Ledy", "", [
            coo(f"{THIGH} {LINE}. Family III."),
            mould(HARD),
            paint("Very wide mouth."),
        ]),
        variant("stormtrooper--pbp", "PBP", "", [
            coo(f"{THIGH} {LINE}. Family III."),
            mould(HARD),
            paint("Thin or small mouth."),
        ]),
        variant("stormtrooper--poch-no-coo", "Poch No COO", "", [
            coo(f"{THIGH} {LINE}. Family III. This is not Poch M2."),
            mould(HARD),
            paint(FLAPS),
        ]),
        variant("stormtrooper--takara", "Takara", "", [
            coo(f"{THIGH} {JAPAN}. No 'MADE IN' and no raised bar. Warren confirmed 1978."),
            assembly("A cross-slot screw is in the back."),
        ]),
        variant("stormtrooper--top-toys", "Top Toys", "", [
            coo(f"{THIGH} {BARE}."),
            mould("No peg holes."),
        ]),
    ]


BLASTER_LINKS = {
    "imperial-blaster--unitoy-m1": ["stormtrooper--unitoy-ii", "stormtrooper--unitoy-iii"],
    "imperial-blaster--unitoy-m2": ["stormtrooper--unitoy-ii", "stormtrooper--unitoy-iii"],
    "imperial-blaster--kader-m3": ["stormtrooper--kader-m1"],
    "imperial-blaster--kader-m4": ["stormtrooper--kader-m1", "stormtrooper--kader-m7"],
    "imperial-blaster--smile-m5": [
        "stormtrooper--smile-m4",
        "stormtrooper--smile-m4-no-coo",
        "stormtrooper--pbp",
    ],
    "imperial-blaster--taiwan-m6": [],
    "imperial-blaster--kader-m7": ["stormtrooper--kader-china"],
    "imperial-blaster--lili-ledy-m7": ["stormtrooper--lili-ledy"],
    "imperial-blaster--kader-m8": [],
    "imperial-blaster--takara-m9": ["stormtrooper--takara"],
    "imperial-blaster--top-toys-m10": ["stormtrooper--top-toys"],
}

BLASTER_NOTES = {
    "imperial-blaster--taiwan-m6": "Boba Fett with a Taiwan COO only. Not the Imperial Stormtrooper.",
    "imperial-blaster--kader-m8": "Survival Kit only. Not carded with the Imperial Stormtrooper.",
}


def apply_blaster_links(payload):
    for row in payload.get("accessoryVariants") or []:
        current = list(row.get("cardedWith") or [])
        extra = BLASTER_LINKS.get(row.get("id"))
        if extra is None:
            continue
        others = [item for item in current if not str(item).startswith("stormtrooper--")]
        row["cardedWith"] = others + list(extra)
        note = BLASTER_NOTES.get(row.get("id"))
        if note and not any(item.get("detail") == note for item in row.get("tells") or []):
            row.setdefault("tells", []).append({
                "category": "mould",
                "detail": note,
                "where": "This mould is not an Imperial Stormtrooper blaster.",
            })


def apply_factory_match(payload):
    load_owner()
    fresh = trooper_variants()
    out = []
    inserted = False
    for row in payload.get("figureVariants") or []:
        if row.get("figure") == "Stormtrooper":
            if not inserted:
                out.extend(fresh)
                inserted = True
            continue
        out.append(row)
    if not inserted:
        out.extend(fresh)
    payload["figureVariants"] = out
    apply_blaster_links(payload)
    payload["stormtrooperOwner"] = "data/references/owner-verified/stormtrooper.md"
    return payload


FAMILIES = """FIGURE VARIANT FAMILIES

- Family I: Kader M1, Poch M1 and Kader China. Rocket mouth. A dimple on the chest knob tells the two torso moulds apart. Poch M1 has extra mouthpiece flaps.
- Family II: Unitoy, and Poch M2. Poch M2 has a HONG KONG COO. Line mouth. Extra mouthpiece flaps mark Poch.
- Family III with HONG KONG is Unitoy. With no country, a hard torso and a very wide mouth is Lili Ledy, a thin or small mouth is PBP, and extra mouthpiece flaps is Poch.
- Family IV: Smile. With the COO it is three side-by-side columns. Without the COO it is two columns and a soft torso. Helmet back A or B tells the torso moulds apart.
- Family V: Takara. Just 'JAPAN', no 'MADE IN', and a cross-slot screw. Warren confirmed '© G.M.F.G.I. 1978' with 'JAPAN'.
- Family VI: Top Toys. No markings at all, and no peg holes.
- Family VII: Kader M7. Three side-by-side columns. The H of HONG starts under the ©. Warren's Kader M8 is this Kader M7.

--------------------------------------------------

GENERAL PRODUCTION NOTES

- Stormtrooper is one of the highest volume figures produced
- Heavy variation exists across:
  - plastic tone (bright white → cream)
  - helmet sculpt
  - torso material
  - COO markings

Important:
- COO alone is not sufficient for identification
- Must combine:
  - torso type
  - helmet details
  - plastic colour
  - mould features

--------------------------------------------------

"""

STAMP_BLOCK = """STAMP

The stamp is on the back of the left thigh. Three side-by-side columns: Kader M1, Kader M7, Poch M1, Kader China and Smile with the COO. On Kader M1 and Kader M7, the H of HONG starts under the ©. Kader China is 'CHINA' on a raised bar, not 'Made in China'. Unitoy is two side-by-side columns. Smile without the COO is two columns and no country. Top Toys has no markings at all.

"""

EXTRA = """BLASTERS

Imperial Blaster moulds are a different series from the figure families. Kader uses M3 then M4. Kader China uses M7. Unitoy uses M1 then M2. Smile uses M5. PBP uses M5. Lili Ledy uses M7. Takara uses M9. Top Toys uses M10. Taiwan M6 is Boba Fett only. Kader M8 is the Survival Kit only.

POON REPRODUCTION

Poon is a reproduction, not a COO family. It is very white. The feet do not point together, and the right leg sits slightly out. A larger flat area sits on top of the torso where the arm meets. The stamp is two side-by-side columns, like family II. The Poon blaster is hard and sinks.

"""


def apply_guides():
    load_owner()
    raw = FIGURE.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")
    start = text.find("FIGURE VARIANT FAMILIES\n")
    end = text.find("COLOUR VARIATION\n")
    if start != -1 and end != -1 and "Kader / Poch / Nina" in text[start:end]:
        text = text[:start] + FAMILIES + text[end:]
    if "back of the left thigh" not in text:
        text = text.replace("\nFIGURE VARIANT FAMILIES\n", "\n" + STAMP_BLOCK + "FIGURE VARIANT FAMILIES\n", 1)
    text = text.replace(
        "Warren's Kader M8 is not a third variant on this sheet.",
        "Warren's Kader M8 is this Kader M7.",
    )
    text = text.replace(
        "COO guide 3.1 shows 1978.",
        "Warren confirmed '© G.M.F.G.I. 1978' with 'JAPAN'.",
    )
    if "Poon is a reproduction" not in text:
        text = text.replace("\nSources:\n", "\n" + EXTRA + "Sources:\n", 1)
    FIGURE.write_bytes(text.replace("\n", newline).encode("utf-8"))


def main():
    load_owner()
    coo = json.loads(COO.read_text(encoding="utf-8"))
    apply_coo_figures(coo["figures"])
    COO.write_text(json.dumps(coo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    record = next(fig for fig in coo["figures"] if fig["name"] == "Stormtrooper")
    sync_owner_stamps(record)
    match = json.loads(MATCH.read_text(encoding="utf-8"))
    apply_factory_match(match)
    MATCH.write_text(json.dumps(match, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    apply_guides()
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_factory_match", ROOT / "tools" / "build-factory-match.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_report(match)
    print("stormtrooper owner applied")


if __name__ == "__main__":
    main()
