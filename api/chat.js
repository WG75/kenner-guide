const fs = require("fs");
const path = require("path");

function normalise(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[’‘]/g, "'")
    .replace(/[^a-z0-9\s\-']/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function hasAny(text, terms) {
  return terms.some((term) => text.includes(term));
}

function makeReply(reply, flowState = null, images = []) {
  return {
    reply: String(reply || "").trim(),
    images: Array.isArray(images) ? images : [],
    flowState: flowState || null
  };
}

function optionFromMessage(message) {
  const t = normalise(message);
  if (/^[1-9]$/.test(t)) return t;
  return null;
}

function readFirstExisting(relativePaths) {
  for (const rel of relativePaths) {
    try {
      const filePath = path.join(process.cwd(), rel);
      if (fs.existsSync(filePath)) {
        return fs.readFileSync(filePath, "utf8");
      }
    } catch (err) {
      // If a reference file is missing, keep the deterministic fallback behaviour.
    }
  }

  return "";
}

function lukeReferenceBundle() {
  return {
    figure: readFirstExisting([
      "data/figures/luke-skywalker-reference.txt",
      "main/data/figures/luke-skywalker-reference.txt",
      "data/luke-skywalker-reference.txt",
      "luke-skywalker-reference.txt"
    ]),
    st: readFirstExisting([
      "data/accessories/telescoping-lightsaber.txt",
      "main/data/accessories/telescoping-lightsaber.txt",
      "data/telescoping-lightsaber.txt",
      "telescoping-lightsaber.txt"
    ]),
    dt: readFirstExisting([
      "data/accessories/double-telescoping-lightsaber.txt",
      "main/data/accessories/double-telescoping-lightsaber.txt",
      "data/double-telescoping-lightsaber.txt",
      "double-telescoping-lightsaber.txt"
    ])
  };
}

function jawaIntro() {
  return makeReply(
    `Jawas… filthy traders. Do you need help identifying one of these?

1 Figure
2 Blaster
3 Cloak
4 Guide me`,
    { topic: "jawa", step: "menu" }
  );
}

function jawaCapeQuestion(prefix = "Start with the easiest visible thing.") {
  return makeReply(
    `${prefix}

What does your Jawa have?

1 Vinyl cape - smooth plastic
2 Cloth cloak - fabric
3 No cape or cloak

Reply with a number or describe it in your own words.`,
    { topic: "jawa", step: "cape" }
  );
}

function jawaClothDecision() {
  return makeReply(
    `A cloth cloaked Jawa. Got it.

Would you like to check:

1 Which cloak version you have
2 Whether the cloak looks original
3 Check which Jawa figure variant you have first

Reply with a number or just type your question in your own words.`,
    { topic: "jawa", step: "cloth_decision" }
  );
}

function jawaCooQuestion(prefix = "Next step:") {
  return makeReply(
    `${prefix}
Check the Country of Origin markings on the legs.

1 Hong Kong
2 No Hong Kong / No COO
3 Can't tell

Reply with a number or describe what you can see.`,
    { topic: "jawa", step: "coo" }
  );
}

function jawaHongKongReferences() {
  const images = [
    {
      title: "1. Kader M1",
      url: "/public/images/jawa_figure_kader_M1.png",
      caption: "Kader M1 1a: © aligns with the G of HONG, and the F of G.M.F.G.I. aligns with the G of KONG.\n\nKader M1 1b: © aligns with the O of HONG, and the second G of G.M.F.G.I. aligns with the G of KONG."
    },
    {
      title: "2. Kader M2",
      url: "/public/images/jawa_figure_kader_M2.png",
      caption: "Kader M2 1a: right side of © aligns with the H of HONG, and the 1 of 1977 aligns with the G of KONG.\n\nKader M2 1b: right side of © aligns with the H of HONG, and the middle of the 9 and 7 of 1977 aligns with the G of KONG."
    },
    {
      title: "3. Unitoy M3",
      url: "/public/images/jawa_figure_unitoy_M3.png",
      caption: "Unitoy M3: the first G of G.M.F.G.I. aligns with the H of HONG, and the middle of the 77 from 1977 aligns with the G of KONG."
    },
    {
      title: "4. Unitoy / Lili Ledy M4",
      url: "/public/images/jawa_figure_unitoy_lili-ledy_M4.png",
      caption: "Unitoy / Lili Ledy M4: the M of G.M.F.G.I. aligns with the H of HONG, and the middle of the second 7 from 1977 aligns with the G of KONG."
    }
  ];

  return makeReply(
    `Ok, compare your left-leg marking with these reference images.

Full Jawa guide on Variant Villain:
https://www.variantvillain.com/characters/sw/jawa/

Which is the closest match?

1 Kader M1
2 Kader M2
3 Unitoy M3
4 Unitoy / Lili Ledy M4

Reply with a number or describe the closest one.`,
    { topic: "jawa", step: "hk_variant" },
    images
  );
}

function jawaNoCooResult() {
  const images = [
    {
      title: "Kader China M2 No COO",
      url: "/public/images/jawa_figure_kader_china_M2.png",
      caption: "Kader China M2 No COO: only © G.M.F.G.I. 1977. No HONG KONG marking."
    }
  ];

  return makeReply(
    `That points towards the Kader China M2 No COO Jawa.

It should show:
© G.M.F.G.I. 1977

With no HONG KONG underneath.

Full reference:
https://www.variantvillain.com/characters/sw/jawa/#f2

Do you also want help checking the Jawa blaster?

1 Yes
2 No`,
    { topic: "jawa", step: "offer_blaster" },
    images
  );
}

function jawaUnclearCoo() {
  return makeReply(
    `If you can't see either expected marking, be careful.

For original vintage Jawa figures, the normal left-leg markings are usually:

• © G.M.F.G.I. 1977 with HONG KONG underneath
• or © G.M.F.G.I. 1977 with no HONG KONG underneath

Possible explanations:
• worn or faint markings
• difficult lighting
• bootleg
• reproduction
• Retro Collection
• modern figure

Check under strong light first.

Do you want to continue anyway?

1 Yes, show Hong Kong references
2 No, I'll check again`,
    { topic: "jawa", step: "unclear_coo" }
  );
}

function jawaVariantResult(choice) {
  const map = {
    "1": { name: "Kader M1", url: "https://www.variantvillain.com/characters/sw/jawa/#f1" },
    "2": { name: "Kader M2", url: "https://www.variantvillain.com/characters/sw/jawa/#f2" },
    "3": { name: "Unitoy M3", url: "https://www.variantvillain.com/characters/sw/jawa/#f3" },
    "4": { name: "Unitoy / Lili Ledy M4", url: "https://www.variantvillain.com/characters/sw/jawa/#f3" }
  };

  const result = map[choice] || map["1"];

  return makeReply(
    `Closest match: ${result.name}.

For a more detailed look, visit:
${result.url}

Do you also want help checking the Jawa blaster?

1 Yes
2 No`,
    { topic: "jawa", step: "offer_blaster" }
  );
}

function jawaCloakStart() {
  return makeReply(
    `Ok — let's check the Jawa cloth cloak.

What do you see?

1 Removable hood
2 Attached / sewn hood
3 Not sure

Reply with a number or describe it in your own words.`,
    { topic: "jawa", step: "cloak" }
  );
}

function jawaCloakM5() {
  return makeReply(
    `A removable hood can point towards a Mexican Lili Ledy M5 Jawa cloak.

Known M5 traits:
• heavier cotton material
• lighter colour compared with many other Jawa cloaks
• often a separate small hood
• beige, brown or dark brown stitching

Known small hood versions include:
• brown stitch / removable hood
• beige stitch / removable hood
• brown stitch / attached hood

Be careful though. A damaged hood, replacement hood or reproduction can confuse things.

Reference:
https://www.variantvillain.com/accessory-guide/jawa-cloak/

What would you like to do next?

1 Check whether the cloak looks original
2 Check the Jawa figure variant
3 Check the blaster`,
    { topic: "jawa", step: "cloak_next" }
  );
}

function jawaCloakAttached() {
  return makeReply(
    `An attached hood is more typical, but some Lili Ledy M5 cloaks are also known with attached hoods.

Next compare:
• fabric weight
• colour tone
• stitching colour
• hood shape
• signs of age or modern replacement

Reference:
https://www.variantvillain.com/accessory-guide/jawa-cloak/

What would you like to do next?

1 Check whether the cloak looks original
2 Check the Jawa figure variant
3 Check the blaster`,
    { topic: "jawa", step: "cloak_next" }
  );
}

function jawaCloakAuth() {
  const images = [
    {
      title: "Jawa Cloth Cloak Comparison",
      url: "/public/images/jawa-cloth-cloak-comparison.png",
      caption: "Compare fabric texture, hood shape, cut, stitching and signs of ageing."
    }
  ];

  return makeReply(
    `To check whether the cloak looks original, compare:

• fabric texture
• stitching style and colour
• cut and hood shape
• signs of natural ageing
• whether the hood looks cut, repaired or replaced

Use the reference image above as a starting point.

For expensive examples, don't rely on this app alone. Get confirmation from experienced collector groups as well.

Full cloak guide:
https://www.variantvillain.com/accessory-guide/jawa-cloak/

Do you want to check the figure variant next?

1 Yes
2 No`,
    { topic: "jawa", step: "cloak_auth_next" },
    images
  );
}

function jawaBlasterStart() {
  const images = [
    {
      title: "Jawa Blaster Reference",
      url: "https://www.variantvillain.com/wp-content/uploads/2021/12/JawaBlaster_000.jpg",
      caption: "Compare mould shape, rear bump length, plastic colour and detail sharpness."
    }
  ];

  return makeReply(
    `Ok — compare your blaster with this reference.

First, can you identify it against the reference image?

1 Yes
2 No
3 Not sure`,
    { topic: "jawa_blaster", step: "reference" },
    images
  );
}

function jawaBlasterFloat() {
  return makeReply(
    `Next check: float test.

• If it sinks, treat it as a reproduction
• If it floats, it may be original

Important:
Modern reproductions can float, so this is not proof.

Does yours sink or float?

1 Float
2 Sink`,
    { topic: "jawa_blaster", step: "float" }
  );
}

function jawaBlasterColour() {
  return makeReply(
    `Good. Since it floats, check the colour.

Most original Jawa blasters are dark blue or black-blue tones.

What colour does yours look like?

1 Dark blue / black-blue
2 Black
3 Grey
4 Silver
5 Not sure`,
    { topic: "jawa_blaster", step: "colour" }
  );
}

function jawaBlasterBump(prefix = "Next check: rear bump.") {
  return makeReply(
    `${prefix}

Which does it look closest to?

1 Long rear bump
2 Short rear bump
3 No rear bump
4 Not sure`,
    { topic: "jawa_blaster", step: "bump" }
  );
}

function jawaBlasterBlack() {
  return makeReply(
    `Black needs caution.

It could be:
• a reproduction
• a modern accessory
• a very dark blue original being mistaken for black
• less commonly, a Brazilian Glasslite black blaster

Place it against a strong light. If the edges look blue, it may actually be very dark blue / black-blue.

If it stays black, compare it especially against the M2 mould:
https://www.variantvillain.com/accessory-guide/jawa-blaster/#m2

What do you see?

1 Edges look blue when backlit
2 It stays black
3 Not sure`,
    { topic: "jawa_blaster", step: "black_light" }
  );
}

function jawaBlasterResult(choice) {
  if (choice === "1") {
    return makeReply(
      `That points towards an M1 Jawa blaster.

M1 is associated with a longer rear bump.

Compare carefully here:
https://www.variantvillain.com/accessory-guide/jawa-blaster/

Anything else you want to check?`,
      null
    );
  }

  if (choice === "2") {
    return makeReply(
      `That points towards an M2 Jawa blaster.

M2 has the short rear bump and is also the mould family associated with the Brazilian Glasslite black blaster.

Compare M2 here:
https://www.variantvillain.com/accessory-guide/jawa-blaster/#m2

Anything else you want to check?`,
      null
    );
  }

  if (choice === "3") {
    return makeReply(
      `That points towards an M3 Jawa blaster.

M3 is the no rear bump version.

Compare here:
https://www.variantvillain.com/accessory-guide/jawa-blaster/

Anything else you want to check?`,
      null
    );
  }

  return makeReply(
    `No problem. If the rear bump is hard to judge, compare against the full guide first:

https://www.variantvillain.com/accessory-guide/jawa-blaster/

Look especially at:
• rear bump length
• mould sharpness
• plastic colour
• detail around the handle

Anything else you want to check?`,
    null
  );
}

function lukeSelector() {
  return makeReply(
    `Which Luke are you checking?

1 Luke Skywalker (Original / Tatooine / Farm boy)
2 Luke Skywalker (X-Wing Pilot)
3 Luke Skywalker (Bespin)
4 Luke Skywalker (Hoth)
5 Luke Skywalker (Jedi Knight)
6 Not sure

Reply with a number or describe it in your own words.`,
    { topic: "luke", step: "selector" }
  );
}

function lukeOriginalWeaponQuestion() {
  return makeReply(
    `Luke Skywalker (Original / Tatooine / Farm boy). Got it.

First check the lightsaber.

Does your Luke have a telescoping lightsaber?

1 Yes, it slides out from the arm
2 No, it has a separate lightsaber
3 No weapon
4 Not sure

Reply with a number or describe it.`,
    { topic: "luke", step: "weapon" }
  );
}

function lukeDoubleTelescopingQuestion() {
  return makeReply(
    `That means you may have an early telescoping-saber Luke.

Now check whether it is single or double telescoping.

1 Double telescoping - a thin inner filament slides out
2 Single telescoping - one blade only
3 Not sure

Reply with a number.`,
    { topic: "luke", step: "double_telescoping" }
  );
}

function lukeDoubleTelescopingResult(choice) {
  if (choice === "1") {
    return makeReply(
      `Double telescoping Luke is the key early Luke feature.

Important:
• DT sabers belong only with the earliest Luke figures
• complete DT sabers are rare
• they are fragile and heavily faked
• many examples are broken, cut down or reproduction pieces

Do not rely on this app alone for authentication. Compare with expert references and experienced collector groups.

Now let's identify the figure itself.`,
      { topic: "luke", step: "hair" }
    );
  }

  if (choice === "2") {
    return makeReply(
      `Single telescoping noted.

That is the standard later telescoping style after Kenner moved away from the fragile double telescoping design.

Now let's identify the figure itself.`,
      { topic: "luke", step: "hair" }
    );
  }

  return makeReply(
    `No problem. If you are unsure whether it is DT or ST, treat it cautiously.

A DT saber has a second thin inner filament that extends from the main blade. ST has only one extending blade.

Now let's identify the figure itself.`,
    { topic: "luke", step: "hair" }
  );
}

function lukeHairQuestion(prefix = "Next check the figure itself.") {
  return makeReply(
    `${prefix}

Check the hair colour.

1 Blonde / yellow hair
2 Brown / darker hair
3 Orange / ginger hair
4 Not sure

Reply with a number or describe it.`,
    { topic: "luke", step: "hair" }
  );
}

function lukeCooQuestion() {
  return makeReply(
    `Next check the Country of Origin marking.

Luke Skywalker can appear with several COO types.

What do you see?

1 No COO
2 Hong Kong
3 Taiwan
4 Not sure

Reply with a number or describe what you can see.`,
    { topic: "luke", step: "coo" }
  );
}

function lukeLegColourQuestion() {
  return makeReply(
    `Now check the plastic colour on the legs / trousers.

1 White / cream
2 Yellowed / aged
3 Not sure

Reply with a number.`,
    { topic: "luke", step: "legs" }
  );
}

function lukeOriginalResult() {
  return makeReply(
    `That gives you a useful starting point for Luke Skywalker (Original / Tatooine / Farm boy).

Use this as a guide, not final authentication. Luke variants depend on several details together:

• hair colour
• COO marking
• plastic tone
• face and body mould details
• lightsaber type
• correct figure and saber pairing

Important pairing note:
DT sabers should only be paired with the earliest Luke figures. ST sabers are correct for most later Luke figures.

Full Luke guide:
https://www.variantvillain.com/characters/sw/luke-skywalker/

Do you want help checking the lightsaber?

1 Yes
2 No`,
    { topic: "luke", step: "offer_lightsaber" }
  );
}

function lukeLightsaberStart() {
  return makeReply(
    `Which Luke lightsaber type do you have?

1 Telescoping from the arm
2 Separate yellow lightsaber
3 No lightsaber
4 Not sure

Reply with a number or describe it.`,
    { topic: "luke_lightsaber", step: "type" }
  );
}

function lukeLightsaberFloat() {
  return makeReply(
    `For a separate Luke lightsaber, start with the float test.

Does it float?

1 Yes
2 No
3 Not tested

Reply with a number.`,
    { topic: "luke_lightsaber", step: "float" }
  );
}

function lukeLightsaberColour() {
  return makeReply(
    `What colour is the lightsaber?

1 Bright yellow
2 Pale yellow
3 Darker yellow / orange-yellow
4 Other / not sure

Reply with a number or describe it.`,
    { topic: "luke_lightsaber", step: "colour" }
  );
}

function lukeLightsaberResult() {
  return makeReply(
    `Good starting checks.

For Luke lightsabers, compare:

• whether it is DT, ST or separate
• colour tone
• tip shape
• blade thickness
• mould detail
• signs of trimming, repair or reproduction
• whether it is correct for the figure version

ST sabers are common and correct for most post-DT Luke figures.
DT sabers are early, rare and heavily faked.

Relevant reference:
https://www.variantvillain.com/accessory-guide/luke-lightsaber/

Anything else you want to check?`,
    null
  );
}

function lukeNotSurePrompt() {
  return makeReply(
    `No problem. Describe the Luke figure as best you can.

Useful details:

1 Outfit
2 Hair colour
3 Weapon / lightsaber type
4 COO marking on the leg
5 Any helmet, jacket or robe

Later, a Google Lens-style photo recognition feature would be ideal for this. For now, describe what you can see and I’ll guide you.`,
    null
  );
}

function lukeReferenceQuestion(message) {
  const t = normalise(message);

  if (hasAny(t, ["double telescoping", "dt saber", "dt lightsaber", "inner filament"])) {
    return makeReply(
      `Double telescoping sabers are the earliest and rarest Kenner lightsaber type.

Key points:
• two-stage blade
• inner filament extends from the main blade
• found only with the earliest Luke, Vader and Obi-Wan figures
• fragile, often broken or missing the inner filament
• frequently faked or cut down

For Luke, a DT saber should only be paired with the earliest figures.

Do you want to check a Luke figure now?

1 Yes
2 No`,
      { topic: "luke", step: "reference_offer_figure" }
    );
  }

  if (hasAny(t, ["single telescoping", "st saber", "st lightsaber"])) {
    return makeReply(
      `Single telescoping sabers replaced the earlier DT design.

Key points:
• one-piece extending blade
• no inner filament
• more durable than DT
• correct for most later production Luke figures

Do you want to check a Luke figure now?

1 Yes
2 No`,
      { topic: "luke", step: "reference_offer_figure" }
    );
  }

  if (hasAny(t, ["early bird", "mailer"])) {
    return makeReply(
      `Luke Skywalker was included in the Early Bird Certificate Package.

Key points:
• shipped in early 1978
• plain white mailer
• one of the first four Kenner figures
• earliest Luke examples may be associated with double telescoping saber versions

Do you want to check whether your Luke could be an early version?

1 Yes
2 No`,
      { topic: "luke", step: "reference_offer_figure" }
    );
  }

  return null;
}

function genericBlasterClarify() {
  return makeReply(
    `I found several vintage Kenner blaster types.

Which one are you asking about?

1 Imperial / Stormtrooper blaster
2 Jawa blaster
3 Princess Leia blaster
4 Rebel / Han Solo blaster
5 Guide me`,
    { topic: "blaster", step: "menu" }
  );
}

function offTopic() {
  return makeReply(
    `Sorry, I’m not familiar with that subject.

I’m a Collector Companion droid focused on vintage Star Wars toys from 1977 to 1985, mostly the figures and accessories.

If you meant something vintage Star Wars related, please clarify and I’ll help.

Do you have any vintage Star Wars questions I can help with?`,
    null
  );
}

function routeInitial(message) {
  const t = normalise(message);

  const isJawa = t.includes("jawa");
  const isLuke = t.includes("luke") || t.includes("skywalker");
  const isBlaster = hasAny(t, ["blaster", "gun", "weapon", "pistol", "pew"]);
  const isLightsaber = hasAny(t, ["lightsaber", "light saber", "saber", "sabre", "telescoping", "dt saber", "st saber"]);
  const isCloak = hasAny(t, ["cloak", "cape", "hood"]);
  const isFigure = hasAny(t, ["figure", "variant", "coo", "country of origin", "identify", "id"]);

  const lukeReferenceReply = lukeReferenceQuestion(message);
  if (isLuke && lukeReferenceReply) return lukeReferenceReply;

  if (isJawa && isBlaster) return jawaBlasterStart();
  if (isJawa && isCloak) return jawaCloakStart();
  if (isJawa && isFigure) return jawaCapeQuestion("Let's identify your Jawa figure.");
  if (isJawa) return jawaIntro();

  if (isLuke && isLightsaber) return lukeLightsaberStart();
  if (isLuke) return lukeSelector();

  if (isBlaster) return genericBlasterClarify();

  if (hasAny(t, ["star wars", "kenner", "vintage", "coo", "variant", "accessory", "figure"])) {
    return makeReply(
      `I can help with vintage Kenner Star Wars figures and accessories.

What would you like to identify?

1 Jawa
2 Luke Skywalker
3 Blaster
4 COO marking
5 Guide me`,
      { topic: "general", step: "menu" }
    );
  }

  return offTopic();
}

function continueGeneral(message, flowState) {
  const t = normalise(message);
  const opt = optionFromMessage(t);

  if (flowState.step === "menu") {
    if (opt === "1" || t.includes("jawa")) return jawaIntro();
    if (opt === "2" || t.includes("luke") || t.includes("skywalker")) return lukeSelector();
    if (opt === "3" || hasAny(t, ["blaster", "gun", "weapon"])) return genericBlasterClarify();
    if (opt === "4" || t.includes("coo")) {
      return makeReply(
        `COO means Country of Origin.

For vintage Kenner figures, COO markings help identify the mould family, factory origin and variant.

They are useful, but not enough on their own. You also need to check sculpt, paint, plastic colour and accessory match.

Do you want to check a Jawa COO?

1 Yes
2 No`,
        { topic: "general", step: "coo_offer" }
      );
    }
    if (opt === "5" || t.includes("guide")) return jawaIntro();
  }

  if (flowState.step === "coo_offer") {
    if (opt === "1" || t.includes("yes")) return jawaCooQuestion("Ok.");
    return makeReply("No problem. Ask me about a figure or accessory when you're ready.", null);
  }

  return routeInitial(message);
}

function continueGenericBlaster(message, flowState) {
  const t = normalise(message);
  const opt = optionFromMessage(t);

  if (flowState.step === "menu") {
    if (opt === "2" || t.includes("jawa")) return jawaBlasterStart();

    if (opt === "1" || t.includes("imperial") || t.includes("stormtrooper")) {
      return makeReply(
        `Imperial / Stormtrooper blaster. I don't have the full guided flow for that one yet, but it's on the demo list.

For now, describe the colour, mould detail and whether it floats.`,
        null
      );
    }

    if (opt === "3" || t.includes("leia")) {
      return makeReply(
        `Princess Leia blaster. I don't have the full guided flow for that one yet.

For now, describe the colour, shape and whether it floats.`,
        null
      );
    }

    if (opt === "4" || t.includes("rebel") || t.includes("han")) {
      return makeReply(
        `Rebel / Han Solo blaster. I don't have the full guided flow for that one yet.

For now, describe the colour, size and mould detail.`,
        null
      );
    }

    if (opt === "5" || t.includes("guide")) {
      return makeReply(
        `No problem. Describe the blaster.

Useful details:
• colour
• size
• long or short barrel
• whether it floats
• which figure it came with, if known`,
        null
      );
    }
  }

  return genericBlasterClarify();
}

function continueJawa(message, flowState) {
  const t = normalise(message);
  const opt = optionFromMessage(t);

  if (flowState.step === "menu") {
    if (opt === "1" || t.includes("figure")) return jawaCapeQuestion("Let's identify the figure first.");
    if (opt === "2" || hasAny(t, ["blaster", "gun", "weapon", "pistol", "pew"])) return jawaBlasterStart();
    if (opt === "3" || hasAny(t, ["cloak", "cape", "hood"])) return jawaCloakStart();
    if (opt === "4" || t.includes("guide")) return jawaCapeQuestion("No problem. Start with the easiest visible thing.");
    return jawaIntro();
  }

  if (flowState.step === "cape") {
    if (opt === "1" || hasAny(t, ["vinyl", "plastic"])) {
      return makeReply(
        `Vinyl cape Jawa. Treat this as potential, not confirmed.

Original vinyl cape Jawas are valuable, so there are many fakes and cut-down Ben Kenobi capes.

Reference:
https://www.variantvillain.com/accessory-guide/jawa-vinyl-cape/

Let's identify the figure itself next.

Reply with any key to continue.`,
        { topic: "jawa", step: "vinyl_then_coo" }
      );
    }

    if (opt === "2" || hasAny(t, ["cloth", "fabric", "cloak"])) return jawaClothDecision();

    if (opt === "3" || hasAny(t, ["none", "naked", "missing", "no cape", "no cloak"])) {
      return jawaCooQuestion("Right — naked Jawa. Let's identify the figure itself.");
    }

    return jawaCapeQuestion("I’m not sure which cape option that matches.");
  }

  if (flowState.step === "vinyl_then_coo") return jawaCooQuestion("Next step:");

  if (flowState.step === "cloth_decision") {
    if (opt === "1" || hasAny(t, ["version", "which cloak", "type"])) return jawaCloakStart();
    if (opt === "2" || hasAny(t, ["original", "real", "authentic", "repro"])) return jawaCloakAuth();
    if (opt === "3" || hasAny(t, ["figure", "variant", "coo"])) return jawaCooQuestion("Ok. Let's identify the figure first.");
    if (hasAny(t, ["removable", "separate hood"])) return jawaCloakM5();
    if (hasAny(t, ["attached", "sewn"])) return jawaCloakAttached();
    return jawaClothDecision();
  }

  if (flowState.step === "coo") {
    if (opt === "1" || hasAny(t, ["hong kong", "hk"])) return jawaHongKongReferences();
    if (opt === "2" || hasAny(t, ["no coo", "no hong kong", "not hong kong", "just copyright", "gmfgi"])) return jawaNoCooResult();
    if (opt === "3" || hasAny(t, ["can't tell", "cant tell", "not sure", "unsure"])) return jawaUnclearCoo();
    return jawaCooQuestion("I’m not sure which COO option that matches.");
  }

  if (flowState.step === "unclear_coo") {
    if (opt === "1" || t.includes("yes")) return jawaHongKongReferences();
    return makeReply("No problem. Check under strong light and ask me again when ready.", null);
  }

  if (flowState.step === "hk_variant") {
    if (["1", "2", "3", "4"].includes(opt)) return jawaVariantResult(opt);
    if (t.includes("m1")) return jawaVariantResult("1");
    if (t.includes("m2")) return jawaVariantResult("2");
    if (t.includes("m3")) return jawaVariantResult("3");
    if (t.includes("m4") || t.includes("lili") || t.includes("unitoy")) return jawaVariantResult("4");
    return jawaHongKongReferences();
  }

  if (flowState.step === "offer_blaster") {
    if (opt === "1" || t.includes("yes")) return jawaBlasterStart();
    if (opt === "2" || t.includes("no")) return makeReply("No problem. Anything else you want to check?", null);
    return makeReply("Do you want help checking the Jawa blaster?\n\n1 Yes\n2 No", { topic: "jawa", step: "offer_blaster" });
  }

  if (flowState.step === "cloak") {
    if (opt === "1" || hasAny(t, ["removable", "separate"])) return jawaCloakM5();
    if (opt === "2" || hasAny(t, ["attached", "sewn"])) return jawaCloakAttached();
    if (opt === "3" || hasAny(t, ["not sure", "unsure"])) {
      return makeReply(
        `No problem. Compare the cloak visually first:

https://www.variantvillain.com/accessory-guide/jawa-cloak/

Look at:
• hood shape
• material weight
• stitching colour
• whether the hood is separate or sewn

Do you want to check the figure variant instead?

1 Yes
2 No`,
        { topic: "jawa", step: "cloak_auth_next" }
      );
    }
    return jawaCloakStart();
  }

  if (flowState.step === "cloak_next") {
    if (opt === "1" || hasAny(t, ["original", "authentic", "real"])) return jawaCloakAuth();
    if (opt === "2" || hasAny(t, ["figure", "variant", "coo"])) return jawaCooQuestion("Ok. Let's check the figure itself.");
    if (opt === "3" || hasAny(t, ["blaster", "weapon", "gun"])) return jawaBlasterStart();
    return jawaCloakM5();
  }

  if (flowState.step === "cloak_auth_next") {
    if (opt === "1" || t.includes("yes")) return jawaCooQuestion("Ok. Let's check the figure itself.");
    return makeReply("No problem. Anything else you want to check?", null);
  }

  return routeInitial(message);
}

function continueJawaBlaster(message, flowState) {
  const t = normalise(message);
  const opt = optionFromMessage(t);

  if (flowState.step === "reference") {
    if (["1", "2", "3"].includes(opt) || hasAny(t, ["yes", "no", "not sure", "unsure"])) return jawaBlasterFloat();
    return jawaBlasterStart();
  }

  if (flowState.step === "float") {
    if (opt === "1" || t.includes("float")) return jawaBlasterColour();
    if (opt === "2" || t.includes("sink")) {
      return makeReply(
        `If it sinks, treat it as a reproduction.

Original vintage Jawa blasters should float, although floating alone does not prove originality.

Full reference:
https://www.variantvillain.com/accessory-guide/jawa-blaster/

Anything else you want to check?`,
        null
      );
    }
    return jawaBlasterFloat();
  }

  if (flowState.step === "colour") {
    if (opt === "1" || hasAny(t, ["dark blue", "blue", "black blue", "black-blue"])) {
      return jawaBlasterBump("That is the safest colour range for most original Jawa blasters. Next check: rear bump.");
    }
    if (opt === "2" || t.includes("black")) return jawaBlasterBlack();
    if (opt === "3" || hasAny(t, ["grey", "gray"])) {
      return makeReply(
        `Grey needs extra caution.

Grey is a very common reproduction colour for Jawa blasters.

There are rare silver Glasslite versions, but they are extremely uncommon and should not be assumed.

Compare:
https://www.variantvillain.com/accessory-guide/jawa-blaster/

Anything else you want to check?`,
        null
      );
    }
    if (opt === "4" || t.includes("silver")) {
      return makeReply(
        `Silver is unusual.

There is a rare silver Jawa blaster associated with Brazilian Glasslite production, but it is extremely uncommon.

Do not assume it is Glasslite without matching the mould and provenance carefully.

Reference:
https://www.variantvillain.com/accessory-guide/jawa-blaster/

Anything else you want to check?`,
        null
      );
    }
    return jawaBlasterBump("No problem. Colour can be hard to judge. Next check: rear bump.");
  }

  if (flowState.step === "black_light") {
    if (opt === "1" || hasAny(t, ["blue", "edges blue", "looks blue"])) {
      return jawaBlasterBump("That may actually be very dark blue / black-blue rather than true black. Next check: rear bump.");
    }

    if (opt === "2" || hasAny(t, ["stays black", "still black", "no blue"])) {
      return makeReply(
        `If it stays black under strong light, compare it especially against the M2 mould.

A legitimate black Jawa blaster is most likely the Brazilian Glasslite version, which belongs to the M2 mould family.

M2 reference:
https://www.variantvillain.com/accessory-guide/jawa-blaster/#m2

Next check: rear bump.

1 Long
2 Short
3 None
4 Not sure`,
        { topic: "jawa_blaster", step: "bump" }
      );
    }

    return jawaBlasterBump("No problem. If the light test is unclear, use the rear bump next.");
  }

  if (flowState.step === "bump") {
    if (opt === "1" || t.includes("long")) return jawaBlasterResult("1");
    if (opt === "2" || hasAny(t, ["short", "medium"])) return jawaBlasterResult("2");
    if (opt === "3" || hasAny(t, ["none", "no bump", "missing bump"])) return jawaBlasterResult("3");
    return jawaBlasterResult("4");
  }

  return jawaBlasterStart();
}

function continueLuke(message, flowState) {
  const t = normalise(message);
  const opt = optionFromMessage(t);

  if (flowState.step === "selector") {
    if (opt === "1" || hasAny(t, ["original", "tatooine", "farm", "farmboy", "farm boy"])) return lukeOriginalWeaponQuestion();

    if (opt === "2" || t.includes("x wing") || t.includes("x-wing")) {
      return makeReply(`Luke Skywalker (X-Wing Pilot) is not fully built into this demo yet.

For now, describe the figure, helmet, COO and accessory and I’ll help as best I can.`, null);
    }

    if (opt === "3" || t.includes("bespin")) {
      return makeReply(`Luke Skywalker (Bespin) is not fully built into this demo yet.

For now, describe the clothing, hair colour, COO and saber and I’ll help as best I can.`, null);
    }

    if (opt === "4" || t.includes("hoth")) {
      return makeReply(`Luke Skywalker (Hoth) is not fully built into this demo yet.

For now, describe the outfit, accessories and markings and I’ll help as best I can.`, null);
    }

    if (opt === "5" || t.includes("jedi")) {
      return makeReply(`Luke Skywalker (Jedi Knight) is not fully built into this demo yet.

For now, describe the cloak, saber, body colour and markings and I’ll help as best I can.`, null);
    }

    if (opt === "6" || hasAny(t, ["not sure", "unsure", "don't know", "dont know", "guide"])) return lukeNotSurePrompt();

    return lukeSelector();
  }

  if (flowState.step === "weapon") {
    if (opt === "1" || hasAny(t, ["telescoping", "slides", "slides out", "arm"])) return lukeDoubleTelescopingQuestion();
    if (opt === "2" || hasAny(t, ["separate", "loose", "yellow saber", "yellow lightsaber"])) return lukeHairQuestion();
    if (opt === "3" || hasAny(t, ["no weapon", "missing", "none"])) return lukeHairQuestion("No weapon. No problem. Let's identify the figure itself.");
    if (opt === "4" || hasAny(t, ["not sure", "unsure", "don't know", "dont know"])) return lukeHairQuestion("No problem. Let's identify the figure itself first.");
    return lukeOriginalWeaponQuestion();
  }

  if (flowState.step === "double_telescoping") {
    if (opt === "1") return lukeDoubleTelescopingResult("1");
    if (opt === "2") return lukeDoubleTelescopingResult("2");
    return lukeDoubleTelescopingResult("3");
  }

  if (flowState.step === "hair") {
    if (["1", "2", "3", "4"].includes(opt) || hasAny(t, ["blonde", "yellow", "brown", "dark", "orange", "ginger", "not sure", "unsure"])) return lukeCooQuestion();
    return lukeHairQuestion("I’m not sure which hair colour that matches.");
  }

  if (flowState.step === "coo") {
    if (["1", "2", "3", "4"].includes(opt) || hasAny(t, ["no coo", "hong kong", "taiwan", "not sure", "unsure"])) return lukeLegColourQuestion();
    return lukeCooQuestion();
  }

  if (flowState.step === "legs") {
    if (["1", "2", "3"].includes(opt) || hasAny(t, ["white", "cream", "yellow", "yellowed", "aged", "not sure", "unsure"])) return lukeOriginalResult();
    return lukeLegColourQuestion();
  }

  if (flowState.step === "offer_lightsaber") {
    if (opt === "1" || t.includes("yes")) return lukeLightsaberStart();
    if (opt === "2" || t.includes("no")) return makeReply("No problem. Anything else you want to check?", null);
    return makeReply("Do you want help checking the lightsaber?\n\n1 Yes\n2 No", { topic: "luke", step: "offer_lightsaber" });
  }

  if (flowState.step === "reference_offer_figure") {
    if (opt === "1" || t.includes("yes")) return lukeOriginalWeaponQuestion();
    return makeReply("No problem. Ask me again if you want to check a Luke figure or lightsaber.", null);
  }

  return lukeSelector();
}

function continueLukeLightsaber(message, flowState) {
  const t = normalise(message);
  const opt = optionFromMessage(t);

  if (flowState.step === "type") {
    if (opt === "1" || hasAny(t, ["telescoping", "slides", "arm"])) return lukeDoubleTelescopingQuestion();
    if (opt === "2" || hasAny(t, ["separate", "loose", "yellow"])) return lukeLightsaberFloat();
    if (opt === "3" || hasAny(t, ["none", "missing", "no lightsaber"])) return makeReply("No problem. If you find the lightsaber later, ask me to check it.", null);
    return lukeLightsaberFloat();
  }

  if (flowState.step === "double_telescoping") {
    if (opt === "1") return lukeDoubleTelescopingResult("1");
    if (opt === "2") return lukeDoubleTelescopingResult("2");
    return lukeDoubleTelescopingResult("3");
  }

  if (flowState.step === "float") {
    if (["1", "2", "3"].includes(opt) || hasAny(t, ["float", "sink", "not tested"])) return lukeLightsaberColour();
    return lukeLightsaberFloat();
  }

  if (flowState.step === "colour") {
    if (["1", "2", "3", "4"].includes(opt) || hasAny(t, ["yellow", "orange", "pale", "bright", "not sure"])) return lukeLightsaberResult();
    return lukeLightsaberColour();
  }

  return lukeLightsaberStart();
}

function continueFlow(message, flowState) {
  if (!flowState || !flowState.topic) return routeInitial(message);

  if (flowState.topic === "jawa") return continueJawa(message, flowState);
  if (flowState.topic === "jawa_blaster") return continueJawaBlaster(message, flowState);
  if (flowState.topic === "luke") return continueLuke(message, flowState);
  if (flowState.topic === "luke_lightsaber") return continueLukeLightsaber(message, flowState);
  if (flowState.topic === "blaster") return continueGenericBlaster(message, flowState);
  if (flowState.topic === "general") return continueGeneral(message, flowState);

  return routeInitial(message);
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  try {
    const message = String(req.body?.message || "").trim();
    const flowState = req.body?.flowState || null;

    if (!message) {
      res.status(400).json({ error: "Missing message" });
      return;
    }

    const result = continueFlow(message, flowState);

    res.status(200).json({
      reply: result.reply,
      images: result.images || [],
      flowState: result.flowState || null
    });
  } catch (err) {
    console.error(err);
    const fallback = makeReply(
      `Sorry, something went wrong inside my collector circuits.

Try again with a simple phrase like:
• Jawa
• Luke
• Luke lightsaber
• Jawa blaster
• Jawa cloak`,
      null
    );

    res.status(200).json({
      reply: fallback.reply,
      images: [],
      flowState: null
    });
  }
};
