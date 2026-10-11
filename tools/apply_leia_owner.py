#!/usr/bin/env python3
"""Apply Warren's 11 Oct 2026 Princess Leia Organa rulings.

The rulings live in data/references/owner-verified/princess-leia-organa.md.
COO and factory-match builds call this after the Luke apply, so a regeneration
keeps the rulings. Running this file applies them to the data on disk.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "data" / "references" / "owner-verified" / "princess-leia-organa.md"
COO = ROOT / "data" / "coo-figures.json"
STAMPS = ROOT / "data" / "coo-owner-stamps.json"
MATCH = ROOT / "data" / "factory-match.json"
FIGURE = ROOT / "data" / "figures" / "princess-leia-organa-reference.txt"
BLASTER = ROOT / "data" / "accessories" / "leia-blaster.txt"
CAPE = ROOT / "data" / "accessories" / "princess-leia-organa-cape.txt"

REQUIRED = [
    "Date: 2026-10-11",
    "Source: owner Warren",
    "back of the left leg",
    "© G.M.F.G.I. 1977",
    "MADE IN TAIWAN",
    "H of HONG starts under the first G of G.M.F.G.I.",
    "G of KONG sits under the 77 of 1977",
    "H of HONG starts under the ©",
    "G of KONG ends under the 9 of 1977",
    "ends before the first 1 of 1977",
    "shorter than Kader M1",
    "Smile can also be No COO",
    "Glasslite M1 and Glasslite M3",
    "Kader M1 and Kader M3 moulds",
    "both are No COO",
    "silver Jawa blaster",
    "M8 Glasslite cape",
    "curves inwards on both sides under the armholes",
    "white vinyl",
    "five Leia blaster moulds",
    "Endor Poncho Leia",
    "cape M3 is Smile",
    "not Lili Ledy",
    "partial or cut-off country name counts as No COO",
    "Never use Mint as a grade",
    "Variant Villain agreed",
]

WHERE = (
    "Look on the back of the left leg, under '© G.M.F.G.I. 1977'. "
    "A partial or cut-off country name counts as No COO."
)
HK = "'HONG KONG' on the back of the left leg under '© G.M.F.G.I. 1977'"
KADER_M1 = (
    "The H of HONG starts under the first G of G.M.F.G.I., "
    "and the G of KONG sits under the 77 of 1977"
)
KADER_M3 = (
    "The H of HONG starts under the ©, and the G of KONG ends under the 9 of 1977"
)
SMILE_HK = (
    "The H of HONG starts under the first G of the licensing line, "
    "and the word ends before the first 1 of 1977 (shorter than Kader M1)"
)
UNITOY = "'MADE IN HONG KONG' on the back of the left leg under '© G.M.F.G.I. 1977'"
TAIWAN = "'MADE IN TAIWAN' on the back of the left leg under '© G.M.F.G.I. 1977'"
NO_COO = "No COO. Licensing line only on the back of the left leg. '© G.M.F.G.I. 1977'"
SMILE_NO = "No COO under the licensing line on the back of the left leg. '© G.M.F.G.I. 1977'"

KADER_M1_ID = "princess-leia-organa--kader-m1"
KADER_M3_ID = "princess-leia-organa--kader-m3"
SMILE_ID = "princess-leia-organa--smile-m4"
GLASS_M1_ID = "princess-leia-organa--glasslite-m1"
GLASS_M3_ID = "princess-leia-organa--glasslite-m3"
UNITOY_ID = "princess-leia-organa--unitoy-m2"
TAIWAN_ID = "princess-leia-organa--taiwan-m5"
KADER_IDS = [KADER_M1_ID, KADER_M3_ID]
GLASS_IDS = [GLASS_M1_ID, GLASS_M3_ID]

LINKS = {
    "leia-blaster--kader-m1": KADER_IDS,
    "leia-blaster--smile-m2": [SMILE_ID],
    "leia-blaster--smile-m3": [SMILE_ID],
    "leia-blaster--unitoy-m4": [UNITOY_ID],
    "leia-blaster--taiwan-m5": [TAIWAN_ID],
    "princess-leia-organa-cape--kader-m1": KADER_IDS,
    "princess-leia-organa-cape--kader-m2": KADER_IDS,
    "princess-leia-organa-cape--smile-m3": [SMILE_ID],
    "princess-leia-organa-cape--unitoy-m4": [UNITOY_ID],
    "princess-leia-organa-cape--unitoy-m5": [UNITOY_ID],
    "princess-leia-organa-cape--taiwan-m6": [TAIWAN_ID],
    "princess-leia-organa-cape--taiwan-m7": [TAIWAN_ID],
    "princess-leia-organa-cape--glasslite-m8": GLASS_IDS,
    "jawa-blaster--glasslite-m2": GLASS_IDS,
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
    return {
        "id": id,
        "label": label,
        "factories": factories,
        "conclusion": conclusion,
        "sure": True,
    }


def leia_options():
    return [
        option(
            "hong-kong",
            HK,
            "Hong Kong",
            ["Kader M1", "Kader M3", "Smile M4"],
            "",
            False,
            [
                follow(
                    "kader-m1-stamp",
                    KADER_M1,
                    ["Kader M1"],
                    f"That is the Kader M1. {KADER_M1}.",
                ),
                follow(
                    "kader-m3-stamp",
                    KADER_M3,
                    ["Kader M3"],
                    f"That is the Kader M3. {KADER_M3}.",
                ),
                follow(
                    "smile-m4-stamp",
                    SMILE_HK,
                    ["Smile M4"],
                    "That is the Smile M4. The H of HONG starts under the first G of the licensing line, "
                    "and the word ends before the first 1 of 1977. That stamp is shorter than the Kader M1. "
                    "Smile can also be No COO.",
                ),
            ],
        ),
        option(
            "made-in-hong-kong",
            UNITOY,
            "Hong Kong",
            ["Unitoy M2"],
            f"That is the Unitoy M2. {UNITOY}.",
            True,
        ),
        option(
            "made-in-taiwan",
            TAIWAN,
            "Taiwan",
            ["Taiwan M5"],
            f"That is the Taiwan M5. {TAIWAN}.",
            True,
        ),
        option(
            "no-coo-glasslite",
            NO_COO,
            "No COO",
            ["Glasslite M1", "Glasslite M3"],
            "",
            False,
            [
                follow(
                    "glasslite-m1-sculpt",
                    "Same sculpt as the Kader M1",
                    ["Glasslite M1"],
                    "That is the Glasslite M1. It shares the Kader M1 mould. "
                    "Glasslite M1 and Glasslite M3 differ by paint and sculpt, and both are No COO.",
                ),
                follow(
                    "glasslite-m3-sculpt",
                    "Same sculpt as the Kader M3",
                    ["Glasslite M3"],
                    "That is the Glasslite M3. It shares the Kader M3 mould. "
                    "Glasslite M1 and Glasslite M3 differ by paint and sculpt, and both are No COO.",
                ),
            ],
        ),
        option(
            "no-coo-smile",
            SMILE_NO,
            "No COO",
            ["Smile M4"],
            "That is the Smile M4. No COO under the licensing line on the back of the left leg. "
            "Smile can also be stamped Hong Kong.",
            True,
        ),
    ]


def leia_stamps():
    return [
        f"Kader M1 = {HK}. {KADER_M1}.",
        f"Kader M3 = {HK}. {KADER_M3}.",
        f"Smile M4 = {HK}. {SMILE_HK}. Smile can also be No COO.",
        f"Unitoy M2 = {UNITOY}.",
        f"Taiwan M5 = {TAIWAN}.",
        "Glasslite M1 = No COO. Licensing line only on the back of the left leg. Shares the Kader M1 mould.",
        "Glasslite M3 = No COO. Licensing line only on the back of the left leg. Shares the Kader M3 mould.",
    ]


def apply_coo_figures(figures):
    """Patch the Princess Leia Organa record inside a coo-figures figures list."""
    load_owner()
    record = next((fig for fig in figures if fig.get("name") == "Princess Leia Organa"), None)
    if not record:
        raise SystemExit("Princess Leia Organa is not in coo-figures")
    record["whereToLook"] = WHERE
    record["ask"] = "Which stamp do you see?"
    record["source"] = "owner"
    record["sourceNote"] = "Owner Warren, 11 Oct 2026. See data/references/owner-verified/princess-leia-organa.md."
    record["verified"] = True
    record["hasDetails"] = True
    record["options"] = leia_options()
    record["ownerStamps"] = leia_stamps()
    record["stamps"] = leia_stamps()
    record["missing"] = ""
    record["tells"] = []
    return figures


def sync_owner_stamps(leia):
    owner = json.loads(STAMPS.read_text(encoding="utf-8"))
    entry = {
        "name": "Princess Leia Organa",
        "recorded": "2026-10-11",
        "source": "owner",
        "whereToLook": leia["whereToLook"],
        "ask": leia["ask"],
        "stamps": leia["ownerStamps"],
        "options": leia["options"],
        "missing": "",
    }
    figures = owner.get("figures") or []
    owner["figures"] = [fig for fig in figures if fig.get("name") != "Princess Leia Organa"] + [entry]
    owner["leiaNote"] = (
        "Princess Leia Organa stamps follow data/references/owner-verified/princess-leia-organa.md "
        "(owner Warren, 2026-10-11)."
    )
    STAMPS.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def coo_tell(detail):
    return {"category": "coo", "detail": detail, "where": "Look at the country stamp."}


def mould_tell(detail):
    return {
        "category": "mould",
        "detail": detail,
        "where": "Look at the mould: shape, proportions, tip or hilt.",
    }


def plastic_tell(detail):
    return {"category": "plastic", "detail": detail, "where": "Look at the plastic colour or shade."}


def card_tell(detail):
    return {"category": "cardback", "detail": detail, "where": "If it is still carded, which card is it on?"}


def add_link(variant, figure_id):
    links = variant.setdefault("cardedWith", [])
    if figure_id not in links:
        links.append(figure_id)


def drop_link(variant, figure_id):
    variant["cardedWith"] = [item for item in variant.get("cardedWith") or [] if item != figure_id]


def add_tell(variant, item):
    tells = variant.setdefault("tells", [])
    key = (item["category"], item["detail"])
    if any((tell.get("category"), tell.get("detail")) == key for tell in tells):
        return
    tells.append(item)


def rename_glasslite(variants):
    kept = []
    seen = set()
    for variant in variants:
        if variant.get("figure") == "Princess Leia Organa" and variant.get("id") == "princess-leia-organa--glasslite":
            variant["id"] = GLASS_M1_ID
            variant["factory"] = "Glasslite M1"
            variant["mould"] = "M1"
        vid = variant.get("id")
        if vid in seen:
            continue
        seen.add(vid)
        kept.append(variant)
    return kept


def set_coo(variant, details):
    other = [tell for tell in variant.get("tells") or [] if tell.get("category") != "coo"]
    variant["tells"] = [coo_tell(detail) for detail in details] + other
    variant["source"] = "owner"
    variant["sourceNote"] = "Owner Warren, 11 Oct 2026. data/references/owner-verified/princess-leia-organa.md."


CAPE_TELLS = {
    "princess-leia-organa-cape--kader-m1": [
        mould_tell("Very round collar. The armholes are usually not in line."),
        plastic_tell("M1a is smooth or faint, with no crosshatch. Also seen from a damaged cutting tool."),
        plastic_tell("M1b is rough, with crosshatch."),
        plastic_tell("M1c has lines and crosshatch."),
    ],
    "princess-leia-organa-cape--kader-m2": [
        mould_tell("Later Kader cape. The armholes moved down and the gap between them is wider."),
        plastic_tell("Faint lines and crosshatch."),
    ],
    "princess-leia-organa-cape--smile-m3": [
        mould_tell("Smile cape, not Lili Ledy. Pointed top to the collar. Early capes have smaller armholes."),
        plastic_tell("M3a has faint lines and crosshatch, with small holes."),
        plastic_tell("M3b is rough, with crosshatch and small holes."),
        plastic_tell("M3c is faint, with crosshatch."),
        plastic_tell("M3d is smooth, with crosshatch."),
    ],
    "princess-leia-organa-cape--unitoy-m4": [
        mould_tell("Bulgy top and sides of the collar. Very early narrow armholes."),
        plastic_tell("Crosshatch on one side and smooth on the other."),
    ],
    "princess-leia-organa-cape--unitoy-m5": [
        mould_tell("Unitoy cape later than the narrow-armhole M4."),
        plastic_tell("Crosshatch on one side and smooth on the other."),
    ],
    "princess-leia-organa-cape--taiwan-m6": [
        mould_tell("Long and very slim, with narrow armholes and bulgy corners."),
        plastic_tell("Smooth or faint, with no crosshatch."),
    ],
    "princess-leia-organa-cape--taiwan-m7": [
        mould_tell("Shorter than the M6 cape, still slim, with narrow armholes."),
        plastic_tell("Faint on both sides, with no crosshatch."),
    ],
    "princess-leia-organa-cape--glasslite-m8": [
        mould_tell(
            "Glasslite cape made in Brazil. Very distinctive shape that curves inwards on both sides under the armholes."
        ),
        plastic_tell("White vinyl. Faint or smooth."),
    ],
}


def apply_factory_match(payload):
    load_owner()
    variants = rename_glasslite(payload.get("figureVariants") or [])
    by_id = {variant.get("id"): variant for variant in variants}
    coo = {
        KADER_M1_ID: [f"{HK}. {KADER_M1}."],
        KADER_M3_ID: [f"{HK}. {KADER_M3}."],
        SMILE_ID: [
            f"{HK}. {SMILE_HK}.",
            f"{SMILE_NO}. Smile can also be No COO.",
        ],
        GLASS_M1_ID: [f"{NO_COO}. Shares the Kader M1 mould."],
        GLASS_M3_ID: [f"{NO_COO}. Shares the Kader M3 mould."],
        UNITOY_ID: [f"{UNITOY}."],
        TAIWAN_ID: [f"{TAIWAN}."],
    }
    for vid, details in coo.items():
        variant = by_id.get(vid)
        if not variant:
            raise SystemExit(f"missing Leia figure variant {vid}")
        if vid == GLASS_M1_ID:
            variant["factory"] = "Glasslite M1"
            variant["mould"] = "M1"
        set_coo(variant, details)
    for variant in payload.get("accessoryVariants") or []:
        vid = variant.get("id")
        if vid in LINKS:
            for figure_id in LINKS[vid]:
                add_link(variant, figure_id)
        if vid in CAPE_TELLS:
            variant["tells"] = CAPE_TELLS[vid]
            variant["sourceNote"] = (
                "Cape tells from the Variant Villain princess-leia-organa-cape guide. "
                "Owner Warren, 11 Oct 2026. data/references/owner-verified/princess-leia-organa.md."
            )
        if vid == "leia-blaster--lili-ledy-m1":
            for figure_id in (KADER_M1_ID, KADER_M3_ID, SMILE_ID, GLASS_M1_ID, GLASS_M3_ID, UNITOY_ID, TAIWAN_ID):
                drop_link(variant, figure_id)
            add_tell(
                variant,
                mould_tell(
                    "Grey M1 is the Lili Ledy blaster for Endor Poncho Leia. Do not pair it with this Princess Leia Organa."
                ),
            )
        if vid == "jawa-blaster--glasslite-m2":
            add_tell(
                variant,
                card_tell("Silver Jawa blaster packed with Glasslite Brazil Princess Leia Organa, in place of a Leia blaster."),
            )
    payload["figureVariants"] = variants
    payload["leiaOwner"] = "data/references/owner-verified/princess-leia-organa.md"
    return payload


BLASTER_TEXT = """Accessory Name: Princess Leia Blaster

