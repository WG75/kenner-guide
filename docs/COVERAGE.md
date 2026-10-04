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

Every index URL is represented. `data/catalog.json` lists each name, era, file and source URL. The chat page searches that list from the box under the header. It does not put the typed search text into the conversation.

An empty chat keeps the greeting, the two Identify buttons, and the input together under that search box. It does not offer pre-set starter questions. The first user message switches the page to a scrolling transcript with those buttons docked at the bottom. Suggested follow-ups still appear under later replies. Identify a figure and Identify Accessories are only the buttons above the input.

## What already existed

Twelve figure dossiers: Luke Skywalker, Princess Leia Organa, R2-D2, Chewbacca, C-3PO, Darth Vader, Stormtrooper, Ben (Obi-Wan) Kenobi, Han Solo, Jawa, Sand People, Death Squad Commander.

Fourteen accessory files already in the repo (blasters, sabers, capes, cloak, bowcaster, gaderffii stick), plus `accessory_lightsaber.json`. Those were not overwritten.

The debut-cardback workbook (96 figures, split reference files) was already present and is still the cardback source when a block exists.

## What was added

New figure and accessory files follow the same rules as the existing reference data: evidence labels, no invented variants, Debut Kenner Cardback kept separate from factory matching, Early Bird limited to Luke, Leia, Chewbacca and R2-D2. Each new file cites its Variant Villain URL. Lists that follow a heading or a colon are kept in full. Shop ads and photo-credit names are not stored as variants.

## Stub and thin files

Before this quality pass, counted on the generated figure files:

- 23 files contained the page-stub sentence "Sorry, content not available" (including 8D8, 2-1B, FX-7, Dengar, and B-Wing Pilot).
- 5 files said the page yielded no section text: Luke Skywalker (Hoth Battle Gear), AT-AT Commander, Bespin Security Guard (Black), Logray (Ewoks), King Gorneesh.
- Paploo was a further thin file: one truncated bullet, no paint list, and "Debut Kenner Cardback: unknown" with no workbook path and none of the cardbacks the page names.
- That is 29 stub or thin figure files. Accessory files kept mould headings but dropped the colour lists and figure pairings under them.

After the re-parse:

- 0 files contain "Sorry, content not available".
- 0 files treat a photo credit as a variant. The R5-D4 "Red Bar" card list no longer carries the contributor's name.
- Paploo now has both Lili Ledy paint bullets, the page cardings (Lili Ledy 50-back, flagged; ROTJ 79; Trilogo; 92-back POTF), and a pointer to `data/compatibility/debut-cardbacks-reference-rotj-4.txt`. The workbook block itself still says the debut is unknown. Rebelscum's photo archive says the US debut is the 79-back and a Canadian 77-back came first. Those two debut claims conflict and stay unresolved. The workbook line remains the debut record.
- 50 figure files still have a Variant Villain body under 900 characters, because the page is an index or unpublished. 43 of those now also cite the Wikipedia Kenner list and/or a Rebelscum photo-archive page. 7 still have no matching row on those sources, so factory, paint, and debut from them are unknown: Droids C-3PO, Dulok Scout, Dulok Shaman, King Gorneesh, Logray (Ewoks), Urgah Lady Gorneesh, and Bespin Security Guard (Black).
- Lando Skiff Helmet still has only the page index (Smile, Unitoy, Lili Ledy). Colours are unknown.

## Retrieval cap

Chat injects a reference file only when `tcLoadFiles` reads it and it is at most 7,000 characters. That scan is `data/figures`, `data/accessories`, `data/references`, `data/terms`, `data/variants`, `data/compatibility`, and `data/factories.json`.

`data/flows` is not in that scan. `loadFlow` reads a scripted flow and its numbered part files whole. `data/catalog.json` and `data/catalog-1.json` through `data/catalog-6.json` are fetched only by the search box in `index.html`. The cap test skips `data/flows` and the catalog JSON files for that reason. Every file the retriever can inject is under 7,000 characters.

