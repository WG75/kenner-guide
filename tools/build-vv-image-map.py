#!/usr/bin/env python3
"""Build the Variant Villain hot-link map used by the chat UI.

Reads figure and accessory page URLs already stored in the repo, fetches any
page that is not already in the local HTML cache, and keeps a few photos per
page (overview, figure guide, COO family, accessory). Every kept image URL is
checked with HEAD, then a short GET if HEAD is not usable. Nothing is
downloaded into the repo: the map stores the remote URL and the source page.

The map is written to data-source/vv-images.json. The chat does not inject
that file into the model.
"""

import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data-source" / "vv-images.json"
COUNTS = ROOT / "data-source" / "vv-variant-counts.json"
HTML_CACHE = Path("/tmp/vv-image-map/html")
CHECK_CACHE = Path("/tmp/vv-image-map/checks.json")
UA = "VF-CB-research/1.0 (collector reference; polite crawl)"
PAGE_DELAY = 1.2
IMAGE_GAP = 0.2
FETCHED = "2026-10-04"

FAMILY_ORDER = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
FAMILY_FROM_ARABIC = {str(i): num for i, num in enumerate(FAMILY_ORDER, start=1)}
FAMILY_HEAD = re.compile(r"^COO Family\s+([IVXLC]+|\d+)\b", re.I)
GUIDE_HEAD = re.compile(r"FIGURE GUIDE|COO SHEET|COO GUIDE", re.I)
OVERVIEW_HEAD = re.compile(r"^table of contents$", re.I)
SKIP_URL = re.compile(
    r"wolff\.jpg|header-2\.jpg|vvlogo|logo-2\.gif|(?:^|/)logo\.gif|complianz|favicon|gravatar|emoji|"
    r"acrylic|display-case|gwacrylic|spacer|pixel\.gif",
    re.I,
)
IMAGE_EXT = re.compile(r"\.(?:jpe?g|png|gif|webp)(?:$|\?)", re.I)
SHEET_NAME = re.compile(r"coo|sheet", re.I)
RESIZE = re.compile(r"-\d+x\d+(?=\.(?:jpe?g|png|gif|webp)$)", re.I)
INDEX_PATHS = {
    "/characters",
    "/characters/sw",
    "/characters/esb",
    "/characters/rotj",
    "/characters/potf",
    "/characters/droids",
    "/accessory-guide",
}


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&#038;", "&").replace("&nbsp;", " ")
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def cache_key(url):
    return re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:180]


def html_candidates(url):
    key = cache_key(url)
    paths = [
        HTML_CACHE / key,
        Path("/tmp/vv-live-2026-10-04") / key,
        Path("/tmp/vv/cache") / key,
        Path("/tmp/vv-family-read") / key,
    ]
    if url.rstrip("/").endswith("/darth-vader"):
        paths.append(Path("/tmp/vv-vader.html"))
        paths.append(Path("/tmp/vv-family-read/vader.html"))
    return paths


class IndexRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        path = urllib.parse.urlparse(newurl).path.rstrip("/") or "/"
        if path in INDEX_PATHS:
            raise urllib.error.HTTPError(req.full_url, code, "redirected to an index", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OPENER = urllib.request.build_opener(IndexRedirect)


def fetch_page(url):
    for path in html_candidates(url):
        if path.exists() and path.stat().st_size > 500:
            return path.read_text(errors="replace"), "cache"
    HTML_CACHE.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with OPENER.open(req, timeout=40) as resp:
        final = resp.geturl()
        path = urllib.parse.urlparse(final).path.rstrip("/")
        if path in INDEX_PATHS:
            raise urllib.error.HTTPError(url, resp.status, "landed on an index", resp.headers, None)
        data = resp.read().decode("utf-8", "replace")
    (HTML_CACHE / cache_key(url)).write_text(data)
    time.sleep(PAGE_DELAY)
    return data, "fetch"


def page_chunk(raw):
    lower = raw.lower()
    start = lower.find("page-content")
    if start < 0:
        start = lower.find("<body")
    if start < 0:
        start = 0
    chunk = raw[start:]
    end = chunk.lower().find("<footer")
    if end > 0:
        chunk = chunk[:end]
    return chunk


def absolute_upload(url, page):
    if not url or url.startswith("data:"):
        return ""
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = "https://www.variantvillain.com" + url
    url = url.split("#")[0].split("?")[0]
    if not url.startswith("https://www.variantvillain.com/wp-content/uploads/"):
        return ""
    if not IMAGE_EXT.search(url):
        return ""
    if SKIP_URL.search(url):
        return ""
    return url


def stem_name(url):
    base = url.rsplit("/", 1)[-1]
    return RESIZE.sub("", base).lower()


def nearest_href(chunk, img_at, src):
    window = chunk[max(0, img_at - 1200):img_at]
    hrefs = re.findall(
        r'href="(https://www\.variantvillain\.com/wp-content/uploads/[^"]+)"',
        window,
        flags=re.I,
    )
    if not hrefs:
        return src
    href = absolute_upload(hrefs[-1], "")
    if href and stem_name(href) == stem_name(src):
        return href
    return src


def normalise_family(token):
    token = token.upper()
    if token.isdigit():
        return FAMILY_FROM_ARABIC.get(token, "")
    if token in FAMILY_ORDER:
        return token
    return ""


def alt_text(name, role, family, factory, page_alt):
    page_alt = clean(page_alt)
    if page_alt and page_alt.lower() not in {"image", "photo", "variant villain"}:
        return page_alt
    if role == "accessory":
        return f"{name}, Variant Villain accessory photo"
    if family:
        factory_bit = f", {factory}" if factory else ""
        return f"{name}, COO family {family}{factory_bit}"
    if role == "coo":
        return f"{name}, COO sheet"
    if role == "guide":
        return f"{name}, figure guide overview"
    return f"{name}, Variant Villain figure photo"


def extract_page(raw, page, name, kind):
    chunk = page_chunk(raw)
    family = ""
    factory = ""
    section = ""
    images = []
    seen_stems = set()
    family_seen = set()
    have_overview = False
    have_guide = False
    have_sheet = False

    def add(url, role, fam, fac, page_alt):
        nonlocal have_overview, have_guide, have_sheet
        url = absolute_upload(url, page)
        if not url:
            return
        stem = stem_name(url)
        if stem in seen_stems:
            return
        if role == "figure":
            if have_overview:
                return
            have_overview = True
        elif role == "guide":
            if have_guide:
                return
            have_guide = True
        elif role == "coo" and not fam:
            if have_sheet:
                return
            have_sheet = True
        elif fam:
            if fam in family_seen:
                return
            family_seen.add(fam)
        elif role == "accessory" and len([img for img in images if img["role"] == "accessory"]) >= 2:
            return
        seen_stems.add(stem)
        images.append({
            "url": url,
            "sourcePage": page,
            "alt": alt_text(name, role, fam, fac, page_alt),
            "role": role,
            "family": fam,
        })

    heading = ""
    for match in re.finditer(r"(<h[1-4][^>]*>.*?</h[1-4]>)|(<img\b[^>]*>)", chunk, flags=re.I | re.S):
        tag = match.group(0)
        if tag.lower().startswith("<h"):
            heading = clean(tag)
            fam = FAMILY_HEAD.match(heading)
            if fam:
                family = normalise_family(fam.group(1))
                factory = ""
                section = "family"
            elif GUIDE_HEAD.search(heading):
                family = ""
                factory = ""
                section = "guide"
            elif heading.lower() == "wolff" or heading.lower().startswith("further reading"):
                family = ""
                factory = ""
                section = "skip"
            elif OVERVIEW_HEAD.match(heading):
                family = ""
                factory = ""
                section = "overview"
            elif section == "family" and family and len(heading) <= 80:
                factory = heading.strip(" :")
            continue
        if section == "skip":
            continue
        src_match = re.search(r'\bsrc="([^"]+)"', tag, re.I)
        if not src_match:
            continue
        src = absolute_upload(src_match.group(1), page)
        if not src:
            continue
        alt_match = re.search(r'\balt="([^"]*)"', tag, re.I)
        page_alt = alt_match.group(1) if alt_match else ""
        if page_alt.lower().startswith("picture of"):
            continue
        before = chunk[max(0, match.start() - 800):match.start()]
        if "elementor-author-box" in before:
            continue
        url = nearest_href(chunk, match.start(), src)
        if SHEET_NAME.search(stem_name(url)) and kind == "figure":
            add(url, "coo", "", "", page_alt)
            continue
        if kind == "accessory":
            add(url, "accessory", "", heading if section != "skip" else "", page_alt)
            continue
        if section == "family" and family:
            add(url, "coo", family, factory, page_alt)
        elif section == "guide":
            add(url, "guide", "", "", page_alt)
        elif section in ("", "overview"):
            add(url, "figure", "", "", page_alt)

    if kind == "figure" and not have_sheet:
        for href in re.findall(
            r'href="(https://www\.variantvillain\.com/wp-content/uploads/[^"]+)"',
            chunk,
            flags=re.I,
        ):
            if SHEET_NAME.search(stem_name(href)):
                add(href, "coo", "", "", "")
                break

    def sort_key(img):
        if img["role"] == "coo" and not img["family"]:
            return (0, 0)
        if img["role"] == "figure":
            return (1, 0)
        if img["role"] == "guide":
            return (2, 0)
        if img["role"] == "accessory":
            return (3, 0)
        if img["family"] in FAMILY_ORDER:
            return (4, FAMILY_ORDER.index(img["family"]))
        return (5, 0)

    images.sort(key=sort_key)
    return images


def file_key(name):
    stem = name[:-4] if name.endswith(".txt") else name
    return re.sub(r"-reference(?:-\d+)?$", "", stem)


def read_texts(folder):
    out = []
    for path in sorted((ROOT / "data" / folder).glob("*.txt")):
        out.append((f"{folder}/{path.name}", path.read_text(errors="replace")))
    return out


def accessory_name(text, slug):
    match = re.search(r"^Accessory Name:\s*(.+)$", text, re.M)
    if match:
        return match.group(1).strip()
    return slug.replace("-", " ").title()


def collect_targets():
    counts = json.loads(COUNTS.read_text())
    figure_files = read_texts("figures")
    accessory_files = read_texts("accessories")
    by_url = {}
    by_slug = {}
    for rel, text in figure_files:
        urls = sorted(set(re.findall(
            r"https://www\.variantvillain\.com/characters/(?:sw|esb|rotj|potf|droids)/[a-z0-9-]+/",
            text,
        )))
        if urls:
            for page in urls:
                by_url.setdefault(page, []).append(rel)
        else:
            by_slug.setdefault(file_key(rel.split("/")[-1]), []).append(rel)
    targets = []
    for fig in counts["figures"]:
        url = fig["url"].rstrip("/") + "/"
        slug = url.rstrip("/").split("/")[-1]
        files = by_url.get(url, []) or by_slug.get(slug, [])
        targets.append({
            "id": "/".join(url.rstrip("/").split("/")[-2:]),
            "kind": "figure",
            "name": fig.get("index_name") or fig["name"],
            "page": url,
            "files": files,
        })
    seen_pages = {item["page"] for item in targets}
    accessory_pages = {}
    for rel, text in accessory_files:
        found = re.findall(r"https://www\.variantvillain\.com/accessory-guide/[a-z0-9-]+/", text)
        found = [url for url in found if url.rstrip("/").split("/")[-1] != "accessory-guide"][:1]
        slug = file_key(rel.split("/")[-1])
        if not found:
            guess = f"https://www.variantvillain.com/accessory-guide/{slug}/"
            found = [guess]
        for url in found:
            bucket = accessory_pages.setdefault(url, {"files": [], "name": "", "text": ""})
            if rel not in bucket["files"]:
                bucket["files"].append(rel)
            if not bucket["name"] or file_key(rel.split("/")[-1]) == url.rstrip("/").split("/")[-1]:
                bucket["name"] = accessory_name(text, url.rstrip("/").split("/")[-1])
                bucket["text"] = text
    for url, info in sorted(accessory_pages.items()):
        if url in seen_pages:
            continue
        targets.append({
            "id": "/".join(url.rstrip("/").split("/")[-2:]),
            "kind": "accessory",
            "name": info["name"],
            "page": url,
            "files": info["files"],
        })
    return targets


class Limiter:
    def __init__(self, gap):
        self.gap = gap
        self.lock = threading.Lock()
        self.nxt = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            delay = max(0.0, self.nxt - now)
            self.nxt = max(now, self.nxt) + self.gap
        if delay:
            time.sleep(delay)


def load_checks():
    if CHECK_CACHE.exists():
        try:
            return json.loads(CHECK_CACHE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_checks(checks):
    CHECK_CACHE.parent.mkdir(parents=True, exist_ok=True)
    CHECK_CACHE.write_text(json.dumps(checks, indent=2, sort_keys=True))


def image_magic(blob):
    if blob.startswith(b"\xff\xd8"):
        return True
    if blob.startswith(b"\x89PNG"):
        return True
    if blob.startswith(b"GIF8"):
        return True
    if blob.startswith(b"RIFF") and b"WEBP" in blob[:16]:
        return True
    return False


def probe_once(url, method):
    headers = {"User-Agent": UA}
    if method == "GET":
        headers["Range"] = "bytes=0-31"
    req = urllib.request.Request(url, headers=headers, method=method)
    with OPENER.open(req, timeout=25) as resp:
        status = getattr(resp, "status", 200)
        final = resp.geturl()
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        body = resp.read(64) if method == "GET" else b""
        return status, final, ctype, body


def check_image(url, checks, limiter):
    cached = checks.get(url)
    if cached and "ok" in cached:
        return cached
    limiter.wait()
    result = {"ok": False, "check": "", "status": 0}
    try:
        status, final, ctype, _body = probe_once(url, "HEAD")
        result.update(status=status, check="HEAD", type=ctype, final=final)
        if (
            status == 200
            and final.startswith("https://www.variantvillain.com/wp-content/uploads/")
            and ctype.startswith("image/")
        ):
            result["ok"] = True
            checks[url] = result
            return result
        if status not in (200, 403, 405, 501) and not ctype.startswith("image/"):
            checks[url] = result
            return result
    except Exception as err:
        result["headError"] = str(err)[:180]
    limiter.wait()
    try:
        status, final, ctype, body = probe_once(url, "GET")
        result.update(status=status, check="GET", type=ctype, final=final)
        host_ok = final.startswith("https://www.variantvillain.com/wp-content/uploads/")
        type_ok = ctype.startswith("image/") or image_magic(body)
        result["ok"] = host_ok and status in (200, 206) and type_ok
    except Exception as err:
        result["getError"] = str(err)[:180]
        result["ok"] = False
    checks[url] = result
    return result


def self_test():
    sample = """
    <div class="page-content">
      <h2>Wolff</h2>
      <img src="https://www.variantvillain.com/wp-content/uploads/2020/01/wolff.jpg" alt="Wolff">
      <h2>TABLE OF CONTENTS</h2>
      <a href="https://www.variantvillain.com/wp-content/uploads/2024/06/SW_DarthVader_NEW4-Kopie.jpg">
        <img src="https://www.variantvillain.com/wp-content/uploads/2024/06/SW_DarthVader_NEW4-Kopie-715x1536.jpg" alt="">
      </a>
      <h2>FIGURE GUIDE: Torso Mould and Colour OVERVIEW</h2>
      <img src="https://www.variantvillain.com/wp-content/uploads/2025/07/000_2_DarthVader_Chest_001.jpg" alt="">
      <h2>COO Family I:</h2>
      <h2>KADER</h2>
      <a href="https://www.variantvillain.com/wp-content/uploads/2025/07/001_DarthVader_Figure_Fam1_001.jpg">
        <img src="https://www.variantvillain.com/wp-content/uploads/2025/07/001_DarthVader_Figure_Fam1_001.jpg" alt="">
      </a>
      <h2>COO Family II:</h2>
      <img src="https://www.variantvillain.com/wp-content/uploads/2025/07/002_DarthVader_Figure_Fam2_001.jpg" alt="Family two photo">
      <img src="https://www.variantvillain.com/wp-content/uploads/2021/01/VVlogo.gif" alt="">
    </div>
    """
    images = extract_page(sample, "https://www.variantvillain.com/characters/sw/darth-vader/", "Darth Vader", "figure")
    urls = [img["url"] for img in images]
    assert not any("wolff" in url or "VVlogo" in url for url in urls)
    assert any(url.endswith("SW_DarthVader_NEW4-Kopie.jpg") for url in urls)
    assert not any("-715x1536" in url for url in urls)
    fam1 = next(img for img in images if img["family"] == "I")
    assert fam1["role"] == "coo"
    assert "KADER" in fam1["alt"]
    fam2 = next(img for img in images if img["family"] == "II")
    assert fam2["alt"] == "Family two photo"
    ad = """
    <div class="page-content">
      <h2>CAPE OVERVIEW</h2>
      <img src="https://www.variantvillain.com/wp-content/uploads/2024/02/LeiaCape.jpg" alt="">
      <img src="https://www.variantvillain.com/wp-content/uploads/2024/02/gw-acrylic-case.jpg" alt="GW Acrylic display case">
      <img src="https://www.variantvillain.com/wp-content/uploads/2024/02/LeiaCape_Kader.jpg" alt="">
      <img src="https://www.variantvillain.com/wp-content/uploads/2024/02/LeiaCape_extra.jpg" alt="">
    </div>
    """
    acc = extract_page(ad, "https://www.variantvillain.com/accessory-guide/leia-bespin-cape/", "Leia Bespin cape", "accessory")
    assert len(acc) == 2
    assert acc[0]["url"].endswith("LeiaCape.jpg")
    assert "acrylic" not in acc[0]["url"]
    assert all(img["role"] == "accessory" for img in acc)
    print("self-test ok")


def main():
    self_test()
    targets = collect_targets()
    checks = load_checks()
    limiter = Limiter(IMAGE_GAP)
    entries = []
    fetched = 0
    cached = 0
    errors = []
    pending = []
    for target in targets:
        try:
            raw, how = fetch_page(target["page"])
        except Exception as err:
            errors.append(f"{target['page']} {err}")
            entries.append({**target, "images": [], "error": str(err)[:180]})
            print("FAIL", target["page"])
            continue
        if how == "fetch":
            fetched += 1
        else:
            cached += 1
        images = extract_page(raw, target["page"], target["name"], target["kind"])
        pending.append((target, images))
        print(f"{how:5} {target['kind']:10} {len(images):2}  {target['name']}")

    unique = []
    seen = set()
    for _target, images in pending:
        for img in images:
            if img["url"] not in seen:
                seen.add(img["url"])
                unique.append(img["url"])
    print(f"checking {len(unique)} image URLs")

    def probe(url):
        return url, check_image(url, checks, limiter)

    results = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for done, (url, result) in enumerate(pool.map(probe, unique), start=1):
            results[url] = result
            if done % 40 == 0:
                save_checks(checks)
                print(f"  checked {done}/{len(unique)}")
    save_checks(checks)

    for target, images in pending:
        kept = []
        for img in images:
            result = results.get(img["url"]) or {}
            if not result.get("ok"):
                continue
            kept.append({
                "url": img["url"],
                "sourcePage": img["sourcePage"],
                "alt": img["alt"],
                "role": img["role"],
                "family": img["family"],
                "check": result.get("check") or "",
                "status": result.get("status") or 0,
            })
        entries.append({
            "id": target["id"],
            "kind": target["kind"],
            "name": target["name"],
            "page": target["page"],
            "files": target["files"],
            "images": kept,
        })

    def names(kind, with_photos):
        chosen = [
            entry["name"]
            for entry in entries
            if entry["kind"] == kind and bool(entry["images"]) == with_photos
        ]
        return sorted(set(chosen))

    payload = {
        "generated": FETCHED,
        "source": "https://www.variantvillain.com/",
        "note": (
            "Hot-link map for the chat UI. Not injected into the model. "
            "Each image URL was checked with HEAD or GET and returned an image from variantvillain.com."
        ),
        "pagesCached": cached,
        "pagesFetched": fetched,
        "errors": errors,
        "entries": entries,
        "coverage": {
            "figuresWithPhotos": names("figure", True),
            "figuresWithoutPhotos": names("figure", False),
            "accessoriesWithPhotos": names("accessory", True),
            "accessoriesWithoutPhotos": names("accessory", False),
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(
        f"wrote {OUT} figures {len(payload['coverage']['figuresWithPhotos'])} with / "
        f"{len(payload['coverage']['figuresWithoutPhotos'])} without; accessories "
        f"{len(payload['coverage']['accessoriesWithPhotos'])} with / "
        f"{len(payload['coverage']['accessoriesWithoutPhotos'])} without; "
        f"fetched {fetched}, cached {cached}, errors {len(errors)}"
    )


if __name__ == "__main__":
    main()
