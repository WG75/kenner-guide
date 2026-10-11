#!/usr/bin/env python3
"""Apply the owner's 11 Oct 2026 COO review sheet.

Columns K onward are one "Factory Mx = stamp description" cell. A row with
those cells is owner-verified and replaces the scraped stamp buttons. A row
with no stamp cells is unchanged, so its source stays as it was.

Typos fixed on import: Lili Lefy, raise bar, left left leg, and the older
10 Oct sheet typos.
"""

import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
COO = ROOT / "data" / "coo-figures.json"
OWNER_JSON = ROOT / "data" / "coo-owner-stamps.json"
SHEET = ROOT / "docs" / "coo-review-2026-10-11.xlsx"
REPORT = ROOT / "docs" / "coo-cross-tells.md"

FACTORY_NAMES = [
    "kader china",
    "lili ledy",
    "top toys",
    "unitoy",
    "glasslite",
    "meccano",
    "taiwan",
    "kader",
    "smile",
    "poch",
    "pbp",
    "takara",
]

CATEGORIES = [
    ("hair", re.compile(r"\b(hair|blonde|blond)\b", re.I)),
    ("paint", re.compile(r"\b(paint|eyes|trousers|boots|scarf|flesh)\b", re.I)),
    ("plastic", re.compile(r"\b(plastic|opaque)\b", re.I)),
    ("head", re.compile(r"\b(head|face sculpt|ears)\b", re.I)),
    ("mould", re.compile(r"\b(moulds?|molds?|sculpt|ejector|epm)\b", re.I)),
    ("date", re.compile(r"\b(date stamp|198[0-9])\b", re.I)),
    ("cavity", re.compile(r"\bcavit", re.I)),
    ("assembly", re.compile(r"\b(mixed legs|assembly)\b", re.I)),
    ("accessory", re.compile(r"\b(saber|sabre|blaster|cape|staff|cloak|belt|helmet|bow)\b", re.I)),
    ("cardback", re.compile(r"\b(cardback|12-back|12b-back|trilogo|92bk)\b", re.I)),
]

WHERE = {
    "hair": "Look at the hair colour.",
    "paint": "Look at the paint colour.",
    "plastic": "Look at the plastic colour.",
    "head": "Look at the head.",
    "mould": "Look at the mould detail.",
    "date": "Look at the date stamp.",
    "cavity": "Look for a cavity mark.",
    "assembly": "Look at how the parts are assembled.",
    "accessory": "Look at the accessory that is with it.",
    "cardback": "If it is still carded, which card is it on?",
}

COO_WORD = re.compile(
    r"(?i)(made in hong kong|hong kong|made in taiwan|taiwan|made in china|china|"
    r"made in japan|japan|no coo|scar)"
)


def fix_text(text):
    text = str(text or "")
    text = text.replace("Lili Lefy", "Lili Ledy").replace("lili lefy", "Lili Ledy")
    text = re.sub(r"(?i)\braise bar\b", "raised bar", text)
    text = re.sub(r"(?i)\bleft left leg\b", "left leg", text)
    text = text.replace("Chna", "China")
    text = text.replace("reminants", "remnants").replace("remanants", "remnants")
    text = text.replace("underneigh", "underneath")
    text = text.replace("remnants of the test", "remnants of the text")
    text = re.sub(r"\bon no COO\b", "or no COO", text, flags=re.I)
    return re.sub(r"\s{2,}", " ", text).strip()


