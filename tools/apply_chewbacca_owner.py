#!/usr/bin/env python3
"""Apply Warren's 11 Oct 2026 Chewbacca rulings.

The rulings live in data/references/owner-verified/chewbacca.md.
COO and factory-match builds call this after the R2 apply, so a regeneration
keeps the rulings. Running this file applies them to the data on disk.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "data" / "references" / "owner-verified" / "chewbacca.md"
COO = ROOT / "data" / "coo-figures.json"
STAMPS = ROOT / "data" / "coo-owner-stamps.json"
MATCH = ROOT / "data" / "factory-match.json"
PART1 = ROOT / "data" / "figures" / "chewbacca-reference-1.txt"
PART2 = ROOT / "data" / "figures" / "chewbacca-reference-2.txt"
BOW = ROOT / "data" / "accessories" / "chewbacca-bowcaster.txt"

REQUIRED = [
    "Date: 2026-10-11",
    "Source: owner Warren",
    "back of the left thigh",
    "running vertically",
    "© L.F.L. 1977",
    "© G.M.F.G.I. 1977",
    "F2.1 Hong Kong Kader still reading G.M.F.G.I.",
    "M of MADE is directly under the ©",
    "K of KONG is under the second 7",
    "H of HONG starts under the ©, to its right",
    "G of KONG ends under the second 7",
    "H starts under the middle of the ©",
    "G of KONG is under the second G",
    "Unpainted pouch",
    "Much darker plastic",
    "circle under the left foot",
    "almond eyes",
    "Two Poch",
    "faded pigment, not a variant",
    "Zuckuss-style rifle",
    "Smile M4",
    "Never use Mint as a grade",
    "partial or cut-off country name counts as No COO",
]

NOTE = "Owner Warren, 11 Oct 2026. data/references/owner-verified/chewbacca.md."
WHERE = (
    "Look on the back of the left thigh. The stamp runs vertically. "
    "The licensing line is the first column, and the country text is beside it. "
    "A partial or cut-off country name counts as No COO. The picture is COO guide 3.2."
)
EXPLANATION = (
    "The country of origin (COO) stamp on this Chewbacca is on the back of the left thigh, "
    "running vertically. The licensing line is the first column and the country text is beside it. "
    "A partial or cut-off country name counts as No COO."
)
GMFGI = "© G.M.F.G.I. 1977"
LFL = "© L.F.L. 1977"
UNITOY_POS = (
    "The M of MADE is directly under the ©, and the K of KONG is under the second 7 of 1977"
)
KADER_POS = (
    "The H of HONG starts under the ©, to its right, "
    "and the G of KONG ends under the second 7 of 1977"
)
SMILE_POS = (
    "The H of HONG starts under the middle of the ©, "
    "and the G of KONG is under the second G of G.M.F.G.I."
)
MIHK = (
    f"'{GMFGI}' and 'MADE IN HONG KONG' on the back of the left thigh. {UNITOY_POS}"
)
HK = f"'{GMFGI}' and 'HONG KONG' on the back of the left thigh"
TAIWAN = f"'{GMFGI}' and 'MADE IN TAIWAN' on the back of the left thigh"
NO_GMFGI = f"No COO. The licensing line reads '{GMFGI}'"
NO_LFL = f"No COO. The licensing line reads '{LFL}'"
DARK = "Much darker plastic than a Kenner Chewbacca"
FOOT = "A circle under the left foot, or reddish plastic with melt marks"
ALMOND = "Large almond-shaped eyes"
LIGHT = "Unpainted pouch and much lighter brown plastic"
SHORT = "Unpainted pouch, a shorter figure, and no peg holes under the feet"
PAINTED = "A painted pouch on reddish-brown plastic"
TOE = "Small blue pupils and a swollen big toe on the left foot"
TURQUOISE = "Large turquoise eyes, or melt marks on the arm or shoulder"
KADER_EYES = f"{KADER_POS}. Small mid-blue pupils"
POCH_POUCH = f"{KADER_POS}. The pouch is purple-brown"

LINKS = {
    "chewbacca-bowcaster--unitoy-m2": [
        "chewbacca--unitoy-m1",
        "chewbacca--poch-unitoy",
        "chewbacca--poch-kader",
    ],
    "chewbacca-bowcaster--kader-m1": [
        "chewbacca--kader-m2-1",
        "chewbacca--kader-m2-2",
        "chewbacca--poch-kader",
        "chewbacca--poch-unitoy",
        "chewbacca--pbp-m1",
    ],
    "chewbacca-bowcaster--smile-m4": ["chewbacca--smile-m3"],
    "chewbacca-bowcaster--smile-m3": [
        "chewbacca--smile-m3",
        "chewbacca--smile-m5",
        "chewbacca--pbp-m1",
    ],
    "chewbacca-bowcaster--lili-ledy-m4": ["chewbacca--lili-ledy-m5"],
    "chewbacca-bowcaster--taiwan-m5": ["chewbacca--taiwan-m4"],
    "chewbacca-bowcaster--top-toys-m6": ["chewbacca--top-toys-m6"],
    "zuckuss-rifle--glasslite-v4": ["chewbacca--glasslite-m2"],
}


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
    return {
        "id": fid,
        "label": label,
        "factories": factories,
        "conclusion": conclusion,
        "sure": True,
    }


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


def chewbacca_options():
    return [
        option(
            "made-in-hong-kong",
            MIHK,
            "Hong Kong",
            ["Unitoy M1", "Poch Unitoy"],
            "",
            False,
            [
                follow(
                    "unitoy-toe",
                    TOE,
                    ["Unitoy M1"],
                    "That is the Unitoy M1. "
                    + UNITOY_POS
                    + ". Small blue pupils and a swollen big toe on the left foot.",
                ),
                follow(
                    "poch-unitoy",
                    TURQUOISE,
                    ["Poch Unitoy"],
                    "That is the Poch built from Unitoy parts. Large turquoise eyes. "
                    "Melt marks on the arm or shoulder. The Hong Kong line matches Unitoy.",
                ),
            ],
        ),
        option(
            "hong-kong",
            HK,
            "Hong Kong",
            ["Kader M2.1", "Smile M3", "Poch Kader"],
            "",
            False,
            [
                follow(
                    "kader-position",
                    KADER_EYES,
                    ["Kader M2.1"],
                    "That is the Kader M2.1. "
                    + KADER_POS
                    + ". Small mid-blue pupils and small eye whites. "
                    "The licensing line reads G.M.F.G.I. 1977. Green limbs are faded pigment, not a variant.",
                ),
                follow(
                    "poch-kader",
                    POCH_POUCH,
                    ["Poch Kader"],
                    "That is the Poch built from Kader parts. "
                    + KADER_POS
                    + ". The pouch is purple-brown. Green limbs are faded pigment, not a variant.",
                ),
                follow(
                    "smile-position",
                    SMILE_POS,
                    ["Smile M3"],
                    "That is the Smile M3. "
                    + SMILE_POS
                    + " The bowcaster is Smile M4 on SW and ESB cards, then Smile M3 from the 65b/c.",
                ),
            ],
        ),
        option(
            "made-in-taiwan",
            TAIWAN,
            "Taiwan",
            ["Taiwan M4"],
            "That is the Taiwan M4. '© G.M.F.G.I. 1977' and 'MADE IN TAIWAN' run vertically "
            "on the back of the left thigh. 12-back and 21-back only.",
            True,
        ),
        option(
            "no-coo-gmfgi",
            NO_GMFGI,
            "No COO",
            ["Lili Ledy M5", "PBP M1", "Smile M5"],
            "",
            False,
            [
                follow(
                    "lili-ledy-dark",
                    DARK,
                    ["Lili Ledy M5"],
                    "That is the Lili Ledy M5. No COO, and the licensing line reads G.M.F.G.I. 1977. "
                    "The plastic is much darker than a Kenner Chewbacca.",
                ),
                follow(
                    "pbp-foot",
                    FOOT,
                    ["PBP M1"],
                    "That is the PBP M1. No COO. Reddish plastic with melt marks. "
                    "Cavity 2b has a large circle under the left foot.",
                ),
                follow(
                    "smile-almond",
                    ALMOND,
                    ["Smile M5"],
                    "That is the Smile M5. No COO, and the licensing line reads G.M.F.G.I. 1977. "
                    "Large almond-shaped eyes. The sheet's family 3 No COO Smile has the same eyes. "
                    "The bowcaster is Smile M3.",
                ),
            ],
        ),
        option(
            "no-coo-lfl",
            NO_LFL,
            "No COO",
            ["Glasslite M2", "Top Toys M6", "Kader M2.2"],
            "",
            False,
            [
                follow(
                    "glasslite-light",
                    LIGHT,
                    ["Glasslite M2"],
                    "That is the Glasslite M2. No COO, and the licensing line reads L.F.L. 1977. "
                    "Much lighter brown than a Kenner Chewbacca, with an unpainted pouch. "
                    "It came with a Zuckuss-style rifle, not a bowcaster.",
                ),
                follow(
                    "top-toys-short",
                    SHORT,
                    ["Top Toys M6"],
                    "That is the Top Toys M6. No COO, and the licensing line reads L.F.L. 1977. "
                    "It is shorter, with no peg holes under the feet, and an unpainted pouch. "
                    "This is the only Top Toys figure with a date.",
                ),
                follow(
                    "kader-potf",
                    PAINTED,
                    ["Kader M2.2"],
                    "That is the Kader M2.2. No COO. The Hong Kong text was removed and the line was "
                    "re-stamped '© L.F.L. 1977'. POTF cards and baggies. The earlier Hong Kong Kader "
                    "still reads G.M.F.G.I. 1977.",
                ),
            ],
        ),
    ]


def chewbacca_stamps():
    return [
        f"Unitoy M1 = {MIHK}.",
        "Poch Unitoy = the same MADE IN HONG KONG line, on Unitoy parts. Large turquoise eyes.",
        f"Kader M2.1 = {HK}. {KADER_POS}. The licensing line reads G.M.F.G.I. 1977.",
        f"Poch Kader = the Kader Hong Kong line. Purple-brown pouch.",
        f"Smile M3 = {HK}. {SMILE_POS}",
        f"Taiwan M4 = {TAIWAN}.",
        "PBP M1 = No COO. The licensing line reads G.M.F.G.I. 1977. Circle under the left foot on cavity 2b.",
        "Smile M5 = No COO. The licensing line reads G.M.F.G.I. 1977. Large almond-shaped eyes.",
        "Lili Ledy M5 = No COO. The licensing line reads G.M.F.G.I. 1977. Much darker plastic.",
        "Kader M2.2 = No COO. The licensing line reads L.F.L. 1977. POTF re-stamp.",
        "Glasslite M2 = No COO. The licensing line reads L.F.L. 1977. Unpainted pouch.",
        "Top Toys M6 = No COO. The licensing line reads L.F.L. 1977. The only Top Toys figure with a date.",
        "Green limbs are faded pigment, not a variant.",
    ]


def apply_coo_figures(figures):
    load_owner()
    record = next((fig for fig in figures if fig.get("name") == "Chewbacca"), None)
    if not record:
        raise SystemExit("Chewbacca is not in coo-figures")
    record["whereToLook"] = WHERE
    record["cooExplanation"] = EXPLANATION
    record["ask"] = "Which stamp do you see?"
    record["source"] = "owner"
    record["sourceNote"] = NOTE
    record["verified"] = True
    record["hasDetails"] = True
    record["options"] = chewbacca_options()
    record["ownerStamps"] = chewbacca_stamps()
    record["stamps"] = chewbacca_stamps()
    record["missing"] = ""
    record["tells"] = []
    record["referenceImage"] = {"id": "chewbacca-coo-guide-3.2"}
    return figures


def sync_owner_stamps(chewie):
    owner = json.loads(STAMPS.read_text(encoding="utf-8"))
    entry = {
        "name": "Chewbacca",
        "recorded": "2026-10-11",
        "source": "owner",
        "whereToLook": chewie["whereToLook"],
        "ask": chewie["ask"],
        "stamps": chewie["ownerStamps"],
        "options": chewie["options"],
        "referenceImage": chewie["referenceImage"],
        "missing": "",
    }
    figures = owner.get("figures") or []
    owner["figures"] = [fig for fig in figures if fig.get("name") != "Chewbacca"] + [entry]
    owner["chewbaccaNote"] = (
        "Chewbacca stamps follow data/references/owner-verified/chewbacca.md (owner Warren, 2026-10-11)."
    )
    STAMPS.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def coo(detail):
    return {"category": "coo", "detail": detail, "where": "Look at the country stamp on the back of the left thigh."}


def plastic(detail):
    return {"category": "plastic", "detail": detail, "where": "Look at the plastic colour or shade."}


def paint(detail):
    return {"category": "paint", "detail": detail, "where": "Look at the paint colour."}


def mould(detail):
    return {"category": "mould", "detail": detail, "where": "Look at the mould: shape, proportions, tip or hilt."}


def card(detail):
    return {"category": "cardback", "detail": detail, "where": "If it is still carded, which card is it on?"}


def dated(detail):
    return {"category": "date", "detail": detail, "where": "Look at the date stamp."}


def variant(vid, factory, mould_name, tells):
    return {
        "id": vid,
        "figure": "Chewbacca",
        "factory": factory,
        "mould": mould_name,
        "source": "owner",
        "sourceUrl": "https://www.variantvillain.com/characters/sw/chewbacca/",
        "sourceNote": NOTE,
        "tells": tells,
    }


def chewbacca_variants():
    return [
        variant("chewbacca--unitoy-m1", "Unitoy M1", "M1", [
            coo(f"'{GMFGI}' and 'MADE IN HONG KONG', vertical on the back of the left thigh. {UNITOY_POS}."),
            plastic("Yellow-brown plastic. Shades run from light brown to black."),
            paint("Small light-blue or dark-blue pupils. The pouch is sprayed soft in the SW era and brushed hard from mid to late ESB. A short run has the pouch dot painted."),
            mould("Swollen big toe on the left foot."),
            card("Early Bird through the 41-back."),
        ]),
        variant("chewbacca--poch-unitoy", "Poch Unitoy", "M1", [
            coo("Same MADE IN HONG KONG line as Unitoy, on Unitoy parts."),
            plastic("Light yellow-brown plastic. Melt marks on the front of the arm or shoulder. Sprue burr. Weak sonic weld."),
            paint("Large turquoise eyes. Some were overpainted in Spain."),
        ]),
        variant("chewbacca--pbp-m1", "PBP M1", "M1", [
            coo(f"No COO. The licensing line reads '{GMFGI}'. Often no date or country is readable."),
            plastic("Reddish-brown plastic. Melt marks. Glossy pouch colours vary."),
            paint("Large eyes. Pupils are light, turquoise, or mid-blue."),
            mould("Cavity 2b has a large circle under the left foot."),
        ]),
        variant("chewbacca--kader-m2-1", "Kader M2.1", "M2.1", [
            coo(f"'{GMFGI}' and 'HONG KONG', vertical on the back of the left thigh. {KADER_POS}."),
            plastic("Reddish or yellow-brown torso and limbs. Mixed shades are possible. Green limbs are faded pigment, not a variant."),
            paint("Small mid-blue pupils and small eye whites. Mid-brown pouches, some with a painted dot."),
            mould("Swollen toe."),
        ]),
        variant("chewbacca--poch-kader", "Poch Kader", "M2", [
            coo(f"Kader Hong Kong layout. '{GMFGI}'. {KADER_POS}."),
            plastic("Reddish torso. Limbs often fade green. Green limbs are faded pigment, not a variant. Burr and a weak weld."),
            paint("Purple-brown pouch. Small dark-blue pupils."),
        ]),
        variant("chewbacca--kader-m2-2", "Kader M2.2", "M2.2", [
            coo(f"No COO. The licensing line reads '{LFL}'. The Hong Kong text was removed and the line was re-stamped. POTF cards and baggies."),
            plastic("Reddish-brown. Darker pouches. Fragile paint. No toe defect."),
            paint("Mid-blue small pupils."),
            card("POTF cards and baggies only."),
        ]),
        variant("chewbacca--glasslite-m2", "Glasslite M2", "M2", [
            coo(f"No COO. '{LFL}', the same re-stamped line as the POTF Kader."),
            plastic("Much lighter brown than a Kenner Chewbacca. Unpainted pouch."),
            paint("Light-blue small pupils."),
            mould("Came with a Glasslite Zuckuss rifle, a Smile mould, not a bowcaster."),
        ]),
        variant("chewbacca--smile-m3", "Smile M3", "M3", [
            coo(f"'{GMFGI}' and 'HONG KONG', vertical on the back of the left thigh. {SMILE_POS}"),
            plastic("Reddish torso and limbs. The limbs are sometimes lighter."),
            paint("Turquoise pupils on the first ones, darker towards the Jedi era. Mid-brown pouches. The pouch can go pearlescent."),
        ]),
        variant("chewbacca--smile-m5", "Smile M5", "M5", [
            coo(f"No COO. The licensing line reads '{GMFGI}'. The sheet's family 3 No COO Smile has the same eyes."),
            paint("Large almond-shaped eyes, dark-blue small pupils, dark grey-brown or grey-green pouch."),
            card("65c-back."),
        ]),
        variant("chewbacca--lili-ledy-m5", "Lili Ledy M5", "M5", [
            coo(f"No COO. The licensing line reads '{GMFGI}'."),
            plastic("Much darker than a Kenner Chewbacca. Light or dark brown."),
            paint("Dark-blue small eyes. The pouch is green, light, mid, or reddish brown."),
        ]),
        variant("chewbacca--taiwan-m4", "Taiwan M4", "M4", [
            coo(f"'{GMFGI}' and 'MADE IN TAIWAN', vertical on the back of the left thigh."),
            plastic("Yellowish-brown, highly glossy, some matt."),
            paint("Mid-blue small pupils. Glossy mid-brown pouch."),
            mould("Wider stance. Swollen toe."),
            card("12-back and 21-back only."),
        ]),
        variant("chewbacca--top-toys-m6", "Top Toys M6", "M6", [
            coo(f"No COO. The licensing line reads '{LFL}'."),
            dated("Chewbacca is the only Top Toys figure to have a date stamp."),
            plastic("Hard brittle plastic. Shorter, because it was cast from a Kenner figure. Unpainted pouch. Flashing."),
            mould("No peg holes under the feet. Ejector-pin marks on all limbs."),
            paint("Mid-blue eyes."),
        ]),
    ]


def apply_factory_match(payload):
    load_owner()
    fresh = chewbacca_variants()
    out = []
    inserted = False
    for row in payload.get("figureVariants") or []:
        if row.get("figure") == "Chewbacca":
            if not inserted:
                out.extend(fresh)
                inserted = True
            continue
        out.append(row)
    if not inserted:
        out.extend(fresh)
    payload["figureVariants"] = out
    by_id = {row.get("id"): row for row in payload.get("accessoryVariants") or []}
    for acc_id, figure_ids in LINKS.items():
        row = by_id.get(acc_id)
        if not row:
            raise SystemExit(f"missing accessory variant {acc_id}")
        kept = [item for item in row.get("cardedWith") or [] if not str(item).startswith("chewbacca--")]
        row["cardedWith"] = kept + figure_ids
    payload["chewbaccaOwner"] = "data/references/owner-verified/chewbacca.md"
    return payload


STAMP_BLOCK = """STAMP

