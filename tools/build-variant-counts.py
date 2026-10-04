#!/usr/bin/env python3
"""Regenerate the variant-count and outfit-count summary.

Variant counts come from data-source/vv-variant-counts.json, a snapshot of
the live Variant Villain figure guides fetched on 2026-10-04. The snapshot
is not served from /data. Each figure has two levels: roman-numeral
manufacturer/region families, and the pictured versions inside those
families. Paint, cape and sabre sections are not counted. A page with no
readable roman grid is unverified. A page whose pictured lists do not cover
every family has no version total.

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


ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

# Longer keys are matched by their own regex. Smile and Lili Ledy (including
# "LL") are one factory: a Smile column sold by Lili Ledy is not a second maker.
FACTORY_RULES = (
    ("kader", re.compile(r"\bkader\b", re.I)),
    ("unitoy", re.compile(r"\bunitoy\b", re.I)),
    ("smile", re.compile(r"\bsmile\b|\blili\s+ledy\b|\bll\b", re.I)),
    ("pbp", re.compile(r"\bpbp\b|\bpoch\b", re.I)),
    ("top toys", re.compile(r"\btop\s+toys\b", re.I)),
    ("takara", re.compile(r"\btakara\b", re.I)),
    ("glasslite", re.compile(r"\bglasslite\b", re.I)),
    ("meccano", re.compile(r"\bmeccano\b", re.I)),
    ("taiwan", re.compile(r"\btaiwan\b|\bu\s*\.?\s*m\s*\.?\b|universal\s+manufacturers", re.I)),
)

FACTORY_NAMES = {
    "kader": "Kader",
    "unitoy": "Unitoy",
    "pbp": "PBP",
    "top toys": "Top Toys",
    "takara": "Takara",
    "glasslite": "Glasslite",
    "meccano": "Meccano",
    "taiwan": "Taiwan",
}


def roman_value(token):
    letters = re.sub(r"[^IVXLCDM]", "", str(token or "").upper())
    total = 0
    previous = 0
    for char in reversed(letters):
        value = ROMAN_VALUES.get(char, 0)
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total


def ordered_families(families):
    return sorted(families, key=lambda family: (roman_value(family.get("numeral")), family.get("numeral") or ""))


def distinct_factories(families):
    """Factory count is fixed here. Smile and Lili Ledy share one slot."""
    seen = []
    saw_smile = False
    saw_lili = False
    for family in ordered_families(families):
        label = family.get("label") or ""
        found = []
        for key, pattern in FACTORY_RULES:
            match = pattern.search(label)
            if match:
                found.append((match.start(), key))
        for _, key in sorted(found):
            if key not in seen:
                seen.append(key)
        if re.search(r"\bsmile\b", label, re.I):
            saw_smile = True
        if re.search(r"\blili\s+ledy\b|\bll\b", label, re.I):
            saw_lili = True
    names = []
    for key in seen:
        if key == "smile":
            if saw_smile and saw_lili:
                names.append("Smile/Lili Ledy")
            elif saw_lili:
                names.append("Lili Ledy")
            else:
                names.append("Smile")
        else:
            names.append(FACTORY_NAMES[key])
    return names


def factory_phrase(names):
    if not names:
        return "not recorded"
    word = "factory" if len(names) == 1 else "different factories"
    return f"{len(names)} {word}: " + ", ".join(names)


def dossier_text(rel_file):
    path = DATA / rel_file
    chunks = []
    if path.exists():
        chunks.append(path.read_text(encoding="utf-8"))
    base = re.sub(r"-\d+$", "", path.stem)
    for sibling in sorted(path.parent.glob(base + "-*.txt")):
        if sibling.resolve() == path.resolve():
            continue
        chunks.append(sibling.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def production_years(text):
    """First and last release from an explicit Released or Release Date line.

    A mould date stamp is not a release year. A missing line stays missing.
    """
    ranges = [
        (int(start), int(end))
        for start, end in re.findall(r"Released:\s*(\d{4})\s*[–—-]\s*(\d{4})", text, flags=re.I)
    ]
    if ranges:
        return min(start for start, _end in ranges), max(end for _start, end in ranges)
    onwards = [int(year) for year in re.findall(r"Released:\s*(\d{4})\s+onwards", text, flags=re.I)]
    if onwards:
        return min(onwards), None
    singles = [int(year) for year in re.findall(r"Release Date:\s*(\d{4})", text, flags=re.I)]
    if singles:
        return min(singles), max(singles)
    return None, None


def years_phrase(first, last):
    if first and last and first != last:
        return f"{first} to {last}"
    if first and last:
        return str(first)
    if first:
        return f"from {first}"
    return "not recorded"


def counted_noun(number, singular):
    plural = {"family": "families", "version": "versions"}[singular]
    word = singular if number == 1 else plural
    return f"{number} {word}"


def figure_block(index, row):
    note = ""
    if row["basis"].startswith("COO Family"):
        note = " (COO Family headings; the page prints the numerals without manufacturer names on those lines)"
    elif "adds VII" in row["basis"]:
        note = " (text index I-VI; COO sheet image shows I-VII)"
    families = ordered_families(row["families"])
    years = f"Years: {row['years']}"
    factories = f"Factories: {row['factories']}"
    if row.get("versions_unverified"):
        block = [
            f"{index}. {row['name']} — {counted_noun(row['count'], 'family')}{note} — versions unverified — {years} — {factories}"
        ]
        for family in families:
            block.append(f"- {family_label(family)}")
        return block
    version_total = counted_noun(row["micro"], "version")
    if row.get("family_count_unverified"):
        block = [
            f"{index}. {row['name']} — {version_total} — family count unverified — {years} — {factories}"
        ]
    else:
        block = [
            f"{index}. {row['name']} — {version_total} across {counted_noun(row['count'], 'family')}{note} — {years} — {factories}"
        ]
    for family in families:
        block.append(f"- {family_label(family)} — {counted_noun(family['micro_count'], 'version')}")
    return block


def version_row(figure, live, families, family_count_unverified=False):
    first, last = production_years(dossier_text(figure.get("file") or ""))
    names = distinct_factories(families)
    return {
        "name": figure["name"],
        "url": live["url"],
        "count": live.get("count"),
        "micro": live.get("micro_count"),
        "basis": live.get("basis") or "",
        "families": families,
        "years": years_phrase(first, last),
        "factories": factory_phrase(names),
        "factory_names": names,
        "family_count_unverified": family_count_unverified,
        "versions_unverified": False,
    }


def render(figures, snapshot, by_url):
    counted = []
    family_only = []
    unverified = []
    for figure in figures:
        live = by_url.get(norm_url(figure.get("url")))
        if not live:
            unverified.append({
                "name": figure["name"],
                "url": figure.get("url") or "",
                "basis": "not in the fetched snapshot",
            })
            continue
        text_versions = live.get("micro_status") == "text" and live.get("micro_count")
        documented = live.get("status") == "documented" and live.get("families")
        if text_versions and documented:
            counted.append(version_row(figure, live, live["families"]))
            continue
        if text_versions and live.get("micro_families"):
            counted.append(version_row(figure, live, live["micro_families"], family_count_unverified=True))
            continue
        if documented:
            row = version_row(figure, live, live["families"])
            row["versions_unverified"] = True
            row["micro"] = None
            family_only.append(row)
            continue
        unverified.append({
            "name": figure["name"],
            "url": live.get("url") or figure.get("url") or "",
            "basis": live.get("basis") or "not in the fetched snapshot",
        })
    counted.sort(key=lambda row: (-row["micro"], row["name"].lower()))
    family_only.sort(key=lambda row: (-(row["count"] or 0), row["name"].lower()))
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
        "Counting basis:",
        f"These variant counts were taken from the live Variant Villain figure guides on {fetched} (https://www.variantvillain.com/characters/sw/, /esb/, /rotj/, /potf/ and /droids/). The snapshot is data-source/vv-variant-counts.json. It records each page URL. Power of the Force and Droids and Ewoks use the same roman-numeral figure guide, so they are included.",
        "A figure has two levels. Families are the documented manufacturer/region columns: lines such as \"I: Kader\" and \"VII: Takara\". A blank label still counts when the numeral is printed (\"II:\"). A label that starts with \"not\" is skipped. A sub-point such as \"IV.1\" is not another family. Versions are the pictured sub-variants inside a family, read from that page's combination list. Paint shades listed on their own, cape moulds and lightsaber moulds are not versions. Darth Vader's capes and telescoping or double-telescoping sabres are accessory variants, not extra figure families.",
        "Each family count was checked against that page's COO sheet or figure-guide image. Where the image and the text disagree, the image is used. A column the sheet marks as not this figure is left out. Stormtrooper's text index lists I-VI. The COO sheet image adds VII: PBP/Lili Ledy, so Stormtrooper is 7 families. Wicket W. Warrick's Return of the Jedi sheet shows two families, I Smile (HK) and II Taiwan. Version totals are ranked only when every family on that line has a pictured list. If the line says versions unverified, do not add the family lines together and do not invent a version total.",
        "If the images do not show a readable roman family grid, the family count is unverified. Do not guess a family count. A line that says family count unverified still has a version total when the page text lists the pictured variants. Yoda's sheet is four families (I Kader HK, II Unitoy, III Smile, IV Top Toys). Lili Ledy, Kader China and Poch/PBP sit under those families. They are not extra roman families. Yoda's snake, cane, belt and cloak are accessories. Darth Vader's version total is the pictured mould and colour lines, which is higher than counting one line per torso mould.",
        "Each figure line has Years and Factories. Those were calculated when this summary was built. Repeat them. Do not count the factories again from the family lines. Do not count the versions again from the family lines. Years come from a Released or Release Date line in that figure's dossier. If Years says not recorded, leave the years out. Smile and Lili Ledy, including an LL line, are one factory. Kader China is Kader. Made in Taiwan, Taiwan and Universal Manufacturers are Taiwan.",
        "",
        "Outfits, versions and looks mean distinct catalog figures of one character. They are not paint variants of a single figure. Han Solo (in Trench Coat) is Han's Endor figure. Princess Leia Organa (in Combat Poncho) is Leia's Endor figure. The catalog has no further Endor figure for either character. A Droids-line figure of the same character counts as one version.",
        "",
        "Character versions (distinct catalog figures, ranked). A character with one catalog figure is not listed. Each line under a character is one version:",
    ]
    for index, (key, names) in enumerate(ranked_characters, start=1):
        lines.append(f"{index}. {key} — {len(names)} versions")
        for name in names:
            lines.append(f"- {name}")
    lines.append("")
    lines.append("Ranked figures by pictured versions (highest first). Each line under a figure is one family, in numeral order, with that family's version count:")
    for index, row in enumerate(counted, start=1):
        lines.extend(figure_block(index, row))
    lines.append("")
    lines.append("Families documented, versions unverified (the pictured lists or the sheet labels do not cover every family, so no version total is given):")
    for index, row in enumerate(family_only, start=1):
        lines.extend(figure_block(index, row))
    lines.append("")
    lines.append("Unverified (no readable roman family grid on the COO sheet or figure-guide images, so no family count is given):")
    for row in unverified:
        extra = f" — {row['basis']}" if row.get("basis") else ""
        lines.append(f"- {row['name']} — {row['url']}{extra}")
    lines.append("")
    lines.append(f"Sources: live Variant Villain character pages fetched {fetched}, stored in data-source/vv-variant-counts.json. Outfit totals use the catalog names in data/catalog-1.json through data/catalog-6.json. Regenerated by tools/build-variant-counts.py.")
    return "\n".join(lines) + "\n", counted, unverified, ranked_characters


def atomic_chunks(text):
    """Keep a count line and the family or version lines under it in one chunk."""
    lines = text.splitlines(keepends=True)
    chunks = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if re.match(r"\d+\. ", line):
            block = line
            index += 1
            while index < len(lines) and lines[index].startswith("- "):
                block += lines[index]
                index += 1
            chunks.append(block)
            continue
        chunks.append(line)
        index += 1
    return chunks


def split_text(text):
    if len(text) <= MAX_CHARS:
        return [text]
    header = "\n".join([
        "Name: Variant and outfit counts",
        "Aliases: most variants, most outfits, most versions, variant counts, outfit counts, character versions, how many versions",
        "Part of the variant and outfit count summary. Counting basis and the top of the ranking are in part 1. Family and version lists continue here. Do not guess a count that is not in this summary. An unverified figure has no number.",
        "",
    ])
    parts = []
    current = ""
    for chunk in atomic_chunks(text):
        if current and len(current) + len(chunk) > MAX_CHARS - len(header):
            parts.append(current if current.endswith("\n") else current + "\n")
            current = header + chunk
        else:
            current += chunk
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
    print(f"figures with version totals: {len(counted)}; unverified families: {len(unverified)}; multi-version characters: {len(characters)}")
    print("top 15 versions:")
    for row in counted[:15]:
        families = "family count unverified" if row.get("family_count_unverified") else counted_noun(row["count"], "family")
        print(f"  {counted_noun(row['micro'], 'version')} across {families}  {row['name']}  years {row['years']}  factories {row['factories']}")
    vader = next(row for row in counted if row["name"] == "Darth Vader")
    print("Vader factories:", vader["factories"])
    for path in written:
        print(f"wrote {path.relative_to(ROOT)} ({len(path.read_text(encoding='utf-8'))} chars)")


if __name__ == "__main__":
    main()
