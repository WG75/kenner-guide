# Owner VF-CB reference pack: conflicts

Compared 10 Oct 2026. Where the pack disagrees with the owner's 10 Oct 2026 stamp sheet or with variantvillain.com, the live data was kept. The pack was not used to overwrite those lines.

## Kept, and not overwritten

- Double-telescoping rarity. The live guide says Luke's yellow DT is the common one (most, but not all, Early Bird Lukes), and that Ben's blue DT and Vader's red DT are both extremely rare. The pack's lightsaber overview says Vader's red is mostly pre-production, and the pack's Ben figure note says blue is very rare compared with Vader's red. Those pack lines were not copied.
- Single-telescoping M6 and M9. The Darth Vader figure guide (variantvillain.com) says M6 is the round transition, thin shaft, PBP, and M9 is the smooth transition, fat tip, short shaft, Lili Ledy Regreso. The pack says M6 is an unknown factory, likely Palitoy, and that M9 has lettered hilts. Lettered hilts are M1, so the pack's M9 also breaks that rule. The Vader list was copied into the telescoping accessory file. The pack's M6 and M9 were not.
- Jawa blaster colours and the Han Solo Glasslite notes already in the live file are more specific than the pack. The pack file was not copied over them.
- Jawa cloth timing. The live Jawa figure note says the switch from vinyl to cloth happened very early, and that cloth appeared very early. The pack calls the cloth cloak a later release. The construction notes were added. The "later release" claim was not.
- Country-of-origin stamps. The 10 Oct 2026 owner stamp sheet and the variantvillain.com character pages stay the button source. The pack has no stamp sheet that replaces them.
- A partial or cut-off country name already counts as No COO in the COO explanation and in `data/references/coo-guide.txt`. Nothing in the pack was needed to add that rule.
- The pack's Luke farmboy JSON says some late No COO Smile examples can use a handheld Bespin-style sabre. That sentence is not in the Luke figure reference, so it was not added.
- The 13 first-wave figure files in the pack are the same as, or shorter than, the live files, apart from biography and the conflicts above. Biography was not copied.

## Owner rules applied on top of an older live line

These were changed because the owner stated the rule with this pack. The older live line is the conflict.

- Lettered sabres are always M1. The double-telescoping file, the Ben Kenobi DT lines, and `accvar_dt_lightsaber_m2_yellow` called the lettered DT M2 and the circled unlettered DT M1. The lettered DT is now M1. The circled DT is described without that old number. The JSON id is unchanged so existing links still resolve. The record's variant code is M1.
- Gaffi sticks exist only as M1 (Unitoy), M2, and M3 (Kader). The live gaderffii file named Kader for early and mid production, and named PBP (Spain) and Lili Ledy (Mexico) as further factories of the stick. Those factory lines were removed. M2's factory is not stated.
- The accessory is the Rebel Blaster. Greedo and Snaggletooth said Smuggler Blaster. The Rebel Blaster file listed the misspellings Smugger Blaster and Smaugglers Blaster as aliases. The name in this guide is Rebel Blaster. Han Solo Blaster remains as the other name already used on those Rebelscum lines.
- This guide does not grade a figure Mint. The glossary still expands MOC as "Mint on Card", which is the sealed-package name. A line was added that the guide does not assign a Mint grade.

## Not restored

- The pack's old `api/chat.js` keeps a running figure and accessory from earlier turns so a follow-up can use them. The live chat already sends the thread history, and the page keeps that thread in sessionStorage. The old file was not restored.
- The pack's `vercel.json` and the Word reference template were not applied. The template is a layout, and the live `vercel.json` is the current app config.