Aliases: Leia Blaster

Category:
Primary Weapon – Small Blaster

Used With:
- Princess Leia Organa
- The grey Lili Ledy copy with Princess Leia (Endor Poncho), not this figure

Variant Villain documents five Leia blaster moulds. Black-blue is the usual colour on the original Princess Leia Organa. These mould numbers are a different series from the figure mould numbers and from the Jawa blaster.

M1 is Kader, made in Hong Kong. The mould was also used by Lili Ledy in Mexico.
- Black-blue dull, dark-blue, translucent blue-green, blue, and translucent blue.
- Light grey and dark grey are the Lili Ledy colours. That grey blaster belongs to Endor Poncho Leia. Do not pair it with this Princess Leia Organa.

M2 is Smile, the early Smile mould, later replaced by M3.
- Black-blue, translucent black-blue, translucent blue-green, and blue.

M3 is Smile, the later Smile mould.
- Translucent light-blue, translucent greenish-blue, translucent blue, dark-blue, and black-blue.

M4 is Unitoy. It seems to be a copied and retooled mould from the Taiwan M5.
- Black-blue, blue, translucent blue, and blue with a rough surface.

M5 is an unknown factory in Taiwan. It is a very early mould, probably shot on one sprue with the Taiwan crossbow, and retooled at least three times.
- Dull black-blue, dull black, and blue.

