#!/usr/bin/env python3
"""Gap report: Wikipedia Kenner figures and original accessories vs Variant Villain.

Figures are data/kenner-debut-figures.json (the Wikipedia Kenner list).
Accessories are the original accessory-guide pages in data/catalog-*.json,
plus any debut bubble piece that does not match one of those pages.
"""

import csv
import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ART = Path("/opt/cursor/artifacts")
CACHE = Path("/tmp/vv-coo-2026-10-10")
UA = "kenner-guide-research/1.0 (Variant Villain gap report; polite, one request at a time)"
DELAY = 0.8
WIKI = "https://en.wikipedia.org/wiki/List_of_Kenner_Star_Wars_action_figures"

DETAIL = re.compile(
    r"(?i)\b(moulds?|molds?|\bm\d\b|smile|unitoy|unitoys|kader|lili|ledy|poch|pbp|"
    r"hong kong|taiwan|macau|macao|no coo|made in|factory|factories)\b"
)
MENU = re.compile(
    r"(?i)^(introduction to coos|coo terms|how to use the coo guides|bootlegs|"
    r"bootlegs by country|bootlegs by character|table of contents|further reading|"
    r"related|share|comments?|cookie policy.*)$"
)


def norm(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def fetch(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:180]
    path = CACHE / key
    if path.exists() and path.stat().st_size > 500:
        return path.read_text(errors="replace"), False
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = resp.read().decode("utf-8", "replace")
    path.write_text(data)
    time.sleep(DELAY)
    return data, True


def page_lines(raw):
    match = re.search(r'(?is)<div[^>]+class="[^"]*page-content[^"]*"[^>]*>(.*)$', raw)
    chunk = match.group(1) if match else raw
    text = re.sub(r"(?is)<script[\s\S]*?</script>", " ", chunk)
    text = re.sub(r"(?is)<style[\s\S]*?</style>", " ", text)
    text = re.sub(r"(?i)</(p|h\d|li|div|tr)>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", "\n", text)
    text = html.unescape(text).replace("\xa0", " ")
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line and len(line) < 240 and not MENU.match(line):
            lines.append(line)
        if len(lines) > 400:
            break
    return lines


BOILER = re.compile(r"(?i)don.?t rely on just the coo|mould, paint colour, plastic colour")


def page_has_details(raw):
    hits = [line for line in page_lines(raw) if DETAIL.search(line) and not BOILER.search(line)]
    return bool(hits), (hits[0][:140] if hits else "")


def load_json(path):
    return json.loads(Path(path).read_text())


def catalogs():
    figures = []
    accessories = []
    for path in sorted((ROOT / "data").glob("catalog-*.json")):
        data = load_json(path)
        figures.extend(data.get("figures") or [])
        accessories.extend(data.get("accessories") or [])
    return figures, accessories


def tokens(value):
    return [tok for tok in norm(value).split() if tok and tok not in {"the", "with", "in"}]


def match_figure(fig, catalog):
    labels = [fig.get("name"), fig.get("wikiName"), *(fig.get("aliases") or [])]
    wanted = {norm(label) for label in labels if label}
    wanted_tokens = set()
    for label in labels:
        wanted_tokens.update(tokens(label))
    hits = [item for item in catalog if norm(item.get("name")) in wanted]
    if len(hits) == 1:
        return hits[0]
    exact = [item for item in hits if norm(item.get("name")) == norm(fig.get("name"))]
    if len(exact) == 1:
        return exact[0]
    # "R2-D2" is the page for "R2-D2 (Artoo-Detoo)". Keep a catalog page only when
    # every word of its name is already in this figure's names, then prefer the
    # longest of those so "Luke Skywalker (X-Wing Pilot)" beats plain Luke.
    contained = []
    for item in catalog:
        name_tokens = tokens(item.get("name"))
        if name_tokens and all(tok in wanted_tokens for tok in name_tokens):
            contained.append(item)
    if not contained:
        return hits[0] if len(hits) == 1 else None
    contained.sort(key=lambda item: len(tokens(item.get("name"))), reverse=True)
    best = len(tokens(contained[0].get("name")))
    top = [item for item in contained if len(tokens(item.get("name"))) == best]
    return top[0] if len(top) == 1 else None


def accessory_covers(piece, figure_name, accessory_name):
    piece_n = norm(piece)
    acc_n = norm(accessory_name)
    fig_n = norm(figure_name)
    if not piece_n or piece_n not in acc_n and not acc_n.endswith(piece_n):
        # "lightsaber" inside "telescoping lightsaber", "bowcaster" contains nothing of "bowcaster" wait
        if piece_n not in acc_n:
            aliases = {
                "bowcaster": "bowcaster",
                "gaderffii stick": "gaderffii",
                "carbonite chamber": "carbonite",
                "helmet": "helmet",
                "cloak": "cloak",
                "cape": "cape",
                "lightsaber": "lightsaber",
                "blaster": "blaster",
                "rifle": "rifle",
            }
            token = aliases.get(piece_n, piece_n)
            if token not in acc_n:
                return False
    fig_tokens = [tok for tok in fig_n.split() if len(tok) > 2 and tok not in {"the", "with"}]
    if not fig_tokens:
        return piece_n in acc_n
    return any(tok in acc_n for tok in fig_tokens[:2]) or piece_n == acc_n


def main():
    debut = load_json(ROOT / "data" / "kenner-debut-figures.json")["figures"]
    catalog_figures, catalog_accessories = catalogs()
    coo = {item["sourceUrl"]: item for item in load_json(ROOT / "data" / "coo-figures.json")["figures"]}
    rows = []

    for fig in debut:
        match = match_figure(fig, catalog_figures)
        url = match.get("url") if match else ""
        record = coo.get(url) if url else None
        has_page = bool(url)
        has_details = bool(record and record.get("hasDetails"))
        if has_page and not has_details:
            gap = "figure-page-missing-details"
        elif not has_page:
            gap = "figure-no-page"
        else:
            gap = "ok"
        rows.append({
            "kind": "figure",
            "name": fig["name"],
            "year": fig.get("year", ""),
            "product": fig.get("product", ""),
            "wiki_name": fig.get("wikiName", ""),
            "has_page": "yes" if has_page else "no",
            "page_url": url,
            "has_coo_factory_mould_details": "yes" if has_details else "no",
            "verified_coo_choices": "yes" if record and record.get("verified") else "no",
            "detail_note": "",
            "gap": gap
        })

    fetched = 0
    for acc in catalog_accessories:
        url = acc.get("url") or ""
        has_details = False
        note = ""
        error = ""
        if url:
            try:
                raw, did = fetch(url)
                if did:
                    fetched += 1
                has_details, note = page_has_details(raw)
            except Exception as err:
                error = str(err)
        if not url:
            gap = "accessory-no-page"
        elif not has_details:
            gap = "accessory-page-missing-details"
        else:
            gap = "ok"
        rows.append({
            "kind": "accessory",
            "name": acc.get("name", ""),
            "year": "",
            "product": "",
            "wiki_name": "",
            "has_page": "yes" if url else "no",
            "page_url": url,
            "has_coo_factory_mould_details": "yes" if has_details else "no",
            "verified_coo_choices": "",
            "detail_note": error or note,
            "gap": gap
        })

    covered = {(norm(acc.get("name")),) for acc in catalog_accessories}
    acc_names = [acc.get("name", "") for acc in catalog_accessories]
    for fig in debut:
        for piece in fig.get("accessories") or []:
            if any(accessory_covers(piece, fig["name"], name) for name in acc_names):
                continue
            rows.append({
                "kind": "accessory",
                "name": f"{fig['name']} — {piece}",
                "year": fig.get("year", ""),
                "product": fig.get("product", ""),
                "wiki_name": fig.get("wikiName", ""),
                "has_page": "no",
                "page_url": "",
                "has_coo_factory_mould_details": "no",
                "verified_coo_choices": "",
                "detail_note": "Original bubble piece with no Variant Villain accessory-guide page.",
                "gap": "accessory-no-page"
            })

    figures = [row for row in rows if row["kind"] == "figure"]
    accessories = [row for row in rows if row["kind"] == "accessory"]
    no_page = [row for row in figures if row["gap"] == "figure-no-page"]
    missing = [row for row in figures if row["gap"] == "figure-page-missing-details"]
    acc_gaps = [row for row in accessories if row["gap"] != "ok"]
    years = sorted({row["year"] for row in figures})

    def lines_for(items):
        if not items:
            return ["None."]
        out = []
        for row in items:
            url = row["page_url"] or "no page"
            out.append(f"- {row['name']}" + (f" ({row['year']})" if row["year"] else "") + f" — {url}")
        return out

    md = []
    md.append("# Variant Villain gaps")
    md.append("")
    md.append(f"Figures are the {len(figures)} entries on the Wikipedia [List of Kenner Star Wars action figures]({WIKI}), stored in `data/kenner-debut-figures.json`. The table's year column runs {years[0]}–{years[-1]}. Twelve of those figures are dated 1977; they are the first wave of the same vintage line (the shelf years collectors call 1978–1985).")
    md.append("")
    md.append("Accessories are the original pieces on the Variant Villain accessory guide, plus any bubble piece from that figure list that has no guide page.")
    md.append("")
    md.append("A figure page \"has COO/factory/mould details\" when the fetched character page names a COO family, a country stamp, or a factory guide line. A verified COO choice is stricter: the bot only offers stamp buttons when the page (or the 1980 Lando leg notes) names the wording. An accessory page has details when its article names a mould, factory, or country stamp. Menu links such as \"Introduction to COOs\" do not count.")
    md.append("")
    md.append("## Counts")
    md.append("")
    md.append(f"- Figures: {len(figures)}")
    md.append(f"- Figures with a Variant Villain page: {sum(row['has_page']=='yes' for row in figures)}")
    md.append(f"- Figures with COO/factory/mould details: {sum(row['has_coo_factory_mould_details']=='yes' for row in figures)}")
    md.append(f"- Figures with verified COO choices in the bot: {sum(row['verified_coo_choices']=='yes' for row in figures)}")
    md.append(f"- (a) Figures with no Variant Villain page: {len(no_page)}")
    md.append(f"- (b) Figures with a page but no COO/factory/mould details: {len(missing)}")
    md.append(f"- Accessories checked: {len(accessories)}")
    md.append(f"- Accessories with a page: {sum(row['has_page']=='yes' for row in accessories)}")
    md.append(f"- Accessories whose page has mould/factory/COO details: {sum(row['has_coo_factory_mould_details']=='yes' for row in accessories)}")
    md.append(f"- (c) Accessories with no page or no details: {len(acc_gaps)}")
    md.append("")
    md.append("## (a) Figures with no Variant Villain page")
    md.append("")
    md.extend(lines_for(no_page))
    md.append("")
    md.append("## (b) Figures with a page but missing COO/factory/mould details")
    md.append("")
    md.extend(lines_for(missing))
    md.append("")
    md.append("## (c) Accessories with no page or no details")
    md.append("")
    if not acc_gaps:
        md.append("None.")
    else:
        for row in acc_gaps:
            why = "no page" if row["has_page"] == "no" else "page has no mould, factory, or COO tells"
            url = row["page_url"] or "no page"
            md.append(f"- {row['name']} — {why} — {url}")
    md.append("")
    md.append("The full row list is `docs/variantvillain-gaps.csv`.")
    md.append("")
    text = "\n".join(md)
    DOCS.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    (DOCS / "variantvillain-gaps.md").write_text(text)
    (ART / "variantvillain-gaps.md").write_text(text)
    fields = list(rows[0].keys())
    for dest in (DOCS / "variantvillain-gaps.csv", ART / "variantvillain-gaps.csv"):
        with dest.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    print(text.split("## (a)")[0])
    print("accessory fetches this run", fetched)
    print("wrote", DOCS / "variantvillain-gaps.md")


if __name__ == "__main__":
    main()
