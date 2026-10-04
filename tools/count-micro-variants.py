#!/usr/bin/env python3
"""Attach pictured sub-variant counts to the variant-count snapshot.

A family is still one roman-numeral manufacturer/region column. A version
is one pictured line in that family's combination list (the lists introduced
as "left to right"). Cape, sabre and accessory sections are not versions.
Bootlegs are not versions. A list that only repeats lines already counted
is left out.

The HTML cache is local and is not committed. If it is missing, this script
exits without changing the snapshot.
"""

import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data-source" / "vv-variant-counts.json"
CACHE = Path("/tmp/vv-live-2026-10-04")

MONTH = (
    "January|February|March|April|May|June|July|August|September|"
    "October|November|December"
)


def norm(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = unescape(text)
    text = (
        text.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u00a0", " ")
        .replace("\u00e4", "a")
    )
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip()


def cache_path(url):
    key = url.rstrip("/").replace("https://", "https-").replace(".", "-").replace("/", "-")
    return CACHE / key


def list_items(ul_html):
    items = []
    for raw in re.findall(r"<li[^>]*>([\s\S]*?)</li>", ul_html, flags=re.I):
        raw = re.split(r"<ul", raw, maxsplit=1, flags=re.I)[0]
        text = norm(raw)
        if len(text) < 3:
            continue
        if re.fullmatch(rf"(?:{MONTH})\s+\d{{1,2}},\s+\d{{4}}", text):
            continue
        items.append(text)
    return items


def parse_families(html):
    main_match = re.search(r"<main[\s\S]*?</main>", html, flags=re.I)
    main = main_match.group(0) if main_match else html
    parts = re.split(r"(<h2[^>]*>[\s\S]*?</h2>)", main, flags=re.I)
    families = []
    current = None
    for part in parts:
        if re.match(r"<h2", part, flags=re.I):
            title = norm(part)
            heading = re.match(r"COO\s+Family\s+([IVXLCDM]+)\s*:?", title, flags=re.I)
            if heading:
                current = {"num": heading.group(1).upper(), "label": "", "html": ""}
                families.append(current)
                continue
            if current is not None and not current["label"]:
                current["label"] = title
                continue
        if current is not None:
            current["html"] += part

    parsed = []
    page_seen = set()
    for family in families:
        items = []
        previous_single = False
        previous_taken = False
        last = 0
        for match in re.finditer(r"<ul[\s\S]*?</ul>", family["html"], flags=re.I):
            gap = norm(family["html"][last:match.start()])
            last = match.end()
            low = gap.lower()
            combo_at = max(low.rfind("left to right"), low.rfind("combination"))
            has_combo = combo_at >= 0
            after = gap[combo_at:] if has_combo else ""
            window = low[max(0, combo_at - 60):combo_at + 30] if has_combo else low
            bootleg = bool(re.search(r"bootleg|unart|model trem", window))
            accessory_after = bool(
                re.search(r"\bACCESSORIES\b|\bCAPES?\b|\bSABRES?\b|\bLIGHTSAB", after)
            )
            heading_stop = (
                "key detail" in low
                or bool(re.search(r"\bACCESSORIES\b|\bCAPES?\b|\bSABRES?\b|\bLIGHTSAB", gap))
            )
            batch = list_items(match.group(0))
            single = len(batch) == 1
            # A short "NO COO:" label between two pictured lists is still that family.
            short_label = previous_taken and bool(re.fullmatch(
                r"(?:NO COO|HONG KONG|MACAU|MADE IN [A-Z ]+|POCH|PBP)\s*:?",
                gap,
                flags=re.I,
            ))
            if has_combo and not bootleg and not accessory_after:
                take = True
            elif previous_single and single and not heading_stop and not bootleg:
                take = True
            elif (short_label or (previous_taken and gap == "")) and not heading_stop and not bootleg:
                take = True
            else:
                take = False
                if heading_stop or bootleg:
                    previous_single = False
                    previous_taken = False
            if not take or not batch:
                continue
            if all(item.lower() in page_seen for item in batch):
                previous_single = False
                previous_taken = False
                continue
            for item in batch:
                items.append(item)
                page_seen.add(item.lower())
            previous_single = single
            previous_taken = True
        if not items and re.search(r"\bthis licensed figure\b", norm(family["html"]), flags=re.I):
            items = ["Top Toys No COO licensed figure"]
        parsed.append({"num": family["num"], "label": family["label"], "items": items})

    merged = {}
    order = []
    for family in parsed:
        if family["num"] not in merged:
            merged[family["num"]] = family
            order.append(family["num"])
        else:
            merged[family["num"]]["items"].extend(family["items"])
            if family["label"] and not merged[family["num"]]["label"]:
                merged[family["num"]]["label"] = family["label"]
    return [merged[num] for num in order]


def shorten(text):
    text = norm(text)
    if len(text) <= 160:
        return text
    return text[:157].rstrip() + "..."


def apply_figure(figure, parsed):
    by_num = {family["num"]: family for family in parsed}
    documented = [family["numeral"].upper() for family in figure.get("families") or []]
    if documented:
        scope = documented
    else:
        scope = [family["num"] for family in parsed if family["items"]]
    present = [num for num in scope if by_num.get(num) and by_num[num]["items"]]
    missing = [num for num in scope if num not in present]

    for family in figure.get("families") or []:
        parsed_family = by_num.get(family["numeral"].upper())
        if parsed_family and parsed_family["items"]:
            family["micro_count"] = len(parsed_family["items"])
            family["micros"] = [shorten(item) for item in parsed_family["items"]]
        else:
            family.pop("micro_count", None)
            family.pop("micros", None)

    figure.pop("micro_families", None)
    if not documented and present:
        figure["micro_families"] = [
            {
                "numeral": num,
                "label": by_num[num]["label"],
                "micro_count": len(by_num[num]["items"]),
                "micros": [shorten(item) for item in by_num[num]["items"]],
            }
            for num in present
        ]

    if scope and present and not missing:
        figure["micro_status"] = "text"
        figure["micro_count"] = sum(len(by_num[num]["items"]) for num in present)
        if documented:
            figure["micro_note"] = "Pictured combination lists cover every documented family."
        else:
            figure["micro_note"] = (
                "Page text lists pictured variants under COO Family headings. "
                "The roman family grid was not confirmed on the sheet image, so the family count stays unverified."
            )
    elif present:
        figure["micro_status"] = "partial"
        figure["micro_count"] = None
        figure["micro_note"] = "Pictured lists do not cover every documented family, so there is no version total."
    else:
        figure["micro_status"] = "unverified"
        figure["micro_count"] = None
        figure["micro_note"] = "No readable pictured-combination list. Sheet labels were not read as a version count."


def expect(figures, name, counts):
    figure = next(row for row in figures if row["index_name"] == name)
    if figure.get("families"):
        got = [family.get("micro_count") for family in figure["families"]]
    else:
        got = [family["micro_count"] for family in figure.get("micro_families") or []]
    if got != list(counts) or figure.get("micro_count") != sum(counts):
        raise SystemExit(f"{name}: expected {list(counts)} total {sum(counts)}, got {got} total {figure.get('micro_count')}")


def main():
    if not CACHE.is_dir():
        print(f"cache missing at {CACHE}; snapshot left unchanged", file=sys.stderr)
        return 1
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    missing_cache = []
    for figure in snapshot["figures"]:
        path = cache_path(figure["url"])
        if not path.exists():
            missing_cache.append(figure["url"])
            continue
        apply_figure(figure, parse_families(path.read_text(encoding="utf-8", errors="replace")))

    vader = next(row for row in snapshot["figures"] if row["index_name"] == "Darth Vader")
    vader["micro_note"] = (
        "71 pictured mould and colour lines. A mould-only reading of the Hong Kong block is lower: "
        "Family I Hong Kong is M1 x2, M2 x3 including one POCH, M3 x2. Glasslite is two lines under Family III, not one."
    )
    yoda = next(row for row in snapshot["figures"] if row["index_name"] == "Yoda")
    yoda["micro_note"] = (
        "29 pictured lines inside the four families. Lili Ledy and Poch sit under families I and II. "
        "Two lines are marked on the page as minor batches and are included. Family IV is the single Top Toys figure. "
        "Snake, cane, belt and cloak stay accessories."
    )

    expect(snapshot["figures"], "Darth Vader", [14, 5, 15, 7, 4, 3, 4, 13, 1, 2, 2, 1])
    expect(snapshot["figures"], "Yoda", [9, 14, 5, 1])
    expect(snapshot["figures"], "Luke Skywalker", [10, 12, 5, 5])
    expect(snapshot["figures"], "Lando Calrissian", [3, 4, 7])
    expect(snapshot["figures"], "Luke Skywalker (Bespin Fatigues)", [7, 9, 14])
    expect(snapshot["figures"], "Han Solo (Hoth Outfit)", [5, 2, 13])
    expect(snapshot["figures"], "Ben (Obi-Wan) Kenobi", [6, 8, 13])
    expect(snapshot["figures"], "Sand People", [5, 5, 3, 5, 7])
    expect(snapshot["figures"], "R5-D4", [6, 2, 4])
    expect(snapshot["figures"], "IG-88", [3, 3, 11])
    expect(snapshot["figures"], "Klaatu", [2, 4, 4])

    if missing_cache:
        print("cache files missing:", len(missing_cache), file=sys.stderr)
        return 1

    SNAPSHOT.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    ranked = sorted(
        (row for row in snapshot["figures"] if row.get("micro_status") == "text" and row.get("micro_count")),
        key=lambda row: (-row["micro_count"], row["index_name"].lower()),
    )
    print(f"text totals: {len(ranked)}; partial: {sum(1 for row in snapshot['figures'] if row.get('micro_status')=='partial')}; unverified: {sum(1 for row in snapshot['figures'] if row.get('micro_status')=='unverified')}")
    for row in ranked:
        print(f"  {row['micro_count']:3}  {row['index_name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
