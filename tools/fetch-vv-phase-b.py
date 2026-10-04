#!/usr/bin/env python3
"""Fetch Variant Villain sections that are not already in the figure corpus.

Reads the sitemaps already saved by a polite crawl, or the URLs listed below.
Stores HTML under /tmp/vv-phase-b (not committed) and writes a fact snapshot
to data-source/vv-phase-b.json. Photographs are not saved. One request at a
time, with a pause between them.

The snapshot holds short paraphrases: headings, name-like lines, and at most
a few shortened factual sentences. It is not a copy of the pages.
"""

import json
import re
import subprocess
import sys
import time
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data-source" / "vv-phase-b.json"
CACHE = Path("/tmp/vv-phase-b/html")
UA = "VF-CB-research/1.0 (collector reference; polite crawl)"
PAUSE = 1.2
FETCHED = "2026-10-04"

SKIP_TAGS = {"script", "style", "noscript", "svg"}
CAPTURE_CLASSES = (
    "elementor-widget-text-editor",
    "elementor-heading-title",
    "wp-caption-text",
    "elementor-image-box-title",
    "elementor-image-box-description",
)
DROP_LINES = {
    "skip to content",
    "a guide to vintage star wars figures & accessories",
    "table of contents",
    "further reading",
    "credits",
    "introduction",
    "knowledge",
    "gallery",
}
PHOTO = re.compile(
    r"photo|picture from|image needed|courtesy of|google images|click on the logos|"
    r"cookie policy|all original content|intellectual property|manage cookie",
    re.I,
)
FLUFF = re.compile(
    r"\b(I am|I'm|I'll|I will|let's rewind|lets rewind|IMO|wonderful|feel free to contact|"
    r"not a native|too long|less people will read)\b",
    re.I,
)
CARD_GUIDES = {
    "https://www.variantvillain.com/characters/rotj/luke-jedi-cardback-guide/",
    "https://www.variantvillain.com/characters/sw/jawa-cardback-guide/",
}


class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.capture_depth = 0
        self.stack = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
            self.stack.append((tag, False))
            return
        cls = dict(attrs).get("class", "")
        start = any(token in cls for token in CAPTURE_CLASSES)
        if start:
            self.capture_depth += 1
        self.stack.append((tag, start))
        if self.capture_depth and tag in ("p", "li", "h1", "h2", "h3", "h4", "br", "tr"):
            self.parts.append("\n")
        if self.capture_depth and tag == "li":
            self.parts.append("- ")

    def handle_endtag(self, tag):
        if not self.stack:
            return
        capturing = False
        if self.stack[-1][0] == tag:
            _, capturing = self.stack.pop()
        else:
            for index in range(len(self.stack) - 1, -1, -1):
                if self.stack[index][0] == tag:
                    capturing = any(flag for _, flag in self.stack[index:])
                    self.stack = self.stack[:index]
                    break
            else:
                return
        if capturing:
            self.capture_depth = max(0, self.capture_depth - 1)
            self.parts.append("\n")
        if tag in SKIP_TAGS and self.skip:
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if self.skip or self.capture_depth <= 0:
            return
        self.parts.append(data)


def extract_lines(html):
    parser = Extract()
    parser.feed(html)
    text = "".join(parser.parts)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.lower() in DROP_LINES:
            continue
        if lines and lines[-1] == line:
            continue
        lines.append(line)
    return lines


def british(text):
    swaps = (
        (r"\bcolors\b", "colours"),
        (r"\bcolor\b", "colour"),
        (r"\bgray\b", "grey"),
        (r"\bmotorized\b", "motorised"),
        (r"\bmolded\b", "moulded"),
        (r"\bmolds\b", "moulds"),
        (r"\bmold\b", "mould"),
        (r"\bcatalogs\b", "catalogues"),
        (r"\bcatalog\b", "catalogue"),
    )
    for pattern, repl in swaps:
        text = re.sub(pattern, repl, text, flags=re.I)
    return text


def facty(text):
    return bool(re.search(
        r"\d|Kenner|Palitoy|Glasslite|Lili|Poch|PBP|factory|COO|card|baggie|mailer|"
        r"mould|figure|vehicle|playset|mini|TIE|X-Wing|issued|released|Hong Kong|"
        r"Taiwan|China|Macau|bootleg",
        text,
        re.I,
    ))