Factory links for this Princess Leia Organa. Checked on 11 Oct 2026 against the Variant Villain leia-blaster guide. Variant Villain agreed.
- Kader figures take blaster M1.
- Smile figures take blaster M2 and M3.
- Unitoy figures take blaster M4.
- Taiwan figures take blaster M5.

Glasslite (Brazil) Leia did not come with a Leia blaster. She came with a silver Jawa blaster. The Variant Villain Leia blaster guide lists no Glasslite mould. Owner Warren keeps the silver Jawa pairing.

A Hungary bootleg exists for the Csillagok Háborúja line. It is not the blaster for this Kenner figure.

Source:
https://www.variantvillain.com/accessory-guide/leia-blaster/
"""

CAPE_TEXT = """Accessory Name: Princess Leia Organa Cape

Aliases: Leia cape

Category:
Soft Goods – Vinyl Cape

Used With:
- Princess Leia Organa

The cape is white vinyl. It has no fixed front or back. The shape is asymmetrical, so it has a left and a right. Variant Villain documents 8 moulds. Cape mould numbers are a different series from the figure mould numbers and the blaster mould numbers. Shrinkage makes measurements a poor tell. Use the collar, the armholes, and the crosshatch.

M1 is Kader. The collar is very round. The armholes are usually not in line. Early capes have no crosshatch.
- M1a is smooth or faint, with no crosshatch, including a damaged cutting tool.
- M1b is rough, with crosshatch.
- M1c has lines and crosshatch.

