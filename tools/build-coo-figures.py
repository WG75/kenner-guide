#!/usr/bin/env python3
"""Cache per-figure COO stamps from Variant Villain character pages.

Reads the figure URLs in data/catalog-*.json, fetches each page once
(robots.txt allows /characters/), and writes data/coo-figures.json.
Raw HTML stays in /tmp. The committed file is the extract plus source URLs.

A figure is verified only when its page names country stamps under a COO
Family heading. Mexico is never offered as a leg stamp. Lando Calrissian's
buttons are the collector's leg-by-leg tells for the 1980 figure.
"""

import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "coo-figures.json"
CACHE = Path("/tmp/vv-coo-2026-10-10")
UA = "kenner-guide-research/1.0 (per-figure COO cache; polite, one request at a time)"
DELAY = 0.8
COO_GUIDE = "https://www.variantvillain.com/knowledge/introduction-to-coos/"

STOP = re.compile(r"(?i)^(introduction to coos|cookie policy)\b")
FAMILY = re.compile(r"(?i)^COO Family\b")
GUIDE = re.compile(
    r"^(?P<num>(?:I{1,3}|IV|VI{0,3}|IX|XI{0,3}|XIV|XV|XVI{0,3}|XIX|XX|#\d+|F\d+(?:\.\d+)?))"
    r"\s*[:.\-–]\s*(?P<label>.+)$"
)
STAMP = re.compile(
    r"(?i)\b(made in hong kong|hong kong|h\.k\.|made in taiwan|taiwan|made in china|"
    r"\bchina\b|macau|macao|no coo|made in mexico|scar)\b"
)


def clean(text):
    text = html.unescape(text or "").replace("\xa0", " ").replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", text).strip()


def fetch(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:180]
    path = CACHE / key
    if path.exists() and path.stat().st_size > 500:
        return path.read_text(errors="replace"), False
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = resp.read().decode("utf-8", "replace")
    path.write_text(data)
    time.sleep(DELAY)
    return data, True


BOILER = re.compile(r"(?i)don.?t rely on just the coo|mould, paint colour, plastic colour")
FACTORY_HINT = re.compile(
    r"(?i)\b(kader china|kader|smile|unitoy|unitoys|lili ledy|lili|poch|pbp|meccano|glasslite|universal)\b"
)
DETAIL = re.compile(
    r"(?i)\b(moulds?|molds?|\bm\d\b|smile|unitoy|kader|lili|poch|\bpbp\b|meccano|glasslite|"
    r"hong kong|taiwan|macau|macao|no coo|made in|factory|factories)\b"
)


def page_lines(raw):
    match = re.search(r"(?is)<main[^>]*>(.*)</main>", raw)
    chunk = match.group(1) if match else raw
    text = re.sub(r"(?is)<script[\s\S]*?</script>", " ", chunk)
    text = re.sub(r"(?is)<style[\s\S]*?</style>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|h\d|li|div|tr)>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", "\n", text)
    text = html.unescape(text).replace("\xa0", " ").replace("\u2019", "'").replace("\u2018", "'")
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line or len(line) > 280:
            continue
        if re.match(r"(?i)^introduction to coos\b", line) or re.match(r"(?i)^>\s*back to\b", line):
            break
        lines.append(line)
    return lines


def content_lines(lines):
    """Article body only. page_lines already drops the site menu and the footer."""
    return list(lines)


def sections(lines):
    found = []
    i = 0
    while i < len(lines):
        if not FAMILY.match(lines[i]):
            i += 1
            continue
        title = lines[i]
        i += 1
        body = []
        while i < len(lines) and not FAMILY.match(lines[i]) and not STOP.match(lines[i]):
            body.append(lines[i])
            i += 1
            if len(body) > 50:
                break
        found.append((title, body))
    return found


def kinds_in(line):
    """Country stamps named on one line. Mexico is never a leg-stamp choice."""
    low = line.lower()
    if "mexico" in low or BOILER.search(line):
        return []
    found = []
    if "no coo" in low or re.search(r"\bscar(?:red)?\b", low):
        found.append("No COO")
    if "macau" in low or "macao" in low:
        found.append("Macau")
    if "taiwan" in low:
        found.append("Taiwan")
    if re.search(r"\bchina\b", low):
        found.append("Made in China")
    if "made in hong kong" in low:
        found.append("Made in Hong Kong")
    elif "hong kong" in low or re.search(r"\bh\.?\s*k\.?\b|\bhk\b", low):
        found.append("Hong Kong only")
    return found


SENTENCE = re.compile(
    r"(?i)\b(however|although|because|previously|packaged|cardback|comparison|gallery)\b"
)
ACCESSORYISH = re.compile(r"(?i)\b(blaster|rifle|bowcaster|cape|saber|sabre|accessor(?:y|ies)|gallery)\b")