NAV_LINES = {
    "baggie guide", "baggie index by character", "sw baggies", "esb baggies", "rotj baggies",
    "palitoy baggies", "euro baggies", "single figure mailers", "> single figure mailers",
    "miscellaneous baggies", "multi-packs", "vehicles & playsets", "popys (japan)",
    "global promotional items", "shipping cases", "early bird 4-packs", "esb full colour 6 packs",
    "fake baggies", "pre-production, qc sign-offs", "bulk baggie finds",
    "kenners replacement parts program", "kenner replacement parts program",
    "gallery > glasslite", "> back to glasslite main menu", "back to glasslite main menu",
}


def shorten_sentence(sentence):
    sentence = re.sub(r",? help make .+$", "", sentence, flags=re.I)
    sentence = re.sub(r"\btruly\b", "", sentence, flags=re.I)
    sentence = FLUFF.sub("", sentence)
    sentence = re.sub(r"\s{2,}", " ", sentence).strip(" ,;-")
    words = sentence.split()
    if len(words) > 28:
        sentence = " ".join(words[:28]).rstrip(",;")
    return sentence


def paraphrase_lines(lines, url):
    long_cap = 8 if "/knowledge/" in url else 3
    facts = []
    long_kept = 0
    seen = set()
    for line in lines:
        if re.match(r"^(photo|picture|image|photos)\b", line, re.I):
            continue
        line = re.sub(r"\b(photo|picture)s? courtesy of [^.,]{0,48}", "", line, flags=re.I)
        line = re.sub(r"\bphoto from google images\b", "", line, flags=re.I)
        line = british(line).replace("–", "-").replace("—", "-").replace("’", "'")
        line = re.sub(r"\s+", " ", line).strip(" -")
        body = line[2:].strip() if line.startswith("- ") else line
        body = body.rstrip(":").strip()
        if len(body) < 3 or body.lower() in NAV_LINES:
            continue
        if re.search(r"\b(I am|I'm|I would|if you have an example)\b", body, re.I):
            continue
        if len(body) < 8 and not re.search(r"\d", body):
            continue
        pieces = [body]
        if len(body) > 140:
            pieces = []
            for sentence in re.split(r"(?<=[.!?])\s+", body):
                if long_kept >= long_cap:
                    break
                sentence = shorten_sentence(sentence)
                if len(sentence) < 12 or not facty(sentence):
                    continue
                pieces.append(sentence)
                long_kept += 1
            if not pieces:
                continue
        for body in pieces:
            key = body.lower()
            if key in seen:
                continue
            seen.add(key)
            facts.append(body)
            if len(facts) >= 72:
                return facts
    return facts


def title_from(html, lines):
    match = re.search(r"<title>([^<]+)</title>", html, re.I)
    if match:
        title = unescape(re.sub(r"\s+", " ", match.group(1)).strip())
        title = re.sub(r"\s+[–-]\s+Variant Villain\s*$", "", title, flags=re.I)
        if title:
            return title
    return lines[0] if lines else "Untitled"


def classify(url):
    path = urlparse(url).path.lower()
    if path.rstrip("/") in ("",) or "cookie" in path or "privacy" in path or "impressum" in path:
        return "skip-legal"
    if "/gallery" in path:
        return "gallery"
    if path.startswith("/accessory-guide"):
        return "skip-accessory"
    if path.startswith("/characters/") and url.rstrip("/") + "/" not in CARD_GUIDES and url.rstrip("/") not in {u.rstrip("/") for u in CARD_GUIDES}:
        return "skip-figure"
    if "cardback" in path:
        return "cardbacks"
    if "/baggie-guide/" in path or path.rstrip("/").endswith("/baggie-guide"):
        return "baggies"
    if "/knowledge/" in path or path.rstrip("/").endswith("/knowledge"):
        return "knowledge"
    if "/bootlegs" in path:
        return "bootlegs"
    if "/variations/" in path or path.rstrip("/").endswith("/variations"):
        return "variations"
    if "article_launch" in path or "hallo-welt" in path or "/category/" in path:
        return "skip-empty"
    return "other"


def wanted(url):
    kind = classify(url)
    return not kind.startswith("skip-") or kind == "gallery"


