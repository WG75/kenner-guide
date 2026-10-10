#!/usr/bin/env python3
"""Build missing Variant Villain figure and accessory reference files.

Fetches index and guide pages with a short delay. Writes only files that
do not already exist. Extracts section headings and short supporting lines
from each page; it does not copy a whole article. Cache lives in /tmp.
"""

import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path("/tmp/vv/cache")
UA = "kenner-guide-research/1.0 (Warren coverage build; polite, one request at a time)"
DELAY = 1.25
MAX_CHARS = 6500

INDEXES = [
    ("Star Wars", "https://www.variantvillain.com/characters/sw/"),
    ("The Empire Strikes Back", "https://www.variantvillain.com/characters/esb/"),
    ("Return of the Jedi", "https://www.variantvillain.com/characters/rotj/"),
    ("Power of the Force", "https://www.variantvillain.com/characters/potf/"),
    ("Droids and Ewoks", "https://www.variantvillain.com/characters/droids/"),
]
ACCESSORY_INDEX = "https://www.variantvillain.com/accessory-guide/"
EARLY_BIRD = {
    "luke skywalker",
    "princess leia organa",
    "chewbacca",
    "r2-d2",
}
VALID = {12, 20, 21, 31, 32, 41, 45, 47, 65, 77, 79, 92}
FLAG = {14, 17, 18, 30, 37, 48, 50, 70}
FLAG_TEXT = (
    "not on Warren's list of valid Kenner families "
    "(12, 20, 21, 31, 32, 41, 45, 47, 65, 77, 79, 92); "
    "regional/other family, flagged for his review"
)


def fetch(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:180]
    path = CACHE / key
    if path.exists() and path.stat().st_size > 500:
        return path.read_text(errors="replace")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as resp:
        data = resp.read().decode("utf-8", "replace")
    path.write_text(data)
    time.sleep(DELAY)
    return data


def clean(text):
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def page_chunk(raw):
    i = raw.find("page-content")
    if i < 0:
        i = 0
    chunk = raw[i:i + 220000]
    end = chunk.find("<footer")
    if end > 0:
        chunk = chunk[:end]
    return chunk


def sections(raw):
    chunk = page_chunk(raw)
    bits = re.split(r"<h[2-4][^>]*>", chunk, flags=re.I)
    out = []
    for bit in bits[1:]:
        title_m = re.match(r"(.*?)</h[2-4]>", bit, flags=re.I | re.S)
        if not title_m:
            continue
        title = clean(re.sub(r"<[^>]+>", " ", title_m.group(1)))
        if not title or len(title) > 80 or len(title) < 3:
            continue
        low = title.lower()
        if low in {
            "star wars", "the empire strikes back", "return of the jedi",
            "power of the force", "droids & ewoks", "droids and ewoks",
            "table of contents", "further reading", "wolff", "share",
            "related", "comments", "comment",
        }:
            continue
        rest = bit[title_m.end():]
        rest = re.split(r"<h[2-4][^>]*>", rest, maxsplit=1, flags=re.I)[0]
        texts = []
        for m in re.finditer(r"<(?:p|li|h[2-4])[^>]*>(.*?)</(?:p|li|h[2-4])>", rest, flags=re.I | re.S):
            line = clean(re.sub(r"<[^>]+>", " ", m.group(1)))
            if len(line) < 25:
                continue
            if line.lower().startswith("table of contents"):
                continue
            texts.append(line)
            if len(texts) >= 2:
                break
        if low.startswith("coo family") and not texts:
            continue
        if not texts and len(title) < 24:
            continue
        out.append((title, texts))
    # page title
    title = ""
    m = re.search(r"<h2[^>]*>(.*?)</h2>", chunk, flags=re.I | re.S)
    titles = re.findall(r"<h2[^>]*>(.*?)</h2>", chunk, flags=re.I | re.S)
    cleaned = [clean(re.sub(r"<[^>]+>", " ", t)) for t in titles]
    cleaned = [t for t in cleaned if t and t.lower() not in {"star wars", "the empire strikes back", "return of the jedi", "power of the force"}]
    if cleaned:
        title = cleaned[0]
    return title, out