M2 is later Kader. The armholes moved down and the gap between them is wider. It has faint lines and crosshatch.

M3 is Smile, not Lili Ledy. The collar has a pointed top. Early capes have smaller armholes. Later armholes are larger.
- M3a has faint lines and crosshatch, with small holes.
- M3b is rough, with crosshatch and small holes.
- M3c is faint, with crosshatch.
- M3d is smooth, with crosshatch.

M4 is Unitoy. The collar is bulgy on the top and the sides. This is a very early cape with narrow armholes. It is crosshatch on one side and smooth on the other.

M5 is Unitoy. It is crosshatch on one side and smooth on the other. It is later than the narrow-armhole M4.

M6 is an unknown factory in Taiwan. It is long and very slim, with narrow armholes and bulgy corners. It is smooth or faint, with no crosshatch.

M7 is Taiwan. It is shorter than M6 and still slim, with narrow armholes. It is faint on both sides, with no crosshatch.

M8 is Glasslite, made in Brazil. The vinyl is white, like the other capes. The shape is very distinctive and curves inwards on both sides under the armholes. It is faint or smooth.

Factory links for this Princess Leia Organa. Checked on 11 Oct 2026 against the Variant Villain cape guide. Variant Villain agreed.
- Kader figures take cape M1 and M2.
- Smile figures take cape M3.
- Unitoy figures take cape M4 and M5.
- Taiwan figures take cape M6 and M7.
- Glasslite figures take cape M8.

