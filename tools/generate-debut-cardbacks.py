#!/usr/bin/env python3
"""Generate debut-cardback reference text from Warren's Variant Villain workbook.

Reads only the Figure -> Cardback Matrix and Cardback Summary / Method & Scope
legend. Does not write collection status or private notes. Run:

  python3 tools/generate-debut-cardbacks.py path/to/workbook.xlsx [output_dir]

Output files go to data/compatibility/ and are named debut-cardbacks-reference*.txt.
"""

import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

import openpyxl

VALID_KENNER = (12, 20, 21, 31, 32, 41, 45, 47, 65, 77, 79, 92)
FLAG_NUMBERS = (48, 14, 17, 18, 30, 37, 50, 70)
FLAG_TEXT = (
    "not on Warren's list of valid Kenner families "
    "(12, 20, 21, 31, 32, 41, 45, 47, 65, 77, 79, 92); "
    "regional/other family, flagged for his review"
)
MAX_CHARS = 6800
UNKNOWN_LINE = "Debut Kenner Cardback: unknown - not established in the reference workbook"

EXACT = "Exact / explicitly documented"
CONFIRMED = "Confirmed production range"


def map_evidence(level):
    if level == EXACT:
        return "documented"
    if level == CONFIRMED:
        return "documented (range only, not an exact card)"
    if level == "Regional family / broad match":
        return "probable"
    if level == "Unconfirmed exact micro-variant":
        return "unknown"
    raise SystemExit(f"Unexpected evidence level: {level!r}")


def flag_numbers(text):
    found = []
    for number in FLAG_NUMBERS:
        if re.search(rf"(?<!\d){number}(?!\d)", text or ""):
            found.append(number)
    return found


def with_flags(text):
    text = (text or "").strip()
    found = flag_numbers(text)
    if not found:
        return text
    labelled = ", ".join(f"{number}-back" for number in found)
    return f"{text} [{labelled}: {FLAG_TEXT}]"


def aliases_from_name(name):
    """Only names already written in the workbook figure title."""
    parts = [name]
    for match in re.findall(r"\(([^)]+)\)", name):
        piece = match.strip()
        if piece and piece not in parts:
            parts.append(piece)
    return parts


def header():
    families = ", ".join(str(n) for n in VALID_KENNER)
    return "\n".join([
        "Debut Kenner Cardback reference",
        "Source: Variant Villain reference workbook, Figure -> Cardback Matrix and Cardback Summary legend. Cardback research date 14 September 2026 (Method & Scope).",
        "Debut Kenner Cardback means the workbook column Earliest / exact cardback. It is not a confirmed debut for most figures, and it is not Warren's own Debut Card Back list. Do not silently overwrite one with the other.",
        "Debut Kenner Cardback, compatible cardbacks (Other documented cardbacks / range) and factory matching are different. A figure on a card does not prove every variant belongs with that card. Factory matching is not established in this workbook (no card-manufacturing source or run). A rationale line below is repeated only when the workbook states that factory-to-card link, with its evidence label.",
        "Evidence: Exact / explicitly documented -> documented. Confirmed production range -> documented (range only, not an exact card). Regional family / broad match -> probable. Unconfirmed exact micro-variant -> unknown.",
        f"Warren's valid Kenner families: {families}. 48-back is in the Cardback Summary (ESB 48A1, 48A2, 48B1, 48B2, 48C; ROTJ 48A1, 48A2, 48A3) but is not on that list. 14, 17, 18, 30, 37, 50 and 70 are not on it either. Flagged where they appear.",
        "96 figure pages. Variant lines are only Exact or Confirmed production range. Aliases are only names already written in the figure title. Packaging is the workbook Era field.",
        "",
    ])