def links(raw, pattern):
    found = []
    seen = set()
    for href, text in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', raw, flags=re.I | re.S):
        if not re.search(pattern, href):
            continue
        name = clean(re.sub(r"<[^>]+>", " ", text))
        if not name or href in seen:
            continue
        if any(x in href for x in ["/characters/sw/", "/characters/esb/", "/characters/rotj/", "/characters/potf/", "/characters/droids/"]):
            if href.rstrip("/").count("/") < 5:
                continue
        seen.add(href)
        found.append((name, href.split("#")[0]))
    return found


def slug_from_url(url):
    slug = url.rstrip("/").split("/")[-1]
    slug = slug.replace("rilfe", "rifle")
    return slug


def flag_numbers(text):
    def repl(m):
        n = int(m.group(1))
        if n in FLAG:
            return f"{m.group(0)} [{n}-back: {FLAG_TEXT}]"
        return m.group(0)
    return re.sub(r"\b(\d{1,3})\s*-?\s*backs?\b", repl, text, flags=re.I)


def debut_index():
    idx = {}
    folder = ROOT / "data" / "compatibility"
    for path in folder.glob("debut-cardbacks-reference-*.txt"):
        text = path.read_text()
        for part in re.split(r"\n(?=Figure Name: )", text):
            m = re.search(r"^Figure Name: (.+)$", part, re.M)
            if not m:
                continue
            debut = re.search(r"^Debut Kenner Cardback: (.+)$", part, re.M)
            idx[m.group(1).strip().lower()] = debut.group(1).strip() if debut else ""
    return idx


def norm(name):
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def debut_line(name, idx):
    key = name.lower().strip().replace("’", "'")
    if key in idx and idx[key]:
        return idx[key]
    n = norm(name)
    for k, v in idx.items():
        if norm(k) == n and v:
            return v
    # Site titles sometimes drop "Princess" or differ by a short prefix.
    # Use a match only when exactly one workbook name contains the other.
    contained = []
    for k, v in idx.items():
        nk = norm(k)
        if not v or not nk or not n:
            continue
        if n in nk or nk in n:
            contained.append((abs(len(nk) - len(n)), v))
    if len(contained) == 1 and contained[0][0] <= 16:
        return contained[0][1]
    return ""


def aliases_for(name):
    aliases = [name]
    for part in re.findall(r"\(([^)]+)\)", name):
        part = part.strip()
        if part and part not in aliases:
            aliases.append(part)
    # "Droids C-3PO" keeps both
    return aliases


def is_early_bird(name):
    n = norm(name)
    return n in EARLY_BIRD or n in {"luke skywalker farmboy", "artoo detoo"}


