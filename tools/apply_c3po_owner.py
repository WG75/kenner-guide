#!/usr/bin/env python3
"""Apply Warren's 11 Oct 2026 C-3PO rulings.

The rulings live in data/references/owner-verified/c-3po.md.
COO and factory-match builds call this after the Chewbacca apply, so a
regeneration keeps the rulings. Running this file applies them to the data on disk.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "data" / "references" / "owner-verified" / "c-3po.md"
COO = ROOT / "data" / "coo-figures.json"
STAMPS = ROOT / "data" / "coo-owner-stamps.json"
MATCH = ROOT / "data" / "factory-match.json"
FIGURE = ROOT / "data" / "figures" / "c-3po-reference.txt"

REQUIRED = [
    "Date: 2026-10-11",
    "Source: owner Warren",
    "back of the left thigh",
    "not on the shin",
    "not near the foot",
    "three side-by-side columns",
    "just to the right of the ©",
    "1977' is level with the ©",
    "two side-by-side columns",
    "Do not invent a letter tell",
    "H of HONG starts under the middle of the ©",
    "similar to M3",
    "© G.M.F.G.I. 1977",
    "© G.M.F.G.I. 1978",
    "JAPAN is reversed",
    "no PBP C-3PO",
    "PBP is Spain",
    "Lili Ledy is Mexico",
    "No C-3PO is stamped Mexico",
    "dent or a hole beside the stamp",
    "dull gold, shiny gold, or silver",
    "bronze-sprayed",
    "fat head",
    "Never use Mint as a grade",
    "partial or cut-off country name counts as No COO",
]

NOTE = "Owner Warren, 11 Oct 2026. data/references/owner-verified/c-3po.md."
WHERE = (
    "Look on the back of the left thigh, not the shin and not near the foot. "
    "The stamp runs vertically in side-by-side columns. "
    "A partial or cut-off country name counts as No COO. The picture is COO guide 3.1."
)
EXPLANATION = (
    "The country of origin (COO) stamp on this C-3PO is on the back of the left thigh, "
    "not the shin and not near the foot. It runs vertically in side-by-side columns. "
    "A partial or cut-off country name counts as No COO."
)
THREE = (
    "Three side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I.', '1977', and 'HONG KONG'"
)
TWO = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I. 1977' and 'HONG KONG'"
)
TAKARA = (
    "Two side-by-side columns on the back of the left thigh: "
    "'© G.M.F.G.I. 1978' and 'JAPAN'"
)
M1_POS = "'1977' starts on the second column, just to the right of the ©"
M2_UNITOY = "'1977' is level with the ©, and there is no dent or hole beside the stamp"
M2_LL = (
    "'1977' is level with the ©, with a dent or a hole beside the stamp, "
    "or a dull gold, shiny gold or silver finish"
)
M5_POS = "The H of HONG starts under the middle of the ©"
LL_REG = (
    "A dent or a hole beside the stamp, or dull gold, shiny gold or silver, "
    "or a bronze-sprayed seat"
)
M3_GUIDE = "It matches family III on the guide, with no dent or hole beside the stamp"
M4_GUIDE = "It matches family IV on the guide"
M7_GUIDE = "It matches family VII on the guide"
THIGH = "The stamp is on the back of the left thigh, not the shin and not near the foot."


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


def c3po_options():
    return [
        option(
            "three-columns",
            THREE,
            "Hong Kong",
            ["Kader M1", "Unitoy M2", "Lili Ledy M2"],
            "",
            False,
            [
                follow(
                    "kader-m1-1977",
                    M1_POS,
                    ["Kader M1"],
                    "That is the Kader M1. Three side-by-side columns on the back of the left thigh. "
                    "1977 starts on the second column, just to the right of the ©.",
                ),
                follow(
                    "unitoy-m2-level",
                    M2_UNITOY,
                    ["Unitoy M2"],
                    "That is the Unitoy M2. Three side-by-side columns, and 1977 is level with the ©. "
                    "There is no dent or hole beside the stamp.",
                ),
                follow(
                    "ll-retorno",
                    M2_LL,
                    ["Lili Ledy M2"],
                    "That is the Lili Ledy Retorno (M2). 1977 is level with the ©. "
                    "A dent or a hole beside the stamp, and a dull gold, shiny gold or silver finish, "
                    "are Lili Ledy tells. The seat is bronze-sprayed. A fat head is a Removable Limbs head "
                    "mixed onto this body. There is no PBP C-3PO.",
                ),
            ],
        ),
        option(
            "two-columns",
            TWO,
            "Hong Kong",
            ["Kader M3", "Lili Ledy M3", "Unitoy M4", "Kader M5", "Unitoy M7"],
            "",
            False,
            [
                follow(
                    "kader-m5-h",
                    M5_POS,
                    ["Kader M5"],
                    "That is the Kader M5. Two side-by-side columns on the back of the left thigh. "
                    "The H of HONG starts under the middle of the ©.",
                ),
                follow(
                    "ll-regreso",
                    LL_REG,
                    ["Lili Ledy M3"],
                    "That is the Lili Ledy Regreso (M3). Two side-by-side columns. "
                    "A dent or a hole beside the stamp, dull gold, shiny gold or silver, "
                    "and a bronze-sprayed seat are Lili Ledy tells. "
                    "A fat head is a Removable Limbs head mixed onto this body. There is no PBP C-3PO.",
                ),
                follow(
                    "kader-m3-guide",
                    M3_GUIDE,
                    ["Kader M3"],
                    "That is the Kader M3. Two side-by-side columns. The alignment is similar to Unitoy M4 "
                    "and Unitoy M7, so match it to family III on COO guide 3.1. There is no separate letter tell.",
                ),
                follow(
                    "unitoy-m4-guide",
                    M4_GUIDE,
                    ["Unitoy M4"],
                    "That is the Unitoy M4. The stamp is on the back of the left thigh, and the alignment "
                    "is similar to Kader M3. Match it to family IV on COO guide 3.1.",
                ),
                follow(
                    "unitoy-m7-guide",
                    M7_GUIDE,
                    ["Unitoy M7"],
                    "That is the Unitoy M7. The stamp is on the back of the left thigh, and the alignment "
                    "is similar to Kader M3. Match it to family VII on COO guide 3.1.",
                ),
            ],
        ),
        option(
            "takara-1978",
            TAKARA,
            "Japan",
            ["Takara M6"],
            "That is the Takara M6. Two side-by-side columns on the back of the left thigh: "
            "'© G.M.F.G.I. 1978' and 'JAPAN'. On cavity 1b, JAPAN is reversed.",
            True,
        ),
    ]


def c3po_stamps():
    return [
        f"Kader M1 = {THREE}. {M1_POS}.",
        f"Unitoy M2 = {THREE}. 1977 is level with the ©.",
        "Lili Ledy Retorno (M2) = the same three columns as Unitoy M2. 1977 is level with the ©.",
        f"Kader M3 = {TWO}. Fairly similar to Unitoy M4 and Unitoy M7. Compare family III on the guide.",
        "Lili Ledy Regreso (M3) = the same two columns as Kader M3.",
        f"Unitoy M4 = {TWO}. Alignment similar to Kader M3. Compare family IV on the guide.",
        f"Kader M5 = {TWO}. {M5_POS}.",
        f"Unitoy M7 = {TWO}. Alignment similar to Kader M3. Compare family VII on the guide.",
        f"Takara M6 = {TAKARA}. On cavity 1b, JAPAN is reversed.",
        "There is no PBP C-3PO. No C-3PO is stamped Mexico.",
    ]


def apply_coo_figures(figures):
    load_owner()
    record = next((fig for fig in figures if fig.get("name") == "C-3PO"), None)
    if not record:
        raise SystemExit("C-3PO is not in coo-figures")
    record["whereToLook"] = WHERE
    record["cooExplanation"] = EXPLANATION
    record["ask"] = "Which stamp do you see?"
    record["source"] = "owner"
    record["sourceNote"] = NOTE
    record["verified"] = True
    record["hasDetails"] = True
    record["options"] = c3po_options()
    record["ownerStamps"] = c3po_stamps()
    record["stamps"] = c3po_stamps()
    record["missing"] = ""
    record["tells"] = []
    record["referenceImage"] = {"id": "c-3po-coo-guide-3.1"}
    return figures


def sync_owner_stamps(record):
    owner = json.loads(STAMPS.read_text(encoding="utf-8"))
    entry = {
        "name": "C-3PO",
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
    owner["figures"] = [fig for fig in figures if fig.get("name") != "C-3PO"] + [entry]
    owner["c3poNote"] = "C-3PO stamps follow data/references/owner-verified/c-3po.md (owner Warren, 2026-10-11)."
    STAMPS.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def coo(detail):
    return {"category": "coo", "detail": detail, "where": "Look at the country stamp on the back of the left thigh."}


def paint(detail):
    return {"category": "paint", "detail": detail, "where": "Look at the paint colour."}


def mould(detail):
    return {"category": "mould", "detail": detail, "where": "Look at the mould: shape, proportions, tip or hilt."}


def head(detail):
    return {"category": "head", "detail": detail, "where": "Look at the head."}


def variant(vid, factory, mould_name, tells):
    return {
        "id": vid,
        "figure": "C-3PO",
        "factory": factory,
        "mould": mould_name,
        "source": "owner",
        "sourceUrl": "https://www.variantvillain.com/characters/sw/c-3po/",
        "sourceNote": NOTE,
        "tells": tells,
    }


def ll_tells():
    return [
        mould("A dent or a hole beside the stamp. This mark is Lili Ledy only."),
        paint("Dull gold, shiny gold, or silver. The seat is bronze-sprayed because it has no chrome."),
        head("A fat head is a C-3PO (Removable Limbs) head mixed onto this body."),
    ]


def c3po_variants():
    return [
        variant("c-3po--kader-m1", "Kader M1", "M1", [
            coo(f"{THIGH} Three side-by-side columns: '© G.M.F.G.I.', '1977', and 'HONG KONG'. {M1_POS}."),
        ]),
        variant("c-3po--unitoy-m2", "Unitoy M2", "M2", [
            coo(f"{THIGH} Three side-by-side columns. 1977 is level with the ©. There is no dent or hole beside the stamp."),
        ]),
        variant("c-3po--lili-ledy-m2", "Lili Ledy M2", "M2", [
            coo(f"{THIGH} Lili Ledy Retorno. Three side-by-side columns. 1977 is level with the ©."),
            *ll_tells(),
        ]),
        variant("c-3po--kader-m3", "Kader M3", "M3", [
            coo(
                f"{THIGH} Two side-by-side columns: '© G.M.F.G.I. 1977' and 'HONG KONG'. "
                "Fairly similar to Unitoy M4 and Unitoy M7. Compare family III on COO guide 3.1."
            ),
        ]),
        variant("c-3po--lili-ledy-m3", "Lili Ledy M3", "M3", [
            coo(f"{THIGH} Lili Ledy Regreso. Two side-by-side columns, the same layout as Kader M3."),
            *ll_tells(),
        ]),
        variant("c-3po--unitoy-m4", "Unitoy M4", "M4", [
            coo(
                f"{THIGH} Two side-by-side columns. The alignment is similar to Kader M3. "
                "Compare family IV on COO guide 3.1."
            ),
        ]),
        variant("c-3po--kader-m5", "Kader M5", "M5", [
            coo(f"{THIGH} Two side-by-side columns. {M5_POS}."),
        ]),
        variant("c-3po--unitoy-m7", "Unitoy M7", "M7", [
            coo(
                f"{THIGH} Two side-by-side columns. The alignment is similar to Kader M3. "
                "Compare family VII on COO guide 3.1."
            ),
        ]),
        variant("c-3po--takara-m6", "Takara M6", "M6", [
            coo(f"{THIGH} Two side-by-side columns: '© G.M.F.G.I. 1978' and 'JAPAN'. On cavity 1b, JAPAN is reversed."),
        ]),
    ]


def apply_factory_match(payload):
    load_owner()
    fresh = c3po_variants()
    out = []
    inserted = False
    for row in payload.get("figureVariants") or []:
        if row.get("figure") == "C-3PO":
            if not inserted:
                out.extend(fresh)
                inserted = True
            continue
        out.append(row)
    if not inserted:
        out.extend(fresh)
    payload["figureVariants"] = out
    payload["c3poOwner"] = "data/references/owner-verified/c-3po.md"
    return payload


STAMP_BLOCK = """STAMP

