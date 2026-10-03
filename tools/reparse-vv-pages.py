#!/usr/bin/env python3
"""Re-parse cached Variant Villain pages into reference files.

Keeps every list that follows a colon or heading. Drops page-stub sentences,
shop ads, and photo-credit names. Does not overwrite the original hand-written
dossiers. Thin figures get a separate other-source block from the Wikipedia
Kenner list, the Rebelscum photo archive, and imperialgunnery when a page
actually states the fact. Unsourced fields stay unknown.
"""

import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path("/tmp/vv/cache")
EXTRA = Path("/tmp/vv/extra")
UA = "kenner-guide-research/1.0 (Warren coverage quality pass; polite, one request at a time)"
DELAY = 1.25
MAX_CHARS = 6800

VALID = {12, 20, 21, 31, 32, 41, 45, 47, 65, 77, 79, 92}
FLAG = {14, 17, 18, 30, 37, 48, 50, 70}
FLAG_NOTE = (
    "not on Warren's list of valid Kenner families "
    "(12, 20, 21, 31, 32, 41, 45, 47, 65, 77, 79, 92); "
    "regional/other family, flagged for his review"
)
BOILER_FIG = "The notes below are only what that page states"
BOILER_ACC = "Notes below are only what that page states"
SKIP_TITLES = {
    "star wars", "the empire strikes back", "return of the jedi",
    "the return of the jedi", "power of the force", "droids & ewoks",
    "droids and ewoks", "ewoks guide", "further reading", "share",
    "related", "comments", "comment", "accessories",
}
PERSONS = {"wolff", "chihuahua", "walkie", "brian angel", "nick eppinga", "jabbawookie"}
FACTORY_WORDS = re.compile(
    r"smile|unitoy|kader|lili|ledy|poch|meccano|universal|hong kong|taiwan|"
    r"coo|mould|mold|family|guide|blaster|staff|cape|glasslite|palitoy",
    re.I,
)
MONTHS = r"January|February|March|April|May|June|July|August|September|October|November|December"
DATE_ONLY = re.compile(rf"^(?:{MONTHS})\s+\d{{1,2}},\s+\d{{4}}$")
THANKS = re.compile(r"(?i)^(many thanks|special thanks|i['’]d like to thank|i would like to thank)\b")


def fetch(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 400:
        return dest.read_text(errors="replace")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as resp:
        raw = resp.read()
    # Rebelscum pages are Windows-1252. UTF-8 pages decode cleanly first.
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", "replace")
    dest.write_text(text)
    time.sleep(DELAY)
    return text


def cache_for(url):
    key = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:180]
    return CACHE / key


def clean(text):
    text = html.unescape(text or "")
    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def page_chunk(raw):
    # The first "page-content" hit can be a head meta snippet. Prefer the
    # elementor page body, which is the block that actually holds the guide.
    marker = 'data-elementor-type="wp-page"'
    i = raw.find(marker)
    if i < 0:
        i = raw.find("page-content")
    if i < 0:
        i = 0
    chunk = raw[i:i + 280000]
    end = chunk.find("<footer")
    if end > 0:
        chunk = chunk[:end]
    return chunk


def html_lines(fragment):
    fragment = re.sub(r"<script[\s\S]*?</script>", " ", fragment, flags=re.I)
    fragment = re.sub(r"<style[\s\S]*?</style>", " ", fragment, flags=re.I)
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"</(?:p|li|div|tr|h\d|td)>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<li[^>]*>", "\n- ", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    lines = []
    seen = set()
    for raw_line in html.unescape(fragment).splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        lines.append(line)
    return lines


def is_person_heading(level, title):
    low = title.lower().strip()
    if low in PERSONS:
        return True
    if str(level) != "4":
        return False
    if FACTORY_WORDS.search(title) or re.search(r"\d", title):
        return False
    words = title.split()
    if not 1 <= len(words) <= 4:
        return False
    return all(re.match(r"[A-Z][a-zA-Z.'-]+$", word) for word in words)


