import fs from "fs";
import path from "path";
import { selectVvReferencePhotos } from "./vv-reference-photos.js";
import { PHOTO_HELPER } from "./kenner-debut.js";

const MATCH_FILE = path.join(process.cwd(), "data", "factory-match.json");
const QUESTION_BUTTON = "Do you have a question about this accessory?";
const HIDDEN = new Set(["date", "cardback", "assembly"]);
const BRIEF_CAP = 6000;

let matchCache = null;
let fileCache = null;

function loadMatch() {
  if (matchCache) return matchCache;
  matchCache = JSON.parse(fs.readFileSync(MATCH_FILE, "utf8"));
  return matchCache;
}

function norm(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function slug(value) {
  return norm(value).replace(/ /g, "_");
}

function accessoryNames() {
  return [...new Set((loadMatch().accessoryVariants || []).map(item => item.accessory).filter(Boolean))];
}

function variantsOf(accessory) {
  return (loadMatch().accessoryVariants || []).filter(item => item.accessory === accessory);
}

function accessoryFile(name) {
  if (!fileCache) {
    fileCache = new Map();
    const dir = path.join(process.cwd(), "data");
    for (const file of fs.readdirSync(dir)) {
      if (!/^catalog.*\.json$/.test(file)) continue;
      const parsed = JSON.parse(fs.readFileSync(path.join(dir, file), "utf8"));
      for (const item of parsed.accessories || []) {
        if (item && item.name && item.file) fileCache.set(norm(item.name), item.file);
      }
    }
  }
  return fileCache.get(norm(name)) || "";
}

/* A typed name that already contains one stored accessory ("Rebel Blaster (DL-44)")
   resolves. A general word ("blaster") stays open so the photo can choose. */
export function resolveAccessoryName(displayName) {
  const want = norm(displayName);
  const names = accessoryNames();
  if (!want) return { accessory: "", candidates: [] };
  const exact = names.find(item => norm(item) === want);
  if (exact) return { accessory: exact, candidates: [exact] };
  const named = names.filter(item => {
    const label = norm(item);
    return label.length > 3 && want.includes(label);
  });
  if (named.length === 1) return { accessory: named[0], candidates: named };
  const contained = names.filter(item => norm(item).includes(want));
  if (contained.length === 1) return { accessory: contained[0], candidates: contained };
  return { accessory: "", candidates: contained.slice(0, 16) };
}

function hasShape(variants) {
  return variants.some(variant => (variant.tells || []).some(tell => tell.category !== "plastic"));
}

export function mouldBrief(accessory) {
  const variants = variantsOf(accessory);
  const lines = [
    `Accessory: ${accessory}`,
    "Match the sculpt in the photo (barrel, scope, grip, bump, proportions) and the comparison photos. Colour is a secondary cue, not enough on its own."
  ];
  for (const variant of variants) {
    const tells = variant.tells || [];
    const shape = tells.filter(tell => tell.category !== "plastic" && !HIDDEN.has(tell.category)).map(tell => tell.detail);
    const hidden = tells.filter(tell => HIDDEN.has(tell.category)).map(tell => tell.detail);
    const colours = tells.filter(tell => tell.category === "plastic").map(tell => tell.detail).slice(0, 6);
    const bits = [`${variant.id} | ${variant.factory} ${variant.mould}`];
    if (shape.length) bits.push(`sculpt: ${shape.join("; ")}`);
    if (hidden.length) bits.push(`not in a loose photo: ${hidden.join("; ")}`);
    if (colours.length) bits.push(`colour (secondary): ${colours.join("; ")}`);
    lines.push(bits.join(" | "));
  }
  let text = lines.join("\n");
  if (text.length > BRIEF_CAP) text = text.slice(0, BRIEF_CAP);
  return { text, variants };
}

/* Comparison photos count as a sculpt cue. Colour records alone do not. */
export function decideMoulds({ ids, variants, photosAttached }) {
  const allowed = new Map((variants || []).map(variant => [variant.id, variant]));
  const picked = [];
  for (const id of Array.isArray(ids) ? ids : []) {
    const variant = allowed.get(String(id || "").trim());
    if (variant && !picked.includes(variant)) picked.push(variant);
  }
  if (!photosAttached && !hasShape(variants || [])) return [];
  return picked;
}

function theList(labels) {
  const items = labels.filter(Boolean);
  if (items.length <= 1) return items[0] || "";
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(", ")}, and ${items[items.length - 1]}`;
}

function cardedSentence(variant) {
  const names = [];
  for (const id of variant.cardedWith || []) {
    const fig = (loadMatch().figureVariants || []).find(item => item.id === id);
    if (fig && fig.figure && !names.includes(fig.figure)) names.push(fig.figure);
  }
  if (!names.length) return "";
  return `It was carded with ${theList(names)}.`;
}

function hiddenAsk(variants) {
  if (!variants || variants.length < 2) return null;
  let best = null;
  for (const category of ["cardback", "date", "assembly"]) {
    const groups = new Map();
    for (const variant of variants) {
      const details = (variant.tells || []).filter(tell => tell.category === category).map(tell => tell.detail).sort();
      const key = details.join("|") || "(none)";
      if (!groups.has(key)) groups.set(key, true);
    }
    if (groups.size < 2) continue;
    const sample = variants.flatMap(variant => variant.tells || []).find(tell =>
      tell.category === category && tell.where && !/plastic colour/i.test(tell.where)
    );
    if (!best) best = { category, where: sample && sample.where };
  }
  if (!best) return null;
  const buttons = [];
  for (const variant of variants) {
    for (const tell of variant.tells || []) {
      if (tell.category !== best.category) continue;
      const label = tell.detail.length > 110 ? `${tell.detail.slice(0, 107).trim()}...` : tell.detail;
      if (!buttons.some(item => norm(item) === norm(label))) buttons.push(label);
    }
  }
  if (!buttons.length) return null;
  buttons.push("I'm not sure");
  return {
    category: best.category,
    reply: best.where || "One stored detail is not in the photo. Which of these applies?",
    actions: buttons.map(label => ({ label, value: label }))
  };
}

function parseModelJson(raw) {
  const text = String(raw || "").replace(/```json|```/g, "").trim();
  try {
    return JSON.parse(text);
  } catch (err) {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start >= 0 && end > start) {
      try {
        return JSON.parse(text.slice(start, end + 1));
      } catch (inner) {
        return null;
      }
    }
    return null;
  }
}

async function vision(system, text, imageParts) {
  try {
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: system },
          {
            role: "user",
            content: [
              { type: "text", text },
              ...imageParts
            ]
          }
        ],
        max_tokens: 400
      })
    });
    if (!response || !response.ok) return "";
    const data = await response.json();
    return data?.choices?.[0]?.message?.content || "";
  } catch (err) {
    return "";
  }
}

function userPhoto(image) {
  return [{ type: "image_url", image_url: { url: image } }];
}

function namedReply(name, picked) {
  const labels = picked.map(variant => `the ${variant.factory} ${variant.mould}`);
  if (!picked.length) {
    return `The accessory in your photo appears to be ${name}. I can't tell the mould from this photo.`;
  }
  if (picked.length === 1) {
    const variant = picked[0];
    const carded = cardedSentence(variant);
    return [
      `The accessory in your photo appears to be ${name}. That is the ${variant.factory} ${variant.mould} ${name}.`,
      carded
    ].filter(Boolean).join(" ");
  }
  return `The accessory in your photo appears to be ${name}. The photo matches ${theList(labels)}.`;
}

