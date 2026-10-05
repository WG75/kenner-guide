import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

// Hot-linked Variant Villain photos shown under a text answer.
// Set this to false if Variant Villain asks us to stop. Nothing else needs to change.
export const VV_REFERENCE_PHOTOS = true;

const MAP_PATH = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "data-source", "vv-images.json");
const CREDIT = "Photo: Variant Villain";
const MAX_IMAGES = 3;
const FAMILY_RE = /\bfamily\s+(xii|xi|x|ix|viii|vii|vi|v|iv|iii|ii|i)\b/i;
const ACCESSORY_RE = /\b(cape|cloak|saber|sabre|blaster|rifle|helmet|staff|weapon|accessory|accessories|bowcaster|gaderffii|gaffi|skirt|belt|hood|spear|axe|pike|cane|net)\b/i;

let mapCache;

function loadMap() {
  if (mapCache) return mapCache;
  try {
    mapCache = JSON.parse(fs.readFileSync(MAP_PATH, "utf8"));
  } catch (err) {
    mapCache = { entries: [] };
  }
  return mapCache;
}

function mentionedFamily(question) {
  const match = String(question || "").match(FAMILY_RE);
  return match ? match[1].toUpperCase() : "";
}

function linkedEntries(sources, entries) {
  const wanted = new Set(sources || []);
  const found = [];
  const seen = new Set();
  for (const source of wanted) {
    for (const entry of entries) {
      if (seen.has(entry.page)) continue;
      if ((entry.files || []).includes(source)) {
        seen.add(entry.page);
        found.push(entry);
      }
    }
  }
  return found;
}

function chooseEntry(question, sources, entries) {
  const linked = linkedEntries(sources, entries);
  if (!linked.length) return null;
  if (ACCESSORY_RE.test(String(question || ""))) {
    const accessory = linked.find(entry => entry.kind === "accessory");
    if (accessory) return accessory;
  }
  return linked.find(entry => entry.kind === "figure") || linked[0];
}

function toClient(image) {
  return {
    url: image.url,
    alt: image.alt || "",
    sourcePage: image.sourcePage,
    credit: CREDIT
  };
}

function chooseImages(entry, question) {
  const images = Array.isArray(entry.images) ? entry.images : [];
  const family = mentionedFamily(question);
  const picked = [];
  const seen = new Set();

  const add = (image) => {
    if (!image || !image.url || seen.has(image.url) || picked.length >= MAX_IMAGES) return;
    seen.add(image.url);
    picked.push(toClient(image));
  };

  if (entry.kind === "accessory") {
    images.forEach(add);
    return picked;
  }

  if (family) add(images.find(image => image.family === family));
  add(images.find(image => image.role === "coo" && !image.family));
  add(images.find(image => image.family));
  add(images.find(image => image.role === "figure"));
  add(images.find(image => image.role === "guide"));
  images.forEach(add);
  return picked;
}

/* Images for one answer. Chosen from the matched figure or accessory, never from model text. */
export function selectVvReferencePhotos({ question, sources, enabled = VV_REFERENCE_PHOTOS, map } = {}) {
  if (!enabled) return [];
  const entries = (map || loadMap()).entries || [];
  const entry = chooseEntry(question, sources, entries);
  if (!entry) return [];
  return chooseImages(entry, question);
}