def drop_line(line):
    low = line.lower().strip(" -")
    if not low or low in {"-", "accessories", "coo sheet", "figure guide", "further reading", "gallery", "reproductions"}:
        return True
    if "sorry, content not available" in low:
        return True
    if DATE_ONLY.match(line.lstrip("- ").strip()):
        return True
    if low.startswith("image credit") or low.startswith("photo credit"):
        return True
    if low.startswith("> back") or low.startswith("gallery >") or low.startswith("back to "):
        return True
    if "page-content" in low or "elementor" in low or low.startswith("skip to content"):
        return True
    if "gw acrylic" in low or "display case" in low:
        return True
    if low == "mi: unitoy":
        return False
    if THANKS.search(line.lstrip("- ").strip()) and not re.search(r"(?i)\b(card|coo|mould|mold|back|colour|color|factory)\b", line):
        return True
    if re.search(r"(?i)(couldn.t have done it without|fine gentlemen|in no particular order|special thanks)", line):
        return True
    if re.search(r"(?i)text\s*&\s*photography by", line):
        return True
    return False


def salvage(line):
    text = line.lstrip("- ").strip()
    text = re.sub(
        r"(?i)^many thanks to [A-Za-z .'-]{2,40} for allowing us to share\s+",
        "The page shares ",
        text,
    )
    return text.strip()


def flag_text(text):
    if "[50-back:" in text or "flagged for his review" in text:
        # Still flag other numbers in the same line, but do not nest the same note.
        pass

    def repl(match):
        number = int(match.group(1))
        if number not in FLAG:
            return match.group(0)
        if f"[{number}-back:" in text:
            return match.group(0)
        return f"{match.group(0)} [{number}-back: {FLAG_NOTE}]"

    text = re.sub(r"\b(\d{1,3})\s*-?\s*(?:backs?|bk)\b", repl, text, flags=re.I)
    text = re.sub(r"\b(14|17|18|30|37|48|50|70)-([A-Z])\b", lambda m: repl(m) if False else m.group(0), text)
    # Card codes such as 48-E are the same flagged family.
    def repl_code(match):
        number = int(match.group(1))
        if f"[{number}-back:" in text:
            return match.group(0)
        return f"{match.group(0)} [{number}-back: {FLAG_NOTE}]"

    text = re.sub(r"\b(14|17|18|30|37|48|50|70)-([A-Z])\b", repl_code, text)
    return text


def split_index_blob(line):
    if not re.search(r"\b[IVX]{1,4}:", line):
        return [line]
    parts = re.split(r"\s+(?=[IVX]{1,4}:)", line)
    out = []
    for part in parts:
        part = re.sub(r"(?i)\b(coo sheet|figure guide|further reading)\b", " ", part)
        part = re.sub(r"\s+", " ", part).strip(" -")
        if part:
            out.append(part)
    return out or [line]


def useful_lines(lines, toc=False):
    kept = []
    bullet_text = set()
    for line in lines:
        bullet = line.startswith("- ")
        text = salvage(line)
        if drop_line(text):
            continue
        pieces = split_index_blob(text) if toc and not bullet else [text]
        for piece in pieces:
            if drop_line(piece):
                continue
            if not bullet and piece.lower() in bullet_text:
                continue
            if bullet:
                bullet_text.add(piece.lower())
            if toc and not bullet:
                low = piece.lower()
                interesting = (
                    FACTORY_WORDS.search(piece)
                    or re.search(r"\b[IVX]{1,4}:", piece)
                    or len(piece) > 70
                    or piece.endswith(":")
                )
                if not interesting:
                    continue
            if piece.lower() == "mi: unitoy":
                piece = "M1: Unitoy"
            kept.append(("- " if bullet else "") + piece if not piece.startswith("- ") else piece)
    # A non-bullet that repeats a bullet is an image alt. Drop it.
    bullets = {ln[2:].lower() for ln in kept if ln.startswith("- ")}
    return [ln for ln in kept if ln.startswith("- ") or ln.lower() not in bullets]


def sections_from(raw):
    chunk = page_chunk(raw)
    marks = list(re.finditer(r"<h([2-4])[^>]*>(.*?)</h\1>", chunk, flags=re.I | re.S))
    sections = []
    credit_notes = []
    for index, mark in enumerate(marks):
        title = clean(re.sub(r"<[^>]+>", " ", mark.group(2)))
        if not title:
            continue
        end = marks[index + 1].start() if index + 1 < len(marks) else len(chunk)
        body = useful_lines(html_lines(chunk[mark.end():end]), toc=title.lower() == "table of contents")
        low = title.lower().strip()
        if is_person_heading(mark.group(1), title):
            credit_notes.extend(body)
            continue
        if low in SKIP_TITLES or low.startswith("gw acrylic") or "display case" in low:
            continue
        if low == "table of contents":
            title = "Families and notes named on the page index"
        if "reproductions" in low or low.startswith("r1"):
            joined = " ".join(body).lower()
            if not body or "coming soon" in joined and len(joined) < 80:
                continue
        if not body and low.startswith("coo family"):
            continue
        if not body:
            continue
        sections.append((title, body))
    if credit_notes:
        sections.append(("Notes from the page with the photo credit name removed", credit_notes))
    return sections


