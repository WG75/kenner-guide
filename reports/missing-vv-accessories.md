# Figure accessories with no Variant Villain guide

Research note, 4 October 2026. Not reference data for the chat. Nothing here was inferred from a name alone. A row is included only when a fetched page, or a line already stored from an earlier fetch, names that accessory for that figure.

Baseline: the live accessory index at https://www.variantvillain.com/accessory-guide/ (fetched 4 October 2026, HTTP 200). It links 64 accessory guides. Our `data/accessories` files match those 64 titles. A guide counts as present when that index has a page, even if the page is thin.

Reliability, as used below:

- **high** — Variant Villain states it.
- **documented** — Rebelscum, Mr Vintage, or Imperial Gunnery states it in plain text. These are collector sites, not factory records.
- **probable** — Imperial Gunnery says "we believe".

## What was read, and what was not

Read on 4 October 2026, all HTTP 200 unless noted:

- https://www.variantvillain.com/accessory-guide/
- Five Mr Vintage list pages: [1977–1979](https://www.mrvintagestarwars.com/kenner-star-wars-action-figures-1977-1979/), [Empire 1980–1982](https://www.mrvintagestarwars.com/kenner-the-empire-strikes-back-action-figures-1980-1982/), [Return of the Jedi 1982–1984](https://www.mrvintagestarwars.com/kenner-the-return-of-the-jedi-1982-1984-action-figures/), [Power of the Force](https://www.mrvintagestarwars.com/kenner-power-of-the-force-action-figures-1984/), [Ewoks 1985](https://www.mrvintagestarwars.com/kenner-ewoks-action-figures-1985/)
- https://imperialgunnery.com/identificationguide.htm and https://www.imperialgunnery.com/other-accessories.htm
- https://en.wikipedia.org/wiki/List_of_Kenner_Star_Wars_action_figures
- Six Rebelscum figure pages, listed in the tables where they were re-fetched
- Five thin Variant Villain accessory pages, listed in the thin section

Stored, not re-fetched this pass:

- The other Rebelscum "Weapons and Accessories" lines already copied into `data/figures`. The six pages re-fetched today still match those stored lines.
- Imperial Gunnery staff and hood notes already copied into the figure files, from https://imperialgunnery.com/staffs-axes.htm and https://imperialgunnery.com/helmets-hoods.htm. Where a file says those two pages did not name the figure, that is the stored result.

Unreachable:

- https://theswca.com/ , https://theswca.com/textf/all-figs-old.html and https://theswca.com/index.php?action=disp_item&item_id=51194 each returned HTTP 403. SWCA was not used.

Wikipedia's Kenner list has card line, number and year. It has no weapons column. The only "lightsaber" on the page is the figure name "Artoo-Detoo (R2-D2) with pop-up Lightsaber". Wikipedia does not attest a separate accessory list.

No Droids accessory list was found on the Mr Vintage pages fetched. The Ewoks cartoon line was.

Left out on purpose:

- Figure features the lists put under weapons: a clicking head, a sensorscope, a movable mouth, and Anakin's "A Million Dollar Smile" / "Absolutely nothing".
- Chewbacca's "Collector's Coin (POTF)" on the 1977–1979 page. One line names a coin. No other figure's coin was copied out, so a coin list was not built.
- The Hoth backpack and the Survival Kit gas mask. Imperial Gunnery says the Hoth backpack was packed in the Survival Kit and the Rebel Transport, not with a figure. https://www.imperialgunnery.com/other-accessories.htm
- Palitoy's Three Position Laser Rifle. Warren's list records it as its own weapon, not as something packed with a figure. There is no Variant Villain accessory page of that name.

## 1. No Variant Villain accessory page

The figure page, where one exists, does not document the accessory. "Yet to be documented" is Variant Villain's own sentence.

### Variant Villain says it is not documented yet

| Figure | Accessory | Also attested by | URL | Reliability |
| --- | --- | --- | --- | --- |
| Paploo | Hood | Rebelscum (re-fetched); Mr Vintage ROTJ list; Imperial Gunnery hoods (stored, documented) | https://www.variantvillain.com/characters/rotj/paploo/ and https://www.rebelscum.com/VINtPaploo.asp and https://www.mrvintagestarwars.com/kenner-the-return-of-the-jedi-1982-1984-action-figures/ and https://imperialgunnery.com/helmets-hoods.htm | high, and documented |
| Paploo | Quiver | Variant Villain figure page only. Rebelscum and Mr Vintage do not name a quiver. | https://www.variantvillain.com/characters/rotj/paploo/ | high |
| Paploo | Spear | Variant Villain figure page only, and it conflicts with the other two. See the note under this table. | https://www.variantvillain.com/characters/rotj/paploo/ | high |
| Romba | Hood | Rebelscum (stored); Mr Vintage POTF list | https://www.variantvillain.com/characters/potf/romba/ and https://www.rebelscum.com/VINtRomba.asp and https://www.mrvintagestarwars.com/kenner-power-of-the-force-action-figures-1984/ | high, and documented |
| Lumat | Hood | Rebelscum (re-fetched); Mr Vintage ROTJ list | https://www.variantvillain.com/characters/rotj/lumat/ and https://www.rebelscum.com/VINtLumat.asp and https://www.mrvintagestarwars.com/kenner-the-return-of-the-jedi-1982-1984-action-figures/ | high, and documented |
| Lumat | Quiver, painted | Rebelscum (re-fetched); Mr Vintage; Imperial Gunnery other-accessories (the heading is there; the fetched text adds no description) | same Lumat and Rebelscum URLs, and https://www.imperialgunnery.com/other-accessories.htm | high, and documented |
| Lumat | Bow, light brown | Rebelscum (re-fetched); Mr Vintage | same Lumat URLs | high, and documented |
| Warok | Hood | Rebelscum (stored); Mr Vintage POTF list ("Removable Hood") | https://www.variantvillain.com/characters/potf/warok/ and https://www.rebelscum.com/VINtWarok.asp and https://www.mrvintagestarwars.com/kenner-power-of-the-force-action-figures-1984/ | high, and documented |
| Warok | Quiver, not painted | Rebelscum (stored, "Ewok Quiver (Not Painted)"); Mr Vintage; Imperial Gunnery ("Warok Quiver (Not Painted)") | same Warok URLs and https://www.imperialgunnery.com/other-accessories.htm | high, and documented |
| Warok | Bow, dark brown | Rebelscum (stored); Mr Vintage. Mr Vintage says the bow is dark brown, against Lumat's light brown. | same Warok URLs | high, and documented |
| Luke Skywalker (Imperial Stormtrooper Outfit) | Helmet | Rebelscum (stored, "Stormtrooper Helmet"); Mr Vintage POTF ("Removable Helmet") | https://www.variantvillain.com/characters/potf/luke-skywalker-imperial-stormtrooper-outfit/ and https://www.rebelscum.com/VINtLukestormtrooper.asp and https://www.mrvintagestarwars.com/kenner-power-of-the-force-action-figures-1984/ | high, and documented |
| Luke Skywalker (in Battle Poncho) | Helmet | Variant Villain figure page only. Rebelscum, re-fetched, names the belt and the poncho, not a helmet. Mr Vintage names the blaster, poncho and belt, not a helmet. | https://www.variantvillain.com/characters/potf/luke-skywalker-in-battle-poncho/ | high |
| Luke Skywalker (in Battle Poncho) | Poncho | Rebelscum (re-fetched, "Battle Poncho (Brown)"); Mr Vintage ("Removable Poncho") | https://www.rebelscum.com/VINtLukeponcho.asp and the POTF list | high, and documented |
| Luke Skywalker (in Battle Poncho) | Belt, 3 settings | Rebelscum (re-fetched, "Poncho Belt (3 Settings)"); Mr Vintage ("Removable Belt with holster") | same | high, and documented |
| Lando Calrissian (General Pilot) | Cape | Mr Vintage POTF ("Removable flowing Cape") | https://www.variantvillain.com/characters/potf/lando-calrissian-general-pilot/ and https://www.mrvintagestarwars.com/kenner-power-of-the-force-action-figures-1984/ | high, and documented |
| Barada | Skiff vibro staff | Mr Vintage POTF calls it "Staff" | https://www.variantvillain.com/characters/potf/barada/ and the POTF list | high, and documented |
| Yak Face | Skiff vibro staff | Mr Vintage POTF calls it "Staff" | https://www.variantvillain.com/characters/potf/yak-face/ and the POTF list | high, and documented |

Paploo and Romba disagree with the accessory index about the spear. Paploo's figure page says he was packed with his own hood, quiver and spear, and that those are yet to be documented. Romba's figure page says his hood is his own, and that his spear, made by Smile in Hong Kong, is shared with Wicket, and that both are yet to be documented. The accessory index does have https://www.variantvillain.com/accessory-guide/ewok-spear/ . That page is thin (next section). Rebelscum and Mr Vintage call Paploo's weapon an Ewok battle staff, not a spear, and they do not mention a Paploo quiver. Imperial Gunnery's stored Paploo note is a staff, and the mark on one version is only "what we believe to be a reverse letter C" (probable). Those are not treated as the same object as the Ewok Spear page.

The blaster packed with Luke in the stormtrooper outfit, Luke in the battle poncho, and Lando General is already on an accessory page (Imperial Blaster or Palace Blaster). Only the helmet, poncho, belt and cape are in this table.

### Other sources name it, and no accessory page was found

The stored figure extract has no Variant Villain description of the accessory. Rebelscum lines marked "stored" were not re-fetched today.

| Figure | Accessory | Source | URL | Reliability |
| --- | --- | --- | --- | --- |
| 4-LOM | Rifle | Rebelscum, re-fetched ("4-LOM Rifle"); Mr Vintage Empire list ("Laser Rifle") | https://www.rebelscum.com/VINt4-LOM.asp and https://www.mrvintagestarwars.com/kenner-the-empire-strikes-back-action-figures-1980-1982/ | documented |
| 4-LOM | Backpack | Rebelscum, re-fetched ("4-LOM Back Pack"). Mr Vintage does not name it. | https://www.rebelscum.com/VINt4-LOM.asp | documented |
| 4-LOM | Cloak | Rebelscum, re-fetched ("4-LOM Cloak"). Mr Vintage does not name it. | https://www.rebelscum.com/VINt4-LOM.asp | documented |
| 4-LOM | Chest armour | Imperial Gunnery. The text describes serial numbers ending 4, 3, 1 and 2. Not the same sentence as the backpack. | https://www.imperialgunnery.com/other-accessories.htm | documented |
| Zuckuss | Rifle | Rebelscum, stored ("Zuckuss Rifle"); Mr Vintage Empire list ("Laser Rifle") | https://www.rebelscum.com/VINtZuckuss.asp and the Empire list | documented |
| Rebel Commando | Rifle | Rebelscum, stored ("Commando Rifle"); Mr Vintage ROTJ list | https://www.rebelscum.com/VINtRebcommando.asp and the ROTJ list | documented |
| Nikto | Skiff guard battle staff | Rebelscum, stored; Mr Vintage ROTJ list; Imperial Gunnery staffs, stored (documented: an ejector-pin mark on either side; the Lili Ledy version is darker grey) | https://www.rebelscum.com/VINtNikto.asp and the ROTJ list and https://imperialgunnery.com/staffs-axes.htm | documented |
| Prune Face | Cloak | Rebelscum, stored ("Pruneface Cloak"); Mr Vintage ROTJ list. The rifle has a page. | https://www.rebelscum.com/VINtPruneface.asp and the ROTJ list | documented |
| Rancor Keeper | Hood | Rebelscum, re-fetched; Mr Vintage ROTJ list; Imperial Gunnery hoods, stored (documented: an ejector-pin mark, and a darker harder version with none) | https://www.rebelscum.com/VINtRancorKeeper.asp and the ROTJ list and https://imperialgunnery.com/helmets-hoods.htm | documented |
| Wicket W. Warrick | Hood | Rebelscum, stored ("Wicket Hood"); Mr Vintage ROTJ list | https://www.rebelscum.com/VINtWicket.asp and the ROTJ list | documented |
| Princess Leia Organa (in Combat Poncho) | Battle helmet | Rebelscum, re-fetched; Mr Vintage ROTJ list | https://www.rebelscum.com/VINtLeiaponcho.asp and the ROTJ list | documented |
| Princess Leia Organa (in Combat Poncho) | Poncho belt, 2 settings | Rebelscum, re-fetched; Mr Vintage ROTJ list. The figure page mentions two poncho colours. It does not describe the belt. | same | documented |
| Klaatu | Skiff guard axe | Mr Vintage ROTJ list, with the Klaatu skirt. The skirt has a page. No sentence was found that this axe is the Vibro Axe page. | the ROTJ list | documented |
| Logray (Ewok Medicine Man) | Shaman staff | Rebelscum, stored ("Shaman Staff"); Mr Vintage ("Shaman Staff"). The figure page has the heading "LOGRAY STAFF" and no text under it. | https://www.rebelscum.com/VINtLogray.asp and the ROTJ list and https://www.variantvillain.com/characters/rotj/logray-ewok-medicine-man/ | documented |
| Logray (Ewok Medicine Man) | Pouch | Rebelscum, stored ("Shaman Satchel"); Mr Vintage ("Shaman Pouch"); Imperial Gunnery (V1 with ejector-pin marks, V2 "Issued with the Top Toys release Logray", V3 with none) | same, and https://www.imperialgunnery.com/other-accessories.htm | documented |
| Logray (Ewok Medicine Man) | Headdress | Rebelscum, stored ("Logray Headdress"); Mr Vintage ("Logray Headgear") | https://www.rebelscum.com/VINtLogray.asp and the ROTJ list | documented |
| Wicket (Ewoks line) | Spear | Mr Vintage Ewoks 1985 list. This is the later cartoon sculpt, not the Return of the Jedi Wicket line above. | https://www.mrvintagestarwars.com/kenner-ewoks-action-figures-1985/ | documented |
| Dulok Shaman | Necklace | Mr Vintage Ewoks list, with a staff. The figure page has the heading "DULOK SHAMAN STAFF" and then "COO V3 sheet coming soon". It does not mention a necklace. | the Ewoks list and https://www.variantvillain.com/characters/droids/dulok-shaman/ | documented |
| Dulok Scout | Club | Mr Vintage Ewoks list. The figure page has no accessory note. | the Ewoks list and https://www.variantvillain.com/characters/droids/dulok-scout/ | documented |
| Dagobah backpack | Figure not stated | Imperial Gunnery headings "Dagobah Backpack" and "Dagobah Backpack Original". The fetched text does not say which figure it came with. | https://www.imperialgunnery.com/other-accessories.htm | documented as an object; figure unknown |

Paploo's staff, as Rebelscum, Mr Vintage and Imperial Gunnery name it, is not the same sentence as Variant Villain's "spear". It is listed here so the disagreement stays visible: those three call it a staff; Variant Villain's Paploo page calls it a spear and says it is undocumented. Imperial Gunnery's stored wording for one mark is probable, not documented.

### A heading on the figure page, and no accessory-guide page

These are not "no page at all". The figure guide names the thing. There is still no page under https://www.variantvillain.com/accessory-guide/ .

| Figure | What the figure page has | Other source | Figure URL |
| --- | --- | --- | --- |
| Chief Chirpa | Family lines name a staff and a hood (brown, reddish, caramel) | Rebelscum and Mr Vintage: "Ewok Chief Staff" and "Chief Chirpa Hood". Imperial Gunnery documents both. | https://www.variantvillain.com/characters/rotj/chief-chirpa/ |
| Klaatu (in Skiff Guard Outfit) | A "SKIFF VIBRO STAFF" heading, and notes on a painted or unpainted hood that read as the figure's own hood | Rebelscum and Mr Vintage call the weapon a "Skiff Guard Force Pike" | https://www.variantvillain.com/characters/rotj/klaatu-in-skiff-guard-outfit/ |
| Squid Head | A "SQUID HEAD CAPE" section. Kenner packed dark green and brown; Lili Ledy a wider set of colours. | Mr Vintage ROTJ list: "Squid Head Cape", plus the skirt, belt and Bespin blaster, which do have pages | https://www.variantvillain.com/characters/rotj/squid-head/ |
| Emperor's Royal Guard | The figure page discusses outer cloaks (ribbed, slit, colour by factory). The pike has its own accessory page. | Mr Vintage: "Outer Cloak" and "Inner Cloak" | https://www.variantvillain.com/characters/rotj/emperors-royal-guard/ |
| Princess Leia Organa (in Combat Poncho) | Two poncho colours are described. No helmet or belt guide. | Rebelscum and Mr Vintage, as in the table above | https://www.variantvillain.com/characters/rotj/princess-leia-organa-in-combat-poncho/ |
| King Gorneesh | Heading "KING GORNEESH STAFF", then "COO V3 sheet coming soon" | Mr Vintage Ewoks list: "Staff" | https://www.variantvillain.com/characters/droids/king-gorneesh/ |
| Logray (Ewoks) | Heading "EWOKS LOGRAY STAFF", then "COO V3 sheet coming soon" | Mr Vintage Ewoks list: "Staff" | https://www.variantvillain.com/characters/droids/logray-ewoks/ |
| Dulok Shaman | Heading "DULOK SHAMAN STAFF", then "COO V3 sheet coming soon" | Mr Vintage Ewoks list: "Staff" | https://www.variantvillain.com/characters/droids/dulok-shaman/ |

## 2. A Variant Villain page exists, and the text is thin or unfinished

Judged from the stored extract, which keeps colour and mould lists that follow a heading, and from a re-read of the live page on 4 October 2026. A page is not called thin just because the file is short. Pages that go on to list colours are left out.

| Accessory | Page | What the text says | Reliability |
| --- | --- | --- | --- |
| Ewok Spear | https://www.variantvillain.com/accessory-guide/ewok-spear/ | Stored text is a mould comparison only: Universal Manufacturers, and Smile. The live text read today did not add colours. Romba's figure page still says this spear is yet to be documented. | high |
| Lando Skiff Helmet | https://www.variantvillain.com/accessory-guide/lando-skiff-helmet/ | Stored text is the index only: Smile, Unitoy, Lili Ledy/MIM. Colours are not stated. Mr Vintage calls the same object a "Skiff Guard Helmet". | high |
| Leia Boushh Rifle | https://www.variantvillain.com/accessory-guide/leia-boushh-rifle/ | Stored text is mould families only: Smile, Smile Macau, Unitoy / Lili Ledy, Universal Manufacturers. No colours in that extract, and none in the live text read today. | high |
| C-3PO (Removable Limbs) Net | https://www.variantvillain.com/accessory-guide/c-3po-removable-limbs-net/ | Stored text is Unitoy, Smile, Lili Ledy. No colours. | high |
| Carbonite Chamber | https://www.variantvillain.com/accessory-guide/carbonite-chamber/ | The live page says a detailed mould guide "will be made eventually", and then describes a reproduction. | high |
| Ugnaught Smock | https://www.variantvillain.com/accessory-guide/ugnaught-smock-guide/ | Factory straps are described. The page itself says the collar heights are an approximation and "I can't say this detail will be completely reliable." | high |

## Names that already have a page

Not gaps. Included so a different collector name is not read as a missing guide.

| What the other list calls it | Figure | Variant Villain page |
| --- | --- | --- |
| Stormtrooper Blaster | Stormtrooper, Death Squad Commander, and the same name on Hammerhead, Walrus Man, Imperial Commander, IG-88, Boba Fett, Luke in stormtrooper outfit | https://www.variantvillain.com/accessory-guide/imperial-blaster/ |
| Smuggler Blaster, Han Solo Blaster | Han Solo and others | https://www.variantvillain.com/accessory-guide/rebel-blaster/ The stored file says it is also called a smuggler's blaster, and that Han is the primary figure. |
| Han Bespin Blaster, Blue Bespin blaster | Han Bespin, Lando, Lobot, the Bespin guards, AT-AT Commander | https://www.variantvillain.com/accessory-guide/bespin-blaster/ |
| Laser Rifle, where the page names that figure | Bossk; IG-88; Dengar and the Hoth stormtrooper; Luke Hoth and Rebel Commander; AT-AT Driver | Bossk Rifle, IG-88 Rifle, Imperial Hoth Rifle, Hoth Rebel Rifle, AT-AT Driver Rifle |
| Laser Pistol, black, for A-Wing Pilot and Imperial Gunner; grey or blue-grey for AT-ST Driver, B-Wing Pilot and Leia Endor | those figures | https://www.variantvillain.com/accessory-guide/endor-blaster/ |
| Laser Pistol and Communicator for the Cloud Car Pilot; Black Pilot Blaster for Nien Nunb | those figures | Pilot Blaster and Commlink Guide. The pilot page names the Cloud Car Pilot, the TIE pilot and Nien Nunb. |
| Admiral Staff | Admiral Ackbar | Ackbar Staff |
| Rebel Battle Staff | General Madine | General Madine Staff |
| Walking Stick | The Emperor | Emperor Cane |
| Headhunter Staff | Amanaman | Amanaman Staff |
| Guard Axe | Gamorrean Guard | Gamorrean Axe |
| Medical stick | 2-1B | 2-1B Probe |
| Tool kit box, and Imperial Gunnery's "Ugnaught Tool Box" | Ugnaught | Ugnaught Case. No sentence was found that uses both "tool box" and "case". Both sources are Ugnaught's container, so it is not listed as missing. |
| Apron | Ugnaught | Ugnaught Smock |
| Boushh Rifle, Boushh Helmet, Scout Blaster, Jedi Cloak, vinyl capes, bowcaster, gaderffii stick, telescoping sabres | the matching figures | the page of that name |

C-3PO (Removable Limbs) is the one open name. Rebelscum and Mr Vintage say "Backpack". Variant Villain's page is the Net, and the stored net extract does not say backpack. They were not merged into one row, and the backpack was not added as a proven extra object.

The Vibro Axe page does not, in the stored extract, name the Rancor Keeper, Weequay or Lando's skiff guard. Rebelscum calls the Rancor Keeper's weapon a vibroblade. Mr Vintage calls Weequay's and Lando Skiff's a skiff guard vibro axe. That link is the word "vibro" only, so those three were not added as extra missing weapons and were not marked as covered.