The 2019 Retro Collection cape is wider and taller than any vintage cape. Both sides are smooth and there is no crosshatch. It mostly imitates the Kader M1 shape.

Reproductions R1 to R5 have no crosshatch. R1 and R4 are die-cut and stiffer than vintage vinyl. R2, R3 and R5 are handcut.

Source:
https://www.variantvillain.com/accessory-guide/princess-leia-organa-cape/
"""

FIGURE_BLOCK = """Owner-verified COO (Warren, 11 Oct 2026):

The country stamp is on the back of the left leg, under "© G.M.F.G.I. 1977". A partial or cut-off country name counts as No COO.

Kader M1 and Kader M3 both read HONG KONG. They differ by paint and sculpt, and by where the stamp sits. On Kader M1 the H of HONG starts under the first G of G.M.F.G.I., and the G of KONG sits under the 77 of 1977. On Kader M3 the H of HONG starts under the ©, and the G of KONG ends under the 9 of 1977.

Smile M4 reads HONG KONG with the H of HONG under the first G of the licensing line, and the word ends before the first 1 of 1977. That stamp is shorter than Kader M1. Smile can also be No COO.

'MADE IN TAIWAN' is on the back of the left leg under the licensing line.

Glasslite M1 and Glasslite M3 are both No COO. They share the Kader M1 and Kader M3 moulds respectively. Glasslite (Brazil) came with a silver Jawa blaster instead of a Leia blaster, and with the M8 cape. The M8 cape is white vinyl and curves inwards on both sides under the armholes.

