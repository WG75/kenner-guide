#!/usr/bin/env python3
"""Apply Warren's 17 Oct 2026 Ben (Obi-Wan) Kenobi rulings.

The rulings live in data/references/owner-verified/ben-obi-wan-kenobi.md.
COO and factory-match builds call this after the Stormtrooper apply.
The Darth Vader apply inserts a Lili Ledy Ben stub for sabre M9.
This apply replaces that stub and keeps the M9 link.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "data" / "references" / "owner-verified" / "ben-obi-wan-kenobi.md"
COO = ROOT / "data" / "coo-figures.json"
STAMPS = ROOT / "data" / "coo-owner-stamps.json"
MATCH = ROOT / "data" / "factory-match.json"
FIGURE = ROOT / "data" / "figures" / "ben-obi-wan-kenobi-reference.txt"

PAGE = "https://www.variantvillain.com/characters/sw/ben-obi-wan-kenobi/"
SHEET = "https://www.variantvillain.com/wp-content/uploads/2021/12/SW_BenKenobi.jpg"
FAM_I = "https://www.variantvillain.com/wp-content/uploads/2022/12/ANH_BenKenobi_01.jpg"
FAM_II = "https://www.variantvillain.com/wp-content/uploads/2022/12/ANH_BenKenobi_03.jpg"
FAM_III = "https://www.variantvillain.com/wp-content/uploads/2022/12/ANH_BenKenobi_05.jpg"
CAPE = "https://www.variantvillain.com/accessory-guide/ben-obi-wan-kenobi-cape/"

REQUIRED = [
    "Date: 2026-10-17",
    "Source: owner Warren",
    "38250",
    "back of the legs",
    "Not every Ben stamp is two lines",
    "licensing line only",
    "runs past the end of 1977",
    "not a tell",
    "starts under the ©",
    "first G of G.M.F.G.I.",
    "three head sizes",
    "glossier and thinner",
    "pale",
    "comparison photos",
    "not a stamp rule",
    "white-hair Trilogo",
    "M6",
    "extremely rare",
    "M5 and M6",
    "Kader China cape",
    "Never use Mint as a grade",
]

NOTE = "Owner Warren, 17 Oct 2026. data/references/owner-verified/ben-obi-wan-kenobi.md."
WHERE = (
    "Look on the back of the legs. "
    "Unitoy family I and family II with a country are two lines, "
    "'© G.M.F.G.I. 1977' and 'MADE IN HONG KONG'. "
    "Kader family III with a country is two lines, 'HONG KONG'. "
    "Lili Ledy and the No COO Bens are one line, the licensing line only. "
    "The picture is the Variant Villain COO sheet."
)
EXPLANATION = (
    "The country of origin (COO) stamp on this Ben (Obi-Wan) Kenobi is on the back of the legs. "
    "Some stamps are two lines. The Lili Ledy and the No COO Bens are one line, the licensing line only. "
    "A partial or cut-off country name counts as No COO."
)
UNITOY = (
    "Two lines on the back of the legs: '© G.M.F.G.I. 1977' and 'MADE IN HONG KONG'"
)
HK = "Two lines on the back of the legs: '© G.M.F.G.I. 1977' and 'HONG KONG'"
LINE = (
    "Only the licensing line on the back of the legs: '© G.M.F.G.I. 1977', with no country"
)
WHITE = "White hair, and it matches family I on the photo"
GREY = "Grey hair, and it matches family II on the photo"
UNDER_C = "HONG KONG starts under the ©"
UNDER_G = "HONG KONG starts under the first G of G.M.F.G.I."
POCH = "The black paint is glossier and thinner, and the hands are pale"
PHOTO_U = "It matches the Unitoy family II figure on the photo"
PHOTO_L = "It matches the Lili Ledy on the photo"
PHOTO_K = "It matches the Kader family III figure on the photo"
UNITOY_LOOK = (
    "Both Unitoy family I and family II use those two lines. "
    "On both, the MADE IN HONG KONG column runs past the end of 1977, so that does not separate them. "
    "Match the hair to the Variant Villain photo.\n\nWhich of these is it?"
)
NOCOO_LOOK = (
    "That one licensing line is shared by the Unitoy family II No COO, the Lili Ledy and the Kader family III No COO. "
    "The stamp does not separate them. Match the figure to the Variant Villain photo.\n\nWhich of these is it?"
)

UNITOY_IDS = [
    "ben-obi-wan-kenobi--unitoy-i",
    "ben-obi-wan-kenobi--unitoy-ii",
    "ben-obi-wan-kenobi--unitoy-ii-no-coo",
]
KADER_IDS = [
    "ben-obi-wan-kenobi--kader-iii-1a",
    "ben-obi-wan-kenobi--kader-iii-1b",
    "ben-obi-wan-kenobi--kader-iii-no-coo",
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


def ben_options():
    return [
        option(
            "made-in-hong-kong",
            UNITOY,
            "Hong Kong",
            ["Unitoy I", "Unitoy II with the country"],
            "",
            False,
            [
                follow(
                    "unitoy-i",
                    WHITE,
                    ["Unitoy I"],
                    "That is the Unitoy family I. Two lines, '© G.M.F.G.I. 1977' and 'MADE IN HONG KONG'. "
                    "White hair. The country column running past 1977 is also true of family II, so that was not the tell. "
                    "Cape M5 and M6. Sabre M1, then M2, then M3.",
                ),
                follow(
                    "unitoy-ii",
                    GREY,
                    ["Unitoy II with the country"],
                    "That is the Unitoy family II with the country. Grey hair. "
                    "The MADE IN HONG KONG column runs past 1977 on family I as well, so that was not the tell. "
                    "Cape M7. Sabre M1, then M2, then M3.",
                ),
            ],
            [photo(FAM_I, "Ben (Obi-Wan) Kenobi, family I, Unitoy"), photo(FAM_II, "Ben (Obi-Wan) Kenobi, family II, Unitoy and Lili Ledy")],
            UNITOY_LOOK,
        ),
        option(
            "hong-kong",
            HK,
            "Hong Kong",
            ["Kader III 1a", "Kader III 1b", "Poch"],
            "",
            False,
            [
                follow(
                    "kader-1a",
                    UNDER_C,
                    ["Kader III 1a"],
                    "That is the Kader family III 1a. HONG KONG starts under the ©. Cape M1 to M4. Sabre M1 lettered, then M5.",
                ),
                follow(
                    "kader-1b",
                    UNDER_G,
                    ["Kader III 1b"],
                    "That is the Kader family III 1b. HONG KONG starts under the first G of G.M.F.G.I. Cape M1 to M4. Sabre M1 lettered, then M5.",
                ),
                follow(
                    "poch",
                    POCH,
                    ["Poch"],
                    "That is the Poch. It uses the Kader Hong Kong stamp. The black paint is glossier and thinner, and the hands are pale.",
                ),
            ],
        ),
        option(
            "licensing-line",
            LINE,
            "No COO",
            ["Unitoy II No COO", "Lili Ledy", "Kader III No COO"],
            "",
            False,
            [
                follow(
                    "unitoy-ii-no-coo",
                    PHOTO_U,
                    ["Unitoy II No COO"],
                    "That is the Unitoy family II No COO. The licensing line is the only marking. "
                    "The stamp does not separate it from the Lili Ledy or the Kader family III No COO. "
                    "It matches the family II photo. Cape M8. Sabre M1, then M2, then M3.",
                ),
                follow(
                    "lili-ledy",
                    PHOTO_L,
                    ["Lili Ledy"],
                    "That is the Lili Ledy. The licensing line is the only marking. Lili Ledy Ben has three head sizes. "
                    "The stamp does not separate it. It matches the photo. Cape M9. Sabre M9.",
                ),
                follow(
                    "kader-no-coo",
                    PHOTO_K,
                    ["Kader III No COO"],
                    "That is the Kader family III No COO. The licensing line is the only marking. "
                    "The No COO white-hair Trilogo Ben also came with sabre M6. "
                    "The stamp does not separate it. It matches the family III photo. Cape M1 to M4. Sabre M1 lettered, then M5, and also M6.",
                ),
            ],
            [photo(FAM_II, "Ben (Obi-Wan) Kenobi, family II, Unitoy and Lili Ledy"), photo(FAM_III, "Ben (Obi-Wan) Kenobi, family III, Kader and Poch")],
            NOCOO_LOOK,
        ),
    ]


def ben_stamps():
    return [
        "Unitoy family I = two lines, '© G.M.F.G.I. 1977' and 'MADE IN HONG KONG'. White hair. The country column runs past 1977, and family II does the same.",
        "Unitoy family II with the country = the same two lines. Grey hair. The column running past 1977 is not the tell.",
        "Unitoy family II No COO = the licensing line only. Match it on the family II photo. Not a stamp rule.",
        "Lili Ledy = the licensing line only. Three head sizes. Match it on the photo. Not a stamp rule.",
        "Kader family III 1a = two lines, 'HONG KONG'. HONG KONG starts under the ©.",
        "Kader family III 1b = two lines, 'HONG KONG'. HONG KONG starts under the first G of G.M.F.G.I.",
        "Poch = the Kader Hong Kong stamp. Glossier, thinner black paint, and pale hands.",
        "Kader family III No COO = the licensing line only. The No COO white-hair Trilogo Ben also uses sabre M6. Match it on the family III photo.",
    ]


def sheet_image():
    return photo(SHEET, "Ben (Obi-Wan) Kenobi COO sheet")


def apply_coo_figures(figures):
    load_owner()
    record = next((fig for fig in figures if fig.get("name") == "Ben (Obi-Wan) Kenobi"), None)
    if not record:
        raise SystemExit("Ben (Obi-Wan) Kenobi is not in coo-figures")
    record["whereToLook"] = WHERE
    record["cooExplanation"] = EXPLANATION
    record["ask"] = "Which stamp do you see?"
    record["source"] = "owner"
    record["sourceNote"] = NOTE
    record["verified"] = True
    record["hasDetails"] = True
    record["options"] = ben_options()
    record["ownerStamps"] = ben_stamps()
    record["stamps"] = ben_stamps()
    record["missing"] = ""
    record["tells"] = []
    record["guide"] = [
        "I: Unitoy",
        "II: Unitoy/ Lili Ledy",
        "III: Kader/ Poch",
    ]
    record["families"] = [
        {"title": "COO Family I:", "lines": ["Unitoy", "Two lines, '© G.M.F.G.I. 1977' and 'MADE IN HONG KONG'. White hair."]},
        {"title": "COO Family II:", "lines": ["Unitoy / Lili Ledy", "Unitoy with the country is the same two lines. Grey hair. Unitoy No COO and Lili Ledy are the licensing line only."]},
        {"title": "COO Family III:", "lines": ["Kader / Poch", "HONG KONG. 1a starts under the ©. 1b starts under the first G. Poch has glossier, thinner black paint and pale hands. Kader No COO is the licensing line only."]},
    ]
    record["referenceImage"] = sheet_image()
    return figures


def sync_owner_stamps(record):
    owner = json.loads(STAMPS.read_text(encoding="utf-8"))
    entry = {
        "name": "Ben (Obi-Wan) Kenobi",
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
    owner["figures"] = [fig for fig in figures if fig.get("name") != "Ben (Obi-Wan) Kenobi"] + [entry]
    owner["benNote"] = (
        "Ben (Obi-Wan) Kenobi stamps follow data/references/owner-verified/ben-obi-wan-kenobi.md (owner Warren, 2026-10-17)."
    )
    STAMPS.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def coo(detail):
    return {"category": "coo", "detail": detail, "where": "Look at the country stamp on the back of the legs."}


def hair(detail):
    return {"category": "hair", "detail": detail, "where": "Look at the hair colour."}


def paint(detail):
    return {"category": "paint", "detail": detail, "where": "Look at the paint."}


def head(detail):
    return {"category": "head", "detail": detail, "where": "Look at the head."}


def variant(vid, factory, mould_name, tells):
    return {
        "id": vid,
        "figure": "Ben (Obi-Wan) Kenobi",
        "factory": factory,
        "mould": mould_name,
        "source": "owner",
        "sourceUrl": PAGE,
        "sourceNote": NOTE,
        "tells": tells,
    }


def ben_variants():
    return [
        variant("ben-obi-wan-kenobi--unitoy-i", "Unitoy I", "I", [
            coo(f"{UNITOY}. Family I. The country column runs past 1977, and family II does the same."),
            hair("White hair."),
        ]),
        variant("ben-obi-wan-kenobi--unitoy-ii", "Unitoy II with the country", "II", [
            coo(f"{UNITOY}. Family II. Grey hair separates it from family I."),
            hair("Grey hair."),
        ]),
        variant("ben-obi-wan-kenobi--unitoy-ii-no-coo", "Unitoy II No COO", "", [
            coo(f"{LINE}. Family II. Match the family II photo. The stamp does not separate the No COO Bens."),
            hair("Grey hair, family II."),
        ]),
        variant("ben-obi-wan-kenobi--lili-ledy", "Lili Ledy", "", [
            coo(f"{LINE}. Family II. Match the photo. The stamp does not separate the No COO Bens."),
            head("Three head sizes."),
        ]),
        variant("ben-obi-wan-kenobi--kader-iii-1a", "Kader III 1a", "III", [
            coo(f"{HK}. HONG KONG starts under the ©."),
        ]),
        variant("ben-obi-wan-kenobi--kader-iii-1b", "Kader III 1b", "III", [
            coo(f"{HK}. HONG KONG starts under the first G of G.M.F.G.I."),
        ]),
        variant("ben-obi-wan-kenobi--poch", "Poch", "", [
            coo(f"{HK}. The Kader Hong Kong stamp."),
            paint("Glossier, thinner black paint, and pale hands."),
        ]),
        variant("ben-obi-wan-kenobi--kader-iii-no-coo", "Kader III No COO", "", [
            coo(f"{LINE}. Family III. The No COO white-hair Trilogo Ben also uses sabre M6. Match the family III photo."),
            hair("White hair."),
        ]),
    ]


SABRE_LINKS = {
    "telescoping-lightsaber--unknown-m1": UNITOY_IDS + KADER_IDS,
    "telescoping-lightsaber--unitoy-m2": UNITOY_IDS,
    "telescoping-lightsaber--unitoy-m3": UNITOY_IDS,
    "telescoping-lightsaber--kader-m5": KADER_IDS,
    "telescoping-lightsaber--pbp-m6": ["ben-obi-wan-kenobi--kader-iii-no-coo"],
    "telescoping-lightsaber--lili-ledy-m9": ["ben-obi-wan-kenobi--lili-ledy"],
}

CAPE_LINKS = {
    "ben-obi-wan-kenobi-cape--unitoy-m5": ["ben-obi-wan-kenobi--unitoy-i"],
    "ben-obi-wan-kenobi-cape--unitoy-m6": ["ben-obi-wan-kenobi--unitoy-i"],
    "ben-obi-wan-kenobi-cape--unitoy-m7": ["ben-obi-wan-kenobi--unitoy-ii"],
    "ben-obi-wan-kenobi-cape--unitoy-m8": ["ben-obi-wan-kenobi--unitoy-ii-no-coo"],
    "ben-obi-wan-kenobi-cape--kader-m1": KADER_IDS,
    "ben-obi-wan-kenobi-cape--kader-m2": KADER_IDS,
    "ben-obi-wan-kenobi-cape--kader-m3": KADER_IDS,
    "ben-obi-wan-kenobi-cape--kader-m4": KADER_IDS,
    "ben-obi-wan-kenobi-cape--lili-ledy-m9": ["ben-obi-wan-kenobi--lili-ledy"],
}

CHINA_NOTE = "Cape M4 is also the Kader China cape. No separate Kader China Ben stamp was named, so this record is not linked to a figure."


def apply_carded(payload):
    links = dict(SABRE_LINKS)
    links.update(CAPE_LINKS)
    for row in payload.get("accessoryVariants") or []:
        extra = links.get(row.get("id"))
        if extra is None:
            continue
        current = list(row.get("cardedWith") or [])
        others = [item for item in current if not str(item).startswith("ben-obi-wan-kenobi--")]
        row["cardedWith"] = others + [item for item in extra if item not in others]
        row["sourceNote"] = NOTE
        if row.get("id") == "ben-obi-wan-kenobi-cape--kader-m4":
            row["sourceNote"] = NOTE + " M4 is also the Kader China cape."
    for row in payload.get("accessoryVariants") or []:
        if row.get("id") == "ben-obi-wan-kenobi-cape--kader-china-m4":
            row["sourceNote"] = NOTE + " " + CHINA_NOTE
            row["cardedWith"] = []


def apply_factory_match(payload):
    load_owner()
    fresh = ben_variants()
    out = []
    inserted = False
    for row in payload.get("figureVariants") or []:
        if row.get("figure") == "Ben (Obi-Wan) Kenobi":
            if not inserted:
                out.extend(fresh)
                inserted = True
            continue
        out.append(row)
    if not inserted:
        out.extend(fresh)
    payload["figureVariants"] = out
    apply_carded(payload)
    payload["benOwner"] = "data/references/owner-verified/ben-obi-wan-kenobi.md"
    return payload


FAMILIES = """FIGURE VARIANT FAMILIES (COO BASED)

