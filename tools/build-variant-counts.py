#!/usr/bin/env python3
"""Regenerate the variant-count and outfit-count summary.

Variant counts come from data-source/vv-variant-counts.json, a snapshot of
the live Variant Villain figure guides fetched on 2026-10-04. The snapshot
is not served from /data. Each count is the page's roman-numeral
manufacturer/region list (I: Kader). Paint, cape and sabre sections are
not counted. A page with no such list and no COO Family headings is
unverified.

An outfit (also called a version or a look) is one catalog figure of a
character. Han Solo (in Trench Coat) is Han's Endor figure. Princess Leia
Organa (in Combat Poncho) is Leia's Endor figure. There is no extra Endor
figure beyond those.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SNAPSHOT = ROOT / "data-source" / "vv-variant-counts.json"
MAX_CHARS = 6800
OUT_DIR = DATA / "references"
OUT_STEM = "variant-counts"

# Longest prefix first. A catalog name maps to one character.
CHARACTER_PREFIXES = [
    ("Luke Skywalker", "Luke Skywalker"),
    ("Han Solo", "Han Solo"),
    ("Princess Leia Organa", "Princess Leia Organa"),
    ("Leia Organa", "Princess Leia Organa"),
    ("Leia (", "Princess Leia Organa"),
    ("Lando Calrissian", "Lando Calrissian"),
    ("Droids C-3PO", "C-3PO"),
    ("C-3PO", "C-3PO"),
    ("Droids R2-D2", "R2-D2"),
    ("Artoo-Detoo", "R2-D2"),
    ("R2-D2", "R2-D2"),
    ("Bespin Security Guard", "Bespin Security Guard"),
    ("Klaatu", "Klaatu"),
    ("Logray", "Logray"),
    ("Wicket", "Wicket W. Warrick"),
    ("Imperial Stormtrooper", "Stormtrooper"),
    ("Stormtrooper", "Stormtrooper"),
]


def character_key(name):
    for prefix, key in CHARACTER_PREFIXES:
        if name == prefix or name.startswith(prefix):
            return key
    return name


def norm_url(url):
    return (url or "").rstrip("/").lower()


def load_catalog():
    index = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    figures = []
    for part_name in index["parts"]:
        part = json.loads((DATA / part_name).read_text(encoding="utf-8"))
        figures.extend(part.get("figures") or [])
    return figures


def load_snapshot():
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    by_url = {}
    for figure in data["figures"]:
        by_url[norm_url(figure["url"])] = figure
    return data, by_url


def family_label(family):
    numeral = family["numeral"].upper()
    label = re.sub(r"\s+", " ", (family.get("label") or "")).strip()
    if label:
        return f"{numeral} {label}"
    return numeral


def render(figures, snapshot, by_url):
    counted = []
    unverified = []
    for figure in figures:
        live = by_url.get(norm_url(figure.get("url")))
        if not live or live.get("status") != "documented" or not live.get("families"):
            unverified.append({
                "name": figure["name"],
                "url": (live or {}).get("url") or figure.get("url") or "",
                "basis": (live or {}).get("basis") or "not in the fetched snapshot",
            })
            continue
        counted.append({
            "name": figure["name"],
            "url": live["url"],
            "count": live["count"],
            "basis": live.get("basis") or "",
            "families": live["families"],
        })
    counted.sort(key=lambda row: (-row["count"], row["name"].lower()))
    unverified.sort(key=lambda row: row["name"].lower())

    groups = {}
    order = []
    for figure in figures:
        key = character_key(figure["name"])
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(figure["name"])
    ranked_characters = sorted(
        ((key, groups[key]) for key in order if len(groups[key]) >= 2),
        key=lambda item: (-len(item[1]), item[0].lower()),
    )

    fetched = snapshot.get("fetched") or "2026-10-04"
    lines = [
        "Name: Variant and outfit counts",
        "Aliases: most variants, most outfits, most versions, variant counts, outfit counts, character versions, how many versions",
        "",
        "Counting basis (evidence: documented):",
        f"These variant counts were taken from the live Variant Villain figure guides on {fetched} (https://www.variantvillain.com/characters/sw/, /esb/, /rotj/, /potf/ and /droids/). The snapshot is data-source/vv-variant-counts.json. It records each page URL. Power of the Force and Droids and Ewoks use the same roman-numeral figure guide, so they are included.",
        "A figure's variant count is the number of documented manufacturer/region families on that page: lines such as \"I: Kader\" and \"VII: Takara\". A blank label still counts when the numeral is printed (\"II:\"). A label that starts with \"not\" is skipped. A sub-point such as \"IV.1\" is not another family. Paint shades, cape moulds and lightsaber moulds are not part of this count. Darth Vader's capes and telescoping or double-telescoping sabres are accessory variants, not extra figure families.",
        "If the page text has no figure-guide numerals, COO Family headings are counted instead. Stormtrooper's text index lists I-VI. The COO sheet image on that page (Stormtrooper-COO-Sheet_3.1.jpg) adds VII: PBP/Lili Ledy, so Stormtrooper is 7.",
        "If the live page text has neither list, the figure is unverified. Do not guess a number, and do not invent a higher count than this summary. Yoda's figure guide is four families (I Kader HK, II Unitoy, III Smile, IV Top Toys). Lili Ledy, Kader China and Poch/PBP on that page sit under those families. They are not extra roman families. Yoda's snake, cane, belt and cloak are accessories.",
        "",
        "Outfits, versions and looks mean distinct catalog figures of one character. They are not paint variants of a single figure. Han Solo (in Trench Coat) is Han's Endor figure. Princess Leia Organa (in Combat Poncho) is Leia's Endor figure. The catalog has no further Endor figure for either character. A Droids-line figure of the same character counts as one version.",
        "",
        "Character versions (distinct catalog figures, ranked). A character with one catalog figure is not listed:",
    ]
    for index, (key, names) in enumerate(ranked_characters, start=1):
        lines.append(f"{index}. {key} — {len(names)} versions — " + "; ".join(names))
    lines.append("")
    lines.append("Ranked figures by documented manufacturer/region variants (highest first):")
    for index, row in enumerate(counted, start=1):
        labels = "; ".join(family_label(family) for family in row["families"])
        note = ""
        if row["basis"].startswith("COO Family"):
            note = " (COO Family headings; the page prints the numerals without manufacturer names on those lines)"
        elif "COO sheet image" in row["basis"]:
            note = " (text index I-VI; COO sheet image adds VII)"
        lines.append(f"{index}. {row['name']} — {row['count']} — {labels}{note}")
    lines.append("")
    lines.append("Unverified (the live page text had no roman figure-guide list and no COO Family headings, so no count is given):")
    for row in unverified:
        lines.append(f"- {row['name']} — {row['url']}")
    lines.append("")
    lines.append(f"Sources: live Variant Villain character pages fetched {fetched}, stored in data-source/vv-variant-counts.json. Outfit totals use the catalog names in data/catalog-1.json through data/catalog-6.json. Regenerated by tools/build-variant-counts.py.")
    return "\n".join(lines) + "\n", counted, unverified, ranked_characters


def split_text(text):
    if len(text) <= MAX_CHARS:
        return [text]
    header = "\n".join([
        "Name: Variant and outfit counts",
        "Aliases: most variants, most outfits, most versions, variant counts, outfit counts, character versions, how many versions",
        "Part of the variant and outfit count summary. Counting basis and the top of the ranking are in part 1. Evidence: documented. Do not guess a count that is not in this summary. An unverified figure has no number.",
        "",
    ])
    body = text.splitlines(keepends=True)
    parts = []
    current = ""
    for line in body:
        if current and len(current) + len(line) > MAX_CHARS - len(header):
            parts.append(current if current.endswith("\n") else current + "\n")
            current = header + line
        else:
            current += line
    if current:
        parts.append(current if current.endswith("\n") else current + "\n")
    return parts


def write_parts(parts):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for index, text in enumerate(parts):
        name = f"{OUT_STEM}.txt" if index == 0 else f"{OUT_STEM}-{index + 1}.txt"
        path = OUT_DIR / name
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    extra = len(parts) + 1
    while True:
        stale = OUT_DIR / f"{OUT_STEM}-{extra}.txt"
        if not stale.exists():
            break
        stale.unlink()
        extra += 1
    return written


def main():
    snapshot, by_url = load_snapshot()
    text, counted, unverified, characters = render(load_catalog(), snapshot, by_url)
    parts = split_text(text)
    written = write_parts(parts)
    print(f"figures counted: {len(counted)}; unverified: {len(unverified)}; multi-version characters: {len(characters)}")
    print("top 15 variants:")
    for row in counted[:15]:
        print(f"  {row['count']:2}  {row['name']}")
    for path in written:
        print(f"wrote {path.relative_to(ROOT)} ({len(path.read_text(encoding='utf-8'))} chars)")


if __name__ == "__main__":
    main()
