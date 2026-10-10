#!/usr/bin/env python3
"""Build data/kenner-debut-figures.json from the Wikipedia Kenner figure list.

The debut card and year come from
https://en.wikipedia.org/wiki/List_of_Kenner_Star_Wars_action_figures
(the table's debut package card and debut year). Accessory names are the
original bubble pieces used only for the photo completeness line.

Pass the MediaWiki parse JSON (action=parse, prop=wikitext) as the argument.
"""

import json
import re
import sys
from pathlib import Path

# Product number -> collector name, pronoun, original bubble accessories.
# Names match the figure dossiers where the app already has one.
EXTRAS = {
    "38180": ("Luke Skywalker", "he", ["lightsaber"]),
    "38190": ("Princess Leia Organa", "she", ["cape", "blaster"]),
    "38200": ("R2-D2 (Artoo-Detoo)", "he", []),
    "38210": ("Chewbacca", "he", ["bowcaster"]),
    "38220": ("C-3PO", "he", []),
    "38230": ("Darth Vader", "he", ["cape", "lightsaber"]),
    "38240": ("Imperial Stormtrooper", "he", ["blaster"]),
    "38250": ("Ben (Obi-Wan) Kenobi", "he", ["cape", "lightsaber"]),
    "38260": ("Han Solo", "he", ["blaster"]),
    "38270": ("Jawa", "he", ["cloak", "blaster"]),
    "38280": ("Tusken Raider (Sand People)", "he", ["gaderffii stick", "cape"]),
    "38290": ("Death Squad Commander", "he", ["blaster"]),
    "39020": ("Greedo", "he", ["blaster"]),
    "39030": ("Hammerhead", "he", []),
    "39040": ("Snaggletooth", "he", ["blaster"]),
    "39050": ("Walrus Man", "he", ["blaster"]),
    "39060": ("Luke Skywalker (X-Wing Pilot)", "he", ["lightsaber"]),
    "39070": ("R5-D4", "it", []),
    "39080": ("Death Star Droid", "it", []),
    "39090": ("Power Droid", "it", []),
    "39250": ("Boba Fett", "he", ["blaster"]),
    "39720": ("Leia Organa (Bespin Gown)", "she", ["cape", "blaster"]),
    "39730": ("FX-7", "it", []),
    "39740": ("Imperial Stormtrooper (Hoth Battle Gear)", "he", ["rifle", "skirt"]),
    "39750": ("Rebel Soldier (Hoth Battle Gear)", "he", ["rifle"]),
    "39760": ("Bossk", "he", ["rifle"]),
    "39770": ("IG-88", "it", ["rifle"]),
    "39780": ("Luke Skywalker (Bespin Fatigues)", "he", ["blaster"]),
    "39790": ("Han Solo (Hoth Outfit)", "he", ["blaster"]),
    "39800": ("Lando Calrissian", "he", ["cape", "blaster"]),
    "39810": ("Bespin Security Guard (White)", "he", ["blaster"]),
    "38310": ("Yoda", "he", ["cane", "snake", "belt"]),
    "39319": ("Ugnaught", "he", ["smock", "case"]),
    "39329": ("Dengar", "he", ["rifle"]),
    "39339": ("Han Solo (Bespin Outfit)", "he", ["cape", "blaster"]),
    "39349": ("Lobot", "he", ["blaster"]),
    "39359": ("Leia (Hoth Outfit)", "she", ["blaster"]),
    "39369": ("Rebel Commander", "he", ["blaster"]),
    "39379": ("AT-AT Driver", "he", ["rifle"]),
    "39389": ("Imperial Commander", "he", ["blaster"]),
    "39399": ("2-1B", "it", ["probe"]),
    "69420": ("R2-D2 (Sensorscope)", "he", ["sensorscope"]),
    "69430": ("C-3PO (Removable Limbs)", "he", []),
    "69610": ("Luke Skywalker (Hoth Battle Gear)", "he", ["blaster"]),
    "69620": ("At-At Commander", "he", ["blaster"]),
    "69630": ("(Twin-Pod) Cloud Car Pilot", "he", ["blaster"]),
    "69640": ("Bespin Security Guard (Black)", "he", ["blaster"]),
    "70010": ("4-LOM", "it", ["blaster"]),
    "70020": ("Zuckuss", "he", ["blaster"]),
    "70030": ("Imperial Tie Fighter Pilot", "he", ["blaster"]),
    "70310": ("Admiral Ackbar", "he", ["staff"]),
    "70650": ("Luke Skywalker (Jedi Knight Outfit)", "he", ["lightsaber", "cloak"]),
    "70660": ("Princess Leia Organa (Boushh Disguise)", "she", ["helmet", "rifle"]),
    "70670": ("Gamorrean Guard", "he", ["axe"]),
    "70680": ("Emperor's Royal Guard", "he", ["pike"]),
    "70690": ("Chief Chirpa", "he", ["staff"]),
    "70710": ("Logray (Ewok Medicine Man)", "he", ["staff"]),
    "70730": ("Klaatu", "he", ["skirt"]),
    "70740": ("Rebel Commando", "he", ["blaster"]),
    "70760": ("Weequay", "he", ["pike"]),
    "70770": ("Squid Head", "he", ["rifle", "skirt"]),
    "70780": ("General Madine", "he", ["staff"]),
    "70790": ("Bib Fortuna", "he", ["cloak", "staff"]),
    "70800": ("Ree Yees", "he", ["rifle"]),
    "70820": ("Biker Scout", "he", ["blaster"]),
    "70830": ("Lando Calrissian (Skiff Guard Disguise)", "he", ["helmet", "cape"]),
    "70840": ("Nien Nunb", "he", ["blaster"]),
    "71190": ("Nikto", "he", ["staff"]),
    "71210": ("8D8", "it", []),
    "71220": ("Princess Leia Organa (in Combat Poncho)", "she", ["blaster"]),
    "71230": ("Wicket W. Warrick", "he", ["spear"]),
    "71240": ("The Emperor", "he", ["cane"]),
    "71280": ("B-Wing Pilot", "he", ["blaster"]),
    "71290": ("Klaatu (in Skiff Guard Outfit)", "he", ["skirt"]),
    "71300": ("Han Solo (in Trench Coat)", "he", ["blaster"]),
    "71310": ("Teebo", "he", ["hood", "axe", "horn"]),
    "71320": ("Prune Face", "he", ["rifle"]),
    "71330": ("AT-ST Driver", "he", ["blaster"]),
    "71350": ("Rancor Keeper", "he", ["axe"]),
    "93670": ("Lumat", "he", ["bow"]),
    "93680": ("Paploo", "he", ["spear"]),
    "93710": ("Luke Skywalker (in Battle Poncho)", "he", ["blaster"]),
    "93720": ("Artoo-Detoo (R2-D2) with pop-up Lightsaber", "he", ["lightsaber"]),
    "93730": ("Romba", "he", ["bow"]),
    "93740": ("Amanaman", "he", ["staff"]),
    "93750": ("Barada", "he", ["polearm"]),
    "93760": ("Imperial Gunner", "he", ["blaster"]),
    "93770": ("Han Solo (in Carbonite Chamber)", "he", ["carbonite chamber"]),
    "93780": ("Luke Skywalker (Imperial Stormtrooper Outfit)", "he", ["blaster"]),
    "93790": ("Anakin Skywalker", "he", ["lightsaber"]),
    "93800": ("EV-9D9", "it", []),
    "93810": ("Warok", "he", ["bow"]),
    "93820": ("Lando Calrissian (General Pilot)", "he", ["cape", "blaster"]),
    "93830": ("A-Wing Pilot", "he", ["blaster"]),
    "93850": ("Imperial Dignitary", "he", []),
    "93840": ("Yak Face", "he", ["staff"]),
}

