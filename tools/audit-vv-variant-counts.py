#!/usr/bin/env python3
"""Fetch Variant Villain character pages and snapshot manufacturer/region counts.

The live page is the source. A count is the figure-guide list of roman
numerals (I: Kader, II: Unitoy, ...) when that list is in the page text.
If the page has no figure-guide list, labelled COO Family headings are
used instead. Paint, cape and sabre sections are recorded and not counted.
A page with neither list is unverified.
"""

import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data-source" / "vv-variant-counts.json"
CACHE = Path("/tmp/vv-live-2026-10-04")
UA = "kenner-guide-research/1.0 (variant count audit; polite, one request at a time)"
DELAY = 1.1
FETCHED = "2026-10-04"

INDEXES = [
    ("Star Wars", "https://www.variantvillain.com/characters/sw/"),
    ("The Empire Strikes Back", "https://www.variantvillain.com/characters/esb/"),
    ("Return of the Jedi", "https://www.variantvillain.com/characters/rotj/"),
    ("Power of the Force", "https://www.variantvillain.com/characters/potf/"),
    ("Droids and Ewoks", "https://www.variantvillain.com/characters/droids/"),
]

ROMAN = (
    "I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX"
)
ROMAN_LINE = re.compile(
    rf"^(?P<nums>(?:{ROMAN})(?:\s*&\s*(?:{ROMAN}))*)\s*:\s*(?P<label>.*)$",
    re.I,
)
# Jawa's figure guide has no colons: "I Kader", "II Kader/ Kader China".
# A sentence that merely starts with "I" ("I couldn't...") does not match.
NOCOLON_LINE = re.compile(
    rf"^(?P<nums>{ROMAN})\s+(?P<label>(?:Kader|Unitoy|Unitoys|Smile|Takara|Poch|PBP|Lili|Taiwan|Top|Glasslite|Meccano|Toltoys|Universal|Made)\b.*)$",
    re.I,
)
FACTORY_START = re.compile(
    r"^(?:Kader|Unitoy|Unitoys|Smile|Takara|Poch|PBP|Lili|Taiwan|Top|Glasslite|Meccano|Toltoys|Universal|Made)\b",
    re.I,
)
FAMILY_HEAD = re.compile(
    rf"^COO Family\s+(?P<nums>(?:{ROMAN}|\d+)(?:\s*&\s*(?:{ROMAN}|\d+))*)\b\s*:?\s*(?P<label>.*)$",
    re.I,
)
ACCESSORY_HEAD = re.compile(
    r"\b(?:cape|cloak|sabre|saber|lightsaber|blaster|bowcaster|mould comparison|mold comparison)\b",
    re.I,
)


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text).replace("\xa0", " ").replace("\u2019", "'")
    return re.sub(r"\s+", " ", text).strip()


def fetch(url, force=False):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:180]
    path = CACHE / key
    if path.exists() and path.stat().st_size > 500 and not force:
        return path.read_text(errors="replace")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = resp.read().decode("utf-8", "replace")
    path.write_text(data)
    time.sleep(DELAY)
    return data


