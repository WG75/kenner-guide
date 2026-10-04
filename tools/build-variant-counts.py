#!/usr/bin/env python3
"""Regenerate the variant-count and outfit-count summary.

Counting rule (manufacturer/region variants only):

1. Roman-numeral index bullets from the Variant Villain page, such as
   "- I: Unitoy". A label that starts with "not" ("Not an R5 COO",
   "Not used for R2SS") is the page saying that family is not this figure,
   so it is skipped.
2. If the file has no such bullets, headings "Family I:", "Family II:"
   are counted. The manufacturer on the following line is the label.
3. If the file has neither, labelled lines "COO Family 1: Unitoy" are
   counted. A bare "COO Family 1:" with nothing after the colon is a
   detail heading, not another family.

Paint shades, cape moulds and lightsaber moulds are not counted. Split
files are read in order and the first part that yields a count is used,
so a repeated index in part 2 is not added again. A figure with none of
these lists is "not counted".

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
MAX_CHARS = 6800
OUT_DIR = DATA / "references"
OUT_STEM = "variant-counts"

ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

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


def roman_to_int(token):
    total = 0
    prev = 0
    for char in reversed(token.upper()):
        value = ROMAN_VALUES.get(char)
        if not value:
            return None
        if value < prev:
            total -= value
        else:
            total += value
            prev = value
    if total < 1 or total > 20:
        return None
    return total


def normalise_label(label):
    return re.sub(r"\s+", " ", label.replace("’", "'")).strip(" -")


def character_key(name):
    for prefix, key in CHARACTER_PREFIXES:
        if name == prefix or name.startswith(prefix):
            return key
    return name


def load_catalog():
    index = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    figures = []
    for part_name in index["parts"]:
        part = json.loads((DATA / part_name).read_text(encoding="utf-8"))
        figures.extend(part.get("figures") or [])
    return figures


def part_paths(rel):
    """figure-reference.txt plus figure-reference-2.txt, not a different figure."""
    path = DATA / rel
    match = re.match(r"^(.*-reference)(?:-(\d+))?\.txt$", path.name)
    if not match:
        return [path]
    prefix = match.group(1)
    paths = sorted(path.parent.glob(prefix + "*.txt"))
    def sort_key(item):
        numbered = re.search(r"-(\d+)\.txt$", item.name)
        return int(numbered.group(1)) if numbered else 0
    return sorted(paths, key=sort_key)


def roman_bullets(text):
    found = []
    for line in text.splitlines():
        match = re.match(r"^\s+-\s+([IVXLCDM]+):\s*(.*?)\s*$", line)
        if not match:
            continue
        number = roman_to_int(match.group(1))
        if not number:
            continue
        label = normalise_label(match.group(2))
        if re.match(r"(?i)^not\b", label):
            continue
        found.append((number, match.group(1).upper(), label))
    return found


def family_headings(text):
    lines = text.splitlines()
    found = []
    for index, line in enumerate(lines):
        match = re.match(r"^Family ([IVXLCDM]+):\s*(.*?)\s*$", line)
        if not match:
            continue
        number = roman_to_int(match.group(1))
        if not number:
            continue
        label = normalise_label(match.group(2))
        if not label:
            for nxt in lines[index + 1:index + 6]:
                stripped = nxt.strip()
                if not stripped or stripped.startswith("---"):
                    continue
                if re.match(r"^Family [IVXLCDM]+:", stripped):
                    break
                if stripped.lower().startswith("traits"):
                    continue
                label = normalise_label(re.sub(r"^-\s+", "", stripped))
                break
        found.append((number, match.group(1).upper(), label))
    return found


def coo_families(text):
    found = []
    seen = set()
    for line in text.splitlines():
        match = re.match(r"^COO Family (\d+):\s+(\S.*?)\s*$", line)
        if not match:
            continue
        number = int(match.group(1))
        if number in seen or number < 1 or number > 20:
            continue
        seen.add(number)
        found.append((number, f"COO {number}", normalise_label(match.group(2))))
    return found


def count_text(text):
    bullets = roman_bullets(text)
    if bullets:
        return "roman-numeral page index", bullets
    headings = family_headings(text)
    if headings:
        return "Family roman headings", headings
    families = coo_families(text)
    if families:
        return "labelled COO Family lines", families
    return None, []


def count_figure(rel):
    for path in part_paths(rel):
        if not path.exists():
            continue
        basis, entries = count_text(path.read_text(encoding="utf-8"))
        if entries:
            return basis, entries, path.name
    return None, [], ""


def entry_label(entry):
    number, token, label = entry
    if label:
        return f"{token} {label}"
    return token


def render(figures):
    counted = []
    not_counted = []
    for figure in figures:
        basis, entries, source_name = count_figure(figure["file"])
        row = {
            "name": figure["name"],
            "file": figure["file"],
            "basis": basis,
            "entries": entries,
            "source_name": source_name,
        }
        if entries:
            counted.append(row)
        else:
            not_counted.append(row)
    counted.sort(key=lambda row: (-len(row["entries"]), row["name"].lower()))
    not_counted.sort(key=lambda row: row["name"].lower())

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

    lines = [
        "Name: Variant and outfit counts",
        "Aliases: most variants, most outfits, most versions, variant counts, outfit counts, character versions, how many versions",
        "",
        "Counting basis (evidence: documented):",
        "A figure's variant count is the number of documented manufacturer/region families in its figure file. Paint shades, cape moulds and lightsaber moulds are not part of this count. Darth Vader's capes and telescoping or double-telescoping sabres are accessory variants, not extra figure families.",
        "The count uses the first list the file actually has:",
        "1. Roman-numeral index bullets from the Variant Villain page, such as \"- I: Unitoy\". A label that starts with \"not\" (for example \"Not an R5 COO\" or \"Not used for R2SS\") is not a variant of that figure and is skipped.",
        "2. If there is no roman index, headings \"Family I:\" and \"Family II:\" are counted.",
        "3. If there is neither, labelled lines \"COO Family 1: Unitoy\" are counted. A bare \"COO Family 1:\" with no manufacturer on that line is a detail heading and is not a second family.",
        "Split reference files are read in order. The first part that contains one of these lists supplies the count, so a repeated index in a later part is not added again.",
        "If the figure file has none of these lists, the count is \"not counted\". Do not guess a number, and do not invent a higher count than this summary.",
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
        labels = "; ".join(entry_label(entry) for entry in row["entries"])
        lines.append(f"{index}. {row['name']} — {len(row['entries'])} — {labels}")
    lines.append("")
    lines.append("Not counted (the figure file has no roman-numeral index, Family heading list, or labelled COO Family list):")
    for row in not_counted:
        lines.append(f"- {row['name']}")
    lines.append("")
    lines.append("Sources: figure files under data/figures and the catalog names in data/catalog-1.json through data/catalog-6.json. Regenerated by tools/build-variant-counts.py.")
    return "\n".join(lines) + "\n", counted, not_counted, ranked_characters


def split_text(text):
    if len(text) <= MAX_CHARS:
        return [text]
    header = "\n".join([
        "Name: Variant and outfit counts",
        "Aliases: most variants, most outfits, most versions, variant counts, outfit counts, character versions, how many versions",
        "Part of the variant and outfit count summary. Counting basis and the top of the ranking are in part 1. Evidence: documented. Do not guess a count that is not in this summary.",
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
    text, counted, not_counted, characters = render(load_catalog())
    parts = split_text(text)
    written = write_parts(parts)
    print(f"figures counted: {len(counted)}; not counted: {len(not_counted)}; multi-version characters: {len(characters)}")
    print("top 5 variants:")
    for row in counted[:5]:
        print(f"  {len(row['entries']):2}  {row['name']}  ({row['basis']})")
    print("character versions:")
    for key, names in characters:
        if key in {"Luke Skywalker", "Han Solo", "Princess Leia Organa", "Lando Calrissian", "Darth Vader", "C-3PO", "R2-D2"} or len(names) >= 2:
            print(f"  {len(names):2}  {key}: {'; '.join(names)}")
    for path in written:
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} chars)")


if __name__ == "__main__":
    main()
