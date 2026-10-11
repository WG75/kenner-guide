#!/usr/bin/env python3
"""Scrape Variant Villain figure and accessory guides into factory-match records.

robots.txt allows /characters/ and /accessory-guide/ (only /wp-admin/ is
disallowed). Imperial Gunnery's robots.txt has no Disallow. HTML stays in
/tmp. This file writes the extract, with a source URL on every record.

Owner-verified COO stamps and the Skiff Vibro Staff override the scrape.
"""

import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "factory-match.json"
REPORT = ROOT / "docs" / "cross-reference-coverage.md"
ARTIFACT = Path("/opt/cursor/artifacts/cross-reference-coverage.md")
CACHE = Path("/tmp/vv-xref-2026-10-11")
UA = "kenner-guide-research/1.0 (factory-match cache; polite, one request at a time)"
DELAY = 0.45

FACTORIES = [
    "Kader China", "Lili Ledy", "Top Toys", "Unitoy", "Glasslite", "Meccano",
    "Kader", "Smile", "Poch", "PBP", "Takara", "Taiwan", "Kenner",
]
FACTORY_RE = re.compile(
    r"(?i)\b(kader china|lili ledy|top toys|unitoy|glasslite|meccano|kader|smile|poch|pbp|takara|taiwan|kenner)\b"
)
WHERE = {
    "hair": "Look at the hair colour.",
    "paint": "Look at the paint colour.",
    "plastic": "Look at the plastic colour or shade.",
    "head": "Look at the head.",
    "mould": "Look at the mould: shape, proportions, tip or hilt.",
    "date": "Look at the date stamp.",
    "cavity": "Look for a cavity mark or a mark by the screw.",
    "assembly": "Look at how the parts are assembled.",
    "cardback": "If it is still carded, which card is it on?",
    "accessory": "Look at the accessory that was packed with it.",
    "coo": "Look at the country stamp.",
    "letter": "Look for a moulded letter or number.",
    "gloss": "Look at the gloss or flash.",
    "pin": "Look for an ejector-pin mark.",
}
CATS = [
    ("hair", re.compile(r"(?i)\bhair\b")),
    ("paint", re.compile(r"(?i)\bpaint\b|\beyes\b|\btrousers\b|\bboots\b|\bscarf\b")),
    ("plastic", re.compile(r"(?i)\bplastic\b|\bopaque\b|\btranslucent\b|\bflesh\b|\bshade\b|\bgrey\b|\bgray\b|\bblack\b|\bblue\b")),
    ("head", re.compile(r"(?i)\bhead\b|\bface\b")),
    ("date", re.compile(r"(?i)\bdate stamp\b|\bdated\b")),
    ("cavity", re.compile(r"(?i)\bcavity\b")),
    ("pin", re.compile(r"(?i)\bejector|\bpin mark\b")),
    ("letter", re.compile(r"(?i)\bmoulded letter\b|\bletter [a-z]\b|\bnumber\b")),
    ("gloss", re.compile(r"(?i)\bgloss\b|\bflash\b|\bshiny\b")),
    ("mould", re.compile(r"(?i)\bmould\b|\bmold\b|\bsculpt\b|\btip\b|\bhilt\b|\bproportion\b")),
    ("assembly", re.compile(r"(?i)\bassembl|\bmixed-up\b")),
    ("cardback", re.compile(r"(?i)\b\d{1,3}[a-e]?-backs?\b|\btrilogo\b|\bcarded\b|\bcardback\b")),
    ("accessory", re.compile(r"(?i)\bcame with\b|\bpacked with\b|\bpackaged with\b|\bpaired with\b")),
]
SKIP_HEAD = re.compile(r"(?i)bootleg|reproduction|\brepro\b|reissue|display case|further reading")
CAME = re.compile(r"(?i)\b(came with|packed with|packaged with|paired with)\b")
MOULD_RE = re.compile(r"\bM(\d+[a-z]?)\b", re.I)
IG_PAGES = [
    "https://imperialgunnery.com/rifles.htm",
    "https://imperialgunnery.com/clothcapesskirts.htm",
    "https://imperialgunnery.com/other-accessories.htm",
    "https://imperialgunnery.com/staffs-axes.htm",
    "https://imperialgunnery.com/otherweapons.htm",
    "https://imperialgunnery.com/helmets-hoods.htm",
    "https://imperialgunnery.com/belts.htm",
]