The grey Lili Ledy blaster is M1 for Endor Poncho Leia. Do not pair it with this figure. Cape M3 is Smile, not Lili Ledy.
"""


def apply_guides():
    load_owner()
    BLASTER.write_text(BLASTER_TEXT, encoding="utf-8")
    CAPE.write_text(CAPE_TEXT, encoding="utf-8")
    text = FIGURE.read_text(encoding="utf-8")
    text = text.replace("M4 – Unitoy / Lili Ledy", "M4 – Unitoy")
    grey = "- The grey Lili Ledy blaster is M1, for Endor Poncho Leia. Do not pair it with this figure.\n"
    silver = "- Glasslite (Brazil) Leia came with a silver Jawa blaster instead of a Leia blaster, and with the M8 cape.\n"
    if grey not in text:
        text = text.replace("- 5 main moulds + subvariants\n", "- 5 main moulds + subvariants\n" + grey + silver, 1)
    if "Owner-verified COO (Warren, 11 Oct 2026):" in text:
        text = re.sub(
            r"\nOwner-verified COO \(Warren, 11 Oct 2026\):.*?(?=\nSources:\n)",
            "\n" + FIGURE_BLOCK + "\n",
            text,
            count=1,
            flags=re.S,
        )
    else:
        text = text.replace("\nSources:\n", "\n" + FIGURE_BLOCK + "\nSources:\n", 1)
    FIGURE.write_text(text, encoding="utf-8")


def main():
    load_owner()
    coo = json.loads(COO.read_text(encoding="utf-8"))
    apply_coo_figures(coo["figures"])
    COO.write_text(json.dumps(coo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    leia = next(fig for fig in coo["figures"] if fig["name"] == "Princess Leia Organa")
    sync_owner_stamps(leia)
    match = json.loads(MATCH.read_text(encoding="utf-8"))
    apply_factory_match(match)
    MATCH.write_text(json.dumps(match, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    apply_guides()
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "build_factory_match", ROOT / "tools" / "build-factory-match.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_report(match)
    print("leia owner applied")


if __name__ == "__main__":
    main()
