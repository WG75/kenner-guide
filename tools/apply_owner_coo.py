#!/usr/bin/env python3
"""Apply the owner's 10 Oct 2026 stamp sheet and export every Wikipedia figure.

The sheet is authoritative for the 31 figures that had no verified stamp
buttons. Typos fixed on import: Chna, Lili Lefy, reminants/remanants,
underneigh, 'remanants of the test', and 'on no COO'.

Buttons group factories that share a tell. A follow-up asks the next
detail that actually separates them. A figure that is always No COO asks
about the licensing location instead of a country list.
"""

import csv
import json
import re
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
COO = ROOT / "data" / "coo-figures.json"
OWNER_JSON = ROOT / "data" / "coo-owner-stamps.json"
GAPS = ROOT / "docs" / "variantvillain-gaps.csv"
XLSX = ROOT / "docs" / "coo-details-all-figures.xlsx"
ART = Path("/opt/cursor/artifacts/coo-details-all-figures.xlsx")


def fix_text(text):
    text = str(text or "")
    text = text.replace("Chna", "China").replace("Lili Lefy", "Lili Ledy")
    text = text.replace("reminants", "remnants").replace("remanants", "remnants")
    text = text.replace("underneigh", "underneath")
    text = text.replace("remnants of the test", "remnants of the text")
    text = re.sub(r"\bon no COO\b", "or no COO", text, flags=re.I)
    return re.sub(r"\s{2,}", " ", text).strip()


def names(items):
    labelled = [f"the {item}" for item in items]
    if len(labelled) == 1:
        return labelled[0]
    if len(labelled) == 2:
        return f"{labelled[0]} and {labelled[1]}"
    return ", ".join(labelled[:-1]) + ", and " + labelled[-1]


def one(factory, detail):
    return f"That is the {factory}. {detail}"


def shared(factories, detail):
    return (
        f"That stamp is shared by {names(factories)}. {detail} "
        "I'm not sure which of those it is from the stamp alone."
    )


def follow(id, label, conclusion, sure=True):
    return {"id": id, "label": label, "conclusion": conclusion, "sure": sure}


def option(id, label, factories, conclusion, sure=False, follows=None, coo=""):
    low = label.lower()
    if not coo:
        if "no coo" in low or "licensing" in low or "h.k." in low:
            coo = "No COO" if "no coo" in low or "licensing" in low else "Hong Kong"
        elif "made in china" in low or "china" in low:
            coo = "China"
        elif "made in hong kong" in low:
            coo = "Hong Kong"
        elif "hong kong" in low:
            coo = "Hong Kong"
        else:
            coo = ""
    return {
        "id": id,
        "label": label,
        "coo": coo,
        "factories": factories,
        "examples": [label],
        "conclusion": "" if follows else conclusion,
        "sure": False if follows else sure,
        "followUps": follows or [],
    }


def figure(name, where, stamps, options, missing, ask="Which stamp do you see?"):
    return {
        "name": name,
        "whereToLook": where,
        "ask": ask,
        "stamps": [fix_text(item) for item in stamps],
        "options": options,
        "missing": missing,
    }