def norm(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def slug(value):
    token = norm(value).replace(" ", "-")
    return token[:48] or "stamp"


def names(items):
    labelled = [f"the {item}" for item in items]
    if len(labelled) == 1:
        return labelled[0]
    if len(labelled) == 2:
        return f"{labelled[0]} and {labelled[1]}"
    return ", ".join(labelled[:-1]) + ", and " + labelled[-1]


def parse_cell(raw):
    text = fix_text(raw)
    match = re.match(r"^(?P<factory>.+?)\s*(?:=|:)\s*(?P<detail>.+)$", text)
    if not match:
        return None
    factory = re.sub(r"\s+", " ", match.group("factory")).strip(" .")
    detail = re.sub(r"\s+", " ", match.group("detail")).strip()
    if not factory or not detail:
        return None
    return {"factory": factory, "detail": detail}


def coo_tokens(detail):
    found = []
    if re.search(r"(?i)without the coo", detail):
        found.append("no coo")
    for match in COO_WORD.finditer(detail):
        token = match.group(1).lower()
        if token.startswith("made in "):
            token = token[len("made in "):]
        if token not in found:
            found.append(token)
    return found


def expand_or(item):
    detail = item["detail"]
    parts = re.split(r"\s+or\s+", detail, maxsplit=1, flags=re.I)
    if len(parts) != 2:
        return [item]
    if not coo_tokens(parts[0]) or not coo_tokens(parts[1]):
        return [item]
    location = ""
    for phrase in (
        "on left leg under licensing details",
        "on a raised bar under licensing details on left leg",
        "on left leg",
        "under licensing details",
    ):
        if phrase in parts[0].lower() or phrase in parts[1].lower():
            location = phrase
            break
    copy = ""
    joined = " ".join(parts)
    mark = re.search(r"'©[^']*'", joined)
    if mark:
        copy = mark.group(0)
    out = []
    for part in parts:
        text = part.strip(" .")
        text = re.sub(r"(?i)\s*without the coo\.?$", "no COO", text).strip(" .")
        if (
            location
            and "leg" not in text.lower()
            and "licensing" not in text.lower()
            and len(coo_tokens(text)) == 1
            and len(text) < 40
        ):
            text = f"{text} {location}"
        if copy and copy not in text:
            text = f"{text}. {copy}"
        out.append({"factory": item["factory"], "detail": fix_text(text)})
    return out


def group_key(detail):
    text = detail.lower().replace("'", "").replace("’", "")
    text = re.sub(r"licensing details are less defined\.?", "", text)
    text = re.sub(r"[^a-z0-9© ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def button_label(detail):
    label = detail.strip().rstrip(".")
    label = re.sub(r"\s+", " ", label)
    if len(label) > 140:
        label = label[:137].rstrip() + "..."
    return label


def build_options(cells):
    items = []
    for cell in cells:
        parsed = parse_cell(cell)
        if not parsed:
            continue
        items.extend(expand_or(parsed))
    groups = []
    for item in items:
        key = group_key(item["detail"])
        found = next((group for group in groups if group["key"] == key), None)
        if not found:
            found = {"key": key, "detail": item["detail"], "factories": [], "notes": []}
            groups.append(found)
        if item["factory"] not in found["factories"]:
            found["factories"].append(item["factory"])
        extra = item["detail"]
        if group_key(extra) == key and "less defined" in extra.lower() and extra not in found["notes"]:
            found["notes"].append(extra)
    options = []
    used_ids = set()
    for group in groups:
        factories = group["factories"]
        label = button_label(group["detail"])
        ident = slug(label)
        base = ident
        n = 2
        while ident in used_ids:
            ident = f"{base}-{n}"
            n += 1
        used_ids.add(ident)
        follow_ups = []
        if any("less defined" in note.lower() for note in group["notes"]):
            defined = []
            for item in items:
                if item["factory"] not in factories:
                    continue
                if group_key(item["detail"]) != group["key"]:
                    continue
                if "less defined" in item["detail"].lower() and item["factory"] not in defined:
                    defined.append(item["factory"])
            ordinary = [name for name in factories if name not in defined]
            if defined and ordinary:
                follow_ups = [
                    {
                        "id": "less-defined",
                        "label": "The licensing details are less defined",
                        "factories": defined,
                        "conclusion": f"That is {names(defined)}. The licensing details are less defined.",
                        "sure": len(defined) == 1,
                    },
                    {
                        "id": "ordinary-licensing",
                        "label": "The licensing details look ordinary",
                        "factories": ordinary,
                        "conclusion": f"That is {names(ordinary)}. The licensing line is the ordinary one.",
                        "sure": len(ordinary) == 1,
                    },
                ]
        if follow_ups:
            conclusion = ""
            sure = False
        elif len(factories) == 1:
            conclusion = f"That is the {factories[0]}. {label}."
            sure = True
        else:
            conclusion = (
                f"That stamp is shared by {names(factories)}. {label}. "
                "I'm not sure which of those it is from the stamp alone."
            )
            sure = False
        low = label.lower()
        if "no coo" in low or "scar" in low:
            coo = "No COO"
        elif "china" in low:
            coo = "China"
        elif "taiwan" in low:
            coo = "Taiwan"
        elif "japan" in low:
            coo = "Japan"
        elif "hong kong" in low:
            coo = "Hong Kong"
        else:
            coo = ""
        options.append({
            "id": ident,
            "label": label,
            "coo": coo,
            "factories": factories,
            "examples": [label],
            "conclusion": conclusion,
            "sure": sure,
            "followUps": follow_ups,
        })
    return options


def factories_in(line):
    low = f" {norm(line)} "
    found = []
    for name in FACTORY_NAMES:
        if f" {name} " in low and name not in found:
            found.append(name)
    # Drop a short name when a longer one on the same line already covers it.
    kept = []
    for name in found:
        if any(other != name and name in other for other in found):
            continue
        kept.append(name)
    return kept


def category_of(line):
    for name, pattern in CATEGORIES:
        if pattern.search(line):
            return name
    return ""


def extract_tells(record):
    lines = []
    for family in record.get("families") or []:
        lines.extend(family.get("lines") or [])
    file_name = record.get("file") or ""
    if file_name:
        path = ROOT / "data" / file_name
        if path.exists():
            for raw in path.read_text(errors="replace").splitlines():
                line = re.sub(r"\s+", " ", raw).strip(" -\t")
                if line:
                    lines.append(line)
    tells = []
    seen = set()
    for line in lines:
        if len(line) < 24 or len(line) > 180:
            continue
        if re.search(r"(?i)^(above you can see|don.?t rely|further reading|accessories)$", line):
            continue
        factories = factories_in(line)
        if len(factories) != 1:
            continue
        if not norm(line).startswith(factories[0]):
            continue
        category = category_of(line)
        if not category:
            continue
        detail = re.sub(r"\s+", " ", line).strip()
        key = (category, norm(detail))
        if key in seen:
            continue
        seen.add(key)
        tells.append({
            "category": category,
            "detail": detail,
            "factories": [factories[0].title() if factories[0] not in {"pbp", "lili ledy"} else ("PBP" if factories[0] == "pbp" else "Lili Ledy")],
            "where": WHERE[category],
        })
        if len(tells) >= 24:
            break
    # Title-case lost "Kader China" style. Restore from the known list.
    pretty = {
        "kader china": "Kader China",
        "lili ledy": "Lili Ledy",
        "top toys": "Top Toys",
        "unitoy": "Unitoy",
        "glasslite": "Glasslite",
        "meccano": "Meccano",
        "taiwan": "Taiwan",
        "kader": "Kader",
        "smile": "Smile",
        "poch": "Poch",
        "pbp": "PBP",
        "takara": "Takara",
    }
    for tell in tells:
        tell["factories"] = [pretty.get(norm(name), name) for name in tell["factories"]]
    return tells


def load_sheet():
    wb = openpyxl.load_workbook(SHEET, data_only=True)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[1]:
            continue
        stamps = [fix_text(cell) for cell in row[10:] if cell and str(cell).strip()]
        rows.append({
            "name": str(row[1]).strip(),
            "url": str(row[6] or "").strip(),
            "stamps": stamps,
        })
    return rows


def write_report(figures, edited_names):
    only_coo = []
    with_tells = []
    for fig in figures:
        cats = []
        for tell in fig.get("tells") or []:
            if tell["category"] not in cats:
                cats.append(tell["category"])
        if cats:
            with_tells.append((fig["name"], cats))
        else:
            only_coo.append(fig["name"])
    lines = [
        "# Cross-reference tells for variant identification",
        "",
        "The identify flow asks the country stamp first. When that stamp still matches more than one factory, it asks the next tell below. A figure with no tell lines has only the COO stamp.",
        "",
        f"- Figures: {len(figures)}",
        f"- Figures with a tell besides the COO stamp: {len(with_tells)}",
        f"- Figures with only COO data: {len(only_coo)}",
        f"- Rows the owner edited on 11 Oct 2026: {len(edited_names)}",
        "",
        "Edited rows: " + "; ".join(edited_names) + ".",
        "",
        "## Figures with tells",
        "",
    ]
    for name, cats in with_tells:
        lines.append(f"- {name}: {', '.join(cats)}")
    lines.extend(["", "## Figures with only COO data", ""])
    for name in only_coo:
        lines.append(f"- {name}")
    lines.append("")
    REPORT.write_text("\n".join(lines))
    art = Path("/opt/cursor/artifacts/coo-cross-tells.md")
    art.parent.mkdir(parents=True, exist_ok=True)
    art.write_text("\n".join(lines))
    print(f"tells {len(with_tells)} only_coo {len(only_coo)} edited {len(edited_names)}")


def main():
    payload = json.loads(COO.read_text())
    by_url = {fig.get("sourceUrl"): fig for fig in payload["figures"]}
    edited = []
    for row in load_sheet():
        record = by_url.get(row["url"])
        if not record:
            raise SystemExit(f"no figure for {row['url']} ({row['name']})")
        if not row["stamps"]:
            continue
        options = build_options(row["stamps"])
        if not options:
            raise SystemExit(f"no buttons parsed for {row['name']}")
        record["verified"] = True
        record["hasDetails"] = True
        record["source"] = "owner"
        record["sourceNote"] = "Owner of variantvillain.com, 11 Oct 2026."
        record["whereToLook"] = (
            "Look at the country stamp and the licensing line beside it. "
            "A partial or cut-off country name counts as No COO."
        )
        record["ask"] = "Which stamp do you see?"
        record["options"] = options
        record["ownerStamps"] = row["stamps"]
        record["missing"] = ""
        record.pop("singleFactory", None)
        edited.append(record["name"])
    for record in payload["figures"]:
        if not record.get("source"):
            record["source"] = "variantvillain.com"
        record["tells"] = extract_tells(record)
    from apply_luke_owner import apply_coo_figures
    apply_coo_figures(payload["figures"])
    payload["ownerStampNote"] = (
        "Six figures were revised by the owner on 11 Oct 2026. "
        "Unchanged rows keep source variantvillain.com, or the earlier owner sheet where that row was already owner-verified."
    )
    COO.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    owner = json.loads(OWNER_JSON.read_text())
    kept = [fig for fig in owner.get("figures") or [] if fig.get("name") not in edited]
    for name in edited:
        record = next(fig for fig in payload["figures"] if fig["name"] == name)
        kept.append({
            "name": name,
            "recorded": "2026-10-11",
            "source": "owner",
            "whereToLook": record["whereToLook"],
            "ask": record["ask"],
            "stamps": record["ownerStamps"],
            "options": record["options"],
            "missing": "",
        })
    owner["figures"] = kept
    owner["reviewNote"] = "11 Oct 2026 review replaced the stamp cells of the edited figures. Blank rows were left as previously exported."
    OWNER_JSON.write_text(json.dumps(owner, indent=2, ensure_ascii=False) + "\n")
    from apply_luke_owner import sync_owner_stamps
    luke = next((fig for fig in payload["figures"] if fig.get("name") == "Luke Skywalker"), None)
    if luke:
        sync_owner_stamps(luke)
    write_report(payload["figures"], edited)
    print("edited", ", ".join(edited))


if __name__ == "__main__":
    main()