Every C-3PO stamp is on the back of the left thigh, running vertically. It is not on the shin and not near the foot.

Only M1 and M2 use three side-by-side columns, "© G.M.F.G.I.", "1977", and "HONG KONG". On Kader M1, 1977 starts on the second column just to the right of the ©. On Unitoy M2 and Lili Ledy Retorno, 1977 is level with the ©.

The other Hong Kong families use two side-by-side columns, "© G.M.F.G.I. 1977" and "HONG KONG". On Kader M5, the H of HONG starts under the middle of the ©. Kader M3, Unitoy M4 and Unitoy M7 are similar, so compare them with COO guide 3.1.

Takara M6 reads "© G.M.F.G.I. 1978" and "JAPAN" in two side-by-side columns. On cavity 1b, JAPAN is reversed.

There is no PBP C-3PO. Lili Ledy was made in Mexico. No C-3PO is stamped Mexico.

"""


def apply_guides():
    load_owner()
    raw = FIGURE.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")
    if "back of the left thigh" not in text:
        text = text.replace("\nFIGURE VARIANT FAMILIES\n", "\n" + STAMP_BLOCK + "FIGURE VARIANT FAMILIES\n", 1)
    ll_extra = """- A dent or a hole beside the stamp is a Lili Ledy mark only.
