import fs from "fs";
import path from "path";

export const PHOTO_HELPER = "Or ask me anything, or upload another photo to identify.";

const QUESTION_BUTTON = "Do you have a question about this figure?";
const ACCESSORY_QUESTION_BUTTON = "Do you have a question about this accessory?";

let cache = null;

function loadFigures() {
  if (cache) return cache;
  const file = path.join(process.cwd(), "data", "kenner-debut-figures.json");
  const parsed = JSON.parse(fs.readFileSync(file, "utf8"));
  cache = Array.isArray(parsed.figures) ? parsed.figures : [];
  return cache;
}

function norm(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

export function findDebutFigure(displayName) {
  const want = norm(displayName);
  if (!want) return null;
  const figures = loadFigures();
  const exact = figures.filter(fig =>
    [fig.name, ...(fig.aliases || [])].some(label => norm(label) === want)
  );
  if (exact.length === 1) return exact[0];
  if (exact.length > 1) {
    const named = exact.filter(fig => norm(fig.name) === want);
    return named.length === 1 ? named[0] : null;
  }
  return null;
}

/* Words that show up in several outfits and must not, on their own, move
   a photo off the original release. */
const GENERIC_WORDS = new Set([
  "outfit", "disguise", "battle", "gear", "pilot", "guard", "with", "from",
  "the", "and", "into", "wear", "wearing", "knight", "suit", "original",
  "imperial", "royal", "organa", "wing", "coat", "gown"
]);

/* Cues the catalogue name does not spell out. Skiff Guard is the helmet
   or skiff outfit. General Pilot is the uniform. */
const EXTRA_PHRASES = {
  "70830": ["helmet", "skiff"],
  "93820": ["uniform", "general"],
  "39060": ["x wing", "flight suit"],
  "70660": ["boushh", "helmet"],
  "93780": ["stormtrooper"],
  "93720": ["pop up", "popup"]
};

function characterId(name) {
  const n = norm(name);
  if (!n) return null;
  if (n.startsWith("luke")) return "luke";
  if (n.includes("leia")) return "leia";
  if (n.startsWith("han solo") || n.startsWith("han ")) return "han";
  if (n.startsWith("lando")) return "lando";
  if (n.startsWith("chewbacca") || n.startsWith("chewie")) return "chewbacca";
  if (n.includes("artoo") || /\br2\b/.test(n)) return "r2";
  if (n.includes("3po")) return "c3po";
  if (n.includes("stormtrooper")) return "stormtrooper";
  if (n.startsWith("bespin security")) return "bespin-guard";
  if (n.startsWith("klaatu")) return "klaatu";
  return null;
}

function qualifierWords(name) {
  const raw = String(name || "");
  const paren = raw.match(/\(([^)]+)\)/);
  let source = paren ? paren[1] : "";
  if (!source) {
    const inMatch = raw.match(/\bin\s+(.+)$/i);
    source = inMatch ? inMatch[1] : "";
  }
  return norm(source).split(" ").filter(word => word.length > 3 && !GENERIC_WORDS.has(word));
}

function variantPhrases(figure) {
  const words = qualifierWords(figure.name);
  const extra = EXTRA_PHRASES[figure.product] || [];
  const phrases = [];
  if (words.length) phrases.push(words.join(" "));
  for (const word of words) phrases.push(word);
  for (const item of extra) phrases.push(norm(item));
  return [...new Set(phrases.filter(Boolean))];
}

function evidenceBlob(visibleAccessories, costumeCues) {
  const parts = [];
  if (Array.isArray(visibleAccessories)) parts.push(...visibleAccessories);
  if (Array.isArray(costumeCues)) parts.push(...costumeCues);
  return norm(parts.join(" "));
}

function baseFigure(group) {
  return group.slice().sort((a, b) =>
    a.year - b.year || a.name.length - b.name.length || String(a.product).localeCompare(String(b.product))
  )[0];
}

function bestSupportedVariant(group, base, blob) {
  let best = null;
  let bestLength = 0;
  for (const figure of group) {
    if (figure === base) continue;
    for (const phrase of variantPhrases(figure)) {
      if (!phrase || !blob.includes(phrase)) continue;
      if (phrase.length > bestLength) {
        best = figure;
        bestLength = phrase.length;
      }
    }
  }
  return best;
}

/* Same-name figures (Lando, Luke, Han, Leia, Chewbacca, and the other
   multi-release characters) stay on the original release unless the photo
   evidence names that later outfit. The model's variant subtitle is not
   evidence: "Lando Calrissian (Skiff Guard)" with no helmet still resolves
   to the 1980 Lando, which is what keeps the debut sentence. */
