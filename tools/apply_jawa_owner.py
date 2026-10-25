#!/usr/bin/env python3
"""Apply Warren's 25 Oct 2026 Jawa rulings.

The rulings live in data/references/owner-verified/jawa.md.
COO and factory-match builds call this after the Han apply.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "data" / "references" / "owner-verified" / "jawa.md"
COO = ROOT / "data" / "coo-figures.json"
STAMPS = ROOT / "data" / "coo-owner-stamps.json"
MATCH = ROOT / "data" / "factory-match.json"
FIGURE = ROOT / "data" / "figures" / "jawa-reference.txt"

PAGE = "https://www.variantvillain.com/characters/sw/jawa/"
SHEET = "https://www.variantvillain.com/wp-content/uploads/2023/10/Jawa-COO-Sheet-3.3.jpg"
FAMILY_II = "https://www.variantvillain.com/wp-content/uploads/2025/09/F2-Kader.jpg"

REQUIRED = [
    "Date: 2026-10-25",
    "Source: owner Warren",
    "38270",
    "left leg",
    "Not the lower robe",
    "© G.M.F.G.I. 1977",
    "Not 'Made in China'",
    "under the ©",
    "under the first G",
    "licensing line only",
    "sits higher",
    "sits lower",
    "0.1%",
    "no stamp of its own",
    "green",
    "Jawa Blaster M2",
    "Jawa Blaster M3",
    "Jawa Blaster M1",
    "Pilot Blaster M6",
    "Vinyl Cape M2",
    "Cloak M2",
    "Never use Mint as a grade",
]

NOTE = "Owner Warren, 25 Oct 2026. data/references/owner-verified/jawa.md."
WHERE = (
    "Look on the left leg. Not the lower robe. "
    "Every stamp but Kader China is two lines, '© G.M.F.G.I. 1977' and 'HONG KONG'. "
    "Kader China, family II 2, is one licensing line and no country. "
    "The picture is the Variant Villain COO sheet."
)
EXPLANATION = (
    "The country of origin (COO) stamp on this Jawa is on the left leg, not the lower robe. "
    "Every factory but Kader China is two lines, '© G.M.F.G.I. 1977' and 'HONG KONG'. "
    "Kader China is one licensing line and no country. Not 'Made in China'. "
    "A partial or cut-off country name counts as No COO. "
    "A cloth cape or no cape is the first question. A vinyl cape is extremely rare, about 0.1%, "
    "so it is not the split to start with."
)
CAPE_ASK = "Cloth cape, or no cape? A vinyl cape is the rare case, not the usual split."
HK = "Two lines on the left leg: '© G.M.F.G.I. 1977' and 'HONG KONG'"
LINE = "Only the licensing line on the left leg: '© G.M.F.G.I. 1977', with no country"
FAM_I = "It matches family I on the sheet"
FAM_II = "It matches family II on the sheet"
H_UNDER = "The H of HONG KONG is under the ©"
H_AFTER = "The H of HONG KONG starts after the ©"
GREEN = "The plastic is green"
UNITOY = "It matches family III or IV on the sheet"
LILI = "It matches the Lili Ledy on the sheet"
POCH = "It matches the Poch on the sheet"
HIGH = "The stamp sits higher on the leg"
LOW = "The stamp sits lower on the leg"
HK_LOOK = (
    "That two-line stamp is '© G.M.F.G.I. 1977' and 'HONG KONG', on the left leg. "
    "Family I is Kader. Family II is Kader Hong Kong, and the photo separates 1a from 1b. "
    "Toltoys is the same stamp on green plastic. Family III and IV are Unitoy. "
    "Lili Ledy and Poch have no stamp of their own.\n\nWhich of these is it?"
)
II_LOOK = (
    "Family II is Kader Hong Kong. Check the photo. "
    "1a has the H of HONG KONG under the ©. "
    "1b has the H starting after the ©, under the first G.\n\nWhich of these is it?"
)
LINE_LOOK = (
    "That is Kader China, family II 2. One licensing line, and no country. Not 'Made in China'. "
    "Check the photo. 2a sits higher on the leg. 2b sits lower.\n\nWhich of these is it?"
)


def load_owner():
    if not OWNER.is_file():
        raise SystemExit(f"missing owner record {OWNER}")
    text = OWNER.read_text(encoding="utf-8")
    folded = text.casefold()
    missing = [phrase for phrase in REQUIRED if phrase.casefold() not in folded]
    if missing:
        raise SystemExit("owner record is missing rulings: " + "; ".join(missing))
    return text


def sheet():
    return {
        "url": SHEET,
        "alt": "Jawa COO sheet",
        "sourcePage": PAGE,
        "credit": "Photo: Variant Villain",
    }


def vv_photo(url, alt, caption):
    # The chat paints alt as the caption when sourcePage is set.
    return {
        "url": url,
        "alt": caption,
        "title": alt,
        "caption": caption,
        "credit": "Photo: Variant Villain",
        "sourcePage": PAGE,
    }


def follow(fid, label, factories, conclusion, follow_ups=None, compare_images=None, compare_reply=""):
    row = {
        "id": fid,
        "label": label,
        "factories": factories,
        "conclusion": conclusion,
        "sure": not follow_ups,
    }
    if follow_ups:
        row["followUps"] = follow_ups
        row["sure"] = False
        row["factories"] = []
    if compare_images:
        row["compareImages"] = compare_images
    if compare_reply:
        row["compareReply"] = compare_reply
    return row


def option(fid, label, coo, factories, conclusion, sure, follow_ups=None, compare_images=None, compare_reply=""):
    row = {
        "id": fid,
        "label": label,
        "coo": coo,
        "factories": factories,
        "examples": [label],
        "conclusion": conclusion,
        "sure": sure,
        "followUps": follow_ups or [],
    }
    if compare_images:
        row["compareImages"] = compare_images
    if compare_reply:
        row["compareReply"] = compare_reply
    return row


def jawa_options():
    hk_photo = [vv_photo(
        FAMILY_II,
        "Kader family II, 1a and 1b",
        "Family II on the Variant Villain sheet. 1a: the H of HONG KONG is under the ©. 1b: the H starts after the ©, under the first G.",
    )]
    china_photo = [vv_photo(
        FAMILY_II,
        "Kader China family II, 2a and 2b",
        "Kader China on the Variant Villain family II sheet. 2a sits higher on the leg. 2b sits lower. Both are one licensing line and no country.",
    )]
    family_ii = follow(
        "kader-ii",
        FAM_II,
        [],
        "",
        [
            follow(
                "kader-1a",
                H_UNDER,
                ["Kader II 1a"],
                "That is the Kader, family II 1a. The H of HONG KONG is under the ©. Jawa Blaster M3.",
            ),
            follow(
                "kader-1b",
                H_AFTER,
                ["Kader II 1b"],
                "That is the Kader, family II 1b. The H of HONG KONG starts after the ©, under the first G. Jawa Blaster M3.",
            ),
        ],
        hk_photo,
        II_LOOK,
    )
    return [
        option(
            "hk-left",
            HK,
            "Hong Kong",
            ["Kader I", "Kader II 1a", "Kader II 1b", "Toltoys", "Unitoy", "Lili Ledy", "Poch"],
            "",
            False,
            [
                follow(
                    "kader-i",
                    FAM_I,
                    ["Kader I"],
                    "That is the Kader, family I. Two lines on the left leg. Vinyl cape on the 12a card, cloth by the 12c card. Jawa Blaster M2.",
                ),
                family_ii,
                follow(
                    "toltoys",
                    GREEN,
                    ["Toltoys"],
                    "That is the Toltoys. Kader Hong Kong tooling, and the plastic is green. The stamp is the same two lines. Bluish Jawa Blaster M3 and Vinyl Cape M2.",
                ),
                follow(
                    "unitoy",
                    UNITOY,
                    ["Unitoy"],
                    "That is the Unitoy, family III or IV. Two lines on the left leg. There is no separate stamp for III and IV. Jawa Blaster M1.",
                ),
                follow(
                    "lili-ledy",
                    LILI,
                    ["Lili Ledy"],
                    "That is the Lili Ledy. Family IV tooling, and no stamp of its own. Pilot Blaster M6.",
                ),
                follow(
                    "poch",
                    POCH,
                    ["Poch"],
                    "That is the Poch. Mixed Kader and Unitoy parts, and no stamp of its own. Jawa Blaster M1.",
                ),
            ],
            [sheet()],
            HK_LOOK,
        ),
        option(
            "licensing-line",
            LINE,
            "No COO",
            ["Kader China II 2a", "Kader China II 2b"],
            "",
            False,
            [
                follow(
                    "china-2a",
                    HIGH,
                    ["Kader China II 2a"],
                    "That is the Kader China, family II 2a. One licensing line, no country. The stamp sits higher on the leg. Jawa Blaster M2 and Cloak M2.",
                ),
                follow(
                    "china-2b",
                    LOW,
                    ["Kader China II 2b"],
                    "That is the Kader China, family II 2b. One licensing line, no country. The stamp sits lower on the leg. Jawa Blaster M2 and Cloak M2.",
                ),
            ],
            china_photo,
            LINE_LOOK,
        ),
    ]


def jawa_stamps():
    return [
        "Family I Kader = two lines on the left leg: '© G.M.F.G.I. 1977' and 'HONG KONG'. Vinyl on 12a, cloth by 12c.",
        "Family II 1a Kader = the H of HONG KONG is under the ©.",
        "Family II 1b Kader = the H of HONG KONG starts after the ©, under the first G.",
        "Family II 2a Kader China = the licensing line only, no country. The stamp sits higher on the leg.",
        "Family II 2b Kader China = the licensing line only, no country. The stamp sits lower on the leg.",
        "Toltoys = the same two lines, on green plastic. Kader Hong Kong tooling.",
        "Family III and IV Unitoy = the same two lines. No separate stamp.",
        "Lili Ledy = Family IV tooling. No stamp of its own.",
        "Poch = mixed Kader and Unitoy parts. No stamp of its own.",
    ]


def apply_coo_figures(figures):
    load_owner()
    record = next((fig for fig in figures if fig.get("name") == "Jawa"), None)
    if not record:
        raise SystemExit("Jawa is not in coo-figures")
    record["whereToLook"] = WHERE
    record["cooExplanation"] = EXPLANATION
    record["ask"] = "Which stamp do you see?"
    record["source"] = "owner"
    record["sourceNote"] = NOTE
    record["verified"] = True
    record["hasDetails"] = True
    record["options"] = jawa_options()
    record["ownerStamps"] = jawa_stamps()
    record["stamps"] = jawa_stamps()
    record["missing"] = ""
    record["tells"] = []
    record["error"] = ""
    record["guide"] = [
        "I: Kader Hong Kong",
        "II: Kader Hong Kong 1a/1b, Kader China 2a/2b",
        "III/IV: Unitoy Hong Kong",
    ]
    record["families"] = [
        {"title": "COO Family I:", "lines": ["Kader Hong Kong", "Two lines on the left leg. Vinyl cape on 12a, cloth by 12c. Jawa Blaster M2."]},
        {"title": "COO Family II:", "lines": ["Kader Hong Kong and Kader China", "1a: the H of HONG KONG is under the ©. 1b: the H starts after the ©, under the first G. 2a and 2b are the licensing line only. 2a sits higher. 2b sits lower."]},
        {"title": "COO Family III and IV:", "lines": ["Unitoy Hong Kong", "The same two lines. No separate stamp. Jawa Blaster M1. Lili Ledy uses Family IV tooling and has no stamp of its own."]},
    ]
    record["capeFirst"] = {
        "ask": CAPE_ASK,
        "choices": [
            {"id": "cloth", "label": "Cloth cape", "note": "Cloth cape. The stamp is next, on the left leg."},
            {"id": "none", "label": "No cape", "note": "No cape. The stamp is still on the left leg."},
            {"id": "vinyl", "label": "Vinyl cape, extremely rare", "note": "A vinyl cape is extremely rare, about 0.1%. It is not a factory by itself. The stamp is still the check."},
        ],
    }
    record["referenceImage"] = sheet()
    record["sourceUrl"] = PAGE
    return figures


def sync_owner_stamps(record):
    owner = json.loads(STAMPS.read_text(encoding="utf-8"))
    entry = {
        "name": "Jawa",
        "recorded": "2026-10-25",
        "source": "owner",
        "whereToLook": record["whereToLook"],
        "ask": record["ask"],
        "stamps": record["ownerStamps"],
        "options": record["options"],
        "referenceImage": record["referenceImage"],
        "capeFirst": record["capeFirst"],
        "missing": "",
    }
    figures = owner.get("figures") or []
    owner["figures"] = [fig for fig in figures if fig.get("name") != "Jawa"] + [entry]
    owner["jawaNote"] = "Jawa stamps follow data/references/owner-verified/jawa.md (owner Warren, 2026-10-25)."
    STAMPS.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def coo(detail):
    return {"category": "coo", "detail": detail, "where": "Look at the country stamp on the left leg."}


def variant(vid, factory, mould_name, detail):
    return {
        "id": vid,
        "figure": "Jawa",
        "factory": factory,
        "mould": mould_name,
        "source": "owner",
        "sourceUrl": PAGE,
        "sourceNote": NOTE,
        "tells": [coo(detail)],
    }


def jawa_variants():
    return [
        variant("jawa--kader-i", "Kader I", "I", f"{HK}. Family I. Vinyl cape on 12a, cloth by 12c."),
        variant("jawa--kader-ii-1a", "Kader II 1a", "II", f"{HK}. The H of HONG KONG is under the ©."),
        variant("jawa--kader-ii-1b", "Kader II 1b", "II", f"{HK}. The H of HONG KONG starts after the ©, under the first G."),
        variant("jawa--kader-china-2a", "Kader China II 2a", "II", f"{LINE}. Family II 2a. The stamp sits higher on the leg."),
        variant("jawa--kader-china-2b", "Kader China II 2b", "II", f"{LINE}. Family II 2b. The stamp sits lower on the leg."),
        variant("jawa--toltoys", "Toltoys", "Toltoys", f"{HK}. Green plastic. Kader Hong Kong tooling."),
        variant("jawa--unitoy", "Unitoy", "III/IV", f"{HK}. Family III or IV. No separate stamp."),
        variant("jawa--lili-ledy", "Lili Ledy", "IV", f"{HK}. Family IV tooling. No stamp of its own."),
        variant("jawa--poch", "Poch", "Poch", f"{HK}. Mixed Kader and Unitoy parts. No stamp of its own."),
    ]


LINKS = {
    "jawa-blaster--kader-m2": ["jawa--kader-i"],
    "jawa-blaster--kader-m3": ["jawa--kader-ii-1a", "jawa--kader-ii-1b", "jawa--toltoys"],
    "jawa-blaster--kader-china-m2": ["jawa--kader-china-2a", "jawa--kader-china-2b"],
    "jawa-cloak--kader-china-m2": ["jawa--kader-china-2a", "jawa--kader-china-2b"],
    "jawa-vinyl-cape--kader-m2": ["jawa--toltoys"],
    "jawa-blaster--unitoy-m1": ["jawa--unitoy", "jawa--poch"],
    "pilot-blaster--lili-ledy-m6": ["jawa--lili-ledy"],
}


def apply_carded(payload):
    for row in payload.get("accessoryVariants") or []:
        extra = LINKS.get(row.get("id"))
        if extra is None:
            continue
        current = list(row.get("cardedWith") or [])
        others = [item for item in current if not str(item).startswith("jawa--")]
        row["cardedWith"] = others + [item for item in extra if item not in others]
        row["sourceNote"] = NOTE
    glass = next((row for row in payload.get("accessoryVariants") or [] if row.get("id") == "jawa-blaster--glasslite-m2"), None)
    if glass is None:
        raise SystemExit("glasslite Jawa blaster M2 is missing")
    carded = list(glass.get("cardedWith") or [])
    if "han-solo--glasslite" not in carded:
        carded.append("han-solo--glasslite")
        glass["cardedWith"] = carded


def apply_factory_match(payload):
    load_owner()
    fresh = jawa_variants()
    out = []
    inserted = False
    for row in payload.get("figureVariants") or []:
        if row.get("figure") == "Jawa":
            if not inserted:
                out.extend(fresh)
                inserted = True
            continue
        out.append(row)
    if not inserted:
        out.extend(fresh)
    payload["figureVariants"] = out
    apply_carded(payload)
    payload["jawaOwner"] = "data/references/owner-verified/jawa.md"
    return payload


def apply_guides():
    load_owner()
    raw = FIGURE.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")
    swaps = [
        (
            "The Jawa is one of the earliest figures in the vintage Star Wars line and is best known for its distinctive body covering and early production vinyl cape variant.",
            "The Jawa is one of the earliest figures in the vintage Star Wars line. Ask cloth cape or no cape first. A vinyl cape is extremely rare, about 0.1%.",
        ),
        (
            "The body covering is the most obvious first visual difference.",
            "Ask cloth cape or no cape first. A vinyl cape is extremely rare, about 0.1%, so it is not the split to start with.",
        ),
        (
            "1. COO (Country of Origin) on the figure\n2. Cloak or cape type\n",
            "1. Cloth cape, or no cape\n2. COO (Country of Origin) on the left leg\n",
        ),
    ]
    for old_bit, new_bit in swaps:
        if old_bit in text:
            text = text.replace(old_bit, new_bit, 1)
        elif new_bit not in text:
            raise SystemExit("jawa reference is missing a block to replace")
    old = (
        "COO (Country of Origin):\n\n"
        "Jawa figures exist with multiple COO markings, including:\n"
        "- Hong Kong\n"
        "- Taiwan\n"
        "- No COO (in some cases)\n\n"
        "COO is one of the most important advanced identifiers because it helps narrow:\n"
        "- production period\n"
        "- factory family\n"
        "- likely correct accessory pairing\n"
    )
    new = (
        "COO (Country of Origin):\n\n"
        "The stamp is on the left leg, not the lower robe. Warren confirmed this on 25 Oct 2026.\n\n"
        "Every stamp is two lines, '© G.M.F.G.I. 1977' and 'HONG KONG', except Kader China. "
        "Kader China, family II 2, is one licensing line and no country. Not 'Made in China'.\n\n"
        "Family I, Kader Hong Kong: vinyl cape on the 12a card, cloth by the 12c card. Jawa Blaster M2.\n"
        "Family II 1a: the H of HONG KONG is under the ©. Family II 1b: the H starts after the ©, under the first G. Jawa Blaster M3.\n"
        "Family II 2a sits higher on the leg. Family II 2b sits lower. Both are Kader China. Jawa Blaster M2 and Cloak M2.\n"
        "Toltoys uses Kader Hong Kong tooling. The plastic is green. Bluish Jawa Blaster M3 and Vinyl Cape M2.\n"
        "Family III and IV are Unitoy. No separate stamp. Jawa Blaster M1.\n"
        "Lili Ledy uses Family IV tooling and has no stamp of its own. Pilot Blaster M6.\n"
        "Poch uses mixed Kader and Unitoy parts and has no stamp of its own. Jawa Blaster M1.\n"
    )
    if old in text:
        text = text.replace(old, new, 1)
    elif "The stamp is on the left leg, not the lower robe." not in text:
        raise SystemExit("jawa reference COO block was not found")
    FIGURE.write_bytes(text.replace("\n", newline).encode("utf-8"))


def main():
    load_owner()
    coo = json.loads(COO.read_text(encoding="utf-8"))
    apply_coo_figures(coo["figures"])
    COO.write_text(json.dumps(coo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    record = next(fig for fig in coo["figures"] if fig["name"] == "Jawa")
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
    print("jawa owner applied")


if __name__ == "__main__":
    main()