POSSESSIVE = {"he": "his", "she": "her", "it": "its"}


def clean_wiki(text):
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text)
    text = re.sub(r"<ref[^>]*/>", "", text)
    text = re.sub(r"\{\{[^{|}]*\|([^{}]*)\}\}", r"\1", text)
    text = re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", r"\1", text)
    text = text.replace("''", "")
    return re.sub(r"\s+", " ", text).strip()


def aliases_for(name, wiki_name):
    found = []
    for label in (name, wiki_name):
        label = re.sub(r"\s+", " ", label).strip()
        if label and label not in found:
            found.append(label)
        swapped = re.sub(r"\s*\(([^)]+)\)", r" in \1", label)
        if swapped != label and swapped not in found:
            found.append(swapped)
    return found


def main():
    raw = json.loads(Path(sys.argv[1]).read_text())
    wiki = raw["parse"]["wikitext"]["*"]
    figures = []
    seen = set()
    for line in wiki.splitlines():
        if not line.startswith("|") or "||" not in line:
            continue
        cells = [clean_wiki(cell) for cell in line.strip("|").split("||")]
        if len(cells) < 5 or cells[0] in {"Wave", '"Wave"'}:
            continue
        card = cells[1]
        match = re.match(r"(\d+)-Back \"(.+?)\"(?: \((.+)\))?$", card)
        if not match:
            continue
        number, line_name, extra = match.groups()
        product = re.search(r"(\d{5})", cells[3])
        if not product:
            continue
        product_no = product.group(1)
        if product_no in seen:
            continue
        seen.add(product_no)
        year = re.search(r"(19\d\d)", cells[4])
        if not year:
            raise SystemExit(f"No year for {cells[2]}")
        name, pronoun, accessories = EXTRAS.get(product_no, (cells[2], "he", []))
        figures.append({
            "product": product_no,
            "name": name,
            "wikiName": cells[2],
            "aliases": aliases_for(name, cells[2]),
            "year": int(year.group(1)),
            "cardback": f"{number}-back",
            "line": line_name,
            "outsideUs": bool(extra and "outside" in extra.lower()),
            "pronoun": pronoun,
            "possessive": POSSESSIVE[pronoun],
            "accessories": accessories,
        })
    if len(figures) != 96:
        raise SystemExit(f"Expected 96 figures, got {len(figures)}")
    missing = [key for key in EXTRAS if key not in seen]
    if missing:
        raise SystemExit(f"Product numbers not in the table: {missing}")
    out = {
        "source": "https://en.wikipedia.org/wiki/List_of_Kenner_Star_Wars_action_figures",
        "sourceNote": "Debut card and year are that page's debut-package table. The year column is production year and is used here as the first-release year in the photo reply. Accessories are the original bubble pieces for the completeness line only. This file is not reference evidence for variant answers.",
        "figures": figures,
    }
    dest = Path(__file__).resolve().parents[1] / "data" / "kenner-debut-figures.json"
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(f"Wrote {len(figures)} figures to {dest}")


if __name__ == "__main__":
    main()
