#!/usr/bin/env python3
"""Apply Warren's 11 Oct 2026 Darth Vader rulings.

The rulings live in data/references/owner-verified/darth-vader.md.
COO and factory-match builds call this after the C-3PO apply.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "data" / "references" / "owner-verified" / "darth-vader.md"
COO = ROOT / "data" / "coo-figures.json"
STAMPS = ROOT / "data" / "coo-owner-stamps.json"
MATCH = ROOT / "data" / "factory-match.json"
FIGURE = ROOT / "data" / "figures" / "darth-vader-reference.txt"

REQUIRED = [
    "Date: 2026-10-11",
    "Source: owner Warren",
    "back of the left thigh",
    "two side-by-side columns",
    "H of HONG starts under the ©",
    "blank raised bar",
    "Kader China",
    "not Kader M1",
    "family III No COO",
    "Smile Vader is always HONG KONG",
    "remnants of HONG KONG",
    "partly visible country counts as No COO",
    "two dots on each foot sole",
    "one in the middle of the sole",
    "one on the toes",
    "Unitoy M7 has none",
    "no markings at all",
    "belt-buckle circle is not painted",
    "cross-slot screw",
    "gate scar",
    "cape M17",
    "Never use Mint as a grade",
    "Kader China is not named on the sabre guide",
    "Lili Ledy Ben",
    "Telescoping Lightsaber",
]

NOTE = "Owner Warren, 11 Oct 2026. data/references/owner-verified/darth-vader.md."
WHERE = (
    "Look on the back of the left thigh. The stamp runs vertically in two side-by-side columns. "
    "A partial or cut-off country name counts as No COO. The picture is COO guide 3.2."
)
EXPLANATION = (
    "The country of origin (COO) stamp on this Darth Vader is on the back of the left thigh. "
    "It runs vertically in two side-by-side columns. "
    "A partial or cut-off country name counts as No COO."
)
THIGH = "The stamp is on the back of the left thigh."
HK = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I. 1977' and 'HONG KONG'"
)
MADE_HK = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I. 1977' and 'MADE IN HONG KONG'"
)
MADE_TW = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I. 1977' and 'MADE IN TAIWAN'"
)
TW = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I. 1977' and 'TAIWAN'"
)
JAPAN = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I. 1978' and 'JAPAN'"
)
BAR = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I. 1977' and a blank raised bar"
)
LINE = (
    "Only the licensing line on the back of the left thigh: "
    "'© G.M.F.G.I. 1977', with no country and no raised bar"
)
REMNANTS = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I. 1977' and clear remnants of 'HONG KONG'. "
    "A partly visible country counts as No COO"
)
SCAR = (
    "The country is scarred out on the back of the left thigh, "
    "beside '© G.M.F.G.I. 1977'"
)
BARE = "No markings at all on the back of the left thigh: no copyright line and no country"
H_UNDER = "The H of HONG starts under the ©"
KADER_I = f"{H_UNDER}, and it matches family I on the guide"
KADER_II = f"{H_UNDER}, and it matches family II on the guide, with no gate scar"
POCH = f"{H_UNDER}, and it matches family II on the guide, with a big leftover gate scar by the stamp"
KADER_III = f"{H_UNDER}, and it matches family III on the guide"
SMILE = "It matches family IV on the guide, and the country reads 'HONG KONG'"
M6 = "Two dots on each foot sole, one in the middle of the sole and one on the toes"
M7 = "No dots on the foot soles, and it matches family VII on the guide"
M8 = "It matches family VIII on the guide"
KADER_NC = "It matches family III on the guide"
GLASS = "The belt-buckle circle is not painted white"
LL_NC = "It matches family IV on the guide, with no country and no remnants"


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


def vader_options():
    return [
        option(
            "hong-kong",
            HK,
            "Hong Kong",
            ["Kader M1", "Kader M2", "Poch", "Kader M3", "Smile M4", "Unitoy M6", "Unitoy M7", "Unitoy M8"],
            "",
            False,
            [
                follow("kader-m1", KADER_I, ["Kader M1"],
                       f"That is the Kader M1, family I. {THIGH} {H_UNDER}. Compare family I on COO guide 3.2."),
                follow("kader-m2", KADER_II, ["Kader M2"],
                       f"That is the Kader M2, family II. {THIGH} {H_UNDER}. There is no gate scar."),
                follow("poch", POCH, ["Poch"],
                       f"That is the Poch on family II. {THIGH} {H_UNDER}. "
                       "A big leftover gate scar sits by the stamp. The cape is M17."),
                follow("kader-m3", KADER_III, ["Kader M3"],
                       f"That is the Kader M3, family III. {THIGH} {H_UNDER}. Compare family III on COO guide 3.2."),
                follow("smile-m4", SMILE, ["Smile M4"],
                       "That is the Smile M4. Smile Vader is always HONG KONG. Match it to family IV on COO guide 3.2."),
                follow("unitoy-m6", M6, ["Unitoy M6"],
                       "That is the Unitoy M6. The stamp text matches Unitoy M7. "
                       "Each foot sole has two dots, one in the middle of the sole and one on the toes."),
                follow("unitoy-m7", M7, ["Unitoy M7"],
                       "That is the Unitoy M7. The stamp text matches Unitoy M6. The foot soles have no dots."),
                follow("unitoy-m8", M8, ["Unitoy M8"],
                       "That is the Unitoy M8. The stamp is on the back of the left thigh. "
                       "Match it to family VIII on COO guide 3.2."),
            ],
        ),
        option("made-in-hong-kong", MADE_HK, "Hong Kong", ["Unitoy M5"],
               f"That is the Unitoy M5. {MADE_HK}.", True),
        option("made-in-taiwan", MADE_TW, "Taiwan", ["Taiwan M10"],
               f"That is the Taiwan M10, family X. {MADE_TW}.", True),
        option("taiwan", TW, "Taiwan", ["Taiwan M11"],
               f"That is the Taiwan M11, family XI. {TW}.", True),
        option("takara-1978", JAPAN, "Japan", ["Takara M12"],
               f"That is the Takara M12. {JAPAN}. A cross-slot screw is in the back.", True),
        option("kader-china-bar", BAR, "No COO", ["Kader China"],
               "That is Kader China, not Kader M1. "
               "The licensing line sits beside a blank raised bar, where HONG KONG was.", True),
        option(
            "licensing-line",
            LINE,
            "No COO",
            ["Kader M3 No COO", "Glasslite M3", "Lili Ledy M4 No COO"],
            "",
            False,
            [
                follow("kader-m3-no-coo", KADER_NC, ["Kader M3 No COO"],
                       "That is the Kader family III No COO. The licensing line is the only marking. "
                       "It is not the blank raised bar, and it is not Kader M1."),
                follow("glasslite", GLASS, ["Glasslite M3"],
                       "That is the Glasslite. The licensing line is there and the country is not. "
                       "The belt-buckle circle is not painted white."),
                follow("ll-no-coo", LL_NC, ["Lili Ledy M4 No COO"],
                       "That is the Lili Ledy family IV version with no country. "
                       "VV calls this the Regreso version."),
            ],
        ),
        option("ll-remnants", REMNANTS, "No COO", ["Lili Ledy M4"],
               "That is the Lili Ledy family IV version with clear remnants of HONG KONG. "
               "A partly visible country counts as No COO. VV calls this the Retorno version.", True),
        option("pbp-scar", SCAR, "No COO", ["PBP M8"],
               "That is the PBP on family VIII. The country is scarred out beside the licensing line.", True),
        option("top-toys-bare", BARE, "", ["Top Toys M9"],
               "That is the Top Toys. There are no markings at all: no copyright line and no country.", True),
    ]


def vader_stamps():
    return [
        f"Kader M1 = {HK}. {H_UNDER}. Family I on the guide.",
        f"Kader M2 = {HK}. {H_UNDER}. Family II on the guide. No gate scar.",
        f"Poch = {HK}. Family II, with a big leftover gate scar by the stamp, and cape M17.",
        f"Kader M3 = {HK}. {H_UNDER}. Family III on the guide.",
        "Kader China = a blank raised bar beside the licensing line. Not Kader M1.",
        "Kader family III No COO = the licensing line only. Not the blank raised bar.",
        "Glasslite = the licensing line only. The belt-buckle circle is not painted white.",
        "Smile M4 = HONG KONG. Smile Vader is always HONG KONG. Family IV on the guide.",
        "Lili Ledy family IV, remnants = clear remnants of HONG KONG. A partly visible country counts as No COO.",
        "Lili Ledy family IV, No COO = no country.",
        f"Unitoy M5 = {MADE_HK}.",
        f"Unitoy M6 = {HK}. Two dots on each foot sole, one in the middle of the sole and one on the toes.",
        f"Unitoy M7 = {HK}. No dots on the foot soles.",
        f"Unitoy M8 = {HK}. Family VIII on the guide.",
        "PBP = the country is scarred out on family VIII.",
        "Top Toys = no markings at all. No copyright line and no country.",
        f"Taiwan M10 = {MADE_TW}.",
        f"Taiwan M11 = {TW}.",
        f"Takara M12 = {JAPAN}. A cross-slot screw is in the back.",
    ]


def apply_coo_figures(figures):
    load_owner()
    record = next((fig for fig in figures if fig.get("name") == "Darth Vader"), None)
    if not record:
        raise SystemExit("Darth Vader is not in coo-figures")
    record["whereToLook"] = WHERE
    record["cooExplanation"] = EXPLANATION
    record["ask"] = "Which stamp do you see?"
    record["source"] = "owner"
    record["sourceNote"] = NOTE
    record["verified"] = True
    record["hasDetails"] = True
    record["options"] = vader_options()
    record["ownerStamps"] = vader_stamps()
    record["stamps"] = vader_stamps()
    record["missing"] = ""
    record["tells"] = []
    record["referenceImage"] = {"id": "darth-vader-coo-guide-3.2"}
    return figures


def sync_owner_stamps(record):
    owner = json.loads(STAMPS.read_text(encoding="utf-8"))
    entry = {
        "name": "Darth Vader",
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
    owner["figures"] = [fig for fig in figures if fig.get("name") != "Darth Vader"] + [entry]
    owner["vaderNote"] = "Darth Vader stamps follow data/references/owner-verified/darth-vader.md (owner Warren, 2026-10-11)."
    STAMPS.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def coo(detail):
    return {"category": "coo", "detail": detail, "where": "Look at the country stamp on the back of the left thigh."}


def paint(detail):
    return {"category": "paint", "detail": detail, "where": "Look at the paint colour."}


def mould(detail):
    return {"category": "mould", "detail": detail, "where": "Look at the mould: shape, proportions, tip or hilt."}


def assembly(detail):
    return {"category": "assembly", "detail": detail, "where": "Look at how the figure is put together."}


def variant(vid, factory, mould_name, tells):
    return {
        "id": vid,
        "figure": "Darth Vader",
        "factory": factory,
        "mould": mould_name,
        "source": "owner",
        "sourceUrl": "https://www.variantvillain.com/characters/sw/darth-vader/",
        "sourceNote": NOTE,
        "tells": tells,
    }


def vader_variants():
    return [
        variant("darth-vader--kader-m1", "Kader M1", "M1", [
            coo(f"{THIGH} {HK}. {H_UNDER}. Family I on COO guide 3.2."),
        ]),
        variant("darth-vader--kader-m2", "Kader M2", "M2", [
            coo(f"{THIGH} {HK}. {H_UNDER}. Family II on COO guide 3.2. No gate scar."),
        ]),
        variant("darth-vader--poch-m2", "Poch", "M2", [
            coo(f"{THIGH} {HK}. Family II, the same stamp as Kader M2."),
            mould("A big leftover gate scar by the stamp."),
        ]),
        variant("darth-vader--kader-m3", "Kader M3", "M3", [
            coo(f"{THIGH} {HK}. {H_UNDER}. Family III on COO guide 3.2."),
        ]),
        variant("darth-vader--kader-china", "Kader China", "", [
            coo(f"{THIGH} {BAR}. This is Kader China, not Kader M1."),
        ]),
        variant("darth-vader--kader-m3-no-coo", "Kader M3 No COO", "M3", [
            coo(f"{THIGH} {LINE}. This is Kader family III No COO, not the blank raised bar and not Kader M1."),
        ]),
        variant("darth-vader--glasslite-m3", "Glasslite M3", "M3", [
            coo(f"{THIGH} {LINE}."),
            paint("The belt-buckle circle is not painted white."),
        ]),
        variant("darth-vader--smile-m4", "Smile M4", "M4", [
            coo(f"{THIGH} {HK}. Smile Vader is always HONG KONG. Family IV on COO guide 3.2."),
        ]),
        variant("darth-vader--lili-ledy-m4", "Lili Ledy M4", "M4", [
            coo(f"{THIGH} Clear remnants of HONG KONG beside the licensing line. "
                "A partly visible country counts as No COO. VV calls this the Retorno version."),
        ]),
        variant("darth-vader--lili-ledy-m4-no-coo", "Lili Ledy M4 No COO", "M4", [
            coo(f"{THIGH} {LINE}. Lili Ledy family IV. VV calls this the Regreso version."),
        ]),
        variant("darth-vader--unitoy-m5", "Unitoy M5", "M5", [
            coo(f"{THIGH} {MADE_HK}."),
        ]),
        variant("darth-vader--unitoy-m6", "Unitoy M6", "M6", [
            coo(f"{THIGH} {HK}. The stamp text matches Unitoy M7."),
            mould("Two dots on each foot sole, one in the middle of the sole and one on the toes."),
        ]),
        variant("darth-vader--unitoy-m7", "Unitoy M7", "M7", [
            coo(f"{THIGH} {HK}. The stamp text matches Unitoy M6."),
            mould("No dots on the foot soles."),
        ]),
        variant("darth-vader--unitoy-m8", "Unitoy M8", "M8", [
            coo(f"{THIGH} {HK}. Family VIII on COO guide 3.2."),
        ]),
        variant("darth-vader--pbp-m8", "PBP M8", "M8", [
            coo(f"{THIGH} {SCAR}."),
        ]),
        variant("darth-vader--top-toys-m9", "Top Toys M9", "M9", [
            coo(f"{THIGH} {BARE}."),
        ]),
        variant("darth-vader--taiwan-m10", "Taiwan M10", "M10", [
            coo(f"{THIGH} {MADE_TW}. Family X."),
        ]),
        variant("darth-vader--taiwan-m11", "Taiwan M11", "M11", [
            coo(f"{THIGH} {TW}. Family XI."),
        ]),
        variant("darth-vader--takara-m12", "Takara M12", "M12", [
            coo(f"{THIGH} {JAPAN}."),
            assembly("A cross-slot screw is in the back."),
        ]),
    ]


VADER_LINKS = {
    "telescoping-lightsaber--unknown-m1": [
        "darth-vader--kader-m1",
        "darth-vader--kader-m2",
        "darth-vader--kader-m3",
        "darth-vader--smile-m4",
        "darth-vader--unitoy-m5",
        "darth-vader--unitoy-m6",
        "darth-vader--unitoy-m7",
        "darth-vader--unitoy-m8",
        "darth-vader--taiwan-m10",
    ],
    "telescoping-lightsaber--unitoy-m2": [
        "darth-vader--unitoy-m5",
        "darth-vader--unitoy-m6",
        "darth-vader--unitoy-m7",
        "darth-vader--unitoy-m8",
    ],
    "telescoping-lightsaber--unitoy-m3": [
        "darth-vader--unitoy-m5",
        "darth-vader--unitoy-m6",
        "darth-vader--unitoy-m7",
        "darth-vader--unitoy-m8",
    ],
    "telescoping-lightsaber--lili-ledy-m3": ["darth-vader--lili-ledy-m4"],
    "telescoping-lightsaber--takara-m4": ["darth-vader--takara-m12"],
    "telescoping-lightsaber--kader-m5": [
        "darth-vader--kader-m1",
        "darth-vader--kader-m3",
        "darth-vader--poch-m2",
    ],
    "telescoping-lightsaber--smile-m5": ["darth-vader--smile-m4"],
    "telescoping-lightsaber--pbp-m5": ["darth-vader--pbp-m8"],
    "telescoping-lightsaber--pbp-m6": ["darth-vader--pbp-m8"],
    "telescoping-lightsaber--taiwan-m7": [
        "darth-vader--taiwan-m10",
        "darth-vader--taiwan-m11",
    ],
    "telescoping-lightsaber--glasslite-m8": ["darth-vader--glasslite-m3"],
    "telescoping-lightsaber--lili-ledy-m9": [
        "darth-vader--lili-ledy-m4-no-coo",
        "ben-obi-wan-kenobi--lili-ledy",
    ],
    "telescoping-lightsaber--top-toys-m10": ["darth-vader--top-toys-m9"],
    "darth-vader-cape--poch-m17": ["darth-vader--poch-m2"],
}


def apply_sabre_links(payload):
    for row in payload.get("accessoryVariants") or []:
        current = list(row.get("cardedWith") or [])
        extra = VADER_LINKS.get(row.get("id"))
        touched = extra is not None or any(str(item).startswith("darth-vader--") for item in current)
        if row.get("accessory") not in ("Telescoping Lightsaber", "Darth Vader Cape") and not touched:
            continue
        if not touched:
            continue
        extra_ids = list(extra or [])
        others = [
            item for item in current
            if item not in extra_ids and not str(item).startswith("darth-vader--")
        ]
        row["cardedWith"] = others + extra_ids


BEN_LILI = {
    "id": "ben-obi-wan-kenobi--lili-ledy",
    "figure": "Ben (Obi-Wan) Kenobi",
    "factory": "Lili Ledy",
    "mould": "",
    "source": "owner",
    "sourceUrl": "https://www.variantvillain.com/characters/sw/ben-obi-wan-kenobi/",
    "sourceNote": "Owner Warren, 11 Oct 2026. data/references/owner-verified/darth-vader.md. Telescoping Lightsaber M9 is this Lili Ledy Ben.",
    "tells": [],
}


def ensure_lili_ledy_ben(payload):
    rows = payload.get("figureVariants") or []
    kept = [row for row in rows if row.get("id") != BEN_LILI["id"]]
    out = []
    inserted = False
    for row in kept:
        out.append(row)
        if row.get("id") == "ben-obi-wan-kenobi--unspecified":
            out.append(dict(BEN_LILI))
            inserted = True
    if not inserted:
        out.append(dict(BEN_LILI))
    payload["figureVariants"] = out


def apply_factory_match(payload):
    load_owner()
    fresh = vader_variants()
    out = []
    inserted = False
    for row in payload.get("figureVariants") or []:
        if row.get("figure") == "Darth Vader":
            if not inserted:
                out.extend(fresh)
                inserted = True
            continue
        out.append(row)
    if not inserted:
        out.extend(fresh)
    payload["figureVariants"] = out
    ensure_lili_ledy_ben(payload)
    apply_sabre_links(payload)
    payload["vaderOwner"] = "data/references/owner-verified/darth-vader.md"
    return payload


STAMP_BLOCK = """STAMP

