#!/usr/bin/env python3
"""Apply Warren's 17 Oct 2026 Han Solo rulings.

The rulings live in data/references/owner-verified/han-solo.md.
COO and factory-match builds call this after the Ben apply.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "data" / "references" / "owner-verified" / "han-solo.md"
COO = ROOT / "data" / "coo-figures.json"
STAMPS = ROOT / "data" / "coo-owner-stamps.json"
MATCH = ROOT / "data" / "factory-match.json"
FIGURE = ROOT / "data" / "figures" / "han-solo-reference.txt"

PAGE = "https://www.variantvillain.com/characters/sw/han-solo/"
SHEET = "https://www.variantvillain.com/wp-content/uploads/2021/12/SW_HanSolo.jpg"
BLASTER = "https://www.variantvillain.com/accessory-guide/rebel-blaster/"

REQUIRED = [
    "Date: 2026-10-17",
    "Source: owner Warren",
    "38260",
    "left leg",
    "© GMFGI 1977",
    "Not 'MADE IN'",
    "under the ©",
    "starts after the ©",
    "licensing line only",
    "PBP or Euro Kenner",
    "no known tell",
    "meltmarks",
    "not a tell",
    "Unitoy M1",
    "black M2 Jawa blaster",
    "content is not available yet",
    "Never use Mint as a grade",
]

NOTE = "Owner Warren, 17 Oct 2026. data/references/owner-verified/han-solo.md."
WHERE = (
    "Look on the left leg, under the licensing details. "
    "Family I is two lines, '© GMFGI 1977' and 'HONG KONG', not 'MADE IN'. "
    "Kader family II 1a has the H of HONG KONG under the ©. "
    "Kader family II 1b has the H starting after the ©. "
    "Glasslite, the Kader with no country, and family III are the licensing line only. "
    "The picture is the Variant Villain COO sheet."
)
EXPLANATION = (
    "The country of origin (COO) stamp on this Han Solo is on the left leg, under the licensing details. "
    "Family I is two lines, '© GMFGI 1977' and 'HONG KONG', not 'MADE IN'. "
    "Glasslite, the Kader with no country, and family III are one line, the licensing line only. "
    "A partial or cut-off country name counts as No COO."
)
HK = (
    "Two lines on the left leg, under the licensing details: '© GMFGI 1977' and 'HONG KONG'. Not 'MADE IN'"
)
LINE = "Only the licensing line on the left leg: '© GMFGI 1977', with no country"
FAM_I = "It matches family I on the sheet"
H_UNDER = "The H of HONG KONG is under the ©"
H_AFTER = "The H of HONG KONG starts after the ©"
GLASS = "It matches Glasslite, family II 2a, on the sheet"
KADER_NC = "It matches the Kader with no country, family II 2b, on the sheet"
PBP = "It matches family III on the sheet"
HK_LOOK = (
    "That two-line stamp is '© GMFGI 1977' and 'HONG KONG', not 'MADE IN'. "
    "Family I on the sheet is Unitoy. On Kader family II, 1a has the H of HONG KONG under the ©, "
    "and 1b has the H starting after the ©.\n\nWhich of these is it?"
)
LINE_LOOK = (
    "That licensing line is shared by Glasslite, the Kader with no country, and family III. "
    "The stamp does not separate them. Match the figure to the COO sheet. "
    "Family III is PBP or Euro Kenner. There is no known tell between those two. "
    "Both can have different meltmarks, and that is not a tell.\n\nWhich of these is it?"
)

KADER_IDS = [
    "han-solo--kader-ii-1a",
    "han-solo--kader-ii-1b",
    "han-solo--kader-ii-no-coo",
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


def photo(url, alt):
    return {
        "url": url,
        "alt": alt,
        "sourcePage": PAGE,
        "credit": "Photo: Variant Villain",
    }


def follow(fid, label, factories, conclusion):
    return {"id": fid, "label": label, "factories": factories, "conclusion": conclusion, "sure": True}


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


def sheet():
    return photo(SHEET, "Han Solo COO sheet")


def han_options():
    picture = [sheet()]
    return [
        option(
            "hk-left",
            HK,
            "Hong Kong",
            ["Unitoy I", "Kader II 1a", "Kader II 1b"],
            "",
            False,
            [
                follow(
                    "unitoy-i",
                    FAM_I,
                    ["Unitoy I"],
                    "That is the Unitoy, family I. Two lines, '© GMFGI 1977' and 'HONG KONG', not 'MADE IN'. "
                    "Rebel Blaster M3, then M2.",
                ),
                follow(
                    "kader-1a",
                    H_UNDER,
                    ["Kader II 1a"],
                    "That is the Kader, family II 1a. The H of HONG KONG is under the ©. Rebel Blaster M4, then M5.",
                ),
                follow(
                    "kader-1b",
                    H_AFTER,
                    ["Kader II 1b"],
                    "That is the Kader, family II 1b. The H of HONG KONG starts after the ©. Rebel Blaster M4, then M5.",
                ),
            ],
            picture,
            HK_LOOK,
        ),
        option(
            "licensing-line",
            LINE,
            "No COO",
            ["Glasslite", "Kader II No COO", "PBP or Euro Kenner"],
            "",
            False,
            [
                follow(
                    "glasslite",
                    GLASS,
                    ["Glasslite"],
                    "That is the Glasslite, family II 2a. The licensing line is the only marking. "
                    "The blaster is the black M2 Jawa blaster, not a Rebel Blaster.",
                ),
                follow(
                    "kader-no-coo",
                    KADER_NC,
                    ["Kader II No COO"],
                    "That is the Kader with no country, family II 2b. The licensing line is the only marking. "
                    "Rebel Blaster M4, then M5.",
                ),
                follow(
                    "pbp-euro",
                    PBP,
                    ["PBP or Euro Kenner"],
                    "That is PBP or Euro Kenner, family III. The licensing line is the only marking. "
                    "There is no known tell between them. Both can have different meltmarks, and that is not a tell. "
                    "Rebel Blaster M5 is the PBP blaster.",
                ),
            ],
            picture,
            LINE_LOOK,
        ),
    ]


def han_stamps():
    return [
        "Unitoy family I = two lines on the left leg: '© GMFGI 1977' and 'HONG KONG'. Not 'MADE IN'.",
        "Kader family II 1a = the H of HONG KONG is under the ©.",
        "Kader family II 1b = the H of HONG KONG starts after the ©.",
        "Glasslite family II 2a = the licensing line only.",
        "Kader family II 2b = the licensing line only. No country.",
        "Family III = the licensing line only. PBP or Euro Kenner. No known tell. Different meltmarks are not a tell.",
    ]


def apply_coo_figures(figures):
    load_owner()
    record = next((fig for fig in figures if fig.get("name") == "Han Solo"), None)
    if not record:
        raise SystemExit("Han Solo is not in coo-figures")
    record["whereToLook"] = WHERE
    record["cooExplanation"] = EXPLANATION
    record["ask"] = "Which stamp do you see?"
    record["source"] = "owner"
    record["sourceNote"] = NOTE
    record["verified"] = True
    record["hasDetails"] = True
    record["options"] = han_options()
    record["ownerStamps"] = han_stamps()
    record["stamps"] = han_stamps()
    record["missing"] = ""
    record["tells"] = []
    record["guide"] = [
        "I: Unitoy",
        "II: Kader/ Glasslite",
        "III: PBP/ Euro Kenner",
    ]
    record["families"] = [
        {"title": "COO Family I:", "lines": ["Unitoy", "Two lines, '© GMFGI 1977' and 'HONG KONG'. Not 'MADE IN'."]},
        {"title": "COO Family II:", "lines": ["Kader / Glasslite", "1a: the H of HONG KONG is under the ©. 1b: the H starts after the ©. 2a Glasslite and 2b Kader No COO are the licensing line only."]},
        {"title": "COO Family III:", "lines": ["PBP / Euro Kenner", "The licensing line only. No known tell. Different meltmarks are not a tell."]},
    ]
    record["referenceImage"] = sheet()
    record["sourceUrl"] = PAGE
    return figures


def sync_owner_stamps(record):
    owner = json.loads(STAMPS.read_text(encoding="utf-8"))
    entry = {
        "name": "Han Solo",
        "recorded": "2026-10-17",
        "source": "owner",
        "whereToLook": record["whereToLook"],
        "ask": record["ask"],
        "stamps": record["ownerStamps"],
        "options": record["options"],
        "referenceImage": record["referenceImage"],
        "missing": "",
    }
    figures = owner.get("figures") or []
    owner["figures"] = [fig for fig in figures if fig.get("name") != "Han Solo"] + [entry]
    owner["hanNote"] = (
        "Han Solo stamps follow data/references/owner-verified/han-solo.md (owner Warren, 2026-10-17)."
    )
    STAMPS.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def coo(detail):
    return {"category": "coo", "detail": detail, "where": "Look at the country stamp on the left leg."}


def variant(vid, factory, mould_name, detail):
    return {
        "id": vid,
        "figure": "Han Solo",
        "factory": factory,
        "mould": mould_name,
        "source": "owner",
        "sourceUrl": PAGE,
        "sourceNote": NOTE,
        "tells": [coo(detail)],
    }


def han_variants():
    return [
        variant("han-solo--unitoy-i", "Unitoy I", "I", f"{HK}. Family I."),
        variant("han-solo--kader-ii-1a", "Kader II 1a", "II", f"{HK}. The H of HONG KONG is under the ©."),
        variant("han-solo--kader-ii-1b", "Kader II 1b", "II", f"{HK}. The H of HONG KONG starts after the ©."),
        variant("han-solo--glasslite", "Glasslite", "II", f"{LINE}. Family II 2a. The blaster is the black M2 Jawa blaster."),
        variant("han-solo--kader-ii-no-coo", "Kader II No COO", "II", f"{LINE}. Family II 2b."),
        variant(
            "han-solo--pbp-euro",
            "PBP or Euro Kenner",
            "III",
            f"{LINE}. Family III. No known tell between PBP and Euro Kenner. Different meltmarks are not a tell.",
        ),
    ]


LINKS = {
    "rebel-blaster--unitoy-m3": ["han-solo--unitoy-i"],
    "rebel-blaster--unitoy-m2": ["han-solo--unitoy-i"],
    "rebel-blaster--kader-m4": KADER_IDS,
    "rebel-blaster--kader-m5": KADER_IDS,
    "rebel-blaster--pbp-m5": ["han-solo--pbp-euro"],
    "jawa-blaster--glasslite-m2": ["han-solo--glasslite"],
}


def apply_carded(payload):
    for row in payload.get("accessoryVariants") or []:
        extra = LINKS.get(row.get("id"))
        if extra is None:
            continue
        current = list(row.get("cardedWith") or [])
        others = [item for item in current if not str(item).startswith("han-solo--")]
        row["cardedWith"] = others + [item for item in extra if item not in others]
        if row.get("id") == "jawa-blaster--glasslite-m2":
            row["sourceNote"] = NOTE + " The Glasslite Han uses the black M2 Jawa blaster."
        else:
            row["sourceNote"] = NOTE


def apply_factory_match(payload):
    load_owner()
    fresh = han_variants()
    out = []
    inserted = False
    for row in payload.get("figureVariants") or []:
        if row.get("figure") == "Han Solo":
            if not inserted:
                out.extend(fresh)
                inserted = True
            continue
        out.append(row)
    if not inserted:
        out.extend(fresh)
    payload["figureVariants"] = out
    apply_carded(payload)
    payload["hanOwner"] = "data/references/owner-verified/han-solo.md"
    return payload


def apply_guides():
    load_owner()
    raw = FIGURE.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")
    old_moulds = (
        "M1 – Early Kenner production  \n"
        "M2 – Unitoy  \n"
        "M3 – Smile  \n"
        "M4 – Kader  \n"
        "M5 – Taiwan  \n"
    )
    new_moulds = (
        "Unitoy family I: Rebel Blaster M3, then M2.\n"
        "Kader family II: Rebel Blaster M4, then M5. That includes the Kader with no country.\n"
        "PBP, family III: Rebel Blaster M5. Euro Kenner is the same figure result, not its own blaster.\n"
        "Glasslite: black M2 Jawa blaster. Not a Rebel Blaster.\n"
    )
    if old_moulds in text:
        text = text.replace(old_moulds, new_moulds, 1)
    old_families = (
        "COO Family 1: Unitoy  \n"
        "COO Family 2: Kader / Glasslite  \n"
        "COO Family 3: PBP  \n"
    )
    new_families = (
        "Family I: Unitoy. Two lines, '© GMFGI 1977' and 'HONG KONG'. Not 'MADE IN'.\n"
        "Family II: Kader and Glasslite. 1a, the H of HONG KONG is under the ©. 1b, the H starts after the ©. "
        "2a Glasslite and 2b Kader No COO are the licensing line only.\n"
        "Family III: PBP or Euro Kenner. The licensing line only. No known tell. Different meltmarks are not a tell.\n"
        "The old names Unitoy M1, Kader M2, Glasslite M2 and PBP M3 are retired. M numbers are blaster moulds.\n"
    )
    if old_families in text:
        text = text.replace(old_families, new_families, 1)
    text = text.replace(
        "- Solid black Jawa blaster (NOT Rebel blaster)",
        "- Solid black M2 Jawa blaster (NOT a Rebel Blaster). Warren confirmed this on 17 Oct 2026.",
    )
    text = text.replace(
        "- Typically Rebel blaster variants (M4 / M5 style)",
        "- Rebel Blaster M5. Euro Kenner shares this family and is not a separate blaster.",
    )
    FIGURE.write_bytes(text.replace("\n", newline).encode("utf-8"))


def main():
    load_owner()
    coo = json.loads(COO.read_text(encoding="utf-8"))
    apply_coo_figures(coo["figures"])
    COO.write_text(json.dumps(coo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    record = next(fig for fig in coo["figures"] if fig["name"] == "Han Solo")
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
    print("han owner applied")


if __name__ == "__main__":
    main()