`data/references/variant-counts.txt` and its numbered parts are generated by `tools/build-variant-counts.py` from `data-source/vv-variant-counts.json`. That snapshot is the live Variant Villain figure guides fetched on 2026-10-04 (SW, ESB, ROTJ, and the POTF and Droids indexes, which use the same roman-numeral rule), checked against each page's COO sheet or figure-guide image. Where the image and the text disagree, the image is used. It is not under `data/`, so the retriever does not load the raw snapshot. Each documented figure's families are listed under its count, one family per line, with a precomputed factory count and production years when a Released or Release Date line exists. A second count, the pictured versions inside each family, is stored on the snapshot. Figures are ranked by that version total when every family has a readable list. Otherwise the version total is unverified. Each multi-version character's catalog names are listed the same way. Paint, cape and sabre sections are not counted. A page with no readable roman grid is "unverified". A count question retrieves the summary, and a question that names a figure also retrieves that figure's dossier. "Which figure has the most variants?" does the same for the top ranked figure when the retrieval index lists that dossier as a figure. Follow-up chips under a count answer are built from that figure's records: a cardback question only when a debut block exists, and a double-telescoping sabre question only for Luke Skywalker, Ben (Obi-Wan) Kenobi and Darth Vader. Each part stays under the 7,000 character cap.

`data/retrieval-index.json` is generated by `tools/build-retrieval-index.py`. It lists each injected file's topic, aliases, keywords and years. Chat reads it for routing and does not inject it, so the cap test skips it, the same way it skips the catalog. Topics recorded now: figure, accessory, cardback, coo, factory, variant, term, reference, and palitoy. Variant-count files are role summary, and their keywords include the ranked figure names. A question can also be routed as playset or vehicle; those boosts apply when a file carries that topic. Ordinary figure questions keep the existing score, so a dossier stays ahead of the index.

Palitoy UK release years are Warren's own list (1978 to 1983; he wrote "1978 to 1975"). `tools/build-palitoy-releases.py` writes `data-source/palitoy-uk-releases.json` and the `data/references/palitoy-uk-*.txt` files. Each entry cites that list, reliability primary, recorded 2026-10-04, and no public URL. A year question loads that year. A "when" question loads the item's year index. A question about what was not a figure loads the non-figure files. Status notes (unconfirmed, not released, not stated) stay on the entry. `data/references/palitoy-history.txt` is a short paraphrase of the Wikipedia Palitoy article (reliability lower, fetched 2026-10-04). The Fandom Palitoy page was skipped because robots.txt returned a Cloudflare challenge.

Phase B adds short paraphrases of the Variant Villain sections that were not already figure or accessory dossiers. `tools/fetch-vv-phase-b.py` reads the sitemaps one page at a time and writes `data-source/vv-phase-b.json`. `tools/build-vv-phase-b.py` writes `data/references/vv-*.txt` and rebuilds the retrieval index. Each note cites Variant Villain, the page URL, reliability high, and 2026-10-04. Photographs are not stored. Topics now include playset and vehicle. Company cardback guides are role guide, so a Palitoy or Trilogo cardback question ranks those files, while a named figure's debut question still ranks the debut workbook first.

These were split so a long guide is not cut off mid-file. Each part repeats the name, aliases, and source. The Early Bird factory sentence stays in part 1 of R2-D2 and Chewbacca.

- `data/figures/r2-d2-reference-1.txt` and `r2-d2-reference-2.txt`
- `data/figures/chewbacca-reference-1.txt` and `chewbacca-reference-2.txt`
- Longer generated guides such as R5-D4, Yoda, and Boba Fett are split the same way (`-2`, `-3`, …).
- `data/flows/jawa.figure.json` and `jawa.figure-2.json` (the guided flow loads both; not retrieval-capped)
- `data/flows/jawa.blaster.json` and `jawa.blaster-2.json`
- `data/catalog.json` plus `data/catalog-1.json` through `data/catalog-6.json` (the search box loads every part; not retrieval-capped)