The stamp is on the back of the left thigh. Kader M1, M2 and M3: the H of HONG starts under the ©. A blank raised bar is Kader China, not Kader M1. Smile Vader is always HONG KONG. Top Toys has no markings at all.

"""
LONG_STAMP = (
    "The stamp is on the back of the left thigh, in two side-by-side columns. "
    "On Kader M1, M2 and M3, the H of HONG starts under the ©. "
    "Use COO guide 3.2 to separate families I, II and III. "
    "A blank raised bar is Kader China, not Kader M1. Smile Vader is always HONG KONG. "
    "Lili Ledy family IV is No COO: one version has no country, and one shows remnants of HONG KONG. "
    "A partly visible country counts as No COO. Unitoy M6 has two dots on each foot sole. "
    "Unitoy M7 has none. Top Toys has no markings at all.\n"
)


def apply_guides():
    load_owner()
    raw = FIGURE.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")
    text = text.replace(LONG_STAMP, STAMP_BLOCK.split("STAMP\n\n", 1)[1])
    if "back of the left thigh" not in text:
        text = text.replace("\nCOO FAMILIES\n", "\n" + STAMP_BLOCK + "COO FAMILIES\n", 1)
    text = text.replace(
        "- Smile → M4 then M3\n- Lili Ledy → M3 then M9\n",
        "- Smile sabres: M1, then M5\n- Lili Ledy sabres: M3, then M9\n",
    )
    text = text.replace(
        "- Smile Vader sabres are M1, then M5\n"
        "- Lili Ledy sabres are M3 on the remnants version and M9 on the version with no country\n",
        "- Smile sabres: M1, then M5\n- Lili Ledy sabres: M3, then M9\n",
    )
    for extra in (
        "- Poch uses this family, with a gate scar by the stamp and cape M17\n",
        "  - The belt-buckle circle is not painted white\n",
        "- A cross-slot screw is in the back\n",
        "- Family 6 has two dots on each foot sole. Family 7 has none\n",
        "- A blank raised bar is Kader China, not a Hong Kong Kader\n",
        "- No markings at all: no copyright line and no country\n",
    ):
        text = text.replace(extra, "")
    FIGURE.write_bytes(text.replace("\n", newline).encode("utf-8"))


def main():
    load_owner()
    coo = json.loads(COO.read_text(encoding="utf-8"))
    apply_coo_figures(coo["figures"])
    COO.write_text(json.dumps(coo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    record = next(fig for fig in coo["figures"] if fig["name"] == "Darth Vader")
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
    print("darth vader owner applied")


if __name__ == "__main__":
    main()