# Raw cells, typos corrected by fix_text when the file is written.
OWNER = [
    figure(
        "Han Solo",
        "Look at the left leg, under the licensing details. 'Hong Kong' is Unitoy or Kader. No COO is Glasslite or PBP.",
        [
            "Unitoy M1 = 'Hong Kong' left leg under licencing details",
            "Kader M2 = 'Hong Kong' left leg under licencing details",
            "Glasslite M2 = No COO, it would be either smooth or dotted reminants of the COO text left leg under licencing details",
            "PBP M3 = Smooth no COO under licencing text.",
        ],
        [
            option(
                "hk-left",
                "Hong Kong, left leg, under the licensing details",
                ["Unitoy M1", "Kader M2"],
                shared(["Unitoy M1", "Kader M2"], "'Hong Kong' is on the left leg under the licensing details."),
            ),
            option(
                "no-coo",
                "No COO, left leg, under the licensing details",
                ["Glasslite M2", "PBP M3"],
                "",
                follows=[
                    follow(
                        "dots",
                        "Dotted remnants of the country text",
                        one("Glasslite M2", "The left leg is No COO, with dotted remnants of the country text under the licensing details."),
                    ),
                    follow(
                        "smooth",
                        "Smooth, no country text left",
                        shared(["Glasslite M2", "PBP M3"], "A smooth No COO under the licensing text is listed for both."),
                        sure=False,
                    ),
                ],
            ),
        ],
        "Hong Kong on the left leg does not separate Unitoy M1 from Kader M2. A smooth No COO does not separate Glasslite M2 from PBP M3.",
    ),
    figure(
        "Death Squad Commander",
        "Look at the left leg, under the licensing details. A clear 'Hong Kong', an almost smoothed 'Hong Kong', and a smooth No COO are different moulds.",
        [
            "Unitoy M1 = 'Hong Kong' left leg under licencing details",
            "Kader M2 = 'Hong Kong' left leg under licencing details",
            "Kader China M2 = 'Hong Kong' left leg under licencing details. Text is undefined almost smoothed over.",
            "Lili Ledy M2 = 'Hong Kong' left leg under licencing details. Text is undefined almost smoothed over.",
            "PBP M3 = 'Hong Kong' left leg under licencing details or No COO just smooth",
        ],
        [
            option(
                "hk-clear",
                "Hong Kong, clear, left leg, under the licensing details",
                ["Unitoy M1", "Kader M2", "PBP M3"],
                shared(["Unitoy M1", "Kader M2", "PBP M3"], "A clear 'Hong Kong' on the left leg under the licensing details is listed for all three."),
            ),
            option(
                "hk-faint",
                "Hong Kong, text almost smoothed over",
                ["Kader China M2", "Lili Ledy M2"],
                shared(["Kader China M2", "Lili Ledy M2"], "The 'Hong Kong' on the left leg under the licensing details is almost smoothed over."),
            ),
            option(
                "smooth",
                "No COO, just smooth",
                ["PBP M3"],
                one("PBP M3", "The left leg is a smooth No COO under the licensing details."),
                sure=True,
            ),
        ],
        "A clear Hong Kong stamp does not separate Unitoy M1, Kader M2, and PBP M3. An almost smoothed Hong Kong stamp does not separate Kader China M2 from Lili Ledy M2.",
    ),
    figure(
        "Greedo",
        "Look at the left leg, under the licensing details. A scar in place of the country is PBP.",
        [
            "Smile M1 = 'Hong Kong' left leg under licencing details or No COO",
            "PBP M1 = No COO scar",
            "Smile M2 = 'Hong Kong' left leg under licencing details or No COO",
        ],
        [
            option(
                "hk",
                "Hong Kong, left leg, under the licensing details",
                ["Smile M1", "Smile M2"],
                shared(["Smile M1", "Smile M2"], "'Hong Kong' is on the left leg under the licensing details."),
            ),
            option(
                "scar",
                "No COO, a scar in place of the country",
                ["PBP M1"],
                one("PBP M1", "The country is a scar, No COO."),
                sure=True,
            ),
            option(
                "no-coo",
                "No COO, no scar",
                ["Smile M1", "Smile M2"],
                shared(["Smile M1", "Smile M2"], "No COO without a scar is listed for both."),
            ),
        ],
        "Hong Kong does not separate Smile M1 from Smile M2. No COO without a scar does not separate them either.",
    ),
    figure(
        "Hammerhead",
        "Look at the left leg, under the licensing details. A scar in place of the country is PBP.",
        [
            "Smile M1 = 'Hong Kong' left leg under licencing details or No COO",
            "PBP M1 = No COO scar",
            "Smile M2 = 'Hong Kong' left leg under licencing details or No COO",
        ],
        [
            option(
                "hk",
                "Hong Kong, left leg, under the licensing details",
                ["Smile M1", "Smile M2"],
                shared(["Smile M1", "Smile M2"], "'Hong Kong' is on the left leg under the licensing details."),
            ),
            option(
                "scar",
                "No COO, a scar in place of the country",
                ["PBP M1"],
                one("PBP M1", "The country is a scar, No COO."),
                sure=True,
            ),
            option(
                "no-coo",
                "No COO, no scar",
                ["Smile M1", "Smile M2"],
                shared(["Smile M1", "Smile M2"], "No COO without a scar is listed for both."),
            ),
        ],
        "Hong Kong does not separate Smile M1 from Smile M2. No COO without a scar does not separate them either.",
    ),
    figure(
        "Snaggletooth",
        "Blue Snaggletooth carries 'Hong Kong' on the left boot, under the licensing details. The other moulds use the left leg.",
        [
            "Smile M1 = 'Hong Kong' left boot under licencing details (Blue Snaggletooth only)",
            "Smile M2 = 'Hong Kong' left leg under licencing details",
            "Smile M3 = 'Hong Kong' left leg under licencing details or a scar instead of COO.",
            "PBP M3 = Scar in place of COO under licencing text.",
        ],
        [
            option(
                "boot",
                "Hong Kong on the left boot, under the licensing details",
                ["Smile M1"],
                one("Smile M1", "That boot stamp is the blue Snaggletooth only. 'Hong Kong' sits on the left boot under the licensing details."),
                sure=True,
            ),
            option(
                "leg",
                "Hong Kong on the left leg, under the licensing details",
                ["Smile M2", "Smile M3"],
                shared(["Smile M2", "Smile M3"], "'Hong Kong' is on the left leg under the licensing details."),
            ),
            option(
                "scar",
                "A scar in place of the COO, under the licensing text",
                ["Smile M3", "PBP M3"],
                shared(["Smile M3", "PBP M3"], "A scar stands in place of the country, under the licensing text."),
            ),
        ],
        "Hong Kong on the left leg does not separate Smile M2 from Smile M3. A scar does not separate Smile M3 from PBP M3. The red Snaggletooth boot stamp is not described.",
    ),
    figure(
        "Walrus Man",
        "Look at the left leg, under the licensing details. No COO, whether scarred, smooth, speckled, or missing its licensing text, is PBP.",
        [
            "Smile M1 = 'Hong Kong' left leg under licencing details",
            "PBP M1 = No COO. Might have a scar, smooth or speckles. Some also have missing licensing text.",
            "Smile M2 = 'Hong Kong' left leg under licencing details",
        ],
        [
            option(
                "hk",
                "Hong Kong, left leg, under the licensing details",
                ["Smile M1", "Smile M2"],
                shared(["Smile M1", "Smile M2"], "'Hong Kong' is on the left leg under the licensing details."),
            ),
            option(
                "no-coo",
                "No COO (scar, smooth, speckles, or missing licensing text)",
                ["PBP M1"],
                one("PBP M1", "No COO on this figure, with a scar, a smooth leg, speckles, or missing licensing text, is the PBP M1."),
                sure=True,
            ),
        ],
        "Hong Kong on the left leg does not separate Smile M1 from Smile M2.",
    ),
    figure(
        "Power Droid",
        "Both moulds say Hong Kong. The tell is where the G of Kong sits against the silver. The leg is not stated.",
        [
            "Kader M1 = 'Hong Kong', the G of Kong is just above the silver",
            "Kader M2 = 'Hong Kong', the G of Kong is one run above the silver",
        ],
        [
            option(
                "g-just",
                "The G of Kong is just above the silver",
                ["Kader M1"],
                one("Kader M1", "'Hong Kong' is stamped with the G of Kong just above the silver."),
                sure=True,
                coo="Hong Kong",
            ),
            option(
                "g-run",
                "The G of Kong is one run above the silver",
                ["Kader M2"],
                one("Kader M2", "'Hong Kong' is stamped with the G of Kong one run above the silver."),
                sure=True,
                coo="Hong Kong",
            ),
        ],
        "Which leg carries the stamp is not stated.",
        ask="Which of these do you see?",
    ),
    figure(
        "Leia Organa (Bespin Gown)",
        "Kader's 'Made in' stamp is on her right leg, across 2 lines. China sits on a raised bar. Unitoy and Smile use 'Hong Kong' under the licensing details, or No COO.",
        [
            "Kader M1 = 'Made in Hong Kong' across 2 lines on her right leg",
            "Kader China M1 = 'Made in China' across 2 lines on her right leg, with China on a raised bar.",
            "Lili Ledy M1 = 'Made in China' across 2 lines on her right leg, with China on a raised bar. Looks more glossy and the letters are not as sharp.",
            "Unitoy M2 = 'Hong Kong' under licensing details or No COO.",
            "Smile M3 = 'Hong Kong' under licensing details or No COO.",
        ],
        [
            option(
                "mihk",
                "Made in Hong Kong, 2 lines, right leg",
                ["Kader M1"],
                one("Kader M1", "'Made in Hong Kong' runs across 2 lines on her right leg."),
                sure=True,
            ),
            option(
                "china",
                "Made in China, 2 lines, right leg, China on a raised bar",
                ["Kader China M1", "Lili Ledy M1"],
                "",
                follows=[
                    follow(
                        "sharp",
                        "Letters are sharp",
                        one("Kader China M1", "'Made in China' runs across 2 lines on her right leg, with China on a raised bar."),
                    ),
                    follow(
                        "glossy",
                        "More glossy, letters not as sharp",
                        one("Lili Ledy M1", "'Made in China' runs across 2 lines on her right leg, with China on a raised bar. The figure looks more glossy and the letters are not as sharp."),
                    ),
                ],
                coo="China",
            ),
            option(
                "hk",
                "Hong Kong under the licensing details",
                ["Unitoy M2", "Smile M3"],
                shared(["Unitoy M2", "Smile M3"], "'Hong Kong' sits under the licensing details. The leg is not stated."),
            ),
            option(
                "no-coo",
                "No COO",
                ["Unitoy M2", "Smile M3"],
                shared(["Unitoy M2", "Smile M3"], "No COO is listed for both."),
            ),
        ],
        "Hong Kong under the licensing details, and No COO, do not separate Unitoy M2 from Smile M3. The leg for Unitoy and Smile is not stated.",
    ),
    figure(
        "FX-7",
        "Kader says Made in Hong Kong and also carries a 1 or 2 on the base plus 3 EPM marks. Unitoy's 'Hong Kong' sits directly under the licensing details.",
        [
            "Kader M1 = 'Made in Hong Kong', also has the number 1 or 2 on its base and 3 EPM marks.",
            "Smile M2 = 'Hong Kong' or No COO.",
            "Unitoy M3 = 'Hong Kong' directly under the licensing details.",
        ],
        [
            option(
                "kader",
                "Made in Hong Kong, with a 1 or 2 on the base and 3 EPM marks",
                ["Kader M1"],
                one("Kader M1", "It says Made in Hong Kong, and the base has the number 1 or 2 plus 3 EPM marks."),
                sure=True,
            ),
            option(
                "unitoy",
                "Hong Kong directly under the licensing details",
                ["Unitoy M3"],
                one("Unitoy M3", "'Hong Kong' sits directly under the licensing details."),
                sure=True,
            ),
            option(
                "smile-hk",
                "Hong Kong, not directly under the licensing details",
                ["Smile M2"],
                one("Smile M2", "The stamp is 'Hong Kong'. The position against the licensing mark is not stated for this mould."),
                sure=True,
            ),
            option(
                "no-coo",
                "No COO",
                ["Smile M2"],
                one("Smile M2", "This mould is also found as No COO."),
                sure=True,
            ),
        ],
        "The leg is not stated for Smile M2 or Unitoy M3. Smile's position against the licensing mark is not stated.",
    ),
    figure(
        "Bossk",
        "Read the left leg and the right leg. 'Made in Hong Kong' on the left leg is Kader. 'Hong Kong' under the licensing details is Smile or Unitoy. Licensing on the right leg with No COO is Kader. Licensing on the left leg only is PBP.",
        [
            "Kader M1 = 'Made in Hong Kong' on left leg or No COO and licensing details on his right leg.",
            "Smile M2 = 'Hong Kong' on left leg under licensing details or licensing details only.",
            "Unitoy M3 = 'Hong Kong' directly under the licensing details.",
            "PBP M4 = Licensing on left leg only. No COO.",
        ],
        [
            option(
                "mihk",
                "Made in Hong Kong on the left leg",
                ["Kader M1"],
                one("Kader M1", "'Made in Hong Kong' is on the left leg."),
                sure=True,
            ),
            option(
                "hk",
                "Hong Kong under the licensing details",
                ["Smile M2", "Unitoy M3"],
                shared(["Smile M2", "Unitoy M3"], "'Hong Kong' sits under the licensing details. Smile's is on the left leg. Unitoy's leg is not stated."),
            ),
            option(
                "right",
                "No COO, licensing details on the right leg",
                ["Kader M1"],
                one("Kader M1", "No COO, with the licensing details on his right leg."),
                sure=True,
            ),
            option(
                "left-only",
                "No COO, licensing on the left leg only",
                ["Smile M2", "PBP M4"],
                shared(["Smile M2", "PBP M4"], "Licensing details with no country are listed for both. PBP's licensing is on the left leg only. Smile's leg is not stated for this state."),
            ),
        ],
        "Hong Kong under the licensing details does not separate Smile M2 from Unitoy M3. Unitoy's leg is not stated. Smile's 'licensing details only' does not name the leg.",
    ),
    figure(
        "Ugnaught",
        "Look at the right leg for 'Made in Hong Kong' across 2 lines, and the left leg for licensing details or a plain 'Hong Kong'.",
        [
            "Unitoy M1 = Made in Hong Kong on right leg across 2 lines or No COO smooth leg.",
            "Kader M2 = 'Made in Hong Kong' across 2 lines on right leg. Licensing details on left leg.",
            "Smile M3 = 'Hong Kong' left leg under licencing details",
        ],
        [
            option(
                "two-lines",
                "Made in Hong Kong, 2 lines, right leg",
                ["Unitoy M1", "Kader M2"],
                "",
                follows=[
                    follow(
                        "left-license",
                        "Licensing details on the left leg",
                        one("Kader M2", "'Made in Hong Kong' runs across 2 lines on the right leg, and the licensing details are on the left leg."),
                    ),
                    follow(
                        "no-left",
                        "No licensing details on the left leg",
                        one("Unitoy M1", "'Made in Hong Kong' runs across 2 lines on the right leg. The left-leg licensing is described for Kader, not this mould."),
                    ),
                ],
            ),
            option(
                "smooth",
                "No COO, smooth leg",
                ["Unitoy M1"],
                one("Unitoy M1", "The leg is a smooth No COO."),
                sure=True,
            ),
            option(
                "hk-left",
                "Hong Kong, left leg, under the licensing details",
                ["Smile M3"],
                one("Smile M3", "'Hong Kong' is on the left leg under the licensing details."),
                sure=True,
            ),
        ],
        "Whether Unitoy M1 can also carry licensing details on the left leg is not stated. The smooth No COO does not name which leg.",
    ),
    figure(
        "Dengar",
        "Smile uses the left leg. Unitoy and PBP use the right leg. Kader's 'Made in Hong Kong' is 2 lines on the left leg.",
        [
            "Smile M1 = 'Hong Kong' left leg under licencing details or No COO",
            "Unitoy M2 = 'Made in Hong Kong' on right leg across 2 lines.",
            "PBP M2 = Scar on right leg or Made In with scar underneath.",
            "Kader M3 = 'Made in Hong Kong' on left leg across 2 lines.",
        ],
        [
            option(
                "smile-hk",
                "Hong Kong, left leg, under the licensing details",
                ["Smile M1"],
                one("Smile M1", "'Hong Kong' is on the left leg under the licensing details."),
                sure=True,
            ),
            option(
                "smile-ncoo",
                "No COO",
                ["Smile M1"],
                one("Smile M1", "No COO is the other state of this mould. A scar is a different mould."),
                sure=True,
            ),
            option(
                "unitoy",
                "Made in Hong Kong, 2 lines, right leg",
                ["Unitoy M2"],
                one("Unitoy M2", "'Made in Hong Kong' runs across 2 lines on the right leg."),
                sure=True,
            ),
            option(
                "pbp",
                "Scar on the right leg, or 'Made in' with a scar underneath",
                ["PBP M2"],
                one("PBP M2", "The right leg has a scar, or it says 'Made in' with a scar underneath."),
                sure=True,
            ),
            option(
                "kader",
                "Made in Hong Kong, 2 lines, left leg",
                ["Kader M3"],
                one("Kader M3", "'Made in Hong Kong' runs across 2 lines on the left leg."),
                sure=True,
            ),
        ],
        "Smile's No COO does not say whether the country is smooth, scarred, or dotted.",
    ),
    figure(
        "Han Solo (Bespin Outfit)",
        "Read which leg says 'Made in Hong Kong', and whether it is across 2 lines. A smooth No COO on the left leg is Kader China or Lili Ledy.",
        [
            "Unitoy M1 = 'Made in Hong Kong' on right leg across 2 lines.",
            "Lili Ledy M1 = 'Made in Hong Kong' on right leg.",
            "Kader M2 = 'Made in Hong Kong' across 2 lines on left leg",
            "Kader China M2 = No COO smooth left leg.",
            "Lili Ledy M2 = No COO smooth left leg.",
            "Smile M3 = 'Hong Kong' under licensing details or No COO.",
        ],
        [
            option(
                "unitoy",
                "Made in Hong Kong, 2 lines, right leg",
                ["Unitoy M1"],
                one("Unitoy M1", "'Made in Hong Kong' runs across 2 lines on the right leg."),
                sure=True,
            ),
            option(
                "lili",
                "Made in Hong Kong on the right leg, not across 2 lines",
                ["Lili Ledy M1"],
                one("Lili Ledy M1", "'Made in Hong Kong' is on the right leg. Line breaks are not stated for this mould."),
                sure=True,
            ),
            option(
                "kader",
                "Made in Hong Kong, 2 lines, left leg",
                ["Kader M2"],
                one("Kader M2", "'Made in Hong Kong' runs across 2 lines on the left leg."),
                sure=True,
            ),
            option(
                "smooth",
                "No COO, smooth left leg",
                ["Kader China M2", "Lili Ledy M2"],
                shared(["Kader China M2", "Lili Ledy M2"], "The left leg is a smooth No COO."),
            ),
            option(
                "smile-hk",
                "Hong Kong under the licensing details",
                ["Smile M3"],
                one("Smile M3", "'Hong Kong' sits under the licensing details. The leg is not stated."),
                sure=True,
            ),
            option(
                "smile-ncoo",
                "No COO, not a smooth left leg",
                ["Smile M3"],
                one("Smile M3", "No COO is the other state of this mould. A smooth left leg is Kader China or Lili Ledy instead."),
                sure=True,
            ),
        ],
        "A smooth No COO on the left leg does not separate Kader China M2 from Lili Ledy M2. Lili Ledy M1 does not say whether the right-leg stamp is one line or two. Smile's leg is not stated.",
    ),
    figure(
        "Lobot",
        "Smile uses 'Hong Kong' on the left leg under the licensing details, or No COO. Unitoy and Kader use 'Made in Hong Kong' across 2 lines on the right leg.",
        [
            "Smile M1 = 'Hong Kong' left leg under licencing details or No COO",
            "Unitoy M2 = 'Made in Hong Kong' across 2 lines on right leg.",
            "Kader M3 = 'Made in Hong Kong' across 2 lines on right leg or no COO.",
        ],
        [
            option(
                "smile",
                "Hong Kong, left leg, under the licensing details",
                ["Smile M1"],
                one("Smile M1", "'Hong Kong' is on the left leg under the licensing details."),
                sure=True,
            ),
            option(
                "two-lines",
                "Made in Hong Kong, 2 lines, right leg",
                ["Unitoy M2", "Kader M3"],
                shared(["Unitoy M2", "Kader M3"], "'Made in Hong Kong' runs across 2 lines on the right leg."),
            ),
            option(
                "no-coo",
                "No COO",
                ["Smile M1", "Kader M3"],
                shared(["Smile M1", "Kader M3"], "No COO is listed for both."),
            ),
        ],
        "Made in Hong Kong across 2 lines on the right leg does not separate Unitoy M2 from Kader M3. No COO does not separate Smile M1 from Kader M3.",
    ),
    figure(
        "Rebel Commander",
        "All three moulds can say 'Made in Hong Kong' across 2 lines on the right leg. Slight remnants of the text are Smile. 'Made in' with the country missing is Kader.",
        [
            "Unitoy M1 = 'Made in Hong Kong' across 2 lines on right leg.",
            "Smile M2 = 'Made in Hong Kong' across 2 lines on right leg, or No COO just slight remanants of the test",
            "Kader M3 = 'Made in Hong Kong' across 2 lines on right leg or 'Made in' with the COO country text missing.",
        ],
        [
            option(
                "full",
                "Made in Hong Kong, 2 lines, right leg",
                ["Unitoy M1", "Smile M2", "Kader M3"],
                shared(["Unitoy M1", "Smile M2", "Kader M3"], "'Made in Hong Kong' runs across 2 lines on the right leg."),
            ),
            option(
                "remnants",
                "No COO, slight remnants of the text",
                ["Smile M2"],
                one("Smile M2", "No COO, with slight remnants of the text."),
                sure=True,
            ),
            option(
                "made-in",
                "'Made in', with the country text missing",
                ["Kader M3"],
                one("Kader M3", "It says 'Made in' and the country text is missing."),
                sure=True,
            ),
        ],
        "A complete 'Made in Hong Kong' across 2 lines on the right leg does not separate Unitoy M1, Smile M2, and Kader M3.",
    ),
    figure(
        "2-1B",
        "Look at the right leg. Across 2 lines is Unitoy or Kader. 'Made in Hong Kong' without that line break, or No COO, is Smile.",
        [
            "Smile M1 = 'Made in Hong Kong' on right leg or no COO",
            "Unitoy M2 = 'Made in Hong Kong' on right leg across 2 lines.",
            "Kader M3 = 'Made in Hong Kong' on right leg across 2 lines.",
        ],
        [
            option(
                "two-lines",
                "Made in Hong Kong, 2 lines, right leg",
                ["Unitoy M2", "Kader M3"],
                shared(["Unitoy M2", "Kader M3"], "'Made in Hong Kong' runs across 2 lines on the right leg."),
            ),
            option(
                "smile",
                "Made in Hong Kong on the right leg, not across 2 lines",
                ["Smile M1"],
                one("Smile M1", "'Made in Hong Kong' is on the right leg. Line breaks are not stated for this mould."),
                sure=True,
            ),
            option(
                "no-coo",
                "No COO",
                ["Smile M1"],
                one("Smile M1", "No COO is the other state of this mould."),
                sure=True,
            ),
        ],
        "Made in Hong Kong across 2 lines on the right leg does not separate Unitoy M2 from Kader M3. Smile does not say whether its stamp is one line or two.",
    ),
    figure(
        "Luke Skywalker (Hoth Battle Gear)",
        "Look at the right leg. A clear single line is Unitoy. A faint 'Made in Hong Kong' is Smile. Small dots and no country are PBP.",
        [
            "Unitoy M1 = 'Made in Hong Kong' on right leg across a single line.",
            "PBP M1 = No COO small dots instead.",
            "Smile M2 = 'Made in Hong Kong' faintly on right leg. Or No COO.",
        ],
        [
            option(
                "clear",
                "Made in Hong Kong, one clear line, right leg",
                ["Unitoy M1"],
                one("Unitoy M1", "'Made in Hong Kong' runs across a single line on the right leg."),
                sure=True,
            ),
            option(
                "faint",
                "Made in Hong Kong, faint, right leg",
                ["Smile M2"],
                one("Smile M2", "'Made in Hong Kong' is faint on the right leg."),
                sure=True,
            ),
            option(
                "dots",
                "No COO, small dots",
                ["PBP M1"],
                one("PBP M1", "No COO, with small dots instead of the country."),
                sure=True,
            ),
            option(
                "no-coo",
                "No COO, no dots",
                ["Smile M2"],
                one("Smile M2", "No COO is the other state of this mould."),
                sure=True,
            ),
        ],
        "Smile's No COO does not say whether any of the country remains.",
    ),
    figure(
        "At-At Commander",
        "Look at the right leg. A single line of 'Made in Hong Kong' is Smile or Unitoy. A scar with dots is PBP.",
        [
            "Smile M1 = 'Made in Hong Kong' on right leg across a single line or no COO.",
            "Unitoy M2 = 'Made in Hong Kong' on right leg across a single line.",
            "PBP M2 = Scar on right leg with dots",
        ],
        [
            option(
                "line",
                "Made in Hong Kong, one line, right leg",
                ["Smile M1", "Unitoy M2"],
                shared(["Smile M1", "Unitoy M2"], "'Made in Hong Kong' runs across a single line on the right leg."),
            ),
            option(
                "no-coo",
                "No COO",
                ["Smile M1"],
                one("Smile M1", "No COO is the other state of this mould."),
                sure=True,
            ),
            option(
                "scar",
                "Scar on the right leg, with dots",
                ["PBP M2"],
                one("PBP M2", "The right leg has a scar with dots."),
                sure=True,
            ),
        ],
        "A single-line 'Made in Hong Kong' on the right leg does not separate Smile M1 from Unitoy M2.",
    ),
    figure(
        "Bespin Security Guard (Black)",
        "Look at the left leg. A single line of 'Made in Hong Kong' is Unitoy or Smile. Rough scarring and no country is PBP.",
        [
            "Unitoy M1 = 'Made in Hong Kong' on left leg across a single line.",
            "PBP M1 = No COO, rough scarring instead on left leg.",
            "Smile M2 = 'Made in Hong Kong' on left leg across a single line or no COO.",
        ],
        [
            option(
                "line",
                "Made in Hong Kong, one line, left leg",
                ["Unitoy M1", "Smile M2"],
                shared(["Unitoy M1", "Smile M2"], "'Made in Hong Kong' runs across a single line on the left leg."),
            ),
            option(
                "scar",
                "No COO, rough scarring on the left leg",
                ["PBP M1"],
                one("PBP M1", "The left leg is No COO, with rough scarring instead of the country."),
                sure=True,
            ),
            option(
                "no-coo",
                "No COO, no scar",
                ["Smile M2"],
                one("Smile M2", "No COO is the other state of this mould."),
                sure=True,
            ),
        ],
        "A single-line 'Made in Hong Kong' on the left leg does not separate Unitoy M1 from Smile M2.",
    ),
    figure(
        "4-LOM",
        "Look at the right leg. A single line of 'Made in Hong Kong' is Smile or Unitoy. No COO is Smile or PBP.",
        [
            "Smile M1 = 'Made in Hong Kong' on right leg across a single line or no COO.",
            "Unitoy M2 = 'Made in Hong Kong' on right leg across a single line.",
            "PBP M2 = No COO.",
        ],
        [
            option(
                "line",
                "Made in Hong Kong, one line, right leg",
                ["Smile M1", "Unitoy M2"],
                shared(["Smile M1", "Unitoy M2"], "'Made in Hong Kong' runs across a single line on the right leg."),
            ),
            option(
                "no-coo",
                "No COO",
                ["Smile M1", "PBP M2"],
                shared(["Smile M1", "PBP M2"], "No COO is listed for both."),
            ),
        ],
        "A single-line 'Made in Hong Kong' on the right leg does not separate Smile M1 from Unitoy M2. No COO does not separate Smile M1 from PBP M2.",
    ),
    figure(
        "Chief Chirpa",
        "These are not a 'Made in Hong Kong' stamp. Look at the right leg for 'H.K.' on a raised bar, and check whether either leg has licensing details.",
        [
            "Smile M1 = 'H.K.' on right leg on raised bar. Sometimes very faint almost smooth raised bar.",
            "Kader M2 = 'H.K.' on right leg on raised bar or no bar and no COO.",
            "Kader M3 = Either no COO or raised bar with 'H.K.'.",
            "Lili Ledy M4 = No COO.",
            "Top Toys M5 = No COO and no licensing details on either leg.",
        ],
        [
            option(
                "hk-bar",
                "'H.K.' on a raised bar on the right leg",
                ["Smile M1", "Kader M2", "Kader M3"],
                "",
                follows=[
                    follow(
                        "faint",
                        "The raised bar is very faint, almost smooth",
                        one("Smile M1", "'H.K.' is on the right leg on a raised bar that is very faint, almost smooth."),
                    ),
                    follow(
                        "clear",
                        "The raised bar is clear",
                        shared(["Smile M1", "Kader M2", "Kader M3"], "A clear 'H.K.' on a raised bar on the right leg is listed for all three."),
                        sure=False,
                    ),
                ],
                coo="Hong Kong",
            ),
            option(
                "no-coo",
                "No COO, no raised bar",
                ["Kader M2", "Kader M3", "Lili Ledy M4", "Top Toys M5"],
                "",
                follows=[
                    follow(
                        "no-license",
                        "No licensing details on either leg",
                        one("Top Toys M5", "No COO, and no licensing details on either leg."),
                    ),
                    follow(
                        "license",
                        "Licensing details are still there",
                        shared(["Kader M2", "Kader M3", "Lili Ledy M4"], "No COO with no raised bar, and licensing details still present, is listed for all three."),
                        sure=False,
                    ),
                ],
            ),
        ],
        "A clear 'H.K.' on a raised bar does not separate Smile M1, Kader M2, and Kader M3. No COO with licensing still present does not separate Kader M2, Kader M3, and Lili Ledy M4.",
        ask="Which of these do you see?",
    ),
    figure(
        "Nien Nunb",
        "Look at the right leg. A single line of 'Made in Hong Kong' is Unitoy or Smile. No COO with the licensing details on the right leg is Lili Ledy.",
        [
            "Unitoy M1 = 'Made in Hong Kong' on right leg across a single line or no COO.",
            "Smile M2 = 'Made in Hong Kong' on right leg across a single line or no COO.",
            "Lili Ledy M3 = No COO with licensing details on right leg.",
        ],
        [
            option(
                "line",
                "Made in Hong Kong, one line, right leg",
                ["Unitoy M1", "Smile M2"],
                shared(["Unitoy M1", "Smile M2"], "'Made in Hong Kong' runs across a single line on the right leg."),
            ),
            option(
                "lili",
                "No COO, licensing details on the right leg",
                ["Lili Ledy M3"],
                one("Lili Ledy M3", "No COO, with the licensing details on the right leg."),
                sure=True,
            ),
            option(
                "no-coo",
                "No COO, licensing not on the right leg",
                ["Unitoy M1", "Smile M2"],
                shared(["Unitoy M1", "Smile M2"], "No COO is the other state of both moulds."),
            ),
        ],
        "A single-line 'Made in Hong Kong' on the right leg does not separate Unitoy M1 from Smile M2. No COO without the licensing on the right leg does not separate them either.",
    ),
    figure(
        "Nikto",
        "Both known moulds are No COO. The stamp does not say which factory it is.",
        [
            "Smile M1 = No COO",
            "Lili Ledy M1 = No COO",
        ],
        [
            option(
                "no-coo",
                "No COO",
                ["Smile M1", "Lili Ledy M1"],
                shared(["Smile M1", "Lili Ledy M1"], "Both are No COO."),
            ),
        ],
        "Nothing in the stamp separates Smile M1 from Lili Ledy M1. Licensing location is not stated.",
    ),
    figure(
        "8D8",
        "Both moulds are No COO. The licensing details are on his back, not the legs.",
        [
            "Smile M1 = No COO with licensing details on his back",
            "Lili Ledy M2 = No COO with licensing details on his back",
        ],
        [
            option(
                "back",
                "No COO, licensing details on the back",
                ["Smile M1", "Lili Ledy M2"],
                shared(["Smile M1", "Lili Ledy M2"], "No COO, with the licensing details on his back."),
            ),
        ],
        "Nothing separates Smile M1 from Lili Ledy M2.",
        ask="Which of these do you see?",
    ),
    figure(
        "Princess Leia Organa (in Combat Poncho)",
        "All of these are No COO. The tell is where the licensing sits.",
        [
            "Smile M1 = No COO with licensing on left leg",
            "Kader M2 = No COO with licensing on left boot",
            "Lili Ledy M2 = No COO with licensing on left boot",
        ],
        [
            option(
                "leg",
                "Licensing on the left leg",
                ["Smile M1"],
                one("Smile M1", "No COO, with the licensing on the left leg."),
                sure=True,
                coo="No COO",
            ),
            option(
                "boot",
                "Licensing on the left boot",
                ["Kader M2", "Lili Ledy M2"],
                shared(["Kader M2", "Lili Ledy M2"], "No COO, with the licensing on the left boot."),
                coo="No COO",
            ),
        ],
        "Licensing on the left boot does not separate Kader M2 from Lili Ledy M2.",
        ask="Which of these do you see?",
    ),
    figure(
        "The Emperor",
        "All three moulds are No COO with the licensing on the left leg. The stamp does not separate them.",
        [
            "Smile M1 = No COO with licensing on left leg",
            "Unitoy M2 = No COO with licensing on left leg",
            "Unitoy M3 = No COO with licensing on left leg",
        ],
        [
            option(
                "left",
                "No COO, licensing on the left leg",
                ["Smile M1", "Unitoy M2", "Unitoy M3"],
                shared(["Smile M1", "Unitoy M2", "Unitoy M3"], "No COO, with the licensing on the left leg."),
            ),
        ],
        "Nothing separates Smile M1, Unitoy M2, and Unitoy M3.",
        ask="Which of these do you see?",
    ),
    figure(
        "B-Wing Pilot",
        "Both moulds are No COO. The tell is which leg carries the licensing.",
        [
            "Unitoy M1 = No COO with licensing on left leg",
            "Kader M2 = No COO with licensing on right leg",
        ],
        [
            option(
                "left",
                "Licensing on the left leg",
                ["Unitoy M1"],
                one("Unitoy M1", "No COO, with the licensing on the left leg."),
                sure=True,
                coo="No COO",
            ),
            option(
                "right",
                "Licensing on the right leg",
                ["Kader M2"],
                one("Kader M2", "No COO, with the licensing on the right leg."),
                sure=True,
                coo="No COO",
            ),
        ],
        "No other stamp wording is described.",
        ask="Which of these do you see?",
    ),
    figure(
        "Klaatu (in Skiff Guard Outfit)",
        "Both moulds are No COO with the licensing on the left leg. The stamp does not separate them.",
        [
            "Smile M1 = No COO with licensing on left leg",
            "Lili Ledy M1 = No COO with licensing on left leg",
        ],
        [
            option(
                "left",
                "No COO, licensing on the left leg",
                ["Smile M1", "Lili Ledy M1"],
                shared(["Smile M1", "Lili Ledy M1"], "No COO, with the licensing on the left leg."),
            ),
        ],
        "Nothing separates Smile M1 from Lili Ledy M1.",
        ask="Which of these do you see?",
    ),
    figure(
        "Prune Face",
        "Both moulds are No COO with the licensing on the left leg. The stamp does not separate them.",
        [
            "Unitoy M1 = No COO with licensing on left leg",
            "Kader M2 = No COO with licensing on left leg",
        ],
        [
            option(
                "left",
                "No COO, licensing on the left leg",
                ["Unitoy M1", "Kader M2"],
                shared(["Unitoy M1", "Kader M2"], "No COO, with the licensing on the left leg."),
            ),
        ],
        "Nothing separates Unitoy M1 from Kader M2.",
        ask="Which of these do you see?",
    ),
    figure(
        "Lumat",
        "The only described mould is No COO.",
        ["Lili Ledy M1 = No COO"],
        [
            option(
                "no-coo",
                "No COO",
                ["Lili Ledy M1"],
                one("Lili Ledy M1", "It is No COO."),
                sure=True,
            ),
        ],
        "Only Lili Ledy M1 is described, and only as No COO. Licensing location is not stated.",
    ),
    figure(
        "Paploo",
        "The only described mould is No COO.",
        ["Lili Ledy M1 = No COO"],
        [
            option(
                "no-coo",
                "No COO",
                ["Lili Ledy M1"],
                one("Lili Ledy M1", "It is No COO."),
                sure=True,
            ),
        ],
        "Only Lili Ledy M1 is described, and only as No COO. Licensing location is not stated.",
    ),
]