def load_urls():
    urls = []
    for name in ("/tmp/vv-pages.xml", "/tmp/tvv-pages.xml"):
        text = Path(name).read_text(encoding="utf-8")
        urls.extend(re.findall(r"<loc>(.*?)</loc>", text))
    urls.extend(CARD_GUIDES)
    cleaned = []
    seen = set()
    for url in urls:
        url = url.replace("&amp;", "&").split("?")[0]
        if not url.endswith("/"):
            url += "/"
        if url in seen:
            continue
        seen.add(url)
        if wanted(url):
            cleaned.append(url)
    return cleaned


def cache_path(url):
    slug = re.sub(r"[^a-z0-9]+", "-", urlparse(url).netloc + urlparse(url).path).strip("-")
    return CACHE / f"{slug[:180]}.html"


def fetch(url):
    path = cache_path(url)
    if path.is_file() and path.stat().st_size > 500:
        return path.read_text(encoding="utf-8", errors="replace"), 200, ""
    CACHE.mkdir(parents=True, exist_ok=True)
    header_path = path.with_suffix(".hdr")
    proc = subprocess.run(
        ["curl", "-sS", "-A", UA, "--max-time", "45", "-D", str(header_path), "-o", str(path), "-w", "%{http_code}", url],
        check=False,
        capture_output=True,
    )
    status_text = proc.stdout.decode("utf-8", "replace").strip()
    try:
        status = int(status_text or "0")
    except ValueError:
        status = 0
    headers = header_path.read_text(encoding="utf-8", errors="replace") if header_path.is_file() else ""
    location = ""
    for line in headers.splitlines():
        if line.lower().startswith("location:"):
            location = line.split(":", 1)[1].strip()
    time.sleep(PAUSE)
    if status == 200 and path.is_file() and path.stat().st_size > 500:
        return path.read_text(encoding="utf-8", errors="replace"), 200, ""
    if path.is_file() and status != 200:
        path.unlink()
    return "", status, location


def reextract():
    payload = json.loads(OUT.read_text(encoding="utf-8"))
    for page in payload["pages"]:
        path = cache_path(page["url"])
        if not path.is_file():
            continue
        html = path.read_text(encoding="utf-8", errors="replace")
        lines = extract_lines(html)
        page["title"] = title_from(html, lines)
        page["facts"] = paraphrase_lines(lines, page["url"])
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"reextracted {len(payload['pages'])} pages")


def main():
    if "--reextract" in sys.argv:
        reextract()
        return
    pages = []
    skipped = []
    errors = []
    urls = load_urls()
    print(f"urls {len(urls)}", flush=True)
    for index, url in enumerate(urls, 1):
        kind = classify(url)
        html, status, location = fetch(url)
        if status in {301, 302, 303, 307, 308} and location:
            target = location.split("#")[0]
            if any(token in target for token in ("/characters/", "/accessory-guide/")):
                skipped.append({
                    "url": url,
                    "title": "",
                    "reason": "redirects to a figure or accessory page already in the corpus",
                    "location": location,
                    "section": kind,
                })
                print(f"{index}/{len(urls)} redirect {location}", flush=True)
                continue
            html, status, _location = fetch(target if target.endswith("/") else target + "/")
        if status != 200 or not html:
            errors.append({"url": url, "http": status, "reason": "fetch failed", "location": location})
            print(f"{index}/{len(urls)} FAIL {status} {url}", flush=True)
            continue
        lines = extract_lines(html)
        facts = paraphrase_lines(lines, url)
        title = title_from(html, lines)
        if kind == "gallery" or len(facts) < 2:
            reason = "image gallery" if kind == "gallery" else "no prose facts"
            skipped.append({"url": url, "title": title, "reason": reason, "section": kind})
            print(f"{index}/{len(urls)} skip {reason} {url}", flush=True)
            continue
        pages.append({
            "url": url,
            "title": title,
            "section": kind,
            "http": status,
            "facts": facts,
        })
        print(f"{index}/{len(urls)} ok {kind} {len(facts)} {title}", flush=True)
    payload = {
        "fetched": FETCHED,
        "source_name": "Variant Villain",
        "reliability": "high",
        "note": "Short paraphrases of pages that were not already stored as figure or accessory dossiers. Photographs were not saved. Reliability is high because this project treats Variant Villain as the collector source for variants.",
        "pages": pages,
        "skipped": skipped,
        "errors": errors,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT} pages {len(pages)} skipped {len(skipped)} errors {len(errors)}")


if __name__ == "__main__":
    main()