def render_figure(name, era, url, title, blocks, debut):
    lines = [
        f"Figure Name: {name}",
        "Aliases: " + "; ".join(aliases_for(name)),
        f"Packaging: {era}",
        "Category: Figure",
        "",
        "Overview:",
        f"{name} is a vintage Kenner Star Wars figure from the {era} line, as covered on Variant Villain. "
        "The notes below are only what that page states. Anything the page does not establish is unknown. Do not invent a variant.",
        "",
    ]
    if is_early_bird(name):
        lines.append(
            "Early Bird: this is one of the four Early Bird figures (Luke, Leia, Chewbacca, R2-D2). "
            "Working assumption, evidence probable: Early Bird figures are Unitoy or Kader only. No Taiwan Early Bird."
        )
    else:
        lines.append(
            "Early Bird: not an Early Bird figure. Early Bird is Luke Skywalker, Princess Leia Organa, Chewbacca and R2-D2 only."
        )
    lines.append("")
    if debut:
        lines.append(f"Debut Kenner Cardback: {debut}")
        lines.append(
            "That debut line is the workbook figure entry already in the debut-cardbacks reference, not a new claim. "
            "Compatible cardbacks are separate from factory matching. Factory matching is not established unless a source states the link."
        )
    else:
        lines.append(
            "Debut Kenner Cardback: unknown - not established in the reference workbook. "
            "Compatible cardbacks and factory matching are not established from the workbook for this figure."
        )
    lines.append("")
    lines.append("COO / factory and body notes from the source page (evidence: documented where the page states them):")
    used = 0
    for heading, texts in blocks:
        if heading.lower() == name.lower():
            continue
        bit = heading
        if texts:
            sentence = texts[0][:280]
            if len(texts[0]) > 280:
                sentence = sentence.rsplit(" ", 1)[0]
            bit += " — " + flag_numbers(sentence)
        lines.append(f"- {bit}")
        used += 1
        if used >= 18:
            lines.append("- Further sections exist on the source page and are not copied here.")
            break
    if used == 0:
        lines.append("- unknown. The fetched page did not yield section text. Do not guess factories or paint variants.")
    lines += [
        "",
        "Accessories:",
        "- See the accessory notes in the sections above. If no accessory is named there, what it came with is unknown from this file.",
        "",
        "Variant questions:",
        "1. Country of origin (COO) is the small text on the back of the legs saying where the figure was made. Use only the stamps named for this figure. A partial or cut-off country name counts as No COO.",
        "2. Which head, paint or body trait matches a section above?",
        "3. Which accessory mould or colour is with it?",
        "4. If carded, which cardback family (12, 20, 21, 31, 32, 41, 45, 47, 65, 77, 79, 92)? 48-back and regional numbers 14, 17, 18, 30, 37, 50 and 70 are not on that list.",
        "",
        "Sources:",
        url,
        "https://www.variantvillain.com/knowledge/introduction-to-coos/",
        "https://www.variantvillain.com/knowledge/factory-codes/",
        "",
    ]
    text = "\n".join(lines)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS - 80].rsplit("\n", 1)[0] + "\n\n[truncated to the retrieval cap]\nSources:\n" + url + "\n"
    return text


def render_accessory(name, url, blocks):
    lines = [
        f"Accessory Name: {name}",
        "Aliases: " + "; ".join(aliases_for(name)),
        "Category: Accessory",
        "",
        "Overview:",
        f"{name} is documented in the Variant Villain accessory guide. Notes below are only what that page states. Unstated moulds, colours and figure pairings are unknown.",
        "",
        "Which figures / mould and colour notes (evidence: documented where the page states them):",
    ]
    used = 0
    for heading, texts in blocks:
        if heading.lower() == name.lower():
            continue
        bit = heading
        if texts:
            sentence = texts[0][:280]
            if len(texts[0]) > 280:
                sentence = sentence.rsplit(" ", 1)[0]
            bit += " — " + flag_numbers(sentence)
        lines.append(f"- {bit}")
        used += 1
        if used >= 18:
            lines.append("- Further sections exist on the source page and are not copied here.")
            break
    if used == 0:
        lines.append("- unknown. The fetched page did not yield section text.")
    lines += [
        "",
        "Identification: use the mould and colour notes above. A COO stamp alone does not prove the accessory mould.",
        "Rarity: unknown unless a section above states it.",
        "",
        "Sources:",
        url,
        "https://www.variantvillain.com/accessory-guide/",
        "https://www.variantvillain.com/knowledge/factory-codes/",
        "",
    ]
    text = "\n".join(lines)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS - 80].rsplit("\n", 1)[0] + "\n\n[truncated to the retrieval cap]\nSources:\n" + url + "\n"
    return text