def strip_mark(line):
    return line[2:].strip() if line.startswith("- ") else line.strip()


def parse_sequence(lines):
    """Group a colon heading with the list under it, including subheadings."""
    items = []
    index = 0
    while index < len(lines):
        text = strip_mark(lines[index])
        index += 1
        children = []
        if text.endswith(":"):
            while index < len(lines):
                nxt = lines[index]
                nxt_text = strip_mark(nxt)
                if (not nxt.startswith("- ")) and (not nxt_text.endswith(":")) and len(nxt_text) > 110:
                    break
                if nxt_text.endswith(":"):
                    sub = [nxt]
                    index += 1
                    while index < len(lines) and lines[index].startswith("- "):
                        sub.append(lines[index])
                        index += 1
                    children.extend(parse_sequence(sub))
                    continue
                children.append((nxt_text, []))
                index += 1
        elif re.match(r"^(?:F\d|M\d)\b", text) and len(text) > 40:
            sub = []
            while index < len(lines):
                nxt_text = strip_mark(lines[index])
                if re.match(r"^(?:F\d|M\d)\b", nxt_text):
                    break
                if len(nxt_text) > 160 and not lines[index].startswith("- ") and not nxt_text.endswith(":"):
                    break
                sub.append(lines[index])
                index += 1
            children = parse_sequence(sub)
        items.append((text, children))
    return items


def emit_items(items, indent, out):
    for text, children in items:
        if text.endswith(":") and not children:
            # A long sentence that ends with a colon is pointing at a photo or a
            # later section. Do not call that list unknown. A short label with
            # nothing under it is unknown.
            words = text[:-1].split()
            if len(words) >= 6:
                text = text[:-1].rstrip() + "."
            else:
                text = text + " unknown (the page does not list them in text)."
        out.append(("  " * indent) + "- " + flag_text(text))
        emit_items(children, indent + 1, out)


def render_lines(lines, indent):
    out = []
    emit_items(parse_sequence(lines), indent, out)
    return out


def cardback_lines(sections):
    found = []
    seen = set()
    for _title, lines in sections:
        for line in lines:
            text = line[2:] if line.startswith("- ") else line
            if not re.search(r"(?i)(cardbacks?|\d{2}\s*-?\s*bk|\d{2}\s*-?\s*backs?\b|trilogo|tri-logo|\bpotf\b)", text):
                continue
            if text.endswith(":"):
                continue
            if len(text) < 20:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(flag_text(text))
    return found


def workbook_index():
    found = {}
    folder = ROOT / "data" / "compatibility"
    for path in sorted(folder.glob("debut-cardbacks-reference-*.txt")):
        text = path.read_text(errors="replace")
        for part in re.split(r"\n(?=Figure Name: )", text):
            name = re.search(r"^Figure Name: (.+)$", part, re.M)
            if not name:
                continue
            debut = re.search(r"^Debut Kenner Cardback: (.+)$", part, re.M)
            rel = f"data/compatibility/{path.name}"
            found[name.group(1).strip().lower()] = (rel, name.group(1).strip(), debut.group(1).strip() if debut else "")
    return found


def norm(name):
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def workbook_for(name, aliases, index):
    keys = [name.lower().strip()]
    for alias in aliases:
        keys.append(alias.lower().strip())
    for key in keys:
        if key in index:
            return index[key]
    n = norm(name)
    hits = []
    for key, value in index.items():
        if norm(key) == n:
            hits.append(value)
    if len(hits) == 1:
        return hits[0]
    return None


def header_of(text):
    fields = {}
    for line in text.splitlines():
        if not line.strip():
            break
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    debut = ""
    url = ""
    for line in text.splitlines():
        if line.startswith("Debut Kenner Cardback:") and not debut:
            debut = line.split(":", 1)[1].strip()
        if line.startswith("https://www.variantvillain.com/") and "/knowledge/" not in line and not url:
            url = line.strip()
    return fields, debut, url


def load_catalog():
    index = json.loads((ROOT / "data" / "catalog.json").read_text())
    rows = {}
    for part_name in index.get("parts", []):
        part = json.loads((ROOT / "data" / part_name).read_text())
        for fig in part.get("figures", []):
            rows[fig["file"]] = fig
        for acc in part.get("accessories", []):
            rows[acc["file"]] = acc
    return rows