def anchors(raw):
    found = []
    for href, text in re.findall(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', raw, flags=re.I | re.S):
        label = clean(text)
        if label:
            found.append((label, href.split("#")[0] if href.startswith("http") else href))
    return found


def character_links(raw, index_url):
    era = index_url.rstrip("/").split("/")[-1]
    prefix = f"https://www.variantvillain.com/characters/{era}/"
    seen = set()
    out = []
    for label, href in anchors(raw):
        if not href.startswith(prefix):
            continue
        url = href if href.endswith("/") else href + "/"
        if url.rstrip("/") == prefix.rstrip("/"):
            continue
        if url.count("/") < 6:
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append({"name": label, "url": url})
    return out


def split_nums(token):
    return [part.strip().upper() for part in re.split(r"\s*&\s*", token) if part.strip()]


def page_lines(raw):
    text = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = html.unescape(text).replace("\xa0", " ").replace("\u2019", "'")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return [line.strip() for line in text.splitlines() if line.strip()]


def entries_from_block(lines):
    entries = []
    for line in lines:
        match = ROMAN_LINE.match(line)
        if not match:
            continue
        label = clean(match.group("label"))
        if re.match(r"(?i)^not\b", label):
            continue
        for num in split_nums(match.group("nums")):
            entries.append({"numeral": num.upper(), "label": label})
    uniq = []
    seen = set()
    for entry in entries:
        key = (entry["numeral"], entry["label"].lower())
        if key in seen:
            continue
        seen.add(key)
        uniq.append(entry)
    return uniq


def guide_lines(raw):
    """Roman guide lines, with a wrapped manufacturer pulled onto a blank label.

    'II:' followed by 'Smile' is family II Smile. The manufacturer was in
    the next element, so the tag strip put it on its own line. A following
    '/' or a second factory under an already labelled family (Yoda's
    Lili Ledy under I) stays a sub-label and is not a new family.
    """
    lines = page_lines(raw)
    chosen = []
    for index, line in enumerate(lines):
        match = ROMAN_LINE.match(line)
        if match:
            label = match.group("label").strip()
            if not label and index + 1 < len(lines):
                nxt = lines[index + 1]
                if FACTORY_START.match(nxt) and not ROMAN_LINE.match(nxt) and not NOCOLON_LINE.match(nxt):
                    line = f"{match.group('nums')}: {nxt}"
            chosen.append(line)
            continue
        plain = NOCOLON_LINE.match(line)
        if plain:
            chosen.append(f"{plain.group('nums')}: {plain.group('label')}")
    return chosen


def figure_guide(raw):
    """Roman lines such as 'I: Kader' anywhere in the page text.

    A dot after the numeral ('IV.1:') is a sub-point, not another family.
    A blank label ('II:') still counts: the numeral is on the page, and
    the manufacturer on the next line is that family's label.
    Labels that start with 'not' are the page saying that family is not
    this figure. The lines may sit just before the FIGURE GUIDE heading
    (Vader) or just after it, including after 'UGNAUGHT FIGURE GUIDE'.

    Some pages print the same guide twice (a short menu and the body).
    When a later run starts again at I and uses the same numerals, keep
    the copy whose labels are longer and do not add a second set.
    Two different labels on one numeral inside a single run both count
    (Luke Jedi lists IV twice).
    """
    lines = guide_lines(raw)
    sequences = []
    current = []
    for line in lines:
        match = ROMAN_LINE.match(line)
        nums = tuple(split_nums(match.group("nums")))
        if current and nums == ("I",) and current[-1][0] != ("I",):
            sequences.append(current)
            current = []
        current.append((nums, line))
    if current:
        sequences.append(current)

    grouped = {}
    order = []
    for seq in sequences:
        skeleton = tuple(nums for nums, _line in seq)
        if skeleton not in grouped:
            order.append(skeleton)
            grouped[skeleton] = []
        grouped[skeleton].append(seq)

    chosen_lines = []
    for skeleton in order:
        group = grouped[skeleton]
        best = max(group, key=lambda seq: sum(len(ROMAN_LINE.match(line).group("label")) for _nums, line in seq))
        chosen_lines.extend(line for _nums, line in best)
    return entries_from_block(chosen_lines)


def headings(raw):
    heads = []
    for bit in re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", raw, flags=re.I | re.S):
        title = clean(bit)
        if title:
            heads.append(title)
    return heads


def coo_headings(heads):
    entries = []
    for title in heads:
        match = FAMILY_HEAD.match(title)
        if not match:
            continue
        label = clean(match.group("label"))
        for num in split_nums(match.group("nums")):
            if num.isdigit():
                # Arabic headings are the same families when the page uses
                # "COO Family 1" instead of "COO Family I".
                roman = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
                number = int(num)
                if number < 1 or number >= len(roman):
                    continue
                num = roman[number]
            entries.append({"numeral": num, "label": label})
    uniq = []
    seen = set()
    for entry in entries:
        key = (entry["numeral"], entry["label"].lower())
        if key in seen:
            continue
        seen.add(key)
        uniq.append(entry)
    return uniq


def page_title(raw, fallback):
    titles = [clean(bit) for bit in re.findall(r"<h2[^>]*>(.*?)</h2>", raw, flags=re.I | re.S)]
    skip = {
        "star wars", "the empire strikes back", "return of the jedi",
        "power of the force", "droids & ewoks", "droids and ewoks",
        "a guide to vintage star wars figures & accessories",
    }
    for title in titles:
        if title and title.lower() not in skip and len(title) < 80:
            return title
    return fallback


def coo_image(raw):
    match = re.search(r'href="(https://www.variantvillain.com/wp-content/uploads/[^"]+(?:COO|coo)[^"]+\.(?:jpg|jpeg|png))"', raw)
    return match.group(1) if match else ""


def parse_page(raw, fallback_name, url, era):
    guide = figure_guide(raw)
    heads = headings(raw)
    families = coo_headings(heads)
    accessory = [title for title in heads if ACCESSORY_HEAD.search(title)]
    if guide:
        status = "documented"
        basis = "figure-guide text"
        families_used = guide
        # The Stormtrooper text index stops at VI. The COO sheet image on the
        # same page (Stormtrooper-COO-Sheet_3.1.jpg) shows a seventh column,
        # VII: PBP/Lili Ledy, which the text links omit.
        if url.rstrip("/").endswith("/stormtrooper") and not any(item["numeral"] == "VII" for item in families_used):
            families_used = families_used + [{"numeral": "VII", "label": "PBP/Lili Ledy"}]
            basis = (
                "figure-guide text lists I-VI; the COO sheet image adds "
                "VII: PBP/Lili Ledy, which that text index omits"
            )
    elif families:
        status = "documented"
        basis = "COO Family headings"
        families_used = families
    else:
        status = "unverified"
        basis = "no roman figure-guide list or COO Family headings in the page text"
        families_used = []
    # Unique numerals. Two labels on the same numeral both count.
    return {
        "name": page_title(raw, fallback_name),
        "index_name": fallback_name,
        "era": era,
        "url": url,
        "fetched": FETCHED,
        "status": status,
        "basis": basis,
        "count": len(families_used) if status == "documented" else None,
        "families": families_used,
        "coo_family_headings": families,
        "accessory_sections": accessory[:8],
        "coo_sheet_image": coo_image(raw),
    }


def main():
    pages = []
    index_notes = []
    for era, url in INDEXES:
        try:
            raw = fetch(url, force=False)
        except Exception as err:
            index_notes.append({"era": era, "url": url, "error": str(err)})
            print("INDEX FAIL", era, err)
            continue
        links = character_links(raw, url)
        index_notes.append({"era": era, "url": url, "figures": len(links)})
        print(f"index {era}: {len(links)}")
        for link in links:
            try:
                html_text = fetch(link["url"], force=False)
            except Exception as err:
                pages.append({
                    "name": link["name"],
                    "index_name": link["name"],
                    "era": era,
                    "url": link["url"],
                    "fetched": FETCHED,
                    "status": "unverified",
                    "basis": f"fetch failed: {err}",
                    "count": None,
                    "families": [],
                    "coo_family_headings": [],
                    "accessory_sections": [],
                    "coo_sheet_image": "",
                })
                print("  FAIL", link["url"], err)
                continue
            page = parse_page(html_text, link["name"], link["url"], era)
            pages.append(page)
            print(f"  {page['status']:12} {page['count']!s:>4}  {page['name']}")

    payload = {
        "fetched": FETCHED,
        "source": "https://www.variantvillain.com/",
        "rule": (
            "Count roman-numeral manufacturer/region families from the page's "
            "figure-guide text (I: Kader). A blank label takes the manufacturer "
            "on the next line (II: then Smile). Jawa's guide has no colons "
            "(I Kader). A repeated guide that starts again at I is one list; "
            "keep the longer labels. If that list is absent, count COO Family "
            "headings. Skip a label that starts with 'not'. IV.1 is a sub-point, "
            "not a family. Do not count paint, cape, sabre or mould-comparison "
            "sections. Stormtrooper's text index is I-VI; the COO sheet image "
            "adds VII: PBP/Lili Ledy. No list means unverified."
        ),
        "indexes": index_notes,
        "figures": pages,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    documented = [p for p in pages if p["status"] == "documented"]
    unverified = [p for p in pages if p["status"] != "documented"]
    print(f"wrote {OUT} documented={len(documented)} unverified={len(unverified)}")


if __name__ == "__main__":
    main()