def main():
    figures = []
    for era, url in INDEXES:
        raw = fetch(url)
        prefix = url.rstrip("/") + "/"
        for name, href in links(raw, re.escape(prefix)):
            if href.rstrip("/") == url.rstrip("/"):
                continue
            # Stay on this era. Site-wide nav repeats other eras' character links.
            if prefix not in href:
                continue
            figures.append({"era": era, "name": name, "url": href})
    # unique by url
    seen = set()
    uniq = []
    for fig in figures:
        if fig["url"] in seen:
            continue
        seen.add(fig["url"])
        uniq.append(fig)
    accessories = []
    araw = fetch(ACCESSORY_INDEX)
    for name, href in links(araw, r"/accessory-guide/"):
        if href.rstrip("/") == ACCESSORY_INDEX.rstrip("/"):
            continue
        accessories.append({"name": name, "url": href})
    seen = set()
    auniq = []
    for acc in accessories:
        if acc["url"] in seen:
            continue
        seen.add(acc["url"])
        auniq.append(acc)

    debut = debut_index()
    fig_dir = ROOT / "data" / "figures"
    acc_dir = ROOT / "data" / "accessories"
    catalog_f = []
    catalog_a = []
    created_f = []
    created_a = []
    skipped_f = []
    skipped_a = []

    for fig in uniq:
        slug = slug_from_url(fig["url"])
        dest = fig_dir / f"{slug}-reference.txt"
        existing = list(fig_dir.glob(f"*{slug}*"))
        if dest.exists() or existing:
            skipped_f.append(fig["name"])
            # still catalog the real file
            path = dest if dest.exists() else existing[0]
            catalog_f.append({"name": fig["name"], "era": fig["era"], "file": f"figures/{path.name}", "url": fig["url"], "status": "existing"})
            continue
        raw = fetch(fig["url"])
        title, blocks = sections(raw)
        display = fig["name"] or title
        text = render_figure(display, fig["era"], fig["url"], title, blocks, debut_line(display, debut))
        dest.write_text(text)
        created_f.append(display)
        catalog_f.append({"name": display, "era": fig["era"], "file": f"figures/{dest.name}", "url": fig["url"], "status": "created"})
        print("figure", display, dest.name, len(text))

    for acc in auniq:
        slug = slug_from_url(acc["url"])
        dest = acc_dir / f"{slug}.txt"
        if dest.exists():
            skipped_a.append(acc["name"])
            catalog_a.append({"name": acc["name"], "file": f"accessories/{dest.name}", "url": acc["url"], "status": "existing"})
            continue
        raw = fetch(acc["url"])
        title, blocks = sections(raw)
        # Index link text is the accessory name. Page h2 is often the site
        # section label "ACCESSORIES", which must not replace it.
        generic = {"accessories", "accessory", "accessory guide", "guide", "star wars"}
        link_name = acc["name"].replace("\u200b", "").strip()
        page_name = (title or "").replace("\u200b", "").strip()
        if link_name and link_name.lower() not in generic:
            display = link_name
        elif page_name and page_name.lower() not in generic:
            display = page_name
        else:
            display = slug.replace("-", " ").title()
        text = render_accessory(display, acc["url"], blocks)
        dest.write_text(text)
        created_a.append(display)
        catalog_a.append({"name": display, "file": f"accessories/{dest.name}", "url": acc["url"], "status": "created"})
        print("accessory", display, dest.name, len(text))

    catalog = {"figures": catalog_f, "accessories": catalog_a}
    (ROOT / "data" / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")
    summary = {
        "figures_on_site": len(uniq),
        "figure_files_created": len(created_f),
        "figure_files_skipped": len(skipped_f),
        "accessories_on_site": len(auniq),
        "accessory_files_created": len(created_a),
        "accessory_files_skipped": len(skipped_a),
    }
    print(json.dumps(summary, indent=2))
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "coverage-build-summary.json").write_text(json.dumps({"summary": summary, "created_figures": created_f, "created_accessories": created_a}, indent=2) + "\n")


if __name__ == "__main__":
    main()