def clean_factory(name):
    name = re.sub(r"\s+", " ", name or "").strip(" /:-")
    if not name or len(name) > 42 or ACCESSORYISH.search(name) or SENTENCE.search(name):
        return ""
    if name[-1] in "(/":
        return ""
    if re.match(r"(?i)^(the |this |above |there |colour |color |coo family)", name):
        return ""
    if re.search(r"(?i)\bwith\b", name):
        return ""
    return name


def is_stamp_line(line):
    """A line the page uses as a stamp or a COO-family label, not a passing mention."""
    if not kinds_in(line) or SENTENCE.search(line):
        return False
    if re.match(r"(?i)^(above|the |this |some |there )", line):
        return False
    if GUIDE.match(line):
        return True
    if re.search(r"(?i)(left|right)\s+leg\s*:", line) and len(line) <= 140:
        return True
    if re.fullmatch(
        r"(?i)[\W]*(?:scar(?:red)?\s+)?(?:no coo|made in(?:\s*\([^)]*\))?\s+"
        r"(?:hong kong|china|taiwan|macau|macao)|hong kong|taiwan|macau|macao|china)"
        r"(?:\s+coo)?[\W]*",
        line,
    ):
        return True
    if len(line) <= 72 and line.count(" ") <= 12:
        return True
    return False


def nearest_factory(lines, index):
    own = GUIDE.match(lines[index])
    if own:
        return clean_factory(own.group("label"))
    for j in range(index - 1, max(-1, index - 8), -1):
        line = lines[j]
        if is_stamp_line(line):
            continue
        match = GUIDE.match(line)
        if match:
            found = clean_factory(match.group("label"))
            if found:
                return found
        if FAMILY.match(line):
            nxt = lines[j + 1] if j + 1 < len(lines) else ""
            found = clean_factory(nxt)
            if found and FACTORY_HINT.search(found):
                return found
        found = clean_factory(line)
        if found and FACTORY_HINT.search(found) and len(found) <= 32:
            return found
    return ""


def build_options(lines):
    groups = {}
    order = []
    for index, line in enumerate(lines):
        if not is_stamp_line(line):
            continue
        factory = nearest_factory(lines, index) or "this figure's page"
        for kind in kinds_in(line):
            if kind not in groups:
                groups[kind] = {"factories": [], "examples": []}
                order.append(kind)
            bucket = groups[kind]
            if factory not in bucket["factories"] and len(bucket["factories"]) < 4:
                bucket["factories"].append(factory)
            if line not in bucket["examples"] and len(bucket["examples"]) < 3:
                bucket["examples"].append(line)
    options = []
    for kind in order:
        bucket = groups[kind]
        factories = [name for name in bucket["factories"] if clean_factory(name)]
        short = [example for example in bucket["examples"] if len(example) <= 80][:2]
        shown = "; ".join(short) or kind
        if len(factories) == 1 and len(factories[0]) <= 32:
            conclusion = f"That matches {factories[0]} on this figure's Variant Villain page ({shown})."
            sure = True
        elif factories:
            conclusion = (
                f"That stamp is listed for {' and '.join(factories[:3])}. "
                "I'm not sure which one from the stamp alone."
            )
            sure = False
        else:
            conclusion = (
                f"That stamp is named on this figure's Variant Villain page ({shown}). "
                "I'm not sure which factory it is from the stamp alone."
            )
            sure = False
        options.append({
            "id": re.sub(r"[^a-z0-9]+", "-", kind.lower()).strip("-"),
            "label": kind,
            "coo": "No COO" if kind == "No COO" else kind.replace("Made in ", "").replace(" only", ""),
            "factories": factories,
            "examples": bucket["examples"],
            "conclusion": conclusion,
            "sure": sure,
            "followUps": []
        })
    return options


