import { normaliseGrade } from "./condition-grades.js";

export const DEFAULT_LIST_NAME = "Personal Collection";
export const STORED_PHOTO_LIMIT = 180_000;

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export function emptyDraft() {
  return {
    figureName: "",
    figureKey: "",
    factory: "",
    mould: "",
    coo: "",
    figureGrade: "",
    notes: "",
    ownedOn: "",
    accessories: []
  };
}

function clean(value, max) {
  return String(value || "").trim().slice(0, max);
}

function figureKeyFrom(name, given) {
  const raw = clean(given, 80) || clean(name, 80);
  return raw.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "").slice(0, 80);
}

function mergeAccessory(list, accessory) {
  const name = clean(accessory && accessory.name, 80);
  if (!name) return list;
  const existing = list.find(item => item.name.toLowerCase() === name.toLowerCase());
  if (existing) {
    if (!existing.variant && accessory.variant) existing.variant = clean(accessory.variant, 80);
    return list;
  }
  list.push({ name, variant: clean(accessory && accessory.variant, 80), grade: "" });
  return list;
}

/* Keep the latest identification on the draft the Save dialog will open. */
export function applyIdentification(draft, flowState) {
  const next = {
    ...(draft || emptyDraft()),
    accessories: Array.isArray(draft && draft.accessories) ? draft.accessories.map(item => ({ ...item })) : []
  };
  if (!flowState || typeof flowState !== "object") return next;
  if (flowState.topic === "image_identified" && flowState.displayName) {
    if (flowState.itemKind === "accessory") {
      mergeAccessory(next.accessories, { name: flowState.displayName });
    } else {
      next.figureName = clean(flowState.displayName, 120);
      next.figureKey = figureKeyFrom(next.figureName, flowState.figure);
      const seen = Array.isArray(flowState.visibleAccessories) ? flowState.visibleAccessories : [];
      for (const name of seen) mergeAccessory(next.accessories, { name });
    }
  }
  if (flowState.figure && flowState.factory) {
    next.figureName = clean(flowState.figure, 120);
    next.figureKey = figureKeyFrom(next.figureName, next.figureKey);
    next.factory = clean(String(flowState.factory).replace(/\s+guide$/i, ""), 80);
  }
  if (flowState.topic === "accessory_factory" && flowState.accessory) {
    mergeAccessory(next.accessories, { name: flowState.accessory });
  }
  return next;
}

export function identificationReady(draft) {
  return Boolean(draft && (clean(draft.figureName, 120) || (draft.accessories || []).some(item => clean(item.name, 80))));
}

export function validateItem(input) {
  const source = input || {};
  const figureName = clean(source.figureName, 120);
  const accessories = Array.isArray(source.accessories) ? source.accessories : [];
  const namedAccessories = accessories.filter(item => clean(item && item.name, 80));
  if (!figureName && !namedAccessories.length) {
    return { ok: false, error: "name_required", message: "Add the figure name, or the accessory name, before saving." };
  }
  if (namedAccessories.length > 12) {
    return { ok: false, error: "too_many_accessories", message: "Save up to 12 accessories on one item." };
  }
  const figureGrade = normaliseGrade(source.figureGrade);
  if (!figureGrade.ok) return { ok: false, error: figureGrade.error, message: figureGrade.message };
  const storedAccessories = [];
  for (const accessory of namedAccessories) {
    const grade = normaliseGrade(accessory.grade);
    if (!grade.ok) return { ok: false, error: grade.error, message: grade.message };
    storedAccessories.push({
      name: clean(accessory.name, 80),
      variant: clean(accessory.variant, 80),
      grade: grade.grade
    });
  }
  const photo = String(source.photo || "");
  if (photo) {
    if (!/^data:image\/jpeg;base64,[a-z0-9+/=\s]+$/i.test(photo)) {
      return { ok: false, error: "bad_photo", message: "The saved photo needs to be a reduced JPEG." };
    }
    if (photo.length > STORED_PHOTO_LIMIT) {
      return { ok: false, error: "photo_too_large", message: "That photo is still too large to keep. Try again without it, or use a smaller picture." };
    }
  }
  let ownedOn = clean(source.ownedOn, 10);
  if (ownedOn && !DATE_RE.test(ownedOn)) {
    return { ok: false, error: "bad_date", message: "Use a date like 2026-10-11." };
  }
  if (!ownedOn) ownedOn = new Date().toISOString().slice(0, 10);
  return {
    ok: true,
    item: {
      figureName,
      figureKey: figureKeyFrom(figureName, source.figureKey),
      factory: clean(source.factory, 80),
      mould: clean(source.mould, 80),
      coo: clean(source.coo, 80),
      figureGrade: figureGrade.grade,
      photo,
      notes: clean(source.notes, 2000),
      ownedOn,
      accessories: storedAccessories
    }
  };
}

export function validateListName(name) {
  const cleaned = clean(name, 40);
  if (!cleaned) return { ok: false, error: "name_required", message: "Give the list a name." };
  return { ok: true, name: cleaned };
}

function norm(value) {
  return String(value || "").trim().toLowerCase().replace(/\s+/g, " ");
}

/* figures: [{ name, aliases }]. items: saved rows with figureName and figureKey. */
export function buildChecklist(figures, items) {
  const saved = Array.isArray(items) ? items : [];
  const rows = (Array.isArray(figures) ? figures : []).map(fig => {
    const names = new Set([norm(fig.name), ...(Array.isArray(fig.aliases) ? fig.aliases.map(norm) : [])].filter(Boolean));
    const key = norm(fig.name).replace(/[^a-z0-9]+/g, " ").trim();
    const matches = saved.filter(item => {
      if (names.has(norm(item.figureName))) return true;
      const itemKey = norm(item.figureKey).replace(/_/g, " ");
      return Boolean(key) && itemKey === key;
    });
    return {
      name: fig.name,
      owned: matches.length > 0,
      copies: matches.length,
      listNames: [...new Set(matches.map(item => item.listName).filter(Boolean))],
      grades: matches.map(item => item.figureGrade).filter(Boolean)
    };
  });
  const owned = rows.filter(row => row.owned).length;
  return { total: rows.length, owned, needed: rows.length - owned, figures: rows };
}