def generated(path):
    text = path.read_text(errors="replace")
    if "Continued reference" in text.split("\n\n", 1)[0] or "\nContinued reference" in text[:500]:
        return False
    return (
        BOILER_FIG in text
        or BOILER_ACC in text
        or "kept in full from the Variant Villain page" in text
        or "Colour lists, mould lists and figure pairings" in text
    )


def render_figure(fields, debut, url, sections, book):
    name = fields.get("Figure Name", "")
    aliases = fields.get("Aliases", name)
    packaging = fields.get("Packaging", "")
    line_name = packaging[4:] if packaging.lower().startswith("the ") else packaging
    from_line = f" from the {line_name} line" if line_name else ""
    lines = [
        f"Figure Name: {name}",
        f"Aliases: {aliases}",
        f"Packaging: {packaging}",
        "Category: Figure",
        "",
        "Overview:",
        (
            f"{name} is a vintage Kenner Star Wars figure{from_line}. "
            "Lists under a heading or a colon are kept in full from the Variant Villain page. "
            "Anything that page does not establish is unknown. Do not invent a variant."
        ),
        "",
        "Early Bird: not an Early Bird figure. Early Bird is Luke Skywalker, Princess Leia Organa, Chewbacca and R2-D2 only.",
        "",
        f"Debut Kenner Cardback: {debut or 'unknown - not established in the reference workbook'}",
    ]
    if book:
        rel, book_name, _book_debut = book
        lines.append(
            f"Workbook block: {rel} under Figure Name: {book_name}. "
            "That block is the debut record. Compatible cardbacks on the Variant Villain page are not a substitute for it. "
            "Factory matching is not established unless a source states the link."
        )
    else:
        lines.append(
            "Workbook block: none. No debut-cardbacks block matches this figure name. "
            "Debut Kenner Cardback stays unknown."
        )
    cards = cardback_lines(sections)
    lines.append("")
    if cards:
        lines.append("Cardbacks named on the Variant Villain page (documented cardings, not a confirmed debut):")
        for card in cards:
            lines.append(f"- {card}")
        lines.append("")
    lines.append("COO / factory and body notes from the source page (evidence: documented where the page states them):")
    used = False
    for title, body in sections:
        if title.lower() == name.lower():
            continue
        lines.append(f"- {title}")
        lines.extend(render_lines(body, 1))
        used = True
    if not used:
        lines.append("- unknown. The page does not state a factory, paint or mould variant. Do not guess one.")
    lines += [
        "",
        "Accessories:",
        "- Named in the notes above when the page states them. If none are named, what it came with is unknown from the Variant Villain page.",
        "",
        "Variant questions:",
        "1. What COO stamp is on the figure (Hong Kong, Taiwan, China, Macau, No COO, Mexico, or another)?",
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
    return "\n".join(lines)


def render_accessory(fields, url, sections):
    name = fields.get("Accessory Name", "")
    aliases = fields.get("Aliases", name)
    lines = [
        f"Accessory Name: {name}",
        f"Aliases: {aliases}",
        "Category: Accessory",
        "",
        "Overview:",
        (
            f"{name} is documented in the Variant Villain accessory guide. "
            "Colour lists, mould lists and figure pairings that follow a colon or a heading are kept in full. "
            "Unstated moulds, colours and figure pairings are unknown."
        ),
        "",
        "Which figures / mould and colour notes (evidence: documented where the page states them):",
    ]
    used = False
    for title, body in sections:
        if title.lower() == name.lower():
            continue
        lines.append(f"- {title}")
        lines.extend(render_lines(body, 1))
        used = True
    if not used:
        lines.append("- unknown. The page does not state moulds, colours or figure pairings.")
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
    return "\n".join(lines)


def split_if_needed(text, kind):
    if len(text) <= MAX_CHARS:
        return [text if text.endswith("\n") else text + "\n"]
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("COO / factory") or line.startswith("Which figures"))
    end = next(i for i, line in enumerate(lines) if line.startswith("Accessories:") or line.startswith("Identification:"))
    head = lines[:start + 1]
    body = lines[start + 1:end]
    tail = lines[end:]

    def size_first(chunk):
        return len("\n".join(head + chunk + tail)) + 40

    def size_later(chunk):
        # Room for the repeated name header and the debut line on later parts.
        return len("\n".join(chunk)) + 1100

    # A heading and the indented lines under it stay in the same part.
    blocks = []
    for line in body:
        top = line.startswith("- ") and not line.startswith("  ")
        if top or not blocks:
            blocks.append([line])
        else:
            blocks[-1].append(line)
    chunks = []
    current = []
    for block in blocks:
        limit = size_first if not chunks else size_later
        if current and limit(current + block) > MAX_CHARS:
            chunks.append(current)
            current = list(block)
        else:
            current.extend(block)
    if current:
        chunks.append(current)
    fixed = []
    for index, chunk in enumerate(chunks):
        limit = size_first if index == 0 and not fixed else size_later
        if limit(chunk) <= MAX_CHARS:
            fixed.append(chunk)
            continue
        sub = []
        for line in chunk:
            if sub and limit(sub + [line]) > MAX_CHARS:
                fixed.append(sub)
                sub = [line]
                limit = size_later
            else:
                sub.append(line)
        if sub:
            fixed.append(sub)
    total = len(fixed)
    rendered = []
    for number, chunk in enumerate(fixed, start=1):
        if number == 1:
            out = []
            inserted = False
            for line in head:
                out.append(line)
                if not inserted and line.startswith("Category:"):
                    out.append(f"Part: 1 of {total}")
                    inserted = True
            out.extend(chunk)
            out.append("")
            out.append("Continued in the next part.")
            out.extend(tail)
        else:
            out = []
            for line in head:
                if line.startswith(("Figure Name:", "Accessory Name:", "Aliases:", "Packaging:", "Category:")):
                    out.append(line)
            out.append(f"Part: {number} of {total}")
            out.append("")
            out.append("Continued reference. The lines below repeat the debut record so this part can answer a cardback question.")
            for line in head:
                if line.startswith("Debut Kenner Cardback:") or line.startswith("Workbook block:"):
                    out.append(line)
            out.append("")
            out.append(head[-1])
            out.extend(chunk)
            if number < total:
                out.append("")
                out.append("Continued in the next part.")
            out.append("")
            out.append("Sources:")
            for line in tail:
                if line.startswith("http"):
                    out.append(line)
                    break
        body_text = "\n".join(out).rstrip() + "\n"
        if len(body_text) > 7000:
            raise SystemExit(f"part {number} still over the cap ({len(body_text)} chars)")
        rendered.append(body_text)
    return rendered


