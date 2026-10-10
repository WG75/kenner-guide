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

export function composePhotoReply({ itemKind, displayName, visibleAccessories }) {
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

  const figure = findDebutFigure(displayName);
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
