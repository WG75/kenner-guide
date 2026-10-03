# VF-CB coverage

Audit of Variant Villain index pages against `/data`, after the full-coverage build.
Source indexes (fetched politely, one request at a time):

- https://www.variantvillain.com/characters/sw/ (21 figures)
- https://www.variantvillain.com/characters/esb/ (29 figures)
- https://www.variantvillain.com/characters/rotj/ (31 figures)
- https://www.variantvillain.com/characters/potf/ (15 figures)
- https://www.variantvillain.com/characters/droids/ (8 figures)
- https://www.variantvillain.com/accessory-guide/ (64 accessories)

Cross-check: https://en.wikipedia.org/wiki/List_of_Kenner_Star_Wars_action_figures (96 carded figures, all matched to a name already on those indexes). Factory and COO pages cited from https://www.variantvillain.com/knowledge/factory-codes/ and https://www.variantvillain.com/knowledge/introduction-to-coos/.

## Status

| Set | On the indexes | Files now | Notes |
| --- | --- | --- | --- |
| Figures | 104 URLs | 103 | Wicket is one file for two URLs (ROTJ and Droids & Ewoks). |
| Kenner carded figures in the debut workbook | 96 | 96 | The original 12 dossiers were kept. 84 new figure files were added. |
| Droids & Ewoks | 8 URLs | 7 unique files plus the shared Wicket file | Not in the debut-cardback workbook. Debut line is unknown. |
| Accessories | 64 | 64 | 14 existing files kept. 50 new files added. |

Every index URL is represented. `data/catalog.json` lists each name, era, file and source URL so the chat page can offer every figure and accessory.

## What already existed

Twelve figure dossiers: Luke Skywalker, Princess Leia Organa, R2-D2, Chewbacca, C-3PO, Darth Vader, Stormtrooper, Ben (Obi-Wan) Kenobi, Han Solo, Jawa, Sand People, Death Squad Commander.

Fourteen accessory files already in the repo (blasters, sabers, capes, cloak, bowcaster, gaderffii stick), plus `accessory_lightsaber.json`. Those were not overwritten.

The debut-cardback workbook (96 figures, split reference files) was already present and is still the cardback source when a block exists.

## What was added

New figure and accessory files follow the same rules as the existing reference data: evidence labels, no invented variants, Debut Kenner Cardback kept separate from factory matching, Early Bird limited to Luke, Leia, Chewbacca and R2-D2. Each new file cites its Variant Villain URL. Page text is a short heading-plus-sentence extract, not a copy of the article.

## Still thin

These pages did not yield prose (image-led pages). The files say unknown and do not guess:

- Luke Skywalker (Hoth Battle Gear)
- AT-AT Commander
- Bespin Security Guard (Black)
- Logray (Ewoks)
- King Gorneesh
- Lando Skiff Helmet

Other new files are extracts. A mould photo with no sentence is not transcribed.

## Retrieval cap

Chat injects a whole reference file only when it is at most 7,000 characters. Every file under `data/` is under that cap.

These were split so an answer is not cut off mid-file. Each part repeats the figure name, aliases, and source. The Early Bird factory sentence stays in part 1.

- `data/figures/r2-d2-reference-1.txt` and `r2-d2-reference-2.txt`
- `data/figures/chewbacca-reference-1.txt` and `chewbacca-reference-2.txt`
- `data/flows/jawa.figure.json` and `jawa.figure-2.json` (the guided flow loads both)
- `data/flows/jawa.blaster.json` and `jawa.blaster-2.json`
- `data/catalog.json` plus `data/catalog-1.json` through `data/catalog-6.json` (the lookup menu loads every part)