export function resolveDebutFigure(displayName, evidence = {}) {
  const figures = loadFigures();
  const familyId = characterId(displayName);
  if (familyId) {
    const group = figures.filter(fig => characterId(fig.name) === familyId);
    if (group.length === 1) return group[0];
    if (group.length > 1) {
      const base = baseFigure(group);
      const blob = evidenceBlob(evidence.visibleAccessories, evidence.costumeCues);
      return bestSupportedVariant(group, base, blob) || base;
    }
  }
  const exact = findDebutFigure(displayName);
  if (exact) return exact;
  const want = norm(displayName);
  if (!want) return null;
  const contained = figures.filter(fig => {
    const name = norm(fig.name);
    return name && (want.includes(name) || name.includes(want));
  });
  if (contained.length === 1) return contained[0];
  return null;
}

function joinList(items) {
  if (items.length <= 1) return items[0] || "";
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

function capitalise(word) {
  const text = String(word || "");
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : text;
}

function accessorySeen(name, visible) {
  const wanted = norm(name);
  if (!wanted) return false;
  return visible.some(item => {
    const seen = norm(item);
    if (!seen) return false;
    return seen === wanted || seen.includes(wanted) || wanted.includes(seen);
  });
}

export function completenessLine(figure, visibleAccessories) {
  const accessories = Array.isArray(figure && figure.accessories) ? figure.accessories : [];
  if (!accessories.length || !Array.isArray(visibleAccessories)) return "";
  const missing = accessories.filter(item => !accessorySeen(item, visibleAccessories));
  const pronoun = capitalise(figure.pronoun || "he");
  const possessive = figure.possessive || "his";
  if (!missing.length) {
    return `${pronoun} looks complete, with ${possessive} ${joinList(accessories)}.`;
  }
  return `${pronoun} appears to be missing ${possessive} ${joinList(missing)}.`;
}

export function variantButtonLabel(possessive, accessories) {
  const poss = possessive || "his";
  const count = Array.isArray(accessories) ? accessories.length : 0;
  if (count === 2) return `Would you like to identify ${poss} variant or either of ${poss} accessories?`;
  if (count === 1) return `Would you like to identify ${poss} variant or ${poss} accessory?`;
  if (count > 2) return `Would you like to identify ${poss} variant or ${poss} accessories?`;
  return `Would you like to identify ${poss} variant?`;
}

function releaseClause(figure) {
  const outside = figure.outsideUs ? " (sold outside the US)" : "";
  return `first released in ${figure.year} on the ${figure.cardback} ${figure.line} cardback${outside}`;
}

export function composePhotoReply({ itemKind, displayName, visibleAccessories, costumeCues }) {
  const accessory = itemKind === "accessory";
  if (accessory) {
    const name = String(displayName || "").trim() || "an unidentified accessory";
    return {
      reply: `The accessory in your photo appears to be ${name}.`,
      displayName: name,
      itemKind: "accessory",
      pronoun: "it",
      possessive: "its",
      accessories: [],
      actions: [
        { label: ACCESSORY_QUESTION_BUTTON, value: "ask-about-accessory" },
        { label: "Would you like to identify its mould, colour or markings?", value: "identify-this-accessory" }
      ],
      quickReplies: true,
      helper: PHOTO_HELPER
    };
  }

  const figure = resolveDebutFigure(displayName, { visibleAccessories, costumeCues });
  const name = figure ? figure.name : (String(displayName || "").trim() || "an unidentified figure");
  const pronoun = figure ? figure.pronoun : "he";
  const possessive = figure ? figure.possessive : "his";
  const accessories = figure && Array.isArray(figure.accessories) ? figure.accessories : [];
  let reply = figure
    ? `The figure in your photo appears to be ${name}, ${releaseClause(figure)}.`
    : `The figure in your photo appears to be ${name}.`;
  const complete = figure ? completenessLine(figure, visibleAccessories) : "";
  if (complete) reply += ` ${complete}`;
  return {
    reply,
    displayName: name,
    itemKind: "figure",
    pronoun,
    possessive,
    accessories,
    actions: [
      { label: QUESTION_BUTTON, value: "ask-about-figure" },
      { label: variantButtonLabel(possessive, accessories), value: "identify-variant-or-accessories" }
    ],
    quickReplies: true,
    helper: PHOTO_HELPER
  };
}