- Finishes are dull gold, shiny gold, or silver. The seat is bronze-sprayed because it has no chrome.
- A fat head is a C-3PO (Removable Limbs) head mixed onto this body.
- There is no PBP C-3PO. No C-3PO is stamped Mexico.
"""
    if "dent or a hole beside the stamp is a Lili Ledy mark" not in text:
        text = text.replace(
            "- Lili Ledy C-3PO is one of the most visually varied figures in the entire line\n",
            "- Lili Ledy C-3PO is one of the most visually varied figures in the entire line\n" + ll_extra,
            1,
        )
    takara_line = "- Licensing line is © G.M.F.G.I. 1978, with JAPAN beside it. On cavity 1b, JAPAN is reversed.\n"
    if takara_line not in text:
        text = text.replace(
            "- High-quality finish compared to Kenner\n",
            "- High-quality finish compared to Kenner\n" + takara_line,
            1,
        )
    FIGURE.write_bytes(text.replace("\n", newline).encode("utf-8"))


def main():
    load_owner()
    coo = json.loads(COO.read_text(encoding="utf-8"))
    apply_coo_figures(coo["figures"])
    COO.write_text(json.dumps(coo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    record = next(fig for fig in coo["figures"] if fig["name"] == "C-3PO")
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
    print("c-3po owner applied")


if __name__ == "__main__":
    main()