def load_rows(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["Figure → Cardback Matrix"]
    rows = []
    for r in range(2, ws.max_row + 1):
        rows.append({
            "era": ws.cell(r, 2).value,
            "figure": ws.cell(r, 3).value,
            "variant": ws.cell(r, 4).value,
            "factory": ws.cell(r, 5).value,
            "earliest": ws.cell(r, 7).value,
            "other": ws.cell(r, 8).value,
            "evidence": ws.cell(r, 10).value,
            "rationale": ws.cell(r, 11).value,
            "figure_source": ws.cell(r, 12).value,
            "cardback_source": ws.cell(r, 13).value,
        })
    return rows


def figure_blocks(rows):
    order = []
    grouped = OrderedDict()
    for row in rows:
        if row["figure"] not in grouped:
            order.append(row["figure"])
            grouped[row["figure"]] = []
        grouped[row["figure"]].append(row)

    blocks = []
    stats = {
        "exact": [],
        "range_only": [],
        "family_only": [],
        "unknown": [],
    }
    for figure in order:
        items = grouped[figure]
        era = items[0]["era"]
        family = []
        for item in items:
            other = str(item["other"] or "")
            if other.startswith("Figure-level family:"):
                text = other.split(":", 1)[1].strip()
                if text not in family:
                    family.append(text)
        strong = [item for item in items if item["evidence"] in (EXACT, CONFIRMED)]
        has_exact = any(item["evidence"] == EXACT for item in strong)
        has_confirmed = any(item["evidence"] == CONFIRMED for item in strong)
        if has_exact:
            stats["exact"].append(figure)
        elif has_confirmed:
            stats["range_only"].append(figure)
        elif family:
            stats["family_only"].append(figure)
        else:
            stats["unknown"].append(figure)

        lines = [
            f"Figure Name: {figure}",
            "Aliases: " + "; ".join(aliases_from_name(figure)),
            f"Packaging: {era}",
        ]
        if not strong and not family:
            lines.append(UNKNOWN_LINE)
            lines.append("Factory matching: not established in this workbook.")
        else:
            if family:
                shown = " | ".join(with_flags(part) for part in family)
                lines.append(
                    "Debut Kenner Cardback: not confirmed for the figure as a whole. "
                    "Workbook figure-level family range (not a confirmed debut): " + shown
                )
            else:
                lines.append(
                    "Debut Kenner Cardback: not confirmed for the figure as a whole. "
                    "No figure-level family range is stated. Variant lines below are the workbook's "
                    "Earliest / exact cardback values, not a single debut for every variant."
                )
            lines.append("Factory matching: not established in this workbook.")
            if strong:
                lines.append("Variant lines (Exact or Confirmed production range only):")
                buckets = OrderedDict()
                for item in strong:
                    key = (
                        item["evidence"],
                        item["factory"],
                        item["earliest"],
                        item["other"],
                        item["rationale"],
                        item["cardback_source"],
                    )
                    buckets.setdefault(key, []).append(item["variant"])
                for key, variants in buckets.items():
                    evidence, factory, earliest, other, rationale, card_source = key
                    other_text = str(other or "").strip()
                    earliest_text = str(earliest or "").strip()
                    if other_text.startswith("Figure-level family:"):
                        other_text = ""
                    if other_text == earliest_text:
                        other_text = ""
                    rationale_text = str(rationale or "").strip().rstrip(".")
                    bits = [
                        f"- {'; '.join(variants)}",
                        f"Factory / origin: {factory}",
                        f"Earliest / exact cardback: {with_flags(earliest_text)}",
                        f"Evidence: {map_evidence(evidence)}",
                    ]
                    if other_text:
                        bits.append("Other documented cardbacks / range: " + with_flags(other_text))
                    if rationale_text:
                        bits.append("Rationale: " + with_flags(rationale_text))
                    if card_source:
                        bits.append(f"Cardback source: {card_source}")
                    lines.append(". ".join(bits) + ".")
            else:
                lines.append("Variant lines: none. No Exact or Confirmed production range row in the workbook.")
        figure_source = next((item["figure_source"] for item in items if item["figure_source"]), "")
        if figure_source:
            lines.append(f"Figure source: {figure_source}")
        blocks.append({"era": era, "figure": figure, "text": "\n".join(lines)})
    return blocks, stats


def pack(blocks):
    """Split into files under MAX_CHARS. Each file keeps a copy of the header."""
    head = header()
    files = []
    current_era = None
    part = 0
    body = []
    used = len(head) + 1

    def era_slug(era):
        slug = {
            "Star Wars": "sw",
            "The Empire Strikes Back": "esb",
            "Return of the Jedi": "rotj",
            "Power of the Force": "potf",
        }.get(era)
        if not slug:
            raise SystemExit(f"Unexpected era: {era!r}")
        return slug

    def flush():
        nonlocal body, used, part
        if not body:
            return
        part += 1
        name = f"debut-cardbacks-reference-{era_slug(current_era)}-{part}.txt"
        files.append((name, head + "\n".join(body).rstrip() + "\n"))
        body = []
        used = len(head) + 1

    for block in blocks:
        if current_era is None:
            current_era = block["era"]
        if block["era"] != current_era:
            flush()
            current_era = block["era"]
            part = 0
        piece = block["text"] + "\n\n"
        if used + len(piece) > MAX_CHARS and body:
            flush()
        if len(head) + len(piece) > MAX_CHARS:
            raise SystemExit(f"Figure block too large to fit: {block['figure']} ({len(piece)} chars)")
        body.append(piece)
        used += len(piece)
    flush()
    return files


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: generate-debut-cardbacks.py workbook.xlsx [output_dir]")
    workbook = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/compatibility")
    rows = load_rows(workbook)
    blocks, stats = figure_blocks(rows)
    files = pack(blocks)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, text in files:
        path = out_dir / name
        path.write_text(text, encoding="utf-8")
        print(f"{path} {len(text)} chars {text.count(chr(10))+1} lines")
    print("figures", len(blocks))
    for key, figures in stats.items():
        print(f"{key} {len(figures)}")
        for figure in figures:
            print(f"  - {figure}")


if __name__ == "__main__":
    main()