function baseFlow(name, figureKey) {
  return {
    topic: "image_identified",
    itemKind: "accessory",
    figure: slug(name) || figureKey || "accessory",
    displayName: name,
    pronoun: "it",
    possessive: "its",
    accessories: [],
    visibleAccessories: [],
    costumeCues: [],
    step: "post_identification"
  };
}

export async function replyToAccessoryPhoto({ image, displayName, figureKey }) {
  const shown = String(displayName || "").trim() || "an unidentified accessory";
  let { accessory, candidates } = resolveAccessoryName(shown);
  if (!accessory && candidates.length > 1) {
    const raw = await vision(
      `The photo is a loose vintage Kenner accessory. Choose the one stored name it shows. Reply with JSON only: {"accessory":"Name"} using a name from the list, or {"accessory":""} when the photo does not show which one. Do not choose a mould. Do not mention colour.`,
      `Stored accessory names:\n${candidates.map(name => `- ${name}`).join("\n")}`,
      userPhoto(image)
    );
    const parsed = parseModelJson(raw);
    const chosen = norm(parsed && parsed.accessory);
    const match = candidates.find(name => norm(name) === chosen);
    if (match) accessory = match;
  }

  const name = accessory || shown;
  const photos = accessory
    ? selectVvReferencePhotos({ question: accessory, sources: [accessoryFile(accessory)].filter(Boolean) })
    : [];
  const brief = accessory ? mouldBrief(accessory) : { text: "", variants: [] };
  const canCompare = photos.length > 0 || hasShape(brief.variants);
  let picked = [];
  if (accessory && canCompare) {
    const raw = await vision(
      `You match a photo of one loose accessory to stored moulds. Use the sculpt and the comparison photos. Colour is a secondary cue. Do not choose a mould from colour alone. If colour is the only difference you can see, return an empty mould_ids list. Copy ids exactly from the list. Return JSON only: {"mould_ids":["id"]}. One id when one mould fits. Several when more than one still fits. [] when the sculpt is not clear. Do not say what it is not.`,
      `${brief.text}\n\nThe first picture is the collector's photo. Any pictures after it are the stored comparison photos.`,
      [
        ...userPhoto(image),
        ...photos.map(photo => ({ type: "image_url", image_url: { url: photo.url } }))
      ]
    );
    const parsed = parseModelJson(raw);
    picked = decideMoulds({
      ids: parsed && parsed.mould_ids,
      variants: brief.variants,
      photosAttached: photos.length > 0
    });
  }

  const ask = hiddenAsk(picked);
  const reply = [namedReply(name, picked), ask ? ask.reply : ""].filter(Boolean).join("\n\n");
  if (ask) {
    return {
      reply,
      flowState: {
        topic: "accessory_factory",
        step: "tell",
        accessory: name,
        variantIds: picked.map(variant => variant.id),
        figure: "",
        factory: "",
        figureVariantIds: [],
        usedTells: [ask.category],
        photoTells: [],
        photoMould: true,
        lead: ""
      },
      actions: ask.actions,
      quickReplies: true,
      helper: PHOTO_HELPER,
      ...(photos.length ? { images: photos } : {})
    };
  }
  return {
    reply,
    flowState: baseFlow(name, figureKey),
    actions: [{ label: QUESTION_BUTTON, value: "ask-about-accessory" }],
    quickReplies: true,
    helper: PHOTO_HELPER,
    ...(photos.length ? { images: photos } : {})
  };
}