def part_paths(path, count):
    if count == 1:
        return [path]
    stem = path.stem
    paths = [path]
    for number in range(2, count + 1):
        paths.append(path.with_name(f"{stem}-{number}{path.suffix}"))
    return paths


def notes_chars(text):
    capture = False
    chars = 0
    for line in text.splitlines():
        if line.startswith("COO / factory") or line.startswith("Which figures"):
            capture = True
            continue
        if capture and line.startswith(("Accessories:", "Identification:", "Other sources", "Variant questions:")):
            break
        if capture:
            chars += len(line)
    return chars


def wikipedia_rows():
    raw = (Path("/tmp/vv/cross/0.html")).read_text(errors="replace")
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    rows = re.findall(
        r'([A-Z])\s+(\d{2})-Back\s+"([^"]+)"\s+(.+?)\s+No\.\s+((?:No\.\s*)?\d+\s*(?:/\s*(?:No\.\s*)?\d+\s*)?)(\d{4})',
        text,
    )
    return rows


def wiki_for(name, rows):
    n = re.sub(r"[^a-z0-9]+", "", name.lower())
    hits = []
    for wave, back, line, fig, number, year in rows:
        fig_n = re.sub(r"[^a-z0-9]+", "", fig.lower())
        if fig_n == n:
            hits.append((wave, back, line, fig.strip(), number.strip(), year))
    uniq = []
    seen = set()
    for hit in hits:
        key = (hit[1], hit[3], hit[4])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(hit)
    return uniq


def rebelscum_index():
    raw = Path("/tmp/vv/vinfigures.html").read_text(errors="replace")
    links = []
    for href, text in re.findall(r'href="([^"]+)"[^>]*>(.*?)</a>', raw, flags=re.I | re.S):
        if "vint" not in href.lower():
            continue
        label = clean(re.sub(r"<[^>]+>", " ", text))
        if label:
            links.append((href, label))
    return links


def compact_name(value):
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def name_tokens(value):
    stop = {"the", "in", "of", "with", "and", "a", "an"}
    squashed = value.lower().replace("-", "")
    return [tok for tok in re.findall(r"[a-z0-9]+", squashed) if tok not in stop and len(tok) > 1]