def norm(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def apply_owner_records(figures):
    by_name = {norm(fig.get("name")): fig for fig in figures}
    applied = 0
    for entry in OWNER:
        record = by_name.get(norm(entry["name"]))
        if not record:
            raise SystemExit(f"owner figure not in coo-figures.json: {entry['name']}")
        record["verified"] = True
        record["hasDetails"] = True
        record["source"] = "owner"
        record["sourceNote"] = "Owner of variantvillain.com, 10 Oct 2026."
        record["whereToLook"] = entry["whereToLook"]
        record["ask"] = entry["ask"]
        record["options"] = entry["options"]
        record["ownerStamps"] = entry["stamps"]
        record["missing"] = entry["missing"]
        applied += 1
    if applied != 31:
        raise SystemExit(f"expected 31 owner figures, applied {applied}")
    return figures


def stamp_phrase(opt):
    conclusion = (opt.get("conclusion") or "").strip()
    if re.search(r"(?i)(leg|boot|back|base|line|raised bar|licensing|scar|silver|EPM|H\.K\.)", conclusion):
        if ":" in conclusion and conclusion.lower().startswith("that "):
            conclusion = conclusion.split(":", 1)[1].strip()
        elif conclusion.lower().startswith("that "):
            parts = re.split(r"(?<=\.)\s+", conclusion, maxsplit=1)
            conclusion = parts[1] if len(parts) > 1 else opt.get("label") or ""
        conclusion = re.sub(r"(?i)\s*I'm not sure.*$", "", conclusion).strip()
        if conclusion:
            return conclusion
    label = opt.get("label") or ""
    for example in opt.get("examples") or []:
        if example == label or len(example) > 90:
            continue
        if re.search(r"(?i)(leg|hong kong|taiwan|china|macau|no coo|scar|H\.K\.)", example):
            return f"{label} ({example})" if label else example
    follows = opt.get("followUps") or []
    if follows and label:
        extra = "; ".join(item.get("label") or "" for item in follows if item.get("label"))
        return f"{label}. Then: {extra}" if extra else label
    return label


def cells_from_options(record):
    cells = []
    for opt in record.get("options") or []:
        phrase = stamp_phrase(opt)
        follows = opt.get("followUps") or []
        if follows and phrase and "Then:" not in phrase:
            bits = []
            for item in follows:
                text = item.get("conclusion") or ""
                if text.lower().startswith("that ") and ". " in text:
                    text = text.split(". ", 1)[1]
                bits.append(f"{item.get('label')}: {text}")
            extra = "; ".join(bits)
            phrase = f"{phrase}. Narrow further: {extra}"
        factories = [
            name for name in (opt.get("factories") or [])
            if name and name.strip().lower() not in {"no coo", "this figure's page"}
            and "this figure" not in name.lower()
            and not name.lower().startswith("coo family")
        ]
        if factories and phrase:
            for name in factories:
                cells.append(f"{name} = {phrase}")
        elif phrase:
            cells.append(phrase)
    deduped = []
    for cell in cells:
        if cell not in deduped:
            deduped.append(cell)
    return deduped


def missing_for_page(record, phrases):
    blob = " ".join(phrases)
    notes = [
        "Scraped from the character page. Leg, line breaks, licensing position, and mould numbers are included only where that page states them."
    ]
    if not record.get("verified"):
        notes.append("No verified stamp wording.")
    elif not re.search(r"(?i)\b(leg|boot|back|base)\b", blob):
        notes.append("Stamp location (leg, boot, back, or base) is not stated.")
    if record.get("verified") and not re.search(r"(?i)\blines?\b", blob):
        notes.append("Line breaks are not stated.")
    if record.get("verified") and not re.search(r"(?i)(licensing|licence|©|under the)", blob):
        notes.append("Position relative to the licensing mark is not stated.")
    guide = record.get("guide") or []
    if guide and not record.get("verified"):
        notes.append("Page factory guide, without stamp wording: " + "; ".join(guide[:8]) + ".")
    return " ".join(notes)


def write_workbook(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "variantvillain-gaps"
    headers = [
        "kind", "name", "year", "product", "wiki_name", "has_page", "page_url",
        "has_coo_factory_mould_details", "source", "missing",
    ]
    widest = max(len(row["stamps"]) for row in rows)
    headers.extend([""] * widest)
    ws.append(headers)
    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(color="FFFFFF", bold=True)
    for cell in ws[1]:
        if cell.value:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row in rows:
        values = [
            row["kind"], row["name"], row["year"], row["product"], row["wiki_name"],
            row["has_page"], row["page_url"], row["has_coo_factory_mould_details"],
            row["source"], row["missing"], *row["stamps"],
        ]
        ws.append(values)
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        width = 18
        if letter in {"B", "E", "G", "J"}:
            width = 42
        elif col[0].column > 10:
            width = 56
        ws.column_dimensions[letter].width = width
    for excel_row in ws.iter_rows(min_row=2):
        for cell in excel_row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.auto_filter.ref = ws.dimensions
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 22
    XLSX.parent.mkdir(parents=True, exist_ok=True)
    ART.parent.mkdir(parents=True, exist_ok=True)
    wb.save(XLSX)
    wb.save(ART)


def export_workbook():
    payload = json.loads(COO.read_text())
    by_url = {fig.get("sourceUrl"): fig for fig in payload["figures"]}
    owner_by_name = {norm(entry["name"]): entry for entry in OWNER}
    gaps = list(csv.DictReader(GAPS.open()))
    rows = []
    for gap in gaps:
        if gap.get("kind") != "figure":
            continue
        record = by_url.get(gap.get("page_url") or "")
        owner = owner_by_name.get(norm(gap.get("name")))
        if owner:
            stamps = owner["stamps"]
            source = "owner"
            missing = owner["missing"]
        elif record:
            stamps = cells_from_options(record)
            source = "variantvillain.com"
            missing = missing_for_page(record, stamps)
        else:
            stamps = []
            source = ""
            missing = "No Variant Villain page matched, so no stamp was exported."
        rows.append({
            "kind": gap.get("kind", "figure"),
            "name": gap.get("name", ""),
            "year": gap.get("year", ""),
            "product": gap.get("product", ""),
            "wiki_name": gap.get("wiki_name", ""),
            "has_page": gap.get("has_page", ""),
            "page_url": gap.get("page_url", ""),
            "has_coo_factory_mould_details": gap.get("has_coo_factory_mould_details", ""),
            "source": source,
            "missing": missing,
            "stamps": stamps,
        })
    if len(rows) != 96:
        raise SystemExit(f"expected 96 figure rows, got {len(rows)}")
    owners = [row for row in rows if row["source"] == "owner"]
    if len(owners) != 31:
        raise SystemExit(f"expected 31 owner rows, got {len(owners)}")
    write_workbook(rows)
    print(f"wrote {XLSX} figures={len(rows)} owner={len(owners)}")


def main():
    payload = json.loads(COO.read_text())
    payload["figures"] = apply_owner_records(payload["figures"])
    payload["ownerStampNote"] = "Owner of variantvillain.com, 10 Oct 2026. Typos corrected on import."
    COO.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    OWNER_JSON.write_text(json.dumps({"recorded": "2026-10-10", "source": "owner", "figures": OWNER}, indent=2, ensure_ascii=False) + "\n")
    verified = sum(1 for fig in payload["figures"] if fig.get("verified"))
    print(f"applied owner stamps verified_now={verified} of {len(payload['figures'])}")


if __name__ == "__main__":
    main()