def clean(text):
    text = html.unescape(text or "").replace("\xa0", " ").replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", text).strip()


def norm(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", norm(value)).strip("-")


def pretty_factory(name):
    key = norm(name)
    for factory in FACTORIES:
        if norm(factory) == key:
            return factory
    return clean(name).title()


def factories_in(text):
    text = re.sub(r"(?i)\bk\.?\s*china\b", "Kader China", text or "")
    found = []
    for part in re.split(r"[/|]", text):
        part_found = []
        for match in FACTORY_RE.finditer(part):
            factory = pretty_factory(match.group(1))
            if factory not in part_found:
                part_found.append(factory)
        for factory in part_found:
            if any(factory != other and norm(factory) in norm(other) for other in part_found):
                continue
            if factory not in found:
                found.append(factory)
    return found


def category_of(line):
    for name, pattern in CATS:
        if pattern.search(line):
            return name
    return ""


def cache_path(url):
    key = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:180]
    return CACHE / key


def fetch(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = cache_path(url)
    if path.exists() and path.stat().st_size > 400:
        return path.read_text(errors="replace"), False
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = resp.read().decode("utf-8", "replace")
    path.write_text(data)
    time.sleep(DELAY)
    return data, True


def page_lines(raw):
    match = re.search(r"(?is)<(?:main|body)[^>]*>(.*)</(?:main|body)>", raw)
    chunk = match.group(1) if match else raw
    chunk = re.sub(r"(?is)<script[\s\S]*?</script>", " ", chunk)
    chunk = re.sub(r"(?is)<style[\s\S]*?</style>", " ", chunk)
    chunk = re.sub(r"(?i)<h([1-6])[^>]*>", r"\n[[H\1]] ", chunk)
    chunk = re.sub(r"(?i)</h[1-6]>", "\n", chunk)
    chunk = re.sub(r"(?i)<br\s*/?>", "\n", chunk)
    chunk = re.sub(r"(?i)</(p|li|div|tr|td|h\d)>", "\n", chunk)
    chunk = re.sub(r"(?is)<[^>]+>", "\n", chunk)
    text = html.unescape(chunk).replace("\xa0", " ").replace("\u2019", "'").replace("\u2018", "'")
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip(" -\t")
        if line:
            lines.append(line)
    return lines


def load_catalog():
    figures, accessories = [], []
    for path in sorted((ROOT / "data").glob("catalog-*.json")):
        data = json.loads(path.read_text())
        figures.extend(data.get("figures") or [])
        accessories.extend(data.get("accessories") or [])
    return figures, accessories


def debut_accessories():
    data = json.loads((ROOT / "data" / "kenner-debut-figures.json").read_text())
    return {fig["name"]: fig.get("accessories") or [] for fig in data["figures"]}


def coo_records():
    data = json.loads((ROOT / "data" / "coo-figures.json").read_text())
    return {fig["name"]: fig for fig in data["figures"]}


def factory_matches(candidate, factory):
    cand = norm(candidate)
    fac = norm(factory)
    if not fac or not (cand == fac or cand.startswith(fac + " ")):
        return False
    if "china" in cand and "china" not in fac:
        return False
    if "ledy" in cand and "ledy" not in fac:
        return False
    if "toys" in cand and "toys" not in fac:
        return False
    return True


def tell(category, detail, source):
    detail = clean(detail)
    if len(detail) < 3 or len(detail) > 180:
        return None
    return {
        "category": category,
        "detail": detail,
        "where": WHERE.get(category, "Look at the next detail."),
        "source": source,
    }


def add_tell(bucket, item):
    if not item:
        return
    key = (item["category"], norm(item["detail"]))
    if key in bucket["seen"]:
        return
    bucket["seen"].add(key)
    bucket["tells"].append({k: item[k] for k in ("category", "detail", "where")})


def figure_variants_from_coo(record):
    variants = []
    seen = set()
    for option in record.get("options") or []:
        for factory in option.get("factories") or []:
            label = clean(factory)
            if not label or label in seen:
                continue
            seen.add(label)
            variants.append({
                "id": f"{slug(record['name'])}--{slug(label)}",
                "figure": record["name"],
                "factory": label,
                "mould": mould_of(label),
                "source": record.get("source") or "variantvillain.com",
                "sourceUrl": record.get("sourceUrl") or "",
                "coo": clean(option.get("label") or ""),
                "tells": [],
            })
    if not variants and record.get("singleFactory"):
        label = clean(record["singleFactory"])
        variants.append({
            "id": f"{slug(record['name'])}--{slug(label)}",
            "figure": record["name"],
            "factory": label,
            "mould": "",
            "source": record.get("source") or "variantvillain.com",
            "sourceUrl": record.get("sourceUrl") or "",
            "coo": "",
            "tells": [],
        })
    return variants


def mould_of(label):
    match = re.search(r"\b(M\d+(?:\.\d+)?)\b", label or "", re.I)
    return match.group(1).upper().replace(".0", "") if match else ""


def parse_figure_page(lines):
    """Non-COO tell lines and accessory moulds named with a figure factory."""
    start = 0
    for i, line in enumerate(lines):
        if re.search(r"(?i)figure guide", line):
            start = i
            break
    body = []
    for line in lines[start:]:
        if SKIP_HEAD.search(line) and line.startswith("[[H"):
            break
        body.append(line)
    families = []
    current = {"factories": [], "lines": []}
    for line in body:
        if re.search(r"(?i)coo family", line):
            if current["lines"] or current["factories"]:
                families.append(current)
            current = {"factories": [], "lines": []}
            continue
        if line.startswith("[[H") and not current["factories"]:
            named = factories_in(line)
            if named:
                current["factories"] = named
                continue
        current["lines"].append(line)
    if current["lines"] or current["factories"]:
        families.append(current)
    tells = []
    links = []
    for family in families:
        for line in family["lines"]:
            plain = re.sub(r"^\[\[H\d\]\]\s*", "", line)
            if len(plain) < 12 or plain in {".", "M1", "M2", "M3", "M5", "M8"}:
                continue
            named = factories_in(plain)
            cat = category_of(plain)
            if len(named) == 1 and cat and cat != "accessory" and 0 <= plain.lower().find(norm(named[0]).split()[0]) <= 24:
                item = tell(cat, plain, "variantvillain.com")
                if item:
                    item["factory"] = named[0]
                    tells.append(item)
        # A mould number often sits on the line after "came with".
        joined = [re.sub(r"^\[\[H\d\]\]\s*", "", item) for item in family["lines"]]
        for index, plain in enumerate(joined):
            blob = plain
            nxt = joined[index + 1] if index + 1 < len(joined) else ""
            if re.match(r"(?i)^M\d+[a-z]?\.?$", nxt.strip(" .")) or re.match(r"(?i)^M\d+[a-z]?\b", nxt) and len(nxt) < 16:
                blob = f"{plain} {nxt}"
            if not CAME.search(plain):
                continue
            after = re.split(r"(?i)came with|packed with|packaged with|paired with", blob, maxsplit=1)[-1]
            moulds = []
            for found in MOULD_RE.findall(after):
                mould = re.sub(r"[A-Z]$", "", f"M{found.upper()}")
                if mould not in moulds:
                    moulds.append(mould)
            factories = factories_in(plain)
            if re.search(r"(?i)french trilogo", plain) and "Meccano" not in factories:
                factories.append("Meccano")
            if not factories:
                factories = list(family["factories"])
            if moulds and factories:
                links.append({"factories": factories, "moulds": moulds, "detail": blob[:180]})
    return tells, links


def attach_figure_tells(variants, scraped):
    for variant in variants:
        bucket = {"tells": [], "seen": set()}
        if variant.get("coo"):
            add_tell(bucket, tell("coo", variant["coo"], variant["source"]))
        for item in scraped:
            if factory_matches(variant["factory"], item["factory"]):
                add_tell(bucket, item)
        variant["tells"] = bucket["tells"][:24]
        variant.pop("coo", None)


def parse_accessory_page(name, url, lines):
    variants = []
    current = None
    colours = False
    stopped = False

    def close():
        nonlocal current, colours
        if not current:
            return
        for factory in current["factories"] or ["Unknown"]:
            tells = []
            seen = set()
            bucket = {"tells": tells, "seen": seen}
            for detail in current["colours"]:
                add_tell(bucket, tell("plastic", detail, "variantvillain.com"))
            for detail in current["notes"]:
                cat = category_of(detail) or "mould"
                if cat == "accessory":
                    cat = "mould"
                add_tell(bucket, tell(cat, detail, "variantvillain.com"))
            variants.append({
                "id": f"{slug(name)}--{slug(factory)}-{slug(current['mould'])}",
                "accessory": name,
                "factory": factory,
                "mould": current["mould"],
                "source": "variantvillain.com",
                "sourceUrl": url,
                "tells": tells[:16],
                "cardedWith": [],
            })
        current = None
        colours = False

    for line in lines:
        if re.search(r"(?i)table of contents", line):
            continue
        if line.startswith("[[H") and SKIP_HEAD.search(line):
            stopped = True
        if stopped:
            continue
        heading = re.sub(r"^\[\[H\d\]\]\s*", "", line)
        mould_heading = re.match(r"(?i)^M(\d+)\b", heading)
        produced = re.match(r"(?i)^M(\d+)$", heading) or (mould_heading and "comparison" not in heading.lower() and len(heading) < 8)
        if line.startswith("[[H") and mould_heading and "," not in heading and not re.search(r"(?i)comparison:\s*M\d", heading):
            close()
            current = {"mould": f"M{mould_heading.group(1)}", "factories": factories_in(heading), "colours": [], "notes": []}
            colours = False
            continue
        if current and re.match(r"(?i)^was produced by$", heading):
            continue
        if current and not colours and len(heading) < 48 and not re.search(r"(?i)colou?r|comparison|produced|hong kong", heading):
            named = factories_in(heading)
            if named:
                for factory in named:
                    if factory not in current["factories"]:
                        current["factories"].append(factory)
                continue
        if current and re.search(r"(?i)colou?rs are known|following colou?rs", heading):
            colours = True
            continue
        if current and colours:
            if line.startswith("[[H") or re.match(r"(?i)^M\d+[a-z]?:?$", heading):
                if re.match(r"(?i)^M\d+[a-z]:?$", heading):
                    continue
                if line.startswith("[[H"):
                    colours = False
                    if mould_heading and "," not in heading:
                        close()
                        current = {"mould": f"M{mould_heading.group(1)}", "factories": factories_in(heading), "colours": [], "notes": []}
                    continue
            if 2 < len(heading) < 60 and not heading.endswith("."):
                current["colours"].append(heading)
                continue
        if current and category_of(heading) and 20 < len(heading) < 100 and not line.startswith("[[H"):
            if not re.search(r"(?i)was produced|following colou?r|comparison", heading):
                current["notes"].append(heading)
    close()
    # De-duplicate ids (same factory+mould from a repeated heading).
    merged = {}
    for variant in variants:
        prior = merged.get(variant["id"])
        if not prior:
            merged[variant["id"]] = variant
            continue
        seen = {(t["category"], norm(t["detail"])) for t in prior["tells"]}
        for item in variant["tells"]:
            key = (item["category"], norm(item["detail"]))
            if key not in seen:
                prior["tells"].append(item)
                seen.add(key)
    return list(merged.values())


def resolve_accessory_names(figure, pieces, accessories):
    """Debut piece names to catalog accessory names. Owner rulings win."""
    same = {
        ("luke skywalker", "lightsaber"): ["Telescoping Lightsaber"],
        ("darth vader", "lightsaber"): ["Telescoping Lightsaber"],
        ("ben obi wan kenobi", "lightsaber"): ["Telescoping Lightsaber"],
        ("luke skywalker jedi knight outfit", "handheld lightsaber"): ["Handheld Lightsaber"],
        ("luke skywalker jedi knight outfit", "cloak"): ["Luke Jedi Cloak"],
        ("luke skywalker jedi knight outfit", "palace blaster"): ["Palace Blaster"],
        ("artoo detoo r2 d2 with pop up lightsaber", "lightsaber"): ["Pop-Up Saber"],
        ("han solo", "blaster"): ["Rebel Blaster"],
        ("greedo", "blaster"): ["Rebel Blaster"],
        ("snaggletooth", "blaster"): ["Rebel Blaster"],
        ("han solo hoth outfit", "blaster"): ["Rebel Blaster"],
        ("han solo in trench coat", "blaster"): ["Rebel Blaster"],
        ("luke skywalker x wing pilot", "rebel blaster"): ["Rebel Blaster"],
        ("luke skywalker bespin fatigues", "rebel blaster"): ["Rebel Blaster"],
        ("luke skywalker bespin fatigues", "handheld lightsaber"): ["Handheld Lightsaber"],
        ("death squad commander", "blaster"): ["Imperial Blaster"],
        ("walrus man", "blaster"): ["Imperial Blaster"],
        ("boba fett", "blaster"): ["Imperial Blaster"],
        ("han solo bespin outfit", "blaster"): ["Bespin Blaster"],
        ("lando calrissian", "blaster"): ["Bespin Blaster"],
        ("lobot", "blaster"): ["Bespin Blaster"],
        ("lando calrissian", "cape"): ["Lando Calrissian Cape"],
        ("barada", "skiff vibro staff"): ["Skiff Vibro Staff"],
        ("nikto", "skiff vibro staff"): ["Skiff Vibro Staff"],
        ("yak face", "skiff vibro staff"): ["Skiff Vibro Staff"],
    }
    found = []
    by_norm = {norm(acc["name"]): acc["name"] for acc in accessories}
    for piece in pieces:
        key = (norm(figure), norm(piece))
        if key in same:
            found.extend(same[key])
            continue
        piece_n = norm(piece)
        hits = [acc["name"] for acc in accessories if piece_n and piece_n in norm(acc["name"])]
        if len(hits) == 1:
            found.append(hits[0])
        elif piece_n in by_norm:
            found.append(by_norm[piece_n])
    out = []
    for name in found:
        if name not in out:
            out.append(name)
    return out


def link_carded(figure_variants, links, accessory_variants, accessory_names):
    by_acc = {}
    for variant in accessory_variants:
        by_acc.setdefault(variant["accessory"], []).append(variant)
    for link in links:
        for accessory in accessory_names:
            for mould in link["moulds"]:
                for acc in by_acc.get(accessory, []):
                    if norm(acc["mould"]) != norm(mould):
                        continue
                    for fig in figure_variants:
                        if any(factory_matches(fig["factory"], factory) for factory in link["factories"]):
                            if fig["id"] not in acc["cardedWith"]:
                                acc["cardedWith"].append(fig["id"])


def vibro_axe():
    """The live page states these traits beside the photos. The 2026-10-05 extract names the factory for each."""
    url = "https://www.variantvillain.com/accessory-guide/vibro-axe/"

    def row(factory, mould, tells):
        built = []
        for cat, detail in tells:
            item = tell(cat, detail, "variantvillain.com")
            if item:
                built.append({k: item[k] for k in ("category", "detail", "where")})
        return {
            "id": f"vibro-axe--{slug(factory)}-{slug(mould)}",
            "accessory": "Vibro Axe",
            "factory": factory,
            "mould": mould,
            "source": "variantvillain.com",
            "sourceUrl": url,
            "tells": built,
            "cardedWith": [],
        }

    return [
        row("Unitoy", "M1", [("plastic", "Lighter grey plastic"), ("pin", "A deep ejector-pin mark on the grip, halfway up the handle")]),
        row("Smile", "M2", [("plastic", "Mid grey plastic"), ("pin", "Ejector-pin marks mirrored on either side of the axe")]),
        row("Lili Ledy", "M3", [("letter", "Commonly lettered A or B, or blank"), ("plastic", "Commonly darker grey, with a distinctly lighter grey also produced"), ("mould", "A thicker blade than the Kenner version")]),
    ]


def owner_staff(figure_variants):
    def ids(figure, factory):
        return [v["id"] for v in figure_variants if v["figure"] == figure and factory_matches(v["factory"], factory)]
    smile_with = ids("Barada", "Smile") + ids("Yak Face", "Smile") + ids("Nikto", "Smile")
    ledy_with = ids("Nikto", "Lili Ledy")
    return [
        {
            "id": "skiff-vibro-staff--smile-m1",
            "accessory": "Skiff Vibro Staff",
            "factory": "Smile",
            "mould": "M1",
            "source": "owner",
            "sourceNote": "Owner-verified, 11 Oct 2026. Overrides the Variant Villain Vibro Axe heading for Nikto.",
            "sourceUrl": "https://imperialgunnery.com/staffs-axes.htm",
            "tells": [
                {"category": "plastic", "detail": "Smile grey, lighter than the Lili Ledy staff", "where": "Look at the plastic colour or shade."},
                {"category": "pin", "detail": "An ejector-pin mark can be on either side", "where": "Look for an ejector-pin mark."},
            ],
            "cardedWith": smile_with,
        },
        {
            "id": "skiff-vibro-staff--lili-ledy-m2",
            "accessory": "Skiff Vibro Staff",
            "factory": "Lili Ledy",
            "mould": "M2",
            "source": "owner",
            "sourceNote": "Owner-verified, 11 Oct 2026.",
            "sourceUrl": "https://imperialgunnery.com/staffs-axes.htm",
            "tells": [
                {"category": "plastic", "detail": "Lili Ledy staff is a darker grey than the Kenner/Smile staff", "where": "Look at the plastic colour or shade."},
            ],
            "cardedWith": ledy_with,
        },
    ]


def ig_variants():
    """Accessories Variant Villain does not guide. Labelled imperialgunnery.com."""
    url = {
        "rifle": "https://imperialgunnery.com/rifles.htm",
        "cloth": "https://imperialgunnery.com/clothcapesskirts.htm",
        "other": "https://imperialgunnery.com/other-accessories.htm",
        "staff": "https://imperialgunnery.com/staffs-axes.htm",
        "weapon": "https://imperialgunnery.com/otherweapons.htm",
        "hood": "https://imperialgunnery.com/helmets-hoods.htm",
        "belt": "https://imperialgunnery.com/belts.htm",
    }

    def row(accessory, factory, mould, tells, page, carded=None):
        built = []
        for cat, detail in tells:
            item = tell(cat, detail, "imperialgunnery.com")
            if item:
                built.append({k: item[k] for k in ("category", "detail", "where")})
        return {
            "id": f"{slug(accessory)}--{slug(factory)}-{slug(mould)}",
            "accessory": accessory,
            "factory": factory,
            "mould": mould,
            "source": "imperialgunnery.com",
            "sourceUrl": url[page],
            "tells": built,
            "cardedWith": carded or [],
        }

    return [
        row("4-LOM Rifle", "Kenner", "V1", [("mould", "Original V1 has a circle")], "rifle"),
        row("4-LOM Rifle", "Kenner", "V2", [("mould", "Original V2 has no circle")], "rifle"),
        row("Zuckuss Rifle", "Kenner", "V1", [("mould", "Original V1 Zuckuss Rifle")], "rifle"),
        row("Zuckuss Rifle", "Kenner", "V2", [("mould", "Original V2 Zuckuss Rifle")], "rifle"),
        row("Zuckuss Rifle", "Lili Ledy", "V3", [("plastic", "Lili Ledy V3 Zuckuss Rifle")], "rifle"),
        row("Zuckuss Rifle", "Glasslite", "V4", [("gloss", "V4 is much shinier and was issued with the Glasslite Chewbacca")], "rifle"),
        row("Chief Chirpa Staff", "Kenner", "V1", [("plastic", "Brown Chief Chirpa staff")], "staff"),
        row("Chief Chirpa Staff", "Lili Ledy", "V2", [("letter", "Lili Ledy staff with a moulded letter L")], "staff"),
        row("Chief Chirpa Staff", "Top Toys", "V3", [("mould", "Top Toys Chief Chirpa staff")], "staff"),
        row("Logray Staff", "Kenner", "V1", [("pin", "V1 has three ejector-pin marks")], "staff"),
        row("Logray Staff", "Top Toys", "V2", [("mould", "V2 is the Top Toys sculpt")], "staff"),
        row("Logray Staff", "Kenner", "V3", [("pin", "V3 has two ejector-pin marks, in dark brown and red brown")], "staff"),
        row("Logray Staff", "Kenner", "V4", [("pin", "V4 has no ejector-pin mark")], "staff"),
        row("Rancor Keeper Staff", "Kenner", "V1", [("mould", "Hong Kong original, called a Gaderffii Stick or Vibroblade on Imperial Gunnery. The owner identifies it as a staff")], "weapon"),
        row("Rancor Keeper Staff", "Taiwan", "V2", [("mould", "Taiwan original of the Rancor Keeper staff")], "weapon"),
        row("Rancor Keeper Hood", "Kenner", "V1", [("pin", "Original hood can show an ejector-pin mark")], "hood"),
        row("Rancor Keeper Hood", "Kenner", "V2", [("plastic", "Darker, harder, and no ejector-pin mark")], "hood"),
        row("Lumat Bow", "Kenner", "V1", [("plastic", "Light brown Ewok bow")], "weapon"),
        row("Warok Bow", "Kenner", "V1", [("plastic", "Dark brown Ewok bow")], "weapon"),
        row("Lumat Hood", "Kenner", "V1", [("mould", "Lumat hood")], "hood"),
        row("Warok Hood", "Kenner", "V1", [("mould", "Warok hood")], "hood"),
        row("Lumat Quiver", "Kenner", "V1", [("mould", "Lumat quiver")], "other"),
        row("Warok Quiver", "Kenner", "V1", [("mould", "Warok quiver")], "other"),
        row("Yoda Cloak", "Kenner", "V1", [("plastic", "Yoda original cloth cloak")], "cloth"),
        row("Prune Face Cape", "Kenner", "V1", [("plastic", "Prune Face original cloth cape")], "cloth"),
        row("Squid Head Cape", "Lili Ledy", "V1", [("plastic", "Lili Ledy burgundy Squid Head cloak")], "cloth"),
        row("Princess Leia Poncho Helmet", "Kenner", "V1", [("letter", "Numbers inside include 1 with a dot, 2, 3 and 4"), ("pin", "An ejector-pin mark is recorded")], "hood"),
        row("Princess Leia Poncho Belt", "Kenner", "V1", [("mould", "Two notches, shorter than the Luke poncho belt"), ("letter", "Numbers 6, 7 and 8 are recorded inside the holster")], "belt"),
        row("Luke Skywalker Battle Poncho", "Kenner", "V1", [("plastic", "Original Luke Skywalker battle poncho")], "cloth"),
        row("Luke Skywalker Poncho Belt", "Kenner", "V1", [("mould", "Three notches, longer than the Leia poncho belt")], "belt"),
        row("Luke Stormtrooper Helmet", "Kenner", "V1", [("mould", "Luke Stormtrooper helmet original")], "hood"),
        row("Lando Calrissian General Cape", "Kenner", "V1", [("plastic", "General-pilot cloth cape, separate from the vinyl Bespin cape")], "cloth"),
        row("4-LOM Cloak", "Kenner", "V1", [("plastic", "V1 lining is beige")], "cloth"),
        row("4-LOM Cloak", "Kenner", "V2", [("plastic", "V2 has a less sharp neck cut and a creamy-white lining")], "cloth"),
        row("Klaatu Skiff Force Pike", "Kenner", "V1", [("mould", "A separate piece from the Skiff Vibro Staff. Imperial Gunnery does not list it with Barada, Nikto or Yak Face")], "staff"),
    ]


def write_report(payload):
    figures = {}
    for variant in payload["figureVariants"]:
        figures.setdefault(variant["figure"], []).append(variant)
    with_tells = []
    only_coo = []
    for name, variants in figures.items():
        cats = []
        for variant in variants:
            for item in variant["tells"]:
                if item["category"] != "coo" and item["category"] not in cats:
                    cats.append(item["category"])
        if cats:
            with_tells.append((name, cats))
        else:
            only_coo.append(name)
    acc_with = [v for v in payload["accessoryVariants"] if v["tells"]]
    acc_without = [v for v in payload["accessoryVariants"] if not v["tells"]]
    links = sum(len(v["cardedWith"]) for v in payload["accessoryVariants"])
    acc_names_with = sorted({v["accessory"] for v in acc_with})
    acc_names_without = sorted({v["accessory"] for v in payload["accessoryVariants"] if v["accessory"] not in set(acc_names_with)})
    lines = [
        "# Factory-match cross-reference coverage",
        "",
        "Scraped 11 Oct 2026 from variantvillain.com character pages and accessory guides. robots.txt allows those paths. Imperial Gunnery pages fill accessories Variant Villain does not guide, and those records are labelled imperialgunnery.com. Owner-verified stamps and the Skiff Vibro Staff override the scrape.",
        "",
        f"- Figure records: {len(figures)}",
        f"- Figures with a tell besides the COO stamp: {len(with_tells)} (was 18/104)",
        f"- Figures with only COO data: {len(only_coo)}",
        f"- Accessory variants: {len(payload['accessoryVariants'])}",
        f"- Accessory variants with tells: {len(acc_with)}",
        f"- Accessory variants with no tells: {len(acc_without)}",
        f"- Factory-match links (accessory variant to figure variant): {links}",
        f"- Character pages fetched: {payload['fetched']['characters']}",
        f"- Accessory guide pages fetched: {payload['fetched']['accessories']}",
        "",
        "## Figures with tells besides the COO stamp",
        "",
    ]
    for name, cats in with_tells:
        lines.append(f"- {name}: {', '.join(cats)}")
    lines.extend(["", "## Figures with only COO data", ""])
    for name in only_coo:
        lines.append(f"- {name}")
    lines.extend(["", "## Accessory variants still lacking tells", ""])
    if acc_without:
        for variant in acc_without:
            lines.append(f"- {variant['accessory']} {variant['factory']} {variant['mould']}")
    else:
        lines.append("- None. Every stored accessory variant has at least one tell.")
    lines.extend(["", "## Accessories with no variant record", ""])
    catalog_names = payload.get("catalogAccessories") or []
    stored = {v["accessory"] for v in payload["accessoryVariants"]}
    missing = [name for name in catalog_names if name not in stored]
    if missing:
        for name in missing:
            lines.append(f"- {name}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Accessories whose variants have tells", ""])
    for name in acc_names_with:
        count = sum(1 for v in acc_with if v["accessory"] == name)
        lines.append(f"- {name}: {count}")
    if acc_names_without:
        lines.extend(["", "## Accessory names with a record but no tells", ""])
        for name in acc_names_without:
            lines.append(f"- {name}")
    text = "\n".join(lines) + "\n"
    REPORT.write_text(text)
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(text)
    print(
        f"figures {len(figures)} with_tells {len(with_tells)} only_coo {len(only_coo)} "
        f"acc {len(payload['accessoryVariants'])} acc_tells {len(acc_with)} links {links}"
    )