Owner Warren, 17 Oct 2026. The stamp is on the back of the legs.

Family I is Unitoy. Two lines, '© G.M.F.G.I. 1977' and 'MADE IN HONG KONG'. White hair.

Family II is Unitoy and Lili Ledy. Unitoy with the country is the same two lines, and the hair is grey. The MADE IN HONG KONG column runs past the end of 1977 on both family I and family II, so that does not separate them. Unitoy No COO and Lili Ledy are one line, the licensing line only. Lili Ledy has three head sizes.

Family III is Kader and Poch. Two lines of 'HONG KONG'. On 1a, HONG KONG starts under the ©. On 1b, it starts under the first G of G.M.F.G.I. Poch uses that Hong Kong stamp, with glossier, thinner black paint and pale hands. Kader No COO is the licensing line only.

The No COO Bens (Unitoy II, Lili Ledy and Kader III) are separated on the Variant Villain photos, not by a stamp rule.

Cape moulds and sabre moulds are a different series from these family numbers.

--------------------------------------------------

"""

SABRE_NOTE = (
    "Ben's sabres, as Variant Villain links them. Kader uses the lettered M1, then M5. "
    "The No COO white-hair Trilogo Ben also uses M6. Unitoy uses M1, then M2, then M3. "
    "Lili Ledy uses M9. The blue double-telescoping sabre is extremely rare.\n\n"
)


def apply_guides():
    load_owner()
    raw = FIGURE.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")
    start = text.find("FIGURE VARIANT FAMILIES (COO BASED)\n")
    end = text.find("CAPE (EXTREMELY IMPORTANT)\n")
    if start != -1 and end != -1:
        text = text[:start] + FAMILIES + text[end:]
    needle = "Ben Kenobi uses BLUE sabers only.\n"
    if "No COO white-hair Trilogo Ben" not in text and needle in text:
        text = text.replace(needle, needle + "\n" + SABRE_NOTE, 1)
    FIGURE.write_bytes(text.replace("\n", newline).encode("utf-8"))


def main():
    load_owner()
    coo = json.loads(COO.read_text(encoding="utf-8"))
    apply_coo_figures(coo["figures"])
    COO.write_text(json.dumps(coo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    record = next(fig for fig in coo["figures"] if fig["name"] == "Ben (Obi-Wan) Kenobi")
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
    print("ben owner applied")


if __name__ == "__main__":
    main()
