#!/usr/bin/env python3
"""Build data/retrieval-index.json for chat retrieval.

The index is a topic, alias and keyword list. Chat does not inject it.
The 7,000 character cap does not apply to it. Palitoy release questions
use the topic and role fields. Other topics are recorded so later
reference files can be routed without a full-text scan.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "retrieval-index.json"
FOLDERS = ["figures", "accessories", "references", "terms", "variants", "compatibility"]
YEAR_RE = re.compile(r"\b(197[5-9]|198[0-5])\b")


def topic_for(folder, name):
    stem = name.lower()
    if stem.startswith("palitoy"):
        return "palitoy"
    if "debut-cardback" in stem:
        return "cardback"
    if "coo" in stem:
        return "coo"
    if stem.startswith("vendor") or stem.startswith("factories"):
        return "factory"
    if "variant-count" in stem:
        return "variant"
    if folder == "figures":
        return "figure"
    if folder == "accessories":
        return "accessory"
    if folder == "terms":
        return "term"
    if folder == "variants":
        return "variant"
    if folder == "compatibility":
        return "cardback"
    return "reference"


def role_for(name):
    stem = Path(name).stem.lower()
    if stem.startswith("palitoy-history"):
        return "history"
    if "not-figures" in stem:
        return "not-figures"
    if "palitoy-uk-when" in stem:
        return "when"
    if "palitoy-uk-overview" in stem:
        return "overview"
    if re.search(r"palitoy-uk-19\d\d", stem):
        return "year"
    if "variant-count" in stem:
        return "summary"
    return ""


def years_for(name, text, topic):
    """Year files use the filename year only.

    The shared header mentions 1978 and 1983 on every Palitoy file, so a
    full-text year scan would mark every year file as every year.
    """
    stem = name.lower()
    match = re.search(r"palitoy-uk-(19\d\d)", stem)
    if match and all(token not in stem for token in ("not-figures", "when", "overview")):
        return [int(match.group(1))]
    if topic != "palitoy":
        return []
    found = set()
    for line in text.splitlines():
        if not line.startswith("- "):
            continue
        found.update(int(year) for year in YEAR_RE.findall(line))
    return sorted(found)


def unique(values):
    seen = set()
    out = []
    for value in values:
        label = re.sub(r"\s+", " ", str(value or "")).strip()
        if len(label) < 2:
            continue
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(label)
    return out


def palitoy_keywords(text):
    names = []
    for line in text.splitlines():
        if not line.startswith("- ") or " | " not in line:
            continue
        parts = [part.strip() for part in line[2:].split(" | ")]
        if len(parts) < 4:
            continue
        if parts[0].lower().startswith("source"):
            continue
        names.append(parts[0])
        for part in parts:
            lower = part.lower()
            if lower.startswith("aka:"):
                names.extend(alias.strip() for alias in part.split(":", 1)[1].split(";"))
            if lower.startswith("years:"):
                continue
    return unique(names)


def variant_count_keywords(text):
    """Figure lines in the variant-count summary.

    Numbered lines are "1. Darth Vader — 71 versions ...". Factory group
    lines have no em dash, so they are not keywords.
    """
    names = []
    for line in text.splitlines():
        match = re.match(r"^(?:\d+\. |- )(.+?) —", line)
        if match:
            names.append(match.group(1).strip())
    return unique(names)


def recorded_keywords(text):
    names = []
    recorded = re.search(r"^(?:Figure|Accessory) Name: (.+)$", text, re.M)
    if recorded:
        names.append(recorded.group(1).strip())
    alias_line = re.search(r"^(?:Aliases|Collector Names \/ Aliases):\s*(.+)$", text, re.M)
    if alias_line:
        names.extend(part.strip() for part in re.split(r"[;,]", alias_line.group(1)))
    for match in re.finditer(r"^Figure Name: (.+)$", text, re.M):
        names.append(match.group(1).strip())
    return unique(names)[:40]


def index_file(folder, name, text):
    rel = f"{folder}/{name}" if folder else name
    topic = topic_for(folder, name)
    keywords = palitoy_keywords(text) if topic == "palitoy" else recorded_keywords(text)
    slug_bits = re.sub(r"\.[a-z0-9]+$", "", name, flags=re.I).replace("-", " ")
    if topic != "palitoy":
        extra = variant_count_keywords(text) if "variant-count" in name.lower() else []
        keywords = unique(keywords + extra + slug_bits.split())
        if "variant-count" not in name.lower():
            keywords = keywords[:40]
    return {
        "relPath": rel,
        "folder": folder,
        "topic": topic,
        "role": role_for(name),
        "name": keywords[0] if keywords else Path(name).stem,
        "aliases": keywords[1:12] if topic != "palitoy" else [],
        "keywords": keywords,
        "years": years_for(name, text, topic),
        "chars": len(text),
    }


def collect():
    files = []
    for folder in FOLDERS:
        folder_path = DATA / folder
        if not folder_path.is_dir():
            continue
        for path in sorted(folder_path.iterdir()):
            if not path.is_file() or path.suffix.lower() not in {".txt", ".json"}:
                continue
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                continue
            files.append(index_file(folder, path.name, text))
    factories = DATA / "factories.json"
    if factories.is_file():
        text = factories.read_text(encoding="utf-8")
        if text.strip():
            files.append(index_file("", factories.name, text))
    files.sort(key=lambda item: item["relPath"])
    return files


def main():
    payload = {
        "generated": "2026-10-04",
        "generator": "tools/build-retrieval-index.py",
        "note": "Not injected into chat. Topic routing reads this file. Palitoy roles: year, when, not-figures, overview, history. Variant-count role: summary.",
        "files": collect(),
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    topics = sorted({item["topic"] for item in payload["files"]})
    print(f"index {OUT.relative_to(ROOT)} files {len(payload['files'])} topics {', '.join(topics)}")


if __name__ == "__main__":
    main()
