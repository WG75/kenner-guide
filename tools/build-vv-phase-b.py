#!/usr/bin/env python3
"""Write Variant Villain paraphrase files from data-source/vv-phase-b.json.

Does not fetch the site. Photographs are not included. Each injected file
stays under 7,000 characters. The retrieval index is rebuilt at the end.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data-source" / "vv-phase-b.json"
OUT_DIR = ROOT / "data" / "references"
MAX_CHARS = 6500

SECTIONS = [
    {
        "key": "vehicles",
        "filename": "vv-vehicles",
        "topic": "vehicle",
        "role": "guide",
        "name": "Variant Villain vehicles and mini-rigs",
        "aliases": "vehicles, mini-rigs, mini rigs, die-cast, Glasslite TIE Fighter, Glasslite X-Wing, Landspeeder, special offer vehicles",
        "intro": (
            "These notes are short paraphrases of Variant Villain vehicle pages and of the mini-rig lines on the baggie guide's vehicles and playsets page. "
            "There is no separate mini-rig catalogue and no die-cast catalogue on the crawled site. "
            "A line marked presumed or unconfirmed stays that way. Photographs are not stored."
        ),
    },
    {
        "key": "playsets",
        "filename": "vv-playsets",
        "topic": "playset",
        "role": "guide",
        "name": "Variant Villain playsets",
        "aliases": "playsets, special offer playsets, Creature Cantina, Hoth Ice Planet, Death Star playset, Sandcrawler",
        "intro": (
            "These notes are short paraphrases of the playset lines on Variant Villain's vehicles and playsets page. "
            "That page is a baggie and special-offer guide, not a full playset catalogue. "
            "Pairings marked presumed or unconfirmed stay that way. Photographs are not stored."
        ),
    },
    {
        "key": "cardbacks",
        "filename": "vv-cardbacks",
        "topic": "cardback",
        "role": "guide",
        "name": "Variant Villain cardback guides",
        "aliases": "Palitoy cardbacks, Trilogo cardbacks, Meccano cardbacks, Glasslite cardbacks, Lili Ledy cardbacks, Top Toys cardbacks, Clipper cardbacks, Toy Toni cardbacks, punch guide, Darth Vader cardbacks, Yoda cardbacks",
        "intro": (
            "Company and character cardback guides from Variant Villain, in short paraphrase. "
            "The debut-cardback workbook remains the debut record for a named figure. "
            "These guides add the company matrices. Photographs are not stored."
        ),
    },
    {
        "key": "baggies",
        "filename": "vv-baggies",
        "topic": "reference",
        "role": "guide",
        "name": "Variant Villain baggie guide",
        "aliases": "baggies, mailers, multi-packs, Early Bird 4 packs, Palitoy baggies",
        "intro": (
            "Short paraphrase of the Variant Villain baggie guide, other than the vehicles and playsets page, which is filed separately. "
            "Photographs are not stored."
        ),
    },
    {
        "key": "coo",
        "filename": "vv-coo-notes",
        "topic": "coo",
        "role": "guide",
        "name": "Variant Villain COO guides",
        "aliases": "introduction to COOs, COO terminology, how to use the COO guides, country of origin guide",
        "intro": (
            "Short paraphrase of Variant Villain's COO articles. "
            "The existing COO glossary is still the definition of the term. "
            "Photographs are not stored."
        ),
    },
    {
        "key": "knowledge",
        "filename": "vv-knowledge",
        "topic": "reference",
        "role": "guide",
        "name": "Variant Villain knowledge notes",
        "aliases": "101 reference guide, accessory production, factory codes, vintage price stickers",
        "intro": (
            "Short paraphrase of the remaining Variant Villain knowledge articles: the 101 guide, accessory production, factory codes and price stickers. "
            "Vendor-codes remains the factory list used for a named factory. Photographs are not stored."
        ),
    },
    {
        "key": "glasslite",
        "filename": "vv-glasslite",
        "topic": "variant",
        "role": "guide",
        "name": "Glasslite figure guide",
        "aliases": "Glasslite, Glasslite figures, Brazil",
        "intro": "Short paraphrase of the Variant Villain Glasslite figure guide. The Glasslite vehicles are filed with the vehicle notes. Photographs are not stored.",
    },
    {
        "key": "lili-ledy",
        "filename": "vv-lili-ledy",
        "topic": "variant",
        "role": "guide",
        "name": "Lili Ledy guide",
        "aliases": "Lili Ledy, Lilly Ledy",
        "intro": "Short paraphrase of the Variant Villain Lili Ledy index. Most character pages in that guide redirect to figure dossiers already stored, so they are not copied again. Photographs are not stored.",
    },
    {
        "key": "poch",
        "filename": "vv-poch",
        "topic": "variant",
        "role": "guide",
        "name": "Poch and PBP guide",
        "aliases": "Poch, PBP, Poch guide",
        "intro": "Short paraphrase of the Variant Villain Poch index. Most character pages in that guide redirect to figure dossiers already stored, so they are not copied again. Photographs are not stored.",
    },
    {
        "key": "top-toys",
        "filename": "vv-top-toys",
        "topic": "variant",
        "role": "guide",
        "name": "Top Toys guide",
        "aliases": "Top Toys",
        "intro": "Short paraphrase of the Variant Villain Top Toys guide. Photographs are not stored.",
    },
    {
        "key": "droids",
        "filename": "vv-droids-line",
        "topic": "variant",
        "role": "guide",
        "name": "Droids line variation guide",
        "aliases": "Droids cartoon figures, Jann Tosh, Jord Dusat, Kea Moll",
        "intro": "Short paraphrase of the Variant Villain Droids variation guide, including figures that are not in the character index. Photographs are not stored.",
    },
    {
        "key": "kenner",
        "filename": "vv-kenner-hard-torso",
        "topic": "variant",
        "role": "guide",
        "name": "Kenner hard-torso and mould-colour notes",
        "aliases": "hard torso, mould colour variants, mold color variants",
        "intro": "Short paraphrase of the Variant Villain Kenner hard-torso and mould-colour pages. Photographs are not stored.",
    },
    {
        "key": "bootlegs",
        "filename": "vv-bootlegs",
        "topic": "variant",
        "role": "guide",
        "name": "Variant Villain bootlegs",
        "aliases": "bootlegs, knock-offs, knockoffs, fakes",
        "intro": "Short paraphrase of the Variant Villain bootleg pages. A bootleg is not a Kenner factory variant. Photographs are not stored.",
    },
]


def load():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def is_vehicle_page(page):
    url = page["url"].lower()
    return any(token in url for token in (
        "glasslite-tie-fighter",
        "glasslite-tie-interceptor",
        "glasslite-x-wing",
    ))


def is_playset_fact(fact):
    return bool(re.search(r"playset|adventure set|cantina|death star|sandcrawler", fact, re.I))


def is_vehicle_fact(fact):
    return bool(re.search(
        r"mini[- ]?rig|\bMLC-3\b|\bPDT-8\b|\bCAP-2\b|\bMTV-7\b|\bINT-4\b|"
        r"\bTIE\b|tie fighter|x-wing|landspeeder|snowspeeder|cloud car|falcon|"
        r"transporter|dewback|wampa|vehicle",
        fact,
        re.I,
    ))


def is_shared_offer_fact(fact):
    return bool(re.search(r"sears|special offer|baggie|MOC|carded|unconfirmed|presumed|catalogue", fact, re.I))


def group_pages(pages):
    groups = {item["key"]: [] for item in SECTIONS}
    for page in pages:
        url = page["url"].lower()
        section = page["section"]
        if section == "cardbacks" or "cardback" in url:
            groups["cardbacks"].append(page)
            continue
        if is_vehicle_page(page):
            groups["vehicles"].append(page)
            continue
        if "special-offer-items" in url:
            vehicle_facts = []
            play_facts = []
            for fact in page["facts"]:
                play = is_playset_fact(fact)
                vehicle = is_vehicle_fact(fact)
                shared = is_shared_offer_fact(fact)
                if play:
                    play_facts.append(fact)
                if vehicle or (shared and not play):
                    vehicle_facts.append(fact)
                elif shared and play:
                    vehicle_facts.append(fact)
            if vehicle_facts:
                groups["vehicles"].append({**page, "title": "Vehicles, mini-rigs and special-offer vehicles", "facts": vehicle_facts})
            if play_facts:
                groups["playsets"].append({**page, "title": "Playsets and special-offer playsets", "facts": play_facts})
            continue
        if section == "baggies":
            groups["baggies"].append(page)
            continue
        if section == "knowledge":
            if any(token in url for token in ("coo", "country-of-origin")):
                groups["coo"].append(page)
            else:
                groups["knowledge"].append(page)
            continue
        if section == "bootlegs":
            groups["bootlegs"].append(page)
            continue
        if section == "variations":
            if "glasslite" in url:
                groups["glasslite"].append(page)
            elif "lili-ledy" in url:
                groups["lili-ledy"].append(page)
            elif "poch" in url:
                groups["poch"].append(page)
            elif "top-toys" in url or url.rstrip("/").endswith("/top-toys"):
                groups["top-toys"].append(page)
            elif "droids" in url:
                groups["droids"].append(page)
            elif "kenner" in url:
                groups["kenner"].append(page)
            else:
                groups["kenner"].append(page)
            continue
        groups["knowledge"].append(page)
    return groups


def header(spec):
    return (
        f"Name: {spec['name']}\n"
        f"Aliases: {spec['aliases']}\n"
        f"Topic: {spec['topic']}\n"
        f"Role: {spec['role']}\n\n"
        f"{spec['intro']}\n"
    )


def page_block(page, fetched):
    lines = [
        page["title"],
        f"Source name: Variant Villain. Source URL: {page['url']} Reliability: high. Recorded: {fetched}.",
    ]
    for fact in page["facts"]:
        fact = fact.rstrip(":").strip()
        if not fact:
            continue
        lines.append(f"- {fact}")
    return "\n".join(lines)


def pack(spec, pages, fetched):
    if not pages:
        return []
    head = header(spec)
    parts = []
    current = [head.rstrip(), ""]
    current_len = len(head) + 1
    for page in pages:
        block = page_block(page, fetched)
        if current_len + len(block) + 2 > MAX_CHARS and len(current) > 2:
            parts.append("\n".join(current).strip() + "\n")
            current = [head.rstrip(), ""]
            current_len = len(head) + 1
        if len(block) + len(head) + 2 > MAX_CHARS:
            # Keep the citation and as many bullets as fit.
            kept = []
            size = len(head) + 2
            for line in block.splitlines():
                if size + len(line) + 1 > MAX_CHARS:
                    break
                kept.append(line)
                size += len(line) + 1
            block = "\n".join(kept)
        current.append(block)
        current.append("")
        current_len += len(block) + 2
    parts.append("\n".join(current).strip() + "\n")
    return parts


def write_parts(spec, parts):
    written = []
    for index, text in enumerate(parts):
        suffix = "" if index == 0 else f"-{index + 1}"
        name = f"{spec['filename']}{suffix}.txt"
        path = OUT_DIR / name
        if len(text) > 7000:
            raise SystemExit(f"{name} is {len(text)} characters")
        path.write_text(text, encoding="utf-8")
        written.append(name)
    return written


def remove_stale(keep):
    for path in OUT_DIR.glob("vv-*.txt"):
        if path.name not in keep:
            path.unlink()


def main():
    payload = load()
    fetched = payload["fetched"]
    groups = group_pages(payload["pages"])
    keep = set()
    for spec in SECTIONS:
        parts = pack(spec, groups[spec["key"]], fetched)
        keep.update(write_parts(spec, parts))
        print(f"{spec['filename']} pages {len(groups[spec['key']])} files {len(parts)}")
    remove_stale(keep)
    subprocess.check_call([sys.executable, str(ROOT / "tools" / "build-retrieval-index.py")])


if __name__ == "__main__":
    main()
