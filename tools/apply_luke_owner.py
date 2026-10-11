#!/usr/bin/env python3
"""Apply Warren's 11 Oct 2026 Luke Skywalker rulings.

The rulings live in data/references/owner-verified/luke-skywalker.md.
COO and factory-match builds call this after they write, so a regeneration
keeps the rulings. Running this file applies them to the data on disk.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "data" / "references" / "owner-verified" / "luke-skywalker.md"
COO = ROOT / "data" / "coo-figures.json"
STAMPS = ROOT / "data" / "coo-owner-stamps.json"
MATCH = ROOT / "data" / "factory-match.json"
FACTORIES = ROOT / "data" / "factories.json"
COVERAGE = ROOT / "docs" / "cross-reference-coverage.md"
VV = "https://www.variantvillain.com/characters/sw/luke-skywalker/"
SABRE = "https://www.variantvillain.com/accessory-guide/telescoping-lightsaber/"
DT_URL = "https://www.variantvillain.com/accessory-guide/double-telescoping-lightsaber/"

REQUIRED = [
    "Date: 2026-10-11",
    "Source: owner Warren",
    "back of the left leg",
    "© G.M.F.G.I. 1977",
    "partial or cut-off country name counts as No COO",
    "Never use Mint as a grade",
    "Poch is the Spanish factory later renamed PBP",
    "older moulds",
    "pale cream hands",
    "higher left eyebrow",
    "melt marks",
    "Brown-hair Poch",
    "Unitoy head on Kader-COO legs",
    "unknown company",
    "sinks in water",
    "12A/B/C",
    "12A only",
    "not Smile",
    "M6 yellow",
    "circled double-telescoping",
    "Lettered sabres are always M1",
    "blank raised bar",
    "no bar points to Smile",
    "bright blonde hair",
    "pinkish hands",
    "double raised bar",
    "scarred raised bar",
    "Kader China (China)",
    "Lili Ledy (Mexico)",
    "Takara (Japan)",
    "Top Toys (Argentina)",
]

WHERE = (
    "Look on the back of the left leg, under '© G.M.F.G.I. 1977'. "
    "A partial or cut-off country name counts as No COO."
)
HK = "'Hong Kong' on the back of the left leg under licensing details. '© G.M.F.G.I. 1977'"
CHINA = "'China' on a raised bar on the back of the left leg under licensing details. '© G.M.F.G.I. 1977'"
SCAR = "COO scar on the back of the left leg under licensing details. '© G.M.F.G.I. 1977'"
TAIWAN = "Taiwan on the back of the left leg under licensing details. '© G.M.F.G.I. 1977'"
SMILE_HK = "'Hong Kong' on the back of the left leg. '© G.M.F.G.I. 1977'"
NO_COO = "No COO on the back of the left leg. '© G.M.F.G.I. 1977'"
BLANK = "No COO blank raised bar under licensing details. '© G.M.F.G.I. 1977'"
POCH_BLONDE = (
    "Poch blonde hair, pale cream hands, greyish blotchy trousers and boots, "
    "higher left eyebrow, melt marks on the back"
)
POCH_BROWN = "Poch brown hair, dark trousers and boots, pale cream or pinkish hands and neck"
POCH_MIXED = "Poch mixed, a Unitoy head on Kader-COO legs"
SABRE_TELL = re.compile(r"(?i)\b(saber|sabre|lightsaber|flat tip|thin tip|lettered|telescop)")

LUKE_M1 = [
    "luke-skywalker--kader-m1",
    "luke-skywalker--unitoy-m2",
    "luke-skywalker--smile-m4",
    "luke-skywalker--taiwan-m3",
]
M1_OLD = [
    "telescoping-lightsaber--kader-m1",
    "telescoping-lightsaber--unitoy-m1",
    "telescoping-lightsaber--smile-m1",
    "telescoping-lightsaber--taiwan-m1",
]
M1_ID = "telescoping-lightsaber--unknown-m1"
POCH_M5 = ["luke-skywalker--poch-blonde", "luke-skywalker--poch-brown-hair"]
M5_LUKE = [
    "luke-skywalker--kader-m1",
    "luke-skywalker--smile-m4",
    "luke-skywalker--pbp-m2",
    *POCH_M5,
]


def load_owner():
    if not OWNER.is_file():
        raise SystemExit(f"missing owner record {OWNER}")
    text = OWNER.read_text(encoding="utf-8")
    folded = text.casefold()
    missing = [phrase for phrase in REQUIRED if phrase.casefold() not in folded]
    if missing:
        raise SystemExit("owner record is missing rulings: " + "; ".join(missing))
    return text


def tell(category, detail, where):
    return {"category": category, "detail": detail, "where": where}


def coo_tell(detail):
    return tell("coo", detail, "Look at the country stamp.")


def hair(detail):
    return tell("hair", detail, "Look at the hair colour.")


def paint(detail):
    return tell("paint", detail, "Look at the paint colour.")


def option(id, label, factories, conclusion, sure, follows=None, coo=""):
    return {
        "id": id,
        "label": label,
        "coo": coo,
        "factories": factories,
        "examples": [label],
        "conclusion": "" if follows else conclusion,
        "sure": False if follows else sure,
        "followUps": follows or [],
    }


def follow(id, label, factories, conclusion):
    return {
        "id": id,
        "label": label,
        "factories": factories,
        "conclusion": conclusion,
        "sure": True,
    }


def luke_options():
    shared = ["Kader M1", "Unitoy M2", "Poch blonde", "Poch brown-hair", "Poch mixed"]
    return [
        option(
            "hong-kong-on-left-leg-under-licensing-details-g-",
            HK,
            shared,
            "That stamp is shared by the Kader M1, the Unitoy M2, the Poch blonde, the Poch brown-hair, and the Poch mixed. "
            + HK
            + ". I'm not sure which of those it is from the stamp alone.",
            False,
            coo="Hong Kong",
        ),
        option(
            "china-on-a-raised-bar-under-licensing-details-on",
            CHINA,
            ["Kader China M1"],
            f"That is the Kader China M1. {CHINA}.",
            True,
            coo="China",
        ),
        option(
            "no-coo-on-the-back-of-the-left-leg",
            NO_COO,
            ["Meccano M1", "Glasslite M1", "Smile No COO"],
            "",
            False,
            follows=[
                follow(
                    "blank-bar-less-defined",
                    "Blank raised bar, and the licensing details are less defined",
                    ["Glasslite M1"],
                    "That is the Glasslite M1. Glasslite and Meccano have a blank raised bar, and the licensing details are less defined.",
                ),
                follow(
                    "blank-bar-ordinary",
                    "Blank raised bar, and the licensing details look ordinary",
                    ["Meccano M1"],
                    "That is the Meccano M1. Glasslite and Meccano have a blank raised bar, and the licensing line is the ordinary one.",
                ),
                follow(
                    "no-bar",
                    "No raised bar",
                    ["Smile No COO"],
                    "That is the Smile No COO. A No COO Luke with no bar is Smile.",
                ),
            ],
            coo="No COO",
        ),
        option(
            "coo-scar-on-left-leg-under-licensing-details-g-m",
            SCAR,
            ["PBP M2"],
            f"That is the PBP M2. {SCAR}.",
            True,
            coo="No COO",
        ),
        option(
            "taiwan-on-left-leg-under-licensing-details-g-m-f",
            TAIWAN,
            ["Taiwan M3"],
            f"That is the Taiwan M3. {TAIWAN}.",
            True,
            coo="Taiwan",
        ),
        option(
            "hong-kong-on-left-leg-g-m-f-g-i-1977",
            SMILE_HK,
            ["Smile M4"],
            f"That is the Smile M4. {SMILE_HK}.",
            True,
            coo="Hong Kong",
        ),
    ]


def luke_stamps():
    return [
        f"Kader M1 = {HK}.",
        f"Kader China M1 = {CHINA}.",
        "Meccano M1: blank raised bar, No COO, ordinary licensing details. '© G.M.F.G.I. 1977'.",
        "Glasslite M1: blank raised bar, No COO. Licensing details are less defined. '© G.M.F.G.I. 1977'.",
        f"Unitoy M2: {HK}.",
        "Poch blonde = Kader COO. Pale cream hands, darker greyish blotchy trousers and boots, higher left eyebrow, melt marks on the back.",
        "Poch brown-hair = Unitoy COO. Dark trousers and boots, pale cream or pinkish hands and neck.",
        "Poch mixed = Unitoy head on Kader-COO legs.",
        f"PBP M2: {SCAR}. Bright blonde hair, pinkish hands and neck, scarred Unitoy COO.",
        f"Taiwan M3 = {TAIWAN}.",
        f"Smile M4 = {SMILE_HK}.",
        "Smile No COO = no raised bar. A No COO Luke with no bar is Smile.",
    ]


def luke_tells():
    """Figure tells only. Sabre moulds stay on the sabre records."""
    return [
        paint("Kader with brown eyes (the earliest Kader figure)"),
        hair("Kader with dull light yellow hair, transition face spray-mask to china, and light flesh hands"),
        paint("Kader with reddish eyes"),
        paint("Kader with black eyes"),
        paint("Unitoy with brown eyes and an opaque body, the earliest Unitoy figure. The opaque material tends to yellow."),
        paint("Unitoy black eyes"),
        paint("Unitoy large black eyes"),
        hair("Unitoy orange hair (dull, US version from 41E-back)"),
        hair("Unitoy orange hair (AU version)"),
        paint("Taiwan with brown eyes and light brown trousers/boots"),
        paint("Taiwan with dark brown eyes and brown trousers/boots"),
        paint("Taiwan with dark brown eyes and reddish brown trousers/boots"),
        paint("Taiwan with dark brown eyes and dark brown trousers/boots"),
        paint("Taiwan with black eyes and dark grey trousers/boots"),
        hair("Smile, early figure with pale yellow hair"),
        hair("Smile with bright yellow hair"),
        hair("Smile with bright yellow hair and tan boots"),
        hair("Smile HK with reddish light brown hair (appeared on HK and No Coo)"),
        hair("Smile No Coo with greenish light brown hair (appeared on HK and No Coo)"),
        hair(POCH_BLONDE),
        hair(POCH_BROWN),
        hair(POCH_MIXED),
        hair("PBP with bright blonde hair"),
        paint("PBP with pinkish hands and neck"),
    ]


def with_factories(item, factories):
    copied = dict(item)
    copied["factories"] = factories
    return copied


def apply_coo_figures(figures):
    """Patch the Luke record inside a coo-figures figures list."""
    load_owner()
    record = next((fig for fig in figures if fig.get("name") == "Luke Skywalker"), None)
    if not record:
        raise SystemExit("Luke Skywalker is not in coo-figures")
    record["whereToLook"] = WHERE
    record["ask"] = "Which stamp do you see?"
    record["source"] = "owner"
    record["sourceNote"] = "Owner Warren, 11 Oct 2026. See data/references/owner-verified/luke-skywalker.md."
    record["verified"] = True
    record["hasDetails"] = True
    record["options"] = luke_options()
    record["ownerStamps"] = luke_stamps()
    record["missing"] = ""
    record["tells"] = [
        with_factories(item, factories)
        for item, factories in (
            (luke_tells()[0], ["Kader"]),
            (luke_tells()[1], ["Kader"]),
            (luke_tells()[2], ["Kader"]),
            (luke_tells()[3], ["Kader"]),
            (luke_tells()[4], ["Unitoy"]),
            (luke_tells()[5], ["Unitoy"]),
            (luke_tells()[6], ["Unitoy"]),
            (luke_tells()[7], ["Unitoy"]),
            (luke_tells()[8], ["Unitoy"]),
            (luke_tells()[9], ["Taiwan"]),
            (luke_tells()[10], ["Taiwan"]),
            (luke_tells()[11], ["Taiwan"]),
            (luke_tells()[12], ["Taiwan"]),
            (luke_tells()[13], ["Taiwan"]),
            (luke_tells()[14], ["Smile"]),
            (luke_tells()[15], ["Smile"]),
            (luke_tells()[16], ["Smile"]),
            (luke_tells()[17], ["Smile"]),
            (luke_tells()[18], ["Smile"]),
            (luke_tells()[19], ["Poch blonde"]),
            (luke_tells()[20], ["Poch brown-hair"]),
            (luke_tells()[21], ["Poch mixed"]),
            (luke_tells()[22], ["PBP"]),
            (luke_tells()[23], ["PBP"]),
        )
    ]
    rewrite_family_lines(record)
    return figures


def rewrite_family_lines(record):
    """Take sabre sentences out of the figure families. Tells are set separately."""
    replacements = {
        "kader with dt (lettered) saber, brown eyes (which is assumed to be the earliest kader figure)":
            "Kader with brown eyes (the earliest Kader figure)",
        "unitoy with dt (circled) saber, brown eyes and opaque body which is the earliest unitoy figure. sadly the opaque material tends to yellow quite easily.":
            "Unitoy with brown eyes and an opaque body, the earliest Unitoy figure. The opaque material tends to yellow.",
    }
    drop = {
        "unitoy changed from lettered to flat tip transition",
        "already on 12b-back. so almost every unitoy figure came with “thick tip, flat transition”",
        "and later with “thin tip, flat transition”",
    }
    added = {
        POCH_BLONDE,
        POCH_BROWN,
        POCH_MIXED,
        "PBP with bright blonde hair, pinkish hands and neck, scarred Unitoy COO",
    }
    for family in record.get("families") or []:
        kept = []
        title = (family.get("title") or "").lower()
        family_ii = re.search(r"coo family ii\b", title) is not None
        for line in family.get("lines") or []:
            key = re.sub(r"\s+", " ", line).strip().lower()
            if key in drop or line in added:
                continue
            if family_ii and line.strip() in {"M2"}:
                continue
            kept.append(replacements.get(key, line))
        if re.search(r"coo family i\b", title):
            kept.append(POCH_BLONDE)
        if family_ii:
            kept.extend([
                POCH_BROWN,
                POCH_MIXED,
                "PBP with bright blonde hair, pinkish hands and neck, scarred Unitoy COO",
            ])
        family["lines"] = kept


def sync_owner_stamps(luke):
    owner = json.loads(STAMPS.read_text(encoding="utf-8"))
    entry = {
        "name": "Luke Skywalker",
        "recorded": "2026-10-11",
        "source": "owner",
        "whereToLook": luke["whereToLook"],
        "ask": luke["ask"],
        "stamps": luke["ownerStamps"],
        "options": luke["options"],
        "missing": "",
    }
    figures = owner.get("figures") or []
    owner["figures"] = [fig for fig in figures if fig.get("name") != "Luke Skywalker"] + [entry]
    owner["lukeNote"] = "Luke Skywalker stamps follow data/references/owner-verified/luke-skywalker.md (owner Warren, 2026-10-11)."
    STAMPS.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def figure_variant(id, factory, mould, tells):
    return {
        "id": id,
        "figure": "Luke Skywalker",
        "factory": factory,
        "mould": mould,
        "source": "owner",
        "sourceNote": "Owner Warren, 11 Oct 2026. data/references/owner-verified/luke-skywalker.md.",
        "sourceUrl": VV,
        "tells": tells,
    }


def luke_variant_tells():
    return {
        "luke-skywalker--kader-m1": [
            coo_tell(HK),
            paint("Kader with brown eyes (the earliest Kader figure)"),
            paint("Kader with reddish eyes"),
            paint("Kader with black eyes"),
            hair("Kader with dull light yellow hair, transition face spray-mask to china, and light flesh hands"),
        ],
        "luke-skywalker--unitoy-m2": [
            coo_tell(HK),
            paint("Unitoy with brown eyes and an opaque body, the earliest Unitoy figure. The opaque material tends to yellow."),
            paint("Unitoy black eyes"),
            paint("Unitoy large black eyes"),
            hair("Unitoy orange hair (dull, US version from 41E-back)"),
            hair("Unitoy orange hair (AU version)"),
            hair("Unitoy with yellowish dark brown hair"),
            hair("Unitoy with reddish dark brown hair"),
            hair("Unitoy with greenish dark brown hair"),
            hair("Unitoy with very dark brown hair"),
        ],
        "luke-skywalker--kader-china-m1": [coo_tell(CHINA)],
        "luke-skywalker--meccano-m1": [
            coo_tell(BLANK),
            coo_tell("French Trilogo (Meccano) double raised bar"),
            coo_tell("French Trilogo (Meccano) scarred raised bar"),
        ],
        "luke-skywalker--glasslite-m1": [
            coo_tell(BLANK),
            coo_tell("Glasslite licensing details are less defined"),
        ],
        "luke-skywalker--pbp-m2": [
            coo_tell(SCAR),
            coo_tell("PBP with a scarred Unitoy COO"),
            hair("PBP with bright blonde hair"),
            paint("PBP with pinkish hands and neck"),
        ],
        "luke-skywalker--taiwan-m3": [
            coo_tell(TAIWAN),
            paint("Taiwan with brown eyes and light brown trousers/boots"),
            paint("Taiwan with dark brown eyes and brown trousers/boots"),
            paint("Taiwan with dark brown eyes and reddish brown trousers/boots"),
            paint("Taiwan with dark brown eyes and dark brown trousers/boots"),
            paint("Taiwan with black eyes and dark grey trousers/boots"),
        ],
        "luke-skywalker--smile-m4": [
            coo_tell(SMILE_HK),
            hair("Smile, early figure with pale yellow hair"),
            hair("Smile with bright yellow hair"),
            hair("Smile with bright yellow hair and tan boots"),
            hair("Smile HK with reddish light brown hair (appeared on HK and No Coo)"),
            hair("Smile No Coo with greenish light brown hair (appeared on HK and No Coo)"),
        ],
        "luke-skywalker--smile-no-coo": [
            coo_tell("No COO on the back of the left leg, no raised bar. '© G.M.F.G.I. 1977'"),
            hair("Smile No COO with brown hair on a Trilogo card"),
            hair("Smile No Coo with greenish light brown hair (appeared on HK and No Coo)"),
        ],
        "luke-skywalker--poch-blonde": [
            coo_tell(HK),
            hair(POCH_BLONDE),
            paint("Poch with pale cream hands and darker greyish blotchy trousers and boots"),
        ],
        "luke-skywalker--poch-brown-hair": [
            coo_tell(HK),
            hair(POCH_BROWN),
        ],
        "luke-skywalker--poch-mixed": [
            coo_tell(HK),
            hair(POCH_MIXED),
        ],
    }


def upsert_figures(variants):
    canonical = luke_variant_tells()
    by_id = {variant["id"]: variant for variant in variants}
    for id, tells in canonical.items():
        current = by_id.get(id)
        factory = {
            "luke-skywalker--kader-m1": ("Kader M1", "M1"),
            "luke-skywalker--unitoy-m2": ("Unitoy M2", "M2"),
            "luke-skywalker--kader-china-m1": ("Kader China M1", "M1"),
            "luke-skywalker--meccano-m1": ("Meccano M1", "M1"),
            "luke-skywalker--glasslite-m1": ("Glasslite M1", "M1"),
            "luke-skywalker--pbp-m2": ("PBP M2", "M2"),
            "luke-skywalker--taiwan-m3": ("Taiwan M3", "M3"),
            "luke-skywalker--smile-m4": ("Smile M4", "M4"),
            "luke-skywalker--smile-no-coo": ("Smile No COO", "M4"),
            "luke-skywalker--poch-blonde": ("Poch blonde", ""),
            "luke-skywalker--poch-brown-hair": ("Poch brown-hair", ""),
            "luke-skywalker--poch-mixed": ("Poch mixed", ""),
        }[id]
        if current and current.get("figure") == "Luke Skywalker":
            current["factory"] = factory[0]
            current["mould"] = factory[1]
            current["source"] = "owner"
            current["sourceUrl"] = VV
            current["sourceNote"] = "Owner Warren, 11 Oct 2026. data/references/owner-verified/luke-skywalker.md."
            current["tells"] = tells
        elif not current:
            made = figure_variant(id, factory[0], factory[1], tells)
            last = max((i for i, variant in enumerate(variants) if variant.get("figure") == "Luke Skywalker"), default=-1)
            variants.insert(last + 1, made)
    for variant in variants:
        if variant.get("figure") != "Luke Skywalker":
            continue
        variant["tells"] = [item for item in variant.get("tells") or [] if not SABRE_TELL.search(item.get("detail") or "")]
        if variant["id"] == "luke-skywalker--meccano-m1":
            for item in variant["tells"]:
                if "raised bar" in item["detail"]:
                    item["category"] = "coo"
                    item["where"] = "Look at the country stamp."
    return variants


def add_link(variant, figure_id):
    links = variant.setdefault("cardedWith", [])
    if figure_id not in links:
        links.append(figure_id)


def drop_link(variant, figure_id):
    variant["cardedWith"] = [item for item in variant.get("cardedWith") or [] if item != figure_id]


def add_tell(variant, item):
    if any(existing.get("detail") == item["detail"] for existing in variant.get("tells") or []):
        return
    variant.setdefault("tells", []).append(item)


def rename_lettered_dt(variants):
    by_id = {variant["id"]: variant for variant in variants}
    circled = by_id.get("double-telescoping-lightsaber--unitoy-m1")
    if circled and any(re.search(r"(?i)circled", item.get("detail") or "") for item in circled.get("tells") or []):
        if not any(re.search(r"(?i)lettered", item.get("detail") or "") for item in circled.get("tells") or []):
            circled["id"] = "double-telescoping-lightsaber--unitoy-circled"
            circled["mould"] = "circled"
            circled["sourceNote"] = "Unlettered circled DT. A lettered hilt is M1, so this sabre is not M1. Owner Warren, 11 Oct 2026."
            by_id = {variant["id"]: variant for variant in variants}
    renames = {
        "double-telescoping-lightsaber--kader-m2": "double-telescoping-lightsaber--kader-m1",
        "double-telescoping-lightsaber--smile-m2": "double-telescoping-lightsaber--smile-m1",
        "double-telescoping-lightsaber--unitoy-m2": "double-telescoping-lightsaber--unitoy-m1",
    }
    for old, new in renames.items():
        variant = by_id.get(old)
        if not variant:
            continue
        if new in by_id:
            raise SystemExit(f"cannot rename {old} to {new}: target already exists")
        variant["id"] = new
        variant["mould"] = "M1"
        variant["sourceNote"] = "Lettered sabres are always M1. Owner Warren, 11 Oct 2026."
        by_id[new] = variant
        by_id.pop(old, None)
    circled = by_id.get("double-telescoping-lightsaber--unitoy-circled")
    if circled:
        add_link(circled, "luke-skywalker--unitoy-m2")
        add_tell(circled, {
            "category": "cardback",
            "detail": "Circled unlettered DT, carded with the earliest Unitoy Luke",
            "where": "If it is still carded, which card is it on?",
        })
    return variants


def merge_m1(variants):
    old = [variant for variant in variants if variant["id"] in M1_OLD]
    merged = next((variant for variant in variants if variant["id"] == M1_ID), None)
    if old:
        base = old[0]
        tells = []
        seen = set()
        carded = []
        for variant in old:
            for item in variant.get("tells") or []:
                key = (item.get("category"), item.get("detail"))
                if key in seen:
                    continue
                seen.add(key)
                tells.append(item)
            for figure_id in variant.get("cardedWith") or []:
                if figure_id not in carded and not figure_id.startswith("luke-skywalker--"):
                    carded.append(figure_id)
        merged = {
            "id": M1_ID,
            "accessory": "Telescoping Lightsaber",
            "factory": "Unknown",
            "mould": "M1",
            "source": "owner",
            "sourceNote": "One M1, made by an unknown company for Kader, Unitoy, Smile and Taiwan. Owner Warren, 11 Oct 2026.",
            "sourceUrl": SABRE,
            "tells": tells,
            "cardedWith": carded,
        }
        variants = [variant for variant in variants if variant["id"] not in M1_OLD]
        variants.append(merged)
    if not merged:
        return variants
    for figure_id in LUKE_M1:
        add_link(merged, figure_id)
    add_tell(merged, {
        "category": "plastic",
        "detail": "sinks in water",
        "where": "Look at the plastic colour or shade.",
    })
    add_tell(merged, {
        "category": "mould",
        "detail": "Made by an unknown company for Kader, Unitoy, Smile and Taiwan",
        "where": "Look at the mould: shape, proportions, tip or hilt.",
    })
    add_tell(merged, {
        "category": "cardback",
        "detail": "Packed with Kader, Unitoy and Smile Luke on 12A, 12B and 12C, and with Taiwan Luke on 12A only",
        "where": "If it is still carded, which card is it on?",
    })
    merged["factory"] = "Unknown"
    merged["mould"] = "M1"
    merged["source"] = "owner"
    merged["sourceUrl"] = SABRE
    return variants


def link_sabres(variants):
    for variant in variants:
        if variant.get("accessory") != "Telescoping Lightsaber":
            continue
        mould = str(variant.get("mould") or "")
        if mould == "M2" and variant.get("factory") == "Unitoy":
            add_link(variant, "luke-skywalker--unitoy-m2")
            drop_link(variant, "luke-skywalker--smile-m4")
        if mould == "M3":
            drop_link(variant, "luke-skywalker--smile-m4")
            if variant.get("factory") == "Unitoy":
                add_link(variant, "luke-skywalker--unitoy-m2")
                add_tell(variant, {
                    "category": "cardback",
                    "detail": "Brown-hair Unitoy Luke from the 21-back, not Smile Luke",
                    "where": "If it is still carded, which card is it on?",
                })
        if mould == "M5":
            for figure_id in M5_LUKE:
                add_link(variant, figure_id)
        if mould == "M6":
            add_link(variant, "luke-skywalker--smile-no-coo")
            add_tell(variant, {
                "category": "cardback",
                "detail": "Yellow M6 carded with the No COO Smile brown-hair Luke on Trilogo cards",
                "where": "If it is still carded, which card is it on?",
            })
    return variants


def apply_factory_match(payload):
    load_owner()
    payload["figureVariants"] = upsert_figures(payload.get("figureVariants") or [])
    accessories = payload.get("accessoryVariants") or []
    accessories = rename_lettered_dt(accessories)
    accessories = merge_m1(accessories)
    accessories = link_sabres(accessories)
    payload["accessoryVariants"] = accessories
    payload["lukeOwner"] = "data/references/owner-verified/luke-skywalker.md"
    return payload


def apply_factories():
    load_owner()
    current = json.loads(FACTORIES.read_text(encoding="utf-8"))
    extra = [
        ("factory_kader_china", "Kader China", "China"),
        ("factory_meccano", "Meccano", "France"),
        ("factory_glasslite", "Glasslite", "Brazil"),
        ("factory_pbp", "PBP", "Spain"),
        ("factory_poch", "Poch", "Spain"),
        ("factory_lili_ledy", "Lili Ledy", "Mexico"),
        ("factory_takara", "Takara", "Japan"),
        ("factory_top_toys", "Top Toys", "Argentina"),
        ("factory_kenner", "Kenner", "United States"),
        ("factory_universal", "Universal Manufacturers", "Taiwan"),
    ]
    by_id = {item["id"]: item for item in current}
    for id, name, country in extra:
        by_id[id] = {"id": id, "name": name, "country": country}
    ordered = []
    seen = set()
    for item in current + [by_id[id] for id, _, _ in extra]:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        ordered.append(by_id[item["id"]])
    FACTORIES.write_text(json.dumps(ordered, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_once(path, old, new):
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"{path} is missing the line to update: {old[:80]}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


def apply_guides():
    load_owner()
    replace_once(
        "data/accessories/telescoping-lightsaber.txt",
        "- M1 – Flat transition, lettered hilt (early Kader, Unitoy, Smile, Taiwan)",
        "- M1 – Flat transition, lettered hilt, made by one unknown company for Kader, Unitoy, Smile and Taiwan. Packed with Kader, Unitoy and Smile Luke on 12A, 12B and 12C, and with Taiwan Luke on 12A only. Sinks in water.",
    )
    replace_once(
        "data/accessories/telescoping-lightsaber.txt",
        "- M3 – Flat transition, thin tip (Unitoy post 21-back, also Lili Ledy Retorno)",
        "- M3 – Flat transition, thin tip. Unitoy from the 21-back, carded with brown-hair Unitoy Luke, not Smile Luke. The mould was also used by Lili Ledy.",
    )
    replace_once(
        "data/accessories/telescoping-lightsaber.txt",
        "- M5 – Round transition, wide shaft (Kader and Smile post 12c-back, also PBP)",
        "- M5 – Round transition, wide shaft. Kader HK, Smile, PBP and Poch, plus Kader China and Meccano.",
    )
    replace_once(
        "data/accessories/telescoping-lightsaber.txt",
        "- M6 – Round transition, thin shaft (PBP)",
        "- M6 – Round transition, thin shaft (PBP). The yellow M6 was carded with the No COO Smile brown-hair Luke on Trilogo cards.",
    )
    replace_once(
        "data/accessories/double-telescoping-lightsaber.txt",
        "- An older copy of this guide called the lettered DT M2. That number is not used.",
        "- An older copy of this guide called the lettered DT M2. That number is not used. Lettered sabres are always M1.",
    )
    replace_once(
        "data/accessories/double-telescoping-lightsaber.txt",
        "- Often treated as the earliest DT type",
        "- Often treated as the earliest DT type. Carded with the earliest Unitoy Luke.",
    )
    note = (
        "\nOwner-verified COO (Warren, 11 Oct 2026):\n\n"
        "The country stamp is on the back of the left leg, under \"© G.M.F.G.I. 1977\". "
        "A partial or cut-off country name counts as No COO.\n\n"
        "Poch is the Spanish factory later renamed PBP. It made figures in Spain from older moulds "
        "received from Kader, Unitoy or Smile. Blonde Poch uses the Kader COO. Brown-hair Poch uses "
        "the Unitoy COO. A mixed figure has a Unitoy head on Kader-COO legs.\n\n"
        "Glasslite and Meccano have a blank raised bar. A No COO Luke with no bar is Smile.\n\n"
    )
    figure = ROOT / "data" / "figures" / "luke-skywalker-reference.txt"
    text = figure.read_text(encoding="utf-8")
    if "Owner-verified COO (Warren, 11 Oct 2026):" not in text:
        text = text.replace("\nRelated reference files:\n", note + "Related reference files:\n", 1)
        figure.write_text(text, encoding="utf-8")
    acc = ROOT / "data" / "variants" / "accvar_st_lightsaber_m1_yellow.json"
    data = json.loads(acc.read_text(encoding="utf-8"))
    data["notes"] = [
        "One unknown company made this M1 for Kader, Unitoy, Smile and Taiwan.",
        "Packed with Kader, Unitoy and Smile Luke on 12A, 12B and 12C, and with Taiwan Luke on 12A only.",
        "Sinks in water. Owner Warren, 11 Oct 2026.",
    ]
    if "Sinks in water" not in data.get("key_traits", []):
        data["key_traits"] = list(data.get("key_traits") or []) + ["Sinks in water"]
    acc.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def refresh_coverage(payload):
    if not COVERAGE.is_file():
        return {}
    figures = {}
    for variant in payload["figureVariants"]:
        figures.setdefault(variant["figure"], []).append(variant)
    with_tells = 0
    luke_cats = []
    for name, variants in figures.items():
        cats = []
        for variant in variants:
            for item in variant.get("tells") or []:
                if item["category"] != "coo" and item["category"] not in cats:
                    cats.append(item["category"])
        if cats:
            with_tells += 1
        if name == "Luke Skywalker":
            luke_cats = cats
    accessories = payload["accessoryVariants"]
    acc_with = sum(1 for variant in accessories if variant.get("tells"))
    acc_without = len(accessories) - acc_with
    links = sum(len(variant.get("cardedWith") or []) for variant in accessories)
    only = len(figures) - with_tells
    text = COVERAGE.read_text(encoding="utf-8")
    text = re.sub(
        r"- Figures with a tell besides the COO stamp: \d+ \(was 18/104\)",
        f"- Figures with a tell besides the COO stamp: {with_tells} (was 18/104)",
        text,
        count=1,
    )
    text = re.sub(r"- Figures with only COO data: \d+", f"- Figures with only COO data: {only}", text, count=1)
    text = re.sub(r"- Accessory variants: \d+", f"- Accessory variants: {len(accessories)}", text, count=1)
    text = re.sub(r"- Accessory variants with tells: \d+", f"- Accessory variants with tells: {acc_with}", text, count=1)
    text = re.sub(r"- Accessory variants with no tells: \d+", f"- Accessory variants with no tells: {acc_without}", text, count=1)
    text = re.sub(
        r"- Factory-match links \(accessory variant to figure variant\): \d+",
        f"- Factory-match links (accessory variant to figure variant): {links}",
        text,
        count=1,
    )
    if luke_cats:
        text = re.sub(r"- Luke Skywalker: [^\n]+", "- Luke Skywalker: " + ", ".join(luke_cats), text, count=1)
    note = " Owner-verified Luke Skywalker rulings in data/references/owner-verified/luke-skywalker.md override the scrape."
    if "owner-verified/luke-skywalker.md" not in text:
        text = text.replace("override the scrape.", "override the scrape." + note, 1)
    COVERAGE.write_text(text, encoding="utf-8")
    return {"with_tells": with_tells, "acc_with": acc_with, "links": links, "accessories": len(accessories), "luke": luke_cats}


def main():
    load_owner()
    coo = json.loads(COO.read_text(encoding="utf-8"))
    apply_coo_figures(coo["figures"])
    COO.write_text(json.dumps(coo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    luke = next(fig for fig in coo["figures"] if fig["name"] == "Luke Skywalker")
    sync_owner_stamps(luke)
    match = json.loads(MATCH.read_text(encoding="utf-8"))
    apply_factory_match(match)
    MATCH.write_text(json.dumps(match, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    apply_factories()
    apply_guides()
    stats = refresh_coverage(match)
    print("luke owner applied", stats)


if __name__ == "__main__":
    main()