def rebelscum_match(name, links):
    target = compact_name(name)
    exact = []
    for href, label in links:
        for part in re.split(r"/", label):
            base = re.sub(r"\([^)]*\)", " ", part)
            if compact_name(part) == target or compact_name(base) == target:
                exact.append((href, label))
                break
    hrefs = {href for href, _label in exact}
    if len(hrefs) == 1:
        return exact[0]
    wanted = name_tokens(name)
    if not wanted:
        return None
    scored = []
    for href, label in links:
        have = name_tokens(label)
        if all(tok in have for tok in wanted):
            scored.append((len(set(have) - set(wanted)), href, label))
    if not scored:
        return None
    best = min(item[0] for item in scored)
    chosen = [item for item in scored if item[0] == best]
    hrefs = {item[1] for item in chosen}
    if len(hrefs) != 1:
        return None
    return (chosen[0][1], chosen[0][2])


RS_LABELS = [
    "Source",
    "Date Stamp",
    "Release Date",
    "Carded Availability",
    "Assortment No.",
    "Retail",
    "Weapons and Accessories",
    "Point of Interest",
    "Comments",
    "Major Variations",
]


def rebelscum_facts(page):
    text = re.sub(r"<script[\s\S]*?</script>", " ", page, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(?:p|div|tr|td|li|h\d)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("Source:"):
            start = i
            break
    facts = {}
    current = None
    bucket = []

    def flush():
        if current:
            value = " ".join(bucket).strip()
            value = re.split(r"Text & Photography", value)[0].strip()
            facts[current] = re.sub(r"\s+", " ", value)

    for line in lines[start:]:
        if line.startswith("Back To ") or line.startswith("SPECIAL FEATURE"):
            break
        label = next((name for name in RS_LABELS if line.lower().startswith(name.lower())), None)
        if label and line.rstrip().endswith(":"):
            flush()
            current = label
            bucket = []
            rest = line.split(":", 1)[1].strip()
            if rest:
                bucket.append(rest)
            continue
        if current:
            bucket.append(line)
    flush()
    return facts


def trim_variation(text):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= 900:
        return text
    cut = text[:900]
    stop = cut.rfind(". ")
    if stop > 400:
        cut = cut[: stop + 1]
    return cut


def enrich_block(name, wiki, rs_facts, rs_url, ig_notes):
    lines = [
        "",
        "Other sources (these do not replace the Variant Villain notes or the workbook Debut Kenner Cardback line):",
    ]
    if wiki:
        lines.append("Wikipedia list of Kenner Star Wars action figures (evidence: documented):")
        for _wave, back, line, fig, number, year in wiki:
            lines.append(f"- Lists {fig} on the {back}-back \"{line}\" card, No. {number}, {year}.")
        lines.append("- https://en.wikipedia.org/wiki/List_of_Kenner_Star_Wars_action_figures")
        lines.append("- That list entry is not the Debut Kenner Cardback. The workbook line is the debut record.")
    else:
        lines.append("- Wikipedia list of Kenner Star Wars action figures: unknown. No row matched this figure name.")
        lines.append("- https://en.wikipedia.org/wiki/List_of_Kenner_Star_Wars_action_figures")
    if rs_facts:
        lines.append(f"Rebelscum photo archive (evidence: documented), {rs_url}")
        for label in ("Source", "Date Stamp", "Release Date", "Carded Availability", "Assortment No.", "Weapons and Accessories", "Point of Interest"):
            value = rs_facts.get(label, "")
            if value:
                lines.append(f"- {label}: {flag_text(value)}")
            else:
                lines.append(f"- {label}: unknown")
        major = rs_facts.get("Major Variations", "")
        if major:
            lines.append(f"- Major variations: {trim_variation(major)}")
        else:
            lines.append("- Major variations: unknown")
        lines.append("- Comment paragraphs on that page are not copied. Where the point of interest names a debut and the workbook debut line does not, the debut is conflicting sources, unresolved. The workbook line stays the debut record.")
    else:
        lines.append("- Rebelscum photo archive: unknown. No archive page matched this figure name.")
        lines.append("- https://www.rebelscum.com/vinfigures.asp")
    if ig_notes:
        lines.extend(ig_notes)
    else:
        lines.append("- imperialgunnery.com: unknown for this figure. No section on the staff/axe or helmet/hood guides named it.")
        lines.append("- https://imperialgunnery.com/staffs-axes.htm")
        lines.append("- https://imperialgunnery.com/helmets-hoods.htm")
    lines.append("- theswca.com: unknown for production COO, paint and debut. Single archive-object pages were not used as production variants.")
    lines.append("- https://theswca.com/")
    lines.append("")
    return lines


def ig_sections(page, names):
    text = re.sub(r"<script[\s\S]*?</script>", " ", page, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(?:p|div|li|h\d|tr|td)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line and len(line) > 2]
    notes = {name: [] for name in names}
    for name in names:
        token = name.split("(")[0].strip()
        if len(re.sub(r"[^a-z0-9]", "", token)) < 4:
            continue
        pattern = re.compile(rf"\b{re.escape(token)}\b", re.I)
        for index, line in enumerate(lines):
            if not pattern.search(line):
                continue
            window = []
            for extra in lines[index:index + 8]:
                if re.search(r"(?i)copyright|navigation|home", extra):
                    break
                if window and not pattern.search(extra) and len(extra.split()) <= 7 and extra[:1].isupper() and not extra.endswith("."):
                    break
                window.append(extra)
                if len(" ".join(window)) > 420:
                    break
            snippet = re.sub(r"\s+", " ", " ".join(window)).strip()
            snippet = re.sub(r"\b([A-Z]) ([a-z]{4,})", r"\1\2", snippet)
            if len(snippet) < 50:
                continue
            key = snippet[:80].lower()
            if any(key == item[:80].lower() for item in notes[name]):
                continue
            notes[name].append(snippet[:420])
            if len(notes[name]) >= 2:
                break
    return notes


def insert_enrichment(text, block_lines):
    lines = text.splitlines()
    # Place the block before Sources, and drop a previous other-source block.
    cleaned = []
    skipping = False
    for line in lines:
        if line.startswith("Other sources"):
            skipping = True
            continue
        if skipping:
            if line.startswith("Sources:"):
                skipping = False
            else:
                continue
        cleaned.append(line)
    out = []
    inserted = False
    for line in cleaned:
        if line.startswith("Sources:") and not inserted:
            out.extend(block_lines)
            inserted = True
        out.append(line)
    if not inserted:
        out.extend(block_lines)
    return "\n".join(out).rstrip() + "\n"


def main():
    catalog = load_catalog()
    books = workbook_index()
    written = []
    thin_targets = []
    for folder, label in (("figures", "Figure Name"), ("accessories", "Accessory Name")):
        for path in sorted((ROOT / "data" / folder).glob("*.txt")):
            rel = f"{folder}/{path.name}"
            if not generated(path):
                continue
            # Part files created by an earlier split of a generated page are regenerated from the base name.
            if re.search(r"-\d+\.txt$", path.name) and not path.name.endswith("-2.txt"):
                pass
            text = path.read_text(errors="replace")
            fields, debut, file_url = header_of(text)
            meta = catalog.get(rel, {})
            # Prefer a URL whose page is already cached. Wicket's catalog row can
            # point at the Droids URL while the file cites the ROTJ page.
            candidates = [file_url, meta.get("url") or ""]
            url = next((item for item in candidates if item and cache_for(item).exists()), "")
            if not url:
                url = meta.get("url") or file_url
            if not url:
                print("skip-no-url", rel)
                continue
            cached = cache_for(url)
            if not cached.exists():
                raw = fetch(url, cached)
            else:
                raw = cached.read_text(errors="replace")
            sections = sections_from(raw)
            if label == "Figure Name":
                book = workbook_for(fields.get("Figure Name", ""), [a.strip() for a in fields.get("Aliases", "").split(";")], books)
                rendered = render_figure(fields, debut, url, sections, book)
            else:
                rendered = render_accessory(fields, url, sections)
            parts = split_if_needed(rendered, label)
            paths = part_paths(path, len(parts))
            for dest, body in zip(paths, parts):
                if len(body) > 7000:
                    raise SystemExit(f"over cap {dest} {len(body)}")
                dest.write_text(body if body.endswith("\n") else body + "\n")
                written.append((str(dest.relative_to(ROOT)), len(body)))
            for number in range(len(paths) + 1, 12):
                extra = path.with_name(f"{path.stem}-{number}{path.suffix}")
                if not extra.exists():
                    continue
                old = extra.read_text(errors="replace")
                if "Continued reference" in old or "Continued in the next part" in old:
                    extra.unlink()
                    print("removed-stale", extra.name)
            body_chars = notes_chars(paths[0].read_text())
            for number in range(2, 8):
                extra = path.with_name(f"{path.stem}-{number}{path.suffix}")
                if extra.exists():
                    body_chars += notes_chars(extra.read_text(errors="replace"))
            # Paploo is included even when the page lists paints and cardings.
            # Other figures are enriched only when the page body is still a stub.
            if label == "Figure Name" and (path.name == "paploo-reference.txt" or body_chars < 900):
                thin_targets.append((paths[0], fields.get("Figure Name", ""), body_chars))
            print(f"{rel} sections={len(sections)} chars={len(parts[0])} parts={len(parts)} notes={body_chars}")

    print("WROTE", len(written))
    print("THIN", len(thin_targets))
    for path, name, body_chars in thin_targets:
        print(f"  thin {name} notes={body_chars}")

    rows = wikipedia_rows()
    links = rebelscum_index()
    # One fetch of the two imperialgunnery guides, then match names.
    ig_names = [name for _path, name, _chars in thin_targets]
    ig_pages = []
    for url, slug in (
        ("https://imperialgunnery.com/staffs-axes.htm", "staffs-axes.htm"),
        ("https://imperialgunnery.com/helmets-hoods.htm", "helmets-hoods.htm"),
    ):
        ig_pages.append((url, fetch(url, EXTRA / slug)))
    ig_by_name = {name: [] for name in ig_names}
    for url, page in ig_pages:
        found = ig_sections(page, ig_names)
        for name, snippets in found.items():
            for snippet in snippets:
                ig_by_name[name].append((url, snippet))

    for path, name, _chars in thin_targets:
        text = path.read_text(errors="replace")
        wiki = wiki_for(name, rows)
        match = rebelscum_match(name, links)
        rs_facts = None
        rs_url = ""
        if match:
            href, _label = match
            rs_url = href if href.startswith("http") else "https://www.rebelscum.com" + ("" if href.startswith("/") else "/") + href
            page = fetch(rs_url, EXTRA / (re.sub(r"[^a-z0-9]+", "-", rs_url.lower()).strip("-")[:120]))
            rs_facts = rebelscum_facts(page)
            if not rs_facts.get("Source") and not rs_facts.get("Point of Interest"):
                rs_facts = None
        ig_notes = []
        tokens = [tok for tok in name_tokens(name) if len(tok) > 3]
        kept_ig = []
        for url, snippet in ig_by_name.get(name, []):
            if snippet.lower().startswith("contents:") or snippet.count(",") > 6:
                continue
            head = snippet[:140].lower()
            if tokens and not all(tok in head for tok in tokens):
                continue
            kept_ig.append((url, snippet))
        if kept_ig:
            ig_notes.append("imperialgunnery.com (evidence: documented where the page states it; 'we believe' stays probable):")
            seen_url = set()
            for url, snippet in kept_ig[:2]:
                evidence = "probable" if re.search(r"we believe|likely", snippet, re.I) else "documented"
                ig_notes.append(f"- ({evidence}) {snippet}")
                if url not in seen_url:
                    ig_notes.append(f"- {url}")
                    seen_url.add(url)
        block = enrich_block(name, wiki, rs_facts, rs_url, ig_notes)
        placed = False
        candidates = [path]
        part_no = 2
        while True:
            nxt = path.with_name(f"{path.stem}-{part_no}{path.suffix}")
            if not nxt.exists():
                break
            candidates.append(nxt)
            part_no += 1
        for cand in candidates:
            updated = insert_enrichment(cand.read_text(errors="replace"), block)
            if len(updated) <= 7000:
                cand.write_text(updated)
                print("enriched", cand.name, len(updated), "wiki", len(wiki), "rs", bool(rs_facts))
                placed = True
                break
        if placed:
            continue
        dest = path.with_name(f"{path.stem}-{part_no}{path.suffix}")
        fields, _debut, src = header_of(path.read_text(errors="replace"))
        extra = [
            f"Figure Name: {fields.get('Figure Name', name)}",
            f"Aliases: {fields.get('Aliases', name)}",
            f"Part: {part_no}",
            "",
            "Continued reference. Debut Kenner Cardback is in part 1.",
            "",
        ] + block + ["", "Sources:", src, ""]
        extra_text = "\n".join(extra).rstrip() + "\n"
        if len(extra_text) > 7000:
            raise SystemExit(f"enrichment part over cap {dest} {len(extra_text)}")
        dest.write_text(extra_text)
        print("enriched-part", dest.name, len(extra_text), "wiki", len(wiki), "rs", bool(rs_facts))


if __name__ == "__main__":
    main()