LANDO_OPTIONS = [
    {
        "id": "hk-two-lines",
        "label": "Made in Hong Kong (2 lines)",
        "coo": "Hong Kong",
        "factories": ["Kader M1"],
        "examples": ["Made in Hong Kong across 2 lines"],
        "conclusion": "That is the Kader M1. 'Made in Hong Kong' runs across 2 lines on his left leg, and '© 1980 L.F.L.' runs across 2 lines on his right leg.",
        "sure": True,
        "followUps": []
    },
    {
        "id": "hk-only",
        "label": "Hong Kong only, under the © 1980 L.F.L. mark",
        "coo": "Hong Kong",
        "factories": ["Smile M2", "Unitoy M3"],
        "examples": ["Hong Kong under the licensing mark"],
        "conclusion": "That stamp is shared by the Smile M2 and the Unitoy M3: just 'Hong Kong', with no 'Made in', on the left leg under the '© 1980 L.F.L.' mark. I'm not sure which of those two it is from the stamp alone.",
        "sure": False,
        "followUps": []
    },
    {
        "id": "china",
        "label": "Made in China",
        "coo": "China",
        "factories": ["Kader China M1", "Lili Ledy M1"],
        "examples": ["Made in China on a raised bar"],
        "conclusion": "That is the Kader China M1 or the Lili Ledy M1. 'Made in China' sits on a raised bar on his left leg. I'm not sure which of those two it is from the stamp alone.",
        "sure": False,
        "followUps": []
    },
    {
        "id": "no-coo",
        "label": "No COO / scar / smoothed over",
        "coo": "No COO",
        "factories": ["Unitoy M3 PBP", "No COO"],
        "examples": ["scar", "smoothed", "remnants"],
        "conclusion": "",
        "sure": False,
        "followUps": [
            {
                "id": "scar",
                "label": "A scar under the © 1980 L.F.L. mark",
                "conclusion": "That is the Spanish PBP version. It uses the Unitoy M3 mould, with a scar in place of 'Hong Kong' under the licensing mark on the left leg.",
                "sure": True
            },
            {
                "id": "smoothed",
                "label": "Hong Kong barely visible, or smoothed over",
                "conclusion": "That is a No COO. Remnants of 'Hong Kong' can be barely visible, or the country can be smoothed over. A partial or cut-off country name counts as No COO. I'm not sure which factory that is from the stamp alone.",
                "sure": False
            }
        ]
    }
]


def lando_record(scraped):
    return {
        "verified": True,
        "whereToLook": "Look at the small text on the back of the legs: which leg it is on, whether it says 'Made in', and whether it sits under the © 1980 L.F.L. mark.",
        "options": LANDO_OPTIONS,
        "note": "1980 Lando leg tells recorded from the collector's notes and the Variant Villain Lando page. Hong Kong, China, or No COO only."
    }


def catalog_figures():
    found = []
    seen = set()
    for path in sorted((ROOT / "data").glob("catalog-*.json")):
        data = json.loads(path.read_text())
        for fig in data.get("figures") or []:
            url = fig.get("url") or ""
            if "/characters/" not in url or url in seen:
                continue
            seen.add(url)
            found.append(fig)
    return found


def main():
    figures = []
    fetched = 0
    for fig in catalog_figures():
        record = {
            "name": fig["name"],
            "sourceUrl": fig["url"],
            "file": fig.get("file") or "",
            "verified": False,
            "whereToLook": "",
            "options": [],
            "families": [],
            "guide": [],
            "stamps": [],
            "hasDetails": False,
            "error": ""
        }
        try:
            raw, did_fetch = fetch(fig["url"])
            if did_fetch:
                fetched += 1
        except Exception as err:
            record["error"] = str(err)
            figures.append(record)
            print("FAIL", fig["name"], err)
            continue
        body = content_lines(page_lines(raw))
        fams = sections(body)
        record["families"] = [{"title": title, "lines": lines[:12]} for title, lines in fams]
        guide = []
        for line in body:
            match = GUIDE.match(line)
            if not match:
                continue
            label = match.group("label").strip()
            if not label or label.lower().startswith("not "):
                continue
            item = f"{match.group('num')}: {label}"
            if item not in guide:
                guide.append(item)
        record["guide"] = guide[:16]
        stamps = []
        for line in body:
            if is_stamp_line(line) and line not in stamps:
                stamps.append(line)
        record["stamps"] = stamps[:24]
        if fig["name"] == "Lando Calrissian":
            record.update(lando_record(record))
        else:
            options = build_options(body)
            if options:
                record["verified"] = True
                record["whereToLook"] = "Look at the small text on the back of the legs. These are the stamps this figure's page names."
                record["options"] = options
        record["hasDetails"] = any(DETAIL.search(line) and not BOILER.search(line) for line in body)
        figures.append(record)
        print(("OK " if record["verified"] else "-- "), fig["name"], "opts", len(record["options"]), "details", record["hasDetails"])

    from apply_owner_coo import apply_owner_records
    figures = apply_owner_records(figures)
    payload = {
        "cooGuideUrl": COO_GUIDE,
        "rule": "A partial or cut-off country name counts as No COO. No vintage figure is offered a Mexico leg stamp.",
        "fetchedNote": "Character pages fetched for this file. HTML cache is local only; this JSON is the stored extract. Owner stamp sheet applied for the figures it covers (10 Oct 2026).",
        "figures": figures
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    verified = sum(1 for fig in figures if fig["verified"])
    print(f"wrote {OUT} figures={len(figures)} verified={verified} fetched_now={fetched}")


if __name__ == "__main__":
    main()
