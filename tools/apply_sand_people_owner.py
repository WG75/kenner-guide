#!/usr/bin/env python3
"""Apply Warren's 25 Oct 2026 Sand People rulings.

The rulings live in data/references/owner-verified/sand-people.md.
COO and factory-match builds call this after the Jawa apply.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "data" / "references" / "owner-verified" / "sand-people.md"
COO = ROOT / "data" / "coo-figures.json"
STAMPS = ROOT / "data" / "coo-owner-stamps.json"
MATCH = ROOT / "data" / "factory-match.json"
FIGURE = ROOT / "data" / "figures" / "sand-people-reference.txt"

PAGE = "https://www.variantvillain.com/characters/sw/sand-people/"
SHEET = "https://www.variantvillain.com/wp-content/uploads/2021/12/sw_tusken.jpg"

REQUIRED = [
    "Date: 2026-10-25",
    "Source: owner Warren",
    "38280",
    "back of the left leg",
    "© G.M.F.G.I. 1977",
    "wider",
    "tighter",
    "end of the lines",
    "no picture",
    "hollow tubes",
    "Meccano is always hollow tubes",
    "purple-brown",
    "Gaderffii Stick M1",
    "Gaderffii Stick M3",
    "Cape M7b",
    "licensing line only",
    "no cloth cloak",
    "Never use Mint as a grade",
]

NOTE = "Owner Warren, 25 Oct 2026. data/references/owner-verified/sand-people.md."
WHERE = (
    "Look on the back of the left leg. "
    "The common stamp is two lines, '© G.M.F.G.I. 1977' and 'HONG KONG'. "
    "The other stamp is one licensing line and no country. "
    "The picture is the Variant Villain COO sheet. "
    "The cape is vinyl. There is no cloth cloak."
)
EXPLANATION = (
    "The country of origin (COO) stamp on this Sand People is on the back of the left leg. "
    "The common stamp is two lines, '© G.M.F.G.I. 1977' and 'HONG KONG'. "
    "The other stamp is one licensing line and no country. "
    "A partial or cut-off country name counts as No COO. "
    "The cape is vinyl. There is no cloth cloak. The stamp is the first check."
)
HK = "Two lines on the back of the left leg: '© G.M.F.G.I. 1977' and 'HONG KONG'"
LINE = "Only the licensing line on the back of the left leg: '© G.M.F.G.I. 1977', with no country"
FAM_I = "It matches family I on the sheet"
FAM_II = "It matches family II on the sheet"
FAM_III = "It matches family III on the sheet"
FAM_IV = "It matches family IV on the sheet"
FAM_V = "It matches family V on the sheet"
HOLLOW = "Very dark brown bandolier and gloves, and thin horns"
POCH = "The bandolier is purple-brown"
WIDER = "The gap between the two lines is wider"
TIGHTER = "The gap between the two lines is tighter"
MATCH_1A = "It matches 1a on the sheet"
MATCH_1B = "It matches 1b on the sheet"
NO_PIC = "Family III 1b. The sheet has no picture"
MATCH_2A = "It matches 2a on the sheet"
MATCH_2B = "It matches 2b on the sheet"
NOCOO_II = "It matches family II 2 on the sheet"
NOCOO_IV = "It matches family IV 2, the Meccano, on the sheet"
HK_LOOK = (
    "That two-line stamp is '© G.M.F.G.I. 1977' and 'HONG KONG', on the back of the left leg. "
    "Family I and II are Unitoy. Family III, IV and V are Kader. "
    "Hollow tubes are the late Kader, very dark brown, with thin horns. "
    "Poch has a purple-brown bandolier.\n\nWhich of these is it?"
)
I_LOOK = (
    "Family I is Unitoy Hong Kong. 1a has a wider gap between the two lines. 1b is tighter. "
    "Check the photo.\n\nWhich of these is it?"
)
II_LOOK = (
    "Family II is Unitoy Hong Kong. Check the end of the lines on the sheet. "
    "Match 1a or 1b.\n\nWhich of these is it?"
)
III_LOOK = (
    "Family III is Kader Hong Kong. 1a is pictured on the sheet. "
    "1b says sorry, no picture. I will not guess a tell for 1b.\n\nWhich of these is it?"
)
IV_LOOK = (
    "Family IV is Kader Hong Kong. Check 1a and 1b on the sheet.\n\nWhich of these is it?"
)
V_LOOK = (
    "Family V is Kader Hong Kong. 1a and 1b differ by how high the © sits on the leg. "
    "Check the photo.\n\nWhich of these is it?"
)
LINE_LOOK = (
    "That is a licensing line only, on the back of the left leg, and no country. "
    "Family II 2 is Unitoy. Family IV 2 is the Meccano, and Meccano is always hollow tubes.\n\n"
    "Which of these is it?"
)
II2_LOOK = (
    "Family II 2 is Unitoy, licensing line only, and the mould is weaker. "
    "Check 2a and 2b on the sheet.\n\nWhich of these is it?"
)
MEC_LOOK = (
    "Family IV 2 is the Meccano. Meccano is always hollow tubes. "
    "Check 2a and 2b on the sheet.\n\nWhich of these is it?"
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
        "alt": "Sand People COO sheet",
        "sourcePage": PAGE,
        "credit": "Photo: Variant Villain",
    }


def look_photo(caption):
    # The chat paints alt as the caption when sourcePage is set.
    return {
        "url": SHEET,
        "alt": caption,
        "title": "Sand People COO sheet",
        "caption": caption,
        "credit": "Photo: Variant Villain",
        "sourcePage": PAGE,
    }


def follow(fid, label, factories, conclusion, follow_ups=None, compare_images=None, compare_reply="", sure=None):
    row = {
        "id": fid,
        "label": label,
        "factories": factories,
        "conclusion": conclusion,
        "sure": (not follow_ups) if sure is None else sure,
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


def pair(fid, label, factory, conclusion):
    return follow(fid, label, [factory], conclusion)


def sand_options():
    photo = [sheet()]
    family_i = follow(
        "unitoy-i",
        FAM_I,
        [],
        "",
        [
            pair("unitoy-i-1a", WIDER, "Unitoy I 1a", "That is the Unitoy, family I 1a. The gap between the two lines is wider. Gaderffii Stick M1. Cape M1 or M3."),
            pair("unitoy-i-1b", TIGHTER, "Unitoy I 1b", "That is the Unitoy, family I 1b. The gap between the two lines is tighter. Gaderffii Stick M1. Cape M1 or M3."),
        ],
        [look_photo("Family I. 1a has a wider gap between the two lines. 1b is tighter.")],
        I_LOOK,
    )
    family_ii = follow(
        "unitoy-ii",
        FAM_II,
        [],
        "",
        [
            pair("unitoy-ii-1a", MATCH_1A, "Unitoy II 1a", "That is the Unitoy, family II 1a. Check the end of the lines on the sheet. Gaderffii Stick M1. Cape M1, M2 or M3."),
            pair("unitoy-ii-1b", MATCH_1B, "Unitoy II 1b", "That is the Unitoy, family II 1b. Check the end of the lines on the sheet. Gaderffii Stick M1. Cape M1, M2 or M3."),
        ],
        [look_photo("Family II. Check the end of the lines. Match 1a or 1b.")],
        II_LOOK,
    )
    family_iii = follow(
        "kader-iii",
        FAM_III,
        [],
        "",
        [
            pair("kader-iii-1a", MATCH_1A, "Kader III 1a", "That is the Kader, family III 1a. It is the one pictured on the sheet. Gaderffii Stick M2. Cape M6."),
            follow(
                "kader-iii-1b",
                NO_PIC,
                [],
                "Variant Villain has no picture of family III 1b. I will not guess a tell.",
                sure=False,
            ),
        ],
        [look_photo("Family III. 1a is pictured. 1b has no picture.")],
        III_LOOK,
    )
    family_iv = follow(
        "kader-iv",
        FAM_IV,
        [],
        "",
        [
            pair("kader-iv-1a", MATCH_1A, "Kader IV 1a", "That is the Kader, family IV 1a. Check the sheet. Gaderffii Stick M2. Cape M4 or M7."),
            pair("kader-iv-1b", MATCH_1B, "Kader IV 1b", "That is the Kader, family IV 1b. Check the sheet. Gaderffii Stick M2. Cape M4 or M7."),
        ],
        [look_photo("Family IV. Check 1a and 1b on the sheet.")],
        IV_LOOK,
    )
    family_v = follow(
        "kader-v",
        FAM_V,
        [],
        "",
        [
            pair("kader-v-1a", MATCH_1A, "Kader V 1a", "That is the Kader, family V 1a. The © height on the leg matches 1a on the sheet. Gaderffii Stick M2. Cape M5."),
            pair("kader-v-1b", MATCH_1B, "Kader V 1b", "That is the Kader, family V 1b. The © height on the leg matches 1b on the sheet. Gaderffii Stick M2. Cape M5."),
        ],
        [look_photo("Family V. 1a and 1b differ by how high the © sits on the leg.")],
        V_LOOK,
    )
    unitoy_open = follow(
        "unitoy-ii-open",
        NOCOO_II,
        [],
        "",
        [
            pair("unitoy-ii-2a", MATCH_2A, "Unitoy II 2a", "That is the Unitoy, family II 2a. Licensing line only, and the mould is weaker. Check the sheet. Gaderffii Stick M1. Cape M1, M2 or M3."),
            pair("unitoy-ii-2b", MATCH_2B, "Unitoy II 2b", "That is the Unitoy, family II 2b. Licensing line only, and the mould is weaker. Check the sheet. Gaderffii Stick M1. Cape M1, M2 or M3."),
        ],
        [look_photo("Family II 2. Licensing line only. Check 2a and 2b on the sheet.")],
        II2_LOOK,
    )
    meccano = follow(
        "meccano",
        NOCOO_IV,
        [],
        "",
        [
            pair("meccano-2a", MATCH_2A, "Hollow Tubes", "That is hollow tubes. Meccano is always hollow tubes. Family IV 2a, licensing line only. Gaderffii Stick M3. Cape M7b."),
            pair("meccano-2b", MATCH_2B, "Hollow Tubes", "That is hollow tubes. Meccano is always hollow tubes. Family IV 2b, licensing line only. Gaderffii Stick M3. Cape M7b."),
        ],
        [look_photo("Family IV 2, the Meccano. Meccano is always hollow tubes. Check 2a and 2b.")],
        MEC_LOOK,
    )
    return [
        option(
            "hk-left",
            HK,
            "Hong Kong",
            ["Unitoy I 1a", "Unitoy I 1b", "Unitoy II 1a", "Unitoy II 1b", "Kader III 1a", "Kader IV 1a", "Kader IV 1b", "Kader V 1a", "Kader V 1b", "Hollow Tubes", "Poch"],
            "",
            False,
            [
                family_i,
                family_ii,
                family_iii,
                family_iv,
                family_v,
                follow(
                    "hollow-tubes",
                    HOLLOW,
                    ["Hollow Tubes"],
                    "That is hollow tubes, the late Kader. Very dark brown bandolier and gloves, and thin horns. Gaderffii Stick M3. Cape M7b.",
                ),
                follow(
                    "poch",
                    POCH,
                    ["Poch"],
                    "That is the Poch. Mixed family II and IV parts. The bandolier is purple-brown. The stamp is the same two lines. Gaderffii Stick M1, sometimes M2.",
                ),
            ],
            photo,
            HK_LOOK,
        ),
        option(
            "licensing-line",
            LINE,
            "No COO",
            ["Unitoy II 2a", "Unitoy II 2b", "Hollow Tubes"],
            "",
            False,
            [unitoy_open, meccano],
            photo,
            LINE_LOOK,
        ),
    ]


def sand_stamps():
    return [
        "Family I Unitoy = two lines on the back of the left leg. 1a has a wider gap. 1b is tighter.",
        "Family II 1a and 1b Unitoy = two lines. Check the end of the lines on the sheet.",
        "Family II 2a and 2b Unitoy = the licensing line only. Check the sheet. The mould is weaker.",
        "Family III 1a Kader = two lines, and it is pictured. Family III 1b has no picture.",
        "Family IV 1a and 1b Kader = two lines. Check the sheet.",
        "Family IV 2 Meccano = the licensing line only. Meccano is always hollow tubes.",
        "Family V 1a and 1b Kader = two lines. The © height on the leg differs. Check the sheet.",
        "Hollow tubes = late Kader. Very dark brown bandolier and gloves, and thin horns.",
        "Poch = mixed family II and IV parts. The bandolier is purple-brown.",
    ]


def apply_coo_figures(figures):
    load_owner()
    record = next((fig for fig in figures if fig.get("name") == "Sand People"), None)
    if not record:
        raise SystemExit("Sand People is not in coo-figures")
    record["whereToLook"] = WHERE
    record["cooExplanation"] = EXPLANATION
    record["ask"] = "Which stamp do you see?"
    record["source"] = "owner"
    record["sourceNote"] = NOTE
    record["verified"] = True
    record["hasDetails"] = True
    record["options"] = sand_options()
    record["ownerStamps"] = sand_stamps()
    record["stamps"] = sand_stamps()
    record["missing"] = "Family III 1b has no picture on the Variant Villain sheet. Do not invent a tell."
    record["tells"] = []
    record["error"] = ""
    record["guide"] = [
        "I: Unitoy Hong Kong",
        "II: Unitoy Hong Kong, and Unitoy No COO",
        "III: Kader Hong Kong",
        "IV: Kader Hong Kong, and Meccano",
        "V: Kader Hong Kong",
    ]
    record["families"] = [
        {"title": "COO Family I:", "lines": ["Unitoy Hong Kong", "1a has a wider gap between the two lines. 1b is tighter. Gaderffii Stick M1. Cape M1 or M3."]},
        {"title": "COO Family II:", "lines": ["Unitoy Hong Kong and Unitoy No COO", "Check the end of the lines for 1a and 1b. 2a and 2b are the licensing line only. Gaderffii Stick M1. Cape M1, M2 or M3."]},
        {"title": "COO Family III:", "lines": ["Kader Hong Kong", "1a is pictured. 1b has no picture. Gaderffii Stick M2. Cape M6."]},
        {"title": "COO Family IV:", "lines": ["Kader Hong Kong and Meccano", "Check 1a and 1b on the sheet. Family IV 2 is the Meccano. Meccano is always hollow tubes."]},
        {"title": "COO Family V:", "lines": ["Kader Hong Kong", "1a and 1b differ by how high the © sits on the leg. Gaderffii Stick M2. Cape M5."]},
    ]
    record["referenceImage"] = sheet()
    record["sourceUrl"] = PAGE
    record.pop("capeFirst", None)
    return figures


def sync_owner_stamps(record):
    owner = json.loads(STAMPS.read_text(encoding="utf-8"))
    entry = {
        "name": "Sand People",
        "recorded": "2026-10-25",
        "source": "owner",
        "whereToLook": record["whereToLook"],
        "ask": record["ask"],
        "stamps": record["ownerStamps"],
        "options": record["options"],
        "referenceImage": record["referenceImage"],
        "missing": record.get("missing") or "",
    }
    figures = owner.get("figures") or []
    owner["figures"] = [fig for fig in figures if fig.get("name") != "Sand People"] + [entry]
    owner["sandPeopleNote"] = "Sand People stamps follow data/references/owner-verified/sand-people.md (owner Warren, 2026-10-25)."
    STAMPS.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def coo(detail):
    return {"category": "coo", "detail": detail, "where": "Look at the country stamp on the back of the left leg."}


def variant(vid, factory, mould_name, detail):
    return {
        "id": vid,
        "figure": "Sand People",
        "factory": factory,
        "mould": mould_name,
        "source": "owner",
        "sourceUrl": PAGE,
        "sourceNote": NOTE,
        "tells": [coo(detail)],
    }


def sand_variants():
    return [
        variant("sand-people--unitoy-i-1a", "Unitoy I 1a", "I", f"{HK}. Family I 1a. The gap between the two lines is wider."),
        variant("sand-people--unitoy-i-1b", "Unitoy I 1b", "I", f"{HK}. Family I 1b. The gap between the two lines is tighter."),
        variant("sand-people--unitoy-ii-1a", "Unitoy II 1a", "II", f"{HK}. Family II 1a. Check the end of the lines on the sheet."),
        variant("sand-people--unitoy-ii-1b", "Unitoy II 1b", "II", f"{HK}. Family II 1b. Check the end of the lines on the sheet."),
        variant("sand-people--unitoy-ii-2a", "Unitoy II 2a", "II", f"{LINE}. Family II 2a. The mould is weaker."),
        variant("sand-people--unitoy-ii-2b", "Unitoy II 2b", "II", f"{LINE}. Family II 2b. The mould is weaker."),
        variant("sand-people--kader-iii-1a", "Kader III 1a", "III", f"{HK}. Family III 1a. It is pictured on the sheet."),
        variant("sand-people--kader-iv-1a", "Kader IV 1a", "IV", f"{HK}. Family IV 1a. Check the sheet."),
        variant("sand-people--kader-iv-1b", "Kader IV 1b", "IV", f"{HK}. Family IV 1b. Check the sheet."),
        variant("sand-people--kader-v-1a", "Kader V 1a", "V", f"{HK}. Family V 1a. The © height on the leg matches the sheet."),
        variant("sand-people--kader-v-1b", "Kader V 1b", "V", f"{HK}. Family V 1b. The © height on the leg matches the sheet."),
        variant("sand-people--hollow-tubes", "Hollow Tubes", "Hollow Tubes", f"{HK}. Late Kader. Very dark brown bandolier and gloves, and thin horns. Meccano is always hollow tubes."),
        variant("sand-people--poch", "Poch", "Poch", f"{HK}. Mixed family II and IV parts. The bandolier is purple-brown."),
    ]


LINKS = {
    "gaderffii-stick--unitoy-m1": [
        "sand-people--unitoy-i-1a",
        "sand-people--unitoy-i-1b",
        "sand-people--unitoy-ii-1a",
        "sand-people--unitoy-ii-1b",
        "sand-people--unitoy-ii-2a",
        "sand-people--unitoy-ii-2b",
        "sand-people--poch",
    ],
    "gaderffii-stick--kader-m2": [
        "sand-people--kader-iii-1a",
        "sand-people--kader-iv-1a",
        "sand-people--kader-iv-1b",
        "sand-people--kader-v-1a",
        "sand-people--kader-v-1b",
        "sand-people--poch",
    ],
    "gaderffii-stick--kader-m3": ["sand-people--hollow-tubes"],
    "tusken-raider-cape--unitoy-m1": [
        "sand-people--unitoy-i-1a",
        "sand-people--unitoy-i-1b",
        "sand-people--unitoy-ii-1a",
        "sand-people--unitoy-ii-1b",
        "sand-people--unitoy-ii-2a",
        "sand-people--unitoy-ii-2b",
    ],
    "tusken-raider-cape--unitoy-m2": [
        "sand-people--unitoy-ii-1a",
        "sand-people--unitoy-ii-1b",
        "sand-people--unitoy-ii-2a",
        "sand-people--unitoy-ii-2b",
    ],
    "tusken-raider-cape--unitoy-m3": [
        "sand-people--unitoy-i-1a",
        "sand-people--unitoy-i-1b",
        "sand-people--unitoy-ii-1a",
        "sand-people--unitoy-ii-1b",
        "sand-people--unitoy-ii-2a",
        "sand-people--unitoy-ii-2b",
    ],
    "tusken-raider-cape--kader-m4": [
        "sand-people--kader-iv-1a",
        "sand-people--kader-iv-1b",
    ],
    "tusken-raider-cape--kader-m5": [
        "sand-people--kader-v-1a",
        "sand-people--kader-v-1b",
    ],
    "tusken-raider-cape--kader-m6": ["sand-people--kader-iii-1a"],
    "tusken-raider-cape--kader-m7": [
        "sand-people--kader-iv-1a",
        "sand-people--kader-iv-1b",
        "sand-people--hollow-tubes",
    ],
}


def apply_carded(payload):
    for row in payload.get("accessoryVariants") or []:
        extra = LINKS.get(row.get("id"))
        if extra is None:
            continue
        current = list(row.get("cardedWith") or [])
        others = [item for item in current if not str(item).startswith("sand-people--")]
        row["cardedWith"] = others + [item for item in extra if item not in others]
        row["sourceNote"] = NOTE


def apply_factory_match(payload):
    load_owner()
    fresh = sand_variants()
    out = []
    inserted = False
    for row in payload.get("figureVariants") or []:
        if row.get("figure") == "Sand People":
            if not inserted:
                out.extend(fresh)
                inserted = True
            continue
        out.append(row)
    if not inserted:
        out.extend(fresh)
    payload["figureVariants"] = out
    apply_carded(payload)
    payload["sandPeopleOwner"] = "data/references/owner-verified/sand-people.md"
    return payload


def apply_guides():
    load_owner()
    raw = FIGURE.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")
    swaps = [
        (
            "COO Families include:\n"
            "- Hong Kong (various factories)\n"
            "- Taiwan\n"
            "- No COO variants\n"
            "- Possible Poch / Lili Ledy variants\n\n"
            "Key Figure Traits:\n"
            "- Mask sculpt differences\n"
            "- Eye paint variation\n"
            "- Belt colour variation\n"
            "- Robe paint tone differences\n",
            "The stamp is on the back of the left leg. Warren confirmed this on 25 Oct 2026.\n\n"
            "The common stamp is two lines, '© G.M.F.G.I. 1977' and 'HONG KONG'. "
            "The other stamp is the licensing line only, and no country.\n\n"
            "Family I, Unitoy Hong Kong: 1a has a wider gap between the two lines. 1b is tighter. Gaderffii Stick M1. Cape M1 or M3.\n"
            "Family II, Unitoy Hong Kong: check the end of the lines on the sheet. Family II 2 is the licensing line only, and the mould is weaker. Gaderffii Stick M1. Cape M1, M2 or M3.\n"
            "Family III, Kader Hong Kong: 1a is pictured. Family III 1b has no picture. Gaderffii Stick M2. Cape M6.\n"
            "Family IV, Kader Hong Kong: check 1a and 1b on the sheet. Gaderffii Stick M2. Cape M4 or M7. Family IV 2 is the Meccano. Meccano is always hollow tubes. Gaderffii Stick M3. Cape M7b.\n"
            "Family V, Kader Hong Kong: 1a and 1b differ by how high the © sits on the leg. Gaderffii Stick M2. Cape M5.\n"
            "Hollow tubes are the late Kader. Very dark brown bandolier and gloves, and thin horns. Gaderffii Stick M3. Cape M7b.\n"
            "Poch uses mixed family II and IV parts. The bandolier is purple-brown. Gaderffii Stick M1, sometimes M2.\n"
            "The cape is vinyl. There is no cloth cloak.\n",
        ),
        (
            "- Early mould variation across multiple factories\n"
            "- Independent evolution of cape cuts and weapon moulds\n"
            "- No strict 1:1 pairing rules like some figures\n\n"
            "Instead:\n"
            "👉 Variants must be judged as combinations\n",
            "- The stamp on the back of the left leg comes first\n"
            "- Then match the family on the Variant Villain COO sheet\n"
            "- Cape and gaderffii stick follow the family\n",
        ),
        (
            "1. Figure sculpt (mask + body)\n"
            "2. Cape variant (cut + holes)\n"
            "3. Gaderffii stick mould + colour\n"
            "4. COO marking\n\n"
            "All three components must align.\n",
            "1. The stamp on the back of the left leg\n"
            "2. The family on the Variant Villain COO sheet\n"
            "3. Cape variant\n"
            "4. Gaderffii stick mould\n",
        ),
    ]
    for old_bit, new_bit in swaps:
        if old_bit in text:
            text = text.replace(old_bit, new_bit, 1)
        elif new_bit not in text:
            raise SystemExit("sand people reference is missing a block to replace")
    FIGURE.write_bytes(text.replace("\n", newline).encode("utf-8"))


def main():
    load_owner()
    coo = json.loads(COO.read_text(encoding="utf-8"))
    apply_coo_figures(coo["figures"])
    COO.write_text(json.dumps(coo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    record = next(fig for fig in coo["figures"] if fig["name"] == "Sand People")
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
    print("sand people owner applied")


if __name__ == "__main__":
    main()