def main():
    robots = fetch("https://www.variantvillain.com/robots.txt")[0]
    if re.search(r"(?i)disallow:\s*/(?:characters|accessory-guide)", robots):
        raise SystemExit("robots.txt disallows the guides")
    figures, accessories = load_catalog()
    debut = debut_accessories()
    coo = coo_records()
    fetched = {"characters": 0, "accessories": 0, "gunnery": 0}
    figure_variants = []
    page_links = {}
    for fig in figures:
        raw, live = fetch(fig["url"])
        fetched["characters"] += 1
        if live:
            print("fetched", fig["url"])
        record = coo.get(fig["name"]) or {"name": fig["name"], "sourceUrl": fig["url"], "options": []}
        variants = figure_variants_from_coo(record)
        if not variants:
            variants = [{
                "id": f"{slug(fig['name'])}--unspecified",
                "figure": fig["name"],
                "factory": "Unspecified",
                "mould": "",
                "source": "variantvillain.com",
                "sourceUrl": fig["url"],
                "coo": "",
                "tells": [],
            }]
        for variant in variants:
            variant["sourceUrl"] = fig["url"]
        tells, links = parse_figure_page(page_lines(raw))
        attach_figure_tells(variants, tells)
        figure_variants.extend(variants)
        page_links[fig["name"]] = links
    accessory_variants = []
    for acc in accessories:
        if not acc.get("url"):
            continue
        raw, live = fetch(acc["url"])
        fetched["accessories"] += 1
        if live:
            print("fetched", acc["url"])
        accessory_variants.extend(parse_accessory_page(acc["name"], acc["url"], page_lines(raw)))
    for url in IG_PAGES:
        raw, live = fetch(url)
        fetched["gunnery"] += 1
        if live:
            print("fetched", url)
        if "Disallow" in raw[:200] and "User-agent" in raw[:200]:
            raise SystemExit(f"unexpected robots body for {url}")
    accessory_variants.extend(vibro_axe())
    accessory_variants = [v for v in accessory_variants if v["accessory"] != "Skiff Vibro Staff"]
    accessory_variants.extend(owner_staff(figure_variants))
    accessory_variants.extend(ig_variants())
    for fig in figures:
        names = resolve_accessory_names(fig["name"], debut.get(fig["name"], []), accessories)
        mine = [v for v in figure_variants if v["figure"] == fig["name"]]
        link_carded(mine, page_links.get(fig["name"], []), accessory_variants, names)
    payload = {
        "fetchedOn": "2026-10-11",
        "rule": "Owner-verified data overrides scraped Variant Villain data. A partial COO counts as No COO. The accessory factory is a separate identification from the figure factory.",
        "fetched": fetched,
        "catalogAccessories": [acc["name"] for acc in accessories],
        "figureVariants": figure_variants,
        "accessoryVariants": accessory_variants,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    write_report(payload)


if __name__ == "__main__":
    main()