The stamp is on the back of the left thigh, running vertically. The licensing line is the first column, and the country text is beside it.

Unitoy M1: the M of MADE is directly under the © and the K of KONG is under the second 7 of 1977. Kader M2.1: the H of HONG starts under the ©, to its right, and the G of KONG ends under the second 7 of 1977. Smile M3: the H starts under the middle of the © and the G of KONG is under the second G of G.M.F.G.I.

Kader M2.2, Glasslite and Top Toys read "© L.F.L. 1977". All others read "© G.M.F.G.I. 1977". The earlier F2.1 Hong Kong Kader still reads G.M.F.G.I. The POTF Kader is the re-stamped L.F.L. line.

Green limbs are faded pigment, not a variant.

"""

BOW_BLOCK = """MATCHING TO FIGURES

- Unitoy Chewbacca came with the Unitoy M2 bowcaster, blue-black then blue.
- Kader Chewbacca, including the POTF re-stamp, came with the Kader M1 bowcaster.
- Smile Hong Kong came with Smile M4 on SW and ESB cards, then Smile M3 from the 65b/c.
- The late No COO Smile came with Smile M3.
- PBP came with an imported Smile M3 or Kader M1.
- Lili Ledy came with the Lili Ledy M4 solid black bowcaster.
- Taiwan came with the Taiwan M5 dull black-blue bowcaster.
- Top Toys came with the Top Toys M6 dark blue bowcaster.
- Glasslite came with a Zuckuss-style rifle, not a bowcaster.
- The two Poch Chewbaccas can carry a Unitoy M2 or a Kader M1.
"""


def apply_guides():
    load_owner()
    part1 = PART1.read_text(encoding="utf-8")
    if "back of the left thigh" not in part1:
        part1 = part1.replace("\nFIGURE VARIANT FAMILIES\n", "\n" + STAMP_BLOCK + "FIGURE VARIANT FAMILIES\n", 1)
    PART1.write_text(part1, encoding="utf-8")

    part2 = PART2.read_text(encoding="utf-8")
    part2 = part2.replace(
        "- Degraded green limbs (NOT a variant)\n",
        "- Green limbs are faded pigment, not a variant\n",
    )
    if "licensing line reads" not in part2:
        part2 = part2.replace(
            "Kader POTF Traits:\n",
            "The POTF licensing line reads © L.F.L. 1977. The earlier Hong Kong Kader still reads © G.M.F.G.I. 1977.\n\nKader POTF Traits:\n",
            1,
        )
    PART2.write_text(part2, encoding="utf-8")

    bow = BOW.read_text(encoding="utf-8")
    old = """MATCHING TO FIGURES

- Early Chewbacca → M1 or early M2
- Mid production → M2
- Later production → M3
"""
    if old in bow:
        bow = bow.replace(old, BOW_BLOCK, 1)
    elif "Zuckuss-style rifle, not a bowcaster" not in bow:
        bow = bow.replace("MATCHING TO FIGURES\n", BOW_BLOCK, 1)
    BOW.write_text(bow, encoding="utf-8")


def main():
    load_owner()
    coo = json.loads(COO.read_text(encoding="utf-8"))
    apply_coo_figures(coo["figures"])
    COO.write_text(json.dumps(coo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    chewie = next(fig for fig in coo["figures"] if fig["name"] == "Chewbacca")
    sync_owner_stamps(chewie)
    match = json.loads(MATCH.read_text(encoding="utf-8"))
    apply_factory_match(match)
    MATCH.write_text(json.dumps(match, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    apply_guides()
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_factory_match", ROOT / "tools" / "build-factory-match.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_report(match)
    print("chewbacca owner applied")


if __name__ == "__main__":
    main()
